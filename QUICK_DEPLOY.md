# 🚀 阿里云快速部署指南

> 5分钟内完成 GitHub Trending 爬虫 API 在阿里云的部署

## 📋 部署前准备

### 1. 阿里云 ECS 要求
- **配置**: 2核4GB 或以上（推荐）
- **系统**: Ubuntu 20.04+、CentOS 7+ 或 AlibabaCloud Linux 3
- **带宽**: 1Mbps 或以上
- **存储**: 40GB 或以上
- **已开放端口**: 80, 443, 22
- **权限**: 具有sudo权限的用户账户

### 2. 域名准备（可选）
- 已备案的域名
- DNS 解析指向 ECS 公网 IP

### ✨ 脚本特性

- 🌐 **智能镜像源配置**：自动配置国内Docker镜像源，解决拉取慢的问题
- 🔧 **多系统支持**：支持Ubuntu/Debian和CentOS/RHEL/AlibabaCloud Linux
- 🛡️ **智能防火墙**：根据系统自动配置UFW或Firewalld
- 🌍 **网络测试**：部署前测试网络连通性
- 📦 **镜像预拉取**：提前拉取基础镜像，提高部署成功率
- 🔒 **SSL支持**：可选的自动SSL证书申请
- 📝 **完整日志**：详细的部署日志和错误处理

## ⚡ 一键部署

### 方式一：自动化脚本（推荐）

```bash
# 1. 克隆项目或下载部署脚本
git clone https://github.com/your-repo/crawlsomething.git
cd crawlsomething

# 或者直接下载脚本
# wget https://raw.githubusercontent.com/your-repo/crawlsomething/main/deploy-aliyun.sh

# 2. 添加执行权限
chmod +x deploy-aliyun.sh

# 3. 运行部署脚本
./deploy-aliyun.sh
```

**🎯 脚本将自动完成：**
- ✅ 系统环境检查和兼容性测试
- ✅ 网络连通性测试
- ✅ Docker 和 Docker Compose 安装
- ✅ **国内镜像源配置**（解决拉取慢的问题）
- ✅ 智能防火墙配置
- ✅ 基础镜像预拉取
- ✅ 应用构建和部署
- ✅ SSL 证书配置（可选）

**🌟 特别优化：**
- 自动配置中科大、网易、百度等国内Docker镜像源
- 支持CentOS/RHEL/AlibabaCloud Linux系统
- 智能重试机制，提高部署成功率

### 方式二：手动部署

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo systemctl start docker
sudo systemctl enable docker

# 2. 配置国内镜像源（重要）
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
sudo systemctl restart docker

# 3. 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 5. 部署应用
mkdir -p logs/nginx ssl
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔧 阿里云安全组配置

在阿里云控制台配置安全组规则：

| 方向 | 协议 | 端口 | 源地址 | 说明 |
|------|------|------|--------|---------|
| 入方向 | TCP | 22 | 0.0.0.0/0 | SSH 访问 |
| 入方向 | TCP | 80 | 0.0.0.0/0 | HTTP 访问 |
| 入方向 | TCP | 443 | 0.0.0.0/0 | HTTPS 访问 |

## 🌐 域名配置（可选）

### 1. DNS 解析
```
A 记录: your-domain.com -> ECS公网IP
CNAME: www.your-domain.com -> your-domain.com
```

### 2. SSL 证书
```bash
# 使用 Let's Encrypt 免费证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

## ✅ 部署验证

### 1. 检查服务状态
```bash
docker-compose -f docker-compose.prod.yml ps
```

### 2. 测试 API 访问
```bash
# HTTP 访问
curl http://your-server-ip/

# API 测试
curl "http://your-server-ip/api/trending?language=python&since=daily"
```

### 3. 访问 API 文档
浏览器访问：`http://your-server-ip/docs`

## 📊 监控和维护

### 常用命令
```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 更新应用
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz logs ssl
```

### 性能监控
```bash
# 查看资源使用
docker stats

# 查看系统负载
top
htop
```

## 🔒 安全建议

1. **定期更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **配置 SSH 密钥登录**
   ```bash
   # 禁用密码登录
   sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   sudo systemctl restart sshd
   ```

3. **设置自动备份**
   ```bash
   # 添加到 crontab
   0 2 * * * cd /opt/crawlsomething && tar -czf backup-$(date +\%Y\%m\%d).tar.gz logs ssl
   ```

## 💰 成本优化

### 推荐配置
- **开发测试**: 1核2GB (约 ¥50/月)
- **小规模生产**: 2核4GB (约 ¥100/月)
- **中等规模**: 4核8GB (约 ¥200/月)

### 节省成本技巧
1. 使用按量付费实例进行测试
2. 合理配置带宽（1-5Mbps 通常足够）
3. 定期清理日志文件
4. 使用阿里云的优惠活动

## 🆘 故障排除

### 常见问题

**1. Docker 拉取镜像失败**
```bash
# 检查镜像源配置
cat /etc/docker/daemon.json

# 测试镜像源连通性
curl -s https://docker.mirrors.ustc.edu.cn

# 重启 Docker 服务
sudo systemctl restart docker

# 手动拉取镜像测试
docker pull python:3.9-slim
```

**2. 网络连接问题**
```bash
# 测试网络连通性
ping docker.mirrors.ustc.edu.cn
ping hub-mirror.c.163.com

# 检查DNS设置
cat /etc/resolv.conf
```

**3. 无法访问 API**
```bash
# 检查防火墙
sudo ufw status

# 检查端口占用
sudo netstat -tlnp | grep :80

# 检查容器状态
docker-compose -f docker-compose.prod.yml ps
```

**4. SSL 证书问题**
```bash
# 检查证书有效期
openssl x509 -in ssl/fullchain.pem -text -noout | grep "Not After"

# 手动续期
sudo certbot renew
```

**5. 权限问题**
```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

**6. CentOS/RHEL 系统特殊问题**
```bash
# 启用 EPEL 仓库
sudo yum install -y epel-release

# 检查 SELinux 状态
getenforce

# 临时关闭 SELinux（如需要）
sudo setenforce 0
```

**7. 性能问题**
```bash
# 查看资源使用
docker stats

# 调整 worker 数量
# 编辑 docker-compose.prod.yml 中的 WORKERS 环境变量
```

## 📞 技术支持

- 📖 详细文档: [ALIYUN_DEPLOYMENT.md](./ALIYUN_DEPLOYMENT.md)
- 🐳 Docker 文档: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- 🔧 项目文档: [README.md](./README.md)

---

**部署成功后，您的 API 将在以下地址可用：**
- HTTP: `http://your-server-ip`
- HTTPS: `https://your-domain.com` (如果配置了域名和SSL)
- API 文档: `http://your-server-ip/docs`