/**
 * @file test_logger.cpp
 * @brief Core logger tests
 *
 * Tests cover:
 * - Logger initialization and configuration
 * - Log level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
 * - Source location capture (file, line, function - REQUIRED fields)
 * - Context inheritance (parent → child loggers)
 * - with_context() creates new logger with merged context
 * - Timer functionality (RAII duration logging)
 */

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>
#include <agora/log/context.hpp>

#include <filesystem>
#include <fstream>
#include <thread>
#include <chrono>
#include <nlohmann/json.hpp>

using namespace agora::log;
using json = nlohmann::json;
namespace fs = std::filesystem;

// Test helper to read and parse JSON log file
std::vector<json> read_json_logs(const fs::path& log_file) {
    std::vector<json> entries;
    std::ifstream file(log_file);
    std::string line;

    while (std::getline(file, line)) {
        if (!line.empty()) {
            entries.push_back(json::parse(line));
        }
    }

    return entries;
}

// Test fixture for logger tests
class LoggerTestFixture {
public:
    fs::path test_log_dir;
    fs::path test_log_file;

    void SetUp() {
        test_log_dir = fs::temp_directory_path() / "agora_log_tests";
        fs::create_directories(test_log_dir);
        test_log_file = test_log_dir / "test.log";

        // Clean up any existing log files
        if (fs::exists(test_log_file)) {
            fs::remove(test_log_file);
        }
    }

    void TearDown() {
        // Clean up test files
        if (fs::exists(test_log_dir)) {
            fs::remove_all(test_log_dir);
        }
        shutdown();
    }

    Config create_test_config() {
        Config config;
        config.service_name = "test-service";
        config.environment = "test";
        config.version = "1.0.0";
        config.level = Level::Debug;
        config.console_enabled = false;  // Disable console for tests
        config.file_enabled = true;
        config.file_path = test_log_file;
        config.max_file_size_mb = 10;
        config.max_backup_count = 3;
        return config;
    }

    // Flush handlers and read log entries (keeps logging active)
    std::vector<json> flush_and_read_logs() {
        flush();  // This flushes all handlers without shutting down
        return read_json_logs(test_log_file);
    }
};

TEST_CASE("Logger initialization", "[logger][init]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    SECTION("Initialize with valid config") {
        auto config = fixture.create_test_config();
        auto result = initialize(config);

        REQUIRE(result.has_value());

        auto logger = get_logger("test.component");
        logger.info("Test message");

        // Verify log file was created
        REQUIRE(fs::exists(fixture.test_log_file));
    }

    SECTION("Initialize with invalid file path") {
        auto config = fixture.create_test_config();
        config.file_path = "/invalid/path/that/does/not/exist/test.log";

        auto result = initialize(config);

        // Should fail with error
        REQUIRE_FALSE(result.has_value());
        REQUIRE(!result.error().message.empty());
    }

    fixture.TearDown();
}

TEST_CASE("Log level filtering", "[logger][levels]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    config.level = Level::Warning;  // Only WARNING and above

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.levels");

    // These should not be logged
    logger.debug("Debug message");
    logger.info("Info message");

    // These should be logged
    logger.warning("Warning message");
    logger.error("Error message");
    logger.critical("Critical message");

    auto entries = fixture.flush_and_read_logs();

    REQUIRE(entries.size() == 3);
    REQUIRE(entries[0]["level"] == "WARNING");
    REQUIRE(entries[0]["message"] == "Warning message");
    REQUIRE(entries[1]["level"] == "ERROR");
    REQUIRE(entries[1]["message"] == "Error message");
    REQUIRE(entries[2]["level"] == "CRITICAL");
    REQUIRE(entries[2]["message"] == "Critical message");

    fixture.TearDown();
}

