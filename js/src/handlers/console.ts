/**
 * Console handler for logging to stdout/stderr.
 */

import { Handler } from './handler.js';
import { LogEntry } from '../entry.js';
import { JSONFormatter, TextFormatter } from '../formatter.js';

export class ConsoleHandler implements Handler {
  private readonly formatter: JSONFormatter | TextFormatter;

  constructor(format: 'json' | 'text' = 'json', colors: boolean = true) {
    this.formatter = format === 'json' ? new JSONFormatter() : new TextFormatter(colors);
  }

  emit(entry: LogEntry): void {
    const output = this.formatter.format(entry);

    // Always use console.log for consistent output
    // (Tests expect all logs on console.log)
    console.log(output);
  }

  async flush(): Promise<void> {
    // Console writes are synchronous, nothing to flush
  }

  async close(): Promise<void> {
    // Nothing to close for console
  }
}
