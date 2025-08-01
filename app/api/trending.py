# -*- coding: utf-8 -*-
"""
Trending API路由模块

提供GitHub trending相关的API端点。
包括获取trending仓库列表、支持的语言列表等功能。
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger

from app.crawler.github_crawler import GitHubTrendingCrawler
from app.schemas.trending import (
    TrendingResponse,
    TrendingRepository,
    TrendingQuery,
    ErrorResponse,
    HealthResponse
)
from app.config import get_settings

settings = get_settings()

# 创建路由器
router = APIRouter(
    prefix="/trending",
    tags=["trending"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    }
)

# 全局爬虫实例
crawler = GitHubTrendingCrawler()


def get_crawler() -> GitHubTrendingCrawler:
    """获取爬虫实例
    
    依赖注入函数，用于获取爬虫实例。
    
    Returns:
        GitHubTrendingCrawler: 爬虫实例
    """
    return crawler


@router.get(
    "/languages/supported",
    response_model=List[str],
    summary="获取支持的编程语言列表",
    description="获取GitHub trending支持的编程语言列表"
)
async def get_supported_languages(
    crawler: GitHubTrendingCrawler = Depends(get_crawler)
) -> List[str]:
    """获取支持的编程语言列表
    
    Args:
        crawler: 爬虫实例
        
    Returns:
        List[str]: 支持的编程语言列表
    """
    try:
        languages = await crawler.get_supported_languages()
        logger.info(f"返回 {len(languages)} 种支持的编程语言")
        return languages
        
    except Exception as e:
        logger.error(f"获取支持语言列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "LANGUAGE_ERROR",
                "message": "Failed to fetch supported languages",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get(
    "/",
    response_model=TrendingResponse,
    summary="获取GitHub trending仓库",
    description="获取GitHub trending仓库列表，支持按编程语言和时间范围筛选"
)
async def get_trending(
    language: Optional[str] = Query(
        None, 
        description="编程语言筛选，如：python, javascript, go等",
        example="python"
    ),
    since: str = Query(
        "daily",
        pattern="^(daily|weekly|monthly)$",
        description="时间范围：daily(今日), weekly(本周), monthly(本月)",
        example="daily"
    ),
    limit: int = Query(
        25,
        ge=1,
        le=100,
        description="返回数量限制，最大100",
        example=25
    ),
    crawler: GitHubTrendingCrawler = Depends(get_crawler)
) -> TrendingResponse:
    """获取GitHub trending仓库列表
    
    Args:
        language: 编程语言筛选
        since: 时间范围
        limit: 返回数量限制
        crawler: 爬虫实例
        
    Returns:
        TrendingResponse: trending仓库响应
        
    Raises:
        HTTPException: 爬取失败时抛出HTTP异常
    """
    try:
        logger.info(f"开始获取trending数据: language={language}, since={since}, limit={limit}")
        
        # 爬取数据
        repositories = await crawler.fetch_trending(
            language=language,
            since=since,
            limit=limit
        )
        
        # 构建响应
        response = TrendingResponse(
            success=True,
            repositories=repositories,
            total_count=len(repositories),
            language=language,
            since=since,
            crawled_at=datetime.now()
        )
        
        logger.info(f"成功返回 {len(repositories)} 个trending仓库")
        return response
        
    except Exception as e:
        logger.error(f"获取trending数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "CRAWL_ERROR",
                "message": "Failed to fetch trending data",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查trending服务的健康状态"
)
async def health_check(
    crawler: GitHubTrendingCrawler = Depends(get_crawler)
) -> HealthResponse:
    """健康检查端点
    
    Args:
        crawler: 爬虫实例
        
    Returns:
        HealthResponse: 健康状态响应
    """
    try:
        # 检查爬虫健康状态
        crawler_health = await crawler.health_check()
        
        status = "healthy" if crawler_health.get('github_accessible', False) else "unhealthy"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now(),
            version=settings.app_version,
            uptime=None  # 可以添加应用启动时间计算
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version=settings.app_version,
            uptime=None
        )


@router.post(
    "/refresh",
    response_model=TrendingResponse,
    summary="手动刷新trending数据",
    description="手动触发trending数据刷新，立即获取最新数据"
)
async def refresh_trending(
    query: TrendingQuery,
    crawler: GitHubTrendingCrawler = Depends(get_crawler)
) -> TrendingResponse:
    """手动刷新trending数据
    
    Args:
        query: 查询参数
        crawler: 爬虫实例
        
    Returns:
        TrendingResponse: 刷新后的trending数据
    """
    logger.info(f"手动刷新trending数据: {query.dict()}")
    
    return await get_trending(
        language=query.language,
        since=query.since,
        limit=query.limit,
        crawler=crawler
    )


@router.get(
    "/{language}",
    response_model=TrendingResponse,
    summary="获取指定语言的trending仓库",
    description="获取指定编程语言的GitHub trending仓库列表"
)
async def get_trending_by_language(
    language: str,
    since: str = Query(default="daily", description="时间范围: daily, weekly, monthly"),
    limit: Optional[int] = Query(default=None, description="返回结果数量限制"),
    crawler: GitHubTrendingCrawler = Depends(get_crawler)
) -> TrendingResponse:
    """获取指定语言的trending仓库
    
    Args:
        language: 编程语言
        since: 时间范围
        limit: 结果数量限制
        crawler: 爬虫实例
        
    Returns:
        TrendingResponse: trending数据响应
    """
    return await get_trending(
        language=language,
        since=since,
        limit=limit,
        crawler=crawler
    )