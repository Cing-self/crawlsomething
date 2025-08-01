# -*- coding: utf-8 -*-
"""
日志配置模块

使用loguru库配置应用日志系统。
支持文件日志、控制台日志、日志轮转和格式化。
"""

import sys
import os
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import get_settings

settings = get_settings()


def setup_logger(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    rotation: Optional[str] = None,
    retention: Optional[str] = None
) -> None:
    """配置日志系统
    
    Args:
        log_level: 日志级别，默认从配置读取
        log_file: 日志文件路径，默认从配置读取
        rotation: 日志轮转规则，默认从配置读取
        retention: 日志保留时间，默认从配置读取
    """
    # 使用配置中的默认值
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    rotation = rotation or settings.log_rotation
    retention = retention or settings.log_retention
    
    # 移除默认的控制台处理器
    logger.remove()
    
    # 添加控制台日志处理器
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 添加文件日志处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        logger.add(
            log_file,
            format=file_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
    
    # 设置第三方库的日志级别
    _configure_third_party_loggers()
    
    logger.info(f"日志系统初始化完成 - 级别: {log_level}, 文件: {log_file}")


def _configure_third_party_loggers() -> None:
    """配置第三方库的日志级别
    
    降低第三方库的日志噪音。
    """
    import logging
    
    # 设置第三方库日志级别
    third_party_loggers = [
        'aiohttp.access',
        'aiohttp.client',
        'aiohttp.internal',
        'aiohttp.server',
        'urllib3.connectionpool',
        'httpx',
        'httpcore',
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str = None):
    """获取日志记录器
    
    Args:
        name: 日志记录器名称，默认使用调用模块名
        
    Returns:
        loguru.Logger: 日志记录器实例
    """
    if name:
        return logger.bind(name=name)
    return logger


class LoggerMixin:
    """日志混入类
    
    为其他类提供日志功能。
    """
    
    @property
    def logger(self):
        """获取当前类的日志记录器
        
        Returns:
            loguru.Logger: 绑定到当前类的日志记录器
        """
        return logger.bind(name=self.__class__.__name__)


def log_function_call(func):
    """函数调用日志装饰器
    
    记录函数的调用和执行时间。
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_logger = logger.bind(function=func.__name__)
        
        func_logger.debug(f"开始执行函数: {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            func_logger.debug(f"函数执行完成: {func.__name__}, 耗时: {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            func_logger.error(f"函数执行失败: {func.__name__}, 耗时: {execution_time:.3f}s, 错误: {str(e)}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_logger = logger.bind(function=func.__name__)
        
        func_logger.debug(f"开始执行函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            func_logger.debug(f"函数执行完成: {func.__name__}, 耗时: {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            func_logger.error(f"函数执行失败: {func.__name__}, 耗时: {execution_time:.3f}s, 错误: {str(e)}")
            raise
    
    # 根据函数类型返回对应的包装器
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def create_request_id() -> str:
    """创建请求ID
    
    用于跟踪单个请求的日志。
    
    Returns:
        str: 唯一的请求ID
    """
    import uuid
    return str(uuid.uuid4())[:8]


class RequestLogger:
    """请求日志记录器
    
    为每个请求创建独立的日志上下文。
    """
    
    def __init__(self, request_id: str = None):
        """初始化请求日志记录器
        
        Args:
            request_id: 请求ID，如果不提供则自动生成
        """
        self.request_id = request_id or create_request_id()
        self.logger = logger.bind(request_id=self.request_id)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)