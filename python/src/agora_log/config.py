"""Logging configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .level import LogLevel


@dataclass
class LogConfig:
    """
    Logging configuration.

    All settings can be overridden via environment variables.
    """
    service_name: str
    environment: Literal["development", "staging", "production"] = "development"
    version: str = "0.0.0"
    level: LogLevel = LogLevel.INFO

    # Console output
    console_enabled: bool = True
    console_format: Literal["json", "text"] = "json"
    console_colors: bool = True

    # File output
    file_enabled: bool = True
    file_path: Path | str = field(default_factory=lambda: Path("/agora/logs/app.log"))
    max_file_size_mb: int = 100
    max_backup_count: int = 5

    # Async settings
    async_enabled: bool = True
    queue_size: int = 10000

    # Default context (included in ALL logs)
    default_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Convert file_path to Path if it's a string."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
    
    @classmethod
    def from_env(cls, service_name: str) -> LogConfig:
        """
        Create configuration from environment variables.
        
        Environment variables take precedence over defaults.
        """
        return cls(
            service_name=service_name,
            environment=os.getenv("ENVIRONMENT", "development"),  # type: ignore
            version=os.getenv("SERVICE_VERSION", "0.0.0"),
            level=LogLevel[os.getenv("LOG_LEVEL", "INFO").upper()],
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
            console_format=os.getenv("LOG_CONSOLE_FORMAT", "json"),  # type: ignore
            console_colors=os.getenv("LOG_CONSOLE_COLORS", "true").lower() == "true",
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            file_path=Path(os.getenv("LOG_FILE_PATH", "logs/app.log")),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "100")),
            max_backup_count=int(os.getenv("LOG_MAX_BACKUP_COUNT", "5")),
            async_enabled=os.getenv("LOG_ASYNC_ENABLED", "true").lower() == "true",
            queue_size=int(os.getenv("LOG_QUEUE_SIZE", "10000")),
        )
