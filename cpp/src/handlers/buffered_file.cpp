/**
 * @file buffered_file.cpp
 * @brief Buffered file handler implementation
 */

#include <agora/log/handlers/buffered_file.hpp>
#include <agora/log/formatter.hpp>
#include <stdexcept>
#include <iostream>
#include <chrono>

namespace agora::log {

BufferedFileHandler::BufferedFileHandler(
    const std::filesystem::path& file_path,
    std::size_t buffer_size,
    std::size_t flush_interval_ms
)
    : file_path_(file_path)
    , buffer_size_(buffer_size)
    , flush_interval_ms_(flush_interval_ms) {

    // Reserve space in buffers
    front_buffer_.reserve(buffer_size / 100);  // Estimate ~100 bytes per entry
    back_buffer_.reserve(buffer_size / 100);

    open_file();

    // Start background flush thread
    flush_thread_ = std::thread(&BufferedFileHandler::flush_thread_func, this);
}

BufferedFileHandler::~BufferedFileHandler() noexcept {
    // Signal thread to stop
    stop_.store(true);
    cv_.notify_all();

    // Wait for thread to finish
    if (flush_thread_.joinable()) {
        flush_thread_.join();
    }

    // Final flush of any remaining entries
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!front_buffer_.empty()) {
            swap_buffers();
            flush_back_buffer();
        }
    } catch (...) {
        // Ignore errors during destruction
    }

    close_file();
}

void BufferedFileHandler::write(const LogEntry& entry) {
    std::string formatted = format_json(entry);
    formatted += '\n';
    std::size_t entry_size = formatted.size();

    std::lock_guard<std::mutex> lock(mutex_);

    // Add to front buffer
    front_buffer_.push_back(std::move(formatted));
    front_buffer_bytes_ += entry_size;
    entries_written_.fetch_add(1, std::memory_order_relaxed);

    // Check if we should trigger a flush
    if (front_buffer_bytes_ >= buffer_size_) {
        flush_requested_.store(true);
        cv_.notify_one();
    }
}

void BufferedFileHandler::flush() noexcept {
    try {
        // Request immediate flush
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!front_buffer_.empty()) {
                flush_requested_.store(true);
                cv_.notify_one();
            }
        }

        // Wait for flush to complete (with timeout)
        auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(1000);
        while (flush_requested_.load() && std::chrono::steady_clock::now() < deadline) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    } catch (...) {
        // Ignore errors during flush
    }
}

void BufferedFileHandler::open_file() {
    // Create parent directories if they don't exist
    if (file_path_.has_parent_path()) {
        std::filesystem::create_directories(file_path_.parent_path());
    }

    file_.open(file_path_, std::ios::app);

    if (!file_.is_open()) {
        throw std::runtime_error("Failed to open log file: " + file_path_.string());
    }
}

void BufferedFileHandler::close_file() noexcept {
    try {
        if (file_.is_open()) {
            file_.flush();
            file_.close();
        }
    } catch (...) {
        // Ignore errors during close
    }
}

void BufferedFileHandler::swap_buffers() {
    // Swap front and back buffers
    std::swap(front_buffer_, back_buffer_);
    front_buffer_bytes_ = 0;
    front_buffer_.clear();
}

void BufferedFileHandler::flush_back_buffer() {
    if (back_buffer_.empty() || !file_.is_open()) {
        return;
    }

    // Write all entries from back buffer to file
    for (const auto& entry : back_buffer_) {
        file_ << entry;
    }
    file_.flush();

    back_buffer_.clear();
}

void BufferedFileHandler::flush_thread_func() {
    using namespace std::chrono;

    while (!stop_.load()) {
        std::unique_lock<std::mutex> lock(mutex_);

        // Wait for flush request or timeout
        cv_.wait_for(lock, milliseconds(flush_interval_ms_), [this] {
            return flush_requested_.load() || stop_.load();
        });

        if (stop_.load() && front_buffer_.empty()) {
            break;
        }

        // Check if there's data to flush
        if (!front_buffer_.empty()) {
            swap_buffers();
            lock.unlock();

            // Write to file (outside of lock)
            try {
                flush_back_buffer();
            } catch (const std::exception& e) {
                std::cerr << "BufferedFileHandler flush error: " << e.what() << std::endl;
            }

            flush_requested_.store(false);
        } else {
            flush_requested_.store(false);
        }
    }
}

}  // namespace agora::log
