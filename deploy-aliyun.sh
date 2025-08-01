#!/bin/bash

# 阿里云服务器部署脚本
# GitHub Trending 爬虫 API 自动化部署
# 
# 功能特性：
# - 支持 Ubuntu/Debian 和 CentOS/RHEL/AlibabaCloud Linux
# - 智能检测Docker/Docker Compose安装状态，避免重复安装
# - 自动配置国内Docker镜像源，解决拉取慢的问题
# - 智能防火墙配置（UFW/Firewalld）
# - 网络连通性测试
# - 镜像预拉取，提高部署成功率
# - SSL证书自动申请（可选）
# - 完整的日志和错误处理
#
# 使用方法：
# chmod +x deploy-aliyun.sh
# ./deploy-aliyun.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行此脚本"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统版本"
        exit 1
    fi
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [[ $MEMORY -lt 1024 ]]; then
        log_warning "系统内存少于1GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    DISK=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ ${DISK%.*} -lt 5 ]]; then
        log_warning "磁盘可用空间少于5GB，可能影响运行"
    fi
    
    log_success "系统环境检查完成"
}

# 检查Docker是否已安装并正常运行
check_docker_installation() {
    log_info "检查Docker安装状态..."
    
    # 检查Docker命令是否存在
    if ! command -v docker &> /dev/null; then
        log_info "Docker未安装，需要安装"
        return 1
    fi
    
    # 检查Docker版本
    DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [[ -z "$DOCKER_VERSION" ]]; then
        log_warning "无法获取Docker版本信息"
        return 1
    fi
    
    log_info "检测到Docker版本: $DOCKER_VERSION"
    
    # 检查Docker服务状态
    if ! sudo systemctl is-active --quiet docker; then
        log_info "Docker服务未运行，尝试启动..."
        if sudo systemctl start docker; then
            log_success "Docker服务启动成功"
        else
            log_error "Docker服务启动失败"
            return 1
        fi
    else
        log_info "Docker服务正在运行"
    fi
    
    # 检查Docker是否可以正常工作
    if sudo docker info &> /dev/null; then
        log_success "Docker安装正常，跳过安装步骤"
        
        # 检查是否配置了国内镜像源
        if ! sudo docker info 2>/dev/null | grep -q "Registry Mirrors"; then
            log_info "检测到Docker未配置国内镜像源，正在配置..."
            configure_docker_mirror
        else
            log_info "Docker镜像源已配置"
        fi
        
        return 0
    else
        log_warning "Docker安装存在问题，需要重新安装"
        return 1
    fi
}

# 安装Docker
install_docker() {
    # 首先检查Docker是否已安装并正常工作
    if check_docker_installation; then
        return
    fi
    
    log_info "开始安装Docker..."
    
    # 检测操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    case $OS in
        ubuntu|debian)
            install_docker_ubuntu
            ;;
        centos|rhel|alinux)
            install_docker_centos
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    # 配置Docker国内镜像源
    configure_docker_mirror
    
    log_success "Docker安装完成"
}

# Ubuntu/Debian系统安装Docker
install_docker_ubuntu() {
    # 更新包管理器
    sudo apt-get update
    
    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 使用阿里云Docker源（国内服务器友好）
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加阿里云Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
}

# CentOS/RHEL/AlibabaCloud Linux系统安装Docker
install_docker_centos() {
    # 更新包管理器
    sudo yum update -y
    
    # 安装必要的包
    sudo yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # 添加阿里云Docker仓库
    sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
    
    # 安装Docker Engine
    sudo yum install -y docker-ce docker-ce-cli containerd.io
}

# 配置Docker国内镜像源
configure_docker_mirror() {
    log_info "配置Docker国内镜像源..."
    
    # 创建Docker配置目录
    sudo mkdir -p /etc/docker
    
    # 配置镜像加速器（阿里云、腾讯云、网易云等）
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "exec-opts": ["native.cgroupdriver=systemd"]
}
EOF
    
    # 重启Docker服务使配置生效
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    log_success "Docker镜像源配置完成"
}

# 检查Docker Compose是否已安装并正常运行
check_docker_compose_installation() {
    log_info "检查Docker Compose安装状态..."
    
    # 检查docker-compose命令是否存在
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [[ -n "$COMPOSE_VERSION" ]]; then
            log_success "Docker Compose已安装，版本: $COMPOSE_VERSION"
            return 0
        fi
    fi
    
    # 检查docker compose命令（Docker Compose V2）
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [[ -n "$COMPOSE_VERSION" ]]; then
            log_success "Docker Compose V2已安装，版本: $COMPOSE_VERSION"
            return 0
        fi
    fi
    
    log_info "Docker Compose未安装，需要安装"
    return 1
}

