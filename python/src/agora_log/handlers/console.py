"""Console handler for logging output."""

import sys
from typing import Any, Literal

from .base import Handler
from ..formatter import format_json, format_text


class ConsoleHandler(Handler):
    """
    Handler that writes log entries to console (stdout/stderr).

    Supports both JSON and text formats with optional color coding.
    """

    def __init__(
        self,
        format: Literal["json", "text"] = "json",
        colors: bool = True,
        stream: Any = None,
    ):
        """
        Initialize console handler.

        Args:
            format: Output format ("json" or "text")
            colors: Enable ANSI color codes for text format
            stream: Output stream (defaults to stdout)
        """
        self.format = format
        self.colors = colors
        self.stream = stream or sys.stdout
        self._color_codes = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m", # Magenta
            "RESET": "\033[0m",     # Reset
        }

    def emit(self, entry: dict[str, Any]) -> None:
        """Write log entry to console."""
        try:
            if self.format == "json":
                output = format_json(entry)
            else:
                output = format_text(entry)
                # Add colors if enabled
                if self.colors and "level" in entry:
                    level = entry["level"]
                    color = self._color_codes.get(level, "")
                    reset = self._color_codes["RESET"]
                    output = f"{color}{output}{reset}"

            self.stream.write(output + "\n")
            self.stream.flush()
        except Exception:
            # Fail silently - logging should not crash the app
            pass

    def flush(self) -> None:
        """Flush the output stream."""
        try:
            self.stream.flush()
        except Exception:
            pass

    def close(self) -> None:
        """Close the handler (no-op for console)."""
        self.flush()
