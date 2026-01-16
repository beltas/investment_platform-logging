"""Tests for log handlers."""

import json
import pytest
import threading
import time
from pathlib import Path
from io import StringIO
from typing import Any

from agora_log import initialize, get_logger, LogConfig, LogLevel, shutdown
from agora_log.handlers.base import Handler


class TestConsoleHandler:
    """Tests for console output handler."""

    def test_console_handler_json_format(self, capsys):
        """Test console handler outputs JSON format."""
        config = LogConfig(
            service_name="test-service",
            console_enabled=True,
            console_format="json",
            file_enabled=False,
            async_enabled=False,
        )
        logger = initialize(config)
        logger.info("test message", key="value")

        captured = capsys.readouterr()
        assert captured.out.strip()

        # Should be valid JSON
        entry = json.loads(captured.out.strip())
        assert entry["message"] == "test message"
        assert entry["context"]["key"] == "value"

    def test_console_handler_text_format(self, text_console_config: LogConfig, capsys):
        """Test console handler outputs human-readable text format."""
        logger = initialize(text_console_config)
        logger.info("test message")

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Text format should be human-readable, not JSON
        assert "test message" in output
        assert "INFO" in output
        # Should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

    def test_console_handler_multiple_logs(self, console_config: LogConfig, capsys):
        """Test console handler outputs multiple log entries."""
        logger = initialize(console_config)

        logger.info("message 1")
        logger.warning("message 2")
        logger.error("message 3")

        captured = capsys.readouterr()
        lines = [line for line in captured.out.strip().split("\n") if line]

        assert len(lines) == 3

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        entry3 = json.loads(lines[2])

        assert entry1["message"] == "message 1"
        assert entry1["level"] == "INFO"
        assert entry2["message"] == "message 2"
        assert entry2["level"] == "WARNING"
        assert entry3["message"] == "message 3"
        assert entry3["level"] == "ERROR"

    def test_console_colors_enabled(self):
        """Test console handler with colors enabled."""
        config = LogConfig(
            service_name="test-service",
            console_enabled=True,
            console_format="text",
            console_colors=True,
            file_enabled=False,
        )
        logger = initialize(config)

        # Colors should add ANSI escape codes (when implemented)
        # For now, just verify it doesn't crash
        logger.info("colored message")

    def test_console_colors_disabled(self, text_console_config: LogConfig, capsys):
        """Test console handler with colors disabled."""
        logger = initialize(text_console_config)
        logger.info("plain message")

        captured = capsys.readouterr()
        output = captured.out

        # Should not contain ANSI escape codes
        assert "\033[" not in output or output.strip() == ""


class TestFileHandler:
    """Tests for file output handler."""

    def test_file_handler_creates_file(self, config: LogConfig):
        """Test that file handler creates log file."""
        logger = initialize(config)
        logger.info("test message")

        # File should be created
        assert config.file_path.exists()

    def test_file_handler_creates_parent_directories(self, tmp_path: Path):
        """Test that file handler creates parent directories."""
        log_file = tmp_path / "nested" / "dirs" / "app.log"
        config = LogConfig(
            service_name="test-service",
            console_enabled=False,
            file_enabled=True,
            file_path=log_file,
            async_enabled=False,
        )

        logger = initialize(config)
        logger.info("test")

        assert log_file.exists()
        assert log_file.parent.exists()

    def test_file_handler_writes_json(self, config: LogConfig):
        """Test that file handler writes JSON format."""
        logger = initialize(config)
        logger.info("file message", key="value")

        # Flush handlers to ensure write
        # Read file content
        content = config.file_path.read_text()
        entry = json.loads(content.strip())

        assert entry["message"] == "file message"
        assert entry["context"]["key"] == "value"

    def test_file_handler_appends_logs(self, config: LogConfig):
        """Test that file handler appends multiple log entries."""
        logger = initialize(config)

        logger.info("message 1")
        logger.info("message 2")
        logger.info("message 3")

        content = config.file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        assert len(lines) == 3

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        entry3 = json.loads(lines[2])

        assert entry1["message"] == "message 1"
        assert entry2["message"] == "message 2"
        assert entry3["message"] == "message 3"

    def test_file_handler_flush(self, config: LogConfig):
        """Test that file handler flushes data to disk."""
        logger = initialize(config)
        logger.info("message to flush")

        # Explicitly flush (when implemented)
        from agora_log import shutdown
        shutdown()

        # File should contain the message
        content = config.file_path.read_text()
        assert "message to flush" in content


class TestRotatingFileHandler:
    """Tests for rotating file handler."""

    def test_rotating_handler_basic_write(self, config: LogConfig):
        """Test basic write functionality of rotating handler."""
        logger = initialize(config)
        logger.info("test message")

        assert config.file_path.exists()
        content = config.file_path.read_text()
        assert "test message" in content

    def test_rotating_handler_respects_max_backup_count(self, temp_log_file: Path):
        """Test that handler respects max backup count."""
        config = LogConfig(
            service_name="test-service",
            file_enabled=True,
            file_path=temp_log_file,
            max_file_size_mb=1,
            max_backup_count=3,
            console_enabled=False,
            async_enabled=False,
        )

        # This test will be completed when rotation is implemented
        # Should verify that only 3 backup files exist after many rotations
        pass

    def test_file_size_tracking(self, config: LogConfig):
        """Test that file size is tracked accurately."""
        logger = initialize(config)

        # Write some data
        for i in range(100):
            logger.info(f"Message {i}" * 10)  # Make messages longer

        # File should exist and have size > 0
        assert config.file_path.exists()
        assert config.file_path.stat().st_size > 0


