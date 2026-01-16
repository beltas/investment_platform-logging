# C++ Logging Library - Implementation Notes

## Overview

Complete implementation of the Agora Trading Platform logging library for C++23, featuring:

- **Source location capture** (file, line, function - REQUIRED fields)
- **Context injection** with fluent builder API
- **Dual output** (console + rotating file)
- **Thread-safe** operations with mutex protection
- **Size-based file rotation**
- **RAII timer** for duration logging
- **Exception logging** with type demangling

## Implementation Summary

### Header Files

1. **include/agora/log/logger.hpp** - Main logger class with source location capture
2. **include/agora/log/config.hpp** - Configuration structure
3. **include/agora/log/context.hpp** - Fluent context builder
4. **include/agora/log/level.hpp** - Log level enum and utilities
5. **include/agora/log/entry.hpp** - Log entry structure
6. **include/agora/log/formatter.hpp** - JSON and text formatters
7. **include/agora/log/timer.hpp** - RAII timer class
8. **include/agora/log/handlers/handler.hpp** - Base handler interface
9. **include/agora/log/handlers/console.hpp** - Console output handler
10. **include/agora/log/handlers/file.hpp** - File output handler
11. **include/agora/log/handlers/rotating_file.hpp** - Rotating file handler

### Source Files

1. **src/logger.cpp** - Logger implementation with global state management
2. **src/config.cpp** - Configuration loading from environment variables
3. **src/formatter.cpp** - JSON/text formatting with nlohmann/json
4. **src/context.cpp** - Context utilities (mostly header-only)
5. **src/timer.cpp** - Timer placeholder (implemented in logger.cpp)
6. **src/handlers/console.cpp** - Console handler (stdout/stderr)
7. **src/handlers/file.cpp** - File handler with directory creation
8. **src/handlers/rotating_file.cpp** - Rotating file handler

## Key Features

### 1. Source Location Capture

Uses C++20 `std::source_location` to automatically capture:
- File name (basename only, not full path)
- Line number
- Function name

Example:
```cpp
logger.info("Message");  // Automatically captures source location
```

### 2. Context Builder

Fluent API for building context:
```cpp
auto ctx = agora::log::ctx()
    .correlation_id("abc123")
    .user_id("user-456")
    .add("custom_key", value)
    .build();

logger.info("Message", ctx);
```

### 3. Context Inheritance

Child loggers inherit parent context:
```cpp
auto parent = get_logger("parent");
auto child = parent.with_context({{"request_id", "123"}});

child.info("Message");  // Includes request_id in all logs
```

### 4. RAII Timer

Automatic duration logging:
```cpp
{
    auto timer = logger.timer("Operation");
    // ... do work ...
}  // Logs duration on destruction
```

Can be cancelled:
```cpp
auto timer = logger.timer("Operation");
if (error) {
    timer.cancel();  // Don't log duration
}
```

### 5. File Rotation

Size-based rotation algorithm:
1. Check if (current_size + entry_size) > max_size
2. If yes:
   - Close current file
   - Delete oldest backup (if max_backup_count reached)
   - Rotate backups: .1 → .2, .2 → .3, etc.
   - Rename current → .1
   - Open new file
3. Write entry

### 6. Thread Safety

All file writes protected by mutex:
- Console handler: uses cout/cerr with flush
- File handler: mutex-protected writes
- Rotating file handler: mutex-protected rotation + writes

### 7. Exception Logging

Captures exception type and message:
```cpp
try {
    risky_operation();
} catch (const std::exception& ex) {
    logger.error("Failed", ex, {{"retry", 3}});
}
```

Exception type is demangled using `abi::__cxa_demangle`.

### 8. JSON Output

All file logs are JSON format:
```json
{
  "timestamp": "2024-12-31T10:30:45.123456Z",
  "level": "INFO",
  "message": "Test message",
  "service": "test-service",
  "environment": "production",
  "version": "1.0.0",
  "logger_name": "test.component",
  "file": "test.cpp",
  "line": 42,
  "function": "main",
  "context": {
    "user_id": "user-123"
  }
}
```

### 9. Console Output

Two formats:
- **JSON**: Same as file output
- **Text**: Human-readable: `[2024-12-31 10:30:45.123456] [INFO] [service] message (context)`

### 10. Configuration from Environment

```cpp
auto result = Config::from_env("service-name");
```

