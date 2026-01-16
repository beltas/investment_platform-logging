/**
 * @file level.hpp
 * @brief Log level enum and utilities
 */

#pragma once

#include <string_view>

namespace agora::log {

/**
 * @brief Log levels.
 */
enum class Level {
    Debug = 10,
    Info = 20,
    Warning = 30,
    Error = 40,
    Critical = 50
};

/**
 * @brief Convert level to string.
 */
constexpr std::string_view to_string(Level level) noexcept {
    switch (level) {
        case Level::Debug: return "DEBUG";
        case Level::Info: return "INFO";
        case Level::Warning: return "WARNING";
        case Level::Error: return "ERROR";
        case Level::Critical: return "CRITICAL";
    }
    return "UNKNOWN";
}

/**
 * @brief Parse level from string.
 */
inline Level from_string(std::string_view str, Level default_level = Level::Info) noexcept {
    if (str == "DEBUG" || str == "debug") return Level::Debug;
    if (str == "INFO" || str == "info") return Level::Info;
    if (str == "WARNING" || str == "warning") return Level::Warning;
    if (str == "ERROR" || str == "error") return Level::Error;
    if (str == "CRITICAL" || str == "critical") return Level::Critical;
    return default_level;
}

}  // namespace agora::log
