# 阿里云ECS部署指南

本文档专门针对阿里云ECS服务器部署GitHub Trending爬虫API，提供公网访问服务。

## 🏗️ 阿里云部署架构

```
公网用户 → 阿里云SLB/CDN → ECS服务器 → Docker容器 → API服务
         ↓
    域名解析(可选)
         ↓
    SSL证书(HTTPS)
```

## 📋 部署前准备

### 1. 阿里云资源要求

**ECS实例配置建议：**
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **磁盘**: 40GB以上SSD
- **带宽**: 5Mbps以上
- **操作系统**: Ubuntu 20.04 LTS / CentOS 8

**网络配置：**
- VPC网络（推荐）
- 弹性公网IP
- 安全组配置

### 2. 域名和证书（可选但推荐）

- 域名备案（如果使用.cn域名或在中国大陆提供服务）
- SSL证书（阿里云免费证书或Let's Encrypt）

## 🔧 ECS服务器配置

### 1. 连接到ECS实例

```bash
# 使用SSH连接（替换为您的ECS公网IP）
ssh root@your-ecs-ip

# 或使用阿里云控制台的远程连接功能
```

### 2. 安装Docker环境

**Ubuntu/Debian:**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

**CentOS/RHEL:**
```bash
# 更新系统
sudo yum update -y

# 安装Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 配置防火墙

**Ubuntu (UFW):**
```bash
# 启用防火墙
sudo ufw enable

# 开放SSH端口
sudo ufw allow 22

# 开放HTTP/HTTPS端口
sudo ufw allow 80
sudo ufw allow 443

# 开放API端口（如果直接访问）
sudo ufw allow 8000

# 查看状态
sudo ufw status
```

**CentOS (firewalld):**
```bash
# 启动防火墙
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 开放端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 🚀 部署应用

### 1. 获取项目代码

```bash
# 安装Git
sudo apt install git -y  # Ubuntu
# 或
sudo yum install git -y  # CentOS

# 克隆项目
git clone https://github.com/Cing-self/crawlsomething.git
cd crawlsomething
```

### 2. 自动化部署（推荐）

项目提供了自动化部署脚本，可以一键完成环境配置和应用部署：

```bash
# 运行自动化部署脚本
./deploy-aliyun.sh
```

该脚本会自动完成：
- 系统环境检查
- Docker 和 Docker Compose 安装
- 防火墙配置
- SSL 证书申请（可选）
- 应用部署和启动

如果需要手动部署，请继续阅读下面的步骤。

### 3. 手动部署配置

项目已包含生产环境的 Docker Compose 配置文件 `docker-compose.prod.yml`，该配置包含：

- **安全配置**：API 服务不直接暴露端口，仅通过 Nginx 代理访问
- **资源限制**：设置 CPU 和内存限制，防止资源滥用
- **日志管理**：持久化日志存储和自动轮转
- **健康检查**：自动监控服务状态
- **SSL 支持**：HTTPS 加密传输

**创建生产环境配置：**
```bash
# 创建环境变量文件
cat > .env.production << EOF
LOG_LEVEL=WARNING
REQUEST_TIMEOUT=30
MAX_RETRIES=3
ENVIRONMENT=production
EOF
```

主要特性：
```yaml
# 资源限制示例
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

**生产版docker-compose配置已包含在项目中：**
```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  crawlsomething:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: github-trending-crawler-prod
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - crawlsomething
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

networks:
  default:
    name: crawler-prod-network
EOF
```

### 4. Nginx 配置

项目已包含优化的 Nginx 配置文件 `nginx.conf`，具备以下特性：

- **API 限流保护**：防止 API 滥用，设置合理的请求频率限制
- **CORS 支持**：允许跨域访问，支持前端应用调用
- **安全头设置**：包含完整的安全响应头
- **SSL/TLS 配置**：支持 HTTPS 加密传输
- **性能优化**：Gzip 压缩、缓冲设置等

主要安全特性：
```nginx
# API 限流（每秒10个请求）
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

# CORS 配置
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;

# 安全头
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**Nginx生产环境配置**

```bash
cat > nginx.prod.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 10M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # 上游服务器
    upstream api_backend {
        server crawlsomething:8000;
    }
    
    # HTTP服务器
    server {
        listen 80;
        server_name _; # 替换为您的域名
        
        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # API限流
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS配置
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range" always;
            
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }
        
        # 根路径
        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 健康检查
        location /health {
            proxy_pass http://api_backend/;
            access_log off;
        }
    }
EOF
```

### 5. 启动服务

```bash
# 创建日志目录
mkdir -p logs/nginx

# 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f crawlsomething
docker-compose -f docker-compose.prod.yml logs -f nginx
```

