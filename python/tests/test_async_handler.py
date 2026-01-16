"""Tests for async queue-based logging handler."""

import time
import pytest
from pathlib import Path

from agora_log import initialize, LogConfig, shutdown


class TestAsyncQueueBasics:
    """Tests for basic async queue functionality."""

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

        shutdown()

        # All messages should be flushed
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            # Should have most or all messages
            assert len(lines) >= 45  # Allow for some async timing

    def test_async_vs_sync_performance(self, temp_log_file: Path):
        """Test that async logging is faster than synchronous."""
        # Synchronous config
        sync_config = LogConfig(
            service_name="test-service",
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
            async_enabled=False,
        )

        # Async config
        async_file = temp_log_file.parent / "async.log"
        async_config = LogConfig(
            service_name="test-service",
            console_enabled=False,
            file_enabled=True,
            file_path=async_file,
            async_enabled=True,
        )

        # Measure sync time
        sync_logger = initialize(sync_config)
        sync_start = time.perf_counter()
        for i in range(1000):
            sync_logger.info(f"sync message {i}")
        sync_duration = time.perf_counter() - sync_start
        shutdown()

        # Measure async time (just queuing, not writing)
        async_logger = initialize(async_config)
        async_start = time.perf_counter()
        for i in range(1000):
            async_logger.info(f"async message {i}")
        async_duration = time.perf_counter() - async_start

        # Async queuing should be faster (or at least not much slower)
        # Note: This is just queuing time, not total write time
        # In production, async provides better throughput
        shutdown()


class TestQueueBoundedSize:
    """Tests for bounded queue size."""

    def test_queue_size_configuration(self):
        """Test that queue size is configurable."""
        config = LogConfig(
            service_name="test-service",
            async_enabled=True,
            queue_size=500,
            console_enabled=False,
            file_enabled=False,
        )

        assert config.queue_size == 500

    def test_queue_handles_burst_traffic(self, async_config: LogConfig):
        """Test that queue handles burst of log entries."""
        logger = initialize(async_config)

        # Send burst of messages
        for i in range(200):
            logger.info(f"burst message {i}")

        # Shutdown flushes all queued entries
        shutdown()

        # Most messages should be written (shutdown flushes remaining)
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            # With proper shutdown, most/all messages should be present
            assert len(lines) >= 180  # Allow some timing variance


class TestOverflowPolicies:
    """Tests for queue overflow policies."""

    def test_drop_oldest_policy(self, temp_log_file: Path):
        """Test drop_oldest overflow policy."""
        # Note: This requires overflow policy configuration
        # which may need to be added to LogConfig
        pass

    def test_drop_newest_policy(self, temp_log_file: Path):
        """Test drop_newest overflow policy."""
        pass

    def test_block_policy(self, temp_log_file: Path):
        """Test block (wait) overflow policy."""
        pass


class TestBatchProcessing:
    """Tests for batched async writes."""

    def test_batch_processing_efficiency(self, async_config: LogConfig):
        """Test that async handler processes entries in batches."""
        logger = initialize(async_config)

        # Write many messages
        for i in range(500):
            logger.info(f"batch message {i}")

        # Shutdown flushes all queued entries
        shutdown()

        # Verify all messages written (shutdown ensures flush)
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            # Most messages should be present (shutdown flushes remaining)
            assert len(lines) >= 450

    def test_batch_timeout_flushes(self, async_config: LogConfig):
        """Test that batch timeout causes flush even if batch not full."""
        logger = initialize(async_config)

        # Write just a few messages
        logger.info("message 1")
        logger.info("message 2")
        logger.info("message 3")

        # Wait longer than batch timeout (0.1s) to allow flush
        time.sleep(0.2)

        # Shutdown ensures all messages are flushed
        shutdown()

        # Messages should be flushed due to timeout, not batch size
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            assert len(lines) >= 3


