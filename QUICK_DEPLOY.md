# 🚀 阿里云快速部署指南

> 5分钟内完成 GitHub Trending 爬虫 API 在阿里云的部署

## 📋 部署前准备

### 1. 阿里云 ECS 要求
- **配置**: 1核2GB 或以上
- **系统**: Ubuntu 20.04 LTS
- **带宽**: 1Mbps 或以上
- **存储**: 20GB 或以上

### 2. 域名准备（可选）
- 已备案的域名
- DNS 解析指向 ECS 公网 IP

## ⚡ 一键部署

### 方式一：自动化脚本（推荐）

```bash
# 1. 上传项目到服务器
scp -r ./crawlsomething root@your-server-ip:/opt/

# 2. 登录服务器
ssh root@your-server-ip

# 3. 进入项目目录
cd /opt/crawlsomething

# 4. 运行一键部署脚本
./deploy-aliyun.sh
```

脚本会自动完成：
- ✅ 系统环境检查
- ✅ Docker 环境安装
- ✅ 防火墙配置
- ✅ SSL 证书申请
- ✅ 应用部署启动

### 方式二：手动部署

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo systemctl start docker
sudo systemctl enable docker

# 2. 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 4. 部署应用
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

**1. 无法访问 API**
```bash
# 检查防火墙
sudo ufw status

# 检查端口占用
sudo netstat -tlnp | grep :80

# 检查容器状态
docker-compose -f docker-compose.prod.yml ps
```

**2. SSL 证书问题**
```bash
# 检查证书有效期
openssl x509 -in ssl/fullchain.pem -text -noout | grep "Not After"

# 手动续期
sudo certbot renew
```

**3. 性能问题**
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