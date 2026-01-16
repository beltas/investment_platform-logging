# JavaScript/TypeScript Logging Library Tests

Comprehensive test suite for the Agora Trading Platform logging library (JavaScript/TypeScript implementation).

## Test Coverage

### Core Logger Tests (`logger.test.ts`)

Tests the main Logger class functionality:

- **Initialization**
  - Logger initialization with configuration
  - Singleton logger instances per name
  - Error handling for uninitialized logger

- **Log Level Filtering**
  - DEBUG, INFO, WARNING, ERROR, CRITICAL levels
  - Level threshold enforcement
  - Level comparison logic

- **Source Location Capture** (REQUIRED)
  - Automatic capture of file, line, function
  - Function name extraction
  - Anonymous function handling
  - Source location from timer calls

- **Context Inheritance**
  - Parent to child context propagation
  - Context merging
  - Context override behavior

- **withContext() Method**
  - Creates new logger instance
  - Preserves parent context
  - Supports multiple nesting levels

- **Timer Functionality**
  - Duration logging on success
  - Duration logging on error
  - Error propagation
  - Additional context in timer logs
  - Return value preservation

- **Required Fields Validation**
  - All required fields present in log entries
  - ISO 8601 timestamp format
  - Proper field types

- **Exception Logging**
  - Error details in exception field
  - Custom error type handling
  - Stack trace inclusion

- **Custom Context**
  - Multiple context values
  - Context merging with inline values
  - Support for various data types

### Configuration Tests (`config.test.ts`)

Tests configuration loading and validation:

- **Environment Variable Parsing**
  - Service name
  - Environment (development/staging/production)
  - Version
  - Log level (case-insensitive)

- **Console Configuration**
  - Enable/disable console output
  - Format selection (JSON/text)
  - Color configuration

- **File Configuration**
  - Enable/disable file logging
  - File path handling
  - Max file size
  - Max backup count

- **Default Values**
  - All configuration options have sensible defaults
  - Type-safe configuration structure

### Source Location Tests (`source-location.test.ts`)

Tests automatic source location capture (REQUIRED feature):

- **Stack Trace Parsing**
  - V8 stack format parsing
  - File name extraction (filename only, not full path)
  - Line number extraction
  - Function name extraction

- **Function Name Handling**
  - Named functions
  - Anonymous functions
  - Arrow functions
  - Class methods
  - Async functions

- **Stack Depth**
  - Correct stack frame navigation
  - Nested function calls
  - Configurable depth parameter

- **Edge Cases**
  - Missing stack traces
  - Very deep call stacks
  - Qualified names (Class.method)

### Formatter Tests (`formatter.test.ts`)

Tests JSON log entry formatting:

- **Required Fields**
  - Timestamp, level, message, service
  - Source location (file, line, function)
  - Environment, version, host

- **Optional Fields**
  - correlationId, userId, traceId, spanId
  - Context object
  - Duration measurements
  - Exception details

- **Data Type Handling**
  - String, number, boolean values
  - Nested objects
  - Arrays
  - Null values

- **JSON Structure**
  - Valid JSON output
  - Parseable by standard JSON parsers
  - Proper escaping and encoding

### Express Integration Tests (`express.test.ts`)

Tests Express middleware integration:

- **Correlation ID Handling**
  - Extraction from X-Correlation-ID header
  - Case-insensitive header matching
  - Automatic generation when missing
  - Unique IDs per request

- **Response Headers**
  - X-Correlation-ID added to response
  - Generated ID propagation

- **Request Logging**
  - Request start logging
  - Request method and path in context
  - Request completion logging
  - Status code logging
  - Duration measurement

- **Async Context Propagation**
  - getRequestLogger() returns scoped logger
  - Context maintained through async operations
  - Fallback to base logger outside request

- **Error Handling**
  - Missing request properties
  - Missing response methods
  - Graceful degradation

### Handler Tests (`handlers.test.ts`)

Tests logging output handlers:

- **Console Handler**
  - JSON format output
  - Text format output
  - Write queue ordering
  - All entry fields included

- **File Handler** (TODO - requires implementation)
  - Basic file writing
  - File creation and appending
  - Write errors and fallback
  - Path handling

- **Rotating File Handler** (TODO - requires implementation)
  - Size-based rotation
  - Backup management
  - Atomic rotation process

- **Handler Interface**
  - emit(), flush(), close() methods
  - Multiple handler support
  - Independent error handling

### Rotation Tests (`rotation.test.ts`)

