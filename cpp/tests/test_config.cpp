/**
 * @file test_config.cpp
 * @brief Configuration tests
 *
 * Tests cover:
 * - Config from environment variables
 * - Default values
 * - Level parsing
 */

#include <catch2/catch_test_macros.hpp>

#include <agora/log/config.hpp>

#include <cstdlib>

using namespace agora::log;

TEST_CASE("Config from environment variables", "[config][env]") {
    // Set environment variables
    setenv("AGORA_LOG_LEVEL", "WARNING", 1);
    setenv("AGORA_LOG_ENVIRONMENT", "production", 1);
    setenv("AGORA_LOG_VERSION", "2.0.0", 1);

    auto result = Config::from_env("test-service");

    REQUIRE(result.has_value());

    auto& config = *result;

    REQUIRE(config.service_name == "test-service");
    REQUIRE(config.level == Level::Warning);
    REQUIRE(config.environment == "production");
    REQUIRE(config.version == "2.0.0");

    // Clean up
    unsetenv("AGORA_LOG_LEVEL");
    unsetenv("AGORA_LOG_ENVIRONMENT");
    unsetenv("AGORA_LOG_VERSION");
}

TEST_CASE("Config default values", "[config][defaults]") {
    // Clear environment
    unsetenv("AGORA_LOG_LEVEL");
    unsetenv("AGORA_LOG_ENVIRONMENT");
    unsetenv("AGORA_LOG_VERSION");

    auto result = Config::from_env("test-service");

    REQUIRE(result.has_value());

    auto& config = *result;

    REQUIRE(config.service_name == "test-service");
    REQUIRE(config.level == Level::Info);  // Default
    REQUIRE(config.environment == "development");  // Default
    REQUIRE(config.console_enabled == true);
}

TEST_CASE("Level parsing", "[config][level]") {
    SECTION("DEBUG") {
        setenv("AGORA_LOG_LEVEL", "DEBUG", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Debug);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("INFO") {
        setenv("AGORA_LOG_LEVEL", "INFO", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Info);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("WARNING") {
        setenv("AGORA_LOG_LEVEL", "WARNING", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Warning);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("ERROR") {
        setenv("AGORA_LOG_LEVEL", "ERROR", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Error);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("CRITICAL") {
        setenv("AGORA_LOG_LEVEL", "CRITICAL", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Critical);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("Case insensitive") {
        setenv("AGORA_LOG_LEVEL", "warning", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Warning);
        unsetenv("AGORA_LOG_LEVEL");
    }

    SECTION("Invalid level falls back to default") {
        setenv("AGORA_LOG_LEVEL", "INVALID", 1);
        auto result = Config::from_env("test");
        REQUIRE(result.has_value());
        REQUIRE(result->level == Level::Info);  // Default
        unsetenv("AGORA_LOG_LEVEL");
    }
}

TEST_CASE("File path configuration", "[config][file]") {
    setenv("AGORA_LOG_FILE_PATH", "/var/log/test.log", 1);

    auto result = Config::from_env("test");

    REQUIRE(result.has_value());
    REQUIRE(result->file_path == "/var/log/test.log");

    unsetenv("AGORA_LOG_FILE_PATH");
}

TEST_CASE("Max file size configuration", "[config][filesize]") {
    setenv("AGORA_LOG_MAX_FILE_SIZE_MB", "200", 1);

    auto result = Config::from_env("test");

    REQUIRE(result.has_value());
    REQUIRE(result->max_file_size_mb == 200);

    unsetenv("AGORA_LOG_MAX_FILE_SIZE_MB");
}

TEST_CASE("Max backup count configuration", "[config][backups]") {
    setenv("AGORA_LOG_MAX_BACKUP_COUNT", "10", 1);

    auto result = Config::from_env("test");

    REQUIRE(result.has_value());
    REQUIRE(result->max_backup_count == 10);

    unsetenv("AGORA_LOG_MAX_BACKUP_COUNT");
}
