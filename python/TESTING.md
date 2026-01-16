# Testing Guide - Agora Logging Library (Python)

Quick reference for running tests on the Python logging library.

## Quick Start

```bash
# Navigate to Python package directory
cd /home/beltas/investment_platform-logging/python

# Install package in development mode with test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=agora_log --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py                        # Shared fixtures
├── test_logger.py                     # Core logger tests (30+ tests)
├── test_config.py                     # Configuration tests (25+ tests)
├── test_source_location.py            # Source capture tests (25+ tests)
├── test_context.py                    # Context management tests (20+ tests)
├── test_handlers.py                   # Handler tests (20+ tests)
├── test_rotation.py                   # File rotation tests (15+ tests)
├── test_async_handler.py              # Async queue tests (25+ tests)
├── test_formatter.py                  # JSON formatter tests (25+ tests)
├── test_integrations_fastapi.py       # FastAPI integration tests (15+ tests)
├── README.md                          # Detailed test documentation
└── TEST_SUMMARY.md                    # Comprehensive summary
```

**Total: ~200 test cases covering all major functionality**

## Common Commands

### Run Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_logger.py

# Specific class
pytest tests/test_logger.py::TestSourceLocationCapture

# Specific test
pytest tests/test_logger.py::TestSourceLocationCapture::test_captures_file_name

# Verbose output
pytest -v

# Extra verbose (show test docstrings)
pytest -vv

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

### Coverage

```bash
# Coverage report in terminal
pytest --cov=agora_log

# Coverage with missing lines
pytest --cov=agora_log --cov-report=term-missing

# HTML coverage report
pytest --cov=agora_log --cov-report=html
# Open htmlcov/index.html in browser

# Coverage for specific module
pytest --cov=agora_log.logger tests/test_logger.py
```

### Test Selection

```bash
# Run unit tests only (fast)
pytest -m unit

# Run integration tests only
pytest -m integration

# Run slow tests only
pytest -m slow

# Exclude slow tests
pytest -m "not slow"

# Run asyncio tests
pytest -m asyncio
```

### Output Control

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Show summary of all test outcomes
pytest -ra

# Quiet mode (less output)
pytest -q

# Show captured log output
pytest --log-cli-level=DEBUG
```

## Test Categories

Tests are organized by markers:

- `@pytest.mark.unit` - Fast unit tests, no I/O
- `@pytest.mark.integration` - Integration tests with I/O
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.asyncio` - Async tests

## Fixtures

Available in `conftest.py`:

- **temp_log_file** - Temporary log file path
- **config** - Basic LogConfig for testing
- **async_config** - LogConfig with async enabled
- **console_config** - LogConfig with console only (JSON)
- **text_console_config** - LogConfig with text console
- **reset_logging_state** - Auto-used, resets global state

## Current Status

### ✅ Test Files Created
- All test files written
- Comprehensive coverage planned
- ~3,400 lines of test code
- ~200 test cases

### ⏳ Pending Implementation
Some tests will fail until handlers are implemented:
- Console handler
- File handler
- Rotating file handler
- Async queue handler

### 🟡 Partial Implementation
- Core logger (basic implementation exists)
- Source location capture (implemented)
- Configuration (implemented)

## Expected Failures

Until handlers are fully implemented, expect:

1. **Handler tests** - Will fail/skip if handlers not implemented
2. **File rotation tests** - Some advanced scenarios stubbed
3. **Async tests** - Some metrics/instrumentation tests stubbed
4. **Integration tests** - Some edge cases stubbed

Tests are designed to fail gracefully with clear messages.

## Debugging Failed Tests

```bash
# Show full diff on assertion failures
pytest --tb=long

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l --tb=short

# Run with print debugging
pytest -s tests/test_logger.py::test_specific_test
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=agora_log --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Coverage Goals

**Target: >80% code coverage on new code**

Check coverage:
```bash
pytest --cov=agora_log --cov-report=term-missing --cov-fail-under=80
```

## Troubleshooting

### "Logging not initialized" errors
- The `reset_logging_state` fixture should handle this
- Ensure you're using fixtures correctly
- Check that `initialize()` is called in test

### Async tests hanging
- Ensure `shutdown()` is called
- Check async handler stops gracefully
- Increase timeout if needed

### File permission errors
- Tests use `tmp_path` fixture automatically
- No manual cleanup needed
- Check pytest has write permissions

### Import errors
- Install package: `pip install -e .`
- Install test deps: `pip install -e ".[dev]"`
- Check Python version (requires 3.11+)

### Captured output empty
- Some handlers may not be implemented yet
- Tests check `if captured.out:` to handle gracefully
- Use `-s` flag to see print statements

## Performance Testing

Async logging performance target: **< 10 microseconds per log entry**

Run performance tests:
```bash
pytest tests/test_async_handler.py::TestAsyncPerformance -v
```

## Writing New Tests

When adding tests:

1. **Follow naming**: `test_*.py`, `class Test*`, `def test_*()`
2. **Use docstrings**: Explain what the test does
3. **Use fixtures**: Leverage shared setup
4. **Add markers**: `@pytest.mark.unit` or `@pytest.mark.integration`
5. **Test edge cases**: Not just happy path
6. **Verify cleanup**: Use fixtures for teardown

Example:
```python
import pytest
from agora_log import initialize, LogConfig

class TestMyFeature:
    """Tests for my new feature."""

    def test_basic_functionality(self, config: LogConfig):
        """Test that basic feature works."""
        logger = initialize(config)
        # Your test here
        assert True

    @pytest.mark.integration
    def test_integration_scenario(self, temp_log_file):
        """Test integration with file system."""
        # Integration test here
        pass
```

## Resources

- **Test README**: `tests/README.md` - Detailed documentation
- **Test Summary**: `tests/TEST_SUMMARY.md` - Statistics and coverage
- **Design Doc**: `../docs/DESIGN.md` - Implementation specifications
- **Use Cases**: `../docs/USE_CASES.md` - Usage examples
- **pytest docs**: https://docs.pytest.org/

## Support

For questions or issues:
1. Check `tests/README.md` for detailed documentation
2. Review `TEST_SUMMARY.md` for coverage mapping
3. Check design documents for requirements
4. Review use cases for examples

## Next Steps

1. **Implement handlers**: Console, File, Rotating, Async
2. **Run tests**: `pytest -v`
3. **Fix failures**: Implement missing functionality
4. **Check coverage**: `pytest --cov`
5. **Complete stubs**: Overflow policies, metrics
6. **Performance benchmark**: Verify < 10μs target
