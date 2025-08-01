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

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. 启动服务
```bash
uvicorn app.main:app --reload
```

4. 访问API文档
```
http://localhost:8000/docs
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

## 部署

支持Docker部署，详见项目中的Dockerfile和docker-compose.yml文件。

## 许可证

MIT License