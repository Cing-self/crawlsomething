# -*- coding: utf-8 -*-
"""
API路由包

包含所有FastAPI路由定义。
每个模块对应一组相关的API端点。
"""

from app.api.trending import router as trending_router

__all__ = [
    "trending_router",
]