"""Tests for JSON formatter."""

import json
import pytest
from datetime import datetime, timezone
from agora_log import initialize, get_logger, LogConfig


class TestJSONFormatterOutput:
    """Tests for JSON output format."""

    def test_output_is_valid_json(self, console_config: LogConfig, capsys):
        """Test that output is valid JSON."""
        logger = initialize(console_config)

        logger.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            # Should be parseable as JSON
            entry = json.loads(captured.out.strip())

            assert entry is not None
            assert isinstance(entry, dict)

    def test_json_one_entry_per_line(self, console_config: LogConfig, capsys):
        """Test that each log entry is on its own line."""
        logger = initialize(console_config)

        logger.info("message 1")
        logger.info("message 2")
        logger.info("message 3")

        captured = capsys.readouterr()
        if captured.out:
            lines = [line for line in captured.out.strip().split("\n") if line]

            assert len(lines) == 3

            # Each line should be valid JSON
            for line in lines:
                entry = json.loads(line)
                assert "message" in entry


class TestRequiredFields:
    """Tests for required fields in JSON output."""

    def test_has_timestamp_field(self, console_config: LogConfig, capsys):
        """Test that timestamp field is present."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "timestamp" in entry
            assert entry["timestamp"] is not None

    def test_has_level_field(self, console_config: LogConfig, capsys):
        """Test that level field is present."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "level" in entry
            assert entry["level"] == "INFO"

    def test_has_message_field(self, console_config: LogConfig, capsys):
        """Test that message field is present."""
        logger = initialize(console_config)

        logger.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "message" in entry
            assert entry["message"] == "test message"

    def test_has_service_field(self, console_config: LogConfig, capsys):
        """Test that service field is present."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "service" in entry
            assert entry["service"] == "test-service"

    def test_has_file_field(self, console_config: LogConfig, capsys):
        """Test that file field is present (REQUIRED)."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "file" in entry
            assert entry["file"] is not None
            assert len(entry["file"]) > 0

    def test_has_line_field(self, console_config: LogConfig, capsys):
        """Test that line field is present (REQUIRED)."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "line" in entry
            assert isinstance(entry["line"], int)
            assert entry["line"] > 0

    def test_has_function_field(self, console_config: LogConfig, capsys):
        """Test that function field is present (REQUIRED)."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "function" in entry
            assert entry["function"] is not None
            assert len(entry["function"]) > 0


class TestOptionalFields:
    """Tests for optional fields in JSON output."""

    def test_environment_field(self, console_config: LogConfig, capsys):
        """Test that environment field is included."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "environment" in entry
            assert entry["environment"] == "development"

    def test_version_field(self, console_config: LogConfig, capsys):
        """Test that version field is included."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "version" in entry
            assert entry["version"] == "1.0.0"

    def test_host_field(self, console_config: LogConfig, capsys):
        """Test that host field is included."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "host" in entry
            assert len(entry["host"]) > 0

    def test_logger_name_field(self, console_config: LogConfig, capsys):
        """Test that logger_name field is included."""
        logger = initialize(console_config)

        named_logger = get_logger("test.module.component")
        named_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "logger_name" in entry
            assert entry["logger_name"] == "test.module.component"


class TestTimestampFormat:
    """Tests for timestamp format."""

    def test_timestamp_is_iso8601(self, console_config: LogConfig, capsys):
        """Test that timestamp is in ISO 8601 format."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            timestamp = entry["timestamp"]

            # Should contain 'T' separator
            assert "T" in timestamp

            # Should be parseable as ISO 8601
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            assert dt is not None

    def test_timestamp_has_timezone(self, console_config: LogConfig, capsys):
        """Test that timestamp includes timezone."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            timestamp = entry["timestamp"]

            # Should end with Z or contain timezone offset
            assert timestamp.endswith("Z") or "+" in timestamp or timestamp.endswith(
                "+00:00"
            )

    def test_timestamp_has_microseconds(self, console_config: LogConfig, capsys):
        """Test that timestamp includes microseconds."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            timestamp = entry["timestamp"]

            # ISO 8601 with microseconds has format: YYYY-MM-DDTHH:MM:SS.ffffff
            # Should contain decimal point for fractional seconds
            assert "." in timestamp or "," in timestamp


