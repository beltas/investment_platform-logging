/**
 * @file config.hpp
 * @brief Configuration structures for Agora logging
 */

#pragma once

#include <string>
#include <filesystem>
#include <expected>
#include <optional>

#include "logger.hpp"

namespace agora::log {

/**
 * @brief Logging configuration.
 */
struct Config {
    std::string service_name;
    std::string environment = "development";
    std::string version = "0.0.0";
    Level level = Level::Info;
    
    // Console output
    bool console_enabled = true;
    bool console_json = true;
    
    // File output
    bool file_enabled = true;
    std::filesystem::path file_path = "/agora/logs/app.log";
    double max_file_size_mb = 100.0;   // Supports fractional MB for small test files
    std::size_t max_backup_count = 5;
    
    // Default context
    Context default_context;
    
    /**
     * @brief Load configuration from environment variables.
     */
    static std::expected<Config, Error> from_env(std::string_view service_name);
};

}  // namespace agora::log
