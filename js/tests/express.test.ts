/**
 * Express middleware integration tests.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { loggingMiddleware, getRequestLogger } from '../src/integrations/express.js';
import { initialize, shutdown } from '../src/logger.js';
import { LogConfig } from '../src/config.js';
import { LogLevel } from '../src/level.js';

describe('Express Middleware', () => {
  let config: LogConfig;
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    config = {
      serviceName: 'test-service',
      environment: 'development',
      version: '1.0.0',
      level: LogLevel.DEBUG,
      console: {
        enabled: true,
        format: 'json',
      },
    };
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    initialize(config);
  });

  afterEach(async () => {
    consoleSpy.mockRestore();
    await shutdown();
  });

  const createMockRequest = (headers: Record<string, string> = {}) => ({
    headers,
    method: 'GET',
    path: '/test',
  });

  const createMockResponse = () => {
    const res: any = {
      statusCode: 200,
      headers: {},
      setHeader: vi.fn((name: string, value: string) => {
        res.headers[name] = value;
      }),
      on: vi.fn((event: string, handler: () => void) => {
        res.finishHandler = handler;
      }),
      finishHandler: null as (() => void) | null,
    };
    return res;
  };

  describe('correlation ID extraction', () => {
    it('should extract correlation ID from X-Correlation-ID header', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'x-correlation-id': 'test-correlation-id',
      });
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(consoleSpy).toHaveBeenCalled();
      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.correlationId).toBe('test-correlation-id');
    });

    it('should be case-insensitive for header name', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'X-CORRELATION-ID': 'test-id',
      });
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.correlationId).toBe('test-id');
    });
  });

  describe('correlation ID generation', () => {
    it('should generate correlation ID when header is missing', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(consoleSpy).toHaveBeenCalled();
      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.correlationId).toBeDefined();
      expect(typeof logEntry.context.correlationId).toBe('string');
      expect(logEntry.context.correlationId.length).toBeGreaterThan(0);
    });

    it('should generate unique correlation IDs for different requests', () => {
      const middleware = loggingMiddleware();

      const req1 = createMockRequest();
      const res1 = createMockResponse();
      const next1 = vi.fn();

      const req2 = createMockRequest();
      const res2 = createMockResponse();
      const next2 = vi.fn();

      middleware(req1, res1, next1);
      middleware(req2, res2, next2);

      const log1 = JSON.parse(consoleSpy.mock.calls[0][0]);
      const log2 = JSON.parse(consoleSpy.mock.calls[1][0]); // Second request start log

      expect(log1.context.correlationId).not.toBe(log2.context.correlationId);
    });
  });

  describe('response header', () => {
    it('should add X-Correlation-ID to response headers', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'x-correlation-id': 'test-id',
      });
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(res.setHeader).toHaveBeenCalledWith('X-Correlation-ID', 'test-id');
    });

    it('should add generated correlation ID to response headers', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(res.setHeader).toHaveBeenCalled();
      const callArgs = res.setHeader.mock.calls[0];
      expect(callArgs[0]).toBe('X-Correlation-ID');
      expect(typeof callArgs[1]).toBe('string');
      expect(callArgs[1].length).toBeGreaterThan(0);
    });
  });

  describe('request logging', () => {
    it('should log request start', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(consoleSpy).toHaveBeenCalledTimes(1);
      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.message).toBe('Request started');
      expect(logEntry.context.method).toBe('GET');
      expect(logEntry.context.path).toBe('/test');
    });

    it('should include request method in context', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      req.method = 'POST';
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.method).toBe('POST');
    });

    it('should include request path in context', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      req.path = '/api/users/123';
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.path).toBe('/api/users/123');
    });
  });

  describe('request completion logging', () => {
    it('should log request completion', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      consoleSpy.mockClear();

      // Simulate response finish
      if (res.finishHandler) {
        res.finishHandler();
      }

      expect(consoleSpy).toHaveBeenCalledTimes(1);
      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.message).toBe('Request completed');
    });

    it('should include status code in completion log', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      res.statusCode = 404;
      const next = vi.fn();

      middleware(req, res, next);
      consoleSpy.mockClear();

      if (res.finishHandler) {
        res.finishHandler();
      }

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.statusCode).toBe(404);
    });

    it('should measure request duration', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);
      consoleSpy.mockClear();

      if (res.finishHandler) {
        res.finishHandler();
      }

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.context.durationMs).toBeDefined();
      expect(typeof logEntry.context.durationMs).toBe('number');
      expect(logEntry.context.durationMs).toBeGreaterThanOrEqual(0);
    });
  });

  describe('getRequestLogger', () => {
    it('should return logger with request context', async () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'x-correlation-id': 'test-id',
      });
      const res = createMockResponse();

      await new Promise<void>((resolve) => {
        const next = vi.fn(() => {
          const logger = getRequestLogger();
          consoleSpy.mockClear();

          logger.info('Inside request handler');

          const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
          expect(logEntry.context.correlationId).toBe('test-id');
          expect(logEntry.context.method).toBe('GET');
          expect(logEntry.context.path).toBe('/test');

          resolve();
        });

        middleware(req, res, next);
      });
    });

    it('should return base logger when called outside request context', () => {
      const logger = getRequestLogger();
      expect(logger).toBeDefined();

      consoleSpy.mockClear();
      logger.info('Outside request');

      const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(logEntry.loggerName).toBe('agora.http');
    });
  });

  describe('next() call', () => {
    it('should call next() to continue middleware chain', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res = createMockResponse();
      const next = vi.fn();

      middleware(req, res, next);

      expect(next).toHaveBeenCalledTimes(1);
    });

    it('should maintain async context through next()', async () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'x-correlation-id': 'async-test',
      });
      const res = createMockResponse();

      await new Promise<void>((resolve) => {
        const next = vi.fn(() => {
          setTimeout(() => {
            const logger = getRequestLogger();
            consoleSpy.mockClear();
            logger.info('Async operation');

            const logEntry = JSON.parse(consoleSpy.mock.calls[0][0]);
            expect(logEntry.context.correlationId).toBe('async-test');
            resolve();
          }, 10);
        });

        middleware(req, res, next);
      });
    });
  });

  describe('error scenarios', () => {
    it('should handle missing request properties', () => {
      const middleware = loggingMiddleware();
      const req: any = { headers: {} };
      const res = createMockResponse();
      const next = vi.fn();

      expect(() => middleware(req, res, next)).not.toThrow();
    });

    it('should handle missing response methods', () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest();
      const res: any = {};
      const next = vi.fn();

      expect(() => middleware(req, res, next)).not.toThrow();
    });
  });

  describe('correlation ID propagation', () => {
    it('should propagate correlation ID throughout request lifecycle', async () => {
      const middleware = loggingMiddleware();
      const req = createMockRequest({
        'x-correlation-id': 'propagate-test',
      });
      const res = createMockResponse();

      await new Promise<void>((resolve) => {
        const next = vi.fn(() => {
          const logger = getRequestLogger();
          logger.info('During request');
          resolve();
        });

        middleware(req, res, next);
      });

      // All logs should have the same correlation ID
      const startLog = JSON.parse(consoleSpy.mock.calls[0][0]);
      const duringLog = JSON.parse(consoleSpy.mock.calls[1][0]);

      expect(startLog.context.correlationId).toBe('propagate-test');
      expect(duringLog.context.correlationId).toBe('propagate-test');
    });
  });
});
