# Docker构建问题修复指南

## 问题描述
构建Docker镜像时遇到以下问题：
1. 清华大学TUNA镜像站阻断了大量下载请求（HTTP 403错误）
2. Docker Hub连接超时

## 解决方案

### 1. 已修复的问题
- ✅ 移除了有问题的清华大学TUNA pip镜像源
- ✅ 添加了多个备选pip镜像源（豆瓣、阿里云、中科大）
- ✅ 使用容错机制，如果一个源失败会自动尝试下一个

### 2. Docker镜像加速器配置（推荐）

#### macOS用户：
1. 打开Docker Desktop
2. 点击设置图标（齿轮）
3. 选择"Docker Engine"
4. 将以下配置添加到JSON配置中：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

5. 点击"Apply & Restart"

#### Linux用户：
1. 创建或编辑文件 `/etc/docker/daemon.json`
2. 添加以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

3. 重启Docker服务：
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 3. 重新构建
配置完成后，重新运行构建命令：

```bash
docker-compose build
```

### 4. 备选方案
如果仍然有网络问题，可以尝试：

1. **使用代理**：
```bash
docker build --build-arg HTTP_PROXY=http://your-proxy:port --build-arg HTTPS_PROXY=http://your-proxy:port .
```

2. **手动拉取基础镜像**：
```bash
docker pull python:3.9-slim
docker-compose build
```

3. **使用本地构建**：
如果Docker问题持续，可以直接在本地运行：
```bash
pip install -r requirements.txt
python run.py
```

## 验证修复
构建成功后，可以运行以下命令验证：

```bash
docker-compose up -d
curl http://localhost:8000/
```

应该看到API正常响应。