# Agora Logging Library - Design Document

**Version:** 1.0  
**Date:** January 2025  
**Status:** Final  
**Authors:** Architecture Team

This document provides the detailed architecture, component design, and implementation specifications for the Agora Trading Platform logging library.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design - Python](#component-design---python)
3. [Component Design - C++](#component-design---c)
4. [Component Design - JavaScript/TypeScript](#component-design---javascripttypescript)
5. [Interface Contracts and API Specifications](#interface-contracts-and-api-specifications)
6. [File Rotation Algorithm](#file-rotation-algorithm)
7. [Thread-Safety Implementation](#thread-safety-implementation)
8. [Async Logging Queue Design](#async-logging-queue-design)
9. [Configuration System Design](#configuration-system-design)
10. [Error Handling Strategy](#error-handling-strategy)
11. [Performance Considerations](#performance-considerations)
12. [Framework Integration Patterns](#framework-integration-patterns)
13. [Log Collection and Aggregation](#log-collection-and-aggregation)
14. [Sensitive Data Handling](#sensitive-data-handling)
15. [Log Sampling and Rate Limiting](#log-sampling-and-rate-limiting)
16. [Dynamic Log Level Control](#dynamic-log-level-control)
17. [Security Considerations](#security-considerations)
18. [Kubernetes and Container Patterns](#kubernetes-and-container-patterns)
19. [Metrics and Observability](#metrics-and-observability)

---

## Architecture Overview

### High-Level Architecture Diagram

```
+------------------------------------------------------------------+
|                         Application Layer                          |
|  +----------------+  +----------------+  +---------------------+   |
|  | Python         |  | C++            |  | JavaScript/         |   |
|  | Services       |  | Services       |  | TypeScript Services |   |
|  | (FastAPI)      |  | (gRPC)         |  | (NestJS/React)      |   |
|  +-------+--------+  +-------+--------+  +----------+----------+   |
+----------|-------------------|------------------------|-------------+
           |                   |                        |
           v                   v                        v
+------------------------------------------------------------------+
|                    Logging Library Layer                           |
|                                                                    |
|  +----------------+  +----------------+  +---------------------+   |
|  | agora-log      |  | libagora_log   |  | @agora/logger       |   |
|  | (Python)       |  | (C++)          |  | (JS/TS)             |   |
|  +-------+--------+  +-------+--------+  +----------+----------+   |
|          |                   |                       |             |
|          +-------------------+-----------------------+             |
|                              |                                     |
|  +----------------------------------------------------------+     |
|  |                    Core Abstractions                      |     |
|  |                                                           |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  |  | Logger        |  | Context       |  | Log Entry     |  |     |
|  |  | Interface     |  | Manager       |  | Formatter     |  |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  |                                                           |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  |  | Level         |  | Timer         |  | Config        |  |     |
|  |  | Filter        |  | Utility       |  | Manager       |  |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  +----------------------------------------------------------+     |
|                              |                                     |
|  +----------------------------------------------------------+     |
|  |                    Output Handlers                        |     |
|  |                                                           |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  |  | Console       |  | Rotating      |  | Async         |  |     |
|  |  | Handler       |  | File Handler  |  | Queue Handler |  |     |
|  |  +---------------+  +---------------+  +---------------+  |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
           |                                     |
           v                                     v
    +-------------+                       +-------------+
    |   Console   |                       |    Files    |
    |  (stdout)   |                       |   (JSON)    |
    |             |                       |             |
    |  JSON or    |                       |  app.log    |
    |  Text       |                       |  app.log.1  |
    +-------------+                       |  app.log.2  |
                                          +-------------+
```

### Component Interaction Flow

```
+------------------+
| Application Code |
+--------+---------+
         |
         | 1. logger.info("message", context={...})
         v
+--------+---------+
|  Logger Instance |
|                  |
| - Validates level|
| - Merges context |
| - Captures source|
+--------+---------+
         |
         | 2. Create LogEntry with file, line, function
         v
+--------+---------+
|  Context Manager |
|                  |
| - Adds service   |
| - Adds env vars  |
| - Adds inherited |
+--------+---------+
         |
         | 3. Complete LogEntry
         v
+--------+---------+
|   Async Queue    |  (Python/JS only)
|   (optional)     |
+--------+---------+
         |
         | 4. Batch or immediate
         v
+--------+---------+     +------------------+
|  JSON Formatter  |---->|  Console Handler |
+--------+---------+     |  (JSON or Text)  |
         |               +------------------+
         |
         v
+--------+---------+
| Rotating File    |
| Handler          |
|                  |
| - Size check     |
| - Rotation logic |
| - Thread-safe    |
+------------------+
```

### Log Entry Data Flow

```
                         REQUIRED FIELDS
                         ===============
+----------------------+
| Application Log Call |
| logger.info(msg)     |
+----------+-----------+
           |
           | Automatic capture (REQUIRED):
           | - file: source filename
           | - line: line number
           | - function: function name
           v
+----------+-----------+
| Source Location      |
| Capture              |
| (inspect/backtrace)  |
+----------+-----------+
           |
           v
+----------+-----------+
| Context Merge        |
|                      |
| + service (REQUIRED) |
| + environment        |
| + version            |
| + host               |
| + correlation_id     |
| + user_id            |
| + custom context     |
+----------+-----------+
           |
           v
+----------+-----------+
| Timestamp Generation |
| ISO 8601 UTC         |
| with microseconds    |
+----------+-----------+
           |
           v
+----------+-----------+
| Final LogEntry       |
|                      |
| REQUIRED:            |
| - timestamp          |
| - level              |
| - message            |
| - service            |
| - file       <---+   |
| - line       <---+   |
| - function   <---+   |
|                      |
| OPTIONAL:            |
| - correlation_id     |
| - user_id            |
| - trace_id           |
| - context            |
| - duration_ms        |
| - exception          |
+----------------------+
```

---

## Component Design - Python

### Module Structure

```
agora_log/
├── __init__.py          # Public API exports
├── config.py            # Configuration classes
├── logger.py            # Logger implementation
├── entry.py             # LogEntry dataclass
├── formatter.py         # JSON and text formatters
├── context.py           # Context management
├── handlers/
│   ├── __init__.py
│   ├── base.py          # Abstract handler interface
│   ├── console.py       # Console output handler
│   ├── file.py          # Basic file handler
│   ├── rotating.py      # Rotating file handler
│   └── async_handler.py # Async queue wrapper
└── integrations/
    ├── __init__.py
    ├── fastapi.py       # FastAPI middleware
    └── opentelemetry.py # OTEL integration
```

### Class Diagram

```
+-------------------+       +-------------------+
|    LogConfig      |       |     LogLevel      |
+-------------------+       +-------------------+
| service_name      |       | DEBUG = 10        |
| environment       |       | INFO = 20         |
| version           |       | WARNING = 30      |
| level             |       | ERROR = 40        |
| console_enabled   |       | CRITICAL = 50     |
| console_format    |       +-------------------+
| file_enabled      |
| file_path         |
| max_file_size_mb  |
| max_backup_count  |
| async_enabled     |
| queue_size        |
| default_context   |
+-------------------+
        |
        | creates
        v
+-------------------+       +-------------------+
|      Logger       |<----->|  ContextManager   |
+-------------------+       +-------------------+
| _name             |       | _service_context  |
| _config           |       | _inherited        |
| _context          |       | _local            |
| _handlers[]       |       +-------------------+
+-------------------+       | merge()           |
| info()            |       | with_values()     |
| error()           |       +-------------------+
| warning()         |
| debug()           |
| critical()        |
| with_context()    |
| timer()           |
+-------------------+
        |
        | writes to
        v
+-------------------+
| <<interface>>     |
|    Handler        |
+-------------------+
| emit(entry)       |
| flush()           |
| close()           |
+-------------------+
        ^
        |
+-------+-------+-------+
|               |       |
v               v       v
+------------+ +------------+ +------------+
| Console    | | Rotating   | | Async      |
| Handler    | | FileHandler| | Handler    |
+------------+ +------------+ +------------+
| _stream    | | _file      | | _queue     |
| _formatter | | _max_size  | | _worker    |
+------------+ | _backups   | | _handler   |
               | _lock      | +------------+
               +------------+
```

### Source Location Capture

The `file`, `line`, and `function` fields are **REQUIRED** and captured automatically.

```python
# logger.py

import inspect
from dataclasses import dataclass
from typing import Optional, Any
import traceback

@dataclass
class SourceLocation:
    """Captured source location information."""
    file: str
    line: int
    function: str

def _capture_source_location(stack_depth: int = 2) -> SourceLocation:
    """
    Capture the source location of the calling code.
    
    Args:
        stack_depth: How many frames to go up the call stack.
                     Default is 2 (caller of the log method).
    
    Returns:
        SourceLocation with file, line, and function name.
    """
    frame = inspect.currentframe()
    try:
        # Walk up the stack to find the actual caller
        for _ in range(stack_depth):
            if frame is not None:
                frame = frame.f_back
        
        if frame is None:
            return SourceLocation(
                file="<unknown>",
                line=0,
                function="<unknown>"
            )
        
        return SourceLocation(
            file=frame.f_code.co_filename.split("/")[-1],  # Just filename
            line=frame.f_lineno,
            function=frame.f_code.co_name
        )
    finally:
        del frame  # Avoid reference cycles


class Logger:
    """Main logger class with automatic source location capture."""
    
    def __init__(
        self,
        name: str,
        config: "LogConfig",
        context: Optional[dict[str, Any]] = None
    ):
        self._name = name
        self._config = config
        self._context = context or {}
        self._handlers: list[Handler] = []
        self._setup_handlers()
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        exception: Optional[BaseException] = None,
        **kwargs: Any
    ) -> None:
        """
        Internal logging method that captures source location.
        
        The source location (file, line, function) is captured automatically
        and is REQUIRED in all log entries.
        """
        # Skip if level is below threshold
        if level.value < self._config.level.value:
            return
        
        # Capture source location (REQUIRED)
        # stack_depth=3: _log -> info/error/etc -> actual caller
        source = _capture_source_location(stack_depth=3)
        
        # Create log entry with required fields
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            service=self._config.service_name,
            environment=self._config.environment,
            version=self._config.version,
            host=self._get_hostname(),
            logger_name=self._name,
            # REQUIRED source location fields
            file=source.file,
            line=source.line,
            function=source.function,
            # Optional fields
            correlation_id=self._context.get("correlation_id"),
            user_id=self._context.get("user_id"),
            trace_id=self._context.get("trace_id"),
            span_id=self._context.get("span_id"),
            context={**self._context, **kwargs},
            exception=self._format_exception(exception) if exception else None
        )
        
        # Emit to all handlers
        for handler in self._handlers:
            handler.emit(entry)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def error(
        self,
        message: str,
        exception: Optional[BaseException] = None,
        **kwargs: Any
    ) -> None:
        """Log at ERROR level with optional exception."""
        self._log(LogLevel.ERROR, message, exception=exception, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def critical(
        self,
        message: str,
        exception: Optional[BaseException] = None,
        **kwargs: Any
    ) -> None:
        """Log at CRITICAL level."""
        self._log(LogLevel.CRITICAL, message, exception=exception, **kwargs)
    
    def with_context(self, **kwargs: Any) -> "Logger":
        """Create child logger with additional context."""
        new_context = {**self._context, **kwargs}
        return Logger(self._name, self._config, new_context)
    
    @contextmanager
    def timer(self, operation: str, **kwargs: Any):
        """
        Context manager that logs operation duration.
        
        Usage:
            with logger.timer("Database query"):
                result = db.execute()
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._log(
                LogLevel.INFO,
                operation,
                duration_ms=duration_ms,
                **kwargs
            )
```

---

## Component Design - C++

### Header Structure

```
include/agora/log/
├── logger.hpp       # Main logger interface
├── config.hpp       # Configuration structures
├── context.hpp      # Context builder
├── entry.hpp        # Log entry structure
├── level.hpp        # Log levels
├── macros.hpp       # Compile-time macros
└── handlers/
    ├── handler.hpp      # Abstract handler interface
    ├── console.hpp      # Console handler
    ├── file.hpp         # File handler
    └── rotating_file.hpp # Rotating file handler
```

### Class Diagram

```
+---------------------+
|       Config        |
+---------------------+
| service_name        |
| environment         |
| version             |
| level               |
| console_enabled     |
| console_json        |
| file_enabled        |
| file_path           |
| max_file_size_mb    |
| max_backup_count    |
+---------------------+
| from_env() static   |
+---------------------+
        |
        | creates
        v
+---------------------+        +---------------------+
|      Logger         |<------>|    ContextBuilder   |
+---------------------+        +---------------------+
| name_               |        | values_             |
| config_             |        +---------------------+
| context_            |        | correlation_id()    |
| handlers_[]         |        | user_id()           |
+---------------------+        | add()               |
| info()              |        | build()             |
| error()             |        +---------------------+
| warning()           |
| debug()             |
| critical()          |
| with_context()      |
| timer()             |
+---------------------+
        |
        | writes to
        v
+---------------------+
|  <<interface>>      |
|      Handler        |
+---------------------+
| emit(entry)         |
| flush()             |
| close()             |
+---------------------+
        ^
        |
+-------+-------+
|               |
v               v
+-------------+ +------------------+
| Console     | | RotatingFile     |
| Handler     | | Handler          |
+-------------+ +------------------+
| stream_     | | file_            |
| json_mode_  | | max_size_bytes_  |
+-------------+ | backup_count_    |
               | mutex_            |
               | current_size_     |
               +------------------+
               | rotate()         |
               +------------------+
```

### Source Location Capture (C++)

C++ uses compiler intrinsics and `std::source_location` (C++20) for zero-overhead source capture.

```cpp
// include/agora/log/source_location.hpp

#pragma once

#include <string_view>
#include <cstdint>

#if __cplusplus >= 202002L
#include <source_location>
#endif

namespace agora::log {

/**
 * @brief Source location information for log entries.
 * 
 * The file, line, and function fields are REQUIRED in all log entries.
 * This structure captures them with minimal overhead.
 */
struct SourceLocation {
    std::string_view file;
    std::uint32_t line;
    std::string_view function;
    
    /**
     * @brief Create from std::source_location (C++20).
     */
#if __cplusplus >= 202002L
    static constexpr SourceLocation current(
        std::source_location loc = std::source_location::current()
    ) noexcept {
        return SourceLocation{
            .file = extract_filename(loc.file_name()),
            .line = loc.line(),
            .function = loc.function_name()
        };
    }
#else
    // Fallback for C++17 - uses macros
    static SourceLocation from_macro(
        const char* file,
        std::uint32_t line,
        const char* function
    ) noexcept {
        return SourceLocation{
            .file = extract_filename(file),
            .line = line,
            .function = function
        };
    }
#endif
    
private:
    static constexpr std::string_view extract_filename(
        std::string_view path
    ) noexcept {
        // Extract just the filename from full path
        auto pos = path.find_last_of("/\\");
        return (pos != std::string_view::npos) 
            ? path.substr(pos + 1) 
            : path;
    }
};

}  // namespace agora::log

// Macros for source location capture
#if __cplusplus >= 202002L
    #define AGORA_LOG_LOCATION() \
        ::agora::log::SourceLocation::current()
#else
    #define AGORA_LOG_LOCATION() \
        ::agora::log::SourceLocation::from_macro(__FILE__, __LINE__, __func__)
#endif
```

### Logger Implementation

```cpp
// include/agora/log/logger.hpp

#pragma once

#include <string>
#include <string_view>
#include <memory>
#include <vector>
#include <unordered_map>
#include <variant>
#include <chrono>

#include "config.hpp"
#include "entry.hpp"
#include "level.hpp"
#include "source_location.hpp"
#include "handlers/handler.hpp"

namespace agora::log {

// Forward declarations
class Timer;

/**
 * @brief Context value type supporting common JSON types.
 */
using ContextValue = std::variant<
    std::string,
    std::int64_t,
    double,
    bool
>;

using Context = std::unordered_map<std::string, ContextValue>;

/**
 * @brief Main logger class with automatic source location capture.
 * 
 * The logger automatically captures file, line, and function for every
 * log entry. These fields are REQUIRED per the logging specification.
 * 
 * Usage:
 *   auto logger = get_logger("agora.service.component");
 *   logger.info("Operation completed", {{"key", "value"}});
 */
class Logger {
public:
    Logger(
        std::string name,
        std::shared_ptr<const Config> config,
        Context context = {}
    );
    
    /**
     * @brief Log at INFO level.
     * @param message The log message.
     * @param ctx Additional context key-value pairs.
     * @param loc Source location (automatically captured).
     */
    void info(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    /**
     * @brief Log at ERROR level with optional exception.
     * @param message The log message.
     * @param ex Optional exception reference.
     * @param ctx Additional context.
     * @param loc Source location (automatically captured).
     */
    void error(
        std::string_view message,
        const std::exception& ex,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    void error(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    void warning(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    void debug(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    void critical(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    void critical(
        std::string_view message,
        const std::exception& ex,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    /**
     * @brief Create child logger with additional context.
     * 
     * The child logger inherits all context from the parent and adds
     * the new context values.
     */
    [[nodiscard]]
    Logger with_context(Context additional_context) const;
    
    /**
     * @brief Create an RAII timer for operation duration logging.
     * 
     * Usage:
     *   {
     *       auto timer = logger.timer("Database query");
     *       // ... operation ...
     *   }  // Logs duration on destruction
     */
    [[nodiscard]]
    Timer timer(
        std::string operation,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
private:
    void log(
        Level level,
        std::string_view message,
        const SourceLocation& loc,
        Context ctx = {},
        const std::exception* ex = nullptr
    ) const;
    
    std::string name_;
    std::shared_ptr<const Config> config_;
    Context context_;
    std::vector<std::shared_ptr<Handler>> handlers_;
};

/**
 * @brief RAII timer that logs operation duration on destruction.
 */
class Timer {
public:
    Timer(
        const Logger& logger,
        std::string operation,
        Context context,
        SourceLocation location
    );
    
    ~Timer();
    
    // Non-copyable, movable
    Timer(const Timer&) = delete;
    Timer& operator=(const Timer&) = delete;
    Timer(Timer&&) noexcept = default;
    Timer& operator=(Timer&&) noexcept = default;
    
    /**
     * @brief Cancel the timer, preventing duration logging.
     */
    void cancel() noexcept;
    
private:
    const Logger* logger_;
    std::string operation_;
    Context context_;
    SourceLocation location_;
    std::chrono::steady_clock::time_point start_;
    bool cancelled_ = false;
};

// Global logger management
[[nodiscard]]
std::expected<void, Error> initialize(const Config& config);

void shutdown();

[[nodiscard]]
Logger get_logger(std::string_view name);

}  // namespace agora::log
```

### Compile-Time Log Level Filtering

```cpp
// include/agora/log/macros.hpp

#pragma once

#include "logger.hpp"
#include "level.hpp"

/**
 * @brief Compile-time minimum log level.
 * 
 * Set via compiler flag: -DAGORA_LOG_MIN_LEVEL=INFO
 * 
 * Log calls below this level compile to no-ops with zero runtime cost.
 */
#ifndef AGORA_LOG_MIN_LEVEL
    #ifdef NDEBUG
        #define AGORA_LOG_MIN_LEVEL INFO
    #else
        #define AGORA_LOG_MIN_LEVEL DEBUG
    #endif
#endif

// Internal macro to convert level name to value
#define AGORA_LOG_LEVEL_VALUE_DEBUG 10
#define AGORA_LOG_LEVEL_VALUE_INFO  20
#define AGORA_LOG_LEVEL_VALUE_WARNING 30
#define AGORA_LOG_LEVEL_VALUE_ERROR 40
#define AGORA_LOG_LEVEL_VALUE_CRITICAL 50

#define AGORA_LOG_MIN_LEVEL_VALUE \
    AGORA_LOG_LEVEL_VALUE_##AGORA_LOG_MIN_LEVEL

/**
 * @brief Debug log macro with compile-time elimination.
 * 
 * In release builds with AGORA_LOG_MIN_LEVEL=INFO or higher,
 * this compiles to nothing - zero runtime cost.
 * 
 * Usage:
 *   AGORA_LOG_DEBUG(logger, "Debug message", {{"key", "value"}});
 */
#if AGORA_LOG_LEVEL_VALUE_DEBUG >= AGORA_LOG_MIN_LEVEL_VALUE
    #define AGORA_LOG_DEBUG(logger, message, ...) \
        (logger).debug((message), ##__VA_ARGS__)
#else
    #define AGORA_LOG_DEBUG(logger, message, ...) \
        do { } while (false)
#endif

#if AGORA_LOG_LEVEL_VALUE_INFO >= AGORA_LOG_MIN_LEVEL_VALUE
    #define AGORA_LOG_INFO(logger, message, ...) \
        (logger).info((message), ##__VA_ARGS__)
#else
    #define AGORA_LOG_INFO(logger, message, ...) \
        do { } while (false)
#endif

// WARNING, ERROR, CRITICAL are always compiled in
#define AGORA_LOG_WARNING(logger, message, ...) \
    (logger).warning((message), ##__VA_ARGS__)

#define AGORA_LOG_ERROR(logger, message, ...) \
    (logger).error((message), ##__VA_ARGS__)

#define AGORA_LOG_CRITICAL(logger, message, ...) \
    (logger).critical((message), ##__VA_ARGS__)
```

---

## Component Design - JavaScript/TypeScript

### Module Structure

```
src/
├── index.ts           # Public API exports
├── config.ts          # Configuration types
├── logger.ts          # Logger implementation
├── entry.ts           # LogEntry interface
├── formatter.ts       # JSON and text formatters
├── context.ts         # Context management
├── handlers/
│   ├── index.ts
│   ├── handler.ts     # Handler interface
│   ├── console.ts     # Console handler
│   ├── file.ts        # File handler (Node.js)
│   └── rotating.ts    # Rotating file handler
├── integrations/
│   ├── express.ts     # Express middleware
│   └── nestjs.ts      # NestJS integration
└── browser.ts         # Browser-specific exports
```

### Class Diagram

```
+---------------------+
|     LogConfig       |
+---------------------+
| serviceName         |
| environment         |
| version             |
| level               |
| console: {...}      |
| file: {...}         |
| defaultContext      |
+---------------------+
        |
        | creates
        v
+---------------------+        +---------------------+
|      Logger         |<------>|   ContextManager    |
+---------------------+        +---------------------+
| name                |        | serviceContext      |
| config              |        | inherited           |
| context             |        +---------------------+
| handlers[]          |        | merge()             |
+---------------------+        | with()              |
| info()              |        +---------------------+
| error()             |
| warning()           |
| debug()             |
| critical()          |
| withContext()       |
| timer()             |
+---------------------+
        |
        | writes to
        v
+---------------------+
|  <<interface>>      |
|      Handler        |
+---------------------+
| emit(entry)         |
| flush()             |
| close()             |
+---------------------+
        ^
        |
+-------+-------+
|               |
v               v
+-------------+ +------------------+
| Console     | | RotatingFile     |
| Handler     | | Handler          |
+-------------+ +------------------+
| stream      | | filePath         |
| formatter   | | maxSizeBytes     |
+-------------+ | backupCount      |
               | currentSize       |
               +------------------+
```

### Source Location Capture (JavaScript/TypeScript)

JavaScript uses `Error.stack` parsing to capture source location.

```typescript
// src/source-location.ts

/**
 * Source location information for log entries.
 * 
 * IMPORTANT: file, line, and function are REQUIRED in all log entries.
 */
export interface SourceLocation {
  file: string;
  line: number;
  function: string;
}

/**
 * Capture the source location of the calling code.
 * 
 * @param stackDepth How many frames to skip (default 2 for direct caller)
 * @returns SourceLocation with file, line, and function name
 */
export function captureSourceLocation(stackDepth: number = 2): SourceLocation {
  const error = new Error();
  const stack = error.stack;
  
  if (!stack) {
    return {
      file: '<unknown>',
      line: 0,
      function: '<unknown>'
    };
  }
  
  const lines = stack.split('\n');
  // Skip "Error" line and specified number of frames
  const targetLine = lines[stackDepth + 1];
  
  if (!targetLine) {
    return {
      file: '<unknown>',
      line: 0,
      function: '<unknown>'
    };
  }
  
  return parseStackLine(targetLine);
}

/**
 * Parse a V8 stack trace line.
 * 
 * Formats:
 *   at functionName (/path/to/file.js:10:5)
 *   at /path/to/file.js:10:5
 *   at Object.<anonymous> (/path/to/file.js:10:5)
 */
function parseStackLine(line: string): SourceLocation {
  // Try: "at functionName (file:line:col)"
  const withFunction = /at\s+(\S+)\s+\((.+):(\d+):\d+\)/.exec(line);
  if (withFunction) {
    return {
      function: withFunction[1].split('.').pop() || withFunction[1],
      file: extractFilename(withFunction[2]),
      line: parseInt(withFunction[3], 10)
    };
  }
  
  // Try: "at file:line:col"
  const withoutFunction = /at\s+(.+):(\d+):\d+/.exec(line);
  if (withoutFunction) {
    return {
      function: '<anonymous>',
      file: extractFilename(withoutFunction[1]),
      line: parseInt(withoutFunction[2], 10)
    };
  }
  
  return {
    file: '<unknown>',
    line: 0,
    function: '<unknown>'
  };
}

function extractFilename(path: string): string {
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1] || path;
}
```

### Logger Implementation

```typescript
// src/logger.ts

import { LogLevel } from './level';
import { LogEntry } from './entry';
import { LogConfig } from './config';
import { Handler } from './handlers/handler';
import { captureSourceLocation, SourceLocation } from './source-location';

export class Logger {
  private readonly name: string;
  private readonly config: LogConfig;
  private readonly context: Record<string, unknown>;
  private readonly handlers: Handler[];
  
  constructor(
    name: string,
    config: LogConfig,
    context: Record<string, unknown> = {}
  ) {
    this.name = name;
    this.config = config;
    this.context = context;
    this.handlers = [];
    this.setupHandlers();
  }
  
  /**
   * Internal log method that captures source location.
   * 
   * The source location (file, line, function) is captured automatically
   * and is REQUIRED in all log entries.
   */
  private log(
    level: LogLevel,
    message: string,
    context: Record<string, unknown> = {},
    error?: Error,
    location?: SourceLocation
  ): void {
    // Skip if level is below threshold
    if (level < this.config.level) {
      return;
    }
    
    // Capture source location (REQUIRED)
    // stackDepth=3: log -> info/error/etc -> actual caller
    const source = location || captureSourceLocation(3);
    
    // Create log entry with required fields
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: LogLevel[level],
      message,
      service: this.config.serviceName,
      environment: this.config.environment,
      version: this.config.version,
      host: this.getHostname(),
      loggerName: this.name,
      // REQUIRED source location fields
      file: source.file,
      line: source.line,
      function: source.function,
      // Optional fields
      correlationId: this.context.correlationId as string | undefined,
      userId: this.context.userId as string | undefined,
      traceId: this.context.traceId as string | undefined,
      spanId: this.context.spanId as string | undefined,
      context: { ...this.context, ...context },
      exception: error ? this.formatException(error) : undefined
    };
    
    // Emit to all handlers
    for (const handler of this.handlers) {
      handler.emit(entry);
    }
  }
  
  info(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.INFO, message, context);
  }
  
  error(
    message: string,
    error?: Error,
    context?: Record<string, unknown>
  ): void {
    this.log(LogLevel.ERROR, message, context, error);
  }
  
  warning(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.WARNING, message, context);
  }
  
  debug(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.DEBUG, message, context);
  }
  
  critical(
    message: string,
    error?: Error,
    context?: Record<string, unknown>
  ): void {
    this.log(LogLevel.CRITICAL, message, context, error);
  }
  
  /**
   * Create child logger with additional context.
   */
  withContext(additionalContext: Record<string, unknown>): Logger {
    return new Logger(
      this.name,
      this.config,
      { ...this.context, ...additionalContext }
    );
  }
  
  /**
   * Timer for measuring async operation duration.
   * 
   * Usage:
   *   const result = await logger.timer(
   *     'Database query',
   *     async () => await db.query()
   *   );
   */
  async timer<T>(
    operation: string,
    fn: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<T> {
    const start = process.hrtime.bigint();
    const location = captureSourceLocation(2);
    
    try {
      const result = await fn();
      const durationMs = Number(process.hrtime.bigint() - start) / 1_000_000;
      
      this.log(
        LogLevel.INFO,
        operation,
        { ...context, durationMs },
        undefined,
        location
      );
      
      return result;
    } catch (error) {
      const durationMs = Number(process.hrtime.bigint() - start) / 1_000_000;
      
      this.log(
        LogLevel.ERROR,
        `${operation} failed`,
        { ...context, durationMs },
        error as Error,
        location
      );
      
      throw error;
    }
  }
  
  private getHostname(): string {
    if (typeof process !== 'undefined' && process.env.HOSTNAME) {
      return process.env.HOSTNAME;
    }
    try {
      const os = require('os');
      return os.hostname();
    } catch {
      return 'unknown';
    }
  }
  
  private formatException(error: Error): {
    type: string;
    message: string;
    stacktrace: string;
  } {
    return {
      type: error.constructor.name,
      message: error.message,
      stacktrace: error.stack || ''
    };
  }
  
  private setupHandlers(): void {
    // Implementation creates handlers based on config
  }
}
```

---

## Interface Contracts and API Specifications

### Log Entry Schema (JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgoraLogEntry",
  "type": "object",
  "required": [
    "timestamp",
    "level",
    "message",
    "service",
    "file",
    "line",
    "function"
  ],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp with microseconds"
    },
    "level": {
      "type": "string",
      "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
      "description": "Log level"
    },
    "message": {
      "type": "string",
      "description": "Human-readable log message"
    },
    "service": {
      "type": "string",
      "description": "Service name"
    },
    "environment": {
      "type": "string",
      "enum": ["development", "staging", "production"],
      "description": "Deployment environment"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+",
      "description": "Service version (semver)"
    },
    "host": {
      "type": "string",
      "description": "Hostname or pod name"
    },
    "logger_name": {
      "type": "string",
      "description": "Hierarchical logger name"
    },
    "file": {
      "type": "string",
      "description": "Source file name (REQUIRED)"
    },
    "line": {
      "type": "integer",
      "minimum": 0,
      "description": "Source line number (REQUIRED)"
    },
    "function": {
      "type": "string",
      "description": "Function/method name (REQUIRED)"
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Request correlation ID"
    },
    "user_id": {
      "type": "string",
      "description": "Authenticated user ID"
    },
    "trace_id": {
      "type": "string",
      "description": "OpenTelemetry trace ID"
    },
    "span_id": {
      "type": "string",
      "description": "OpenTelemetry span ID"
    },
    "context": {
      "type": "object",
      "description": "Additional structured data"
    },
    "duration_ms": {
      "type": "number",
      "description": "Operation duration in milliseconds"
    },
    "exception": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "message": { "type": "string" },
        "stacktrace": { "type": "string" }
      }
    }
  }
}
```

### Handler Interface Contract

All handlers must implement this interface:

```
Interface: Handler
├── emit(entry: LogEntry) -> void
│   - Write a log entry to the output
│   - Must be thread-safe
│   - Must not throw exceptions (log errors instead)
│
├── flush() -> void
│   - Flush any buffered entries
│   - Block until all entries are written
│
└── close() -> void
    - Release resources
    - Flush remaining entries
    - Safe to call multiple times
```

---

## File Rotation Algorithm

### Algorithm Pseudocode

```
ALGORITHM: SizeBasedFileRotation

CONSTANTS:
  MAX_FILE_SIZE = config.max_file_size_mb * 1024 * 1024 (bytes)
  MAX_BACKUPS = config.max_backup_count (default 5)

STATE:
  current_file: File handle
  current_size: int (bytes written to current file)
  mutex: Lock (for thread safety)

FUNCTION write(entry: string):
  entry_bytes = encode_utf8(entry)
  
  ACQUIRE mutex
  TRY:
    IF current_size + len(entry_bytes) + 1 > MAX_FILE_SIZE:
      rotate()
    
    current_file.write(entry_bytes)
    current_file.write('\n')
    current_file.flush()
    current_size += len(entry_bytes) + 1
  FINALLY:
    RELEASE mutex

FUNCTION rotate():
  # Close current file
  current_file.close()
  
  # Delete oldest backup if exists
  oldest_backup = file_path + '.' + str(MAX_BACKUPS)
  IF exists(oldest_backup):
    delete(oldest_backup)
  
  # Rotate existing backups
  FOR i FROM MAX_BACKUPS - 1 DOWN TO 1:
    src = file_path + '.' + str(i)
    dst = file_path + '.' + str(i + 1)
    IF exists(src):
      rename(src, dst)
  
  # Move current to .1
  IF exists(file_path):
    rename(file_path, file_path + '.1')
  
  # Open new file
  current_file = open(file_path, 'a')
  current_size = 0
```

### Rotation State Diagram

```
                    +---------------+
                    |    WRITING    |
                    |               |
                    | current_file  |
                    | open          |
                    +-------+-------+
                            |
                            | write(entry)
                            v
                    +---------------+
                    |  SIZE CHECK   |
                    |               |
                    | size + entry  |
                    | > max_size?   |
                    +-------+-------+
                            |
              +-------------+-------------+
              | NO                        | YES
              v                           v
      +---------------+           +---------------+
      |    APPEND     |           |   ROTATING    |
      |               |           |               |
      | write entry   |           | 1. close file |
      | update size   |           | 2. del oldest |
      |               |           | 3. rename all |
      +-------+-------+           | 4. open new   |
              |                   +-------+-------+
              |                           |
              +-------------+-------------+
                            |
                            v
                    +---------------+
                    |    WRITING    |
                    +---------------+
```

### File Layout Example

```
BEFORE ROTATION:
  /var/log/agora/
  ├── market-data.log      (98 MB)  <- current file
  ├── market-data.log.1    (100 MB) <- most recent backup
  ├── market-data.log.2    (100 MB)
  ├── market-data.log.3    (100 MB)
  ├── market-data.log.4    (100 MB)
  └── market-data.log.5    (100 MB) <- oldest backup

WRITE THAT TRIGGERS ROTATION (entry would exceed 100 MB):
  1. Close market-data.log
  2. DELETE market-data.log.5
  3. RENAME market-data.log.4 -> market-data.log.5
  4. RENAME market-data.log.3 -> market-data.log.4
  5. RENAME market-data.log.2 -> market-data.log.3
  6. RENAME market-data.log.1 -> market-data.log.2
  7. RENAME market-data.log -> market-data.log.1
  8. CREATE new market-data.log
  9. WRITE entry to new file

AFTER ROTATION:
  /var/log/agora/
  ├── market-data.log      (0 KB)   <- new file with entry
  ├── market-data.log.1    (98 MB)  <- was market-data.log
  ├── market-data.log.2    (100 MB) <- was .1
  ├── market-data.log.3    (100 MB) <- was .2
  ├── market-data.log.4    (100 MB) <- was .3
  └── market-data.log.5    (100 MB) <- was .4 (old .5 deleted)
```

---

## Thread-Safety Implementation

### Python Thread Safety

```python
# handlers/rotating.py

import threading
from pathlib import Path
from typing import TextIO

class RotatingFileHandler:
    """
    Thread-safe rotating file handler.
    
    Uses a reentrant lock to allow the same thread to acquire
    the lock multiple times (e.g., during rotation).
    """
    
    def __init__(
        self,
        file_path: Path,
        max_size_bytes: int,
        max_backup_count: int
    ):
        self._file_path = Path(file_path)
        self._max_size_bytes = max_size_bytes
        self._max_backup_count = max_backup_count
        
        # Reentrant lock for thread safety
        self._lock = threading.RLock()
        
        # File state
        self._file: TextIO | None = None
        self._current_size: int = 0
        
        # Open initial file
        self._open_file()
    
    def emit(self, entry: str) -> None:
        """
        Write a log entry to the file.
        
        Thread-safe: Multiple threads can call emit() concurrently.
        """
        entry_bytes = entry.encode('utf-8')
        entry_size = len(entry_bytes) + 1  # +1 for newline
        
        with self._lock:
            # Check if rotation needed
            if self._current_size + entry_size > self._max_size_bytes:
                self._rotate()
            
            # Write entry
            if self._file:
                self._file.write(entry + '\n')
                self._file.flush()
                self._current_size += entry_size
    
    def _rotate(self) -> None:
        """
        Rotate log files.
        
        Called within lock context.
        """
        # Close current file
        if self._file:
            self._file.close()
            self._file = None
        
        # Rotate existing files
        for i in range(self._max_backup_count, 0, -1):
            src = self._backup_path(i - 1) if i > 1 else self._file_path
            dst = self._backup_path(i)
            
            if src.exists():
                if i == self._max_backup_count:
                    src.unlink()  # Delete oldest
                else:
                    src.rename(dst)
        
        # Open new file
        self._open_file()
    
    def _open_file(self) -> None:
        """Open or create log file."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get existing file size
        if self._file_path.exists():
            self._current_size = self._file_path.stat().st_size
        else:
            self._current_size = 0
        
        self._file = open(self._file_path, 'a', encoding='utf-8')
    
    def _backup_path(self, index: int) -> Path:
        """Get path for backup file at given index."""
        return self._file_path.with_suffix(f'{self._file_path.suffix}.{index}')
    
    def flush(self) -> None:
        """Flush buffered data."""
        with self._lock:
            if self._file:
                self._file.flush()
    
    def close(self) -> None:
        """Close file handle."""
        with self._lock:
            if self._file:
                self._file.close()
                self._file = None
```

### C++ Thread Safety

```cpp
// src/handlers/rotating_file.cpp

#include <mutex>
#include <fstream>
#include <filesystem>

namespace agora::log {

class RotatingFileHandler : public Handler {
public:
    RotatingFileHandler(
        std::filesystem::path file_path,
        std::size_t max_size_bytes,
        std::size_t max_backup_count
    ) : file_path_(std::move(file_path))
      , max_size_bytes_(max_size_bytes)
      , max_backup_count_(max_backup_count)
      , current_size_(0)
    {
        open_file();
    }
    
    ~RotatingFileHandler() override {
        close();
    }
    
    void emit(const LogEntry& entry) override {
        std::string formatted = format(entry);
        std::size_t entry_size = formatted.size() + 1;  // +1 for newline
        
        // Lock for thread-safe access
        std::unique_lock lock(mutex_);
        
        // Check if rotation needed
        if (current_size_ + entry_size > max_size_bytes_) {
            rotate();
        }
        
        // Write entry
        if (file_.is_open()) {
            file_ << formatted << '\n';
            file_.flush();
            current_size_ += entry_size;
        }
    }
    
    void flush() override {
        std::unique_lock lock(mutex_);
        if (file_.is_open()) {
            file_.flush();
        }
    }
    
    void close() override {
        std::unique_lock lock(mutex_);
        if (file_.is_open()) {
            file_.close();
        }
    }
    
private:
    void rotate() {
        // Close current file
        if (file_.is_open()) {
            file_.close();
        }
        
        namespace fs = std::filesystem;
        
        // Delete oldest backup
        auto oldest = backup_path(max_backup_count_);
        if (fs::exists(oldest)) {
            fs::remove(oldest);
        }
        
        // Rotate existing files
        for (std::size_t i = max_backup_count_ - 1; i >= 1; --i) {
            auto src = (i == 1) ? file_path_ : backup_path(i);
            auto dst = backup_path(i + 1);
            
            if (fs::exists(src)) {
                fs::rename(src, dst);
            }
        }
        
        // Rename current to .1
        if (fs::exists(file_path_)) {
            fs::rename(file_path_, backup_path(1));
        }
        
        // Open new file
        open_file();
    }
    
    void open_file() {
        // Create directory if needed
        if (auto parent = file_path_.parent_path(); !parent.empty()) {
            std::filesystem::create_directories(parent);
        }
        
        // Get existing size
        if (std::filesystem::exists(file_path_)) {
            current_size_ = std::filesystem::file_size(file_path_);
        } else {
            current_size_ = 0;
        }
        
        file_.open(file_path_, std::ios::app);
    }
    
    std::filesystem::path backup_path(std::size_t index) const {
        return std::filesystem::path(
            file_path_.string() + "." + std::to_string(index)
        );
    }
    
    std::filesystem::path file_path_;
    std::size_t max_size_bytes_;
    std::size_t max_backup_count_;
    std::size_t current_size_;
    
    std::mutex mutex_;
    std::ofstream file_;
};

}  // namespace agora::log
```

### JavaScript/TypeScript Thread Safety

Node.js is single-threaded for JavaScript execution. The RotatingFileHandler uses
synchronous file operations to ensure data integrity during rotation, while the
regular FileHandler uses async streams with batching for higher throughput.

```typescript
// src/handlers/rotating.ts
// Uses synchronous file operations for guaranteed data integrity during rotation

import * as fs from 'fs';
import * as path from 'path';

export class RotatingFileHandler implements Handler {
  private readonly filePath: string;
  private readonly maxSizeBytes: number;
  private readonly maxBackupCount: number;
  private readonly formatter: JSONFormatter;

  private fd: number | null = null;       // File descriptor for sync I/O
  private currentSize: number = 0;
  private closed: boolean = false;

  constructor(filePath: string, maxSizeMB: number, maxBackupCount: number) {
    this.filePath = filePath;
    this.maxSizeBytes = maxSizeMB * 1024 * 1024;
    this.maxBackupCount = maxBackupCount;
    this.formatter = new JSONFormatter();
    this.ensureDirectory();
    this.openFile();
    this.syncCurrentSize();
  }

  private ensureDirectory(): void {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private openFile(): void {
    // Open in append mode with synchronous writes
    this.fd = fs.openSync(this.filePath, 'a');
  }

  private closeFile(): void {
    if (this.fd !== null) {
      fs.fsyncSync(this.fd);  // Ensure all data on disk
      fs.closeSync(this.fd);
      this.fd = null;
    }
  }

  private syncCurrentSize(): void {
    try {
      const stats = fs.statSync(this.filePath);
      this.currentSize = stats.size;
    } catch {
      this.currentSize = 0;
    }
  }

  emit(entry: LogEntry): void {
    if (this.closed || this.fd === null) return;

    const formatted = this.formatter.format(entry);
    const output = formatted + '\n';
    const entryBytes = Buffer.byteLength(output, 'utf8');

    // Check if rotation needed BEFORE writing
    if (this.currentSize + entryBytes > this.maxSizeBytes) {
      this.rotate();
    }

    // Synchronous write - guarantees data integrity
    fs.writeSync(this.fd!, output, null, 'utf8');
    this.currentSize += entryBytes;
  }

  private rotate(): void {
    // Close current file (fsync ensures data on disk)
    this.closeFile();

    // Delete oldest backup
    const oldest = `${this.filePath}.${this.maxBackupCount}`;
    if (fs.existsSync(oldest)) {
      fs.unlinkSync(oldest);
    }

    // Rotate existing files (reverse order to avoid overwrites)
    for (let i = this.maxBackupCount - 1; i >= 1; i--) {
      const src = `${this.filePath}.${i}`;
      const dst = `${this.filePath}.${i + 1}`;
      if (fs.existsSync(src)) {
        fs.renameSync(src, dst);
      }
    }

    // Rename current to .1
    if (fs.existsSync(this.filePath)) {
      fs.renameSync(this.filePath, `${this.filePath}.1`);
    }

    // Open new file
    this.openFile();
    this.currentSize = 0;
  }

  async flush(): Promise<void> {
    if (this.fd !== null) {
      fs.fsyncSync(this.fd);
    }
  }

  async close(): Promise<void> {
    this.closed = true;
    this.closeFile();
  }
}
```

> **Implementation Note:** The JavaScript RotatingFileHandler uses synchronous file operations
> (`fs.openSync`, `fs.writeSync`, `fs.fsyncSync`) instead of async streams. This guarantees
> no data loss during rotation by ensuring all data is written to disk before any file
> operations occur. While this has slightly higher latency per write (~1-5ms), it provides
> stronger data integrity guarantees required for reliable log rotation.

---

## Async Logging Queue Design

### Queue Architecture

```
+-------------------+
| Application Code  |
| logger.info()     |
+--------+----------+
         |
         | 1. Create LogEntry
         | 2. Enqueue (non-blocking)
         v
+-------------------+
|    Async Queue    |
|                   |
| - Bounded size    |
| - Thread-safe     |
| - Overflow policy |
+--------+----------+
         |
         | Background worker thread
         v
+-------------------+
| Batch Processor   |
|                   |
| - Batch entries   |
| - Write to handler|
| - Flush on timeout|
+-------------------+
```

### Python Async Queue Implementation

```python
# handlers/async_handler.py

import threading
import queue
from typing import Callable
from dataclasses import dataclass

@dataclass
class AsyncConfig:
    queue_size: int = 10000
    batch_size: int = 100
    flush_interval_ms: int = 10
    overflow_policy: str = "drop_oldest"  # drop_oldest, drop_newest, block

class AsyncHandler:
    """
    Async handler that wraps another handler with a queue.
    
    Provides non-blocking logging by queuing entries and
    processing them in a background thread.
    """
    
    def __init__(
        self,
        handler: Handler,
        config: AsyncConfig
    ):
        self._handler = handler
        self._config = config
        
        # Bounded queue
        self._queue: queue.Queue[LogEntry | None] = queue.Queue(
            maxsize=config.queue_size
        )
        
        # Overflow tracking
        self._dropped_count = 0
        self._dropped_lock = threading.Lock()
        
        # Background worker
        self._running = True
        self._worker = threading.Thread(
            target=self._process_loop,
            daemon=True,
            name="agora-log-worker"
        )
        self._worker.start()
    
    def emit(self, entry: LogEntry) -> None:
        """
        Queue a log entry for async processing.
        
        Non-blocking unless overflow_policy is 'block'.
        """
        try:
            if self._config.overflow_policy == "block":
                self._queue.put(entry)  # Blocks if full
            else:
                try:
                    self._queue.put_nowait(entry)
                except queue.Full:
                    self._handle_overflow(entry)
        except Exception:
            pass  # Never fail on logging
    
    def _handle_overflow(self, entry: LogEntry) -> None:
        """Handle queue overflow based on policy."""
        with self._dropped_lock:
            self._dropped_count += 1
        
        if self._config.overflow_policy == "drop_oldest":
            try:
                # Remove oldest entry to make room
                self._queue.get_nowait()
                self._queue.put_nowait(entry)
            except queue.Empty:
                pass
        # drop_newest: just don't add the new entry
    
    def _process_loop(self) -> None:
        """Background worker that processes queued entries."""
        batch: list[LogEntry] = []
        last_flush = time.monotonic()
        
        while self._running or not self._queue.empty():
            try:
                # Wait for entry with timeout
                entry = self._queue.get(
                    timeout=self._config.flush_interval_ms / 1000
                )
                
                if entry is None:  # Shutdown signal
                    break
                
                batch.append(entry)
                
                # Flush if batch is full
                if len(batch) >= self._config.batch_size:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.monotonic()
                    
            except queue.Empty:
                # Timeout - flush partial batch
                elapsed = (time.monotonic() - last_flush) * 1000
                if batch and elapsed >= self._config.flush_interval_ms:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.monotonic()
        
        # Flush remaining entries
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: list[LogEntry]) -> None:
        """Write a batch of entries to the underlying handler."""
        for entry in batch:
            self._handler.emit(entry)
        self._handler.flush()
        
        # Log dropped count if any
        with self._dropped_lock:
            if self._dropped_count > 0:
                warn_entry = LogEntry(
                    level="WARNING",
                    message=f"Async queue overflow, dropped {self._dropped_count} entries",
                    # ... other fields
                )
                self._handler.emit(warn_entry)
                self._dropped_count = 0
    
    def flush(self) -> None:
        """Flush all pending entries."""
        # Wait for queue to drain
        self._queue.join()
        self._handler.flush()
    
    def close(self) -> None:
        """Stop worker and close handler."""
        self._running = False
        self._queue.put(None)  # Shutdown signal
        self._worker.join(timeout=5)
        self._handler.close()
```

---

## Configuration System Design

### Configuration Hierarchy

```
+------------------------+
| Environment Variables  |  Highest priority
| LOG_LEVEL, etc.        |
+-----------+------------+
            |
            v
+------------------------+
| Configuration File     |  logging.yaml
| (if present)           |
+-----------+------------+
            |
            v
+------------------------+
| Programmatic Config    |  LogConfig object
| (code)                 |
+-----------+------------+
            |
            v
+------------------------+
| Default Values         |  Lowest priority
+------------------------+
```

### Configuration Loading (Python)

```python
# config.py

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import yaml

@dataclass
class LogConfig:
    """
    Logging configuration with defaults and environment override.
    """
    service_name: str
    environment: Literal["development", "staging", "production"] = "development"
    version: str = "0.0.0"
    level: LogLevel = LogLevel.INFO
    
    # Console output
    console_enabled: bool = True
    console_format: Literal["json", "text"] = "json"
    console_colors: bool = True
    
    # File output
    file_enabled: bool = True
    file_path: Path = Path("/var/log/agora/app.log")
    max_file_size_mb: int = 100
    max_backup_count: int = 5
    
    # Async settings
    async_enabled: bool = True
    queue_size: int = 10000
    
    # Default context
    default_context: dict = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, service_name: str) -> "LogConfig":
        """
        Create configuration from environment variables.
        
        Environment variables take precedence over defaults.
        """
        return cls(
            service_name=service_name,
            environment=os.getenv("ENVIRONMENT", "development"),
            version=os.getenv("SERVICE_VERSION", "0.0.0"),
            level=LogLevel[os.getenv("LOG_LEVEL", "INFO").upper()],
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
            console_format=os.getenv("LOG_CONSOLE_FORMAT", "json"),
            console_colors=os.getenv("LOG_CONSOLE_COLORS", "true").lower() == "true",
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            file_path=Path(os.getenv("LOG_FILE_PATH", "/var/log/agora/app.log")),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "100")),
            max_backup_count=int(os.getenv("LOG_MAX_BACKUP_COUNT", "5")),
            async_enabled=os.getenv("LOG_ASYNC_ENABLED", "true").lower() == "true",
            queue_size=int(os.getenv("LOG_QUEUE_SIZE", "10000")),
        )
    
    @classmethod
    def from_file(cls, path: Path, service_name: str) -> "LogConfig":
        """
        Load configuration from YAML file.
        
        Environment variables override file values.
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        
        # Apply environment overrides
        config = cls(
            service_name=service_name,
            environment=os.getenv("ENVIRONMENT", data.get("environment", "development")),
            version=os.getenv("SERVICE_VERSION", data.get("version", "0.0.0")),
            level=LogLevel[os.getenv("LOG_LEVEL", data.get("level", "INFO")).upper()],
            console_enabled=_env_bool("LOG_CONSOLE_ENABLED", 
                                      data.get("console", {}).get("enabled", True)),
            console_format=os.getenv("LOG_CONSOLE_FORMAT",
                                     data.get("console", {}).get("format", "json")),
            file_enabled=_env_bool("LOG_FILE_ENABLED",
                                   data.get("file", {}).get("enabled", True)),
            file_path=Path(os.getenv("LOG_FILE_PATH",
                                     data.get("file", {}).get("path", "/var/log/agora/app.log"))),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB",
                                           data.get("file", {}).get("max_size_mb", 100))),
            max_backup_count=int(os.getenv("LOG_MAX_BACKUP_COUNT",
                                           data.get("file", {}).get("max_backup_count", 5))),
            default_context=data.get("default_context", {}),
        )
        
        return config

def _env_bool(name: str, default: bool) -> bool:
    """Get boolean from environment with default."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() == "true"
```

---

## Error Handling Strategy

### Error Handling Principles

1. **Logging must never crash the application**
2. **Errors in one handler should not affect other handlers**
3. **Graceful degradation: file failure should fall back to console**
4. **Error information should be visible for debugging**

### Error Handling Implementation

```python
# handlers/base.py

class SafeHandler:
    """
    Base handler with error protection.
    
    Wraps handler operations to catch and handle errors gracefully.
    """
    
    def __init__(self, handler: Handler, fallback: Handler | None = None):
        self._handler = handler
        self._fallback = fallback
        self._error_count = 0
        self._last_error: Exception | None = None
        self._error_logged = False
    
    def emit(self, entry: LogEntry) -> None:
        """
        Emit entry with error protection.
        
        If the primary handler fails:
        1. Log error to fallback handler (if available)
        2. Increment error count
        3. Continue operation (don't crash)
        """
        try:
            self._handler.emit(entry)
            self._error_logged = False  # Reset on success
        except Exception as e:
            self._error_count += 1
            self._last_error = e
            
            # Log error once to avoid spam
            if self._fallback and not self._error_logged:
                error_entry = LogEntry(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    level="ERROR",
                    message=f"Handler error: {type(e).__name__}: {e}",
                    service="agora-logging",
                    file="base.py",
                    line=0,
                    function="emit",
                    context={
                        "handler_type": type(self._handler).__name__,
                        "error_count": self._error_count
                    }
                )
                self._fallback.emit(error_entry)
                self._error_logged = True
            
            # Try fallback for the original entry
            if self._fallback:
                try:
                    self._fallback.emit(entry)
                except Exception:
                    pass  # Give up silently
    
    def flush(self) -> None:
        """Flush with error protection."""
        try:
            self._handler.flush()
        except Exception:
            pass
    
    def close(self) -> None:
        """Close with error protection."""
        try:
            self._handler.close()
        except Exception:
            pass
```

### Graceful Degradation Example

```
NORMAL OPERATION:
  Application -> Logger -> [Console Handler, File Handler]
                              |                |
                              v                v
                           Console           File

FILE FAILURE (disk full):
  Application -> Logger -> [Console Handler, File Handler]
                              |                |
                              v                X (fails)
                           Console
                              ^
                              |
                    "File logging failed: No space left"

  - Application continues running
  - Console receives all logs
  - Periodic retry attempts to restore file logging
```

---

## Performance Considerations

### Performance Targets

| Metric | Python | C++ | JavaScript |
|--------|--------|-----|------------|
| Log entry (async) | < 10 microseconds | N/A | < 10 microseconds |
| Log entry (sync) | N/A | < 2 microseconds | N/A |
| File rotation | < 50 ms | < 50 ms | < 50 ms |
| Memory per entry | ~500 bytes | ~200 bytes | ~400 bytes |
| Max queue size | 10,000 entries | N/A | 10,000 entries |

### Optimization Techniques

#### 1. Source Location Caching (Python)

```python
# Avoid repeated stack inspection for hot paths

@functools.lru_cache(maxsize=1000)
def _get_cached_location(frame_id: int) -> SourceLocation:
    """Cache source location by frame identity."""
    # ... capture logic
```

#### 2. JSON Serialization Optimization

```python
# Use orjson for fast JSON serialization (3-10x faster than stdlib)
import orjson

def format_entry(entry: LogEntry) -> str:
    return orjson.dumps(
        entry.__dict__,
        option=orjson.OPT_UTC_Z | orjson.OPT_NAIVE_UTC
    ).decode('utf-8')
```

#### 3. String Interning (C++)

```cpp
// Intern common strings to avoid repeated allocations
static const std::string LEVEL_INFO = "INFO";
static const std::string LEVEL_ERROR = "ERROR";
// ...

// Use string_view for non-owned strings
void log(Level level, std::string_view message, ...) {
    // No string copy for message parameter
}
```

#### 4. Buffer Pooling (C++)

```cpp
// Reuse output buffers
thread_local std::string output_buffer;

std::string_view format(const LogEntry& entry) {
    output_buffer.clear();
    // Format directly into buffer
    return output_buffer;
}
```

### Benchmarking Guidelines

```python
# benchmark.py

import timeit

def benchmark_logging():
    """Benchmark log entry creation and emission."""
    
    config = LogConfig(
        service_name="benchmark",
        file_enabled=False,  # Isolate logger overhead
        console_enabled=False,
        async_enabled=False
    )
    initialize(config)
    logger = get_logger("benchmark")
    
    # Warm up
    for _ in range(1000):
        logger.info("warmup")
    
    # Benchmark
    iterations = 100000
    start = timeit.default_timer()
    
    for i in range(iterations):
        logger.info("benchmark message", iteration=i)
    
    elapsed = timeit.default_timer() - start
    per_entry = (elapsed / iterations) * 1_000_000  # microseconds
    
    print(f"Time per entry: {per_entry:.2f} microseconds")
    print(f"Entries per second: {iterations / elapsed:.0f}")
```

---

## Framework Integration Patterns

### FastAPI Middleware Integration

```python
# integrations/fastapi.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar
import uuid

# Context variable for request-scoped logger
_request_logger: ContextVar[Logger | None] = ContextVar(
    "request_logger", default=None
)

def get_request_logger() -> Logger:
    """Get the logger for the current request."""
    logger = _request_logger.get()
    if logger is None:
        return get_logger("agora.http")
    return logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that creates request-scoped loggers.
    
    Features:
    - Generates or extracts correlation ID
    - Extracts user ID from authentication
    - Logs request start and completion
    - Measures request duration
    """
    
    async def dispatch(
        self, request: Request, call_next
    ) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )
        
        # Extract user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        
        # Extract trace context if present
        trace_id = request.headers.get("X-Trace-ID")
        span_id = request.headers.get("X-Span-ID")
        
        # Create request-scoped logger
        base_logger = get_logger("agora.http")
        request_logger = base_logger.with_context(
            correlation_id=correlation_id,
            user_id=user_id,
            trace_id=trace_id,
            span_id=span_id,
            method=request.method,
            path=request.url.path
        )
        
        # Set context variable
        token = _request_logger.set(request_logger)
        
        try:
            request_logger.info("Request started")
            start = time.perf_counter()
            
            response = await call_next(request)
            
            duration_ms = (time.perf_counter() - start) * 1000
            request_logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Add correlation ID to response
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            request_logger.error(
                "Request failed",
                exception=e,
                duration_ms=duration_ms
            )
            raise
        finally:
            _request_logger.reset(token)
```

### gRPC Interceptor Integration (C++)

```cpp
// integrations/grpc_interceptor.hpp

#include <grpcpp/grpcpp.h>
#include <agora/log/logger.hpp>

namespace agora::log::integrations {

/**
 * gRPC server interceptor for automatic logging.
 * 
 * Features:
 * - Extracts correlation ID from metadata
 * - Logs RPC start and completion
 * - Measures RPC duration
 */
class LoggingInterceptor : public grpc::experimental::Interceptor {
public:
    void Intercept(grpc::experimental::InterceptorBatchMethods* methods) override {
        if (methods->QueryInterceptionHookPoint(
            grpc::experimental::InterceptionHookPoints::POST_RECV_INITIAL_METADATA
        )) {
            // Extract metadata
            auto metadata = methods->GetRecvInitialMetadata();
            
            std::string correlation_id;
            if (auto it = metadata->find("x-correlation-id"); it != metadata->end()) {
                correlation_id = std::string(it->second.data(), it->second.size());
            } else {
                correlation_id = generate_uuid();
            }
            
            // Store in context for this call
            // ... context management
            
            logger_.info("RPC started", {
                {"method", methods->GetMethod()},
                {"correlation_id", correlation_id}
            });
            
            start_time_ = std::chrono::steady_clock::now();
        }
        
        if (methods->QueryInterceptionHookPoint(
            grpc::experimental::InterceptionHookPoints::POST_SEND_STATUS
        )) {
            auto duration = std::chrono::steady_clock::now() - start_time_;
            auto duration_ms = std::chrono::duration<double, std::milli>(duration).count();
            
            logger_.info("RPC completed", {
                {"duration_ms", duration_ms}
            });
        }
        
        methods->Proceed();
    }
    
private:
    Logger logger_ = get_logger("agora.grpc");
    std::chrono::steady_clock::time_point start_time_;
};

class LoggingInterceptorFactory 
    : public grpc::experimental::ServerInterceptorFactoryInterface {
public:
    grpc::experimental::Interceptor* CreateServerInterceptor(
        grpc::experimental::ServerRpcInfo* info
    ) override {
        return new LoggingInterceptor();
    }
};

}  // namespace agora::log::integrations
```

### Express/NestJS Middleware Integration

```typescript
// integrations/express.ts

import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { getLogger, Logger } from '../logger';
import { AsyncLocalStorage } from 'async_hooks';

// Async local storage for request-scoped logger
const requestLogger = new AsyncLocalStorage<Logger>();

export function getRequestLogger(): Logger {
  return requestLogger.getStore() || getLogger('agora.http');
}

export function loggingMiddleware() {
  const baseLogger = getLogger('agora.http');
  
  return (req: Request, res: Response, next: NextFunction) => {
    // Extract or generate correlation ID
    const correlationId = 
      (req.headers['x-correlation-id'] as string) || uuidv4();
    
    // Extract user ID if authenticated
    const userId = (req as any).user?.id;
    
    // Create request-scoped logger
    const logger = baseLogger.withContext({
      correlationId,
      userId,
      method: req.method,
      path: req.path
    });
    
    logger.info('Request started');
    const start = process.hrtime.bigint();
    
    // Add correlation ID to response
    res.setHeader('X-Correlation-ID', correlationId);
    
    // Log on response finish
    res.on('finish', () => {
      const duration = Number(process.hrtime.bigint() - start) / 1_000_000;
      logger.info('Request completed', {
        statusCode: res.statusCode,
        durationMs: duration
      });
    });
    
    // Run handler with request-scoped logger
    requestLogger.run(logger, () => {
      next();
    });
  };
}
```

---

## Log Collection and Aggregation

The logging library is designed to integrate seamlessly with Fluent Bit and Loki for centralized log aggregation.

### Architecture Overview

```
+------------------+     +------------------+     +------------------+
|   Microservice   |     |   Microservice   |     |   Microservice   |
|   (Python)       |     |   (C++)          |     |   (Node.js)      |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         | Write JSON logs        | Write JSON logs        | Write JSON logs
         v                        v                        v
+------------------------------------------------------------------+
|                    /var/log/agora/                                |
|  +--------------+  +--------------+  +--------------+             |
|  | market-data  |  | portfolio-   |  | notification |             |
|  | .log         |  | manager.log  |  | .log         |             |
|  +--------------+  +--------------+  +--------------+             |
+------------------------------------------------------------------+
         |                        |                        |
         +------------------------+------------------------+
                                  |
                                  v
                    +----------------------------+
                    |        Fluent Bit          |
                    |  (Sidecar or DaemonSet)    |
                    |                            |
                    |  - Tail JSON log files     |
                    |  - Parse structured logs   |
                    |  - Extract labels          |
                    |  - Forward to Loki         |
                    +-------------+--------------+
                                  |
                                  v
                    +----------------------------+
                    |           Loki             |
                    |                            |
                    |  - Index by labels         |
                    |  - Store log content       |
                    |  - Query via LogQL         |
                    +-------------+--------------+
                                  |
                                  v
                    +----------------------------+
                    |          Grafana           |
                    |                            |
                    |  - Dashboard visualization |
                    |  - Log exploration         |
                    |  - Alerting                |
                    +----------------------------+
```

### Standardized Log File Paths

All services MUST write logs to standardized paths for Fluent Bit collection:

| Service | Log File Path |
|---------|---------------|
| Market Data Service | `/var/log/agora/market-data.log` |
| Analysis Engine | `/var/log/agora/analysis-engine.log` |
| Portfolio Manager | `/var/log/agora/portfolio-manager.log` |
| Recommendation Engine | `/var/log/agora/recommendation-engine.log` |
| Notification Service | `/var/log/agora/notification-service.log` |
| Time Series Analysis | `/var/log/agora/timeseries-analysis.log` |

**Configuration:**
```python
# Python service configuration
config = LogConfig(
    service_name="market-data",
    file_path="/var/log/agora/market-data.log",
    max_file_size_mb=100,
    max_backup_count=5
)
```

```cpp
// C++ service configuration
auto config = agora::log::Config::from_env();
config.file_path = "/var/log/agora/portfolio-manager.log";
```

### Fluent Bit Integration

Fluent Bit is configured to tail all log files in `/var/log/agora/`:

```ini
# fluent-bit.conf
[INPUT]
    Name              tail
    Path              /var/log/agora/*.log
    Tag               agora.*
    Parser            agora-json
    Refresh_Interval  5
    Rotate_Wait       30
    DB                /var/log/agora/fluentbit.db
    Mem_Buf_Limit     10MB

[FILTER]
    Name              lua
    Match             agora.*
    Script            extract_service.lua
    Call              extract_service

[OUTPUT]
    Name              loki
    Match             agora.*
    Host              loki
    Port              3100
    Labels            job=agora, service=$service, environment=$environment, level=$level
    Label_Keys        $correlation_id
    Remove_Keys       service,environment,level,host
    Line_Format       json
```

### Loki Label Strategy

Labels are extracted for efficient querying:

| Label | Source | Purpose |
|-------|--------|---------|
| `job` | Static | Group all Agora logs |
| `service` | `service` field | Filter by microservice |
| `environment` | `environment` field | Filter dev/staging/prod |
| `level` | `level` field | Filter by severity |

**LogQL Query Examples:**
```logql
# All errors from market-data service
{job="agora", service="market-data", level="ERROR"}

# Logs with specific correlation ID
{job="agora"} |= "550e8400-e29b-41d4-a716-446655440000"

# Parse JSON and filter by context
{job="agora", service="analysis-engine"} | json | duration_ms > 1000

# Count errors by service
sum by (service) (count_over_time({job="agora", level="ERROR"}[5m]))
```

### Log Retention

Loki is configured with 30-day retention:

```yaml
# loki-config.yml
limits_config:
  retention_period: 720h  # 30 days
  allow_structured_metadata: true

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
```

---

## Sensitive Data Handling

The logging library includes built-in support for sensitive data redaction and masking.

### Redaction Configuration

```python
from agora_log import LogConfig, SensitiveDataConfig

config = LogConfig(
    service_name="market-data",
    sensitive_data=SensitiveDataConfig(
        # Redact these fields completely
        redact_fields=["password", "api_key", "secret", "token", "authorization"],

        # Mask these fields (show partial)
        mask_fields={
            "credit_card": {"show_last": 4, "mask_char": "*"},
            "ssn": {"show_last": 4, "mask_char": "X"},
            "email": {"mask_domain": False}  # user@***
        },

        # Regex patterns to redact
        redact_patterns=[
            r"Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+",  # JWT
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        ]
    )
)
```

### Redaction Implementation

```python
# sensitive.py

import re
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SensitiveDataConfig:
    redact_fields: list[str] = field(default_factory=lambda: [
        "password", "api_key", "secret", "token", "authorization",
        "private_key", "credential", "access_token", "refresh_token"
    ])
    mask_fields: dict[str, dict] = field(default_factory=dict)
    redact_patterns: list[str] = field(default_factory=list)
    redaction_text: str = "[REDACTED]"

class SensitiveDataRedactor:
    """Redacts sensitive data from log entries."""

    def __init__(self, config: SensitiveDataConfig):
        self._config = config
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in config.redact_patterns
        ]

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Redact sensitive data from a dictionary.

        Returns a new dictionary with sensitive fields redacted.
        """
        return self._redact_dict(data)

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in data.items():
            key_lower = key.lower()

            # Check if field should be completely redacted
            if any(field in key_lower for field in self._config.redact_fields):
                result[key] = self._config.redaction_text
                continue

            # Check if field should be masked
            for mask_field, mask_config in self._config.mask_fields.items():
                if mask_field in key_lower:
                    result[key] = self._mask_value(str(value), mask_config)
                    break
            else:
                # Process nested structures
                if isinstance(value, dict):
                    result[key] = self._redact_dict(value)
                elif isinstance(value, str):
                    result[key] = self._redact_string(value)
                elif isinstance(value, list):
                    result[key] = [
                        self._redact_dict(v) if isinstance(v, dict)
                        else self._redact_string(v) if isinstance(v, str)
                        else v
                        for v in value
                    ]
                else:
                    result[key] = value

        return result

    def _redact_string(self, value: str) -> str:
        """Apply pattern-based redaction to string values."""
        result = value
        for pattern in self._compiled_patterns:
            result = pattern.sub(self._config.redaction_text, result)
        return result

    def _mask_value(self, value: str, config: dict) -> str:
        """Mask a value based on configuration."""
        if not value:
            return value

        show_last = config.get("show_last", 4)
        mask_char = config.get("mask_char", "*")

        if len(value) <= show_last:
            return mask_char * len(value)

        visible = value[-show_last:]
        masked = mask_char * (len(value) - show_last)
        return masked + visible
```

### Usage Example

```python
logger = get_logger("auth")

# These fields will be automatically redacted
logger.info("User authenticated",
    user_id="123",
    api_key="sk_live_abc123xyz",  # -> [REDACTED]
    authorization="Bearer eyJ..."   # -> [REDACTED]
)

# Masked fields
logger.info("Payment processed",
    credit_card="4532015112830366",  # -> ************0366
    amount=100.00
)
```

---

## Log Sampling and Rate Limiting

High-volume services can configure log sampling to reduce storage costs while maintaining visibility.

### Sampling Configuration

```python
from agora_log import LogConfig, SamplingConfig

config = LogConfig(
    service_name="market-data",
    sampling=SamplingConfig(
        # Sample rate per log level
        rates={
            "DEBUG": 0.01,    # Log 1% of DEBUG messages
            "INFO": 0.10,     # Log 10% of INFO messages
            "WARNING": 1.0,   # Log all warnings
            "ERROR": 1.0,     # Log all errors
            "CRITICAL": 1.0   # Log all critical
        },

        # Always log these patterns regardless of sampling
        always_log_patterns=[
            r".*startup.*",
            r".*shutdown.*",
            r".*health.*check.*"
        ],

        # Rate limiting (per logger name)
        rate_limit={
            "messages_per_second": 1000,
            "burst_size": 5000
        }
    )
)
```

### Sampling Implementation

```python
# sampling.py

import random
import re
import time
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

@dataclass
class SamplingConfig:
    rates: dict[str, float] = field(default_factory=lambda: {
        "DEBUG": 1.0,
        "INFO": 1.0,
        "WARNING": 1.0,
        "ERROR": 1.0,
        "CRITICAL": 1.0
    })
    always_log_patterns: list[str] = field(default_factory=list)
    rate_limit: dict | None = None

class LogSampler:
    """
    Implements log sampling and rate limiting.

    Sampling reduces log volume for high-frequency events.
    Rate limiting prevents log flooding.
    """

    def __init__(self, config: SamplingConfig):
        self._config = config
        self._always_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in config.always_log_patterns
        ]

        # Rate limiting state
        self._rate_limit_lock = Lock()
        self._token_buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": config.rate_limit["burst_size"] if config.rate_limit else 0,
                     "last_update": time.monotonic()}
        )

    def should_log(
        self,
        level: str,
        message: str,
        logger_name: str
    ) -> tuple[bool, dict]:
        """
        Determine if a log entry should be emitted.

        Returns:
            (should_log, metadata) where metadata includes sampling info
        """
        metadata = {}

        # Check always-log patterns
        for pattern in self._always_patterns:
            if pattern.search(message):
                return True, {"sampled": False}

        # Check rate limit
        if self._config.rate_limit:
            if not self._check_rate_limit(logger_name):
                metadata["rate_limited"] = True
                return False, metadata

        # Apply sampling
        sample_rate = self._config.rates.get(level, 1.0)
        if sample_rate >= 1.0:
            return True, {"sampled": False}

        if random.random() < sample_rate:
            metadata["sampled"] = True
            metadata["sample_rate"] = sample_rate
            return True, metadata

        return False, {"sampled": True, "dropped": True}

    def _check_rate_limit(self, logger_name: str) -> bool:
        """Token bucket rate limiting."""
        if not self._config.rate_limit:
            return True

        with self._rate_limit_lock:
            bucket = self._token_buckets[logger_name]
            now = time.monotonic()

            # Refill tokens
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self._config.rate_limit["burst_size"],
                bucket["tokens"] + elapsed * self._config.rate_limit["messages_per_second"]
            )
            bucket["last_update"] = now

            # Consume token
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True

            return False
```

---

## Dynamic Log Level Control

Services can change log levels at runtime without restart.

### Runtime Level Changes

```python
from agora_log import set_level, get_level, LogLevel

# Check current level
current = get_level()  # LogLevel.INFO

# Change at runtime
set_level(LogLevel.DEBUG)  # All loggers now log DEBUG

# Change for specific logger
set_level(LogLevel.DEBUG, logger_name="agora.market_data.ingestion")

# Reset to configured level
reset_level()
```

### HTTP Endpoint for Level Changes

```python
# FastAPI endpoint for dynamic level control
from fastapi import APIRouter, HTTPException
from agora_log import set_level, get_level, LogLevel, get_all_levels

router = APIRouter(prefix="/admin/logging", tags=["admin"])

@router.get("/level")
async def get_log_level(logger_name: str | None = None):
    """Get current log level."""
    if logger_name:
        return {"logger": logger_name, "level": str(get_level(logger_name))}
    return {"levels": get_all_levels()}

@router.put("/level")
async def set_log_level(
    level: str,
    logger_name: str | None = None,
    duration_seconds: int | None = None
):
    """
    Change log level dynamically.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Optional specific logger (default: all)
        duration_seconds: Auto-revert after this duration (optional)
    """
    try:
        log_level = LogLevel[level.upper()]
    except KeyError:
        raise HTTPException(400, f"Invalid level: {level}")

    set_level(log_level, logger_name, auto_revert_seconds=duration_seconds)

    return {
        "status": "updated",
        "level": level,
        "logger": logger_name or "all",
        "auto_revert_seconds": duration_seconds
    }
```

### Environment Variable Override

```bash
# Override at container start
LOG_LEVEL=DEBUG python -m service

# Or via Kubernetes ConfigMap/Secret
env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: logging-config
        key: level
```

---

## Security Considerations

### Security Best Practices

1. **Never log sensitive credentials**
   - API keys, passwords, tokens
   - Database connection strings
   - Private keys or certificates
   - Use the sensitive data redaction feature

2. **Control log file permissions**
   ```bash
   # Log directory permissions
   chmod 750 /var/log/agora
   chown app:app /var/log/agora

   # Log file permissions
   chmod 640 /var/log/agora/*.log
   ```

3. **Encrypt logs in transit**
   - Fluent Bit → Loki uses TLS
   - Configure mTLS for production

4. **Encrypt logs at rest**
   - Use encrypted storage volumes
   - Loki supports encryption at rest

5. **Access control for log queries**
   - Grafana RBAC for log access
   - Service-specific access policies

### Log Injection Prevention

The library automatically sanitizes log messages to prevent log injection attacks:

```python
# Log injection prevention

def sanitize_message(message: str) -> str:
    """
    Sanitize log message to prevent injection attacks.

    - Escapes newlines (prevents log splitting)
    - Removes ANSI escape codes
    - Limits message length
    """
    # Escape newlines
    message = message.replace('\n', '\\n').replace('\r', '\\r')

    # Remove ANSI escape codes
    message = re.sub(r'\x1b\[[0-9;]*m', '', message)

    # Limit length (configurable)
    max_length = 10000
    if len(message) > max_length:
        message = message[:max_length] + "...[truncated]"

    return message
```

### Audit Logging

For compliance requirements, configure audit logging:

```python
from agora_log import get_logger, LogConfig, AuditConfig

config = LogConfig(
    service_name="auth-service",
    audit=AuditConfig(
        enabled=True,
        file_path="/var/log/agora/audit/auth-audit.log",
        include_user_id=True,
        include_ip_address=True,
        include_request_id=True,
        retention_days=365  # 1 year for compliance
    )
)

# Audit logger with immutable entries
audit_logger = get_logger("audit", config)
audit_logger.audit("User login", user_id="123", ip_address="10.0.0.1")
```

---

## Kubernetes and Container Patterns

### Container Logging Strategy

```
+--------------------------------------------------+
|                  Kubernetes Pod                   |
|                                                   |
|  +-----------------+  +------------------------+  |
|  |   Application   |  |   Fluent Bit Sidecar   |  |
|  |   Container     |  |   Container            |  |
|  |                 |  |                        |  |
|  | Writes to:      |  | Tails:                 |  |
|  | /var/log/agora/ |  | /var/log/agora/*.log   |  |
|  |                 |  |                        |  |
|  +--------+--------+  +------------+-----------+  |
|           |                        |              |
|           |    Shared Volume       |              |
|           |  (emptyDir or PVC)     |              |
|           +-----------+------------+              |
+--------------------------------------------------+
                        |
                        v
              +---------+---------+
              |       Loki        |
              | (ClusterIP/LB)    |
              +-------------------+
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-data-service
spec:
  template:
    spec:
      containers:
        # Application container
        - name: market-data
          image: agora/market-data:latest
          env:
            - name: LOG_FILE_PATH
              value: /var/log/agora/market-data.log
            - name: LOG_CONSOLE_ENABLED
              value: "true"
            - name: LOG_CONSOLE_FORMAT
              value: json
            - name: ENVIRONMENT
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: HOSTNAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          volumeMounts:
            - name: logs
              mountPath: /var/log/agora

        # Fluent Bit sidecar
        - name: fluent-bit
          image: fluent/fluent-bit:latest
          volumeMounts:
            - name: logs
              mountPath: /var/log/agora
              readOnly: true
            - name: fluent-bit-config
              mountPath: /fluent-bit/etc
          resources:
            limits:
              memory: 128Mi
              cpu: 100m

      volumes:
        - name: logs
          emptyDir: {}
        - name: fluent-bit-config
          configMap:
            name: fluent-bit-config
```

### ConfigMap for Fluent Bit

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Daemon        Off
        Log_Level     info
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/agora/*.log
        Tag               agora.*
        Parser            agora-json
        Refresh_Interval  5
        Mem_Buf_Limit     10MB

    [OUTPUT]
        Name              loki
        Match             agora.*
        Host              loki.monitoring.svc.cluster.local
        Port              3100
        Labels            job=agora, namespace=${POD_NAMESPACE}, pod=${POD_NAME}

  parsers.conf: |
    [PARSER]
        Name         agora-json
        Format       json
        Time_Key     timestamp
        Time_Format  %Y-%m-%dT%H:%M:%S.%LZ
```

### Log Aggregation Patterns

**Pattern 1: Sidecar (Recommended)**
- One Fluent Bit per pod
- Reads from shared volume
- Best isolation and control

**Pattern 2: DaemonSet**
- One Fluent Bit per node
- Uses hostPath volumes
- Lower resource overhead

**Pattern 3: Direct Push**
- Application pushes directly to Loki
- No sidecar needed
- Higher latency, less resilient

---

## Metrics and Observability

### Prometheus Metrics

The logging library exposes metrics for monitoring:

```python
# metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Log entry counters
LOG_ENTRIES_TOTAL = Counter(
    'agora_log_entries_total',
    'Total number of log entries',
    ['service', 'level', 'logger']
)

# Log entry latency
LOG_ENTRY_DURATION = Histogram(
    'agora_log_entry_duration_seconds',
    'Time to process log entry',
    ['handler'],
    buckets=[.00001, .00005, .0001, .0005, .001, .005, .01, .05]
)

# Queue metrics
LOG_QUEUE_SIZE = Gauge(
    'agora_log_queue_size',
    'Current async queue size',
    ['service']
)

LOG_QUEUE_DROPPED = Counter(
    'agora_log_queue_dropped_total',
    'Total dropped entries due to queue overflow',
    ['service']
)

# File handler metrics
LOG_FILE_ROTATIONS = Counter(
    'agora_log_file_rotations_total',
    'Total log file rotations',
    ['service', 'file_path']
)

LOG_FILE_SIZE_BYTES = Gauge(
    'agora_log_file_size_bytes',
    'Current log file size',
    ['service', 'file_path']
)
```

### Metrics Integration

```python
# In logger implementation
class MetricsHandler(Handler):
    """Handler that updates Prometheus metrics."""

    def __init__(self, service_name: str, wrapped_handler: Handler):
        self._service = service_name
        self._handler = wrapped_handler

    def emit(self, entry: LogEntry) -> None:
        # Increment counter
        LOG_ENTRIES_TOTAL.labels(
            service=self._service,
            level=entry.level,
            logger=entry.logger_name
        ).inc()

        # Measure handler duration
        with LOG_ENTRY_DURATION.labels(
            handler=type(self._handler).__name__
        ).time():
            self._handler.emit(entry)
```

### Grafana Dashboard Integration

```json
{
  "dashboard": {
    "title": "Agora Logging Metrics",
    "panels": [
      {
        "title": "Log Volume by Service",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum by (service) (rate(agora_log_entries_total[5m]))",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum by (service) (rate(agora_log_entries_total{level=\"ERROR\"}[5m]))",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Queue Overflow Events",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(agora_log_queue_dropped_total)"
          }
        ]
      },
      {
        "title": "Log Processing Latency (p99)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(agora_log_entry_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      }
    ]
  }
}
```

### Health Check Endpoint

```python
# health.py

from fastapi import APIRouter
from agora_log import get_health_status

router = APIRouter()

@router.get("/health/logging")
async def logging_health():
    """
    Check logging subsystem health.

    Returns status of all handlers and queue.
    """
    status = get_health_status()

    return {
        "status": "healthy" if status.is_healthy else "degraded",
        "handlers": [
            {
                "type": h.type,
                "status": "ok" if h.is_healthy else "error",
                "error": h.last_error
            }
            for h in status.handlers
        ],
        "queue": {
            "size": status.queue_size,
            "capacity": status.queue_capacity,
            "dropped_total": status.dropped_total
        },
        "metrics": {
            "entries_total": status.entries_total,
            "errors_total": status.errors_total
        }
    }
```

---

## Summary

This design document covers the complete architecture and implementation details for the Agora logging library:

1. **Architecture Overview** - Multi-language library with consistent API
2. **Component Design** - Detailed class structures for Python, C++, and JavaScript
3. **Source Location Capture** - REQUIRED file, line, function fields
4. **Interface Contracts** - JSON schema and handler interfaces
5. **File Rotation** - Size-based rotation algorithm
6. **Thread Safety** - Lock-based implementations for each language
7. **Async Queue** - Non-blocking logging with bounded queues
8. **Configuration** - Environment variable and file-based configuration
9. **Error Handling** - Graceful degradation strategy
10. **Performance** - Optimization techniques and benchmarking
11. **Framework Integration** - FastAPI, gRPC, Express/NestJS patterns
12. **Log Collection** - Fluent Bit and Loki integration for centralized aggregation
13. **Sensitive Data** - Redaction and masking of credentials and PII
14. **Sampling** - Rate limiting and sampling for high-volume services
15. **Dynamic Levels** - Runtime log level changes without restart
16. **Security** - Best practices for log security and audit logging
17. **Kubernetes** - Container and sidecar patterns for cloud-native deployment
18. **Metrics** - Prometheus metrics and Grafana dashboard integration

Key implementation requirements:
- `file`, `line`, and `function` are **REQUIRED** in all log entries
- Dual output to both console and files
- Standardized log paths: `/var/log/agora/<service-name>.log`
- Size-based rotation at 100MB with 5 backup files
- Performance targets: Python/JS < 10 microseconds, C++ < 2 microseconds
- Thread-safe implementations in all languages
- Fluent Bit sidecar pattern for log collection
- 30-day log retention in Loki
- Sensitive data redaction enabled by default
