# Python Logging Library Implementation

## Overview

Comprehensive implementation of the `agora-log` Python logging library for the Agora Trading Platform. This library provides structured JSON logging with automatic source location capture, context management, file rotation, and async processing.

## Implementation Summary

### Core Components Implemented

#### 1. **Logger Class** (`logger.py`)
- **Source Location Capture**: Automatically captures file, line, and function for every log entry using `inspect` module
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL with runtime filtering
- **Context Management**: `with_context(**kwargs)` creates child loggers with merged context
- **Timer Context Manager**: `with logger.timer("operation"):` logs duration on exit
- **Exception Logging**: Captures exception type, message, and full stacktrace
- **Handler Integration**: Emits log entries to all configured handlers

#### 2. **Configuration** (`config.py`)
- **Dataclass-based Config**: Type-safe configuration with defaults
- **Environment Variable Loading**: `Config.from_env()` reads from env vars
- **Supported Settings**:
  - Service metadata (name, environment, version)
  - Log level filtering
  - Console output (JSON/text format, colors)
  - File output (path, rotation, async)
  - Default context

#### 3. **Handlers** (`handlers/`)

##### ConsoleHandler (`console.py`)
- Outputs to stdout/stderr
- Supports JSON and text formats
- Optional ANSI color coding for text format
- Thread-safe output

##### FileHandler (`file.py`)
- Writes JSON-formatted logs to file
- Automatic directory creation
- Thread-safe writes with lock
- Flush on demand

##### RotatingFileHandler (`rotating.py`)
- Size-based rotation (configurable MB threshold)
- Numbered backups: `app.log.1`, `app.log.2`, etc.
- Configurable backup count
- Thread-safe rotation
- Automatic cleanup of old backups

##### AsyncHandler (`async_handler.py`)
- Queue-based async processing
- Background thread for non-blocking writes
- Bounded queue (configurable size)
- Delegates to underlying handler
- Graceful shutdown with flush

#### 4. **Formatter** (`formatter.py`)
- **JSON Format**: Uses `orjson` (if available) for performance, falls back to stdlib `json`
- **Text Format**: Human-readable output with timestamp, level, service, message, context
- **Required Fields**: timestamp (ISO 8601 with microseconds), level, message, service, file, line, function
- **Special Keys**: `correlation_id`, `user_id`, `trace_id`, `span_id` promoted to top level
- **Custom Serializer**: Handles datetime, Path, and other non-JSON types

#### 5. **FastAPI Integration** (`integrations/fastapi.py`)
- **LoggingMiddleware**: ASGI middleware for request-scoped logging
- **Correlation ID Handling**: Extracts from `X-Correlation-ID` header or generates new UUID
- **Request Context**: Uses `contextvars` for request-scoped logger isolation
- **Duration Logging**: Logs request start, completion, and duration
- **Error Logging**: Captures and logs exceptions with context
- **get_request_logger()**: Access request-scoped logger from route handlers

## File Structure Created

```
python/src/agora_log/
├── __init__.py                 # Exports
├── logger.py                   # Logger class (UPDATED)
├── config.py                   # Configuration (EXISTING)
├── level.py                    # Log levels (EXISTING)
├── formatter.py                # JSON/text formatters (NEW)
├── handlers/
│   ├── __init__.py            # Handler exports (UPDATED)
│   ├── base.py                # Handler interface (EXISTING)
│   ├── console.py             # Console handler (NEW)
│   ├── file.py                # File handler (NEW)
│   ├── rotating.py            # Rotating file handler (NEW)
│   └── async_handler.py       # Async handler (NEW)
└── integrations/
    ├── __init__.py            # Integration exports (EXISTING)
    └── fastapi.py             # FastAPI middleware (NEW)
```

## Key Features Implemented

### 1. Source Location Capture (REQUIRED)
```python
# Automatically captures:
# - file: "api.py" (basename only)
# - line: 42
# - function: "process_order"

logger.info("Order processed")
# Output includes: "file": "api.py", "line": 42, "function": "process_order"
```

