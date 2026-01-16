/**
 * @file rotating_file.cpp
 * @brief Rotating file handler implementation
 */

#include <agora/log/handlers/rotating_file.hpp>
#include <agora/log/formatter.hpp>
#include <filesystem>
#include <iostream>

namespace agora::log {

namespace fs = std::filesystem;

RotatingFileHandler::RotatingFileHandler(
    const fs::path& file_path,
    std::size_t max_size_bytes,
    std::size_t max_backup_count
)
    : FileHandler(file_path)
    , max_size_bytes_(max_size_bytes)
    , max_backup_count_(max_backup_count) {

    // Get current file size if it exists
    if (fs::exists(file_path_)) {
        current_size_ = fs::file_size(file_path_);
    }
}

void RotatingFileHandler::write(const LogEntry& entry) {
    std::string formatted = format_json(entry);
    std::size_t entry_size = formatted.size() + 1;  // +1 for newline

    std::lock_guard<std::mutex> lock(mutex_);

    // Check if rotation is needed
    if (should_rotate(entry_size)) {
        rotate();
    }

    // Write entry
    if (!file_.is_open()) {
        open_file();
    }

    file_ << formatted << '\n';
    current_size_ += entry_size;
}

bool RotatingFileHandler::should_rotate(std::size_t entry_size) const noexcept {
    // Don't rotate if rotation has been disabled due to previous errors
    if (rotation_disabled_) {
        return false;
    }
    return current_size_ + entry_size > max_size_bytes_;
}

void RotatingFileHandler::rotate() {
    try {
        // Close current file
        close_file();

        // Delete oldest backup if it exists
        auto oldest = get_backup_path(max_backup_count_);
        if (fs::exists(oldest)) {
            fs::remove(oldest);
        }

        // Rotate existing backups
        for (std::size_t i = max_backup_count_; i > 1; --i) {
            auto src = get_backup_path(i - 1);
            auto dst = get_backup_path(i);

            if (fs::exists(src)) {
                fs::rename(src, dst);
            }
        }

        // Move current file to .1
        if (fs::exists(file_path_)) {
            fs::rename(file_path_, get_backup_path(1));
        }

        // Reset size counter
        current_size_ = 0;

        // Open new file
        open_file();

    } catch (const fs::filesystem_error& e) {
        // Log to stderr - logging should never crash the application
        std::cerr << "Log file rotation failed: " << e.what() << std::endl;

        // Try to reopen the original file to continue logging
        try {
            open_file();
            // If we get here, we can at least continue logging to the file
            // even if rotation failed
        } catch (...) {
            // If reopening fails too, disable rotation to prevent repeated failures
            // but file writes will still be attempted in write()
            std::cerr << "Failed to reopen log file after rotation failure. "
                      << "Disabling file rotation." << std::endl;
            rotation_disabled_ = true;
        }
    }
}

fs::path RotatingFileHandler::get_backup_path(std::size_t index) const noexcept {
    try {
        return fs::path(file_path_.string() + "." + std::to_string(index));
    } catch (...) {
        return file_path_;  // Fallback if string operations fail
    }
}

}  // namespace agora::log
