#!/usr/bin/env python3
"""Quick test runner to verify implementation."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agora_log import initialize, get_logger, LogConfig, LogLevel, shutdown

def test_basic_logging():
    """Test basic logging functionality."""
    print("Testing basic logging...")

    config = LogConfig(
        service_name="test-service",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=True,
        console_format="json",
        file_enabled=False,
        async_enabled=False,
    )

    logger = initialize(config)

    # Test all log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    print("\n✓ Basic logging test passed\n")

def test_context():
    """Test context management."""
    print("Testing context management...")

    config = LogConfig(
        service_name="test-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    # Test with_context
    ctx_logger = logger.with_context(user_id="user123", request_id="req456")
    ctx_logger.info("Message with context")

    # Test special keys promotion
    trace_logger = logger.with_context(
        correlation_id="corr-123",
        trace_id="trace-456",
        span_id="span-789"
    )
    trace_logger.info("Message with tracing")

    print("\n✓ Context test passed\n")

def test_timer():
    """Test timer context manager."""
    print("Testing timer...")

    config = LogConfig(
        service_name="test-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    import time
    with logger.timer("Test operation"):
        time.sleep(0.01)

    print("\n✓ Timer test passed\n")

def test_exception():
    """Test exception logging."""
    print("Testing exception logging...")

    config = LogConfig(
        service_name="test-service",
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    logger = initialize(config)

    try:
        raise ValueError("Test error message")
    except ValueError as e:
        logger.error("An error occurred", exception=e)

    print("\n✓ Exception test passed\n")

if __name__ == "__main__":
    try:
        test_basic_logging()
        shutdown()

        test_context()
        shutdown()

        test_timer()
        shutdown()

        test_exception()
        shutdown()

        print("\n✅ All manual tests passed!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
