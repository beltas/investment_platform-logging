/**
 * Rotating file handler with size-based rotation.
 *
 * Uses synchronous file operations to guarantee no data loss during rotation.
 * Tracks file size incrementally for accurate rotation triggering.
 * Rotation occurs before a write would exceed maxSizeBytes, not after.
 */

import * as fs from 'fs';
import * as path from 'path';
import { Handler } from './handler.js';
import { LogEntry } from '../entry.js';
import { JSONFormatter } from '../formatter.js';

export class RotatingFileHandler implements Handler {
  private readonly filePath: string;
  private readonly maxSizeBytes: number;
  private readonly maxBackupCount: number;
  private currentSize: number = 0;
  private readonly formatter: JSONFormatter;
  private rotating: boolean = false;
  private fd: number | null = null;
  private closed: boolean = false;

  constructor(filePath: string, maxSizeMB: number, maxBackupCount: number) {
    this.filePath = filePath;
    this.maxSizeBytes = maxSizeMB * 1024 * 1024;
    this.maxBackupCount = maxBackupCount;
    this.formatter = new JSONFormatter();
    this.ensureDirectory();
    this.openFile();
    this.syncCurrentSize();
  }

  private ensureDirectory(): void {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private openFile(): void {
    try {
      // Open in append mode, create if doesn't exist
      this.fd = fs.openSync(this.filePath, 'a');
    } catch (err) {
      console.error(`Failed to open log file: ${(err as Error).message}`);
    }
  }

  private closeFile(): void {
    if (this.fd !== null) {
      try {
        fs.fsyncSync(this.fd);
        fs.closeSync(this.fd);
      } catch {
        // Ignore errors on close
      }
      this.fd = null;
    }
  }

  /**
   * Sync current size from filesystem (used on startup and after rotation).
   */
  private syncCurrentSize(): void {
    try {
      const stats = fs.statSync(this.filePath);
      this.currentSize = stats.size;
    } catch {
      this.currentSize = 0;
    }
  }

  emit(entry: LogEntry): void {
    if (this.closed || this.fd === null) {
      return;
    }

    // Calculate the byte size of this entry (including newline)
    const formatted = this.formatter.format(entry);
    const output = formatted + '\n';
    const entryBytes = Buffer.byteLength(output, 'utf8');

    // Check if rotation is needed BEFORE writing
    if (this.shouldRotate(entryBytes)) {
      this.rotate();
    }

    // Write the entry synchronously
    try {
      if (this.fd !== null) {
        fs.writeSync(this.fd, output, null, 'utf8');
        this.currentSize += entryBytes;
      }
    } catch (err) {
      console.error(`Failed to write log entry: ${(err as Error).message}`);
    }
  }

  private shouldRotate(entryBytes: number): boolean {
    return this.currentSize + entryBytes > this.maxSizeBytes;
  }

  private rotate(): void {
    // Prevent concurrent rotation attempts
    if (this.rotating) {
      return;
    }

    this.rotating = true;

    try {
      // Close current file (ensures all data is flushed to disk)
      this.closeFile();

      const basePath = this.filePath;

      // Delete oldest backup if it exists
      const oldestBackup = this.getBackupPath(this.maxBackupCount);
      if (fs.existsSync(oldestBackup)) {
        fs.unlinkSync(oldestBackup);
      }

      // Rename existing backups (in reverse order to avoid overwriting)
      for (let i = this.maxBackupCount - 1; i >= 1; i--) {
        const src = this.getBackupPath(i);
        const dst = this.getBackupPath(i + 1);

        if (fs.existsSync(src)) {
          fs.renameSync(src, dst);
        }
      }

      // Rename current log file to .1
      if (fs.existsSync(basePath)) {
        fs.renameSync(basePath, this.getBackupPath(1));
      }

      // Open new log file
      this.openFile();

      // Reset size counter
      this.currentSize = 0;

    } catch (err) {
      console.error(`Log rotation failed: ${(err as Error).message}`);
      // Try to reopen the original file to continue logging
      try {
        this.openFile();
        this.syncCurrentSize();
      } catch (reopenErr) {
        console.error(`Failed to reopen log file: ${(reopenErr as Error).message}`);
      }
    } finally {
      this.rotating = false;
    }
  }

  private getBackupPath(index: number): string {
    return `${this.filePath}.${index}`;
  }

  async flush(): Promise<void> {
    if (this.fd !== null) {
      try {
        fs.fsyncSync(this.fd);
      } catch {
        // Ignore errors
      }
    }
  }

  async close(): Promise<void> {
    this.closed = true;
    this.closeFile();
  }
}
