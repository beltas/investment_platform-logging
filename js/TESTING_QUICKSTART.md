# Testing Quick Start Guide

## TL;DR - Run the Tests

```bash
cd /home/beltas/investment_platform-logging/js

# Install dependencies
npm install

# Run tests
npm test

# Watch mode (auto-rerun on changes)
npm run test:watch

# With coverage report
npm run test:coverage
```

## What Gets Tested

| Feature | Test File | Status |
|---------|-----------|--------|
| Logger initialization & logging | `logger.test.ts` | ✅ Ready |
| Source location capture | `source-location.test.ts` | ✅ Ready |
| Configuration from env | `config.test.ts` | ✅ Ready |
| JSON formatting | `formatter.test.ts` | ✅ Ready |
| Express middleware | `express.test.ts` | ✅ Ready |
| Console handler | `handlers.test.ts` | ✅ Ready |
| File rotation | `rotation.test.ts` | ⏳ TODO |

## Test Command Reference

```bash
# Run all tests once (for CI/CD)
npm test

# Run tests in watch mode (for development)
npm run test:watch

# Run with coverage report (HTML + JSON + text)
npm run test:coverage

# Run specific test file
npm test logger.test.ts

# Run tests matching a pattern
npm test -- --grep "source location"

# Run in UI mode (interactive)
npx vitest --ui
```

## Expected Output

```
 ✓ tests/logger.test.ts (40+ tests)
 ✓ tests/config.test.ts (20+ tests)
 ✓ tests/source-location.test.ts (15+ tests)
 ✓ tests/formatter.test.ts (30+ tests)
 ✓ tests/express.test.ts (25+ tests)
 ✓ tests/handlers.test.ts (10+ tests)

 Test Files  6 passed (6)
      Tests  140+ passed (140+)
   Duration  < 1s
```

## Coverage Report

After running `npm run test:coverage`, open:

```
coverage/index.html
```

Target: >80% coverage on new code

## Key Test Features

### 1. Source Location Capture (REQUIRED)

Every log entry must have `file`, `line`, `function`:

```typescript
logger.info('test');
// Output includes:
// file: "myfile.ts"
// line: 42
// function: "myFunction"
```

**Tested in:** `source-location.test.ts` + every logger test

### 2. Context Inheritance

Child loggers inherit parent context:

```typescript
const parent = logger.withContext({ user: 'alice' });
const child = parent.withContext({ request: '123' });

child.info('message');
// Context: { user: 'alice', request: '123' }
```

**Tested in:** `logger.test.ts` - "context inheritance" group

### 3. Async Timer

Measures async operation duration:

```typescript
await logger.timer('operation', async () => {
  await doWork();
});
// Logs: { message: 'operation', durationMs: 123.45 }
```

**Tested in:** `logger.test.ts` - "timer functionality" group

### 4. Express Middleware

Automatic correlation IDs:

```typescript
app.use(loggingMiddleware());

app.get('/api', (req, res) => {
  const logger = getRequestLogger();
  logger.info('handling request');
  // Automatically has correlation_id, method, path
});
```

**Tested in:** `express.test.ts`

## Troubleshooting

### "Logging not initialized" Error

**Solution:** Ensure `initialize()` is called before `getLogger()`.

Tests do this in `beforeEach()`:

```typescript
beforeEach(() => {
  initialize(config);
});
```

### Tests Hang

**Solution:** Ensure `shutdown()` is called in `afterEach()`:

```typescript
afterEach(async () => {
  await shutdown();
});
```

### Import Errors

**Solution:** Use `.js` extensions in imports (even for TypeScript):

```typescript
// Correct
import { Logger } from '../src/logger.js';

// Wrong (may fail)
import { Logger } from '../src/logger';
```

### Timer Tests Flaky

**Solution:** Increase timeout in tests if CI is slow:

```typescript
await new Promise(resolve => setTimeout(resolve, 50)); // Increased from 10ms
```

## Next Steps

1. **Run tests locally:** `npm test`
2. **Check coverage:** `npm run test:coverage`
3. **Implement pending handlers:**
   - `src/handlers/file.ts`
   - `src/handlers/rotating.ts`
4. **Remove `.todo()` from rotation tests**
5. **Re-run tests:** `npm test`

## Documentation

- **Full test documentation:** `tests/README.md`
- **Test implementation summary:** `TEST_SUMMARY.md`
- **Design reference:** `../docs/DESIGN.md`
- **Use cases:** `../docs/USE_CASES.md`

## CI/CD Integration

Example GitHub Actions:

```yaml
- name: Install dependencies
  run: npm ci
  working-directory: js

- name: Run tests
  run: npm test
  working-directory: js

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: js/coverage/coverage-final.json
```

## Quick Test Examples

### Run specific test group

```bash
# Only logger tests
npm test logger.test.ts

# Only source location tests
npm test source-location.test.ts
```

### Run tests matching name

```bash
# All tests with "context" in the name
npm test -- --grep context

# All tests with "timer" in the name
npm test -- --grep timer
```

### Debug failing test

```bash
# Run in UI mode for interactive debugging
npx vitest --ui

# Or add console.log in test and run normally
npm test
```

## Test File Locations

```
js/
├── tests/
│   ├── logger.test.ts           # Core logger tests
│   ├── config.test.ts           # Configuration tests
│   ├── source-location.test.ts  # Source capture tests
│   ├── formatter.test.ts        # JSON formatter tests
│   ├── express.test.ts          # Express middleware tests
│   ├── handlers.test.ts         # Handler tests
│   ├── rotation.test.ts         # Rotation tests (TODO)
│   └── README.md                # Full documentation
├── vitest.config.ts             # Vitest configuration
├── package.json                 # Test scripts defined here
└── TEST_SUMMARY.md              # Implementation summary
```

## Success Criteria

- [ ] All tests pass: `npm test`
- [ ] Coverage >80%: `npm run test:coverage`
- [ ] No TypeScript errors: `npm run typecheck`
- [ ] No linting errors: `npm run lint`

---

**Ready to test?**

```bash
cd /home/beltas/investment_platform-logging/js && npm install && npm test
```
