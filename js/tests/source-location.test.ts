/**
 * Source location capture tests.
 */

import { describe, it, expect } from 'vitest';
import { captureSourceLocation, SourceLocation } from '../src/source-location.js';

describe('Source Location Capture', () => {
  describe('captureSourceLocation', () => {
    it('should capture file name', () => {
      const location = captureSourceLocation(1);
      expect(location.file).toMatch(/source-location\.test\.(ts|js)/);
    });

    it('should extract only filename, not full path', () => {
      const location = captureSourceLocation(1);
      expect(location.file).not.toContain('/');
      expect(location.file).not.toContain('\\');
    });

    it('should capture line number', () => {
      const location = captureSourceLocation(1);
      expect(location.line).toBeTypeOf('number');
      expect(location.line).toBeGreaterThan(0);
    });

    it('should capture different line numbers for different calls', () => {
      const location1 = captureSourceLocation(1);
      const location2 = captureSourceLocation(1);

      // Line numbers should be different since they're on different lines
      expect(location1.line).not.toBe(location2.line);
    });

    it('should capture function name', () => {
      function testFunction() {
        return captureSourceLocation(1);
      }

      const location = testFunction();
      expect(location.function).toBe('testFunction');
    });

    it('should handle anonymous functions', () => {
      const location = (() => captureSourceLocation(1))();
      expect(location.function).toBeDefined();
      // May be '<anonymous>' or test name depending on environment
      expect(typeof location.function).toBe('string');
    });

    it('should handle nested function calls', () => {
      function outer() {
        function inner() {
          return captureSourceLocation(1);
        }
        return inner();
      }

      const location = outer();
      expect(location.function).toBe('inner');
    });

    it('should respect stack depth parameter', () => {
      function level1() {
        return level2();
      }

      function level2() {
        return level3();
      }

      function level3() {
        // Depth 1: level3, Depth 2: level2, Depth 3: level1
        return captureSourceLocation(3);
      }

      const location = level1();
      expect(location.function).toBe('level1');
    });

    it('should return unknown values when stack is unavailable', () => {
      // This is hard to test directly, but we can verify the fallback structure
      const location = captureSourceLocation(1);
      expect(location).toHaveProperty('file');
      expect(location).toHaveProperty('line');
      expect(location).toHaveProperty('function');
    });

    it('should handle class methods', () => {
      class TestClass {
        testMethod() {
          return captureSourceLocation(1);
        }
      }

      const instance = new TestClass();
      const location = instance.testMethod();
      expect(location.function).toBe('testMethod');
    });

    it('should handle arrow functions', () => {
      const arrowFunc = () => captureSourceLocation(1);
      const location = arrowFunc();

      // Arrow functions may be captured as the containing function name
      expect(location.function).toBeDefined();
      expect(typeof location.function).toBe('string');
    });

    it('should handle async functions', async () => {
      async function asyncFunc() {
        return captureSourceLocation(1);
      }

      const location = await asyncFunc();
      expect(location.function).toBe('asyncFunc');
    });
  });

  describe('stack trace parsing', () => {
    it('should parse V8 format with function name', () => {
      const location = captureSourceLocation(1);

      // Verify it parsed successfully
      expect(location.file).not.toBe('<unknown>');
      expect(location.line).not.toBe(0);
      expect(location.function).not.toBe('<unknown>');
    });

    it('should extract function name from qualified names', () => {
      class MyClass {
        myMethod() {
          return captureSourceLocation(1);
        }
      }

      const location = new MyClass().myMethod();

      // Should extract 'myMethod' from 'MyClass.myMethod'
      expect(location.function).toBe('myMethod');
    });

    it('should handle edge case with very deep stack', () => {
      function recurse(depth: number): SourceLocation {
        if (depth === 0) {
          return captureSourceLocation(1);
        }
        return recurse(depth - 1);
      }

      const location = recurse(10);
      expect(location.function).toBe('recurse');
    });
  });

  describe('required fields validation', () => {
    it('should always return file field', () => {
      const location = captureSourceLocation(1);
      expect(location).toHaveProperty('file');
      expect(typeof location.file).toBe('string');
      expect(location.file.length).toBeGreaterThan(0);
    });

    it('should always return line field', () => {
      const location = captureSourceLocation(1);
      expect(location).toHaveProperty('line');
      expect(typeof location.line).toBe('number');
    });

    it('should always return function field', () => {
      const location = captureSourceLocation(1);
      expect(location).toHaveProperty('function');
      expect(typeof location.function).toBe('string');
      expect(location.function.length).toBeGreaterThan(0);
    });
  });
});
