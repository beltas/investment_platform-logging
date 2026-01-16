"""
Agora Trading Platform Logging Library - Python Implementation

A unified logging solution with:
- Structured JSON logging
- Automatic source location capture (file, line, function - REQUIRED)
- Context injection and inheritance
- Dual output (console + file)
- Size-based file rotation
- Async logging with bounded queues
"""

from .config import LogConfig
from .level import LogLevel
from .logger import Logger, get_logger, initialize, shutdown, SourceLocation

__all__ = [
    "LogConfig",
    "LogLevel",
    "Logger",
    "SourceLocation",
    "get_logger",
    "initialize",
    "shutdown",
]

__version__ = "0.1.0"
