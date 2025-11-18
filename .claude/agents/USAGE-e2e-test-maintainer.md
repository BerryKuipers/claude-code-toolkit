# E2E Test Maintainer Agent - Usage Guide

## Quick Start

**Agent Name:** `e2e-test-maintainer`

**Purpose:** Autonomous E2E test maintenance - fixes test issues, reports code bugs

**Location:** `.claude-toolkit/.claude/agents/e2e-test-maintainer.md`

---

## When to Use This Agent

Use the E2E Test Maintainer agent when:

1. **E2E tests are failing** after code changes
2. **Tests are flaky** or unreliable
3. **PR requires green E2E checks** before merge
4. **New features need test coverage** verification
5. **Test patterns are outdated** (inline login, hardcoded waits, etc.)

---

## How to Invoke

### Via Natural Language (Recommended)

```
"Fix the failing E2E tests"
"Make the E2E tests pass"
"Update the E2E tests to use proper patterns"
"Check if E2E tests are reliable"
```

### Via Agent Name

```
@e2e-test-maintainer fix all failing E2E tests
```

### Via Conductor/Orchestrator

The conductor will automatically route E2E test maintenance tasks to this agent.

---

## What the Agent Does

### 1. Runs E2E Tests

```bash
npx playwright test --workers=1 --max-failures=1
```

### 2. Analyzes Failures

For each failure, classifies as:
- **Test Issue** (agent fixes) - outdated selectors, bad patterns, etc.
- **Code Bug** (agent reports) - backend errors, component issues, etc.

### 3. Fixes Test Issues Autonomously

- Updates outdated selectors
- Replaces inline login with `loginToApp()` helper
- Removes hardcoded `waitForTimeout()` calls
- Migrates to Page Object Models
- Uses test data factories instead of hardcoded values

### 4. Re-Runs Tests

Verifies fixes work by re-running tests.

### 5. Reports Results

Clear summary of:
- Test issues fixed
- Code bugs found (requires developer action)
- Tests now passing vs still failing

---

## Example Workflow

**User Request:**
```
"Fix the failing E2E tests"
```

**Agent Execution:**

1. **Run tests:**
   ```bash
   npx playwright test
   ```
   Output: 3 tests failing

2. **Analyze failures:**
   - `universe-selection.spec.ts`: Selector not found ✅ TEST ISSUE
   - `characters.spec.ts`: Inline login code ✅ TEST ISSUE
   - `locations.spec.ts`: Backend 500 error ❌ CODE BUG

3. **Fix test issues:**
   - Update selector in `universe-selection.spec.ts`
   - Replace inline login with `loginToApp()` in `characters.spec.ts`

4. **Re-run tests:**
   ```bash
   npx playwright test
   ```
   Output: 1 test failing (locations.spec.ts - code bug)

5. **Report results:**
   ```markdown
   ## E2E Test Maintenance - Code Bug Detected

   **Tests Fixed**: 2 files
   - Updated selector in universe-selection.spec.ts
   - Migrated to loginToApp() helper in characters.spec.ts

   **Code Bug Found**:
   - locations.spec.ts: Backend returns 500 on POST /api/locations
   - Error: "Cannot read property 'id' of undefined"
   - File: backend/src/routes/locations.ts:32

   **Tests Passing**: 2/3
   **Tests Blocked by Bug**: 1/3
   ```

---

## Best Practices the Agent Enforces

### 1. Authentication Pattern

**Before (Bad):**
```typescript
test('should do something', async ({ page }) => {
  await page.goto('/#/login');
  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'password');
  await page.click('button[type="submit"]');
  // Test logic...
});
```

**After (Good):**
```typescript
import { loginToApp } from './helpers/auth-helpers';

test.beforeEach(async ({ page }) => {
  await loginToApp(page); // Handles entire login flow
});

test('should do something', async ({ page }) => {
  // Test logic...
});
```

---

### 2. Page Object Models

**Before (Bad):**
```typescript
await page.goto('/#/characters');
await page.click('[data-testid="add-character-btn"]');
await page.fill('[data-testid="name-input"]', 'Test Character');
```

**After (Good):**
```typescript
import { CharactersPage, testCharacter } from './fixtures/test-helpers';

const charactersPage = new CharactersPage(page);
await charactersPage.goto();
await charactersPage.clickAddCharacter();
await charactersPage.fillCharacterForm(testCharacter);
```

---

### 3. Waiting Patterns

**Before (Bad):**
```typescript
await page.click('[data-testid="submit-btn"]');
await page.waitForTimeout(2000); // Flaky!
await expect(page.locator('[data-testid="success"]')).toBeVisible();
```

