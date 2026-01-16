# C++ Logging Library - Quick Start Guide

## Installation

### Using CMake

```cmake
find_package(agora_log REQUIRED)
target_link_libraries(your_target PRIVATE agora::log)
```

### Using Conan

```bash
conan install agora_log/0.1.0@agora/stable
```

## Basic Usage

```cpp
#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>

int main() {
    // 1. Create configuration
    agora::log::Config config;
    config.service_name = "my-service";
    config.environment = "production";
    config.version = "1.0.0";
    config.level = agora::log::Level::Info;
    config.file_path = "/var/log/agora/my-service.log";

    // 2. Initialize logging
    auto result = agora::log::initialize(config);
    if (!result) {
        std::cerr << "Failed to init: " << result.error().message << '\n';
        return 1;
    }

    // 3. Get a logger
    auto logger = agora::log::get_logger("my.component");

    // 4. Log messages
    logger.info("Application started");
    logger.debug("Debug info", {{"key", "value"}});
    logger.warning("Warning message");
    logger.error("Error occurred", {{"code", std::int64_t{500}}});

    // 5. Shutdown
    agora::log::shutdown();
    return 0;
}
```

## Configuration from Environment

```cpp
// Reads AGORA_LOG_* environment variables
auto config = agora::log::Config::from_env("my-service");

if (config) {
    agora::log::initialize(*config);
}
```

## Context Usage

### Direct Context

```cpp
logger.info("User logged in", {
    {"user_id", "user-123"},
    {"ip_address", "192.168.1.1"},
    {"session_id", "sess-456"}
});
```

### Fluent Builder

```cpp
#include <agora/log/context.hpp>

auto ctx = agora::log::ctx()
    .correlation_id("abc-123")
    .user_id("user-456")
    .trace_id("trace-789")
    .add("custom_key", "custom_value")
    .add("count", std::int64_t{42})
    .add("price", 99.99)
    .add("active", true)
    .build();

logger.info("Complex event", ctx);
```

### Child Logger

```cpp
auto request_logger = logger.with_context({
    {"request_id", "req-123"},
    {"user_id", "user-456"}
});

// All logs from request_logger include request_id and user_id
request_logger.info("Processing request");
request_logger.info("Request completed");
```

## Timer for Duration Logging

```cpp
{
    auto timer = logger.timer("Database query", {
        {"table", "users"},
        {"operation", "select"}
    });

    // ... perform database query ...

}  // Automatically logs duration on destruction
```

### Cancellable Timer

```cpp
auto timer = logger.timer("Operation");

try {
    risky_operation();
} catch (...) {
    timer.cancel();  // Don't log duration on failure
    throw;
}
```

## Exception Logging

```cpp
try {
    throw std::runtime_error("Something went wrong");
} catch (const std::exception& ex) {
    logger.error("Operation failed", ex, {
        {"operation", "process_data"},
        {"retry_count", std::int64_t{3}}
    });
}
```

## Log Levels

```cpp
logger.debug("Debug message");     // Level::Debug
logger.info("Info message");       // Level::Info
logger.warning("Warning message"); // Level::Warning
logger.error("Error message");     // Level::Error
logger.critical("Critical");       // Level::Critical
```

## Configuration Options

```cpp
agora::log::Config config;

// Required
config.service_name = "my-service";

// Optional (with defaults)
config.environment = "development";  // or "staging", "production"
config.version = "0.0.0";
config.level = Level::Info;

// Console output
config.console_enabled = true;
config.console_json = true;  // false for human-readable text

// File output
config.file_enabled = true;
config.file_path = "/var/log/agora/my-service.log";
config.max_file_size_mb = 100;  // Rotate at 100 MB
config.max_backup_count = 5;     // Keep 5 backup files

// Default context (included in all logs)
config.default_context = {
    {"datacenter", "us-east-1"},
    {"cluster", "prod-01"}
};
```

## Environment Variables

