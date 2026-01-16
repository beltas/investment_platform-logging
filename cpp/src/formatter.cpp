/**
 * @file formatter.cpp
 * @brief Log entry formatters implementation
 */

#include <agora/log/formatter.hpp>
#include <agora/log/level.hpp>
#include <nlohmann/json.hpp>
#include <iomanip>
#include <sstream>
#include <ctime>

namespace agora::log {

using json = nlohmann::json;

/**
 * @brief Convert context value to JSON.
 */
json context_value_to_json(const ContextValue& value) {
    return std::visit([](const auto& v) -> json {
        return v;
    }, value);
}

/**
 * @brief Format timestamp as ISO 8601 with microseconds.
 */
std::string format_timestamp(std::chrono::system_clock::time_point tp) {
    auto time_t_val = std::chrono::system_clock::to_time_t(tp);
    auto microseconds = std::chrono::duration_cast<std::chrono::microseconds>(
        tp.time_since_epoch()
    ) % 1'000'000;

    std::tm tm{};
    gmtime_r(&time_t_val, &tm);

    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(6) << microseconds.count();
    oss << 'Z';

    return oss.str();
}

std::string format_json(const LogEntry& entry) {
    json j;

    // Required fields
    j["timestamp"] = format_timestamp(entry.timestamp);
    j["level"] = to_string(entry.level);
    j["message"] = entry.message;
    j["service"] = entry.service_name;
    j["environment"] = entry.environment;
    j["version"] = entry.version;
    j["logger_name"] = entry.logger_name;

    // Source location (REQUIRED)
    j["file"] = entry.location.file;
    j["line"] = entry.location.line;
    j["function"] = entry.location.function;

    // Context (if not empty)
    if (!entry.context.empty()) {
        json context_obj;
        for (const auto& [key, value] : entry.context) {
            context_obj[key] = context_value_to_json(value);
        }
        j["context"] = context_obj;
    }

    // Exception (if present)
    if (entry.exception) {
        j["exception"] = {
            {"type", entry.exception->type},
            {"message", entry.exception->message}
        };
    }

    // Duration (if present)
    if (entry.duration_ms) {
        j["duration_ms"] = *entry.duration_ms;
    }

    return j.dump();
}

std::string format_text(const LogEntry& entry) {
    std::ostringstream oss;

    // [YYYY-MM-DD HH:MM:SS.ssssss] [LEVEL] [service] message
    auto time_t_val = std::chrono::system_clock::to_time_t(entry.timestamp);
    auto microseconds = std::chrono::duration_cast<std::chrono::microseconds>(
        entry.timestamp.time_since_epoch()
    ) % 1'000'000;

    std::tm tm{};
    localtime_r(&time_t_val, &tm);

    oss << '[' << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(6) << microseconds.count();
    oss << "] ";

    oss << '[' << to_string(entry.level) << "] ";
    oss << '[' << entry.service_name << "] ";
    oss << entry.message;

    // Add context in parentheses
    if (!entry.context.empty()) {
        oss << " (";
        bool first = true;
        for (const auto& [key, value] : entry.context) {
            if (!first) oss << ", ";
            first = false;

            oss << key << '=';
            std::visit([&oss](const auto& v) {
                using T = std::decay_t<decltype(v)>;
                if constexpr (std::is_same_v<T, std::string>) {
                    oss << v;
                } else if constexpr (std::is_same_v<T, bool>) {
                    oss << (v ? "true" : "false");
                } else {
                    oss << v;
                }
            }, value);
        }
        oss << ')';
    }

    // Add duration if present
    if (entry.duration_ms) {
        oss << " [" << *entry.duration_ms << "ms]";
    }

    // Add exception if present
    if (entry.exception) {
        oss << " [" << entry.exception->type << ": " << entry.exception->message << "]";
    }

    return oss.str();
}

}  // namespace agora::log
