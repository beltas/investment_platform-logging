# Agora Trading Platform Logging Library

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![C++](https://img.shields.io/badge/C++-23-blue.svg)](https://isocpp.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A unified, multi-language logging library for the Agora Trading Platform microservices architecture. Provides consistent, structured logging across Python, C++, and JavaScript/TypeScript services.

## Overview

The `investment_platform-logging` library enables:

- **Unified API** across Python, C++, and JavaScript/TypeScript
- **Context injection** - initialization parameters automatically included in all logs
- **Dual output** - simultaneous logging to files (JSON) and console (JSON or text)
- **Size-based rotation** - automatic file rotation with configurable size and backup count
- **High performance** - async logging, compile-time optimizations, thread-safe
- **Framework integrations** - FastAPI, gRPC, Express, NestJS, React

## Installation

The library supports multiple installation methods across all three languages.

**Quick install from Git:**

```bash
# Python
pip install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python

# JavaScript/TypeScript
npm install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js

# C++ (via CMake FetchContent - see full docs)
```

For detailed installation instructions including local development, specific versions, and troubleshooting, see the [Installation Guide](docs/INSTALLATION.md).

## Quick Start

### Python

**Installation:**
```bash
pip install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python
```

**Usage:**

```python
from agora_log import initialize, get_logger, LogConfig

config = LogConfig(
    service_name="market-data-service",
    environment="production",
    version="1.2.3"
)
initialize(config)

logger = get_logger("agora.market_data.api")
logger.info("Price fetched", symbol="AAPL", price=150.25)
```

### C++

**Installation via CMake FetchContent:**

```cmake
include(FetchContent)
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG main
  SOURCE_SUBDIR cpp
)
FetchContent_MakeAvailable(agora_log)
```

**Usage:**

```cpp
#include <agora/log/logger.hpp>

auto logger = agora::log::get_logger("agora.portfolio.main");
logger.info("Server starting", {{"grpc_port", 50052}});
```

### JavaScript/TypeScript

**Installation:**
```bash
npm install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js
```

**Usage:**

```typescript
import { initialize, getLogger } from '@agora/logger';

initialize({
  serviceName: 'notification-service',
  environment: 'production',
  version: '1.0.0'
});

const logger = getLogger('agora.notification.service');
logger.info('Email sent', { userId: 'user-123' });
```

## Log Format

All logs follow a consistent JSON structure:

```json
{
  "timestamp": "2024-12-31T10:30:45.123456Z",
  "level": "INFO",
  "message": "Price data fetched successfully",
  "service": "market-data-service",
  "environment": "production",
  "version": "1.2.3",
  "host": "market-data-pod-abc123",
  "logger_name": "agora.market_data.ingestion",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "file": "ingestion.py",
  "line": 145,
  "function": "fetch_prices",
  "context": {
    "symbol": "AAPL",
    "records_count": 252
  }
}
```

### Required Fields

Every log entry **must** include:
- `timestamp` - ISO 8601 UTC timestamp with microseconds
- `level` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` - Human-readable message
- `service` - Service name
- `file` - Source file name
- `line` - Source line number
- `function` - Function/method name

## Key Features

### Context Injection

Set context once, included in all subsequent logs:

```python
# Python
logger = get_logger("api").with_context(
    correlation_id="550e8400-e29b-41d4-a716-446655440000",
    user_id="user-123"
)
logger.info("Processing request")  # correlation_id and user_id included
```

### Dual Output

Logs are written to both files (JSON) and console simultaneously:

```python
config = LogConfig(
    service_name="market-data",
    console_enabled=True,
    console_format="text",  # Human-readable for development
    file_enabled=True,
    file_path="/var/log/agora/market-data.log"
)
```

### File Rotation

Automatic rotation when file size exceeds threshold:

```python
config = LogConfig(
    file_path="/var/log/agora/app.log",
    max_file_size_mb=100,  # Rotate at 100MB
    max_backup_count=5     # Keep 5 backup files
)
```

### Operation Timing

Built-in support for measuring operation duration:

```python
# Python
with logger.timer("Database query"):
    result = db.execute_query()
# Automatically logs: "Database query completed" with duration_ms
```

```typescript
// TypeScript
const result = await logger.timer(
  'Email sent',
  async () => await emailClient.send(email)
);
```

## Performance

| Language | Mode | Target Latency |
|----------|------|----------------|
| Python | Async | < 10 microseconds |
| Node.js | Async | < 10 microseconds |
| C++ | Sync | < 2 microseconds |

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed installation instructions for all languages
- [Use Cases](docs/USE_CASES.md) - Detailed use cases and scenarios
- [Design Document](docs/DESIGN.md) - Architecture and implementation details
- [API Reference - Python](python/README.md)
- [API Reference - C++](cpp/README.md)
- [API Reference - JavaScript](js/README.md)

## Repository Structure

```
investment_platform-logging/
├── python/           # Python package (agora-log)
├── cpp/              # C++ library (libagora_log)
├── js/               # JavaScript/TypeScript package (@agora/logger)
├── examples/         # Example integrations
│   ├── python-fastapi/
│   ├── cpp-grpc/
│   └── nodejs-nestjs/
└── docs/             # Documentation
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Minimum log level |
| `LOG_CONSOLE_ENABLED` | `true` | Enable console output |
| `LOG_CONSOLE_FORMAT` | `json` | Console format: `json` or `text` |
| `LOG_FILE_ENABLED` | `true` | Enable file output |
| `LOG_FILE_PATH` | `/var/log/agora/<service>.log` | Log file path (standardized) |
| `LOG_MAX_FILE_SIZE_MB` | `100` | Max file size before rotation |
| `LOG_MAX_BACKUP_COUNT` | `5` | Number of backup files |

## Integration with Agora Platform

This library is designed for use with:

- **Market Data Service** (Python/FastAPI) - Port 50051
- **Analysis Engine** (Python/FastAPI + ML) - Port 50053
- **Portfolio Manager** (C++23) - Port 50052
- **Recommendation Engine** (Python/FastAPI) - Port 50054
- **Notification Service** (Node.js/NestJS) - Port 50055
- **Time Series Analysis** (Python/FastAPI) - Port 50056

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
