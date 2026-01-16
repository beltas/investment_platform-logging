/**
 * Logging configuration with runtime validation.
 */

import { LogLevel } from './level.js';

export interface ConsoleConfig {
  enabled: boolean;
  format: 'json' | 'text';
  colors?: boolean;
}

export interface FileConfig {
  enabled: boolean;
  path: string;
  maxSizeMB: number;
  maxBackupCount: number;
}

export interface LogConfig {
  serviceName: string;
  environment: 'development' | 'staging' | 'production';
  version: string;
  level: LogLevel;
  console: ConsoleConfig;
  file?: FileConfig;
  defaultContext?: Record<string, unknown>;
}

/** Valid environment values */
const VALID_ENVIRONMENTS = ['development', 'staging', 'production'] as const;

/** Valid console format values */
const VALID_FORMATS = ['json', 'text'] as const;

/**
 * Parse and validate log level from string.
 * Returns default level if invalid, with optional warning.
 */
export function parseLogLevel(value: string | undefined, warnOnInvalid = true): LogLevel {
  if (!value) return LogLevel.INFO;

  const normalized = value.toUpperCase();

  // Check if it's a valid LogLevel key
  if (normalized in LogLevel) {
    const levelValue = LogLevel[normalized as keyof typeof LogLevel];
    // Ensure it's a number (not the reverse mapping)
    if (typeof levelValue === 'number') {
      return levelValue;
    }
  }

  if (warnOnInvalid) {
    console.warn(`Invalid log level "${value}", defaulting to INFO. Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL`);
  }
  return LogLevel.INFO;
}

/**
 * Parse and validate environment from string.
 */
export function parseEnvironment(value: string | undefined, warnOnInvalid = true): LogConfig['environment'] {
  if (!value) return 'development';

  const normalized = value.toLowerCase();

  if (VALID_ENVIRONMENTS.includes(normalized as typeof VALID_ENVIRONMENTS[number])) {
    return normalized as LogConfig['environment'];
  }

  if (warnOnInvalid) {
    console.warn(`Invalid environment "${value}", defaulting to development. Valid values: ${VALID_ENVIRONMENTS.join(', ')}`);
  }
  return 'development';
}

/**
 * Parse and validate console format from string.
 */
export function parseConsoleFormat(value: string | undefined, warnOnInvalid = true): 'json' | 'text' {
  if (!value) return 'json';

  const normalized = value.toLowerCase();

  if (VALID_FORMATS.includes(normalized as typeof VALID_FORMATS[number])) {
    return normalized as 'json' | 'text';
  }

  if (warnOnInvalid) {
    console.warn(`Invalid console format "${value}", defaulting to json. Valid values: ${VALID_FORMATS.join(', ')}`);
  }
  return 'json';
}

/**
 * Parse positive integer with validation.
 */
function parsePositiveInt(value: string | undefined, defaultValue: number, fieldName: string): number {
  if (!value) return defaultValue;

  const parsed = parseInt(value, 10);

  if (isNaN(parsed) || parsed <= 0) {
    console.warn(`Invalid ${fieldName} "${value}", defaulting to ${defaultValue}. Must be a positive integer.`);
    return defaultValue;
  }

  return parsed;
}

/**
 * Validate a LogConfig object.
 * Throws if critical fields are missing.
 */
export function validateConfig(config: LogConfig): void {
  if (!config.serviceName || config.serviceName.trim() === '') {
    throw new Error('LogConfig.serviceName is required and cannot be empty');
  }

  if (config.file?.enabled) {
    if (!config.file.path || config.file.path.trim() === '') {
      throw new Error('LogConfig.file.path is required when file logging is enabled');
    }
    if (config.file.maxSizeMB <= 0) {
      throw new Error('LogConfig.file.maxSizeMB must be positive');
    }
    if (config.file.maxBackupCount < 0) {
      throw new Error('LogConfig.file.maxBackupCount cannot be negative');
    }
  }
}

/**
 * Create configuration from environment variables with full validation.
 */
export function configFromEnv(serviceName: string): LogConfig {
  const env = process.env;

  const config: LogConfig = {
    serviceName,
    environment: parseEnvironment(env.ENVIRONMENT),
    version: env.SERVICE_VERSION || '0.0.0',
    level: parseLogLevel(env.LOG_LEVEL),
    console: {
      enabled: env.LOG_CONSOLE_ENABLED !== 'false',
      format: parseConsoleFormat(env.LOG_CONSOLE_FORMAT),
      colors: env.LOG_CONSOLE_COLORS !== 'false',
    },
    file: env.LOG_FILE_ENABLED !== 'false' ? {
      enabled: true,
      path: env.LOG_FILE_PATH || '/agora/logs/app.log',
      maxSizeMB: parsePositiveInt(env.LOG_MAX_FILE_SIZE_MB, 100, 'LOG_MAX_FILE_SIZE_MB'),
      maxBackupCount: parsePositiveInt(env.LOG_MAX_BACKUP_COUNT, 5, 'LOG_MAX_BACKUP_COUNT'),
    } : undefined,
  };

  // Validate the constructed config
  validateConfig(config);

  return config;
}
