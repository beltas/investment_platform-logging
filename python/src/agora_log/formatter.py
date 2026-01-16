"""JSON formatter for log entries."""

import json
from datetime import datetime, timezone
from typing import Any

# Try to use orjson for better performance
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


def format_json(entry: dict[str, Any]) -> str:
    """
    Format a log entry as JSON.

    Returns a single-line JSON string with:
    - ISO 8601 timestamps with microseconds
    - All required fields
    - Special context keys promoted to top level
    """
    if HAS_ORJSON:
        # orjson returns bytes, decode to str
        return orjson.dumps(entry, default=_json_serializer).decode("utf-8")
    else:
        return json.dumps(entry, default=_json_serializer, ensure_ascii=False)


def format_text(entry: dict[str, Any]) -> str:
    """
    Format a log entry as human-readable text.

    Format: YYYY-MM-DD HH:MM:SS.fff [LEVEL] [service] message [key=value ...]
    """
    timestamp = entry.get("timestamp", "")
    # Parse and reformat for text output
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Milliseconds
    except Exception:
        time_str = timestamp[:23] if len(timestamp) >= 23 else timestamp

    level = entry.get("level", "INFO")
    service = entry.get("service", "")
    message = entry.get("message", "")

    # Build base message
    parts = [f"{time_str} [{level}] [{service}] {message}"]

    # Add context if present
    context = entry.get("context", {})
    if context:
        ctx_parts = [f"{k}={v}" for k, v in context.items()]
        if ctx_parts:
            parts.append(" ".join(ctx_parts))

    # Add exception if present
    if "exception" in entry:
        exc = entry["exception"]
        parts.append(f"Exception: {exc.get('type', 'Unknown')}: {exc.get('message', '')}")

    return " ".join(parts)


def _json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for non-standard types.

    Handles datetime, Path, and other common types.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "__str__"):
        return str(obj)
    else:
        return repr(obj)
