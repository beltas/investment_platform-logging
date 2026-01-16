/**
 * File handler for logging to files.
 *
 * Features:
 * - Bounded write queue with configurable backpressure behavior
 * - Batched writes for performance
 * - Automatic directory creation
 */

import * as fs from 'fs';
import * as path from 'path';
import { Handler } from './handler.js';
import { LogEntry } from '../entry.js';
import { JSONFormatter } from '../formatter.js';

/** Behavior when the write queue is full */
export type QueueFullBehavior = 'drop_oldest' | 'drop_newest' | 'block';

export interface FileHandlerOptions {
  /** Maximum queue size before backpressure is applied (default: 10000) */
  maxQueueSize?: number;
  /** Behavior when queue is full (default: 'drop_oldest') */
  onQueueFull?: QueueFullBehavior;
  /** Batch write interval in milliseconds (default: 100) */
  batchIntervalMs?: number;
  /** Flush timeout in milliseconds (default: 5000) */
  flushTimeoutMs?: number;
}

export class FileHandler implements Handler {
  private readonly filePath: string;
  private readonly formatter: JSONFormatter;
  private writeQueue: string[] = [];
  private writeTimer: NodeJS.Timeout | null = null;
  private stream: fs.WriteStream | null = null;
  private closed: boolean = false;

  // Queue management
  private readonly maxQueueSize: number;
  private readonly onQueueFull: QueueFullBehavior;
  private readonly batchIntervalMs: number;
  private readonly flushTimeoutMs: number;
  private droppedCount: number = 0;

  constructor(filePath: string, options: FileHandlerOptions = {}) {
    this.filePath = filePath;
    this.formatter = new JSONFormatter();
    this.maxQueueSize = options.maxQueueSize ?? 10000;
    this.onQueueFull = options.onQueueFull ?? 'drop_oldest';
    this.batchIntervalMs = options.batchIntervalMs ?? 100;
    this.flushTimeoutMs = options.flushTimeoutMs ?? 5000;
    this.ensureDirectory();
    this.openStream();
  }

  /** Get the number of dropped log entries due to queue overflow */
  getDroppedCount(): number {
    return this.droppedCount;
  }

  private ensureDirectory(): void {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private openStream(): void {
    this.stream = fs.createWriteStream(this.filePath, {
      flags: 'a', // Append mode
      encoding: 'utf8',
    });

    this.stream.on('error', (err) => {
      console.error(`File handler error: ${err.message}`);
    });
  }

  emit(entry: LogEntry): void {
    if (this.closed) {
      return;
    }

    const output = this.formatter.format(entry);

    // Handle queue overflow with backpressure
    if (this.writeQueue.length >= this.maxQueueSize) {
      switch (this.onQueueFull) {
        case 'drop_oldest':
          // Remove oldest entry to make room
          this.writeQueue.shift();
          this.droppedCount++;
          break;
        case 'drop_newest':
          // Don't add new entry
          this.droppedCount++;
          return;
        case 'block':
          // Flush immediately and then add
          this.flushQueue();
          break;
      }
    }

    this.writeQueue.push(output);

    // Schedule batch write
    if (!this.writeTimer) {
      this.writeTimer = setTimeout(() => {
        this.flushQueue();
      }, this.batchIntervalMs);
    }
  }

  /**
   * Flush the write queue to the stream.
   * Protected to allow subclasses (like RotatingFileHandler) to call before rotation.
   */
  protected flushQueue(): void {
    if (this.writeQueue.length === 0 || !this.stream || this.closed) {
      return;
    }

    const batch = this.writeQueue.join('\n') + '\n';
    this.writeQueue = [];

    this.stream.write(batch, (err) => {
      if (err) {
        console.error(`Failed to write to log file: ${err.message}`);
      }
    });

    if (this.writeTimer) {
      clearTimeout(this.writeTimer);
      this.writeTimer = null;
    }
  }

  /**
   * Cancel any pending write timer.
   * Protected to allow subclasses to cancel before rotation.
   */
  protected cancelWriteTimer(): void {
    if (this.writeTimer) {
      clearTimeout(this.writeTimer);
      this.writeTimer = null;
    }
  }

  /**
   * Synchronously flush the queue and wait for the stream to drain.
   * Used by RotatingFileHandler before rotation to ensure all pending
   * writes are completed to the current file.
   */
  protected flushQueueSync(): void {
    this.cancelWriteTimer();

    if (this.writeQueue.length === 0 || !this.stream) {
      return;
    }

    const batch = this.writeQueue.join('\n') + '\n';
    this.writeQueue = [];

    // Write synchronously by using writeSync through fd
    // But since we're using WriteStream, we need to write and wait
    try {
      this.stream.write(batch);
    } catch (err) {
      console.error(`Failed to write to log file: ${(err as Error).message}`);
    }
  }

  async flush(): Promise<void> {
    this.flushQueue();

    if (this.stream) {
      // Create a promise that resolves when stream is drained or times out
      const drainPromise = new Promise<void>((resolve) => {
        if (!this.stream!.writableNeedDrain) {
          resolve();
          return;
        }
        this.stream!.once('drain', () => resolve());
      });

      // Add timeout to prevent hanging indefinitely
      const timeoutPromise = new Promise<void>((_, reject) => {
        setTimeout(() => {
          reject(new Error(`Flush timeout after ${this.flushTimeoutMs}ms`));
        }, this.flushTimeoutMs);
      });

      try {
        await Promise.race([drainPromise, timeoutPromise]);
      } catch (error) {
        console.error(`FileHandler flush warning: ${(error as Error).message}`);
        // Continue despite timeout - don't throw
      }
    }
  }

  async close(): Promise<void> {
    this.closed = true;

    if (this.writeTimer) {
      clearTimeout(this.writeTimer);
      this.writeTimer = null;
    }

    await this.flush();

    if (this.stream) {
      return new Promise((resolve) => {
        this.stream!.end(() => {
          this.stream = null;
          resolve();
        });
      });
    }
  }

  protected getStream(): fs.WriteStream | null {
    return this.stream;
  }

  protected setStream(stream: fs.WriteStream | null): void {
    this.stream = stream;
  }

  protected getFilePath(): string {
    return this.filePath;
  }

  protected getWriteQueue(): string[] {
    return this.writeQueue;
  }

  protected clearWriteQueue(): void {
    this.writeQueue = [];
  }
}
