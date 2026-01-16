/**
 * @file formatter.hpp
 * @brief Log entry formatters
 */

#pragma once

#include <string>
#include "entry.hpp"

namespace agora::log {

/**
 * @brief Format log entry as JSON string.
 */
std::string format_json(const LogEntry& entry);

/**
 * @brief Format log entry as human-readable text.
 */
std::string format_text(const LogEntry& entry);

}  // namespace agora::log
