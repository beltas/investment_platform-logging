/**
 * @file test_formatter.cpp
 * @brief JSON formatter tests
 *
 * Tests cover:
 * - JSON output format validation
 * - Required fields present (timestamp, level, message, service, file, line, function)
 * - Context serialization
 * - Exception formatting
 * - Duration formatting
 */

#include <catch2/catch_test_macros.hpp>

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>

#include <filesystem>
#include <fstream>
#include <thread>
#include <chrono>
#include <nlohmann/json.hpp>

using namespace agora::log;
using json = nlohmann::json;
namespace fs = std::filesystem;

class FormatterTestFixture {
public:
    fs::path test_log_dir;
    fs::path test_log_file;

    void SetUp() {
        test_log_dir = fs::temp_directory_path() / "agora_formatter_tests";
        fs::create_directories(test_log_dir);
        test_log_file = test_log_dir / "formatter.log";
    }

    void TearDown() {
        if (fs::exists(test_log_dir)) {
            fs::remove_all(test_log_dir);
        }
        shutdown();
    }

    json read_first_entry() {
        flush();  // Flush handlers before reading (keeps logging active)
        std::ifstream file(test_log_file);
        std::string line;
        std::getline(file, line);
        return json::parse(line);
    }
};

TEST_CASE("JSON formatter - required fields", "[formatter][json]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test-service";
    config.environment = "test-env";
    config.version = "1.2.3";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.formatter");
    logger.info("Test message");

    shutdown();

    auto entry = fixture.read_first_entry();

    // REQUIRED fields
    REQUIRE(entry.contains("timestamp"));
    REQUIRE(entry.contains("level"));
    REQUIRE(entry.contains("message"));
    REQUIRE(entry.contains("service"));
    REQUIRE(entry.contains("environment"));
    REQUIRE(entry.contains("version"));
    REQUIRE(entry.contains("file"));      // REQUIRED
    REQUIRE(entry.contains("line"));      // REQUIRED
    REQUIRE(entry.contains("function"));  // REQUIRED
    REQUIRE(entry.contains("logger_name"));

    // Verify values
    REQUIRE(entry["level"] == "INFO");
    REQUIRE(entry["message"] == "Test message");
    REQUIRE(entry["service"] == "test-service");
    REQUIRE(entry["environment"] == "test-env");
    REQUIRE(entry["version"] == "1.2.3");

    fixture.TearDown();
}

TEST_CASE("JSON formatter - timestamp format", "[formatter][timestamp]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");
    logger.info("Test");

    shutdown();

    auto entry = fixture.read_first_entry();

    // Timestamp should be ISO 8601 format with microseconds
    std::string timestamp = entry["timestamp"];

    // Basic format check: YYYY-MM-DDTHH:MM:SS.ssssssZ
    REQUIRE(timestamp.length() >= 20);
    REQUIRE(timestamp.find('T') != std::string::npos);
    REQUIRE(timestamp.find('Z') != std::string::npos);

    fixture.TearDown();
}

TEST_CASE("JSON formatter - context serialization", "[formatter][context]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");

    logger.info("Test with context", {
        {"string_val", "hello"},
        {"int_val", std::int64_t{42}},
        {"double_val", 3.14},
        {"bool_val", true}
    });

    shutdown();

    auto entry = fixture.read_first_entry();

    REQUIRE(entry.contains("context"));
    auto context = entry["context"];

    REQUIRE(context["string_val"] == "hello");
    REQUIRE(context["int_val"] == 42);
    REQUIRE(context["double_val"] == 3.14);
    REQUIRE(context["bool_val"] == true);

    fixture.TearDown();
}

TEST_CASE("JSON formatter - exception formatting", "[formatter][exception]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");

    try {
        throw std::logic_error("Test exception");
    } catch (const std::exception& ex) {
        logger.error("Error occurred", ex);
    }

    shutdown();

    auto entry = fixture.read_first_entry();

    REQUIRE(entry.contains("exception"));
    auto exception = entry["exception"];

    REQUIRE(exception.contains("type"));
    REQUIRE(exception.contains("message"));

    REQUIRE(exception["type"] == "std::logic_error");
    REQUIRE(exception["message"] == "Test exception");

    fixture.TearDown();
}

TEST_CASE("JSON formatter - duration formatting", "[formatter][duration]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");

    {
        auto timer = logger.timer("Test operation");
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    shutdown();

    auto entry = fixture.read_first_entry();

    REQUIRE(entry.contains("duration_ms"));
    double duration = entry["duration_ms"];

    // Should be at least 10ms
    REQUIRE(duration >= 10.0);
    REQUIRE(duration < 100.0);

    fixture.TearDown();
}

TEST_CASE("JSON formatter - special characters escaping", "[formatter][escaping]") {
    FormatterTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test");

    logger.info("Message with \"quotes\" and \n newlines", {
        {"key_with_\"quotes\"", "value"},
        {"backslash", "C:\\Path\\To\\File"}
    });

    shutdown();

    // Should be valid JSON
    REQUIRE_NOTHROW(fixture.read_first_entry());

    fixture.TearDown();
}
