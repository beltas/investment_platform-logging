/**
 * @file entry.hpp
 * @brief Log entry structure
 */

#pragma once

#include <string>
#include <chrono>
#include <optional>
#include "logger.hpp"

namespace agora::log {

/**
 * @brief Exception information for log entries.
 */
struct ExceptionInfo {
    std::string type;
    std::string message;

    ExceptionInfo() noexcept = default;
    ExceptionInfo(std::string t, std::string m) noexcept
        : type(std::move(t)), message(std::move(m)) {}

    ExceptionInfo(const ExceptionInfo&) = default;
    ExceptionInfo(ExceptionInfo&&) noexcept = default;
    ExceptionInfo& operator=(const ExceptionInfo&) = default;
    ExceptionInfo& operator=(ExceptionInfo&&) noexcept = default;
    ~ExceptionInfo() noexcept = default;
};

/**
 * @brief Complete log entry with all metadata.
 */
struct LogEntry {
    std::chrono::system_clock::time_point timestamp;
    Level level;
    std::string message;
    std::string logger_name;
    SourceLocation location;
    Context context;
    std::optional<ExceptionInfo> exception;
    std::optional<double> duration_ms;

    // Config metadata
    std::string service_name;
    std::string environment;
    std::string version;

    LogEntry() noexcept = default;
    LogEntry(const LogEntry&) = default;
    LogEntry(LogEntry&&) noexcept = default;
    LogEntry& operator=(const LogEntry&) = default;
    LogEntry& operator=(LogEntry&&) noexcept = default;
    ~LogEntry() noexcept = default;
};

}  // namespace agora::log
