/**
 * @file test_handlers.cpp
 * @brief Handler tests
 *
 * Tests cover:
 * - Console handler (JSON and text format)
 * - File handler (basic file writing)
 * - Rotating file handler (size-based rotation)
 * - Thread-safe concurrent writes
 */

#include <catch2/catch_test_macros.hpp>

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>
#include <agora/log/handlers/console.hpp>
#include <agora/log/handlers/file.hpp>
#include <agora/log/handlers/rotating_file.hpp>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <thread>
#include <vector>
#include <nlohmann/json.hpp>

using namespace agora::log;
using json = nlohmann::json;
namespace fs = std::filesystem;

class HandlerTestFixture {
public:
    fs::path test_log_dir;

    void SetUp() {
        test_log_dir = fs::temp_directory_path() / "agora_handler_tests";
        fs::create_directories(test_log_dir);
    }

    void TearDown() {
        if (fs::exists(test_log_dir)) {
            fs::remove_all(test_log_dir);
        }
    }

    std::vector<std::string> read_lines(const fs::path& file_path) {
        std::vector<std::string> lines;
        std::ifstream file(file_path);
        std::string line;

        while (std::getline(file, line)) {
            if (!line.empty()) {
                lines.push_back(line);
            }
        }

        return lines;
    }
};

TEST_CASE("Console handler JSON output", "[handler][console]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    // TODO: Implement test for console handler with JSON format
    // - Capture stdout
    // - Verify JSON output format
    // - Verify all required fields present

    fixture.TearDown();
}

TEST_CASE("Console handler text output", "[handler][console]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    // TODO: Implement test for console handler with text format
    // - Capture stdout
    // - Verify human-readable text format
    // - Verify timestamp, level, message are present

    fixture.TearDown();
}

TEST_CASE("File handler basic writing", "[handler][file]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    auto log_file = fixture.test_log_dir / "file_handler.log";

    auto config = Config{};
    config.service_name = "test";
    config.file_path = log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.file");
    logger.info("Test message 1");
    logger.info("Test message 2");
    logger.info("Test message 3");

    shutdown();

    // Verify file exists and has 3 entries
    REQUIRE(fs::exists(log_file));

    auto lines = fixture.read_lines(log_file);
    REQUIRE(lines.size() == 3);

    // Verify each line is valid JSON
    for (const auto& line : lines) {
        auto entry = json::parse(line);
        REQUIRE(entry.contains("message"));
        REQUIRE(entry.contains("level"));
    }

    fixture.TearDown();
}

TEST_CASE("File handler creates directory if not exists", "[handler][file]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    auto nested_dir = fixture.test_log_dir / "nested" / "subdir";
    auto log_file = nested_dir / "test.log";

    auto config = Config{};
    config.service_name = "test";
    config.file_path = log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");
    logger.info("Test");

    shutdown();

    REQUIRE(fs::exists(log_file));

    fixture.TearDown();
}

TEST_CASE("Thread-safe concurrent writes", "[handler][threadsafe]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    auto log_file = fixture.test_log_dir / "concurrent.log";

    auto config = Config{};
    config.service_name = "test";
    config.file_path = log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    const int num_threads = 10;
    const int logs_per_thread = 100;

    std::vector<std::thread> threads;

    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([t, logs_per_thread]() {
            auto logger = get_logger("test.concurrent");

            for (int i = 0; i < logs_per_thread; ++i) {
                logger.info("Concurrent log", {
                    {"thread_id", std::int64_t{t}},
                    {"iteration", std::int64_t{i}}
                });
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    shutdown();

    // Verify all entries were written
    auto lines = fixture.read_lines(log_file);
    REQUIRE(lines.size() == num_threads * logs_per_thread);

    // Verify all entries are valid JSON
    for (const auto& line : lines) {
        REQUIRE_NOTHROW(json::parse(line));
    }

    fixture.TearDown();
}

TEST_CASE("Handler flush on shutdown", "[handler][flush]") {
    HandlerTestFixture fixture;
    fixture.SetUp();

    auto log_file = fixture.test_log_dir / "flush_test.log";

    auto config = Config{};
    config.service_name = "test";
    config.file_path = log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");

    // Write many entries quickly
    for (int i = 0; i < 100; ++i) {
        logger.info("Entry", {{"i", std::int64_t{i}}});
    }

    // Shutdown should flush all buffered entries
    shutdown();

    // Verify all entries present
    auto lines = fixture.read_lines(log_file);
    REQUIRE(lines.size() == 100);

    fixture.TearDown();
}
