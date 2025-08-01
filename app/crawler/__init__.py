# -*- coding: utf-8 -*-
"""
爬虫模块包

包含GitHub trending数据爬取的核心逻辑。
提供异步爬虫功能，支持多种时间范围和编程语言筛选。
"""

from app.crawler.github_crawler import GitHubTrendingCrawler

__all__ = [
    "GitHubTrendingCrawler",
]