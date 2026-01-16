/**
 * @file buffered_file.hpp
 * @brief Buffered file handler with double buffering for high-throughput logging
 */

#pragma once

#include "handler.hpp"
#include <filesystem>
#include <fstream>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <atomic>
#include <vector>
#include <string>

namespace agora::log {

/**
 * @brief High-performance file handler with double buffering.
 *
 * Uses two buffers to minimize write latency:
 * - Front buffer: Accumulates log entries from application threads
 * - Back buffer: Being flushed to disk by background thread
 *
 * When front buffer reaches threshold, buffers are swapped and
 * the background thread writes the back buffer to disk.
 *
 * This design allows application threads to continue logging
 * while disk I/O is in progress.
 */
class BufferedFileHandler : public Handler {
public:
    /**
     * @brief Construct a buffered file handler.
     *
     * @param file_path Path to the log file
     * @param buffer_size Size of each buffer in bytes (default: 64KB)
     * @param flush_interval_ms Maximum time before flushing (default: 100ms)
     */
    BufferedFileHandler(
        const std::filesystem::path& file_path,
        std::size_t buffer_size = 64 * 1024,
        std::size_t flush_interval_ms = 100
    );

    ~BufferedFileHandler() noexcept override;

    void write(const LogEntry& entry) override;
    void flush() noexcept override;

    /** Get the file path */
    [[nodiscard]] const std::filesystem::path& path() const noexcept { return file_path_; }

    /** Get buffer size */
    [[nodiscard]] std::size_t buffer_size() const noexcept { return buffer_size_; }

    /** Get number of entries written */
    [[nodiscard]] std::size_t entries_written() const noexcept { return entries_written_.load(); }

private:
    std::filesystem::path file_path_;
    std::ofstream file_;
    std::size_t buffer_size_;
    std::size_t flush_interval_ms_;

    // Double buffer
    std::vector<std::string> front_buffer_;
    std::vector<std::string> back_buffer_;
    std::size_t front_buffer_bytes_ = 0;

    // Synchronization
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic<bool> stop_{false};
    std::atomic<bool> flush_requested_{false};
    std::atomic<std::size_t> entries_written_{0};

    // Background flush thread
    std::thread flush_thread_;

    void open_file();
    void close_file() noexcept;
    void swap_buffers();
    void flush_back_buffer();
    void flush_thread_func();
};

}  // namespace agora::log
