/**
 * Configuration tests.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { configFromEnv, LogConfig } from '../src/config.js';
import { LogLevel } from '../src/level.js';

describe('Configuration', () => {
  let originalEnv: NodeJS.ProcessEnv;

  beforeEach(() => {
    originalEnv = { ...process.env };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('configFromEnv', () => {
    it('should create config with service name', () => {
      const config = configFromEnv('test-service');
      expect(config.serviceName).toBe('test-service');
    });

    it('should use default environment', () => {
      delete process.env.ENVIRONMENT;
      const config = configFromEnv('test-service');
      expect(config.environment).toBe('development');
    });

    it('should read environment from env var', () => {
      process.env.ENVIRONMENT = 'production';
      const config = configFromEnv('test-service');
      expect(config.environment).toBe('production');
    });

    it('should use default version', () => {
      delete process.env.SERVICE_VERSION;
      const config = configFromEnv('test-service');
      expect(config.version).toBe('0.0.0');
    });

    it('should read version from env var', () => {
      process.env.SERVICE_VERSION = '1.2.3';
      const config = configFromEnv('test-service');
      expect(config.version).toBe('1.2.3');
    });

    it('should default to INFO level', () => {
      delete process.env.LOG_LEVEL;
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.INFO);
    });

    it('should parse DEBUG level', () => {
      process.env.LOG_LEVEL = 'DEBUG';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.DEBUG);
    });

    it('should parse INFO level', () => {
      process.env.LOG_LEVEL = 'INFO';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.INFO);
    });

    it('should parse WARNING level', () => {
      process.env.LOG_LEVEL = 'WARNING';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.WARNING);
    });

    it('should parse ERROR level', () => {
      process.env.LOG_LEVEL = 'ERROR';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.ERROR);
    });

    it('should parse CRITICAL level', () => {
      process.env.LOG_LEVEL = 'CRITICAL';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.CRITICAL);
    });

    it('should handle lowercase log level', () => {
      process.env.LOG_LEVEL = 'debug';
      const config = configFromEnv('test-service');
      expect(config.level).toBe(LogLevel.DEBUG);
    });
  });

  describe('console configuration', () => {
    it('should enable console by default', () => {
      delete process.env.LOG_CONSOLE_ENABLED;
      const config = configFromEnv('test-service');
      expect(config.console.enabled).toBe(true);
    });

    it('should disable console when env var is false', () => {
      process.env.LOG_CONSOLE_ENABLED = 'false';
      const config = configFromEnv('test-service');
      expect(config.console.enabled).toBe(false);
    });

    it('should default to JSON format', () => {
      delete process.env.LOG_CONSOLE_FORMAT;
      const config = configFromEnv('test-service');
      expect(config.console.format).toBe('json');
    });

    it('should use text format when specified', () => {
      process.env.LOG_CONSOLE_FORMAT = 'text';
      const config = configFromEnv('test-service');
      expect(config.console.format).toBe('text');
    });

    it('should enable colors by default', () => {
      delete process.env.LOG_CONSOLE_COLORS;
      const config = configFromEnv('test-service');
      expect(config.console.colors).toBe(true);
    });

    it('should disable colors when env var is false', () => {
      process.env.LOG_CONSOLE_COLORS = 'false';
      const config = configFromEnv('test-service');
      expect(config.console.colors).toBe(false);
    });
  });

  describe('file configuration', () => {
    it('should enable file logging by default', () => {
      delete process.env.LOG_FILE_ENABLED;
      const config = configFromEnv('test-service');
      expect(config.file).toBeDefined();
      expect(config.file!.enabled).toBe(true);
    });

    it('should disable file logging when env var is false', () => {
      process.env.LOG_FILE_ENABLED = 'false';
      const config = configFromEnv('test-service');
      expect(config.file).toBeUndefined();
    });

    it('should use default file path', () => {
      delete process.env.LOG_FILE_PATH;
      const config = configFromEnv('test-service');
      expect(config.file!.path).toBe('/agora/logs/app.log');
    });

    it('should read file path from env var', () => {
      process.env.LOG_FILE_PATH = '/var/log/custom.log';
      const config = configFromEnv('test-service');
      expect(config.file!.path).toBe('/var/log/custom.log');
    });

    it('should use default max file size', () => {
      delete process.env.LOG_MAX_FILE_SIZE_MB;
      const config = configFromEnv('test-service');
      expect(config.file!.maxSizeMB).toBe(100);
    });

    it('should read max file size from env var', () => {
      process.env.LOG_MAX_FILE_SIZE_MB = '50';
      const config = configFromEnv('test-service');
      expect(config.file!.maxSizeMB).toBe(50);
    });

    it('should use default max backup count', () => {
      delete process.env.LOG_MAX_BACKUP_COUNT;
      const config = configFromEnv('test-service');
      expect(config.file!.maxBackupCount).toBe(5);
    });

    it('should read max backup count from env var', () => {
      process.env.LOG_MAX_BACKUP_COUNT = '10';
      const config = configFromEnv('test-service');
      expect(config.file!.maxBackupCount).toBe(10);
    });
  });

  describe('config type validation', () => {
    it('should have correct type for environment', () => {
      const config = configFromEnv('test-service');
      const validEnvs: Array<'development' | 'staging' | 'production'> = [
        'development',
        'staging',
        'production',
      ];
      expect(validEnvs).toContain(config.environment);
    });

    it('should have correct type for console format', () => {
      const config = configFromEnv('test-service');
      const validFormats: Array<'json' | 'text'> = ['json', 'text'];
      expect(validFormats).toContain(config.console.format);
    });

    it('should have correct type for log level', () => {
      const config = configFromEnv('test-service');
      expect(Object.values(LogLevel)).toContain(config.level);
    });
  });

  describe('complete configuration', () => {
    it('should create complete config from environment', () => {
      process.env.ENVIRONMENT = 'production';
      process.env.SERVICE_VERSION = '2.0.0';
      process.env.LOG_LEVEL = 'WARNING';
      process.env.LOG_CONSOLE_FORMAT = 'text';
      process.env.LOG_CONSOLE_COLORS = 'false';
      process.env.LOG_FILE_PATH = '/var/log/app.log';
      process.env.LOG_MAX_FILE_SIZE_MB = '200';
      process.env.LOG_MAX_BACKUP_COUNT = '3';

      const config = configFromEnv('production-service');

      expect(config).toEqual({
        serviceName: 'production-service',
        environment: 'production',
        version: '2.0.0',
        level: LogLevel.WARNING,
        console: {
          enabled: true,
          format: 'text',
          colors: false,
        },
        file: {
          enabled: true,
          path: '/var/log/app.log',
          maxSizeMB: 200,
          maxBackupCount: 3,
        },
      });
    });
  });
});
