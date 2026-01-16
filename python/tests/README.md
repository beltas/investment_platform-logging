# Agora Logging Library - Python Tests

Comprehensive test suite for the Python logging library implementation.

## Test Structure

### Core Tests

- **test_logger.py** - Core logger functionality
  - Logger initialization and configuration
  - Log level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Source location capture (file, line, function - REQUIRED)
  - Context inheritance
  - Timer context manager
  - Exception logging

- **test_config.py** - Configuration system
  - Default configuration values
  - Environment variable parsing (from_env)
  - Configuration validation
  - Edge cases and immutability

- **test_source_location.py** - Source location capture
  - _capture_source_location() function
  - Stack depth handling
  - Nested call handling
  - Location accuracy (file, line, function)

- **test_context.py** - Context management
  - Context inheritance and merging
  - with_context() functionality
  - Context isolation
  - Special context keys (correlation_id, user_id, trace_id, span_id)
  - Various data types in context

### Handler Tests

- **test_handlers.py** - Log handlers
  - Console handler (JSON and text format)
  - File handler (basic file writing)
  - Thread-safe concurrent writes
  - Handler interface compliance

- **test_rotation.py** - File rotation
  - Rotation triggers at size threshold
  - Backup file naming (app.log.1, app.log.2, etc.)
  - Max backup count enforcement
  - Thread-safe rotation
  - Startup recovery

- **test_async_handler.py** - Async queue handler
  - Queue bounded size
  - Overflow policies
  - Batch processing
  - Graceful shutdown
  - Performance characteristics

### Formatter Tests

- **test_formatter.py** - JSON formatter
  - JSON output validation
  - Required fields (timestamp, level, message, service, file, line, function)
  - Optional fields (environment, version, host, logger_name)
  - Context serialization
  - Exception formatting
  - Duration formatting
  - Timestamp format (ISO 8601 with microseconds)

### Integration Tests

- **test_integrations_fastapi.py** - FastAPI middleware
  - LoggingMiddleware functionality
  - Correlation ID extraction from X-Correlation-ID header
  - Correlation ID generation
  - Request logger (get_request_logger)
  - Request lifecycle logging
  - Duration measurement

## Running Tests

### Run all tests
```bash
cd /home/beltas/investment_platform-logging/python
pytest
```

### Run specific test file
```bash
pytest tests/test_logger.py
pytest tests/test_rotation.py
```

### Run specific test class
```bash
pytest tests/test_logger.py::TestLoggerInitialization
pytest tests/test_config.py::TestConfigFromEnv
```

### Run specific test
```bash
pytest tests/test_logger.py::TestSourceLocationCapture::test_captures_file_name
```

### Run with coverage
```bash
pytest --cov=agora_log --cov-report=html
# Open htmlcov/index.html in browser
```

### Run with verbose output
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run only fast tests (unit tests)
```bash
pytest -m unit
```

### Run integration tests
```bash
pytest -m integration
```

## Test Categories

Tests are marked with pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no I/O
- `@pytest.mark.integration` - Integration tests with I/O
- `@pytest.mark.slow` - Tests that take > 1 second
- `@pytest.mark.asyncio` - Tests using asyncio

## Coverage Goals

Target: **>80% code coverage** on new code

Run coverage report:
```bash
pytest --cov=agora_log --cov-report=term-missing
```

## Key Test Fixtures

Defined in `conftest.py`:

- **temp_log_file** - Temporary log file path
- **config** - Basic test configuration
- **async_config** - Async logging configuration
- **console_config** - Console-only configuration
- **text_console_config** - Text console output configuration
- **reset_logging_state** - Auto-used fixture that resets global state

## Design Requirements Covered

### Source Location Capture (REQUIRED)
- File, line, and function are captured automatically
- Tests verify correct stack depth handling
- Tests verify accuracy of captured location

### Thread Safety
- Concurrent write tests with multiple threads
- Rotation during concurrent writes
- No corruption or lost entries

### Async Logging
- Queue-based async handler
- Bounded queue with overflow handling
- Graceful shutdown and flush

### File Rotation
- Size-based rotation triggers
- Backup file naming and counting
- Thread-safe rotation
- Startup recovery

### Context Management
- Context inheritance
- Special keys (correlation_id, user_id, etc.)
- Context merging and isolation

### Integration
- FastAPI middleware
- Correlation ID propagation
- Request-scoped logging

## TODO / Future Tests

Some test implementations are marked with `pass` placeholders:

1. **Overflow policies** - drop_oldest, drop_newest, block
2. **Metrics/instrumentation** - dropped entry counting, queue depth
3. **Complex rotation scenarios** - Very large files, many backups
4. **Performance benchmarks** - < 10 microseconds per log entry (async)
5. **WebSocket handling** - FastAPI middleware with WebSockets

## Dependencies

Required:
- pytest >= 7.0
- python >= 3.11

Optional:
- pytest-cov - For coverage reports
- pytest-asyncio - For async tests
- fastapi - For FastAPI integration tests
- starlette - For FastAPI middleware tests

Install test dependencies:
```bash
pip install -e ".[test]"
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest --cov=agora_log --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests fail with "Logging not initialized"
- The `reset_logging_state` fixture should handle this automatically
- If it persists, ensure fixtures are being used correctly

### Async tests hang
- Check that `shutdown()` is called
- Ensure async handler worker thread stops gracefully

### File permission errors
- Tests use `tmp_path` fixture which creates temporary directories
- No manual cleanup needed

### Captured output empty in tests
- Some handlers may not be implemented yet
- Tests check `if captured.out:` to handle this gracefully

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*.py`, `Test*` classes, `test_*` functions
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
3. **Use fixtures**: Leverage shared fixtures from `conftest.py`
4. **Document test purpose**: Clear docstrings explaining what is tested
5. **Test edge cases**: Not just happy path
6. **Verify cleanup**: Use fixtures for setup/teardown
7. **Check coverage**: Aim for >80% coverage on new code

## References

- Design document: `/home/beltas/investment_platform-logging/docs/DESIGN.md`
- Use cases: `/home/beltas/investment_platform-logging/docs/USE_CASES.md`
- Main implementation: `/home/beltas/investment_platform-logging/python/src/agora_log/`
