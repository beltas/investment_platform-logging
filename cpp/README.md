# libagora_log - C++ Logging Library

C++23 implementation of the Agora Trading Platform logging library.

## Features

- Ultra-low latency (< 2 microseconds per log entry)
- Thread-safe rotating file handler
- Automatic source location capture (file, line, function) - **REQUIRED in all log entries**
- JSON structured logging with ISO 8601 timestamps
- Context inheritance with `with_context()`
- RAII timer for duration logging
- Exception logging with type demangling
- Configuration from environment variables

## Requirements

- **C++ Compiler**: GCC 13+ or Clang 16+ (C++23 support required)
- **CMake**: 3.25+
- **Conan**: 2.0+ (package manager)

### Dependencies (managed by Conan)

- `nlohmann_json` - JSON formatting
- `spdlog` - High-performance logging backend
- `catch2` - Testing framework

## Installation

### Option 1: Build from Source

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging/cpp

# Install dependencies with Conan
conan install . --output-folder=build --build=missing

# Build with CMake
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc)

# Install system-wide (optional)
sudo cmake --install .
```

### Option 2: CMake FetchContent

```cmake
include(FetchContent)

FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG main
  SOURCE_SUBDIR cpp
)

FetchContent_MakeAvailable(agora_log)

target_link_libraries(my_service PRIVATE agora::log)
```

### Option 3: Git Submodule

```bash
git submodule add git@github.com:agora/investment_platform-logging.git external/logging
```

```cmake
add_subdirectory(external/logging/cpp)
target_link_libraries(my_service PRIVATE agora::log)
```

## Testing

### Run All Tests

```bash
cd investment_platform-logging/cpp

# Build with tests enabled
conan install . --output-folder=build --build=missing
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake -DBUILD_TESTING=ON
cmake --build . -j$(nproc)

# Run tests
ctest --output-on-failure

# Or run the test executable directly
./agora_log_tests
```

### Simple Standalone Test

```bash
cd investment_platform-logging/cpp

# Build and run simple test (no Conan required for basic test)
make -f Makefile.simple
./simple_test
```

### Test Coverage

The test suite includes:
- `test_logger.cpp` - Core logger functionality
- `test_handlers.cpp` - Console and file handlers
- `test_rotation.cpp` - File rotation with size threshold
- `test_formatter.cpp` - JSON formatting
- `test_config.cpp` - Configuration from environment

## Quick Start

```cpp
#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>

int main() {
    using namespace agora::log;

    // Option 1: Manual configuration
    Config config;
    config.service_name = "portfolio-manager";
    config.environment = "production";
    config.version = "1.0.0";
    config.level = Level::Info;
    config.file_path = "/var/log/agora/portfolio.log";
    config.max_file_size_mb = 100;
    config.max_backup_count = 5;

    // Option 2: From environment variables
    // auto config = Config::from_env("portfolio-manager");

    // Initialize logging
    auto result = initialize(config);
    if (!result) {
        std::cerr << "Failed to init logging: " << result.error().message << '\n';
        return 1;
    }

    // Get a logger
    auto logger = get_logger("agora.portfolio.main");

    // Log messages with context
    logger.info("Server starting", {
        {"grpc_port", std::int64_t{50052}},
        {"version", "1.0.0"}
    });

    // Create child logger with additional context
    auto request_logger = logger.with_context({
        {"request_id", "req-12345"},
        {"user_id", "user-789"}
    });
    request_logger.info("Processing request");

    // Timer for duration logging
    {
        auto timer = logger.timer("Database query", {
            {"table", "portfolios"}
        });
        // ... perform database query ...
    }  // Automatically logs duration on destruction

    // Exception logging
    try {
        throw std::runtime_error("Connection failed");
    } catch (const std::exception& ex) {
        logger.error("Operation failed", ex, {
            {"operation", "db_connect"}
        });
    }

    // Shutdown gracefully
    shutdown();
    return 0;
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGORA_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `AGORA_LOG_ENVIRONMENT` | `development` | Environment name |
| `AGORA_LOG_VERSION` | `0.0.0` | Service version |
| `AGORA_LOG_CONSOLE_ENABLED` | `true` | Enable console output |
| `AGORA_LOG_CONSOLE_JSON` | `true` | Use JSON format for console |
| `AGORA_LOG_FILE_ENABLED` | `true` | Enable file output |
| `AGORA_LOG_FILE_PATH` | `logs/app.log` | Log file path |
| `AGORA_LOG_MAX_FILE_SIZE_MB` | `100` | Max file size before rotation |
| `AGORA_LOG_MAX_BACKUP_COUNT` | `5` | Number of backup files to keep |

## Log Output Format

```json
{
  "timestamp": "2024-01-15T12:34:56.789123Z",
  "level": "INFO",
  "message": "Server starting",
  "service": "portfolio-manager",
  "environment": "production",
  "version": "1.0.0",
  "logger_name": "agora.portfolio.main",
  "file": "main.cpp",
  "line": 42,
  "function": "main",
  "context": {
    "grpc_port": 50052
  }
}
```

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Implementation details
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [../docs/DESIGN.md](../docs/DESIGN.md) - API design specification
