"""Tests for context management."""

import json
import pytest
from agora_log import initialize, get_logger, LogConfig


class TestContextManagement:
    """Tests for logger context management."""

    def test_logger_context_property(self, config: LogConfig):
        """Test that logger has context property."""
        logger = initialize(config)

        assert hasattr(logger, "context")
        assert isinstance(logger.context, dict)

    def test_empty_context_by_default(self, config: LogConfig):
        """Test that logger starts with empty context."""
        logger = initialize(config)

        # Should be empty initially (no context set)
        assert logger.context == {}

    def test_with_context_adds_values(self, config: LogConfig):
        """Test that with_context adds context values."""
        logger = initialize(config)

        ctx_logger = logger.with_context(key1="value1", key2="value2")

        assert "key1" in ctx_logger.context
        assert "key2" in ctx_logger.context
        assert ctx_logger.context["key1"] == "value1"
        assert ctx_logger.context["key2"] == "value2"

    def test_with_context_preserves_existing(self, config: LogConfig):
        """Test that with_context preserves existing context."""
        logger = initialize(config)

        logger1 = logger.with_context(key1="value1")
        logger2 = logger1.with_context(key2="value2")

        # logger2 should have both key1 and key2
        assert logger2.context["key1"] == "value1"
        assert logger2.context["key2"] == "value2"

    def test_with_context_overrides_existing(self, config: LogConfig):
        """Test that with_context can override existing values."""
        logger = initialize(config)

        logger1 = logger.with_context(key="original")
        logger2 = logger1.with_context(key="overridden")

        assert logger2.context["key"] == "overridden"
        # Original logger unchanged
        assert logger1.context["key"] == "original"

    def test_with_context_creates_new_instance(self, config: LogConfig):
        """Test that with_context creates new logger instance."""
        logger = initialize(config)

        ctx_logger = logger.with_context(key="value")

        # Should be different instances
        assert logger is not ctx_logger

        # But original is unchanged
        assert "key" not in logger.context
        assert "key" in ctx_logger.context


class TestContextInheritance:
    """Tests for context inheritance chains."""

    def test_three_level_inheritance(self, config: LogConfig):
        """Test context inheritance through three levels."""
        logger = initialize(config)

        logger1 = logger.with_context(level1="value1")
        logger2 = logger1.with_context(level2="value2")
        logger3 = logger2.with_context(level3="value3")

        # logger3 should have all three
        assert logger3.context["level1"] == "value1"
        assert logger3.context["level2"] == "value2"
        assert logger3.context["level3"] == "value3"

    def test_context_chain_isolation(self, config: LogConfig):
        """Test that context chains are isolated."""
        logger = initialize(config)

        branch_a = logger.with_context(branch="a")
        branch_b = logger.with_context(branch="b")

        # Branches should be independent
        assert branch_a.context["branch"] == "a"
        assert branch_b.context["branch"] == "b"

        # Further modifications should be isolated
        branch_a1 = branch_a.with_context(sub="a1")
        branch_b1 = branch_b.with_context(sub="b1")

        assert branch_a1.context["branch"] == "a"
        assert branch_a1.context["sub"] == "a1"
        assert branch_b1.context["branch"] == "b"
        assert branch_b1.context["sub"] == "b1"

    def test_deep_context_chain(self, config: LogConfig):
        """Test deep context inheritance chain."""
        logger = initialize(config)

        current = logger
        for i in range(10):
            current = current.with_context(**{f"level{i}": f"value{i}"})

        # Should have all 10 levels
        for i in range(10):
            assert current.context[f"level{i}"] == f"value{i}"


