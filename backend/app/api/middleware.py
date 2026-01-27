"""
API Middleware

CORS, 错误处理, 日志记录
"""

import time
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_middleware(app: FastAPI):
    """
    设置所有中间件

    Args:
        app: FastAPI 应用实例
    """
    # CORS
    setup_cors(app)

    # 错误处理
    setup_error_handlers(app)

    # 请求日志
    setup_request_logging(app)


def setup_cors(app: FastAPI):
    """
    设置 CORS 中间件

    允许前端跨域访问 API
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:5173",  # Vite dev server
            "http://localhost:8080",
            # 生产环境需要添加实际域名
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    logger.info("CORS middleware configured")


def setup_error_handlers(app: FastAPI):
    """
    设置全局错误处理器
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """处理 HTTP 异常"""
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail} | Path: {request.url.path}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTPException",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证错误"""
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error["loc"],
                "msg": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Validation error: {errors} | Path: {request.url.path}"
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "ValidationError",
                    "message": "Request validation failed",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理未捕获的异常"""
        error_traceback = traceback.format_exc()

        logger.error(
            f"Unhandled exception: {str(exc)} | Path: {request.url.path}\n{error_traceback}"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": type(exc).__name__,
                    "message": "Internal server error",
                    # 生产环境不要暴露详细错误信息
                    # "detail": str(exc),
                }
            },
        )

    logger.info("Error handlers configured")


def setup_request_logging(app: FastAPI):
    """
    设置请求日志中间件
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录所有请求"""
        start_time = time.time()

        # 记录请求
        logger.info(
            f"→ {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应
            logger.info(
                f"← {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            logger.error(
                f"✗ {request.method} {request.url.path} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s"
            )

            raise

    logger.info("Request logging middleware configured")
