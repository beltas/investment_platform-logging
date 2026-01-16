/**
 * Basic usage example of the Agora logging library.
 */

import { initialize, getLogger, shutdown, configFromEnv } from '../src/index.js';
import { LogLevel } from '../src/level.js';

async function main() {
  // Example 1: Initialize with manual config
  console.log('=== Example 1: Manual Configuration ===\n');

  const logger = initialize({
    serviceName: 'example-service',
    environment: 'development',
    version: '1.0.0',
    level: LogLevel.DEBUG,
    console: {
      enabled: true,
      format: 'text',
      colors: true,
    },
    file: {
      enabled: true,
      path: 'logs/example.log',
      maxSizeMB: 10,
      maxBackupCount: 3,
    },
  });

  // Basic logging
  logger.info('Service started successfully');
  logger.debug('Debug information', { userId: 'user-123', action: 'login' });
  logger.warning('High memory usage detected', { memoryMB: 512 });

  // Error logging with exception
  try {
    throw new Error('Database connection failed');
  } catch (error) {
    logger.error('Failed to connect to database', error as Error, {
      host: 'localhost',
      port: 5432,
    });
  }

  // Child logger with context
  const requestLogger = logger.withContext({
    correlationId: '550e8400-e29b-41d4-a716-446655440000',
    userId: 'user-456',
  });

  requestLogger.info('Processing user request', { action: 'fetch_portfolio' });

  // Timer for async operations
  await requestLogger.timer('Database query', async () => {
    // Simulate async work
    await new Promise((resolve) => setTimeout(resolve, 50));
    return { rows: 10 };
  }, { table: 'portfolios' });

  console.log('\n=== Example 2: Environment Variables ===\n');

  // Clean up first example
  await shutdown();

  // Example 2: Configuration from environment variables
  process.env.ENVIRONMENT = 'production';
  process.env.SERVICE_VERSION = '2.0.0';
  process.env.LOG_LEVEL = 'INFO';
  process.env.LOG_CONSOLE_FORMAT = 'json';

  const envLogger = initialize(configFromEnv('env-example-service'));
  envLogger.info('Logger initialized from environment variables');
  envLogger.debug('This will not be logged (level is INFO)');

  // Multiple logger instances
  const apiLogger = getLogger('api');
  const dbLogger = getLogger('database');

  apiLogger.info('API request received', { endpoint: '/api/prices' });
  dbLogger.info('Query executed', { duration_ms: 25 });

  // Clean up
  await shutdown();

  console.log('\n=== All examples completed ===');
}

main().catch(console.error);