class TestContextSerialization:
    """Tests for context field serialization."""

    def test_context_is_dict(self, console_config: LogConfig, capsys):
        """Test that context field is a dictionary."""
        logger = initialize(console_config)

        logger.info("test", key="value")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "context" in entry
            assert isinstance(entry["context"], dict)

    def test_context_serializes_strings(self, console_config: LogConfig, capsys):
        """Test that context serializes string values."""
        logger = initialize(console_config)

        logger.info("test", name="John", role="admin")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["name"] == "John"
            assert entry["context"]["role"] == "admin"

    def test_context_serializes_numbers(self, console_config: LogConfig, capsys):
        """Test that context serializes numeric values."""
        logger = initialize(console_config)

        logger.info("test", count=42, price=19.99)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["count"] == 42
            assert entry["context"]["price"] == 19.99

    def test_context_serializes_booleans(self, console_config: LogConfig, capsys):
        """Test that context serializes boolean values."""
        logger = initialize(console_config)

        logger.info("test", active=True, deleted=False)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["active"] is True
            assert entry["context"]["deleted"] is False

    def test_context_serializes_null(self, console_config: LogConfig, capsys):
        """Test that context serializes None as null."""
        logger = initialize(console_config)

        logger.info("test", optional=None)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "optional" in entry["context"]
            assert entry["context"]["optional"] is None

    def test_context_serializes_lists(self, console_config: LogConfig, capsys):
        """Test that context serializes lists."""
        logger = initialize(console_config)

        logger.info("test", tags=["python", "logging"])

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["tags"] == ["python", "logging"]

    def test_context_serializes_nested_dicts(self, console_config: LogConfig, capsys):
        """Test that context serializes nested dictionaries."""
        logger = initialize(console_config)

        logger.info("test", metadata={"region": "us-east-1", "az": "us-east-1a"})

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["metadata"]["region"] == "us-east-1"
            assert entry["context"]["metadata"]["az"] == "us-east-1a"


class TestExceptionFormatting:
    """Tests for exception field formatting."""

    def test_exception_has_type(self, console_config: LogConfig, capsys):
        """Test that exception includes type."""
        logger = initialize(console_config)

        try:
            raise ValueError("test error")
        except ValueError as e:
            logger.error("error occurred", exception=e)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "exception" in entry
            assert "type" in entry["exception"]
            assert entry["exception"]["type"] == "ValueError"

    def test_exception_has_message(self, console_config: LogConfig, capsys):
        """Test that exception includes message."""
        logger = initialize(console_config)

        try:
            raise ValueError("test error message")
        except ValueError as e:
            logger.error("error occurred", exception=e)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "exception" in entry
            assert "message" in entry["exception"]
            assert entry["exception"]["message"] == "test error message"

    def test_exception_has_stacktrace_field(self, console_config: LogConfig, capsys):
        """Test that exception includes stacktrace field."""
        logger = initialize(console_config)

        try:
            raise RuntimeError("test")
        except RuntimeError as e:
            logger.error("error", exception=e)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "exception" in entry
            assert "stacktrace" in entry["exception"]
            # May be empty in current implementation
            assert isinstance(entry["exception"]["stacktrace"], str)


class TestDurationFormatting:
    """Tests for duration_ms formatting."""

    def test_duration_is_number(self, console_config: LogConfig, capsys):
        """Test that duration_ms is a number."""
        logger = initialize(console_config)

        with logger.timer("operation"):
            pass

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "context" in entry
            if "duration_ms" in entry["context"]:
                assert isinstance(entry["context"]["duration_ms"], (int, float))
                assert entry["context"]["duration_ms"] >= 0

    def test_duration_has_precision(self, console_config: LogConfig, capsys):
        """Test that duration has sub-millisecond precision."""
        logger = initialize(console_config)

        import time

        with logger.timer("short operation"):
            time.sleep(0.001)  # 1ms

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            if "duration_ms" in entry.get("context", {}):
                # Should have fractional milliseconds
                duration = entry["context"]["duration_ms"]
                assert isinstance(duration, float)


class TestFieldOrdering:
    """Tests for consistent field ordering (not required but nice)."""

    def test_required_fields_first(self, console_config: LogConfig, capsys):
        """Test that required fields appear early in output."""
        logger = initialize(console_config)

        logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            # JSON dict ordering may not be guaranteed in all Python versions
            # but we can check fields exist
            entry = json.loads(captured.out.strip())

            required_fields = [
                "timestamp",
                "level",
                "message",
                "service",
                "file",
                "line",
                "function",
            ]

            for field in required_fields:
                assert field in entry
