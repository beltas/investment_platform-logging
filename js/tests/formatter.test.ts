/**
 * JSON formatter tests.
 */

import { describe, it, expect } from 'vitest';
import { LogEntry } from '../src/entry.js';

describe('JSON Formatter', () => {
  const createSampleEntry = (overrides: Partial<LogEntry> = {}): LogEntry => ({
    timestamp: '2025-01-15T10:30:45.123Z',
    level: 'INFO',
    message: 'test message',
    service: 'test-service',
    environment: 'development',
    version: '1.0.0',
    host: 'test-host',
    loggerName: 'test.logger',
    file: 'test.ts',
    line: 42,
    function: 'testFunction',
    ...overrides,
  });

  describe('required fields', () => {
    it('should include all required fields', () => {
      const entry = createSampleEntry();
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.timestamp).toBe('2025-01-15T10:30:45.123Z');
      expect(parsed.level).toBe('INFO');
      expect(parsed.message).toBe('test message');
      expect(parsed.service).toBe('test-service');
      expect(parsed.environment).toBe('development');
      expect(parsed.version).toBe('1.0.0');
      expect(parsed.host).toBe('test-host');
      expect(parsed.loggerName).toBe('test.logger');
      expect(parsed.file).toBe('test.ts');
      expect(parsed.line).toBe(42);
      expect(parsed.function).toBe('testFunction');
    });

    it('should validate timestamp format', () => {
      const entry = createSampleEntry();
      const timestamp = new Date(entry.timestamp);
      expect(timestamp.toISOString()).toBe(entry.timestamp);
    });

    it('should validate source location fields are present', () => {
      const entry = createSampleEntry();
      expect(entry.file).toBeDefined();
      expect(entry.line).toBeDefined();
      expect(entry.function).toBeDefined();
    });
  });

  describe('optional fields', () => {
    it('should include correlationId when present', () => {
      const entry = createSampleEntry({ correlationId: 'corr-123' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.correlationId).toBe('corr-123');
    });

    it('should include userId when present', () => {
      const entry = createSampleEntry({ userId: 'user-456' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.userId).toBe('user-456');
    });

    it('should include traceId when present', () => {
      const entry = createSampleEntry({ traceId: 'trace-789' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.traceId).toBe('trace-789');
    });

    it('should include spanId when present', () => {
      const entry = createSampleEntry({ spanId: 'span-abc' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.spanId).toBe('span-abc');
    });

    it('should not include optional fields when absent', () => {
      const entry = createSampleEntry();
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.correlationId).toBeUndefined();
      expect(parsed.userId).toBeUndefined();
      expect(parsed.traceId).toBeUndefined();
      expect(parsed.spanId).toBeUndefined();
    });
  });

  describe('context serialization', () => {
    it('should serialize string context values', () => {
      const entry = createSampleEntry({
        context: { key: 'value' },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.key).toBe('value');
    });

    it('should serialize number context values', () => {
      const entry = createSampleEntry({
        context: { count: 42 },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.count).toBe(42);
    });

    it('should serialize boolean context values', () => {
      const entry = createSampleEntry({
        context: { flag: true },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.flag).toBe(true);
    });

    it('should serialize nested objects', () => {
      const entry = createSampleEntry({
        context: {
          nested: {
            key: 'value',
            count: 42,
          },
        },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.nested.key).toBe('value');
      expect(parsed.context.nested.count).toBe(42);
    });

    it('should serialize arrays', () => {
      const entry = createSampleEntry({
        context: {
          items: ['a', 'b', 'c'],
        },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.items).toEqual(['a', 'b', 'c']);
    });

    it('should handle empty context', () => {
      const entry = createSampleEntry({ context: {} });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context).toEqual({});
    });

    it('should handle undefined context', () => {
      const entry = createSampleEntry({ context: undefined });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context).toBeUndefined();
    });
  });

  describe('exception formatting', () => {
    it('should format exception with type, message, and stacktrace', () => {
      const entry = createSampleEntry({
        exception: {
          type: 'Error',
          message: 'test error',
          stacktrace: 'Error: test error\n    at test.ts:10:5',
        },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.exception.type).toBe('Error');
      expect(parsed.exception.message).toBe('test error');
      expect(parsed.exception.stacktrace).toContain('test error');
      expect(parsed.exception.stacktrace).toContain('test.ts:10:5');
    });

    it('should handle custom error types', () => {
      const entry = createSampleEntry({
        exception: {
          type: 'CustomError',
          message: 'custom error message',
          stacktrace: 'CustomError: custom error message',
        },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.exception.type).toBe('CustomError');
    });

    it('should not include exception when absent', () => {
      const entry = createSampleEntry();
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.exception).toBeUndefined();
    });
  });

  describe('duration formatting', () => {
    it('should include durationMs when present', () => {
      const entry = createSampleEntry({
        durationMs: 123.456,
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.durationMs).toBe(123.456);
    });

    it('should handle integer durations', () => {
      const entry = createSampleEntry({
        durationMs: 100,
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.durationMs).toBe(100);
    });

    it('should not include durationMs when absent', () => {
      const entry = createSampleEntry();
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.durationMs).toBeUndefined();
    });
  });

  describe('log levels', () => {
    it('should format DEBUG level', () => {
      const entry = createSampleEntry({ level: 'DEBUG' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.level).toBe('DEBUG');
    });

    it('should format INFO level', () => {
      const entry = createSampleEntry({ level: 'INFO' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.level).toBe('INFO');
    });

    it('should format WARNING level', () => {
      const entry = createSampleEntry({ level: 'WARNING' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.level).toBe('WARNING');
    });

    it('should format ERROR level', () => {
      const entry = createSampleEntry({ level: 'ERROR' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.level).toBe('ERROR');
    });

    it('should format CRITICAL level', () => {
      const entry = createSampleEntry({ level: 'CRITICAL' });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.level).toBe('CRITICAL');
    });
  });

  describe('complete log entry', () => {
    it('should format complete log entry with all fields', () => {
      const entry = createSampleEntry({
        correlationId: 'corr-123',
        userId: 'user-456',
        traceId: 'trace-789',
        spanId: 'span-abc',
        context: {
          operation: 'database_query',
          table: 'users',
          rowCount: 42,
        },
        durationMs: 25.5,
        exception: {
          type: 'DatabaseError',
          message: 'Connection timeout',
          stacktrace: 'DatabaseError: Connection timeout\n    at db.ts:100:10',
        },
      });

      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed).toMatchObject({
        timestamp: '2025-01-15T10:30:45.123Z',
        level: 'INFO',
        message: 'test message',
        service: 'test-service',
        environment: 'development',
        version: '1.0.0',
        host: 'test-host',
        loggerName: 'test.logger',
        file: 'test.ts',
        line: 42,
        function: 'testFunction',
        correlationId: 'corr-123',
        userId: 'user-456',
        traceId: 'trace-789',
        spanId: 'span-abc',
        context: {
          operation: 'database_query',
          table: 'users',
          rowCount: 42,
        },
        durationMs: 25.5,
        exception: {
          type: 'DatabaseError',
          message: 'Connection timeout',
          stacktrace: expect.stringContaining('Connection timeout'),
        },
      });
    });
  });

  describe('JSON structure validation', () => {
    it('should produce valid JSON', () => {
      const entry = createSampleEntry();
      const json = JSON.stringify(entry);
      expect(() => JSON.parse(json)).not.toThrow();
    });

    it('should be parseable by standard JSON parsers', () => {
      const entry = createSampleEntry({
        context: {
          string: 'value',
          number: 42,
          boolean: true,
          null: null,
        },
      });
      const json = JSON.stringify(entry);
      const parsed = JSON.parse(json);

      expect(parsed.context.string).toBe('value');
      expect(parsed.context.number).toBe(42);
      expect(parsed.context.boolean).toBe(true);
      expect(parsed.context.null).toBe(null);
    });
  });
});
