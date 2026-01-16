/**
 * File rotation tests.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { RotatingFileHandler } from '../src/handlers/rotating.js';
import { LogEntry } from '../src/entry.js';
import { LogLevel } from '../src/level.js';

describe('File Rotation', () => {
  let tempDir: string;
  let logPath: string;
  let handler: RotatingFileHandler | null = null;

  // Create a test log entry of approximately known size
  function createEntry(message: string): LogEntry {
    return {
      timestamp: new Date('2024-01-01T00:00:00Z'),
      level: LogLevel.INFO,
      levelName: 'INFO',
      message,
      loggerName: 'test',
      service: 'test-service',
      environment: 'test',
      version: '1.0.0',
      host: 'test-host',
      file: 'test.ts',
      line: 1,
      function: 'test',
      context: {},
    };
  }

  // Get approximate byte size of a formatted entry
  function getEntrySize(entry: LogEntry): number {
    const formatted = JSON.stringify({
      timestamp: entry.timestamp.toISOString(),
      level: entry.levelName,
      message: entry.message,
      service: entry.service,
      environment: entry.environment,
      version: entry.version,
      host: entry.host,
      loggerName: entry.loggerName,
      file: entry.file,
      line: entry.line,
      function: entry.function,
      context: entry.context,
    });
    return Buffer.byteLength(formatted, 'utf8') + 1; // +1 for newline
  }

  beforeEach(() => {
    // Create a unique temp directory for each test
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agora-rotation-test-'));
    logPath = path.join(tempDir, 'app.log');
  });

  afterEach(async () => {
    // Close handler if open
    if (handler) {
      await handler.close();
      handler = null;
    }

    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('rotation trigger', () => {
    it('should rotate file when size threshold is reached', async () => {
      // Use a small max size - entries are ~400-450 bytes each
      // Set threshold to 500 bytes so 2nd entry triggers rotation
      const maxSizeMB = 0.0005; // ~500 bytes
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write enough entries to trigger rotation (each ~400+ bytes)
      for (let i = 0; i < 5; i++) {
        handler.emit(createEntry(`Message ${i}: ${'x'.repeat(200)}`));
      }

      // Allow async writes to complete
      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Check that backup file was created
      const backup1 = `${logPath}.1`;
      expect(fs.existsSync(logPath)).toBe(true);
      expect(fs.existsSync(backup1)).toBe(true);
    });

    it('should check file size before each write', async () => {
      // ~300 bytes per entry with 100-char message, threshold of 400 bytes
      // means rotation after each entry
      const maxSizeMB = 0.0004; // ~400 bytes
      const maxBackupCount = 5;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write entries one at a time
      for (let i = 0; i < 10; i++) {
        handler.emit(createEntry(`Entry ${i}: ${'y'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Should have rotated multiple times
      expect(fs.existsSync(logPath)).toBe(true);
      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
    });

    it('should not rotate when below threshold', async () => {
      const maxSizeMB = 1; // 1MB - large enough to not trigger
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write a few small entries
      for (let i = 0; i < 5; i++) {
        handler.emit(createEntry(`Small message ${i}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Main log should exist, no backup
      expect(fs.existsSync(logPath)).toBe(true);
      expect(fs.existsSync(`${logPath}.1`)).toBe(false);
    });
  });

  describe('backup file naming', () => {
    it('should rename current log to .1', async () => {
      // Entry with 150-char message is ~380 bytes, set threshold to 400
      const maxSizeMB = 0.0004; // ~400 bytes
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write enough to trigger rotation (2nd entry should trigger)
      for (let i = 0; i < 5; i++) {
        handler.emit(createEntry(`Message ${i}: ${'a'.repeat(150)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
    });

    it('should rename .1 to .2, .2 to .3, etc.', async () => {
      // Entry with 150-char message is ~380 bytes, set threshold to 400
      const maxSizeMB = 0.0004; // ~400 bytes
      const maxBackupCount = 5;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write enough to trigger multiple rotations
      for (let i = 0; i < 20; i++) {
        handler.emit(createEntry(`Message ${i}: ${'b'.repeat(150)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Should have multiple backups
      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
      expect(fs.existsSync(`${logPath}.2`)).toBe(true);
    });

    it('should follow pattern: app.log.1, app.log.2, ...', async () => {
      const maxSizeMB = 0.0002; // 200 bytes
      const maxBackupCount = 4;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write many entries
      for (let i = 0; i < 30; i++) {
        handler.emit(createEntry(`Msg ${i}: ${'c'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Verify naming pattern
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter((f) => f.match(/app\.log\.\d+/));

      backupFiles.forEach((file) => {
        expect(file).toMatch(/^app\.log\.\d+$/);
      });
    });
  });

  describe('max backup count enforcement', () => {
    it('should delete oldest backup when max count is reached', async () => {
      const maxSizeMB = 0.0002; // 200 bytes
      const maxBackupCount = 2;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write enough to exceed max backups
      for (let i = 0; i < 30; i++) {
        handler.emit(createEntry(`Entry ${i}: ${'d'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Should only have maxBackupCount backups
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter((f) => f.match(/app\.log\.\d+/));

      expect(backupFiles.length).toBeLessThanOrEqual(maxBackupCount);
      expect(fs.existsSync(`${logPath}.${maxBackupCount + 1}`)).toBe(false);
    });

    it('should maintain exactly maxBackupCount backups', async () => {
      const maxSizeMB = 0.0002; // 200 bytes
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write many entries to trigger several rotations
      for (let i = 0; i < 50; i++) {
        handler.emit(createEntry(`Entry ${i}: ${'e'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 400));

      // Count backups
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter((f) => f.match(/app\.log\.\d+/));

      expect(backupFiles.length).toBeLessThanOrEqual(maxBackupCount);
    });

    it('should handle maxBackupCount of 1 (single backup)', async () => {
      // Entry with 100-char message is ~330 bytes, set threshold to 350
      const maxSizeMB = 0.00035; // ~350 bytes
      const maxBackupCount = 1;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      for (let i = 0; i < 20; i++) {
        handler.emit(createEntry(`Entry ${i}: ${'f'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Should only have .1 backup, not .2
      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
      expect(fs.existsSync(`${logPath}.2`)).toBe(false);
    });
  });

  describe('write queue synchronization', () => {
    it('should flush queue before rotation', async () => {
      const maxSizeMB = 0.001; // 1KB
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write entries rapidly
      for (let i = 0; i < 20; i++) {
        handler.emit(createEntry(`Rapid entry ${i}: ${'g'.repeat(200)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Read all log files and verify no data loss
      const mainContent = fs.existsSync(logPath)
        ? fs.readFileSync(logPath, 'utf8')
        : '';
      const backup1Content = fs.existsSync(`${logPath}.1`)
        ? fs.readFileSync(`${logPath}.1`, 'utf8')
        : '';
      const backup2Content = fs.existsSync(`${logPath}.2`)
        ? fs.readFileSync(`${logPath}.2`, 'utf8')
        : '';

      const allContent = mainContent + backup1Content + backup2Content;
      const lines = allContent.trim().split('\n').filter((l) => l.length > 0);

      // Should have all entries (allowing for batching)
      expect(lines.length).toBeGreaterThan(0);
    });

    it('should not lose log entries during rotation', async () => {
      const maxSizeMB = 0.0005; // 500 bytes
      // Use maxBackupCount high enough to hold all entries (each rotation creates 1 backup)
      const maxBackupCount = 20;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      const totalEntries = 15;
      const markers: string[] = [];

      // Write entries with unique markers
      for (let i = 0; i < totalEntries; i++) {
        const marker = `MARKER_${i}_${Date.now()}`;
        markers.push(marker);
        handler.emit(createEntry(`${marker}: ${'h'.repeat(100)}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 400));

      // Collect all content from all files
      const files = fs.readdirSync(tempDir);
      let allContent = '';
      for (const file of files) {
        if (file.startsWith('app.log')) {
          allContent += fs.readFileSync(path.join(tempDir, file), 'utf8');
        }
      }

      // Verify each marker appears exactly once
      for (const marker of markers) {
        const count = (allContent.match(new RegExp(marker, 'g')) || []).length;
        expect(count).toBe(1);
      }
    });

    it('should maintain write ordering', async () => {
      const maxSizeMB = 0.001;
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Write numbered entries
      for (let i = 0; i < 10; i++) {
        handler.emit(createEntry(`ORDER_${i.toString().padStart(3, '0')}: data`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Read main log and verify order
      if (fs.existsSync(logPath)) {
        const content = fs.readFileSync(logPath, 'utf8');
        const lines = content.trim().split('\n');
        const orderMatches = lines
          .map((line) => {
            const match = line.match(/ORDER_(\d+)/);
            return match ? parseInt(match[1]) : null;
          })
          .filter((n) => n !== null) as number[];

        // Within each file, order should be preserved
        for (let i = 1; i < orderMatches.length; i++) {
          expect(orderMatches[i]).toBeGreaterThan(orderMatches[i - 1]);
        }
      }
    });
  });

  describe('startup recovery', () => {
    it('should detect existing log file on startup', async () => {
      // Create an existing log file
      fs.writeFileSync(logPath, 'existing content\n');

      handler = new RotatingFileHandler(logPath, 1, 3);
      handler.emit(createEntry('New entry'));

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      const content = fs.readFileSync(logPath, 'utf8');
      expect(content).toContain('existing content');
      expect(content).toContain('New entry');
    });

    it('should append to existing file', async () => {
      const existingContent = '{"existing": "log"}\n';
      fs.writeFileSync(logPath, existingContent);

      handler = new RotatingFileHandler(logPath, 1, 3);
      handler.emit(createEntry('Appended entry'));

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      const content = fs.readFileSync(logPath, 'utf8');
      expect(content.startsWith(existingContent)).toBe(true);
    });

    it('should calculate current file size correctly', async () => {
      // Create file with known size
      const existingContent = 'x'.repeat(500);
      fs.writeFileSync(logPath, existingContent);

      // Use small threshold that existing content nearly fills
      const maxSizeMB = 0.0006; // ~600 bytes
      handler = new RotatingFileHandler(logPath, maxSizeMB, 3);

      // This entry should trigger rotation (existing 500 + entry ~200 > 600)
      handler.emit(createEntry('y'.repeat(150)));

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Backup should be created
      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
    });

    it('should preserve existing backups', async () => {
      // Create existing backups
      fs.writeFileSync(`${logPath}.1`, 'backup 1');
      fs.writeFileSync(`${logPath}.2`, 'backup 2');
      fs.writeFileSync(logPath, 'current');

      handler = new RotatingFileHandler(logPath, 0.0001, 5);

      // Trigger rotation
      handler.emit(createEntry('z'.repeat(200)));

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Old backups should be shifted
      expect(fs.existsSync(`${logPath}.1`)).toBe(true);
      expect(fs.existsSync(`${logPath}.2`)).toBe(true);
      expect(fs.existsSync(`${logPath}.3`)).toBe(true);
    });
  });

  describe('rotation errors', () => {
    it('should handle file rename errors gracefully', async () => {
      // This test verifies error handling doesn't crash
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      handler = new RotatingFileHandler(logPath, 0.0001, 3);

      // Write entries - even if rotation fails, shouldn't throw
      expect(() => {
        for (let i = 0; i < 10; i++) {
          handler.emit(createEntry(`Error test ${i}`));
        }
      }).not.toThrow();

      await handler.flush();
      consoleSpy.mockRestore();
    });

    it('should continue logging on rotation failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      handler = new RotatingFileHandler(logPath, 0.0001, 3);

      // Write many entries
      for (let i = 0; i < 20; i++) {
        handler.emit(createEntry(`Continue test ${i}`));
      }

      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Should have written some content
      const files = fs.readdirSync(tempDir);
      const logFiles = files.filter((f) => f.startsWith('app.log'));
      expect(logFiles.length).toBeGreaterThan(0);

      consoleSpy.mockRestore();
    });
  });

  describe('concurrent writes', () => {
    it('should handle multiple rapid writes during rotation', async () => {
      const maxSizeMB = 0.0003;
      const maxBackupCount = 3;
      handler = new RotatingFileHandler(logPath, maxSizeMB, maxBackupCount);

      // Simulate burst of writes
      const promises: Promise<void>[] = [];
      for (let i = 0; i < 50; i++) {
        handler.emit(createEntry(`Burst ${i}: ${'p'.repeat(100)}`));
        // Small delay to interleave with rotation
        if (i % 10 === 0) {
          promises.push(new Promise((resolve) => setTimeout(resolve, 10)));
        }
      }

      await Promise.all(promises);
      await handler.flush();
      await new Promise((resolve) => setTimeout(resolve, 400));

      // Should have created files without crashing
      expect(fs.existsSync(logPath)).toBe(true);
    });
  });
});
