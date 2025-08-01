# -*- coding: utf-8 -*-
"""
Pydantic模式包

包含所有用于API请求和响应的Pydantic模型。
这些模型用于数据验证、序列化和API文档生成。
"""

from app.schemas.trending import (
    TrendingRepository,
    TrendingResponse,
    TrendingQuery,
    ErrorResponse
)

__all__ = [
    "TrendingRepository",
    "TrendingResponse", 
    "TrendingQuery",
    "ErrorResponse"
]