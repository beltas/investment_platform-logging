/**
 * @file config.cpp
 * @brief Configuration implementation
 */

#include <agora/log/config.hpp>
#include <agora/log/level.hpp>
#include <cstdlib>
#include <string>

namespace agora::log {

namespace {

std::string getenv_or(const char* name, std::string default_value) {
    const char* value = std::getenv(name);
    return value ? std::string(value) : default_value;
}

int getenv_int_or(const char* name, int default_value) {
    const char* value = std::getenv(name);
    if (!value) return default_value;

    try {
        return std::stoi(value);
    } catch (...) {
        return default_value;
    }
}

double getenv_double_or(const char* name, double default_value) {
    const char* value = std::getenv(name);
    if (!value) return default_value;

    try {
        return std::stod(value);
    } catch (...) {
        return default_value;
    }
}

bool getenv_bool_or(const char* name, bool default_value) {
    const char* value = std::getenv(name);
    if (!value) return default_value;

    std::string str(value);
    if (str == "true" || str == "1" || str == "yes") return true;
    if (str == "false" || str == "0" || str == "no") return false;

    return default_value;
}

}  // anonymous namespace

std::expected<Config, Error> Config::from_env(std::string_view service_name) {
    Config config;
    config.service_name = std::string(service_name);

    // Read environment variables
    config.environment = getenv_or("AGORA_LOG_ENVIRONMENT", "development");
    config.version = getenv_or("AGORA_LOG_VERSION", "0.0.0");

    // Parse log level
    std::string level_str = getenv_or("AGORA_LOG_LEVEL", "INFO");
    config.level = from_string(level_str, Level::Info);

    // Console settings
    config.console_enabled = getenv_bool_or("AGORA_LOG_CONSOLE_ENABLED", true);
    config.console_json = getenv_bool_or("AGORA_LOG_CONSOLE_JSON", true);

    // File settings
    config.file_enabled = getenv_bool_or("AGORA_LOG_FILE_ENABLED", true);

    std::string file_path = getenv_or(
        "AGORA_LOG_FILE_PATH",
        "/var/log/agora/" + std::string(service_name) + ".log"
    );
    config.file_path = file_path;

    config.max_file_size_mb = static_cast<std::size_t>(
        getenv_double_or("AGORA_LOG_MAX_FILE_SIZE_MB", 100.0)
    );
    config.max_backup_count = static_cast<std::size_t>(
        getenv_int_or("AGORA_LOG_MAX_BACKUP_COUNT", 5)
    );

    return config;
}

}  // namespace agora::log