Reads environment variables:
- `AGORA_LOG_LEVEL` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `AGORA_LOG_ENVIRONMENT` - Environment name
- `AGORA_LOG_VERSION` - Service version
- `AGORA_LOG_CONSOLE_ENABLED` - Enable console output
- `AGORA_LOG_CONSOLE_JSON` - JSON or text console format
- `AGORA_LOG_FILE_ENABLED` - Enable file output
- `AGORA_LOG_FILE_PATH` - Log file path
- `AGORA_LOG_MAX_FILE_SIZE_MB` - Max file size before rotation
- `AGORA_LOG_MAX_BACKUP_COUNT` - Number of backup files to keep

## Design Decisions

### 1. Global State Management

- Single global config and handlers (per process)
- Loggers are lightweight (copy-friendly)
- Thread-safe access via mutex

### 2. Handler Architecture

- Abstract `Handler` base class
- Polymorphic dispatch for extensibility
- Error handling: catch exceptions in handlers to prevent crashes

### 3. Context Storage

- `std::variant<string, int64_t, double, bool>` for type safety
- Efficient copying with move semantics
- Merge on log call (default + logger + call context)

### 4. Performance Optimizations

- No dynamic allocation in log calls (except string formatting)
- Move semantics throughout
- Mutex only when writing (not during formatting)
- Level filtering before entry creation

### 5. Error Handling

- `std::expected` for initialization (can fail)
- Exceptions caught in handlers (fail gracefully)
- Logging never crashes the application

## Building

### With CMake (recommended)

```bash
cd cpp
mkdir build && cd build
conan install .. --build=missing
cmake ..
cmake --build .
```

### Simple Test

```bash
cd cpp
make -f Makefile.simple
./simple_test
```

## Testing

Run tests with:
```bash
cd build
ctest --output-on-failure
```

Tests cover:
- Logger initialization
- Log level filtering
- Source location capture (REQUIRED)
- Context injection and inheritance
- Exception logging
- Timer functionality
- File rotation
- Thread safety
- JSON formatting
- Configuration from environment

## Dependencies

- **nlohmann/json** - JSON formatting
- **Catch2** - Unit testing
- **C++23** compiler (GCC 13+, Clang 16+)

## File Structure

```
cpp/
├── include/agora/log/
│   ├── logger.hpp           # Main logger
│   ├── config.hpp           # Configuration
│   ├── context.hpp          # Context builder
│   ├── level.hpp            # Log levels
│   ├── entry.hpp            # Log entry
│   ├── formatter.hpp        # Formatters
│   ├── timer.hpp            # RAII timer
│   └── handlers/
│       ├── handler.hpp      # Base
│       ├── console.hpp      # Console
│       ├── file.hpp         # File
│       └── rotating_file.hpp # Rotating
├── src/
│   ├── logger.cpp           # Logger impl
│   ├── config.cpp           # Config impl
│   ├── formatter.cpp        # Formatters
│   ├── context.cpp          # Context
│   ├── timer.cpp            # Timer
│   └── handlers/
│       ├── console.cpp      # Console impl
│       ├── file.cpp         # File impl
│       └── rotating_file.cpp # Rotating impl
├── tests/
│   ├── test_logger.cpp      # Logger tests
│   ├── test_handlers.cpp    # Handler tests
│   ├── test_rotation.cpp    # Rotation tests
│   ├── test_formatter.cpp   # Formatter tests
│   └── test_config.cpp      # Config tests
├── CMakeLists.txt
├── conanfile.txt
├── simple_test.cpp          # Standalone test
└── Makefile.simple          # Simple build
```

## Known Limitations

1. **No async logging** - All writes are synchronous (meets <2μs target for C++)
2. **No log sampling** - Future enhancement
3. **No dynamic level changes** - Requires restart
4. **No custom handlers** - Extension point exists but not documented

## Future Enhancements

1. Custom handler registration
2. Dynamic log level control
3. Prometheus metrics integration
4. Batch writes for performance
5. Memory-mapped file I/O
6. Lock-free queues for async mode

## Usage Example

See `simple_test.cpp` for a complete working example.

Basic usage:
```cpp
#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>

int main() {
    // Initialize
    agora::log::Config config;
    config.service_name = "my-service";
    config.file_path = "/var/log/agora/my-service.log";

    auto result = agora::log::initialize(config);
    if (!result) {
        return 1;
    }

    // Get logger
    auto logger = agora::log::get_logger("main");

    // Log messages
    logger.info("Application started");
    logger.debug("Debug info", {{"key", "value"}});

    // Child logger with context
    auto req_logger = logger.with_context({
        {"request_id", "abc123"},
        {"user_id", "user-456"}
    });

    req_logger.info("Processing request");

    // Timer
    {
        auto timer = logger.timer("Operation");
        // ... work ...
    }

    // Shutdown
    agora::log::shutdown();
    return 0;
}
```
