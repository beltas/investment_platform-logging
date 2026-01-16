"""Base handler interface."""

from abc import ABC, abstractmethod
from typing import Any


class Handler(ABC):
    """Abstract base class for log handlers."""
    
    @abstractmethod
    def emit(self, entry: dict[str, Any]) -> None:
        """Write a log entry to the output."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered entries."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        pass
