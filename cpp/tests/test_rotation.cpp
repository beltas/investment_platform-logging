/**
 * @file test_rotation.cpp
 * @brief File rotation tests
 *
 * Tests cover:
 * - Rotation triggers at size threshold
 * - Backup file naming (app.log.1, app.log.2, etc.)
 * - Max backup count enforcement (oldest deleted)
 * - Thread-safe rotation during concurrent writes
 */

#include <catch2/catch_test_macros.hpp>

#include <agora/log/logger.hpp>
#include <agora/log/config.hpp>

#include <filesystem>
#include <fstream>
#include <thread>
#include <vector>

using namespace agora::log;
namespace fs = std::filesystem;

class RotationTestFixture {
public:
    fs::path test_log_dir;
    fs::path test_log_file;

    void SetUp() {
        test_log_dir = fs::temp_directory_path() / "agora_rotation_tests";
        // Clean up any existing files from previous runs
        if (fs::exists(test_log_dir)) {
            fs::remove_all(test_log_dir);
        }
        fs::create_directories(test_log_dir);
        test_log_file = test_log_dir / "rotation.log";
    }

    void TearDown() {
        if (fs::exists(test_log_dir)) {
            fs::remove_all(test_log_dir);
        }
        shutdown();
    }

    std::size_t count_lines(const fs::path& file_path) {
        if (!fs::exists(file_path)) {
            return 0;
        }

        std::ifstream file(file_path);
        std::size_t count = 0;
        std::string line;

        while (std::getline(file, line)) {
            if (!line.empty()) {
                ++count;
            }
        }

        return count;
    }

    std::vector<fs::path> get_log_files() {
        flush();  // Flush handlers before reading (keeps logging active)
        std::vector<fs::path> files;

        if (fs::exists(test_log_file)) {
            files.push_back(test_log_file);
        }

        // Check for backups: rotation.log.1, rotation.log.2, etc.
        // Check up to 250 to support tests with many small files
        for (int i = 1; i <= 250; ++i) {
            auto backup = fs::path(test_log_file.string() + "." + std::to_string(i));
            if (fs::exists(backup)) {
                files.push_back(backup);
            }
        }

        return files;
    }
};

