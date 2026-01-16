"""Shared pytest fixtures for logging tests."""

import pytest
from pathlib import Path
from typing import Generator
from agora_log import LogConfig, LogLevel


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """Create a temporary log file path."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "test.log"


@pytest.fixture
def config(temp_log_file: Path) -> LogConfig:
    """Create a test configuration with console disabled, file enabled."""
    return LogConfig(
        service_name="test-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=False,
        file_enabled=True,
        file_path=temp_log_file,
        max_file_size_mb=1,  # Small for testing rotation
        max_backup_count=3,
        async_enabled=False,  # Synchronous by default for easier testing
    )


@pytest.fixture
def async_config(temp_log_file: Path) -> LogConfig:
    """Create a test configuration with async enabled."""
    return LogConfig(
        service_name="test-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=False,
        file_enabled=True,
        file_path=temp_log_file,
        max_file_size_mb=1,
        max_backup_count=3,
        async_enabled=True,
        queue_size=10000,  # Large enough for burst tests
    )


@pytest.fixture
def console_config() -> LogConfig:
    """Create a test configuration with only console output."""
    return LogConfig(
        service_name="test-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=True,
        console_format="json",
        file_enabled=False,
        async_enabled=False,
    )


@pytest.fixture
def text_console_config() -> LogConfig:
    """Create a test configuration with text console output."""
    return LogConfig(
        service_name="test-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=True,
        console_format="text",
        console_colors=False,  # No colors for easier testing
        file_enabled=False,
        async_enabled=False,
    )


@pytest.fixture(autouse=True)
def reset_logging_state() -> Generator[None, None, None]:
    """Reset global logging state before and after each test."""
    # Import here to avoid circular imports
    from agora_log import logger as logger_module

    # Clear state before test
    logger_module._config = None
    logger_module._loggers.clear()
    logger_module._hostname = None

    yield

    # Clear state after test
    logger_module._config = None
    logger_module._loggers.clear()
    logger_module._hostname = None
