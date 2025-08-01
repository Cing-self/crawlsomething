#!/bin/bash

# 阿里云服务器部署脚本
# GitHub Trending 爬虫 API 自动化部署

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

# 安装Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker已安装，版本: $(docker --version)"
        return
    fi
    
    log_info "安装Docker..."
    
    # 更新包管理器
    sudo apt-get update
    
    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose已安装，版本: $(docker-compose --version)"
        return
    fi
    
    log_info "安装Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 添加执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
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
    
    log_success "防火墙配置完成"
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
    
    check_root
    check_system
    install_docker
    install_docker_compose
    setup_firewall
    setup_directories
    setup_ssl
    deploy_app
    show_info
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"