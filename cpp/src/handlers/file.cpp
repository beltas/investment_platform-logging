/**
 * @file file.cpp
 * @brief File handler implementation
 */

#include <agora/log/handlers/file.hpp>
#include <agora/log/formatter.hpp>
#include <stdexcept>

namespace agora::log {

FileHandler::FileHandler(const std::filesystem::path& file_path)
    : file_path_(file_path) {
    open_file();
}

FileHandler::~FileHandler() noexcept {
    close_file();
}

void FileHandler::write(const LogEntry& entry) {
    std::string formatted = format_json(entry);

    std::lock_guard<std::mutex> lock(mutex_);

    if (!file_.is_open()) {
        open_file();
    }

    file_ << formatted << '\n';
}

void FileHandler::flush() noexcept {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (file_.is_open()) {
            file_.flush();
        }
    } catch (...) {
        // Ignore errors during flush - noexcept guarantee
    }
}

void FileHandler::open_file() {
    // Create parent directories if they don't exist
    if (file_path_.has_parent_path()) {
        std::filesystem::create_directories(file_path_.parent_path());
    }

    file_.open(file_path_, std::ios::app);

    if (!file_.is_open()) {
        throw std::runtime_error("Failed to open log file: " + file_path_.string());
    }
}

void FileHandler::close_file() noexcept {
    try {
        if (file_.is_open()) {
            file_.flush();
            file_.close();
        }
    } catch (...) {
        // Ignore errors during close - noexcept guarantee
    }
}

}  // namespace agora::log
