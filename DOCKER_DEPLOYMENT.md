# GitHub Trending Crawler - Docker部署指南

本文档提供了GitHub Trending爬虫API的完整Docker容器化部署方案。

## 📋 部署前准备

### 系统要求
- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少2GB可用内存
- 至少5GB可用磁盘空间

### 安装Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install --cask docker
```

## 🚀 快速部署

### 方式一：仅API服务

```bash
# 1. 克隆项目
git clone https://github.com/Cing-self/crawlsomething.git
cd crawlsomething

# 2. 构建镜像
docker build -t github-trending-crawler .

# 3. 运行容器
docker run -d \
  --name crawler-api \
  -p 8000:8000 \
  --restart unless-stopped \
  github-trending-crawler
```

### 方式二：完整服务栈（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Cing-self/crawlsomething.git
cd crawlsomething

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

## 🔧 配置选项

### 环境变量

在`docker-compose.yml`中可以配置以下环境变量：

```yaml
environment:
  - LOG_LEVEL=INFO          # 日志级别: DEBUG, INFO, WARNING, ERROR
  - PYTHONPATH=/app         # Python路径
  - REQUEST_TIMEOUT=30      # 请求超时时间（秒）
  - MAX_RETRIES=3          # 最大重试次数
```

### 端口配置

- **API服务**: 8000端口
- **Nginx代理**: 80端口（HTTP）、443端口（HTTPS）

### 数据持久化

```yaml
volumes:
  - ./logs:/app/logs        # 日志持久化
  - ./data:/app/data        # 数据持久化（如果需要）
```

## 🌐 生产环境部署

### 1. 安全配置

**创建环境变量文件：**
```bash
# .env
LOG_LEVEL=WARNING
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

**更新docker-compose.yml：**
```yaml
services:
  crawlsomething:
    env_file:
      - .env
```

### 2. HTTPS配置

**生成SSL证书：**
```bash
# 创建SSL目录
mkdir -p ssl

# 使用Let's Encrypt（推荐）
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# 或生成自签名证书（仅测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem
```

**启用HTTPS：**
在`nginx.conf`中取消注释HTTPS服务器配置块。

### 3. 负载均衡

**多实例部署：**
```yaml
services:
  crawlsomething:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

## 📊 监控和维护

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f crawlsomething

# 查看最近100行日志
docker-compose logs --tail=100 crawlsomething
```

### 健康检查

```bash
# 检查容器状态
docker-compose ps

# 检查API健康状态
curl http://localhost:8000/

# 检查通过Nginx的访问
curl http://localhost/
```

### 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

## 🔍 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 查看端口占用
sudo netstat -tlnp | grep :8000

# 修改端口映射
# 在docker-compose.yml中修改ports配置
```

**2. 容器启动失败**
```bash
# 查看详细错误信息
docker-compose logs crawlsomething

# 检查容器状态
docker inspect crawlsomething
```

**3. 网络连接问题**
```bash
# 检查Docker网络
docker network ls
docker network inspect crawlsomething_crawler-network

# 测试容器间连接
docker-compose exec nginx ping crawlsomething
```

### 性能优化

**1. 资源限制**
```yaml
services:
  crawlsomething:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**2. 缓存优化**
```bash
# 启用Docker BuildKit
export DOCKER_BUILDKIT=1

# 使用多阶段构建缓存
docker build --cache-from github-trending-crawler:latest .
```

## 📝 API使用示例

部署完成后，可以通过以下方式访问API：

```bash
# 获取GitHub Trending项目
curl "http://localhost/api/trending?language=python&since=daily"

# 通过Nginx代理访问
curl "http://localhost/api/trending?language=javascript&since=weekly"

# HTTPS访问（如果配置了SSL）
curl "https://your-domain.com/api/trending?language=go&since=monthly"
```

## 🛡️ 安全建议

1. **定期更新镜像**：保持基础镜像和依赖包的最新版本
2. **使用非root用户**：Dockerfile中已配置非root用户运行
3. **网络隔离**：使用自定义Docker网络
4. **资源限制**：设置合适的CPU和内存限制
5. **日志管理**：配置日志轮转，避免磁盘空间耗尽
6. **防火墙配置**：仅开放必要的端口

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的GitHub Issues
3. 提交新的Issue并附上详细的错误信息和环境描述

---

**部署成功后，您的GitHub Trending爬虫API将在以下地址可用：**
- API直接访问：http://localhost:8000
- Nginx代理访问：http://localhost
- API文档：http://localhost:8000/docs