/**
 * @file console.hpp
 * @brief Console output handler
 */

#pragma once

#include "handler.hpp"
#include <iostream>

namespace agora::log {

/**
 * @brief Console handler that writes to stdout/stderr.
 */
class ConsoleHandler : public Handler {
public:
    /**
     * @param json_format If true, output JSON; otherwise text format
     */
    explicit ConsoleHandler(bool json_format = true) noexcept;

    void write(const LogEntry& entry) override;
    void flush() noexcept override;

    /** Check if JSON format is enabled */
    [[nodiscard]] bool is_json_format() const noexcept { return json_format_; }

private:
    bool json_format_;
};

}  // namespace agora::log
