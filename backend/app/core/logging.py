"""
Structured logging configuration using structlog.
All logs include trace_id for request tracing.
"""
import logging
import sys
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, MutableMapping

import structlog

from app.core.config import settings

# Context variable for request tracing
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)

Processor = Callable[
    [Any, str, MutableMapping[str, Any]],
    MutableMapping[str, Any] | str | bytes | bytearray | tuple[Any, ...],
]


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return request_id_ctx_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    request_id_ctx_var.set(request_id)


def add_request_id(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Add request_id to log records."""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request_id to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'request_id'):
            record.request_id = get_request_id() or "-"
        return True


class RequestIdFormatter(logging.Formatter):
    """Custom formatter that includes request_id."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'request_id'):
            record.request_id = get_request_id() or "-"
        return super().format(record)


def configure_logging() -> None:
    """Configure structlog for structured logging."""

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create custom formatter with request_id for standard library logs
    std_formatter = RequestIdFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root handler for non-structlog loggers
    std_handler = logging.StreamHandler(sys.stdout)
    std_handler.setFormatter(std_formatter)
    std_handler.setLevel(log_level)

    # Configure sqlalchemy to use standard format with request_id
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
    sqlalchemy_logger.handlers = []
    sqlalchemy_logger.addHandler(std_handler)
    sqlalchemy_logger.setLevel(log_level)
    sqlalchemy_logger.propagate = False

    # Disable uvicorn access logger since we use APILoggingMiddleware with request_id
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []
    uvicorn_access.disabled = True
    uvicorn_access.propagate = False

    # Configure structlog processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # For structlog's output
    if settings.ENVIRONMENT == "production":
        final_processors: list[Processor] = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        final_processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        ]

    # Configure structlog to output directly to stdout
    structlog.configure(
        processors=final_processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set root logger level
    logging.getLogger().setLevel(log_level)


# Initialize logging on import
configure_logging()

# Export logger getter
get_logger = structlog.get_logger