### 2. Context Inheritance
```python
# Parent context flows to children
parent = logger.with_context(user_id="user123")
child = parent.with_context(request_id="req456")

child.info("Processing")
# Output includes both user_id and request_id
```

### 3. Special Context Keys
```python
# These keys are promoted to top level in JSON output
logger = logger.with_context(
    correlation_id="corr-123",
    user_id="user-456",
    trace_id="trace-789",
    span_id="span-abc"
)

# JSON output:
# {
#   "correlation_id": "corr-123",  # Top level
#   "user_id": "user-456",         # Top level
#   "context": { ... }              # Other context here
# }
```

### 4. Timer Context Manager
```python
with logger.timer("Database query", table="users"):
    result = db.execute()

# Logs: duration_ms automatically calculated and included
```

### 5. Exception Logging
```python
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exception=e)

# Output includes:
# "exception": {
#   "type": "ValueError",
#   "message": "Invalid input",
#   "stacktrace": "Traceback (most recent call last):\n..."
# }
```

### 6. File Rotation
```python
config = LogConfig(
    service_name="market-data",
    file_path=Path("logs/app.log"),
    max_file_size_mb=100,  # Rotate at 100MB
    max_backup_count=5,    # Keep 5 backups
)

# Files: app.log, app.log.1, app.log.2, ..., app.log.5
```

### 7. Async Logging
```python
config = LogConfig(
    service_name="market-data",
    async_enabled=True,    # Enable async
    queue_size=10000,      # Bounded queue
)

# Log entries queued and processed by background thread
# Non-blocking writes for high-throughput scenarios
```

### 8. FastAPI Integration
```python
from fastapi import FastAPI
from agora_log import initialize, LogConfig
from agora_log.integrations.fastapi import LoggingMiddleware, get_request_logger

app = FastAPI()
app.add_middleware(LoggingMiddleware)

initialize(LogConfig(service_name="api"))

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    logger = get_request_logger()  # Has correlation_id in context
    logger.info("Fetching order", order_id=order_id)
    return {"order_id": order_id}
```

## Configuration Examples

### Basic Configuration
```python
from agora_log import initialize, LogConfig, LogLevel

config = LogConfig(
    service_name="market-data",
    environment="production",
    version="1.2.3",
    level=LogLevel.INFO,
)

logger = initialize(config)
```

### Environment-Based Configuration
```bash
# .env file
ENVIRONMENT=production
SERVICE_VERSION=1.2.3
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/app.log
LOG_MAX_FILE_SIZE_MB=50
```

```python
config = LogConfig.from_env("market-data")
logger = initialize(config)
```

### File-Only Logging (No Console)
```python
config = LogConfig(
    service_name="background-worker",
    console_enabled=False,
    file_enabled=True,
    file_path=Path("logs/worker.log"),
)
```

### Development Mode (Text Console)
```python
config = LogConfig(
    service_name="dev-service",
    console_enabled=True,
    console_format="text",
    console_colors=True,
    file_enabled=False,
)
```

## Thread Safety

All components are thread-safe:
- **FileHandler**: Uses `threading.Lock` for file writes
- **RotatingFileHandler**: Locks during rotation
- **AsyncHandler**: Thread-safe queue
- **Logger**: Stateless logging (context stored in instances)

## Performance Optimizations

1. **orjson**: Fast JSON serialization (falls back to stdlib)
2. **Source Location Caching**: Hostname cached globally
3. **Async Handler**: Non-blocking writes for high throughput
4. **Bounded Queue**: Prevents memory exhaustion
5. **Lazy Handler Initialization**: Only create configured handlers

## Testing Coverage

All test files from the existing test suite should pass:
- `test_logger.py` - Core logger functionality
- `test_handlers.py` - Handler implementations
- `test_rotation.py` - File rotation (if exists)
- `test_formatter.py` - JSON/text formatting
- `test_config.py` - Configuration loading
- `test_context.py` - Context management
- `test_integrations_fastapi.py` - FastAPI middleware
- `test_async.py` - Async handler (if exists)

## Usage Examples