# 安装Docker Compose
install_docker_compose() {
    # 首先检查Docker Compose是否已安装
    if check_docker_compose_installation; then
        return
    fi
    
    log_info "开始安装Docker Compose..."
    
    # 尝试从国内镜像下载Docker Compose
    COMPOSE_VERSION="v2.20.0"
    ARCH=$(uname -m)
    OS=$(uname -s)
    
    # 国内镜像源列表
    MIRRORS=(
        "https://get.daocloud.io/docker/compose/releases/download"
        "https://github.com/docker/compose/releases/download"
    )
    
    for MIRROR in "${MIRRORS[@]}"; do
        log_info "尝试从 $MIRROR 下载..."
        if sudo curl -L "$MIRROR/$COMPOSE_VERSION/docker-compose-$OS-$ARCH" -o /usr/local/bin/docker-compose --connect-timeout 10; then
            break
        else
            log_warning "从 $MIRROR 下载失败，尝试下一个源..."
        fi
    done
    
    # 检查下载是否成功
    if [[ ! -f /usr/local/bin/docker-compose ]]; then
        log_error "Docker Compose下载失败"
        exit 1
    fi
    
    # 添加执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    # 检测操作系统并配置相应的防火墙
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
    fi
    
    case $OS in
        ubuntu|debian)
            setup_ufw_firewall
            ;;
        centos|rhel|alinux)
            setup_firewalld
            ;;
        *)
            log_warning "未知操作系统，跳过防火墙配置"
            ;;
    esac
}

# Ubuntu/Debian系统防火墙配置
setup_ufw_firewall() {
    # 检查ufw是否安装
    if ! command -v ufw &> /dev/null; then
        sudo apt-get install -y ufw
    fi
    
    # 配置防火墙规则
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    
    log_success "UFW防火墙配置完成"
}

# CentOS/RHEL系统防火墙配置
setup_firewalld() {
    # 启动firewalld服务
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    
    # 配置防火墙规则
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
    
    log_success "Firewalld防火墙配置完成"
}

# 测试网络连通性
test_network() {
    log_info "测试网络连通性..."
    
    # 测试国内镜像源连通性
    MIRRORS=(
        "docker.mirrors.ustc.edu.cn"
        "hub-mirror.c.163.com"
        "mirror.baidubce.com"
    )
    
    for mirror in "${MIRRORS[@]}"; do
        if curl -s --connect-timeout 5 "https://$mirror" > /dev/null; then
            log_success "$mirror 连通正常"
        else
            log_warning "$mirror 连通失败"
        fi
    done
}

# 预拉取Docker镜像
pre_pull_images() {
    log_info "预拉取Docker镜像..."
    
    # 基础镜像列表
    IMAGES=(
        "python:3.9-slim"
        "nginx:alpine"
        "alpine:latest"
    )
    
    for image in "${IMAGES[@]}"; do
        log_info "拉取镜像: $image"
        if docker pull "$image"; then
            log_success "镜像 $image 拉取成功"
        else
            log_warning "镜像 $image 拉取失败，部署时将重试"
        fi
    done
}

# 创建必要目录
setup_directories() {
    log_info "创建必要目录..."
    
    mkdir -p logs/nginx
    mkdir -p ssl
    
    # 设置权限
    chmod 755 logs
    chmod 755 ssl
    
    log_success "目录创建完成"
}

# 配置SSL证书（Let's Encrypt）
setup_ssl() {
    read -p "是否配置SSL证书？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "跳过SSL配置"
        return
    fi
    
    read -p "请输入您的域名: " DOMAIN
    read -p "请输入您的邮箱: " EMAIL
    
    if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
        log_error "域名和邮箱不能为空"
        return
    fi
    
    log_info "安装Certbot..."
    sudo apt-get install -y certbot
    
    log_info "申请SSL证书..."
    sudo certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
    
    # 复制证书到项目目录
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
    sudo chown $USER:$USER ssl/*.pem
    
    # 设置自动续期
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
    
    log_success "SSL证书配置完成"
}

# 部署应用
deploy_app() {
    log_info "部署应用..."
    
    # 停止现有服务
    if [[ -f docker-compose.prod.yml ]]; then
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    fi
    
    # 构建并启动服务
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "应用部署成功"
    else
        log_error "应用部署失败，请检查日志"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# 显示部署信息
show_info() {
    log_success "=== 部署完成 ==="
    echo
    log_info "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
    echo
    log_info "访问地址:"
    echo "  HTTP:  http://$(curl -s ifconfig.me)"
    if [[ -f ssl/fullchain.pem ]]; then
        echo "  HTTPS: https://$(curl -s ifconfig.me)"
    fi
    echo
    log_info "API文档: http://$(curl -s ifconfig.me)/docs"
    echo
    log_info "常用命令:"
    echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
    echo
}

# 主函数
main() {
    log_info "开始阿里云服务器部署..."
    echo
    
    # 基础环境检查和安装
    check_root
    check_system
    
    # 网络连通性测试
    test_network
    
    # Docker环境安装
    install_docker
    install_docker_compose
    
    # 预拉取镜像（提高部署成功率）
    pre_pull_images
    
    # 系统配置
    setup_firewall
    setup_directories
    
    # SSL证书配置（可选）
    setup_ssl
    
    # 应用部署
    deploy_app
    
    # 显示部署信息
    show_info
    
    log_success "🎉 阿里云部署完成！"
}

# 执行主函数
main "$@"