**After (Good):**
```typescript
await page.click('[data-testid="submit-btn"]');
// Playwright auto-waits for element (default timeout: 30s)
await expect(page.locator('[data-testid="success"]')).toBeVisible();
```

---

### 4. Selector Quality

**Before (Bad):**
```typescript
await page.click('.btn.btn-primary.mt-4'); // CSS classes change
await page.click('div > button:nth-child(3)'); // Structure-dependent
```

**After (Good):**
```typescript
await page.click('[data-testid="add-character-btn"]'); // Semantic
await page.click('button:has-text("Add Character")'); // Fallback
```

---

## Special Backend Configuration

**CRITICAL:** E2E tests require backend in test mode to avoid rate limiting.

**✅ Correct:**
```bash
# Terminal 1: Backend with E2E test mode (10,000 req/15min)
cd backend && npm run dev:e2e

# Terminal 2: Frontend
npm run dev

# Terminal 3: Run E2E tests
npx playwright test
```

**❌ Wrong:**
```bash
# Terminal 1: Normal backend (500 req/15min - will rate limit!)
cd backend && npm run dev
```

The agent will remind you if tests fail with 429 (rate limit) errors.

---

## Agent Output Examples

### Success (All Tests Pass)

```markdown
## E2E Test Maintenance - Complete ✅

**Tests Fixed**: 5 files
**Issues Resolved**:
- Updated 8 outdated selectors
- Replaced 3 inline login patterns with loginToApp() helper
- Removed 4 hardcoded waitForTimeout() calls
- Migrated 2 tests to use Page Object Models

**All E2E tests now pass:**
- e2e/universe-selection.spec.ts ✅
- e2e/characters.spec.ts ✅
- e2e/locations.spec.ts ✅
- e2e/story-creation.spec.ts ✅
- e2e/account-management.spec.ts ✅

**Next Steps**: Tests are reliable and follow best practices.
```

---

### Code Bugs Found

```markdown
## E2E Test Maintenance - Code Bugs Detected ❌

**Tests Fixed**: 3 files (test issues resolved)

**Remaining Failures (CODE BUGS)**:

1. **Character Creation API Fails**
   - Test: e2e/characters.spec.ts - "should create new character"
   - Error: POST /api/characters returns 500
   - Backend logs: TypeError: Cannot read property 'species' of undefined
   - File: backend/src/services/character.service.ts:78
   - **Action Required**: Fix character service validation logic

2. **Universe Selection Modal Not Appearing**
   - Test: e2e/universe-selection.spec.ts - "should show universe selection modal"
   - Error: Selector '[data-testid="universe-selection-modal"]' not found
   - Component: src/components/UniverseSelectionModal.tsx
   - **Action Required**: Modal may not be rendered when user has no active universe

**Tests Passing**: 13/15
**Tests Blocked by Bugs**: 2/15

**Next Steps**: Fix the above code bugs, then re-run E2E tests.
```

---

## Integration with Other Agents

The E2E Test Maintainer can be invoked by:

- **Conductor** - Routes E2E test maintenance tasks
- **QA Triage** - After manual QA finds issues, uses this agent to verify tests
- **Implementation** - After feature implementation, ensures tests pass

---

## Troubleshooting

### "Agent says backend is not running"

**Solution:**
```bash
# Terminal 1: Start backend in E2E mode
cd backend && npm run dev:e2e

# Terminal 2: Start frontend
npm run dev
```

---

### "Tests still failing after fixes"

**Likely Causes:**
1. Code bug (not test issue) - agent will report this
2. Backend rate limiting - use `npm run dev:e2e`
3. Database state issue - reset test database

---

### "Agent changed my source code"

**This should never happen.** The agent only modifies files in `e2e/` directory.

If source code was changed, report this as an agent bug.

---

## When NOT to Use This Agent

Don't use this agent for:

- ❌ Unit test failures (use different testing agent)
- ❌ Backend logic bugs (use implementation/debugging agent)
- ❌ Frontend component bugs (use UI/frontend agent)
- ❌ Creating new E2E tests (use implementation agent)

**This agent only fixes existing E2E tests, not code bugs.**

---

## Summary

**Agent:** `e2e-test-maintainer`

**Best For:**
- Fixing flaky E2E tests
- Updating outdated test patterns
- Ensuring tests follow best practices
- Distinguishing test issues from code bugs

**Workflow:**
Run → Analyze → Fix → Re-Run → Report

**Output:**
Clear report of test issues fixed and code bugs found

**Integration:**
Works with Conductor, QA Triage, Implementation agents
