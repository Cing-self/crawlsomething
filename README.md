# GitHub Trending 爬虫后端服务

一个用于获取和提供GitHub trending数据的后端API服务。

## 功能特性

- 🚀 实时爬取GitHub trending页面数据
- 📊 提供RESTful API接口
- 🔄 支持多种时间范围（daily, weekly, monthly）
- 🏷️ 支持按编程语言筛选
- ⚡ 高性能异步处理
- 📝 完整的API文档
- 🎯 无需数据库，直接返回最新数据
- 🛡️ 反爬虫优化：随机延迟、User-Agent轮换、智能重试
- 🔄 指数退避重试机制，避免GitHub频率限制
- 🎭 多浏览器User-Agent模拟，提高爬取成功率

## 技术栈

- **Web框架**: FastAPI
- **异步HTTP客户端**: aiohttp
- **HTML解析**: BeautifulSoup4
- **数据验证**: Pydantic
- **日志**: loguru
- **环境管理**: python-dotenv

## 项目结构

```
crawlsomething/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── trending.py
│   ├── schemas/             # Pydantic模式
│   │   ├── __init__.py
│   │   └── trending.py
│   ├── api/                 # API路由
│   │   ├── __init__.py
│   │   └── trending.py
│   ├── crawler/             # 爬虫模块
│   │   ├── __init__.py
│   │   └── github_crawler.py
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── logger.py
├── requirements.txt         # 依赖包
├── .env                     # 环境变量
├── .gitignore
└── README.md
```

## 部署指南

### 本地部署

#### 方式一：直接运行

**系统要求**
- Python 3.8+
- Git

**环境准备**

<details>
<summary>Windows 系统</summary>

1. **安装 Python**
   - 访问 [Python官网](https://www.python.org/downloads/) 下载最新版本
   - 安装时勾选 "Add Python to PATH"
   - 验证安装：
   ```cmd
   python --version
   pip --version
   ```

2. **安装 Git**
   - 访问 [Git官网](https://git-scm.com/download/win) 下载安装包
   - 使用默认配置安装
   - 验证安装：
   ```cmd
   git --version
   ```

</details>

<details>
<summary>Linux/macOS 系统</summary>

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip git

# CentOS/RHEL
sudo yum install python3 python3-pip git

# macOS (使用 Homebrew)
brew install python git
```

</details>

**部署步骤**

1. **克隆项目**
```bash
git clone <repository-url>
cd crawlsomething
```

2. **创建虚拟环境**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# Linux/macOS
cp .env.example .env

# Windows
copy .env.example .env
```

5. **启动服务**
```bash
uvicorn app.main:app --reload
```

6. **访问服务**
- API服务：http://localhost:8000
- API文档：http://localhost:8000/docs

#### 方式二：Docker 容器

**系统要求**
- Docker
- Docker Compose

**Docker 安装**

<details>
<summary>Windows 系统</summary>

1. **系统要求**
   - Windows 10 64位：专业版、企业版或教育版（版本1903或更高）
   - Windows 11 64位：家庭版或专业版
   - 启用 WSL 2 功能

2. **启用 WSL 2**
   ```powershell
   # 以管理员身份运行 PowerShell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   
   # 重启计算机后，设置 WSL 2 为默认版本
   wsl --set-default-version 2
   ```

3. **安装 Docker Desktop**
   - 访问 [Docker Desktop官网](https://www.docker.com/products/docker-desktop) 下载
   - 运行安装程序，使用默认设置
   - 安装完成后重启计算机
   - 启动 Docker Desktop 并完成初始配置

4. **验证安装**
   ```cmd
   docker --version
   docker-compose --version
   ```

</details>

<details>
<summary>Linux 系统</summary>

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo yum install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

</details>

<details>
<summary>macOS 系统</summary>

```bash
# 使用 Homebrew
brew install --cask docker

# 或者下载 Docker Desktop for Mac
# https://www.docker.com/products/docker-desktop
```

</details>

**部署步骤**

1. **克隆项目**
```bash
git clone <repository-url>
cd crawlsomething
```

2. **启动服务**
```bash
docker-compose up -d
```

> **Windows 用户提示**：
> - 请在 PowerShell 或 Git Bash 中运行上述命令
> - 确保 Docker Desktop 正在运行
> - 首次运行可能需要较长时间下载镜像
> - 如果遇到 `No such file or directory` 错误，说明镜像源配置问题，已在最新版本修复

3. **查看服务状态**
```bash
docker-compose ps
```

4. **查看日志**
```bash
docker-compose logs -f
```

**访问地址**
- API服务：http://localhost:8000
- Nginx代理：http://localhost:80
- API文档：http://localhost:8000/docs

**常用命令**
```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新服务
docker-compose pull
docker-compose up -d

# 查看日志
docker-compose logs -f [service_name]
```

## API接口

### 主要接口

- `GET /api/trending` - 获取trending仓库列表（实时爬取）
- `GET /api/trending/{language}` - 获取指定语言的trending仓库
- `GET /api/languages` - 获取支持的编程语言列表
- `POST /api/refresh` - 手动刷新trending数据
- `GET /health` - 健康检查

### 查询参数
- `since`: 时间范围 (daily, weekly, monthly)
- `limit`: 返回数量限制
- `offset`: 分页偏移

### 云端部署

#### 阿里云一键部署

**系统要求**
- 阿里云ECS实例（推荐配置：2核4GB内存）
- CentOS 7+ 或 Ubuntu 18.04+
- 已安装Docker和Docker Compose

**特色功能**
- 🚀 一键部署脚本，自动配置环境
- 🔧 自动安装Docker和依赖
- 🌐 自动配置Nginx反向代理
- 🔒 SSL证书自动申请和配置
- 📊 系统监控和日志管理
- 🔄 自动备份和更新机制

**一键部署**
```bash
# 下载并运行部署脚本
wget -O deploy.sh https://raw.githubusercontent.com/your-repo/crawlsomething/main/deploy-aliyun.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

部署脚本将自动完成以下操作：
1. 检查系统环境和依赖
2. 安装Docker和Docker Compose
3. 克隆项目代码
4. 配置环境变量
5. 启动服务容器
6. 配置Nginx反向代理
7. 设置防火墙规则
8. 配置系统服务自启动

## 许可证

MIT License