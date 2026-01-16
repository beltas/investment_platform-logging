"""Rotating file handler with size-based rotation."""

import os
import threading
from pathlib import Path
from typing import Any

from .base import Handler
from ..formatter import format_json


class RotatingFileHandler(Handler):
    """
    Handler that rotates log files based on size.

    When the current log file reaches max_bytes, it is rotated to
    filename.1, previous .1 becomes .2, etc.

    Thread-safe rotation and writes.
    """

    def __init__(
        self,
        file_path: Path,
        max_bytes: int,
        backup_count: int,
    ):
        """
        Initialize rotating file handler.

        Args:
            file_path: Path to the log file
            max_bytes: Maximum file size before rotation (in bytes)
            backup_count: Number of backup files to keep
        """
        self.file_path = Path(file_path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        self._file = None
        self._current_size = 0

        # Create parent directories if they don't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file and get current size
        self._open()

    def _open(self) -> None:
        """Open the log file for writing."""
        # Get current size if file exists
        if self.file_path.exists():
            self._current_size = self.file_path.stat().st_size
        else:
            self._current_size = 0

        self._file = open(self.file_path, "a", encoding="utf-8")

    def _should_rotate(self, message_size: int) -> bool:
        """Check if rotation is needed."""
        return self.max_bytes > 0 and (self._current_size + message_size) > self.max_bytes

    def _do_rotate(self) -> None:
        """
        Perform file rotation.

        Renames:
          app.log -> app.log.1
          app.log.1 -> app.log.2
          ...
          app.log.N-1 -> app.log.N
        """
        # Close current file
        if self._file and not self._file.closed:
            self._file.close()

        # Rotate backup files (start from highest number)
        for i in range(self.backup_count - 1, 0, -1):
            src = Path(f"{self.file_path}.{i}")
            dst = Path(f"{self.file_path}.{i + 1}")
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)

        # Rotate current file to .1
        if self.file_path.exists():
            backup = Path(f"{self.file_path}.1")
            if backup.exists():
                backup.unlink()
            self.file_path.rename(backup)

        # Open new file
        self._current_size = 0
        self._file = open(self.file_path, "a", encoding="utf-8")

    def emit(self, entry: dict[str, Any]) -> None:
        """Write log entry to file with rotation check."""
        try:
            output = format_json(entry) + "\n"
            message_size = len(output.encode("utf-8"))

            with self._lock:
                # Check if rotation is needed
                if self._should_rotate(message_size):
                    self._do_rotate()

                # Write to file
                if self._file and not self._file.closed:
                    self._file.write(output)
                    self._file.flush()
                    self._current_size += message_size
        except Exception:
            # Fail silently - logging should not crash the app
            pass

    def flush(self) -> None:
        """Flush the file buffer."""
        try:
            with self._lock:
                if self._file and not self._file.closed:
                    self._file.flush()
        except Exception:
            pass

    def close(self) -> None:
        """Close the file handler."""
        try:
            with self._lock:
                if self._file and not self._file.closed:
                    self._file.flush()
                    self._file.close()
        except Exception:
            pass
