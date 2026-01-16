/**
 * Agora Trading Platform Logging Library - JavaScript/TypeScript Implementation
 *
 * A unified logging solution with:
 * - Structured JSON logging
 * - Automatic source location capture (file, line, function - REQUIRED)
 * - Context injection and inheritance
 * - Dual output (console + file)
 * - Size-based file rotation
 * - Async logging
 */

export { LogConfig, ConsoleConfig, FileConfig, configFromEnv } from './config.js';
export { LogLevel } from './level.js';
export { Logger, getLogger, initialize, shutdown } from './logger.js';
export { LogEntry } from './entry.js';
export type { SourceLocation } from './source-location.js';
