/**
 * Source location capture for log entries.
 *
 * IMPORTANT: file, line, and function are REQUIRED in all log entries.
 */

export interface SourceLocation {
  file: string;
  line: number;
  function: string;
}

/**
 * Capture the source location of the calling code.
 *
 * @param stackDepth How many frames to skip (default 2 for direct caller)
 * @returns SourceLocation with file, line, and function name
 */
export function captureSourceLocation(stackDepth: number = 2): SourceLocation {
  const error = new Error();
  const stack = error.stack;

  if (!stack) {
    return {
      file: '<unknown>',
      line: 0,
      function: '<unknown>',
    };
  }

  const lines = stack.split('\n');
  // Skip "Error" line and specified number of frames
  const targetLine = lines[stackDepth + 1];

  if (!targetLine) {
    return {
      file: '<unknown>',
      line: 0,
      function: '<unknown>',
    };
  }

  return parseStackLine(targetLine);
}

/**
 * Parse a V8 stack trace line.
 */
function parseStackLine(line: string): SourceLocation {
  // Try: "at functionName (file:line:col)"
  const withFunction = /at\s+(\S+)\s+\((.+):(\d+):\d+\)/.exec(line);
  if (withFunction) {
    return {
      function: withFunction[1].split('.').pop() || withFunction[1],
      file: extractFilename(withFunction[2]),
      line: parseInt(withFunction[3], 10),
    };
  }

  // Try: "at file:line:col"
  const withoutFunction = /at\s+(.+):(\d+):\d+/.exec(line);
  if (withoutFunction) {
    return {
      function: '<anonymous>',
      file: extractFilename(withoutFunction[1]),
      line: parseInt(withoutFunction[2], 10),
    };
  }

  return {
    file: '<unknown>',
    line: 0,
    function: '<unknown>',
  };
}

function extractFilename(path: string): string {
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1] || path;
}
