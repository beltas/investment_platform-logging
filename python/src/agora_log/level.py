"""Log level definitions."""

from enum import IntEnum


class LogLevel(IntEnum):
    """
    Standard log levels.
    
    Values are compatible with Python's logging module.
    """
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
