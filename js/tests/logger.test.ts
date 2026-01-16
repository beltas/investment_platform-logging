/**
 * Core logger tests.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { Logger, initialize, getLogger, shutdown } from '../src/logger.js';
import { LogConfig } from '../src/config.js';
import { LogLevel } from '../src/level.js';

describe('Logger', () => {
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
  });

  afterEach(async () => {
    consoleSpy.mockRestore();
    await shutdown();
  });

  describe('initialization', () => {
    it('should initialize logger with configuration', () => {
      const logger = initialize(config);
      expect(logger).toBeInstanceOf(Logger);
    });

    it('should throw error if getLogger called before initialization', () => {
      expect(() => getLogger('test')).toThrow('Logging not initialized');
    });

    it('should return same logger instance for same name', () => {
      initialize(config);
      const logger1 = getLogger('test');
      const logger2 = getLogger('test');
      expect(logger1).toBe(logger2);
    });

    it('should return different logger instances for different names', () => {
      initialize(config);
      const logger1 = getLogger('test1');
      const logger2 = getLogger('test2');
      expect(logger1).not.toBe(logger2);
    });
  });

  describe('log level filtering', () => {
    it('should log when level is at threshold', () => {
      initialize(config);
      const logger = getLogger('test');
      logger.info('test message');
      expect(consoleSpy).toHaveBeenCalledTimes(1);
    });

    it('should not log when level is below threshold', () => {
      config.level = LogLevel.INFO;
      initialize(config);
      const logger = getLogger('test');
      logger.debug('debug message');
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should log INFO messages when level is INFO', () => {
      config.level = LogLevel.INFO;
      initialize(config);
      const logger = getLogger('test');
      logger.info('info message');
      expect(consoleSpy).toHaveBeenCalledTimes(1);
    });

    it('should log WARNING messages when level is INFO', () => {
      config.level = LogLevel.INFO;
      initialize(config);
      const logger = getLogger('test');
      logger.warning('warning message');
      expect(consoleSpy).toHaveBeenCalledTimes(1);
    });

    it('should log ERROR messages when level is INFO', () => {
      config.level = LogLevel.INFO;
      initialize(config);
      const logger = getLogger('test');
      logger.error('error message');
      expect(consoleSpy).toHaveBeenCalledTimes(1);
    });

    it('should log CRITICAL messages when level is INFO', () => {
      config.level = LogLevel.INFO;
      initialize(config);
      const logger = getLogger('test');
      logger.critical('critical message');
      expect(consoleSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('source location capture', () => {
    it('should capture file, line, and function in log entries', () => {
      initialize(config);
      const logger = getLogger('test');
      logger.info('test message');

      expect(consoleSpy).toHaveBeenCalledTimes(1);
      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);

      // REQUIRED fields
      expect(loggedData.file).toBeDefined();
      expect(loggedData.file).toMatch(/logger\.test\.(ts|js)/);
      expect(loggedData.line).toBeTypeOf('number');
      expect(loggedData.line).toBeGreaterThan(0);
      expect(loggedData.function).toBeDefined();
      expect(loggedData.function).toBeTruthy();
    });

    it('should capture correct function name', () => {
      initialize(config);
      const logger = getLogger('test');

      function namedFunction() {
        logger.info('test from named function');
      }

      namedFunction();

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.function).toBe('namedFunction');
    });

    it('should handle anonymous functions', () => {
      initialize(config);
      const logger = getLogger('test');

      (() => {
        logger.info('test from anonymous');
      })();

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      // Function name may be '<anonymous>' or the test name
      expect(loggedData.function).toBeDefined();
    });
  });

  describe('context inheritance', () => {
    it('should inherit parent context in child logger', () => {
      initialize(config);
      const parent = getLogger('parent').withContext({
        parentKey: 'parentValue',
      });

      parent.info('test message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.parentKey).toBe('parentValue');
    });

    it('should merge child context with parent context', () => {
      initialize(config);
      const parent = getLogger('parent').withContext({
        parentKey: 'parentValue',
      });

      const child = parent.withContext({
        childKey: 'childValue',
      });

      child.info('test message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.parentKey).toBe('parentValue');
      expect(loggedData.context.childKey).toBe('childValue');
    });

    it('should override parent context with child context', () => {
      initialize(config);
      const parent = getLogger('parent').withContext({
        key: 'parentValue',
      });

      const child = parent.withContext({
        key: 'childValue',
      });

      child.info('test message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.key).toBe('childValue');
    });
  });

  describe('withContext()', () => {
    it('should create new logger instance', () => {
      initialize(config);
      const logger = getLogger('test');
      const child = logger.withContext({ key: 'value' });

      expect(child).toBeInstanceOf(Logger);
      expect(child).not.toBe(logger);
    });

    it('should not modify parent logger context', () => {
      initialize(config);
      const parent = getLogger('test');
      const child = parent.withContext({ childKey: 'value' });

      parent.info('parent message');
      child.info('child message');

      const parentLog = JSON.parse(consoleSpy.mock.calls[0][0]);
      const childLog = JSON.parse(consoleSpy.mock.calls[1][0]);

      expect(parentLog.context.childKey).toBeUndefined();
      expect(childLog.context.childKey).toBe('value');
    });

    it('should support multiple levels of nesting', () => {
      initialize(config);
      const level1 = getLogger('test').withContext({ level1: 'value1' });
      const level2 = level1.withContext({ level2: 'value2' });
      const level3 = level2.withContext({ level3: 'value3' });

      level3.info('nested message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.level1).toBe('value1');
      expect(loggedData.context.level2).toBe('value2');
      expect(loggedData.context.level3).toBe('value3');
    });
  });

  describe('timer functionality', () => {
    it('should log operation duration on success', async () => {
      initialize(config);
      const logger = getLogger('test');

      await logger.timer('test operation', async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return 'result';
      });

      expect(consoleSpy).toHaveBeenCalledTimes(1);
      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);

      expect(loggedData.message).toBe('test operation');
      expect(loggedData.context.durationMs).toBeTypeOf('number');
      // Allow some timing variance (setTimeout is not precise)
      expect(loggedData.context.durationMs).toBeGreaterThanOrEqual(8);
    });

    it('should log operation duration on error', async () => {
      initialize(config);
      const logger = getLogger('test');

      const error = new Error('test error');

      await expect(
        logger.timer('test operation', async () => {
          await new Promise((resolve) => setTimeout(resolve, 10));
          throw error;
        })
      ).rejects.toThrow('test error');

      expect(consoleSpy).toHaveBeenCalledTimes(1);
      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);

      expect(loggedData.message).toBe('test operation failed');
      expect(loggedData.level).toBe('ERROR');
      expect(loggedData.context.durationMs).toBeTypeOf('number');
      // Allow some timing variance (setTimeout is not precise)
      expect(loggedData.context.durationMs).toBeGreaterThanOrEqual(8);
      expect(loggedData.exception).toBeDefined();
      expect(loggedData.exception.message).toBe('test error');
    });

    it('should include additional context in timer log', async () => {
      initialize(config);
      const logger = getLogger('test');

      await logger.timer(
        'test operation',
        async () => 'result',
        { operationType: 'database' }
      );

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.operationType).toBe('database');
    });

    it('should return operation result', async () => {
      initialize(config);
      const logger = getLogger('test');

      const result = await logger.timer('test operation', async () => {
        return { data: 'test' };
      });

      expect(result).toEqual({ data: 'test' });
    });

    it('should capture source location from timer call site', async () => {
      initialize(config);
      const logger = getLogger('test');

      await logger.timer('test operation', async () => 'result');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.file).toMatch(/logger\.test\.(ts|js)/);
      expect(loggedData.line).toBeTypeOf('number');
    });
  });

  describe('required fields', () => {
    it('should include all required fields in log entry', () => {
      initialize(config);
      const logger = getLogger('test');
      logger.info('test message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);

      // Required fields
      expect(loggedData.timestamp).toBeDefined();
      expect(loggedData.level).toBe('INFO');
      expect(loggedData.message).toBe('test message');
      expect(loggedData.service).toBe('test-service');
      expect(loggedData.environment).toBe('development');
      expect(loggedData.version).toBe('1.0.0');
      expect(loggedData.host).toBeDefined();
      expect(loggedData.loggerName).toBe('test');
      expect(loggedData.file).toBeDefined();
      expect(loggedData.line).toBeDefined();
      expect(loggedData.function).toBeDefined();
    });

    it('should format timestamp as ISO 8601', () => {
      initialize(config);
      const logger = getLogger('test');
      logger.info('test message');

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      const timestamp = new Date(loggedData.timestamp);
      expect(timestamp.toISOString()).toBe(loggedData.timestamp);
    });
  });

  describe('exception logging', () => {
    it('should log exception with error details', () => {
      initialize(config);
      const logger = getLogger('test');
      const error = new Error('test error');

      logger.error('error occurred', error);

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.exception).toBeDefined();
      expect(loggedData.exception.type).toBe('Error');
      expect(loggedData.exception.message).toBe('test error');
      expect(loggedData.exception.stacktrace).toBeDefined();
      expect(loggedData.exception.stacktrace).toContain('test error');
    });

    it('should handle custom error types', () => {
      initialize(config);
      const logger = getLogger('test');

      class CustomError extends Error {
        constructor(message: string) {
          super(message);
          this.name = 'CustomError';
        }
      }

      const error = new CustomError('custom error');
      logger.error('custom error occurred', error);

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.exception.type).toBe('CustomError');
      expect(loggedData.exception.message).toBe('custom error');
    });

    it('should log critical errors with exception', () => {
      initialize(config);
      const logger = getLogger('test');
      const error = new Error('critical error');

      logger.critical('critical failure', error);

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.level).toBe('CRITICAL');
      expect(loggedData.exception).toBeDefined();
      expect(loggedData.exception.message).toBe('critical error');
    });
  });

  describe('custom context', () => {
    it('should include custom context in log entry', () => {
      initialize(config);
      const logger = getLogger('test');

      logger.info('test message', { customKey: 'customValue' });

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.customKey).toBe('customValue');
    });

    it('should support multiple context values', () => {
      initialize(config);
      const logger = getLogger('test');

      logger.info('test message', {
        key1: 'value1',
        key2: 42,
        key3: true,
      });

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.key1).toBe('value1');
      expect(loggedData.context.key2).toBe(42);
      expect(loggedData.context.key3).toBe(true);
    });

    it('should merge inline context with logger context', () => {
      initialize(config);
      const logger = getLogger('test').withContext({ loggerKey: 'loggerValue' });

      logger.info('test message', { inlineKey: 'inlineValue' });

      const loggedData = JSON.parse(consoleSpy.mock.calls[0][0]);
      expect(loggedData.context.loggerKey).toBe('loggerValue');
      expect(loggedData.context.inlineKey).toBe('inlineValue');
    });
  });

  describe('console output disabled', () => {
    it('should not output to console when disabled', () => {
      config.console.enabled = false;
      initialize(config);
      const logger = getLogger('test');

      logger.info('test message');

      expect(consoleSpy).not.toHaveBeenCalled();
    });
  });

  describe('text format console output', () => {
    it('should output text format when configured', () => {
      config.console.format = 'text';
      initialize(config);
      const logger = getLogger('test');

      logger.info('test message');

      const output = consoleSpy.mock.calls[0][0];
      expect(output).toContain('INFO');
      expect(output).toContain('test-service');
      expect(output).toContain('test message');
      expect(() => JSON.parse(output)).toThrow(); // Not JSON
    });
  });
});
