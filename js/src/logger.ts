/**
 * Core logger implementation.
 */

import * as os from 'os';
import { LogConfig } from './config.js';
import { LogLevel, levelToString } from './level.js';
import { LogEntry } from './entry.js';
import { captureSourceLocation, SourceLocation } from './source-location.js';
import { Handler, ConsoleHandler, RotatingFileHandler } from './handlers/index.js';

// Global state
let globalConfig: LogConfig | null = null;
const loggers: Map<string, Logger> = new Map();
const handlers: Handler[] = [];

export class Logger {
  private readonly name: string;
  private readonly config: LogConfig;
  private readonly context: Record<string, unknown>;

  constructor(
    name: string,
    config: LogConfig,
    context: Record<string, unknown> = {}
  ) {
    this.name = name;
    this.config = config;
    this.context = context;
  }

  /**
   * Internal log method that captures source location.
   *
   * Optimized with lazy evaluation:
   * - Level check happens first (before any expensive operations)
   * - Source location capture only occurs if log will be emitted
   */
  private log(
    level: LogLevel,
    message: string,
    context: Record<string, unknown> = {},
    error?: Error,
    location?: SourceLocation
  ): void {
    // Skip if level is below threshold - this is checked FIRST
    // to avoid expensive source location capture for filtered logs
    if (level < this.config.level) {
      return;
    }

    // Capture source location (REQUIRED) - only after level check passes
    const source = location || captureSourceLocation(3);

    // Create log entry with required fields
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: levelToString(level),
      message,
      service: this.config.serviceName,
      environment: this.config.environment,
      version: this.config.version,
      host: this.getHostname(),
      loggerName: this.name,
      // REQUIRED source location fields
      file: source.file,
      line: source.line,
      function: source.function,
      // Optional fields
      correlationId: this.context.correlationId as string | undefined,
      userId: this.context.userId as string | undefined,
      traceId: this.context.traceId as string | undefined,
      spanId: this.context.spanId as string | undefined,
      context: { ...this.context, ...context },
      exception: error
        ? {
            type: error.constructor.name,
            message: error.message,
            stacktrace: error.stack || '',
          }
        : undefined,
    };

    // Emit to all handlers
    for (const handler of handlers) {
      try {
        handler.emit(entry);
      } catch (error) {
        // Log handler errors to console to avoid losing the original log
        console.error(`Handler error: ${(error as Error).message}`);
      }
    }
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.INFO, message, context);
  }

  error(
    message: string,
    error?: Error,
    context?: Record<string, unknown>
  ): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  warning(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.WARNING, message, context);
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  critical(
    message: string,
    error?: Error,
    context?: Record<string, unknown>
  ): void {
    this.log(LogLevel.CRITICAL, message, context, error);
  }

  /**
   * Create child logger with additional context.
   */
  withContext(additionalContext: Record<string, unknown>): Logger {
    return new Logger(this.name, this.config, {
      ...this.context,
      ...additionalContext,
    });
  }

  /**
   * Timer for measuring async operation duration.
   */
  async timer<T>(
    operation: string,
    fn: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<T> {
    const start = process.hrtime.bigint();
    const location = captureSourceLocation(2);

    try {
      const result = await fn();
      const durationMs = Number(process.hrtime.bigint() - start) / 1_000_000;

      this.log(LogLevel.INFO, operation, { ...context, durationMs }, undefined, location);

      return result;
    } catch (error) {
      const durationMs = Number(process.hrtime.bigint() - start) / 1_000_000;

      this.log(
        LogLevel.ERROR,
        `${operation} failed`,
        { ...context, durationMs },
        error as Error,
        location
      );

      throw error;
    }
  }

  private getHostname(): string {
    try {
      return os.hostname();
    } catch {
      return 'unknown';
    }
  }
}

export function initialize(config: LogConfig): Logger {
  globalConfig = config;

  // Clear existing handlers
  handlers.length = 0;

  // Add console handler if enabled
  if (config.console.enabled) {
    handlers.push(
      new ConsoleHandler(config.console.format, config.console.colors ?? true)
    );
  }

  // Add file handler if enabled
  if (config.file?.enabled) {
    handlers.push(
      new RotatingFileHandler(
        config.file.path,
        config.file.maxSizeMB,
        config.file.maxBackupCount
      )
    );
  }

  return getLogger(config.serviceName);
}

export function getLogger(name: string): Logger {
  if (!globalConfig) {
    throw new Error('Logging not initialized. Call initialize() first.');
  }

  if (!loggers.has(name)) {
    loggers.set(name, new Logger(name, globalConfig));
  }

  return loggers.get(name)!;
}

export async function shutdown(): Promise<void> {
  // Flush and close all handlers
  await Promise.all(handlers.map((h) => h.flush()));
  await Promise.all(handlers.map((h) => h.close()));

  handlers.length = 0;
  loggers.clear();
  globalConfig = null;
}
