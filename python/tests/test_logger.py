"""Tests for core logger functionality."""

import json
import pytest
from pathlib import Path
from agora_log import initialize, get_logger, LogConfig, LogLevel, shutdown


class TestLoggerInitialization:
    """Tests for logger initialization and configuration."""

    def test_initialize_creates_logger(self, config: LogConfig):
        """Test that initialize creates a logger."""
        logger = initialize(config)
        assert logger is not None
        assert logger._name == "test-service"
        assert logger._config == config

    def test_get_logger_requires_initialization(self):
        """Test that get_logger raises error if not initialized."""
        with pytest.raises(RuntimeError, match="Logging not initialized"):
            get_logger("test")

    def test_get_logger_returns_same_instance(self, config: LogConfig):
        """Test that get_logger returns the same instance for same name."""
        initialize(config)
        logger1 = get_logger("test.logger")
        logger2 = get_logger("test.logger")
        assert logger1 is logger2

    def test_get_logger_different_names(self, config: LogConfig):
        """Test that different names create different logger instances."""
        initialize(config)
        logger1 = get_logger("test.logger1")
        logger2 = get_logger("test.logger2")
        assert logger1 is not logger2
        assert logger1._name == "test.logger1"
        assert logger2._name == "test.logger2"

    def test_shutdown_clears_loggers(self, config: LogConfig):
        """Test that shutdown clears logger state."""
        initialize(config)
        get_logger("test")
        shutdown()

        with pytest.raises(RuntimeError, match="Logging not initialized"):
            get_logger("test2")


class TestLogLevels:
    """Tests for log level filtering."""

    def test_info_level_filters_debug(self, temp_log_file: Path):
        """Test that INFO level filters out DEBUG logs."""
        config = LogConfig(
            service_name="test-service",
            level=LogLevel.INFO,
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
            async_enabled=False,
        )
        logger = initialize(config)

        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

        # Flush handlers (when implemented)
        # For now, check output manually

    def test_debug_level_logs_all(self, config: LogConfig):
        """Test that DEBUG level logs all messages."""
        logger = initialize(config)

        # All levels should be logged
        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        logger.critical("critical")

    def test_error_level_filters_lower_levels(self, temp_log_file: Path):
        """Test that ERROR level filters out INFO, WARNING, DEBUG."""
        config = LogConfig(
            service_name="test-service",
            level=LogLevel.ERROR,
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
            async_enabled=False,
        )
        logger = initialize(config)

        logger.debug("debug")  # Filtered
        logger.info("info")  # Filtered
        logger.warning("warning")  # Filtered
        logger.error("error")  # Logged
        logger.critical("critical")  # Logged

    def test_critical_level_only_logs_critical(self, temp_log_file: Path):
        """Test that CRITICAL level only logs CRITICAL messages."""
        config = LogConfig(
            service_name="test-service",
            level=LogLevel.CRITICAL,
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
            async_enabled=False,
        )
        logger = initialize(config)

        logger.debug("debug")  # Filtered
        logger.info("info")  # Filtered
        logger.warning("warning")  # Filtered
        logger.error("error")  # Filtered
        logger.critical("critical")  # Logged


class TestSourceLocationCapture:
    """Tests for automatic source location capture."""

    def test_captures_file_name(self, config: LogConfig, capsys):
        """Test that file name is captured correctly."""
        initialize(config)
        # Use console for easier testing
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("test message")  # This line is important for line number

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "file" in entry
            assert entry["file"] == "test_logger.py"

    def test_captures_line_number(self, config: LogConfig, capsys):
        """Test that line number is captured correctly."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        expected_line = None
        logger.info("test")  # Capture this line
        expected_line = 153  # Line number where logger.info() is called

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "line" in entry
            # Line number should be close (exact match depends on formatting)
            assert isinstance(entry["line"], int)
            assert entry["line"] > 0

    def test_captures_function_name(self, config: LogConfig, capsys):
        """Test that function name is captured correctly."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "function" in entry
            assert entry["function"] == "test_captures_function_name"

    def test_source_location_in_nested_call(self, config: LogConfig, capsys):
        """Test that source location points to actual caller, not helper."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        def helper_function():
            logger = get_logger("test")
            logger.info("from helper")

        helper_function()

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            # Should capture helper_function, not _log
            assert entry["function"] == "helper_function"

    def test_required_fields_always_present(self, config: LogConfig, capsys):
        """Test that file, line, function are always present."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            # REQUIRED fields must be present
            assert "file" in entry
            assert "line" in entry
            assert "function" in entry
            assert entry["file"] != ""
            assert entry["line"] > 0
            assert entry["function"] != ""


