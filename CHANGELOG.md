# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository structure
- Documentation framework
- Use cases document
- Design document

## [0.1.0] - TBD

### Added
- Python package `agora-log` with core logging functionality
- C++ library `libagora_log` with thread-safe logging
- JavaScript/TypeScript package `@agora/logger` for Node.js and browser
- JSON structured logging format
- Dual output (console + file)
- Size-based file rotation
- Context injection and inheritance
- FastAPI integration middleware
- Express/NestJS integration middleware
- gRPC context extraction
- Async logging queues (Python/Node.js)
- Compile-time log level filtering (C++)
- Timer utilities for operation duration tracking
- Environment variable configuration
- YAML configuration file support

### Performance
- Python async mode: < 10 microseconds per log entry
- Node.js async mode: < 10 microseconds per log entry
- C++ sync mode: < 2 microseconds per log entry
- File rotation: < 50 milliseconds

[Unreleased]: https://github.com/agora/investment_platform-logging/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/agora/investment_platform-logging/releases/tag/v0.1.0
