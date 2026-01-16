#!/usr/bin/env python3
"""Basic usage examples for agora-log."""

import sys
from pathlib import Path

# Add src to path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agora_log import initialize, get_logger, LogConfig, LogLevel, shutdown


def example_basic_logging():
    """Example: Basic logging at different levels."""
    print("=== Example: Basic Logging ===\n")

    config = LogConfig(
        service_name="example-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Log at different levels
    logger.debug("Debug message", component="main")
    logger.info("Information message", status="running")
    logger.warning("Warning message", resource="memory", usage_percent=85)
    logger.error("Error message", error_code="E001")
    logger.critical("Critical message", service="database", state="down")

    shutdown()
    print("\n")


def example_context_management():
    """Example: Using context for request tracking."""
    print("=== Example: Context Management ===\n")

    config = LogConfig(
        service_name="api-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Simulate request handling
    request_logger = logger.with_context(
        request_id="req-12345",
        user_id="user-67890",
        ip_address="192.168.1.1"
    )

    request_logger.info("Request received", method="GET", path="/api/orders")

    # Nested context for database operations
    db_logger = request_logger.with_context(component="database")
    db_logger.info("Executing query", table="orders", rows=150)

    # All logs include request_id and user_id
    request_logger.info("Request completed", status_code=200, duration_ms=45.2)

    shutdown()
    print("\n")


def example_timer():
    """Example: Using timer for performance monitoring."""
    print("=== Example: Timer Context Manager ===\n")

    import time

    config = LogConfig(
        service_name="worker-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Time a simple operation
    with logger.timer("Data processing"):
        time.sleep(0.1)  # Simulate work

    # Time with additional context
    with logger.timer("Database query", table="users", query_type="SELECT"):
        time.sleep(0.05)  # Simulate query

    # Timer works even with exceptions
    try:
        with logger.timer("Failed operation"):
            time.sleep(0.02)
            raise ValueError("Something went wrong")
    except ValueError:
        pass  # Timer still logs duration

    shutdown()
    print("\n")


def example_exception_logging():
    """Example: Logging exceptions with full context."""
    print("=== Example: Exception Logging ===\n")

    config = LogConfig(
        service_name="error-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Log exceptions
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Division error", exception=e, dividend=10, divisor=0)

    try:
        data = {"key": "value"}
        _ = data["missing_key"]
    except KeyError as e:
        logger.error("Key not found", exception=e, key="missing_key")

    try:
        raise RuntimeError("Critical system failure")
    except RuntimeError as e:
        logger.critical("System failure", exception=e, component="auth")

    shutdown()
    print("\n")


def example_special_context_keys():
    """Example: Special context keys promoted to top level."""
    print("=== Example: Special Context Keys ===\n")

    config = LogConfig(
        service_name="trace-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Correlation ID for request tracking
    trace_logger = logger.with_context(
        correlation_id="corr-abc123",
        trace_id="trace-xyz789",
        span_id="span-000111",
        user_id="user-42"
    )

    trace_logger.info("Distributed trace example")

    # These keys appear at top level in JSON output, not in context object
    # This is useful for log aggregation systems like ELK, Loki, etc.

    shutdown()
    print("\n")


def example_hierarchical_loggers():
    """Example: Hierarchical logger names."""
    print("=== Example: Hierarchical Loggers ===\n")

    config = LogConfig(
        service_name="market-data",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    initialize(config)

    # Get loggers with hierarchical names
    api_logger = get_logger("market_data.api")
    db_logger = get_logger("market_data.database")
    cache_logger = get_logger("market_data.cache")

    api_logger.info("API request", endpoint="/prices/AAPL")
    db_logger.info("Database query", table="stock_prices")
    cache_logger.info("Cache hit", key="price:AAPL:latest")

    shutdown()
    print("\n")


def example_file_logging():
    """Example: Logging to file with rotation."""
    print("=== Example: File Logging ===\n")

    import tempfile

    # Create temp directory for logs
    temp_dir = Path(tempfile.mkdtemp())
    log_file = temp_dir / "app.log"

    config = LogConfig(
        service_name="file-service",
        console_enabled=False,  # Only file
        file_enabled=True,
        file_path=log_file,
        max_file_size_mb=1,  # Small for demo
        max_backup_count=3,
        async_enabled=False,  # Sync for demo
    )

    logger = initialize(config)

    # Write some logs
    for i in range(10):
        logger.info(f"Log entry {i}", iteration=i, data="x" * 100)

    shutdown()

    # Show what was written
    if log_file.exists():
        content = log_file.read_text()
        lines = content.strip().split("\n")
        print(f"Wrote {len(lines)} log entries to {log_file}")
        print(f"File size: {log_file.stat().st_size} bytes")

        # Show first entry
        if lines:
            import json
            first_entry = json.loads(lines[0])
            print(f"\nFirst entry:")
            print(f"  Timestamp: {first_entry['timestamp']}")
            print(f"  Level: {first_entry['level']}")
            print(f"  Message: {first_entry['message']}")
            print(f"  File: {first_entry['file']}")
            print(f"  Line: {first_entry['line']}")
            print(f"  Function: {first_entry['function']}")

    print("\n")


def example_text_format():
    """Example: Human-readable text format for development."""
    print("=== Example: Text Format Console ===\n")

    config = LogConfig(
        service_name="dev-service",
        console_enabled=True,
        console_format="text",  # Human-readable
        console_colors=True,    # With colors
        file_enabled=False,
    )

    logger = initialize(config)

    logger.debug("Debug message for developers")
    logger.info("Server started", port=8000, host="localhost")
    logger.warning("High memory usage", percent=85)
    logger.error("Connection failed", retry_count=3)

    shutdown()
    print("\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Agora Log - Python Examples")
    print("=" * 60 + "\n")

    example_basic_logging()
    example_context_management()
    example_timer()
    example_exception_logging()
    example_special_context_keys()
    example_hierarchical_loggers()
    example_file_logging()
    example_text_format()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")
