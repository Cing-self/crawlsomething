# -*- coding: utf-8 -*-
"""
FastAPI应用主入口文件

创建和配置FastAPI应用实例，注册路由、中间件和异常处理器。
这是整个应用的启动入口点。
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from app.config import get_settings
from app.utils.logger import setup_logger, RequestLogger
from app.api.trending import router as trending_router
from app.schemas.trending import ErrorResponse

settings = get_settings()

# 应用启动时间
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    处理应用启动和关闭时的初始化和清理工作。
    
    Args:
        app: FastAPI应用实例
    """
    # 启动时执行
    logger.info("🚀 应用启动中...")
    
    # 初始化日志系统
    setup_logger()
    logger.info("📝 日志系统初始化完成")
    
    # 应用启动完成
    logger.info(f"✅ {settings.app_name} v{settings.app_version} 启动完成")
    logger.info(f"🌐 服务地址: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API文档: http://{settings.host}:{settings.port}{settings.docs_url}")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 应用关闭中...")
    logger.info("👋 应用已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="一个用于获取GitHub trending数据的后端API服务",
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
    debug=settings.debug
)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件
    
    记录每个HTTP请求的详细信息和响应时间。
    
    Args:
        request: HTTP请求对象
        call_next: 下一个中间件或路由处理器
        
    Returns:
        HTTP响应
    """
    # 创建请求日志记录器
    request_logger = RequestLogger()
    
    # 记录请求开始
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    request_logger.info(
        f"📥 {request.method} {request.url.path} - IP: {client_ip}"
    )
    
    # 将请求日志记录器添加到请求状态中
    request.state.logger = request_logger
    
    try:
        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录响应
        request_logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"状态: {response.status_code}, 耗时: {process_time:.3f}s"
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_logger.request_id
        
        return response
        
    except Exception as e:
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录错误
        request_logger.error(
            f"❌ {request.method} {request.url.path} - "
            f"错误: {str(e)}, 耗时: {process_time:.3f}s"
        )
        
        # 重新抛出异常
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器
    
    统一处理HTTP异常，返回标准格式的错误响应。
    
    Args:
        request: HTTP请求对象
        exc: HTTP异常
        
    Returns:
        JSON错误响应
    """
    request_logger = getattr(request.state, 'logger', logger)
    
    request_logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器
    
    处理Pydantic模型验证失败的异常。
    
    Args:
        request: HTTP请求对象
        exc: 验证异常
        
    Returns:
        JSON错误响应
    """
    request_logger = getattr(request.state, 'logger', logger)
    
    request_logger.warning(f"请求验证失败: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": exc.errors(),
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器
    
    处理所有未被其他处理器捕获的异常。
    
    Args:
        request: HTTP请求对象
        exc: 异常对象
        
    Returns:
        JSON错误响应
    """
    request_logger = getattr(request.state, 'logger', logger)
    
    request_logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": time.time()
        }
    )


# 注册路由
app.include_router(
    trending_router,
    prefix=settings.api_prefix,
    tags=["trending"]
)


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """根路径端点
    
    返回应用基本信息。
    
    Returns:
        Dict[str, Any]: 应用信息
    """
    uptime = time.time() - start_time
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime": f"{uptime:.2f}s",
        "docs_url": settings.docs_url,
        "api_prefix": settings.api_prefix,
        "environment": settings.environment
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """健康检查端点
    
    检查应用的健康状态。
    
    Returns:
        Dict[str, Any]: 健康状态信息
    """
    uptime = time.time() - start_time
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": uptime,
        "version": settings.app_version,
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境直接运行
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )