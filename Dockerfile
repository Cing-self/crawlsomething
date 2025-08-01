# GitHub Trending Crawler API - Docker配置文件
# 基于Python 3.9的轻量级镜像构建FastAPI应用容器

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 更换为阿里云镜像源以提高下载速度（兼容新版Debian）
RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list; \
    fi && \
    if [ -d /etc/apt/sources.list.d ]; then \
        find /etc/apt/sources.list.d -name "*.list" -exec sed -i 's/deb.debian.org/mirrors.aliyun.com/g' {} \; && \
        find /etc/apt/sources.list.d -name "*.list" -exec sed -i 's/security.debian.org/mirrors.aliyun.com/g' {} \; ; \
    fi

# 安装系统依赖（添加重试机制和多个镜像源备选）
RUN for i in 1 2 3; do \
        apt-get update && apt-get install -y \
            gcc \
            curl \
        && rm -rf /var/lib/apt/lists/* && break || \
        (echo "Attempt $i failed, trying alternative sources..." && \
         if [ -f /etc/apt/sources.list ]; then \
             sed -i 's/mirrors.aliyun.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list; \
         fi && \
         if [ -d /etc/apt/sources.list.d ]; then \
             find /etc/apt/sources.list.d -name "*.list" -exec sed -i 's/mirrors.aliyun.com/mirrors.tuna.tsinghua.edu.cn/g' {} \; ; \
         fi && \
         sleep 5); \
    done

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app

# 创建日志目录并设置权限（确保在用户创建后）
RUN mkdir -p /app/logs \
    && chown -R app:app /app \
    && chmod -R 755 /app/logs

# 切换到非root用户
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]