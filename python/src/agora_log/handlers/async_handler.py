"""Async handler with queue-based processing and configurable backpressure."""

from __future__ import annotations

import queue
import sys
import threading
import time
from enum import Enum
from typing import Any, Optional, List

from .base import Handler


class QueueFullBehavior(Enum):
    """Behavior when the async queue is full."""
    DROP = "drop"          # Silently drop the log entry (default)
    BLOCK = "block"        # Block until space is available
    FALLBACK = "fallback"  # Write synchronously to underlying handler


class AsyncHandler(Handler):
    """
    Handler that queues log entries for async processing.

    Uses a background thread to process entries from a bounded queue,
    delegating actual writes to an underlying handler.

    Features:
    - Configurable queue full behavior (drop, block, fallback)
    - Batch processing for improved throughput
    - Dropped entry tracking
    - Graceful shutdown with timeout

    Args:
        underlying_handler: The handler to delegate writes to
        queue_size: Maximum queue size (default: 10000)
        on_full: Behavior when queue is full (default: DROP)
        batch_size: Number of entries to process in a batch (default: 100)
        batch_timeout: Max seconds to wait before processing partial batch (default: 0.1)
    """

    def __init__(
        self,
        underlying_handler: Handler,
        queue_size: int = 10000,
        on_full: QueueFullBehavior = QueueFullBehavior.DROP,
        batch_size: int = 100,
        batch_timeout: float = 0.1,
    ) -> None:
        self._underlying_handler: Handler = underlying_handler
        self._queue: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=queue_size)
        self._on_full: QueueFullBehavior = on_full
        self._batch_size: int = batch_size
        self._batch_timeout: float = batch_timeout
        self._stop: bool = False
        self._dropped_count: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._thread: threading.Thread = threading.Thread(
            target=self._process_queue,
            daemon=True,
            name="AsyncLogHandler"
        )
        self._thread.start()

    @property
    def dropped_count(self) -> int:
        """Number of log entries dropped due to queue overflow."""
        return self._dropped_count

    def _process_queue(self) -> None:
        """Background thread that processes queued entries in batches."""
        batch: List[dict[str, Any]] = []
        last_flush_time: float = time.monotonic()

        while not self._stop:
            try:
                # Calculate remaining time until we should flush the batch
                time_since_flush = time.monotonic() - last_flush_time
                timeout = max(0.01, self._batch_timeout - time_since_flush)

                try:
                    entry = self._queue.get(timeout=timeout)

                    if entry is None:  # Sentinel value to stop
                        # Flush remaining batch before exiting
                        if batch:
                            self._flush_batch(batch)
                        break

                    batch.append(entry)
                    self._queue.task_done()

                except queue.Empty:
                    pass  # Timeout - check if we should flush

                # Flush batch if full or timeout reached
                should_flush = (
                    len(batch) >= self._batch_size or
                    (batch and time.monotonic() - last_flush_time >= self._batch_timeout)
                )

                if should_flush and batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush_time = time.monotonic()

            except Exception as e:
                # Log errors shouldn't crash the thread
                print(f"AsyncHandler error: {e}", file=sys.stderr)
                continue

    def _flush_batch(self, batch: List[dict[str, Any]]) -> None:
        """Write a batch of entries to the underlying handler."""
        for entry in batch:
            try:
                self._underlying_handler.emit(entry)
            except Exception as e:
                print(f"AsyncHandler emit error: {e}", file=sys.stderr)

    def emit(self, entry: dict[str, Any]) -> None:
        """Queue log entry for async processing."""
        if self._stop:
            return

        try:
            if self._on_full == QueueFullBehavior.BLOCK:
                # Blocking put - wait indefinitely for space
                self._queue.put(entry)
            elif self._on_full == QueueFullBehavior.FALLBACK:
                # Try non-blocking put, fall back to sync write
                try:
                    self._queue.put_nowait(entry)
                except queue.Full:
                    # Write synchronously as fallback
                    with self._lock:
                        self._dropped_count += 1
                    try:
                        self._underlying_handler.emit(entry)
                    except Exception:
                        pass  # Don't crash on fallback failure
            else:  # DROP (default)
                # Non-blocking put, silently drop if full
                try:
                    self._queue.put_nowait(entry)
                except queue.Full:
                    with self._lock:
                        self._dropped_count += 1
        except Exception:
            pass  # Don't crash on queue errors

    def flush(self) -> None:
        """Flush all queued entries."""
        # Wait for queue to be processed (with timeout)
        try:
            # Use a timeout to prevent hanging forever
            deadline = time.monotonic() + 10.0  # 10 second timeout
            while not self._queue.empty() and time.monotonic() < deadline:
                time.sleep(0.01)
        except Exception:
            pass

        # Flush underlying handler
        self._underlying_handler.flush()

    def close(self) -> None:
        """Close the async handler gracefully."""
        # Signal thread to stop
        self._stop = True

        try:
            self._queue.put_nowait(None)  # Sentinel
        except queue.Full:
            pass  # Queue is full, thread will see _stop flag

        # Wait for thread to finish (with timeout)
        self._thread.join(timeout=5.0)

        if self._thread.is_alive():
            print("AsyncHandler: Worker thread did not terminate in time", file=sys.stderr)

        # Flush and close underlying handler
        self._underlying_handler.flush()
        self._underlying_handler.close()

        # Report dropped entries
        if self._dropped_count > 0:
            print(f"AsyncHandler: Dropped {self._dropped_count} log entries due to queue overflow", file=sys.stderr)