TEST_CASE("Source location capture", "[logger][source]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.source");

    // Log from this exact line
    const int log_line = __LINE__ + 1;
    logger.info("Test source location");

    auto entries = fixture.flush_and_read_logs();

    REQUIRE(entries.size() == 1);

    // REQUIRED fields must be present
    REQUIRE(entries[0].contains("file"));
    REQUIRE(entries[0].contains("line"));
    REQUIRE(entries[0].contains("function"));

    // File should be just the filename, not full path
    std::string file = entries[0]["file"];
    REQUIRE(file == "test_logger.cpp");

    // Line number should match
    int line = entries[0]["line"];
    REQUIRE(line == log_line);

    // Function name should be present
    std::string function = entries[0]["function"];
    REQUIRE(!function.empty());

    fixture.TearDown();
}

TEST_CASE("Context injection", "[logger][context]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.context");

    SECTION("Basic context") {
        logger.info("Test message", {
            {"user_id", "user-123"},
            {"request_id", "req-456"},
            {"count", std::int64_t{42}},
            {"price", 99.99},
            {"active", true}
        });

        auto entries = fixture.flush_and_read_logs();
        REQUIRE(entries.size() == 1);

        auto context = entries[0]["context"];
        REQUIRE(context["user_id"] == "user-123");
        REQUIRE(context["request_id"] == "req-456");
        REQUIRE(context["count"] == 42);
        REQUIRE(context["price"] == 99.99);
        REQUIRE(context["active"] == true);
    }

    SECTION("Context builder") {
        auto ctx = agora::log::ctx()
            .correlation_id("corr-789")
            .user_id("user-456")
            .trace_id("trace-abc")
            .span_id("span-def")
            .add("custom_field", "custom_value")
            .build();

        logger.info("Test with builder", ctx);

        auto entries = fixture.flush_and_read_logs();
        REQUIRE(entries.size() == 1);

        auto context = entries[0]["context"];
        REQUIRE(context["correlation_id"] == "corr-789");
        REQUIRE(context["user_id"] == "user-456");
        REQUIRE(context["trace_id"] == "trace-abc");
        REQUIRE(context["span_id"] == "span-def");
        REQUIRE(context["custom_field"] == "custom_value");
    }

    fixture.TearDown();
}

TEST_CASE("Context inheritance with with_context()", "[logger][inheritance]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto parent_logger = get_logger("test.parent");

    // Create child logger with additional context
    auto child_logger = parent_logger.with_context({
        {"request_id", "req-123"},
        {"user_id", "user-456"}
    });

    // Child logger inherits parent context and adds new fields
    child_logger.info("Child log message", {
        {"action", "create"}
    });

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == 1);

    auto context = entries[0]["context"];

    // Child context should include both inherited and new fields
    REQUIRE(context["request_id"] == "req-123");
    REQUIRE(context["user_id"] == "user-456");
    REQUIRE(context["action"] == "create");

    SECTION("Nested child loggers") {
        auto grandchild = child_logger.with_context({
            {"operation", "update"}
        });

        grandchild.info("Grandchild log message");

        auto all_entries = fixture.flush_and_read_logs();
        REQUIRE(all_entries.size() == 2);

        auto grandchild_context = all_entries[1]["context"];

        // Should have all inherited context
        REQUIRE(grandchild_context["request_id"] == "req-123");
        REQUIRE(grandchild_context["user_id"] == "user-456");
        REQUIRE(grandchild_context["operation"] == "update");
    }

    fixture.TearDown();
}

TEST_CASE("Exception logging", "[logger][exception]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.exception");

    try {
        throw std::runtime_error("Test exception message");
    } catch (const std::exception& ex) {
        logger.error("Operation failed", ex, {
            {"operation", "test_operation"}
        });
    }

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == 1);

    REQUIRE(entries[0]["level"] == "ERROR");
    REQUIRE(entries[0]["message"] == "Operation failed");

    // Exception should be captured
    REQUIRE(entries[0].contains("exception"));
    auto exception = entries[0]["exception"];
    REQUIRE(exception["type"] == "std::runtime_error");
    REQUIRE(exception["message"] == "Test exception message");

    fixture.TearDown();
}

