/**
 * @file handler.hpp
 * @brief Base handler interface
 */

#pragma once

#include "../entry.hpp"

namespace agora::log {

/**
 * @brief Abstract base class for log handlers.
 */
class Handler {
public:
    Handler() noexcept = default;
    virtual ~Handler() noexcept = default;

    // Non-copyable, non-movable (polymorphic base class)
    Handler(const Handler&) = delete;
    Handler& operator=(const Handler&) = delete;
    Handler(Handler&&) = delete;
    Handler& operator=(Handler&&) = delete;

    /**
     * @brief Write a log entry.
     */
    virtual void write(const LogEntry& entry) = 0;

    /**
     * @brief Flush any buffered entries.
     */
    virtual void flush() noexcept = 0;
};

}  // namespace agora::log
