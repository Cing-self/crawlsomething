#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目启动脚本

用于启动GitHub Trending爬虫后端服务
"""

import uvicorn
from app.config import get_settings

def main():
    """主函数"""
    settings = get_settings()
    
    print(f"🚀 启动 {settings.app_name} v{settings.app_version}")
    print(f"🌐 服务地址: http://{settings.host}:{settings.port}")
    print(f"📚 API文档: http://{settings.host}:{settings.port}{settings.docs_url}")
    print(f"🔧 环境: {settings.environment}")
    print("-" * 50)
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()