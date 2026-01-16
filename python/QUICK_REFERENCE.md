# Agora Log - Quick Reference

## Installation

```bash
pip install agora-log
```

## Basic Setup

```python
from agora_log import initialize, get_logger, LogConfig

# Initialize once at app startup
config = LogConfig(service_name="my-service")
initialize(config)

# Get logger anywhere
logger = get_logger(__name__)
```

## Logging Methods

```python
logger.debug("Debug info", key="value")
logger.info("Info message", status="ok")
logger.warning("Warning", threshold=90)
logger.error("Error occurred", code="E001")
logger.critical("Critical failure", component="auth")
```

## Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exception=e)
```

## Context Management

```python
# Add context
user_logger = logger.with_context(user_id="123")
user_logger.info("User action")  # Includes user_id

# Nested context
req_logger = user_logger.with_context(request_id="req-456")
req_logger.info("Processing")  # Includes user_id and request_id
```

## Timer

```python
with logger.timer("Database query"):
    result = db.execute()
# Automatically logs duration_ms
```

## Configuration

### From Code

```python
from agora_log import LogConfig, LogLevel
from pathlib import Path

config = LogConfig(
    service_name="market-data",
    environment="production",
    version="1.2.3",
    level=LogLevel.INFO,
    file_path=Path("logs/app.log"),
    max_file_size_mb=100,
    max_backup_count=5,
)
```

### From Environment

```bash
# .env file
ENVIRONMENT=production
SERVICE_VERSION=1.2.3
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/app.log
```

```python
config = LogConfig.from_env("market-data")
```

## FastAPI Integration

```python
from fastapi import FastAPI
from agora_log import initialize, LogConfig
from agora_log.integrations.fastapi import LoggingMiddleware, get_request_logger

# Setup
config = LogConfig(service_name="api")
initialize(config)

app = FastAPI()
app.add_middleware(LoggingMiddleware)

# Use in routes
@app.get("/orders/{id}")
async def get_order(id: str):
    logger = get_request_logger()  # Has correlation_id
    logger.info("Fetching order", order_id=id)
    return {"id": id}
```

## Common Patterns

### Request Handling

```python
@app.post("/orders")
async def create_order(order: dict):
    logger = get_request_logger()

    logger.info("Order received", order_id=order["id"])

    try:
        with logger.timer("Order validation"):
            validate(order)

        with logger.timer("Order processing"):
            result = process_order(order)

        logger.info("Order created", order_id=result.id)
        return result

    except ValidationError as e:
        logger.warning("Invalid order", exception=e)
        raise
    except DatabaseError as e:
        logger.error("Database error", exception=e)
        raise
```

### Background Tasks

```python
def process_batch(batch_id: str):
    logger = get_logger(__name__).with_context(batch_id=batch_id)

    logger.info("Batch processing started", size=len(items))

    for item in items:
        item_logger = logger.with_context(item_id=item.id)

        try:
            with item_logger.timer("Item processing"):
                process_item(item)
            item_logger.info("Item processed")
        except Exception as e:
            item_logger.error("Item failed", exception=e)

    logger.info("Batch processing completed")
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `service_name` | str | Required | Service identifier |
| `environment` | str | "development" | development/staging/production |
| `version` | str | "0.0.0" | Service version |
| `level` | LogLevel | INFO | Minimum log level |
| `console_enabled` | bool | True | Enable console output |
| `console_format` | str | "json" | json or text |
| `console_colors` | bool | True | Enable ANSI colors |
| `file_enabled` | bool | True | Enable file output |
| `file_path` | Path | "logs/app.log" | Log file path |
| `max_file_size_mb` | int | 100 | Rotation threshold |
| `max_backup_count` | int | 5 | Number of backups |
| `async_enabled` | bool | True | Enable async logging |
| `queue_size` | int | 10000 | Async queue size |

## Log Output Format

```json
{
  "timestamp": "2024-01-15T12:34:56.789123Z",
  "level": "INFO",
  "message": "Order created",
  "service": "market-data",
  "environment": "production",
  "version": "1.2.3",
  "host": "server-01",
  "logger_name": "market_data.orders",
  "file": "orders.py",
  "line": 42,
  "function": "create_order",
  "correlation_id": "corr-123",
  "user_id": "user-456",
  "context": {
    "order_id": "ord-789",
    "symbol": "AAPL",
    "quantity": 100
  }
}
```

## Special Context Keys

These keys are promoted to top-level fields (not in context object):
- `correlation_id`
- `user_id`
- `trace_id`
- `span_id`

```python
logger = logger.with_context(
    correlation_id="corr-123",  # Top level
    user_id="user-456",          # Top level
    custom_key="value",          # In context
)
```

## Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | production | Environment name |
| `SERVICE_VERSION` | 1.2.3 | Service version |
| `LOG_LEVEL` | INFO | Minimum log level |
| `LOG_CONSOLE_ENABLED` | true | Enable console |
| `LOG_CONSOLE_FORMAT` | json | Console format |
| `LOG_FILE_PATH` | /var/log/app.log | Log file path |
| `LOG_MAX_FILE_SIZE_MB` | 100 | Rotation size |
| `LOG_MAX_BACKUP_COUNT` | 5 | Backup count |
| `LOG_ASYNC_ENABLED` | true | Enable async |

## Performance Tips

1. **Use INFO or higher in production**
   ```python
   level=LogLevel.INFO  # Not DEBUG
   ```

2. **Enable async logging**
   ```python
   async_enabled=True
   ```

3. **Use context wisely**
   ```python
   # Good: Reuse logger with context
   req_logger = logger.with_context(request_id=req_id)
   req_logger.info("Start")
   req_logger.info("End")

   # Avoid: Creating context per log
   logger.info("Start", request_id=req_id)
   logger.info("End", request_id=req_id)
   ```

4. **Timer for slow operations only**
   ```python
   # Use for I/O, database, external APIs
   with logger.timer("Database query"):
       db.execute()

   # Don't use for fast operations
   # result = x + y  # Too fast to time
   ```

## Troubleshooting

### Logs not appearing

Check log level:
```python
config = LogConfig(level=LogLevel.DEBUG)  # Lower the level
```

Verify handlers:
```python
config = LogConfig(
    console_enabled=True,  # Enable console
    file_enabled=True,      # Enable file
)
```

### File rotation not working

```python
config = LogConfig(
    max_file_size_mb=100,  # Must be > 0
    max_backup_count=5,     # Number of backups
)
```

### Wrong source location

Ensure you're not wrapping logger methods:
```python
# Good
logger.info("message")

# Avoid wrapping
def my_log(msg):
    logger.info(msg)  # Shows my_log, not caller
```

## Shutdown

Always shutdown gracefully:
```python
from agora_log import shutdown

# At app shutdown
shutdown()  # Flushes all queued entries
```

## More Information

- Full documentation: `IMPLEMENTATION.md`
- Examples: `examples/`
- Tests: `tests/`
