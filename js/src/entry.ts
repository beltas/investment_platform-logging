/**
 * Log entry structure.
 */

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  service: string;
  environment: string;
  version: string;
  host: string;
  loggerName: string;
  // REQUIRED source location fields
  file: string;
  line: number;
  function: string;
  // Optional fields
  correlationId?: string;
  userId?: string;
  traceId?: string;
  spanId?: string;
  context?: Record<string, unknown>;
  durationMs?: number;
  exception?: {
    type: string;
    message: string;
    stacktrace: string;
  };
}