TEST_CASE("Timer functionality", "[logger][timer]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.timer");

    SECTION("RAII timer logs duration on destruction") {
        {
            auto timer = logger.timer("Database query", {
                {"table", "users"}
            });

            // Simulate some work
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }  // Timer destructor logs duration

        auto entries = fixture.flush_and_read_logs();
        REQUIRE(entries.size() == 1);

        REQUIRE(entries[0]["message"] == "Database query");
        REQUIRE(entries[0].contains("duration_ms"));

        double duration = entries[0]["duration_ms"];
        REQUIRE(duration >= 50.0);  // At least 50ms
        REQUIRE(duration < 200.0);  // But not too much more

        auto context = entries[0]["context"];
        REQUIRE(context["table"] == "users");
    }

    SECTION("Cancelled timer does not log") {
        {
            auto timer = logger.timer("Operation that fails");
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            timer.cancel();  // Cancel the timer
        }

        auto entries = fixture.flush_and_read_logs();
        REQUIRE(entries.size() == 0);  // No log entry
    }

    SECTION("Timer with move semantics") {
        auto create_timer = [&logger]() {
            return logger.timer("Moved timer");
        };

        {
            auto timer = create_timer();  // Move constructor
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }

        auto entries = fixture.flush_and_read_logs();
        REQUIRE(entries.size() == 1);
        REQUIRE(entries[0]["message"] == "Moved timer");
        REQUIRE(entries[0].contains("duration_ms"));
    }

    fixture.TearDown();
}

TEST_CASE("Required fields in all log entries", "[logger][required]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.required");

    logger.info("Test message");

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == 1);

    auto& entry = entries[0];

    // REQUIRED fields per specification
    REQUIRE(entry.contains("timestamp"));
    REQUIRE(entry.contains("level"));
    REQUIRE(entry.contains("message"));
    REQUIRE(entry.contains("service"));
    REQUIRE(entry.contains("file"));      // REQUIRED
    REQUIRE(entry.contains("line"));      // REQUIRED
    REQUIRE(entry.contains("function"));  // REQUIRED

    // Verify types
    REQUIRE(entry["level"] == "INFO");
    REQUIRE(entry["message"] == "Test message");
    REQUIRE(entry["service"] == "test-service");
    REQUIRE(entry["file"].is_string());
    REQUIRE(entry["line"].is_number());
    REQUIRE(entry["function"].is_string());

    fixture.TearDown();
}

TEST_CASE("Multiple loggers with different names", "[logger][multiple]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger1 = get_logger("service.component1");
    auto logger2 = get_logger("service.component2");

    logger1.info("From component 1");
    logger2.info("From component 2");

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == 2);

    REQUIRE(entries[0]["logger_name"] == "service.component1");
    REQUIRE(entries[1]["logger_name"] == "service.component2");

    fixture.TearDown();
}

TEST_CASE("Log all severity levels", "[logger][severity]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    config.level = Level::Debug;  // Allow all levels
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.severity");

    logger.debug("Debug message");
    logger.info("Info message");
    logger.warning("Warning message");
    logger.error("Error message");
    logger.critical("Critical message");

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == 5);

    REQUIRE(entries[0]["level"] == "DEBUG");
    REQUIRE(entries[1]["level"] == "INFO");
    REQUIRE(entries[2]["level"] == "WARNING");
    REQUIRE(entries[3]["level"] == "ERROR");
    REQUIRE(entries[4]["level"] == "CRITICAL");

    fixture.TearDown();
}

TEST_CASE("Performance - logging overhead", "[logger][performance]") {
    LoggerTestFixture fixture;
    fixture.SetUp();

    auto config = fixture.create_test_config();
    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.performance");

    const int num_logs = 1000;
    auto start = std::chrono::steady_clock::now();

    for (int i = 0; i < num_logs; ++i) {
        logger.info("Performance test message", {
            {"iteration", std::int64_t{i}}
        });
    }

    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    double avg_per_log = static_cast<double>(duration.count()) / num_logs;

    // Performance target: < 2 microseconds per log entry (from design doc)
    // We'll be more lenient in tests since file I/O can vary
    REQUIRE(avg_per_log < 100.0);  // 100 microseconds average

    auto entries = fixture.flush_and_read_logs();
    REQUIRE(entries.size() == num_logs);

    fixture.TearDown();
}