### Basic Logging
```python
from agora_log import initialize, get_logger, LogConfig

# Initialize once at startup
config = LogConfig(service_name="market-data")
initialize(config)

# Get logger anywhere in the code
logger = get_logger("market_data.prices")

logger.debug("Starting price fetch")
logger.info("Fetched prices", symbol="AAPL", count=100)
logger.warning("Rate limit approaching", remaining=10)
logger.error("API error", exception=e)
logger.critical("Service unavailable")
```

### Context Management
```python
# Request-scoped logging
request_logger = logger.with_context(
    request_id="req-123",
    user_id="user-456"
)

request_logger.info("Processing request")
# All logs include request_id and user_id

# Nested contexts
db_logger = request_logger.with_context(component="database")
db_logger.info("Executing query")
# Includes request_id, user_id, and component
```

### Timer Usage
```python
# Measure operation duration
with logger.timer("Market data fetch", symbol="AAPL"):
    prices = fetch_prices("AAPL")

# Automatically logs:
# {
#   "message": "Market data fetch",
#   "context": {
#     "symbol": "AAPL",
#     "duration_ms": 125.43
#   }
# }
```

### Exception Handling
```python
try:
    process_order(order)
except ValidationError as e:
    logger.error("Order validation failed", exception=e, order_id=order.id)
except DatabaseError as e:
    logger.critical("Database error", exception=e, query=query)
```

## Integration with Agora Platform

This logging library is designed to integrate with:
- **Market Data Service** (Python/FastAPI)
- **Analysis Engine** (Python/FastAPI + ML)
- **Recommendation Engine** (Python/FastAPI)
- **Time Series Analysis** (Python/FastAPI)

All Python microservices should use this library for consistent logging across the platform.

## Migration from Standard Logging

```python
# Before (stdlib logging)
import logging
logger = logging.getLogger(__name__)
logger.info("Message", extra={"key": "value"})

# After (agora-log)
from agora_log import get_logger
logger = get_logger(__name__)
logger.info("Message", key="value")
```

## Future Enhancements

Potential improvements (not implemented):
- OpenTelemetry integration (stub exists)
- Structured logging adapters for popular libraries
- Log sampling for high-volume scenarios
- Remote log shipping (Elasticsearch, Loki)
- Metric extraction from logs

## Dependencies

- **Required**: None (pure Python 3.11+)
- **Optional**:
  - `orjson>=3.9.0` - Fast JSON serialization
  - `fastapi>=0.100.0` - FastAPI integration
  - `starlette>=0.27.0` - ASGI middleware

## Production Checklist

Before deploying to production:
- [ ] Set `LOG_LEVEL=INFO` or higher (not DEBUG)
- [ ] Configure file rotation (`max_file_size_mb`, `max_backup_count`)
- [ ] Enable async logging (`async_enabled=True`) for high-throughput services
- [ ] Set proper `file_path` with write permissions
- [ ] Configure log retention/cleanup (external)
- [ ] Set up log aggregation (Loki, Elasticsearch, CloudWatch)
- [ ] Test thread safety under load
- [ ] Verify source location accuracy
- [ ] Check log volume and adjust sampling if needed

## Troubleshooting

### Logs not appearing
- Check `LOG_LEVEL` - ensure it's not filtering out messages
- Verify `console_enabled` or `file_enabled` is True
- Check file permissions for log directory

### File rotation not working
- Verify `max_file_size_mb > 0`
- Check disk space
- Ensure write permissions on log directory

### Source location shows wrong file
- Check stack depth in `_capture_source_location()`
- Ensure not wrapping logger methods

### Performance issues
- Enable async logging (`async_enabled=True`)
- Reduce log level in production
- Use `orjson` for faster JSON serialization
- Increase `queue_size` if dropping messages

## Notes

- All log entries are JSON-formatted when written to file
- Console can use text format for development
- Source location (file, line, function) is REQUIRED and always captured
- Context is inherited but can be overridden
- Handlers are created once at initialization
- Thread-safe for concurrent logging
- Graceful shutdown flushes all queued entries