class TestContextInLogOutput:
    """Tests for context appearing in log output."""

    def test_context_in_log_entry(self, console_config: LogConfig, capsys):
        """Test that context appears in log entry."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(user_id="user123", request_id="req456")
        ctx_logger.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # user_id is a special key that gets promoted to top level
            assert entry["user_id"] == "user123"
            # request_id stays in context
            assert "context" in entry
            assert entry["context"]["request_id"] == "req456"

    def test_kwargs_merged_with_context(self, console_config: LogConfig, capsys):
        """Test that kwargs are merged with logger context."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(user_id="user123")
        ctx_logger.info("test", action="login", success=True)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # user_id is a special key promoted to top level
            assert entry["user_id"] == "user123"
            # Other kwargs stay in context
            assert entry["context"]["action"] == "login"
            assert entry["context"]["success"] is True

    def test_kwargs_override_logger_context(self, console_config: LogConfig, capsys):
        """Test that kwargs override logger context for same keys."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(status="default")
        ctx_logger.info("test", status="overridden")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # kwargs should win
            assert entry["context"]["status"] == "overridden"


class TestContextDataTypes:
    """Tests for different data types in context."""

    def test_context_with_string_values(self, console_config: LogConfig, capsys):
        """Test context with string values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(name="John Doe", role="admin")
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["name"] == "John Doe"
            assert entry["context"]["role"] == "admin"

    def test_context_with_numeric_values(self, console_config: LogConfig, capsys):
        """Test context with numeric values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(user_id=12345, balance=1000.50)
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # user_id is a special key promoted to top level
            assert entry["user_id"] == 12345
            assert entry["context"]["balance"] == 1000.50

    def test_context_with_boolean_values(self, console_config: LogConfig, capsys):
        """Test context with boolean values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(active=True, verified=False)
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["active"] is True
            assert entry["context"]["verified"] is False

    def test_context_with_list_values(self, console_config: LogConfig, capsys):
        """Test context with list values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(tags=["python", "logging", "json"])
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["tags"] == ["python", "logging", "json"]

    def test_context_with_dict_values(self, console_config: LogConfig, capsys):
        """Test context with nested dict values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(
            metadata={"region": "us-east-1", "env": "prod"}
        )
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["metadata"]["region"] == "us-east-1"
            assert entry["context"]["metadata"]["env"] == "prod"

    def test_context_with_none_values(self, console_config: LogConfig, capsys):
        """Test context with None values."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(optional_field=None)
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "optional_field" in entry["context"]
            assert entry["context"]["optional_field"] is None


class TestSpecialContextKeys:
    """Tests for special context keys (correlation_id, user_id, etc.)."""

    def test_correlation_id_in_context(self, console_config: LogConfig, capsys):
        """Test that correlation_id appears at top level."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(correlation_id="corr-123")
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # correlation_id should be at top level
            assert "correlation_id" in entry
            assert entry["correlation_id"] == "corr-123"

    def test_user_id_in_context(self, console_config: LogConfig, capsys):
        """Test that user_id appears at top level."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(user_id="user-456")
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # user_id should be at top level
            assert "user_id" in entry
            assert entry["user_id"] == "user-456"

    def test_trace_id_in_context(self, console_config: LogConfig, capsys):
        """Test that trace_id appears at top level."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(trace_id="trace-789")
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # trace_id should be at top level
            assert "trace_id" in entry
            assert entry["trace_id"] == "trace-789"

    def test_span_id_in_context(self, console_config: LogConfig, capsys):
        """Test that span_id appears at top level."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(span_id="span-abc")
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # span_id should be at top level
            assert "span_id" in entry
            assert entry["span_id"] == "span-abc"


class TestContextEdgeCases:
    """Tests for edge cases in context handling."""

    def test_context_with_empty_dict(self, config: LogConfig):
        """Test with_context with empty dict."""
        logger = initialize(config)

        ctx_logger = logger.with_context()

        # Should still create new instance
        assert logger is not ctx_logger

        # Context should be empty
        assert ctx_logger.context == {}

    def test_context_with_many_keys(self, config: LogConfig):
        """Test context with many keys."""
        logger = initialize(config)

        # Add 100 context keys
        context = {f"key{i}": f"value{i}" for i in range(100)}
        ctx_logger = logger.with_context(**context)

        # All keys should be present
        for i in range(100):
            assert ctx_logger.context[f"key{i}"] == f"value{i}"

    def test_context_with_special_characters(self, console_config: LogConfig, capsys):
        """Test context keys/values with special characters."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(
            key_with_underscore="value",
            **{"key-with-dash": "value"},
            **{"key.with.dot": "value"},
        )
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert "key_with_underscore" in entry["context"]
            assert "key-with-dash" in entry["context"]
            assert "key.with.dot" in entry["context"]

    def test_context_value_with_unicode(self, console_config: LogConfig, capsys):
        """Test context values with Unicode characters."""
        logger = initialize(console_config)

        ctx_logger = logger.with_context(
            name="José García", message="Hello 世界", emoji="🔥"
        )
        ctx_logger.info("test")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["context"]["name"] == "José García"
            assert entry["context"]["message"] == "Hello 世界"
            assert entry["context"]["emoji"] == "🔥"
