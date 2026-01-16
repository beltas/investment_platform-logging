/**
 * @file simple_test.cpp
 * @brief Simple standalone test to verify the library compiles and runs
 */

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>
#include <agora/log/context.hpp>
#include <iostream>
#include <filesystem>

int main() {
    namespace fs = std::filesystem;

    try {
        // Create a test config
        agora::log::Config config;
        config.service_name = "simple-test";
        config.environment = "test";
        config.version = "0.0.1";
        config.level = agora::log::Level::Debug;
        config.console_enabled = true;
        config.console_json = false;  // Use text format for readability
        config.file_enabled = true;

        // Use temp directory for test logs
        fs::path test_dir = fs::temp_directory_path() / "agora_simple_test";
        fs::create_directories(test_dir);
        config.file_path = test_dir / "test.log";
        config.max_file_size_mb = 1;
        config.max_backup_count = 2;

        // Initialize logging
        auto result = agora::log::initialize(config);
        if (!result) {
            std::cerr << "Failed to initialize: " << result.error().message << std::endl;
            return 1;
        }

        std::cout << "\n=== Simple Test Starting ===\n" << std::endl;

        // Get a logger
        auto logger = agora::log::get_logger("test.main");

        // Test basic logging
        logger.info("Application started");
        logger.debug("Debug message", {{"key", "value"}});
        logger.warning("Warning message");

        // Test context
        auto ctx = agora::log::ctx()
            .correlation_id("test-123")
            .user_id("user-456")
            .add("custom", "data")
            .build();

        logger.info("Message with context", ctx);

        // Test child logger
        auto child = logger.with_context({{"request_id", "req-789"}});
        child.info("Child logger message");

        // Test timer
        {
            auto timer = logger.timer("Test operation", {{"operation", "test"}});
            // Simulate some work
            for (volatile int i = 0; i < 1000000; ++i) {}
        }

        // Test exception logging
        try {
            throw std::runtime_error("Test exception");
        } catch (const std::exception& ex) {
            logger.error("Caught exception", ex, {{"location", "main"}});
        }

        // Verify log file was created
        if (fs::exists(config.file_path)) {
            std::cout << "\nLog file created: " << config.file_path << std::endl;
            std::cout << "File size: " << fs::file_size(config.file_path) << " bytes" << std::endl;
        } else {
            std::cerr << "ERROR: Log file not created!" << std::endl;
            return 1;
        }

        // Shutdown
        agora::log::shutdown();

        std::cout << "\n=== Simple Test Passed ===\n" << std::endl;
        return 0;

    } catch (const std::exception& ex) {
        std::cerr << "Test failed with exception: " << ex.what() << std::endl;
        return 1;
    }
}
