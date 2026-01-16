"""FastAPI integration for request-scoped logging."""

import time
import uuid
from contextvars import ContextVar
from typing import Callable

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError:
    # FastAPI/Starlette not installed
    BaseHTTPMiddleware = object  # type: ignore
    Request = None  # type: ignore
    Response = None  # type: ignore

from ..logger import get_logger, Logger

# Request-scoped logger storage
_request_logger: ContextVar[Logger | None] = ContextVar("request_logger", default=None)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation ID and request logging.

    Features:
    - Extracts or generates correlation ID
    - Creates request-scoped logger
    - Logs request start and completion
    - Logs request duration
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging context."""
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Get logger with correlation ID
        logger = get_logger("fastapi").with_context(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        # Store in context var for access in route handlers
        _request_logger.set(logger)

        # Log request start
        start_time = time.perf_counter()
        logger.info("Request started")

        try:
            # Process request
            response = await call_next(request)

            # Log request completion
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Log error
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                exception=exc,
                duration_ms=duration_ms,
            )
            raise

        finally:
            # Clear context var
            _request_logger.set(None)


def get_request_logger() -> Logger:
    """
    Get the request-scoped logger.

    Returns the logger with correlation ID and request context.
    Must be called within a request context (after middleware).
    """
    logger = _request_logger.get()
    if logger is None:
        # Fallback to root logger if not in request context
        return get_logger("fastapi")
    return logger
