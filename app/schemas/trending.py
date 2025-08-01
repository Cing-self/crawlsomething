# -*- coding: utf-8 -*-
"""
Trending相关的Pydantic模式

定义用于API请求和响应的数据模型，包括验证规则和示例数据。
这些模型确保API的输入输出数据格式正确且一致。
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class TrendingRepository(BaseModel):
    """GitHub trending仓库数据模型
    
    用于API响应中的单个仓库信息。
    """
    
    # 基本信息
    name: str = Field(..., description="仓库名称，格式：owner/repo")
    url: HttpUrl = Field(..., description="仓库URL")
    description: Optional[str] = Field(None, description="仓库描述")
    
    # 统计信息
    stars: int = Field(default=0, description="总星标数量")
    forks: int = Field(default=0, description="Fork数量")
    language: Optional[str] = Field(None, description="主要编程语言")
    language_color: Optional[str] = Field(None, description="编程语言颜色")
    
    # Trending特有信息
    stars_today: int = Field(default=0, description="今日新增星标数")
    period_stars: int = Field(default=0, description="指定周期内新增星标数")
    
    # 仓库详细信息
    owner: str = Field(..., description="仓库所有者")
    repo_name: str = Field(..., description="仓库名")
    avatar_url: Optional[HttpUrl] = Field(None, description="所有者头像URL")
    
    # 时间信息
    crawled_at: datetime = Field(default_factory=datetime.now, description="爬取时间")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "name": "microsoft/vscode",
                "url": "https://github.com/microsoft/vscode",
                "description": "Visual Studio Code",
                "stars": 150000,
                "forks": 25000,
                "language": "TypeScript",
                "language_color": "#3178c6",
                "stars_today": 120,
                "period_stars": 120,
                "owner": "microsoft",
                "repo_name": "vscode",
                "avatar_url": "https://avatars.githubusercontent.com/u/6154722?v=4",
                "crawled_at": "2024-01-01T12:00:00"
            }
        }


class TrendingResponse(BaseModel):
    """Trending API响应模型
    
    包装trending仓库列表和相关元数据。
    """
    
    success: bool = Field(default=True, description="请求是否成功")
    repositories: List[TrendingRepository] = Field(..., description="trending仓库列表")
    total_count: int = Field(..., description="返回的仓库数量")
    language: Optional[str] = Field(None, description="筛选的编程语言")
    since: str = Field(default="daily", description="时间范围")
    crawled_at: datetime = Field(default_factory=datetime.now, description="爬取时间")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "success": True,
                "repositories": [],
                "total_count": 25,
                "language": "python",
                "since": "daily",
                "crawled_at": "2024-01-01T12:00:00"
            }
        }


class TrendingQuery(BaseModel):
    """Trending查询参数模型
    
    定义API查询参数的验证规则和默认值。
    """
    
    language: Optional[str] = Field(
        None, 
        description="编程语言筛选，如：python, javascript, go等",
        example="python"
    )
    since: str = Field(
        default="daily",
        description="时间范围：daily(今日), weekly(本周), monthly(本月)",
        pattern="^(daily|weekly|monthly)$",
        example="daily"
    )
    limit: int = Field(
        default=25,
        ge=1,
        le=100,
        description="返回数量限制，最大100"
    )
    
    class Config:
        """Pydantic配置"""
        schema_extra = {
            "example": {
                "language": "python",
                "since": "daily",
                "limit": 25
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型
    
    统一的错误响应格式。
    """
    
    success: bool = Field(default=False, description="请求是否成功")
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "success": False,
                "error": "CRAWL_ERROR",
                "message": "Failed to fetch trending data",
                "detail": "Network timeout after 30 seconds",
                "timestamp": "2024-01-01T12:00:00"
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应模型
    
    用于服务健康状态检查。
    """
    
    status: str = Field(default="healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field(..., description="应用版本")
    uptime: Optional[float] = Field(None, description="运行时间（秒）")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00",
                "version": "1.0.0",
                "uptime": 3600.5
            }
        }