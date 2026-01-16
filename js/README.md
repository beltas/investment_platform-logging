# @agora/logger - JavaScript/TypeScript Logging Library

JavaScript/TypeScript implementation of the Agora Trading Platform logging library.

## Features

- Structured JSON logging with ISO 8601 timestamps
- Automatic source location capture (file, line, function) - **REQUIRED in all log entries**
- Context inheritance with `withContext()`
- Async operation timing with `timer()`
- Dual output (console + file)
- Size-based file rotation
- Express middleware with correlation ID
- Browser support with optional backend logging
- Full TypeScript support with strict types

## Requirements

- **Node.js**: 18+ (for ES2022 features)
- **TypeScript**: 5.3+ (optional, for development)

### Dependencies

**Production:**
- `uuid` - Correlation ID generation

**Development:**
- `typescript` - TypeScript compiler
- `vitest` - Testing framework
- `tsup` - Build tool

## Installation

### Option 1: From Git Repository

```bash
# Using npm
npm install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js

# Using HTTPS
npm install git+https://github.com/agora/investment_platform-logging.git#subdirectory=js

# Using yarn
yarn add git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js
```

### Option 2: Local Development

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging/js

# Install dependencies
npm install

# Build the library
npm run build

# Link for local development
npm link

# In your project
cd /path/to/your/project
npm link @agora/logger
```

## Testing

### Run All Tests

```bash
cd investment_platform-logging/js

# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Coverage

The test suite includes:
- `test_logger.test.ts` - Core logger functionality
- `test_handlers.test.ts` - Console and file handlers
- `test_rotation.test.ts` - File rotation
- `test_formatter.test.ts` - JSON/text formatting
- `test_config.test.ts` - Configuration
- `test_context.test.ts` - Context inheritance
- `test_express.test.ts` - Express middleware

## Building

```bash
# Build for production
npm run build

# Output in dist/
# - index.js, index.mjs (main exports)
# - browser.js, browser.mjs (browser logger)
# - integrations/express.js (Express middleware)
# - *.d.ts (TypeScript declarations)
```

## Quick Start

### Node.js / TypeScript

```typescript
import { initialize, getLogger, configFromEnv } from '@agora/logger';

// Option 1: Manual configuration
initialize({
  serviceName: 'notification-service',
  environment: 'production',
  version: '1.0.0',
  level: 'INFO',
  console: {
    enabled: true,
    format: 'json',
  },
  file: {
    enabled: true,
    path: 'logs/app.log',
    maxSizeMb: 100,
    maxBackups: 5,
  },
});

// Option 2: From environment variables
// initialize(configFromEnv('notification-service'));

// Get a logger
const logger = getLogger('agora.notification.service');

// Log messages with context
logger.info('Email sent', { userId: 'user-123', emailType: 'welcome' });

// Create child logger with additional context
const requestLogger = logger.withContext({
  requestId: 'req-456',
  correlationId: 'corr-789',
});
requestLogger.info('Processing notification');

// Timer for async operations
const result = await logger.timer('Send email', async () => {
  return await sendEmail(user);
}, { recipient: user.email });

// Exception logging
try {
  await riskyOperation();
} catch (error) {
  logger.error('Operation failed', { error, operation: 'sendEmail' });
}

// Shutdown gracefully
await shutdown();
```

### Express Integration

```typescript
import express from 'express';
import { initialize } from '@agora/logger';
import { loggingMiddleware, getRequestLogger } from '@agora/logger/express';

// Initialize logging
initialize({
  serviceName: 'api-gateway',
  environment: 'production',
});

const app = express();

// Add logging middleware (handles correlation ID)
app.use(loggingMiddleware());

app.get('/api/users/:id', (req, res) => {
  // Get request-scoped logger with correlation ID
  const logger = getRequestLogger();

  logger.info('Fetching user', { userId: req.params.id });

  // ... handle request

  res.json({ id: req.params.id });
});

app.listen(3000);
```

### Browser

```typescript
import { initializeBrowserLogger, getBrowserLogger } from '@agora/logger/browser';

// Initialize once
const logger = initializeBrowserLogger({
  serviceName: 'agora-web',
  environment: 'production',
  console: {
    enabled: true,
    format: 'text',  // Human-readable in browser console
  },
  endpoint: '/api/logs',  // Optional: Send logs to backend
});

// Use the logger
logger.info('User logged in', { userId: 'user-123' });

// Get logger elsewhere
const log = getBrowserLogger();
log.error('Failed to load data', { error: err.message });
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENVIRONMENT` | `development` | Environment name |
| `SERVICE_VERSION` | `0.0.0` | Service version |
| `LOG_CONSOLE_ENABLED` | `true` | Enable console output |
| `LOG_CONSOLE_FORMAT` | `json` | Console format (json or text) |
| `LOG_FILE_ENABLED` | `true` | Enable file output |
| `LOG_FILE_PATH` | `logs/app.log` | Log file path |
| `LOG_MAX_FILE_SIZE_MB` | `100` | Max file size before rotation |
| `LOG_MAX_BACKUP_COUNT` | `5` | Number of backup files to keep |

## Log Output Format

### JSON (File/Production)

```json
{
  "timestamp": "2024-01-15T12:34:56.789123Z",
  "level": "INFO",
  "message": "Email sent",
  "service": "notification-service",
  "environment": "production",
  "version": "1.0.0",
  "host": "server-01",
  "loggerName": "agora.notification.service",
  "file": "email.ts",
  "line": 42,
  "function": "sendWelcomeEmail",
  "correlationId": "corr-789",
  "context": {
    "userId": "user-123",
    "emailType": "welcome"
  }
}
```

### Text (Console/Development)

```
[2024-01-15 12:34:56.789] [INFO] [notification-service] Email sent (userId=user-123, emailType=welcome)
```

## Package Exports

```javascript
// Main exports
import { initialize, getLogger, shutdown, configFromEnv } from '@agora/logger';

// Browser logger
import { initializeBrowserLogger, getBrowserLogger } from '@agora/logger/browser';

// Express middleware
import { loggingMiddleware, getRequestLogger } from '@agora/logger/express';
```

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Implementation details
- [examples/](examples/) - Usage examples
- [../docs/DESIGN.md](../docs/DESIGN.md) - API design specification
