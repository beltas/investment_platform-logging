/**
 * @file logger.hpp
 * @brief Main logger interface for Agora Trading Platform
 *
 * Provides a high-performance, thread-safe logging API with:
 * - Automatic source location capture (file, line, function - REQUIRED)
 * - Context injection and inheritance
 * - Dual output (console + file)
 * - Compile-time log level filtering
 */

#pragma once

#include <string>
#include <string_view>
#include <memory>
#include <vector>
#include <unordered_map>
#include <variant>
#include <chrono>
#include <expected>
#include <source_location>
#include <cstdint>
#include <mutex>

#include "level.hpp"

namespace agora::log {

// Forward declarations
class Config;
class Handler;
class Timer;

/**
 * @brief Error information for logging operations.
 */
struct Error {
    std::string message;
    int code = 0;
};

/**
 * @brief Source location information for log entries.
 * 
 * IMPORTANT: file, line, and function are REQUIRED in all log entries.
 */
struct SourceLocation {
    std::string_view file;
    std::uint32_t line;
    std::string_view function;
    
    /**
     * @brief Create from std::source_location (C++20).
     */
    static constexpr SourceLocation current(
        std::source_location loc = std::source_location::current()
    ) noexcept {
        return SourceLocation{
            .file = extract_filename(loc.file_name()),
            .line = loc.line(),
            .function = loc.function_name()
        };
    }
    
private:
    static constexpr std::string_view extract_filename(
        std::string_view path
    ) noexcept {
        auto pos = path.find_last_of("/\\");
        return (pos != std::string_view::npos) 
            ? path.substr(pos + 1) 
            : path;
    }
};

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
     */
    void info(
        std::string_view message,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
    /**
     * @brief Log at ERROR level with optional exception.
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
    
    /**
     * @brief Create child logger with additional context.
     */
    [[nodiscard]]
    Logger with_context(Context additional_context) const;
    
    /**
     * @brief Create an RAII timer for operation duration logging.
     */
    [[nodiscard]]
    Timer timer(
        std::string operation,
        Context ctx = {},
        SourceLocation loc = SourceLocation::current()
    ) const;
    
private:
    friend class Timer;  // Timer needs access to private members for logging

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
 *
 * Thread-safe: Uses mutex protection for move operations to prevent
 * race conditions during concurrent access.
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

    Timer(const Timer&) = delete;
    Timer& operator=(const Timer&) = delete;
    Timer(Timer&& other) noexcept;
    Timer& operator=(Timer&& other) noexcept;

    void cancel() noexcept;

private:
    mutable std::mutex mutex_;  // Protects cancelled_ during move/destruction
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

/**
 * @brief Flush all handlers without shutting down.
 *
 * Call this to ensure all buffered log entries are written to disk
 * while keeping the logging system active.
 */
void flush();

/**
 * @brief Shutdown the logging system.
 *
 * Flushes all handlers and clears all state. After calling shutdown(),
 * initialize() must be called again before logging.
 */
void shutdown();

[[nodiscard]]
Logger get_logger(std::string_view name);

}  // namespace agora::log
