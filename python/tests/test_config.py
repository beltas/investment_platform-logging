"""Tests for configuration system."""

import os
import pytest
from pathlib import Path

from agora_log import LogConfig, LogLevel


class TestLogConfigDefaults:
    """Tests for default configuration values."""

    def test_default_config_values(self):
        """Test that default values are set correctly."""
        config = LogConfig(service_name="test-service")

        assert config.service_name == "test-service"
        assert config.environment == "development"
        assert config.version == "0.0.0"
        assert config.level == LogLevel.INFO
        assert config.console_enabled is True
        assert config.console_format == "json"
        assert config.console_colors is True
        assert config.file_enabled is True
        assert config.file_path == Path("/agora/logs/app.log")
        assert config.max_file_size_mb == 100
        assert config.max_backup_count == 5
        assert config.async_enabled is True
        assert config.queue_size == 10000
        assert config.default_context == {}

    def test_custom_config_values(self):
        """Test that custom values override defaults."""
        config = LogConfig(
            service_name="custom-service",
            environment="production",
            version="2.1.0",
            level=LogLevel.ERROR,
            console_enabled=False,
            file_path=Path("/var/log/custom.log"),
            max_file_size_mb=50,
            max_backup_count=10,
        )

        assert config.service_name == "custom-service"
        assert config.environment == "production"
        assert config.version == "2.1.0"
        assert config.level == LogLevel.ERROR
        assert config.console_enabled is False
        assert config.file_path == Path("/var/log/custom.log")
        assert config.max_file_size_mb == 50
        assert config.max_backup_count == 10


