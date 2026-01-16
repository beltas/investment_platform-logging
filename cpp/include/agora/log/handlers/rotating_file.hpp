/**
 * @file rotating_file.hpp
 * @brief Rotating file handler with size-based rotation
 */

#pragma once

#include "file.hpp"
#include <cstddef>

namespace agora::log {

/**
 * @brief File handler with automatic size-based rotation.
 *
 * When file exceeds max_size_bytes:
 * - Close current file
 * - Rotate backups: app.log -> app.log.1, app.log.1 -> app.log.2, etc.
 * - Delete oldest backup if exceeds max_backup_count
 * - Open new file
 */
class RotatingFileHandler : public FileHandler {
public:
    RotatingFileHandler(
        const std::filesystem::path& file_path,
        std::size_t max_size_bytes,
        std::size_t max_backup_count
    );

    void write(const LogEntry& entry) override;

    /** Get maximum file size before rotation */
    [[nodiscard]] std::size_t max_size_bytes() const noexcept { return max_size_bytes_; }

    /** Get maximum number of backup files */
    [[nodiscard]] std::size_t max_backup_count() const noexcept { return max_backup_count_; }

    /** Get current file size */
    [[nodiscard]] std::size_t current_size() const noexcept { return current_size_; }

    /** Check if rotation is disabled due to errors */
    [[nodiscard]] bool rotation_disabled() const noexcept { return rotation_disabled_; }

private:
    std::size_t max_size_bytes_;
    std::size_t max_backup_count_;
    std::size_t current_size_ = 0;
    bool rotation_disabled_ = false;  // Disable rotation if filesystem errors occur

    void rotate();
    [[nodiscard]] std::filesystem::path get_backup_path(std::size_t index) const noexcept;
    [[nodiscard]] bool should_rotate(std::size_t entry_size) const noexcept;
};

}  // namespace agora::log