Tests file rotation logic (TODO - requires RotatingFileHandler implementation):

- **Rotation Triggers**
  - Size threshold detection
  - Pre-write size checks

- **Backup Naming**
  - Sequential numbering (.1, .2, .3, ...)
  - Max backup count enforcement
  - Oldest backup deletion

- **Async Handling**
  - Write queuing during rotation
  - No lost entries
  - Concurrent write safety

- **Error Scenarios**
  - File rename errors
  - Permission errors
  - Disk full conditions

- **Startup Recovery**
  - Existing file detection
  - Append mode
  - Backup preservation

## Running Tests

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm run test:watch
```

### Run Tests with Coverage

```bash
npm run test:coverage
```

### Run Specific Test File

```bash
npm test logger.test.ts
```

### Run Tests Matching Pattern

```bash
npm test -- --grep "source location"
```

## Test Requirements

### Dependencies

- `vitest` - Test runner and assertion library
- `@vitest/coverage-v8` - Code coverage provider
- `@types/node` - Node.js type definitions
- `uuid` - UUID generation (for Express middleware)
- `@types/uuid` - UUID type definitions

### Node.js Version

Node.js 18.0.0 or higher is required.

## Test Standards

### Coverage Goals

- Minimum 80% code coverage on new code
- 100% coverage on critical paths (error handling, source location capture)
- All exported functions must have tests

### Test Structure

Each test file follows this structure:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('Component Name', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
  });

  describe('feature group', () => {
    it('should do something specific', () => {
      // Test implementation
      expect(actual).toBe(expected);
    });
  });
});
```

### Assertion Guidelines

- Use descriptive test names: `it('should capture file, line, and function')`
- One logical assertion per test (related assertions can be grouped)
- Test both happy path and edge cases
- Test error conditions explicitly

### Mocking

- Mock `console.log` to capture output: `vi.spyOn(console, 'log')`
- Mock external dependencies (file system, network)
- Restore mocks in `afterEach()`

## Test Implementation Status

### Implemented Tests

- [x] Core logger functionality
- [x] Log level filtering
- [x] Source location capture
- [x] Context inheritance
- [x] Timer functionality
- [x] Configuration from environment
- [x] JSON formatting
- [x] Express middleware integration

### TODO Tests (Pending Implementation)

- [ ] File handler tests (requires file.ts implementation)
- [ ] Rotating file handler tests (requires rotating.ts implementation)
- [ ] Async queue handler tests
- [ ] Browser-specific tests
- [ ] NestJS integration tests

## Design Document References

See `/home/beltas/investment_platform-logging/docs/DESIGN.md`:

- Section: "Component Design - JavaScript/TypeScript" (lines 921-1000+)
- Source location capture requirements
- Async queue design
- File rotation algorithm

See `/home/beltas/investment_platform-logging/docs/USE_CASES.md`:

- Section: "Node.js NestJS Services" (UC-JS-001 through UC-JS-004)
- Express middleware use cases
- Timer usage patterns
- Context propagation examples

## Key Features Tested

### REQUIRED: Source Location Capture

Every log entry MUST include:
- `file` - Source filename (not full path)
- `line` - Line number where log was called
- `function` - Function name (or `<anonymous>`)

Tests validate that these fields are:
- Always present
- Accurately captured
- Properly formatted

### Performance

Target: < 10 microseconds per log entry (async mode)

While performance testing is not included in these unit tests, the test suite verifies that:
- Source location capture works correctly (prerequisite for performance)
- Async timer properly measures duration
- Context inheritance doesn't modify parent loggers (avoids object copying)

### Error Handling

Tests verify graceful degradation:
- Missing stack traces default to `<unknown>`
- Logger continues functioning after errors
- Console fallback when file writing fails

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Aim for >80% code coverage
4. Update this README if adding new test categories

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: npm ci

- name: Run tests
  run: npm test

- name: Check coverage
  run: npm run test:coverage
```

## Troubleshooting

### Tests Fail with "Logging not initialized"

Ensure `initialize()` is called in `beforeEach()` and `shutdown()` in `afterEach()`.

### Source Location Tests Fail

Source location capture depends on V8 stack trace format. Tests may need adjustment for different JavaScript engines.

### Timer Tests Flaky

Timer tests use `setTimeout()` with minimum delays. CI environments may be slower; increase delays if needed.

### Import Errors

Ensure `.js` extensions are included in imports:
```typescript
import { Logger } from '../src/logger.js';  // Correct
import { Logger } from '../src/logger';     // May fail
```