## 🔒 阿里云安全组配置

### 1. 登录阿里云控制台

1. 进入ECS管理控制台
2. 选择您的ECS实例
3. 点击"安全组"标签
4. 配置安全组规则

### 2. 入方向规则配置

| 协议类型 | 端口范围 | 授权对象 | 描述 |
|---------|---------|---------|------|
| TCP | 22 | 0.0.0.0/0 | SSH访问 |
| TCP | 80 | 0.0.0.0/0 | HTTP访问 |
| TCP | 443 | 0.0.0.0/0 | HTTPS访问 |
| TCP | 8000 | 0.0.0.0/0 | API直接访问（可选） |

**安全建议：**
- SSH端口22建议限制为特定IP访问
- 生产环境建议关闭8000端口，仅通过Nginx代理访问

## 🌐 域名配置（可选）

### 1. 域名解析

在阿里云域名控制台添加A记录：
```
类型: A
主机记录: api (或 @)
记录值: 您的ECS公网IP
TTL: 600
```

### 2. SSL证书配置

**方式一：阿里云免费证书**
```bash
# 下载证书到ECS
mkdir -p ssl
# 上传证书文件到ssl目录
# 修改nginx配置启用HTTPS
```

**方式二：Let's Encrypt免费证书**
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx -y

# 申请证书（替换为您的域名）
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控和维护

### 1. 服务监控

```bash
# 查看容器状态
docker ps

# 查看资源使用
docker stats

# 查看日志
tail -f logs/nginx/access.log
tail -f logs/nginx/error.log
```

### 2. 自动化脚本

**创建启动脚本：**
```bash
cat > start.sh << 'EOF'
#!/bin/bash
cd /root/crawlsomething
docker-compose -f docker-compose.prod.yml up -d
echo "服务已启动"
EOF

chmod +x start.sh
```

**创建停止脚本：**
```bash
cat > stop.sh << 'EOF'
#!/bin/bash
cd /root/crawlsomething
docker-compose -f docker-compose.prod.yml down
echo "服务已停止"
EOF

chmod +x stop.sh
```

### 3. 系统服务配置

```bash
# 创建systemd服务
sudo cat > /etc/systemd/system/crawler-api.service << 'EOF'
[Unit]
Description=GitHub Trending Crawler API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/crawlsomething
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable crawler-api.service
sudo systemctl start crawler-api.service
```

## 🧪 部署验证

### 1. 本地测试

```bash
# 测试API响应
curl http://localhost/api/trending

# 测试健康检查
curl http://localhost/health
```

### 2. 公网测试

```bash
# 替换为您的ECS公网IP或域名
curl http://your-ecs-ip/api/trending
curl http://your-domain.com/api/trending

# 测试HTTPS（如果配置了SSL）
curl https://your-domain.com/api/trending
```

### 3. 性能测试

```bash
# 安装ab工具
sudo apt install apache2-utils -y

# 并发测试
ab -n 1000 -c 10 http://your-domain.com/api/trending
```

## 🚨 故障排除

### 常见问题

**1. 无法访问API**
```bash
# 检查容器状态
docker ps

# 检查端口监听
sudo netstat -tlnp | grep :80

# 检查防火墙
sudo ufw status
```

**2. 性能问题**
```bash
# 查看系统资源
top
df -h
free -h

# 查看Docker资源
docker stats
```

**3. SSL证书问题**
```bash
# 检查证书有效期
openssl x509 -in ssl/cert.pem -text -noout

# 测试SSL配置
openssl s_client -connect your-domain.com:443
```

## 💰 成本优化建议

1. **选择合适的ECS规格**：根据实际访问量选择
2. **使用按量付费**：测试阶段使用按量付费
3. **配置弹性伸缩**：根据负载自动调整实例数量
4. **使用CDN**：减少ECS带宽成本
5. **定期清理日志**：避免磁盘空间不足

## 📈 扩展方案

### 1. 负载均衡

使用阿里云SLB实现多实例负载均衡：
```bash
# 部署多个ECS实例
# 配置SLB后端服务器池
# 配置健康检查
```

### 2. 数据库集成

如需数据持久化，可集成阿里云RDS：
```yaml
# 在docker-compose中添加数据库配置
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 3. 监控告警

集成阿里云云监控：
- 配置ECS监控指标
- 设置告警规则
- 配置通知方式

---

**部署完成后，您的API将在以下地址可用：**
- HTTP: `http://your-ecs-ip/api/trending`
- HTTPS: `https://your-domain.com/api/trending`
- API文档: `http://your-domain.com/docs`