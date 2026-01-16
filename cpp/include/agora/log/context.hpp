/**
 * @file context.hpp
 * @brief Context builder utilities
 */

#pragma once

#include <string>
#include <unordered_map>
#include <variant>

#include "logger.hpp"

namespace agora::log {

/**
 * @brief Fluent builder for logging context.
 * 
 * Usage:
 *   auto ctx = agora::log::ctx()
 *       .correlation_id("abc123")
 *       .user_id("user-456")
 *       .add("custom_key", "value")
 *       .build();
 */
class ContextBuilder {
public:
    ContextBuilder& correlation_id(std::string value) {
        context_["correlation_id"] = std::move(value);
        return *this;
    }
    
    ContextBuilder& user_id(std::string value) {
        context_["user_id"] = std::move(value);
        return *this;
    }
    
    ContextBuilder& trace_id(std::string value) {
        context_["trace_id"] = std::move(value);
        return *this;
    }
    
    ContextBuilder& span_id(std::string value) {
        context_["span_id"] = std::move(value);
        return *this;
    }
    
    /**
     * @brief Add a key-value pair to the context.
     *
     * Supports string, integral, floating-point, and boolean types.
     */
    template<typename T>
    ContextBuilder& add(std::string key, T value) {
        if constexpr (std::is_same_v<T, std::string>) {
            context_[std::move(key)] = std::move(value);
        } else if constexpr (std::is_same_v<std::decay_t<T>, const char*> ||
                             std::is_same_v<std::decay_t<T>, char*>) {
            // Explicit handling for C-style strings to avoid template deduction issues
            context_[std::move(key)] = std::string(value);
        } else if constexpr (std::is_convertible_v<T, std::string_view>) {
            context_[std::move(key)] = std::string(value);
        } else if constexpr (std::is_same_v<std::decay_t<T>, bool>) {
            // Must check bool before integral, since bool is integral
            context_[std::move(key)] = value;
        } else if constexpr (std::is_integral_v<T>) {
            context_[std::move(key)] = static_cast<std::int64_t>(value);
        } else if constexpr (std::is_floating_point_v<T>) {
            context_[std::move(key)] = static_cast<double>(value);
        }
        return *this;
    }

    /**
     * @brief Explicit overload for const char* to ensure proper handling.
     */
    ContextBuilder& add(std::string key, const char* value) {
        context_[std::move(key)] = std::string(value);
        return *this;
    }

    /**
     * @brief Explicit overload for string_view.
     */
    ContextBuilder& add(std::string key, std::string_view value) {
        context_[std::move(key)] = std::string(value);
        return *this;
    }
    
    Context build() const {
        return context_;
    }
    
private:
    Context context_;
};

/**
 * @brief Create a new context builder.
 */
inline ContextBuilder ctx() {
    return ContextBuilder{};
}

}  // namespace agora::log