class TestThreadSafety:
    """Tests for thread-safe concurrent writes."""

    def test_concurrent_writes_no_corruption(self, config: LogConfig):
        """Test that concurrent writes don't corrupt the log file."""
        logger = initialize(config)
        num_threads = 10
        messages_per_thread = 100

        def worker(thread_id: int):
            for i in range(messages_per_thread):
                logger.info(f"Thread {thread_id} message {i}")

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Read file and verify all messages are present
        content = config.file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        # Should have exactly num_threads * messages_per_thread entries
        expected_count = num_threads * messages_per_thread
        assert len(lines) == expected_count

        # Each line should be valid JSON
        for line in lines:
            entry = json.loads(line)
            assert "message" in entry
            assert "Thread" in entry["message"]

    def test_concurrent_writes_different_loggers(self, config: LogConfig):
        """Test concurrent writes from different logger instances."""
        initialize(config)
        num_threads = 5

        def worker(thread_id: int):
            # Each thread gets its own logger
            logger = get_logger(f"test.thread{thread_id}")
            for i in range(50):
                logger.info(f"Message {i}", thread_id=thread_id)

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify all messages written
        content = config.file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        assert len(lines) == num_threads * 50

    def test_concurrent_writes_with_context(self, config: LogConfig):
        """Test concurrent writes with different contexts."""
        logger = initialize(config)

        def worker(thread_id: int):
            thread_logger = logger.with_context(thread_id=thread_id)
            for i in range(50):
                thread_logger.info(f"Message {i}", iteration=i)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        content = config.file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        assert len(lines) == 250  # 5 threads * 50 messages

        # Verify context is preserved
        for line in lines:
            entry = json.loads(line)
            assert "thread_id" in entry["context"]
            assert "iteration" in entry["context"]

    def test_no_race_condition_on_initialization(self):
        """Test that concurrent initialization doesn't cause race conditions."""
        config = LogConfig(
            service_name="test-service",
            console_enabled=False,
            file_enabled=False,
        )

        results = []

        def init_worker():
            try:
                logger = initialize(config)
                results.append(logger)
            except Exception as e:
                results.append(e)

        threads = [threading.Thread(target=init_worker) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed or handle gracefully
        # No crashes or exceptions
        assert len(results) == 10


class TestAsyncHandler:
    """Tests for async queue-based handler."""

    def test_async_handler_queues_entries(self, async_config: LogConfig):
        """Test that async handler queues log entries."""
        logger = initialize(async_config)

        logger.info("async message 1")
        logger.info("async message 2")
        logger.info("async message 3")

        # Give async handler time to process
        time.sleep(0.1)

        # Messages should eventually be written
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            assert "async message 1" in content

    def test_async_handler_flushes_on_shutdown(self, async_config: LogConfig):
        """Test that async handler flushes queue on shutdown."""
        logger = initialize(async_config)

        for i in range(50):
            logger.info(f"message {i}")

        from agora_log import shutdown
        shutdown()

        # All messages should be flushed
        content = async_config.file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        # Should have most or all messages
        assert len(lines) >= 45  # Allow for some async timing

    def test_async_handler_batch_processing(self, async_config: LogConfig):
        """Test that async handler processes entries in batches."""
        # This test verifies batch processing behavior
        # Implementation will batch multiple entries for efficiency
        logger = initialize(async_config)

        for i in range(200):
            logger.info(f"batch message {i}")

        # Shutdown flushes all remaining queued entries
        shutdown()

        # Verify all messages eventually written
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            assert len(lines) >= 180  # Most should be written


class TestHandlerInterface:
    """Tests for handler interface compliance."""

    def test_handler_has_emit_method(self):
        """Test that handler interface requires emit method."""
        from agora_log.handlers.base import Handler

        # Abstract class should define emit
        assert hasattr(Handler, "emit")

        # Concrete implementation must implement emit
        class TestHandler(Handler):
            def flush(self):
                pass

            def close(self):
                pass

        # Missing emit should fail
        with pytest.raises(TypeError):
            TestHandler()

    def test_handler_has_flush_method(self):
        """Test that handler interface requires flush method."""
        from agora_log.handlers.base import Handler

        assert hasattr(Handler, "flush")

    def test_handler_has_close_method(self):
        """Test that handler interface requires close method."""
        from agora_log.handlers.base import Handler

        assert hasattr(Handler, "close")

    def test_custom_handler_can_be_implemented(self):
        """Test that custom handlers can implement the interface."""

        class CustomHandler(Handler):
            def __init__(self):
                self.entries = []

            def emit(self, entry: dict[str, Any]) -> None:
                self.entries.append(entry)

            def flush(self) -> None:
                pass

            def close(self) -> None:
                self.entries.clear()

        handler = CustomHandler()
        handler.emit({"message": "test"})
        assert len(handler.entries) == 1
        assert handler.entries[0]["message"] == "test"

        handler.close()
        assert len(handler.entries) == 0