class TestConfigFromEnv:
    """Tests for configuration from environment variables."""

    def test_from_env_default_values(self, monkeypatch):
        """Test from_env with no environment variables set."""
        # Clear any existing env vars
        for key in [
            "ENVIRONMENT",
            "SERVICE_VERSION",
            "LOG_LEVEL",
            "LOG_CONSOLE_ENABLED",
            "LOG_CONSOLE_FORMAT",
            "LOG_FILE_PATH",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = LogConfig.from_env("test-service")

        assert config.service_name == "test-service"
        assert config.environment == "development"
        assert config.version == "0.0.0"
        assert config.level == LogLevel.INFO

    def test_from_env_environment(self, monkeypatch):
        """Test that ENVIRONMENT variable is read."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = LogConfig.from_env("test-service")

        assert config.environment == "production"

    def test_from_env_version(self, monkeypatch):
        """Test that SERVICE_VERSION variable is read."""
        monkeypatch.setenv("SERVICE_VERSION", "1.2.3")

        config = LogConfig.from_env("test-service")

        assert config.version == "1.2.3"

    def test_from_env_log_level(self, monkeypatch):
        """Test that LOG_LEVEL variable is read and parsed."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        config = LogConfig.from_env("test-service")

        assert config.level == LogLevel.DEBUG

    def test_from_env_log_level_case_insensitive(self, monkeypatch):
        """Test that log level parsing is case insensitive."""
        monkeypatch.setenv("LOG_LEVEL", "error")

        config = LogConfig.from_env("test-service")

        assert config.level == LogLevel.ERROR

    def test_from_env_console_enabled(self, monkeypatch):
        """Test that LOG_CONSOLE_ENABLED variable is read."""
        monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")

        config = LogConfig.from_env("test-service")

        assert config.console_enabled is False

    def test_from_env_console_format(self, monkeypatch):
        """Test that LOG_CONSOLE_FORMAT variable is read."""
        monkeypatch.setenv("LOG_CONSOLE_FORMAT", "text")

        config = LogConfig.from_env("test-service")

        assert config.console_format == "text"

    def test_from_env_console_colors(self, monkeypatch):
        """Test that LOG_CONSOLE_COLORS variable is read."""
        monkeypatch.setenv("LOG_CONSOLE_COLORS", "false")

        config = LogConfig.from_env("test-service")

        assert config.console_colors is False

    def test_from_env_file_enabled(self, monkeypatch):
        """Test that LOG_FILE_ENABLED variable is read."""
        monkeypatch.setenv("LOG_FILE_ENABLED", "false")

        config = LogConfig.from_env("test-service")

        assert config.file_enabled is False

    def test_from_env_file_path(self, monkeypatch):
        """Test that LOG_FILE_PATH variable is read."""
        monkeypatch.setenv("LOG_FILE_PATH", "/var/log/custom/app.log")

        config = LogConfig.from_env("test-service")

        assert config.file_path == Path("/var/log/custom/app.log")

    def test_from_env_max_file_size(self, monkeypatch):
        """Test that LOG_MAX_FILE_SIZE_MB variable is read."""
        monkeypatch.setenv("LOG_MAX_FILE_SIZE_MB", "50")

        config = LogConfig.from_env("test-service")

        assert config.max_file_size_mb == 50

    def test_from_env_max_backup_count(self, monkeypatch):
        """Test that LOG_MAX_BACKUP_COUNT variable is read."""
        monkeypatch.setenv("LOG_MAX_BACKUP_COUNT", "10")

        config = LogConfig.from_env("test-service")

        assert config.max_backup_count == 10

    def test_from_env_async_enabled(self, monkeypatch):
        """Test that LOG_ASYNC_ENABLED variable is read."""
        monkeypatch.setenv("LOG_ASYNC_ENABLED", "false")

        config = LogConfig.from_env("test-service")

        assert config.async_enabled is False

    def test_from_env_queue_size(self, monkeypatch):
        """Test that LOG_QUEUE_SIZE variable is read."""
        monkeypatch.setenv("LOG_QUEUE_SIZE", "5000")

        config = LogConfig.from_env("test-service")

        assert config.queue_size == 5000

    def test_from_env_multiple_variables(self, monkeypatch):
        """Test that multiple environment variables work together."""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("SERVICE_VERSION", "2.0.0")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("LOG_CONSOLE_ENABLED", "true")
        monkeypatch.setenv("LOG_FILE_ENABLED", "false")

        config = LogConfig.from_env("test-service")

        assert config.environment == "staging"
        assert config.version == "2.0.0"
        assert config.level == LogLevel.WARNING
        assert config.console_enabled is True
        assert config.file_enabled is False


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_service_name_required(self):
        """Test that service_name is required."""
        # Service name is a required parameter
        with pytest.raises(TypeError):
            LogConfig()  # type: ignore

    def test_environment_literal_type(self):
        """Test that environment accepts only valid literal values."""
        # Valid environments
        config1 = LogConfig(service_name="test", environment="development")
        config2 = LogConfig(service_name="test", environment="staging")
        config3 = LogConfig(service_name="test", environment="production")

        assert config1.environment == "development"
        assert config2.environment == "staging"
        assert config3.environment == "production"

    def test_console_format_literal_type(self):
        """Test that console_format accepts only valid literal values."""
        # Valid formats
        config1 = LogConfig(service_name="test", console_format="json")
        config2 = LogConfig(service_name="test", console_format="text")

        assert config1.console_format == "json"
        assert config2.console_format == "text"

    def test_log_level_enum_values(self):
        """Test that level accepts LogLevel enum values."""
        for level in [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
        ]:
            config = LogConfig(service_name="test", level=level)
            assert config.level == level

    def test_file_path_accepts_string_or_path(self):
        """Test that file_path accepts both string and Path objects."""
        config1 = LogConfig(service_name="test", file_path="logs/app.log")
        config2 = LogConfig(service_name="test", file_path=Path("/var/log/app.log"))

        # Both should be Path objects
        assert isinstance(config1.file_path, Path)
        assert isinstance(config2.file_path, Path)

    def test_integer_values_positive(self):
        """Test that integer configuration values are positive."""
        config = LogConfig(
            service_name="test",
            max_file_size_mb=100,
            max_backup_count=5,
            queue_size=10000,
        )

        assert config.max_file_size_mb > 0
        assert config.max_backup_count >= 0
        assert config.queue_size > 0

    def test_default_context_is_dict(self):
        """Test that default_context is a dictionary."""
        config = LogConfig(
            service_name="test",
            default_context={"key1": "value1", "key2": 123},
        )

        assert isinstance(config.default_context, dict)
        assert config.default_context["key1"] == "value1"
        assert config.default_context["key2"] == 123


class TestConfigEdgeCases:
    """Tests for edge cases in configuration."""

    def test_empty_service_name(self):
        """Test behavior with empty service name."""
        config = LogConfig(service_name="")

        # Should accept empty string
        assert config.service_name == ""

    def test_max_backup_count_zero(self):
        """Test that max_backup_count can be zero (no backups)."""
        config = LogConfig(service_name="test", max_backup_count=0)

        assert config.max_backup_count == 0

    def test_very_large_queue_size(self):
        """Test that very large queue size is accepted."""
        config = LogConfig(service_name="test", queue_size=1000000)

        assert config.queue_size == 1000000

    def test_very_small_file_size(self):
        """Test that small file size is accepted."""
        config = LogConfig(service_name="test", max_file_size_mb=1)

        assert config.max_file_size_mb == 1

    def test_default_context_empty_dict(self):
        """Test that default_context can be empty."""
        config = LogConfig(service_name="test", default_context={})

        assert config.default_context == {}

    def test_default_context_with_nested_values(self):
        """Test that default_context can contain nested structures."""
        context = {
            "user": {"id": 123, "name": "John"},
            "tags": ["production", "critical"],
            "metadata": {"region": "us-east-1"},
        }

        config = LogConfig(service_name="test", default_context=context)

        assert config.default_context["user"]["id"] == 123
        assert config.default_context["tags"] == ["production", "critical"]
        assert config.default_context["metadata"]["region"] == "us-east-1"


class TestConfigImmutability:
    """Tests for configuration immutability (dataclass frozen)."""

    def test_config_is_dataclass(self):
        """Test that LogConfig is a dataclass."""
        import dataclasses

        assert dataclasses.is_dataclass(LogConfig)

    def test_config_fields_accessible(self):
        """Test that all config fields are accessible."""
        config = LogConfig(service_name="test")

        # All fields should be accessible
        _ = config.service_name
        _ = config.environment
        _ = config.version
        _ = config.level
        _ = config.console_enabled
        _ = config.console_format
        _ = config.console_colors
        _ = config.file_enabled
        _ = config.file_path
        _ = config.max_file_size_mb
        _ = config.max_backup_count
        _ = config.async_enabled
        _ = config.queue_size
        _ = config.default_context

    def test_config_repr(self):
        """Test that config has useful repr."""
        config = LogConfig(service_name="test-service")
        repr_str = repr(config)

        assert "LogConfig" in repr_str
        assert "test-service" in repr_str
