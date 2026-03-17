"""
Structured logging configuration using structlog.

Provides:
- configure_logging(): call once at startup
- get_logger(): returns a bound structlog logger
- RequestLoggingMiddleware: ASGI middleware that logs every request/response
"""

from __future__ import annotations

import logging
import time
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog for JSON output in production and pretty output in dev.

    Should be called once, during application startup.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger."""
    return structlog.get_logger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that logs HTTP request metadata and timing.

    Logs: method, path, status_code, duration_ms, client IP.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = structlog.get_logger("request")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self._logger.exception(
                "Unhandled exception",
                duration_ms=duration_ms,
                exc=str(exc),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = self._logger.info if response.status_code < 400 else self._logger.warning
        log(
            "Request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        structlog.contextvars.clear_contextvars()
        return response
