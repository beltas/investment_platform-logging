/**
 * @file logger.cpp
 * @brief Logger implementation
 */

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>
#include <agora/log/entry.hpp>
#include <agora/log/handlers/handler.hpp>
#include <agora/log/handlers/console.hpp>
#include <agora/log/handlers/rotating_file.hpp>
#include <mutex>
#include <unordered_map>
#include <memory>
#include <cxxabi.h>

namespace agora::log {

// Global state
namespace {
    std::mutex g_mutex;
    std::shared_ptr<const Config> g_config;
    std::unordered_map<std::string, Logger> g_loggers;
    std::vector<std::shared_ptr<Handler>> g_handlers;
}

// Logger implementation

Logger::Logger(
    std::string name,
    std::shared_ptr<const Config> config,
    Context context
)
    : name_(std::move(name))
    , config_(std::move(config))
    , context_(std::move(context))
    , handlers_(g_handlers) {
}

void Logger::info(
    std::string_view message,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Info, message, loc, std::move(ctx));
}

void Logger::debug(
    std::string_view message,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Debug, message, loc, std::move(ctx));
}

void Logger::warning(
    std::string_view message,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Warning, message, loc, std::move(ctx));
}

void Logger::error(
    std::string_view message,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Error, message, loc, std::move(ctx));
}

void Logger::error(
    std::string_view message,
    const std::exception& ex,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Error, message, loc, std::move(ctx), &ex);
}

void Logger::critical(
    std::string_view message,
    Context ctx,
    SourceLocation loc
) const {
    log(Level::Critical, message, loc, std::move(ctx));
}

Logger Logger::with_context(Context additional_context) const {
    // Merge contexts: parent + additional
    Context merged = context_;
    for (auto& [key, value] : additional_context) {
        merged[key] = std::move(value);
    }

    return Logger(name_, config_, std::move(merged));
}

Timer Logger::timer(
    std::string operation,
    Context ctx,
    SourceLocation loc
) const {
    // Merge context
    Context merged = context_;
    for (auto& [key, value] : ctx) {
        merged[key] = std::move(value);
    }

    return Timer(*this, std::move(operation), std::move(merged), loc);
}

void Logger::log(
    Level level,
    std::string_view message,
    const SourceLocation& loc,
    Context ctx,
    const std::exception* ex
) const {
    // Filter by level - use [[unlikely]] since most logs pass the filter
    // when the configured level is appropriate
    if (level < config_->level) [[unlikely]] {
        return;
    }

    // Merge context: default + logger + call
    Context merged = config_->default_context;
    for (const auto& [key, value] : context_) {
        merged[key] = value;
    }
    for (auto& [key, value] : ctx) {
        merged[key] = std::move(value);
    }

    // Create log entry
    LogEntry entry;
    entry.timestamp = std::chrono::system_clock::now();
    entry.level = level;
    entry.message = std::string(message);
    entry.logger_name = name_;
    entry.location = loc;
    entry.context = std::move(merged);
    entry.service_name = config_->service_name;
    entry.environment = config_->environment;
    entry.version = config_->version;

    // Add exception info if present
    if (ex) {
        ExceptionInfo ex_info;

        // Demangle exception type name
        int status = 0;
        char* demangled = abi::__cxa_demangle(typeid(*ex).name(), nullptr, nullptr, &status);
        ex_info.type = (status == 0 && demangled) ? demangled : typeid(*ex).name();
        if (demangled) {
            free(demangled);
        }

        ex_info.message = ex->what();
        entry.exception = ex_info;
    }

    // Write to all handlers
    for (const auto& handler : handlers_) {
        try {
            handler->write(entry);
        } catch (...) {
            // Ignore handler errors to prevent logging from crashing the application
        }
    }
}

// Timer implementation

Timer::Timer(
    const Logger& logger,
    std::string operation,
    Context context,
    SourceLocation location
)
    : logger_(&logger)
    , operation_(std::move(operation))
    , context_(std::move(context))
    , location_(location)
    , start_(std::chrono::steady_clock::now()) {
}

