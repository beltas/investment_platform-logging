/**
 * @file console.cpp
 * @brief Console handler implementation
 */

#include <agora/log/handlers/console.hpp>
#include <agora/log/formatter.hpp>
#include <iostream>

namespace agora::log {

ConsoleHandler::ConsoleHandler(bool json_format) noexcept
    : json_format_(json_format) {
}

void ConsoleHandler::write(const LogEntry& entry) {
    std::string formatted = json_format_
        ? format_json(entry)
        : format_text(entry);

    // Use stderr for ERROR and CRITICAL, stdout for others
    if (entry.level >= Level::Error) {
        std::cerr << formatted << std::endl;
    } else {
        std::cout << formatted << std::endl;
    }
}

void ConsoleHandler::flush() noexcept {
    try {
        std::cout.flush();
        std::cerr.flush();
    } catch (...) {
        // Ignore flush errors - noexcept guarantee
    }
}

}  // namespace agora::log
