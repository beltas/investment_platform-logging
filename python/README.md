# agora-log - Python Logging Library

Python implementation of the Agora Trading Platform logging library.

## Features

- Structured JSON logging with ISO 8601 timestamps
- Automatic source location capture (file, line, function) - **REQUIRED in all log entries**
- Context inheritance with `with_context()`
- Timer context manager for duration logging
- Dual output (console + file)
- Size-based file rotation with numbered backups
- Async logging with bounded queues
- FastAPI middleware with correlation ID
- Thread-safe concurrent logging

## Requirements

- **Python**: 3.11+

### Dependencies

**Production:**
- `orjson` (optional) - Fast JSON serialization

**Development:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting

**Optional:**
- `fastapi` - For FastAPI middleware integration
- `starlette` - Required by FastAPI middleware

## Installation

### Option 1: From Git Repository

```bash
# Basic installation
pip install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python

# With FastAPI integration
pip install "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python[fastapi]"

# Specific version
pip install git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python
```

### Option 2: Local Development

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging/python

# Install in editable mode
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# With FastAPI support
pip install -e ".[fastapi]"

# With all extras
pip install -e ".[dev,fastapi]"
```

## Testing

### Run All Tests

```bash
cd investment_platform-logging/python

# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=agora_log --cov-report=html

# Run specific test file
pytest tests/test_logger.py

# Run specific test
pytest tests/test_logger.py::test_info_logging
```

### Test Coverage

The test suite includes:
- `test_logger.py` - Core logger functionality
- `test_handlers.py` - Console and file handlers
- `test_rotation.py` - File rotation
- `test_formatter.py` - JSON/text formatting
- `test_config.py` - Configuration
- `test_context.py` - Context inheritance
- `test_timer.py` - Timer context manager
- `test_source_location.py` - Source location capture
- `test_integration.py` - End-to-end tests
- `test_integrations_fastapi.py` - FastAPI middleware

## Quick Start

```python
from agora_log import initialize, get_logger, shutdown, LogConfig, LogLevel
from pathlib import Path

# Option 1: Manual configuration
config = LogConfig(
    service_name="market-data-service",
    environment="production",
    version="1.2.3",
    level=LogLevel.INFO,
    console_enabled=True,
    console_format="json",
    file_enabled=True,
    file_path=Path("logs/app.log"),
    max_file_size_mb=100,
    max_backup_count=5,
)

# Option 2: From environment variables
# config = LogConfig.from_env("market-data-service")

# Initialize once at startup
initialize(config)

# Get a logger
logger = get_logger("agora.market_data.api")

# Log messages with context
logger.info("Price fetched", symbol="AAPL", price=150.25)

# Create child logger with additional context
request_logger = logger.with_context(
    request_id="req-12345",
    user_id="user-789",
)
request_logger.info("Processing request")

# Timer context manager
with logger.timer("Database query"):
    result = db.execute("SELECT * FROM prices")
# Automatically logs duration

# Exception logging
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exception=e, operation="fetch_prices")

# Shutdown gracefully (flushes all queued entries)
shutdown()
```

### FastAPI Integration

```python
from fastapi import FastAPI
from agora_log import initialize, LogConfig
from agora_log.integrations.fastapi import LoggingMiddleware, get_request_logger

# Initialize logging
config = LogConfig(service_name="api-gateway")
initialize(config)

app = FastAPI()

# Add logging middleware (handles correlation ID)
app.add_middleware(LoggingMiddleware)

@app.get("/prices/{symbol}")
async def get_price(symbol: str):
    # Get request-scoped logger with correlation ID
    logger = get_request_logger()

    logger.info("Fetching price", symbol=symbol)

    with logger.timer("Database query"):
        price = await db.get_price(symbol)

    logger.info("Price retrieved", symbol=symbol, price=price)
    return {"symbol": symbol, "price": price}

@app.get("/health")
async def health():
    logger = get_request_logger()
    logger.debug("Health check")
    return {"status": "ok"}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENVIRONMENT` | `development` | Environment name |
| `SERVICE_VERSION` | `0.0.0` | Service version |
| `LOG_CONSOLE_ENABLED` | `true` | Enable console output |
| `LOG_CONSOLE_FORMAT` | `json` | Console format (json or text) |
| `LOG_CONSOLE_COLORS` | `true` | Enable ANSI colors in text format |
| `LOG_FILE_ENABLED` | `true` | Enable file output |
| `LOG_FILE_PATH` | `logs/app.log` | Log file path |
| `LOG_MAX_FILE_SIZE_MB` | `100` | Max file size before rotation |
| `LOG_MAX_BACKUP_COUNT` | `5` | Number of backup files to keep |
| `LOG_ASYNC_ENABLED` | `true` | Enable async logging |
| `LOG_QUEUE_SIZE` | `10000` | Async queue size |

## Log Output Format

### JSON (File/Production)

```json
{
  "timestamp": "2024-01-15T12:34:56.789123Z",
  "level": "INFO",
  "message": "Price fetched",
  "service": "market-data-service",
  "environment": "production",
  "version": "1.2.3",
  "host": "server-01",
  "logger_name": "agora.market_data.api",
  "file": "prices.py",
  "line": 42,
  "function": "fetch_price",
  "correlation_id": "corr-789",
  "user_id": "user-123",
  "context": {
    "symbol": "AAPL",
    "price": 150.25
  }
}
```

### Text (Console/Development)

```
[2024-01-15 12:34:56.789] [INFO] [market-data-service] Price fetched (symbol=AAPL, price=150.25)
```

## API Reference

### Core Functions

```python
from agora_log import (
    initialize,      # Initialize logging system
    get_logger,      # Get a named logger
    shutdown,        # Flush and close all handlers
    LogConfig,       # Configuration dataclass
    LogLevel,        # Log level enum
)
```

### Logger Methods

```python
logger = get_logger("my.module")

# Log at different levels
logger.debug("Debug message", key="value")
logger.info("Info message", key="value")
logger.warning("Warning message", key="value")
logger.error("Error message", key="value", exception=exc)
logger.critical("Critical message", key="value")

# Create child logger with context
child = logger.with_context(request_id="123", user_id="456")

# Timer context manager
with logger.timer("operation name"):
    # ... timed code ...
```

### FastAPI Integration

```python
from agora_log.integrations.fastapi import (
    LoggingMiddleware,    # ASGI middleware
    get_request_logger,   # Get request-scoped logger
)
```

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Implementation details
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference guide
- [examples/](examples/) - Usage examples
- [../docs/DESIGN.md](../docs/DESIGN.md) - API design specification
