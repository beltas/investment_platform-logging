/**
 * Log level definitions.
 */

export enum LogLevel {
  DEBUG = 10,
  INFO = 20,
  WARNING = 30,
  ERROR = 40,
  CRITICAL = 50,
}

export function levelToString(level: LogLevel): string {
  switch (level) {
    case LogLevel.DEBUG:
      return 'DEBUG';
    case LogLevel.INFO:
      return 'INFO';
    case LogLevel.WARNING:
      return 'WARNING';
    case LogLevel.ERROR:
      return 'ERROR';
    case LogLevel.CRITICAL:
      return 'CRITICAL';
    default:
      return 'UNKNOWN';
  }
}
