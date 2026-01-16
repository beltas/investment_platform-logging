/**
 * Browser-specific logging implementation.
 *
 * Provides logging for React/Next.js frontend applications with:
 * - Console output only (no file logging in browser)
 * - Optional backend log endpoint
 * - Source location capture
 */

import { LogLevel, levelToString } from './level.js';
import { captureSourceLocation, SourceLocation } from './source-location.js';

export interface BrowserLogConfig {
  serviceName: string;
  environment: 'development' | 'staging' | 'production';
  version?: string;
  console: {
    enabled: boolean;
    format: 'json' | 'text';
  };
  endpoint?: string; // Optional: POST logs to backend
}

export class BrowserLogger {
  private readonly name: string;
  private readonly config: BrowserLogConfig;
  private readonly context: Record<string, unknown>;

  constructor(
    name: string,
    config: BrowserLogConfig,
    context: Record<string, unknown> = {}
  ) {
    this.name = name;
    this.config = config;
    this.context = context;
  }

  private log(
    level: LogLevel,
    message: string,
    context: Record<string, unknown> = {},
    error?: Error,
    location?: SourceLocation
  ): void {
    const source = location || captureSourceLocation(3);

    const entry = {
      timestamp: new Date().toISOString(),
      level: levelToString(level),
      message,
      service: this.config.serviceName,
      environment: this.config.environment,
      version: this.config.version || '0.0.0',
      loggerName: this.name,
      file: source.file,
      line: source.line,
      function: source.function,
      context: { ...this.context, ...context },
      exception: error
        ? {
            type: error.constructor.name,
            message: error.message,
            stacktrace: error.stack || '',
          }
        : undefined,
    };

    // Console output
    if (this.config.console.enabled) {
      const consoleMethod =
        level >= LogLevel.ERROR
          ? console.error
          : level >= LogLevel.WARNING
          ? console.warn
          : console.log;

      if (this.config.console.format === 'json') {
        consoleMethod(JSON.stringify(entry));
      } else {
        consoleMethod(
          `[${entry.level}] [${entry.service}] ${entry.message}`,
          entry.context
        );
      }
    }

    // Send to backend endpoint if configured
    if (this.config.endpoint) {
      this.sendToBackend(entry);
    }
  }

  private sendToBackend(entry: Record<string, unknown>): void {
    if (!this.config.endpoint) return;

    // Use sendBeacon for reliability (doesn't block page unload)
    if (navigator.sendBeacon) {
      navigator.sendBeacon(
        this.config.endpoint,
        JSON.stringify(entry)
      );
    } else {
      // Fallback to fetch
      fetch(this.config.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
        keepalive: true,
      }).catch(() => {
        // Ignore errors - logging should never fail the app
      });
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

  withContext(additionalContext: Record<string, unknown>): BrowserLogger {
    return new BrowserLogger(this.name, this.config, {
      ...this.context,
      ...additionalContext,
    });
  }

  async timer<T>(
    operation: string,
    fn: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<T> {
    const start = performance.now();
    const location = captureSourceLocation(2);

    try {
      const result = await fn();
      const durationMs = performance.now() - start;

      this.log(
        LogLevel.INFO,
        operation,
        { ...context, durationMs },
        undefined,
        location
      );

      return result;
    } catch (error) {
      const durationMs = performance.now() - start;

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
}

let browserLogger: BrowserLogger | null = null;

export function initializeBrowserLogger(config: BrowserLogConfig): BrowserLogger {
  browserLogger = new BrowserLogger(config.serviceName, config);
  return browserLogger;
}

export function getBrowserLogger(name?: string): BrowserLogger {
  if (!browserLogger) {
    throw new Error('Browser logger not initialized. Call initializeBrowserLogger() first.');
  }

  if (name && name !== browserLogger['name']) {
    return new BrowserLogger(name, browserLogger['config']);
  }

  return browserLogger;
}