TEST_CASE("Rotation triggers at size threshold", "[rotation][size]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    // Configure small file size for testing (1 KB)
    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 0.001;  // ~1 KB
    config.max_backup_count = 3;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.rotation");

    // Write many log entries to trigger rotation
    // Each entry is ~500 bytes
    for (int i = 0; i < 100; ++i) {
        logger.info("Log entry with some substantial content to increase file size", {
            {"iteration", std::int64_t{i}},
            {"data", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
            {"more_data", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"}
        });
    }

    shutdown();

    // Should have rotated multiple times
    auto files = fixture.get_log_files();
    REQUIRE(files.size() > 1);  // At least main file + 1 backup

    // Verify backup naming
    REQUIRE(fs::exists(fixture.test_log_file));
    REQUIRE(fs::exists(fs::path(fixture.test_log_file.string() + ".1")));

    fixture.TearDown();
}

TEST_CASE("Max backup count enforcement", "[rotation][backups]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 0.001;  // ~1 KB
    config.max_backup_count = 3;  // Keep max 3 backups
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.backups");

    // Write many entries to trigger multiple rotations
    for (int i = 0; i < 200; ++i) {
        logger.info("Rotation test entry with substantial content for size", {
            {"iteration", std::int64_t{i}},
            {"padding_1", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"},
            {"padding_2", "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"}
        });
    }

    shutdown();

    auto files = fixture.get_log_files();

    // Should have main file + max 3 backups = 4 total
    REQUIRE(files.size() <= 4);

    // Verify backup numbering
    REQUIRE(fs::exists(fixture.test_log_file));

    // Should have .1, .2, .3, but not .4 or higher
    REQUIRE(fs::exists(fs::path(fixture.test_log_file.string() + ".1")));

    auto backup_4 = fs::path(fixture.test_log_file.string() + ".4");
    REQUIRE_FALSE(fs::exists(backup_4));

    fixture.TearDown();
}

TEST_CASE("Backup file rotation order", "[rotation][order]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    // Manually create backup files
    auto backup_1 = fs::path(fixture.test_log_file.string() + ".1");
    auto backup_2 = fs::path(fixture.test_log_file.string() + ".2");
    auto backup_3 = fs::path(fixture.test_log_file.string() + ".3");

    std::ofstream(backup_1) << "backup 1\n";
    std::ofstream(backup_2) << "backup 2\n";
    std::ofstream(backup_3) << "backup 3\n";

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 0.001;  // ~1 KB
    config.max_backup_count = 3;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.order");

    // Write enough to trigger one rotation
    for (int i = 0; i < 50; ++i) {
        logger.info("Entry to trigger rotation", {
            {"iteration", std::int64_t{i}},
            {"padding", "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"}
        });
    }

    shutdown();

    // After rotation:
    // - backup 3 should be deleted (oldest)
    // - backup 2 -> backup 3
    // - backup 1 -> backup 2
    // - current -> backup 1
    // - new current file created

    REQUIRE(fs::exists(backup_1));
    REQUIRE(fs::exists(backup_2));
    REQUIRE(fs::exists(backup_3));

    fixture.TearDown();
}

TEST_CASE("Thread-safe rotation during concurrent writes", "[rotation][threadsafe]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 0.050;  // 50 KB per file to reduce rotation frequency
    config.max_backup_count = 20;     // Allow enough backups to retain all entries
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    const int num_threads = 4;
    const int logs_per_thread = 50;

    std::vector<std::thread> threads;

    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([t, logs_per_thread]() {
            auto logger = get_logger("test.concurrent_rotation");

            for (int i = 0; i < logs_per_thread; ++i) {
                logger.info("Concurrent rotation test entry", {
                    {"thread_id", std::int64_t{t}},
                    {"iteration", std::int64_t{i}},
                    {"data_1", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
                    {"data_2", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"}
                });
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    shutdown();

    // Count total entries across all files
    auto files = fixture.get_log_files();
    std::size_t total_entries = 0;

    for (const auto& file : files) {
        total_entries += fixture.count_lines(file);
    }

    // Should have all entries (no lost writes during rotation)
    REQUIRE(total_entries == num_threads * logs_per_thread);

    fixture.TearDown();
}

TEST_CASE("Rotation preserves log integrity", "[rotation][integrity]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 0.010;  // 10 KB per file
    config.max_backup_count = 20;     // Allow enough backups to retain all entries
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.integrity");

    // Write sequentially numbered entries
    for (int i = 0; i < 100; ++i) {
        logger.info("Sequential entry", {
            {"sequence", std::int64_t{i}},
            {"padding", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}
        });
    }

    shutdown();

    // Verify all entries present across all files
    auto files = fixture.get_log_files();
    std::size_t total = 0;

    for (const auto& file : files) {
        total += fixture.count_lines(file);
    }

    REQUIRE(total == 100);

    fixture.TearDown();
}

TEST_CASE("Startup with existing log file", "[rotation][startup]") {
    RotationTestFixture fixture;
    fixture.SetUp();

    // Create existing log file with content
    {
        std::ofstream file(fixture.test_log_file);
        for (int i = 0; i < 10; ++i) {
            file << "Existing entry " << i << "\n";
        }
    }

    auto existing_size = fs::file_size(fixture.test_log_file);
    REQUIRE(existing_size > 0);

    auto config = Config{};
    config.service_name = "test";
    config.file_path = fixture.test_log_file;
    config.max_file_size_mb = 10;
    config.console_enabled = false;

    auto result = initialize(config);
    REQUIRE(result.has_value());

    auto logger = get_logger("test.startup");
    logger.info("New entry");

    shutdown();

    // Should append to existing file
    auto new_size = fs::file_size(fixture.test_log_file);
    REQUIRE(new_size > existing_size);

    fixture.TearDown();
}
