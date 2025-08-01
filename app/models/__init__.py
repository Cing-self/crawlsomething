# -*- coding: utf-8 -*-
"""
数据模型包

包含所有SQLAlchemy数据模型定义。
每个模型对应数据库中的一个表。
"""

from app.models.trending import TrendingRepository

__all__ = [
    "TrendingRepository",
]