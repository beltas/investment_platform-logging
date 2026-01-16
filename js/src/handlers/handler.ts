/**
 * Handler interface.
 */

import { LogEntry } from '../entry.js';

export interface Handler {
  emit(entry: LogEntry): void;
  flush(): Promise<void>;
  close(): Promise<void>;
}