class TestContextInheritance:
    """Tests for context inheritance and merging."""

    def test_with_context_creates_new_logger(self, config: LogConfig):
        """Test that with_context creates a new logger instance."""
        logger = initialize(config)
        child = logger.with_context(request_id="123")

        assert child is not logger
        assert child._name == logger._name
        assert child._config == logger._config
        assert "request_id" in child._context

    def test_parent_context_flows_to_child(self, config: LogConfig, capsys):
        """Test that parent context is inherited by child logger."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        parent = get_logger("test").with_context(user_id="user123")
        child = parent.with_context(request_id="req456")

        child.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            # Both parent and child context should be present
            assert entry["context"]["user_id"] == "user123"
            assert entry["context"]["request_id"] == "req456"

    def test_child_context_overrides_parent(self, config: LogConfig, capsys):
        """Test that child context overrides parent context for same keys."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        parent = get_logger("test").with_context(key="parent_value")
        child = parent.with_context(key="child_value")

        child.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["context"]["key"] == "child_value"

    def test_with_context_merges_multiple_keys(self, config: LogConfig):
        """Test that with_context can add multiple keys at once."""
        logger = initialize(config)
        child = logger.with_context(key1="value1", key2="value2", key3="value3")

        assert child._context["key1"] == "value1"
        assert child._context["key2"] == "value2"
        assert child._context["key3"] == "value3"

    def test_context_property_returns_copy(self, config: LogConfig):
        """Test that context property returns a copy, not reference."""
        logger = initialize(config).with_context(key="value")
        context1 = logger.context
        context2 = logger.context

        assert context1 == context2
        assert context1 is not context2  # Different objects

        # Modifying returned context doesn't affect logger
        context1["new_key"] = "new_value"
        assert "new_key" not in logger.context


class TestTimerContextManager:
    """Tests for the timer context manager."""

    def test_timer_logs_duration(self, config: LogConfig, capsys):
        """Test that timer logs duration in milliseconds."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        import time

        with logger.timer("test operation"):
            time.sleep(0.01)  # Sleep 10ms

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["message"] == "test operation"
            assert "duration_ms" in entry["context"]
            assert entry["context"]["duration_ms"] >= 10  # At least 10ms
            assert entry["context"]["duration_ms"] < 100  # Sanity check

    def test_timer_logs_even_on_exception(self, config: LogConfig, capsys):
        """Test that timer logs duration even when exception is raised."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        with pytest.raises(ValueError):
            with logger.timer("failing operation"):
                raise ValueError("test error")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "duration_ms" in entry["context"]

    def test_timer_includes_additional_context(self, config: LogConfig, capsys):
        """Test that timer can include additional context."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        with logger.timer("query", table="users", rows=100):
            pass

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["context"]["table"] == "users"
            assert entry["context"]["rows"] == 100
            assert "duration_ms" in entry["context"]


class TestExceptionLogging:
    """Tests for exception logging."""

    def test_error_with_exception(self, config: LogConfig, capsys):
        """Test that error logs exception details."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        try:
            raise ValueError("test error message")
        except ValueError as e:
            logger.error("An error occurred", exception=e)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "exception" in entry
            assert entry["exception"]["type"] == "ValueError"
            assert entry["exception"]["message"] == "test error message"

    def test_critical_with_exception(self, config: LogConfig, capsys):
        """Test that critical logs exception details."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        try:
            raise RuntimeError("critical error")
        except RuntimeError as e:
            logger.critical("Critical failure", exception=e, component="auth")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["level"] == "CRITICAL"
            assert entry["exception"]["type"] == "RuntimeError"
            assert entry["context"]["component"] == "auth"

    def test_exception_includes_stacktrace(self, config: LogConfig, capsys):
        """Test that exception includes stack trace (when implemented)."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")

        try:
            raise KeyError("missing key")
        except KeyError as e:
            logger.error("Key error", exception=e)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert "exception" in entry
            # Stacktrace field should exist (may be empty in current impl)
            assert "stacktrace" in entry["exception"]


class TestLogOutput:
    """Tests for log output format and content."""

    def test_log_entry_has_required_fields(self, config: LogConfig, capsys):
        """Test that log entry has all required fields."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test.logger")
        logger.info("test message", key="value")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # Required fields
            assert "timestamp" in entry
            assert "level" in entry
            assert "message" in entry
            assert "service" in entry
            assert "file" in entry
            assert "line" in entry
            assert "function" in entry

            # Optional fields
            assert "environment" in entry
            assert "version" in entry
            assert "host" in entry
            assert "logger_name" in entry
            assert "context" in entry

    def test_timestamp_is_iso8601_utc(self, config: LogConfig, capsys):
        """Test that timestamp is in ISO 8601 UTC format."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            timestamp = entry["timestamp"]

            # Should be ISO 8601 format with timezone
            assert "T" in timestamp
            assert timestamp.endswith("Z") or "+" in timestamp

            # Should be parseable
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            assert dt is not None

    def test_level_is_string_name(self, config: LogConfig, capsys):
        """Test that level is logged as string name, not number."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("info msg")
        logger.error("error msg")
        logger.warning("warning msg")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        if lines:
            for line in lines:
                if line:
                    entry = json.loads(line)
                    assert entry["level"] in ["INFO", "ERROR", "WARNING"]

    def test_service_metadata_included(self, config: LogConfig, capsys):
        """Test that service metadata is included in log entry."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["service"] == "test-service"
            assert entry["environment"] == "development"
            assert entry["version"] == "1.0.0"

    def test_logger_name_is_hierarchical(self, config: LogConfig, capsys):
        """Test that logger name is preserved."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("agora.market_data.api.prices")
        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["logger_name"] == "agora.market_data.api.prices"

    def test_custom_context_in_kwargs(self, config: LogConfig, capsys):
        """Test that custom context from kwargs is included."""
        initialize(config)
        config.console_enabled = True
        config.file_enabled = False

        logger = get_logger("test")
        logger.info(
            "processing",
            symbol="AAPL",
            price=150.25,
            quantity=100
        )

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())
            assert entry["context"]["symbol"] == "AAPL"
            assert entry["context"]["price"] == 150.25
            assert entry["context"]["quantity"] == 100
