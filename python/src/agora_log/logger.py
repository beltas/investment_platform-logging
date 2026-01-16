"""Core logger implementation."""

from __future__ import annotations

import copy
import inspect
import os
import socket
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from types import FrameType
from typing import Any, Generator, Optional

from .config import LogConfig
from .level import LogLevel
from .handlers.base import Handler
from .handlers.console import ConsoleHandler
from .handlers.file import FileHandler
from .handlers.rotating import RotatingFileHandler
from .handlers.async_handler import AsyncHandler


@dataclass
class SourceLocation:
    """Captured source location information."""
    file: str
    line: int
    function: str


def _capture_source_location(stack_depth: int = 2) -> SourceLocation:
    """
    Capture the source location of the calling code.

    The file, line, and function fields are REQUIRED in all log entries.

    Args:
        stack_depth: Number of frames to go back in the call stack.

    Returns:
        SourceLocation with file, line, and function information.
    """
    frame: Optional[FrameType] = inspect.currentframe()
    try:
        for _ in range(stack_depth):
            if frame is None:
                break
            frame = frame.f_back

        if frame is None:
            return SourceLocation(
                file="<unknown>",
                line=0,
                function="<unknown>"
            )

        # Use os.path.basename for cross-platform compatibility
        filename = os.path.basename(frame.f_code.co_filename)
        return SourceLocation(
            file=filename,
            line=frame.f_lineno,
            function=frame.f_code.co_name
        )
    finally:
        del frame  # Prevent reference cycles


# Global state
_config: LogConfig | None = None
_loggers: dict[str, Logger] = {}
_hostname: str | None = None


def _get_hostname() -> str:
    """Get cached hostname."""
    global _hostname
    if _hostname is None:
        _hostname = socket.gethostname()
    return _hostname


class Logger:
    """
    Main logger class with automatic source location capture.
    
    The file, line, and function fields are REQUIRED in all log entries
    and are captured automatically.
    """
    
    def __init__(
        self,
        name: str,
        config: LogConfig,
        context: dict[str, Any] | None = None,
        handlers: list[Handler] | None = None
    ):
        self._name = name
        self._config = config
        self._context = context or {}
        self._handlers: list[Handler] = handlers or []
    
    @property
    def context(self) -> dict[str, Any]:
        """Get the current context."""
        return self._context.copy()
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        exception: BaseException | None = None,
        **kwargs: Any
    ) -> None:
        """Internal logging method that captures source location."""
        if level.value < self._config.level.value:
            return
        
        # Capture source location (REQUIRED)
        source = _capture_source_location(stack_depth=3)
        
        # Merge context and kwargs
        merged_context = {**self._context, **kwargs}

        # Build log entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.name,
            "message": message,
            "service": self._config.service_name,
            "environment": self._config.environment,
            "version": self._config.version,
            "host": _get_hostname(),
            "logger_name": self._name,
            # REQUIRED source location fields
            "file": source.file,
            "line": source.line,
            "function": source.function,
            # Merge context (will be filtered below)
            "context": merged_context.copy(),
        }

        # Promote special keys to top level
        special_keys = ["correlation_id", "user_id", "trace_id", "span_id"]
        for key in special_keys:
            if key in merged_context:
                entry[key] = merged_context[key]
                # Remove from context dict to avoid duplication
                del entry["context"][key]
        
        if exception:
            entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "stacktrace": "".join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )) if exception.__traceback__ else ""
            }

        # Emit to all handlers
        for handler in self._handlers:
            handler.emit(entry)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def error(
        self,
        message: str,
        exception: BaseException | None = None,
        **kwargs: Any
    ) -> None:
        """Log at ERROR level with optional exception."""
        self._log(LogLevel.ERROR, message, exception=exception, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def critical(
        self,
        message: str,
        exception: BaseException | None = None,
        **kwargs: Any
    ) -> None:
        """Log at CRITICAL level."""
        self._log(LogLevel.CRITICAL, message, exception=exception, **kwargs)
    
    def with_context(self, **kwargs: Any) -> Logger:
        """
        Create child logger with additional context.

        Uses deep copy to prevent mutation of nested context values
        from affecting the parent logger.

        Args:
            **kwargs: Additional context key-value pairs.

        Returns:
            New Logger instance with merged context.
        """
        # Deep copy existing context to prevent mutation issues
        new_context = copy.deepcopy(self._context)
        # Merge new kwargs (also deep copied for safety)
        for key, value in kwargs.items():
            new_context[key] = copy.deepcopy(value)
        return Logger(self._name, self._config, new_context, self._handlers)
    
    @contextmanager
    def timer(self, operation: str, **kwargs: Any) -> Generator[None, None, None]:
        """
        Context manager that logs operation duration.
        
        Usage:
            with logger.timer("Database query"):
                result = db.execute()
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._log(
                LogLevel.INFO,
                operation,
                duration_ms=duration_ms,
                **kwargs
            )


def initialize(config: LogConfig) -> Logger:
    """
    Initialize the logging system.

    Must be called once at application startup.
    """
    global _config
    _config = config

    # Create handlers based on configuration
    handlers: list[Handler] = []

    # Console handler
    if config.console_enabled:
        console_handler = ConsoleHandler(
            format=config.console_format,
            colors=config.console_colors
        )
        handlers.append(console_handler)

    # File handler (with or without rotation)
    if config.file_enabled:
        if config.max_file_size_mb > 0:
            # Rotating file handler
            file_handler: Handler = RotatingFileHandler(
                file_path=config.file_path,
                max_bytes=config.max_file_size_mb * 1024 * 1024,
                backup_count=config.max_backup_count
            )
        else:
            # Simple file handler
            file_handler = FileHandler(config.file_path)

        # Wrap in async handler if enabled
        if config.async_enabled:
            file_handler = AsyncHandler(file_handler, config.queue_size)

        handlers.append(file_handler)

    # Create root logger with handlers
    root_logger = Logger(config.service_name, config, config.default_context, handlers)
    _loggers[config.service_name] = root_logger

    return root_logger


def get_logger(name: str) -> Logger:
    """
    Get or create a logger by name.

    Logger names are hierarchical (e.g., "agora.market_data.api").
    """
    global _config, _loggers

    if _config is None:
        raise RuntimeError("Logging not initialized. Call initialize() first.")

    if name not in _loggers:
        # Get handlers from root logger
        root_logger = _loggers.get(_config.service_name)
        handlers = root_logger._handlers if root_logger else []
        _loggers[name] = Logger(name, _config, None, handlers)

    return _loggers[name]


def shutdown() -> None:
    """Shutdown the logging system and flush all handlers."""
    global _config, _loggers
    
    for logger in _loggers.values():
        for handler in logger._handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
            if hasattr(handler, 'close'):
                handler.close()
    
    _loggers.clear()
    _config = None
