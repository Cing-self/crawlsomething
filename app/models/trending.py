# -*- coding: utf-8 -*-
"""
Trending数据模型

定义GitHub trending仓库的数据结构，用于API响应。
不涉及数据库存储，仅作为数据传输对象(DTO)。
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class TrendingRepository(BaseModel):
    """GitHub trending仓库数据模型
    
    用于表示从GitHub trending页面爬取的仓库信息。
    """
    
    # 基本信息
    name: str = Field(..., description="仓库名称，格式：owner/repo")
    url: HttpUrl = Field(..., description="仓库URL")
    description: Optional[str] = Field(None, description="仓库描述")
    
    # 统计信息
    stars: int = Field(default=0, description="星标数量")
    forks: int = Field(default=0, description="Fork数量")
    language: Optional[str] = Field(None, description="主要编程语言")
    
    # Trending特有信息
    stars_today: int = Field(default=0, description="今日新增星标数")
    period_stars: int = Field(default=0, description="指定周期内新增星标数")
    
    # 额外信息
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
    
    包装trending仓库列表和元数据信息。
    """
    
    repositories: List[TrendingRepository] = Field(..., description="trending仓库列表")
    total_count: int = Field(..., description="总数量")
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
                "repositories": [],
                "total_count": 25,
                "language": "python",
                "since": "daily",
                "crawled_at": "2024-01-01T12:00:00"
            }
        }


class TrendingQuery(BaseModel):
    """Trending查询参数模型
    
    定义API查询参数的验证规则。
    """
    
    language: Optional[str] = Field(
        None, 
        description="编程语言筛选",
        example="python"
    )
    since: str = Field(
        default="daily",
        description="时间范围",
        regex="^(daily|weekly|monthly)$",
        example="daily"
    )
    limit: int = Field(
        default=25,
        ge=1,
        le=100,
        description="返回数量限制"
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