# -*- coding: utf-8 -*-
"""
配置管理模块

使用Pydantic Settings管理应用配置，支持从环境变量和.env文件读取配置。
包含数据库、爬虫、API、日志等各模块的配置项。
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类
    
    使用Pydantic Settings自动从环境变量和.env文件加载配置。
    所有配置项都有合理的默认值。
    """
    
    # 应用基础配置
    app_name: str = Field(default="GitHub Trending Crawler", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="production", description="运行环境")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # 爬虫配置
    # crawl_interval_minutes: int = Field(default=60, description="爬虫执行间隔（分钟）")  # 不需要定时爬取
    request_timeout: int = Field(default=30, description="HTTP请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    request_delay: float = Field(default=5.0, description="请求间隔延迟（秒）")
    min_delay: float = Field(default=3.0, description="最小随机延迟（秒）")
    max_delay: float = Field(default=8.0, description="最大随机延迟（秒）")
    
    # GitHub配置
    github_base_url: str = Field(
        default="https://github.com", 
        description="GitHub基础URL"
    )
    github_trending_url: str = Field(
        default="https://github.com/trending", 
        description="GitHub Trending页面URL"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="HTTP请求User-Agent"
    )
    
    # API配置
    api_prefix: str = Field(default="/api", description="API路径前缀")
    docs_url: str = Field(default="/docs", description="API文档URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc文档URL")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/app.log", description="日志文件路径")
    log_rotation: str = Field(default="1 day", description="日志轮转周期")
    log_retention: str = Field(default="30 days", description="日志保留时间")
    
    # 缓存配置
    cache_ttl_seconds: int = Field(default=3600, description="缓存TTL（秒）")
    
    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="应用密钥"
    )
    access_token_expire_minutes: int = Field(
        default=30, 
        description="访问令牌过期时间（分钟）"
    )
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


def is_development() -> bool:
    """判断是否为开发环境
    
    Returns:
        bool: 是否为开发环境
    """
    return settings.environment.lower() in ["development", "dev"]


def is_production() -> bool:
    """判断是否为生产环境
    
    Returns:
        bool: 是否为生产环境
    """
    return settings.environment.lower() in ["production", "prod"]