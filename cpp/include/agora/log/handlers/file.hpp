/**
 * @file file.hpp
 * @brief File output handler
 */

#pragma once

#include "handler.hpp"
#include <filesystem>
#include <fstream>
#include <mutex>

namespace agora::log {

/**
 * @brief File handler that writes JSON logs to a file.
 */
class FileHandler : public Handler {
public:
    explicit FileHandler(const std::filesystem::path& file_path);
    ~FileHandler() noexcept override;

    void write(const LogEntry& entry) override;
    void flush() noexcept override;

    /** Get the file path */
    [[nodiscard]] const std::filesystem::path& path() const noexcept { return file_path_; }

protected:
    std::filesystem::path file_path_;
    std::ofstream file_;
    std::mutex mutex_;

    void open_file();
    void close_file() noexcept;
};

}  // namespace agora::log
