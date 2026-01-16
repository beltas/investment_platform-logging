"""File handler for logging output."""

import threading
from pathlib import Path
from typing import Any

from .base import Handler
from ..formatter import format_json


class FileHandler(Handler):
    """
    Handler that writes log entries to a file.

    Thread-safe file writes with automatic directory creation.
    Always uses JSON format for file output.
    """

    def __init__(self, file_path: Path):
        """
        Initialize file handler.

        Args:
            file_path: Path to the log file
        """
        self.file_path = Path(file_path)
        self._lock = threading.Lock()
        self._file = None

        # Create parent directories if they don't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file in append mode
        self._open()

    def _open(self) -> None:
        """Open the log file for writing."""
        self._file = open(self.file_path, "a", encoding="utf-8")

    def emit(self, entry: dict[str, Any]) -> None:
        """Write log entry to file."""
        try:
            output = format_json(entry)
            with self._lock:
                if self._file and not self._file.closed:
                    self._file.write(output + "\n")
                    self._file.flush()
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
