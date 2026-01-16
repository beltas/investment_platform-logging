/**
 * Express middleware integration.
 */

import { getLogger, Logger } from '../logger.js';
import { AsyncLocalStorage } from 'async_hooks';
import { v4 as uuidv4 } from 'uuid';

// Async local storage for request-scoped logger
const requestLoggerStorage = new AsyncLocalStorage<Logger>();

export function getRequestLogger(): Logger {
  return requestLoggerStorage.getStore() || getLogger('agora.http');
}

export function loggingMiddleware() {
  const baseLogger = getLogger('agora.http');

  return (req: any, res: any, next: any) => {
    // Extract or generate correlation ID (case-insensitive header lookup)
    const headerKey = Object.keys(req.headers || {}).find(
      (key) => key.toLowerCase() === 'x-correlation-id'
    );
    const correlationId = (headerKey ? req.headers[headerKey] : null) || uuidv4();

    // Create request-scoped logger
    const logger = baseLogger.withContext({
      correlationId,
      method: req.method,
      path: req.path,
    });

    // Add correlation ID to response (if setHeader exists)
    if (typeof res.setHeader === 'function') {
      res.setHeader('X-Correlation-ID', correlationId);
    }

    logger.info('Request started');
    const start = Date.now();

    // Listen for response finish (if on method exists)
    if (typeof res.on === 'function') {
      res.on('finish', () => {
        const duration = Date.now() - start;
        logger.info('Request completed', {
          statusCode: res.statusCode,
          durationMs: duration,
        });
      });
    }

    requestLoggerStorage.run(logger, () => {
      next();
    });
  };
}
