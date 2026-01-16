# JavaScript/TypeScript Logging Examples

This directory contains examples of how to use the Agora logging library in JavaScript/TypeScript applications.

## Examples

### Basic Usage (`basic-usage.ts`)

Demonstrates:
- Manual configuration
- Environment variable configuration
- Basic logging methods (info, debug, warning, error, critical)
- Context inheritance with `withContext()`
- Async timer for measuring operation duration
- Multiple logger instances

Run:
```bash
npx tsx examples/basic-usage.ts
```

### Express Integration (`express-usage.ts`)

Demonstrates:
- Express middleware integration
- Automatic correlation ID generation
- Request-scoped logging
- Error handling with logging

Run:
```bash
npx tsx examples/express-usage.ts
```

Then test with:
```bash
curl http://localhost:3000/api/prices/AAPL
curl http://localhost:3000/api/error
```

## Key Features Demonstrated

### 1. Source Location Capture (REQUIRED)

All log entries automatically include:
- `file`: Source file name
- `line`: Line number
- `function`: Function name

### 2. Context Injection

```typescript
const logger = getLogger('service');
const childLogger = logger.withContext({
  userId: 'user-123',
  correlationId: 'abc-def',
});

// All logs from childLogger will include userId and correlationId
childLogger.info('User action');
```

### 3. Async Timer

```typescript
const result = await logger.timer(
  'Operation name',
  async () => await doWork(),
  { additionalContext: 'value' }
);
```

### 4. Dual Output

Logs are written to both:
- Console (JSON or text format)
- Files (JSON format with rotation)

### 5. File Rotation

Files are automatically rotated when they reach the configured size:
- `app.log` (current)
- `app.log.1` (most recent backup)
- `app.log.2`, `app.log.3`, etc.

### 6. Express Middleware

Automatically adds:
- Correlation ID (from header or generated)
- Request method and path
- Request start/completion logs
- Request duration measurement

## Configuration

### Manual Configuration

```typescript
import { initialize } from '@agora/logger';

initialize({
  serviceName: 'my-service',
  environment: 'production',
  version: '1.0.0',
  level: LogLevel.INFO,
  console: {
    enabled: true,
    format: 'json',
    colors: false,
  },
  file: {
    enabled: true,
    path: '/var/log/agora/my-service.log',
    maxSizeMB: 100,
    maxBackupCount: 5,
  },
});
```

### Environment Variables

```typescript
import { configFromEnv } from '@agora/logger';

// Reads LOG_LEVEL, LOG_CONSOLE_FORMAT, LOG_FILE_PATH, etc.
initialize(configFromEnv('my-service'));
```

Supported environment variables:
- `ENVIRONMENT`: development, staging, production
- `SERVICE_VERSION`: Service version
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_CONSOLE_ENABLED`: true/false
- `LOG_CONSOLE_FORMAT`: json/text
- `LOG_CONSOLE_COLORS`: true/false
- `LOG_FILE_ENABLED`: true/false
- `LOG_FILE_PATH`: Path to log file
- `LOG_MAX_FILE_SIZE_MB`: Max file size in MB
- `LOG_MAX_BACKUP_COUNT`: Number of backup files

## Browser Usage

For React/Next.js frontend applications:

```typescript
import { initializeBrowserLogger } from '@agora/logger/browser';

const logger = initializeBrowserLogger({
  serviceName: 'web-app',
  environment: 'production',
  console: {
    enabled: true,
    format: 'text', // Human-readable in browser
  },
  endpoint: '/api/logs', // Optional: Send logs to backend
});

logger.info('Page loaded', { route: window.location.pathname });
```

## Performance

- **Async file writes**: Non-blocking with write queue
- **Batch writes**: Log entries are batched for efficiency
- **Source location capture**: < 10μs overhead per log entry
- **File rotation**: < 50ms for rotation operation