```bash
# Log level
export AGORA_LOG_LEVEL=INFO

# Environment name
export AGORA_LOG_ENVIRONMENT=production

# Service version
export AGORA_LOG_VERSION=1.2.3

# Console settings
export AGORA_LOG_CONSOLE_ENABLED=true
export AGORA_LOG_CONSOLE_JSON=true

# File settings
export AGORA_LOG_FILE_ENABLED=true
export AGORA_LOG_FILE_PATH=/var/log/agora/my-service.log
export AGORA_LOG_MAX_FILE_SIZE_MB=100
export AGORA_LOG_MAX_BACKUP_COUNT=5
```

## Output Format

### JSON (File Output)

```json
{
  "timestamp": "2024-12-31T10:30:45.123456Z",
  "level": "INFO",
  "message": "User logged in",
  "service": "my-service",
  "environment": "production",
  "version": "1.0.0",
  "logger_name": "my.component",
  "file": "main.cpp",
  "line": 42,
  "function": "main",
  "context": {
    "user_id": "user-123",
    "ip_address": "192.168.1.1"
  }
}
```

### Text (Console Output)

```
[2024-12-31 10:30:45.123456] [INFO] [my-service] User logged in (user_id=user-123, ip_address=192.168.1.1)
```

## Common Patterns

### Request Logging

```cpp
void handle_request(const Request& req) {
    auto logger = agora::log::get_logger("api.handler")
        .with_context({
            {"request_id", req.id},
            {"user_id", req.user_id},
            {"endpoint", req.path}
        });

    logger.info("Request received");

    auto timer = logger.timer("Request processing");

    try {
        process(req);
        logger.info("Request completed successfully");
    } catch (const std::exception& ex) {
        timer.cancel();
        logger.error("Request failed", ex);
        throw;
    }
}
```

### Nested Operations

```cpp
void process_order(const Order& order) {
    auto logger = agora::log::get_logger("orders")
        .with_context({{"order_id", order.id}});

    logger.info("Processing order");

    {
        auto timer = logger.timer("Validate order");
        validate(order);
    }

    {
        auto timer = logger.timer("Calculate total");
        auto total = calculate_total(order);
        logger.info("Total calculated", {{"total", total}});
    }

    {
        auto timer = logger.timer("Save to database");
        save(order);
    }

    logger.info("Order processed successfully");
}
```

### Error Handling

```cpp
void risky_operation() {
    auto logger = agora::log::get_logger("operations");

    int retry_count = 0;
    const int max_retries = 3;

    while (retry_count < max_retries) {
        try {
            logger.debug("Attempting operation", {
                {"attempt", std::int64_t{retry_count + 1}}
            });

            perform_operation();

            logger.info("Operation succeeded");
            return;

        } catch (const std::exception& ex) {
            retry_count++;

            if (retry_count >= max_retries) {
                logger.error("Operation failed after retries", ex, {
                    {"retry_count", std::int64_t{retry_count}}
                });
                throw;
            }

            logger.warning("Operation failed, retrying", {
                {"error", ex.what()},
                {"retry_count", std::int64_t{retry_count}}
            });
        }
    }
}
```

## Best Practices

1. **Use hierarchical logger names**: `"service.component.subcomponent"`
2. **Create child loggers for requests**: Include correlation IDs
3. **Use timers for operations**: Automatic performance tracking
4. **Log exceptions with context**: Include operation details
5. **Set appropriate log levels**: DEBUG for dev, INFO for prod
6. **Use structured context**: Not string concatenation
7. **Shutdown gracefully**: Call `shutdown()` before exit

## Performance

- Target: < 2 microseconds per log entry
- Thread-safe: All operations are thread-safe
- Efficient: No dynamic allocation in hot path
- Async-friendly: Works in multi-threaded environments

## Troubleshooting

### Logs not appearing

Check:
1. Log level is appropriate (`config.level`)
2. Handlers are enabled (`console_enabled`, `file_enabled`)
3. File path is writable
4. `initialize()` was called successfully

### File rotation not working

Check:
1. `max_file_size_mb` is set appropriately
2. File has write permissions
3. Parent directory exists

### Compilation errors

Ensure:
1. C++23 compiler (GCC 13+, Clang 16+)
2. nlohmann/json is available
3. Headers are in include path