Timer::Timer(Timer&& other) noexcept
    : logger_(nullptr)
    , start_(std::chrono::steady_clock::now())
    , cancelled_(true) {
    // Lock the moved-from timer to prevent race with its destructor
    std::lock_guard<std::mutex> lock(other.mutex_);
    logger_ = other.logger_;
    operation_ = std::move(other.operation_);
    context_ = std::move(other.context_);
    location_ = other.location_;
    start_ = other.start_;
    cancelled_ = other.cancelled_;
    other.cancelled_ = true;  // Cancel moved-from timer
}

Timer& Timer::operator=(Timer&& other) noexcept {
    if (this != &other) {
        // Lock both mutexes to prevent races, using std::lock to avoid deadlock
        std::unique_lock<std::mutex> lock1(mutex_, std::defer_lock);
        std::unique_lock<std::mutex> lock2(other.mutex_, std::defer_lock);
        std::lock(lock1, lock2);

        logger_ = other.logger_;
        operation_ = std::move(other.operation_);
        context_ = std::move(other.context_);
        location_ = other.location_;
        start_ = other.start_;
        cancelled_ = other.cancelled_;
        other.cancelled_ = true;
    }
    return *this;
}

Timer::~Timer() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!cancelled_ && logger_) {
        auto end = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start_);
        double duration_ms = duration.count() / 1000.0;

        // Create entry with duration
        LogEntry entry;
        entry.timestamp = std::chrono::system_clock::now();
        entry.level = Level::Info;
        entry.message = operation_;
        entry.logger_name = logger_->name_;
        entry.location = location_;
        entry.context = context_;
        entry.duration_ms = duration_ms;
        entry.service_name = logger_->config_->service_name;
        entry.environment = logger_->config_->environment;
        entry.version = logger_->config_->version;

        // Write to handlers
        for (const auto& handler : logger_->handlers_) {
            try {
                handler->write(entry);
            } catch (...) {
                // Ignore errors
            }
        }
    }
}

void Timer::cancel() noexcept {
    std::lock_guard<std::mutex> lock(mutex_);
    cancelled_ = true;
}

// Global functions

std::expected<void, Error> initialize(const Config& config) {
    std::lock_guard<std::mutex> lock(g_mutex);

    try {
        // Store config
        g_config = std::make_shared<Config>(config);

        // Clear existing handlers
        g_handlers.clear();

        // Create console handler if enabled
        if (config.console_enabled) {
            g_handlers.push_back(
                std::make_shared<ConsoleHandler>(config.console_json)
            );
        }

        // Create file handler if enabled
        if (config.file_enabled) {
            std::size_t max_size_bytes = config.max_file_size_mb * 1024 * 1024;

            g_handlers.push_back(
                std::make_shared<RotatingFileHandler>(
                    config.file_path,
                    max_size_bytes,
                    config.max_backup_count
                )
            );
        }

        return {};
    } catch (const std::exception& ex) {
        return std::unexpected(Error{ex.what(), -1});
    }
}

void flush() {
    std::lock_guard<std::mutex> lock(g_mutex);

    // Flush all handlers without clearing state
    for (const auto& handler : g_handlers) {
        try {
            handler->flush();
        } catch (...) {
            // Ignore errors during flush
        }
    }
}

void shutdown() {
    std::lock_guard<std::mutex> lock(g_mutex);

    // Flush all handlers
    for (const auto& handler : g_handlers) {
        try {
            handler->flush();
        } catch (...) {
            // Ignore errors during shutdown
        }
    }

    // Clear state
    g_handlers.clear();
    g_loggers.clear();
    g_config.reset();
}

Logger get_logger(std::string_view name) {
    std::lock_guard<std::mutex> lock(g_mutex);

    std::string name_str(name);

    // Return existing logger if found
    auto it = g_loggers.find(name_str);
    if (it != g_loggers.end()) {
        return it->second;
    }

    // Create new logger
    if (!g_config) {
        // If not initialized, use default config
        Config default_config;
        default_config.service_name = "unknown";
        g_config = std::make_shared<Config>(default_config);
    }

    Logger logger(name_str, g_config, {});
    auto [inserted_it, _] = g_loggers.emplace(name_str, logger);

    return inserted_it->second;
}

}  // namespace agora::log