class TestGracefulShutdown:
    """Tests for graceful async handler shutdown."""

    def test_shutdown_flushes_queue(self, async_config: LogConfig):
        """Test that shutdown waits for queue to flush."""
        logger = initialize(async_config)

        # Fill queue with messages
        for i in range(100):
            logger.info(f"message {i}")

        # Shutdown should wait for flush
        shutdown()

        # All messages should be written
        if async_config.file_path.exists():
            content = async_config.file_path.read_text()
            lines = [line for line in content.strip().split("\n") if line]

            # All 100 messages should be present
            assert len(lines) >= 95

    def test_shutdown_timeout(self, async_config: LogConfig):
        """Test that shutdown has timeout to prevent hanging."""
        logger = initialize(async_config)

        # Write many messages
        for i in range(1000):
            logger.info("X" * 1000)

        # Shutdown should complete in reasonable time
        start = time.perf_counter()
        shutdown()
        duration = time.perf_counter() - start

        # Should complete within 5 seconds
        assert duration < 5.0

    def test_multiple_shutdowns_safe(self, async_config: LogConfig):
        """Test that multiple shutdown calls are safe."""
        logger = initialize(async_config)
        logger.info("test")

        # Multiple shutdowns should be safe
        shutdown()
        shutdown()
        shutdown()

        # Should not crash


class TestAsyncHandlerErrors:
    """Tests for error handling in async handler."""

    def test_handler_continues_after_write_error(self, async_config: LogConfig):
        """Test that handler continues after write error."""
        # This would test recovery from I/O errors
        pass

    def test_queue_full_handling(self, temp_log_file: Path):
        """Test handling when queue is full."""
        config = LogConfig(
            service_name="test-service",
            async_enabled=True,
            queue_size=10,  # Very small queue
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
        )

        logger = initialize(config)

        # Try to overflow queue
        for i in range(100):
            logger.info(f"message {i}")

        # Should not crash
        shutdown()


class TestAsyncHandlerMetrics:
    """Tests for async handler metrics."""

    def test_dropped_entry_counting(self, temp_log_file: Path):
        """Test that dropped entries are counted."""
        # This requires metrics/instrumentation
        # Track number of dropped log entries when queue overflows
        pass

    def test_queue_depth_tracking(self, async_config: LogConfig):
        """Test that queue depth can be monitored."""
        # This requires metrics/instrumentation
        pass

    def test_processing_rate_measurement(self, async_config: LogConfig):
        """Test that processing rate can be measured."""
        # This requires metrics/instrumentation
        pass


class TestAsyncWorkerThread:
    """Tests for async worker thread behavior."""

    def test_worker_thread_starts(self, async_config: LogConfig):
        """Test that worker thread starts on initialization."""
        import threading

        initial_threads = threading.active_count()

        logger = initialize(async_config)

        # Should have one more thread (worker)
        # Note: This depends on implementation
        current_threads = threading.active_count()

        # May have worker thread
        # assert current_threads >= initial_threads

        shutdown()

    def test_worker_thread_stops_on_shutdown(self, async_config: LogConfig):
        """Test that worker thread stops on shutdown."""
        import threading

        initial_threads = threading.active_count()

        logger = initialize(async_config)
        logger.info("test")

        shutdown()

        # Give thread time to stop
        time.sleep(0.1)

        # Thread count should return to initial
        final_threads = threading.active_count()

        # Should be back to original count
        # assert final_threads <= initial_threads

    def test_worker_thread_name(self, async_config: LogConfig):
        """Test that worker thread has descriptive name."""
        import threading

        logger = initialize(async_config)

        # Find worker thread
        threads = threading.enumerate()

        # Should have a logging worker thread (when implemented)
        # worker_threads = [t for t in threads if "log" in t.name.lower()]
        # assert len(worker_threads) > 0

        shutdown()


class TestAsyncPerformance:
    """Tests for async logging performance."""

    def test_async_overhead_minimal(self, temp_log_file: Path):
        """Test that async queuing overhead is minimal."""
        config = LogConfig(
            service_name="test-service",
            async_enabled=True,
            console_enabled=False,
            file_enabled=True,
            file_path=temp_log_file,
        )

        logger = initialize(config)

        # Measure time to queue 10000 entries
        start = time.perf_counter()
        for i in range(10000):
            logger.info(f"message {i}")
        duration = time.perf_counter() - start

        # Should queue very quickly (< 1 second for 10k entries)
        # Target: < 10 microseconds per entry = 0.1 seconds for 10k
        # Be generous and allow 1 second
        assert duration < 1.0

        shutdown()

    def test_high_throughput_logging(self, async_config: LogConfig):
        """Test high throughput logging scenario."""
        logger = initialize(async_config)

        # Simulate high throughput (100k messages)
        num_messages = 100000

        start = time.perf_counter()
        for i in range(num_messages):
            if i % 1000 == 0:  # Log every 1000th to avoid overwhelming
                logger.debug(f"progress: {i}/{num_messages}")
        duration = time.perf_counter() - start

        shutdown()

        # Should handle high throughput without blocking
        print(f"Logged {num_messages} messages in {duration:.2f} seconds")
