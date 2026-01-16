/**
 * Log formatters for different output formats.
 */

import { LogEntry } from './entry.js';

export interface Formatter {
  format(entry: LogEntry): string;
}

/**
 * JSON formatter - outputs structured JSON logs.
 */
export class JSONFormatter implements Formatter {
  format(entry: LogEntry): string {
    return JSON.stringify(entry);
  }
}

/**
 * Text formatter - outputs human-readable logs.
 */
export class TextFormatter implements Formatter {
  private readonly useColors: boolean;

  constructor(useColors: boolean = true) {
    this.useColors = useColors;
  }

  format(entry: LogEntry): string {
    const timestamp = entry.timestamp;
    const level = this.colorize(entry.level, this.getLevelColor(entry.level));
    const service = entry.service;
    const message = entry.message;

    let output = `[${timestamp}] [${level}] [${service}] ${message}`;

    // Add context if present
    if (entry.context && Object.keys(entry.context).length > 0) {
      const contextStr = Object.entries(entry.context)
        .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
        .join(' ');
      output += ` (${contextStr})`;
    }

    // Add exception if present
    if (entry.exception) {
      output += `\n  ${entry.exception.type}: ${entry.exception.message}`;
      if (entry.exception.stacktrace) {
        output += `\n${entry.exception.stacktrace}`;
      }
    }

    return output;
  }

  private colorize(text: string, color: string): string {
    if (!this.useColors) {
      return text;
    }
    return `${color}${text}\x1b[0m`;
  }

  private getLevelColor(level: string): string {
    switch (level) {
      case 'DEBUG':
        return '\x1b[36m'; // Cyan
      case 'INFO':
        return '\x1b[32m'; // Green
      case 'WARNING':
        return '\x1b[33m'; // Yellow
      case 'ERROR':
        return '\x1b[31m'; // Red
      case 'CRITICAL':
        return '\x1b[35m'; // Magenta
      default:
        return '';
    }
  }
}
