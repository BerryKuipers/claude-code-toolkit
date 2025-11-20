---
name: fix-e2e-tests
description: Systematic E2E test fixing workflow with parallel agents, MCP tools, and automated failure tracking
---

# E2E Test Fixing Workflow (Modern)

Systematically fix E2E test failures using automated scripts, MCP tools, and parallel agent execution.

## Overview

This workflow integrates:
- ✅ `run-failed-tests.mjs` - Run and track failing tests from `failed-tests.json`
- ✅ `run-iterative.mjs` - Iterative test runner with flaky test detection
- ✅ Playwright MCP - Browser automation and debugging
- ✅ Jam MCP - Visual bug reporting with screenshots
- ✅ Parallel agents - Fix multiple test files concurrently
- ✅ TodoWrite - Track progress across all test fixes

---

## Phase 0: Environment Setup

### Check E2E Scripts Availability

```bash
# Verify scripts exist
ls -la scripts/run-failed-tests.mjs scripts/run-iterative.mjs

# If missing, copy from toolkit templates
cp .claude-toolkit/templates/e2e-scripts/*.mjs scripts/
chmod +x scripts/*.mjs
```

### Start Backend & Frontend

```bash
# Terminal 1: Backend in E2E mode (10,000 req/15min)
cd backend && npm run dev:e2e

# Terminal 2: Frontend
npm run dev

# Verify backend is in test mode
curl http://localhost:3000/health | grep -i "test"
```

---

## Phase 1: Analyze Failed Tests

### Load Failed Tests Inventory

```bash
# Check how many tests are tracked as failing
cat e2e/failed-tests.json | jq '.tests | length'

# Show test breakdown by file
cat e2e/failed-tests.json | jq -r '.tests[] | .file' | sort | uniq -c
```

**Create initial todo list:**

```javascript
[
  { content: "Load and analyze failed tests inventory", status: "in_progress", activeForm: "Loading failed tests" },
  { content: "Group tests by file for parallel execution", status: "pending", activeForm: "Grouping tests" },
  { content: "Launch parallel agents for test suites", status: "pending", activeForm: "Launching agents" },
  { content: "Monitor progress and consolidate results", status: "pending", activeForm: "Monitoring progress" },
  { content: "Generate summary report", status: "pending", activeForm: "Generating report" }
]
```

### Group Tests by File

**Analyze failed tests and group by suite:**

```bash
# Get unique test files with failure counts
cat e2e/failed-tests.json | jq -r '.tests[] | .file' | sort | uniq -c | sort -rn
```

**Example output:**
```
15 e2e/api-smoke-test.spec.ts
12 e2e/account-management.spec.ts
 8 e2e/universe-settings.spec.ts
 5 e2e/story-creation.spec.ts
 ...
```

**Create execution plan:**
1. High-count suites → Parallel agents
2. Low-count suites → Sequential batch
3. Single-test files → Run together at end

---

## Phase 2: Parallel Agent Execution

### Strategy: Divide & Conquer

**For each test suite with 5+ failures:**
- Launch dedicated agent
- Agent fixes that suite autonomously
- Agents work in parallel on different files

**User confirmation required:**

```markdown
## Execution Plan

### Parallel Execution (High Priority)
- **Agent 1:** e2e/api-smoke-test.spec.ts (15 failures)
- **Agent 2:** e2e/account-management.spec.ts (12 failures)
- **Agent 3:** e2e/universe-settings.spec.ts (8 failures)

### Sequential Batch (Medium Priority)
- e2e/story-creation.spec.ts (5 failures)
- e2e/locations.spec.ts (2 failures)

### Quick Fixes (Low Priority)
- Remaining single-test failures (run together)

Proceed with parallel agent launch?
```

### Launch Parallel Agents

**For each high-priority suite, launch agent:**

> I need an agent to fix ALL failing tests in `e2e/api-smoke-test.spec.ts` using the run-failed-tests.mjs script.
>
> **Test Suite:** `e2e/api-smoke-test.spec.ts`
> **Failing Tests:** 15
>
> **Workflow:**
> 1. Run tests from failed-tests.json for this file using:
>    ```bash
>    node scripts/run-failed-tests.mjs
>    ```
> 2. For each failing test:
>    - Analyze error output
>    - Use Playwright MCP to debug if needed:
>      - `playwright_screenshot` for visual inspection
>      - `playwright_evaluate` for state checking
>    - Fix the issue (test OR backend)
>    - Run test again to verify
>    - Commit the fix
> 3. Use TodoWrite to track each test fix
> 4. Report back when suite is green
>
> **Stay on current branch during entire execution.**

**Repeat for each parallel agent (different suite).**

---

## Phase 3: Agent Workflows (Per Suite)

**Each agent follows this autonomous workflow:**

### 3.1 Initial Run

```bash
# Run only failing tests for this suite
node scripts/run-failed-tests.mjs
```

**Parse output:**
- Which tests are still failing?
- What are the error messages?
- Are there patterns (common selectors, API issues)?

### 3.2 Fix Loop (Per Test)

**For EACH failing test:**

#### Step 1: Analyze Error

**Common error types:**
1. **Selector Issues** (Strict mode violations)
2. **Click Intercepted** (Overlays, modals)
3. **API/Backend Issues** (500 errors, cascade deletes)
4. **Timing Issues** (Race conditions)
5. **Data Issues** (Missing test data)

#### Step 2: Debug with MCP (if needed)

**Use Playwright MCP for complex failures:**

```typescript
// Take screenshot of current state
playwright_screenshot({ name: "test-failure-state" })

// Check element visibility
playwright_evaluate({
  expression: "document.querySelector('[data-testid=\"target\"]') ? 'visible' : 'missing'"
})

// Get console errors
playwright_evaluate({ expression: "console.log(window.lastError)" })
```

#### Step 3: Apply Fix

**Fix categories:**

**A. Selector Fixes:**
```typescript
// ❌ Before: Non-unique selector
await page.locator('.button').click();

// ✅ After: Use data-testid
await page.getByTestId('submit-button').click();

// OR use nth() if multiple valid
await page.locator('.item').nth(0).click();
```

**B. Click Intercepted Fixes:**
```typescript
// ❌ Before: Blocked by overlay
await button.click();

// ✅ After: Force click through overlay
await button.click({ force: true });

// OR wait for overlay to disappear
await page.getByTestId('loading-overlay').waitFor({ state: 'hidden' });
await button.click();
```

**C. Backend Fixes:**
```typescript
// Fix cascade delete in service
async deleteCharacter(id: string, universeId: string) {
  // Ensure ALL related entities are soft-deleted
  await this.relationshipsRepo.softDeleteByCharacterId(id, universeId);
  await this.traitsRepo.softDeleteByCharacterId(id, universeId);
  await this.characterRepo.softDelete(id, universeId);
}
```

**D. Timing Fixes:**
```typescript
// ❌ Before: Race condition
await button.click();
expect(result).toBeTruthy();

// ✅ After: Wait for result
await button.click();
await expect(page.getByTestId('result')).toBeVisible();
```

#### Step 4: Verify Fix

```bash
# Run just this test
npx playwright test e2e/suite.spec.ts -g "test title" --project=chromium
```

**If passing:**
- ✅ Mark todo as completed
- Commit the fix
- Move to next test

**If still failing:**
- Analyze new error
- Try alternative fix
- Use Playwright MCP for deeper debugging

#### Step 5: Commit Fix

```bash
git add {modified-files}
git commit -m "fix(e2e): {test-name} - {brief-description}

Fixes:
- {issue-description}
- {technical-fix}

Test: e2e/{suite}.spec.ts -g \"{test-title}\"
"
```

### 3.3 Suite Completion

**When all tests in suite pass:**

```bash
# Verify entire suite is green
npx playwright test e2e/{suite}.spec.ts --project=chromium

# If all pass:
✅ Suite complete
```

**Report back to main workflow:**
```markdown
## Suite Fixed: e2e/api-smoke-test.spec.ts

**Tests Fixed:** 15/15
**Commits:** 15
**Time:** ~45 minutes

**Common Issues:**
- 8 tests: Selector issues (fixed with data-testid)
- 4 tests: Click intercepted (added force: true)
- 2 tests: Backend cascade delete (fixed service layer)
- 1 test: Timing issue (added proper waits)

**All tests now passing ✅**
```

---

## Phase 4: Iterative Testing (Flaky Test Detection)

### Use run-iterative.mjs for Stability

**After all agents complete, verify stability:**

```bash
# Run iterative test to detect flaky tests
PW_PROJECT=chromium PW_MAX_ATTEMPTS=5 node scripts/run-iterative.mjs
```

**This script:**
1. Runs full suite
2. If any test fails, reruns it immediately
3. If passes on rerun → Flaky test (logs it)
4. If fails on rerun → Real failure (exits)
5. Repeats for max 5 attempts

**If flaky tests found:**
- Investigate why (timing, race conditions)
- Add proper waits/assertions
- Commit fix

---

## Phase 5: Update Failed Tests Tracking

### Sync failed-tests.json

```bash
# Run failed tests script one more time to update JSON
node scripts/run-failed-tests.mjs

# Check remaining failures
cat e2e/failed-tests.json | jq '.tests | length'

# If 0:
✅ All tests fixed!

# If > 0:
⚠️  Some tests still failing - review and continue
```

---

## Phase 6: Visual Bug Reporting (Optional)

### Use Jam MCP for Complex Bugs

**For tests that need visual documentation:**

```typescript
// Create Jam report with screenshots
jam_create({
  title: "E2E Test Failure: Character deletion cascade issue",
  description: "Characters not being fully deleted - related entities remain",
  url: "http://localhost:5173/characters",
  attachScreenshot: true
})

// Search existing Jams for similar issues
jam_search({ query: "cascade delete" })
```

---

## Common Fix Patterns

### 1. Strict Mode Violations

**Error:** `locator resolved to 3 elements`

**Fix:**
```typescript
// Option A: Use data-testid (preferred)
await page.getByTestId('unique-id').click();

// Option B: Use nth() for specific element
await page.locator('.button').nth(0).click();

// Option C: Use more specific selector
await page.locator('.modal .submit-button').click();
```

### 2. Click Intercepted

**Error:** `<div class="overlay"> intercepts pointer events`

**Fix:**
```typescript
// Option A: Force click
await button.click({ force: true });

// Option B: Wait for overlay to disappear
await page.getByTestId('overlay').waitFor({ state: 'hidden' });
await button.click();

// Option C: Close overlay first
await page.getByTestId('overlay-close').click();
await button.click();
```

### 3. Backend Cascade Delete

**Error:** `500 Internal Server Error` when deleting

**Fix (Service Layer):**
```typescript
async deleteCharacter(id: string, universeId: string) {
  // Delete in correct order (children first)
  await this.traitsRepo.softDeleteByCharacterId(id, universeId);
  await this.relationshipsRepo.softDeleteByCharacterId(id, universeId);
  await this.notesRepo.softDeleteByCharacterId(id, universeId);
  await this.characterRepo.softDelete(id, universeId);

  // Verify cascade worked
  const remaining = await this.characterRepo.findById(id, universeId);
  if (remaining && !remaining.deletedAt) {
    throw new Error('Cascade delete failed');
  }
}
```

### 4. Rate Limiting

**Error:** `429 Too Many Requests`

**Already Fixed:** `npm run dev:e2e` sets `NODE_ENV=test` (10,000 req/15min)

**Verify:**
```bash
curl http://localhost:3000/health | jq '.environment'
# Should show: "test"
```

### 5. API Response Mismatch

**Error:** Test expects data but receives `null`

**Fix:**
```typescript
// ❌ Before: Test uses stale props
expect(character.name).toBe('Test');

// ✅ After: Fetch fresh data from API
const response = await fetch('/api/characters/123');
const character = await response.json();
expect(character.name).toBe('Test');
```

### 6. Timing/Race Conditions

**Error:** Element not ready when test runs

**Fix:**
```typescript
// ❌ Before: No wait
await button.click();
expect(result).toBeTruthy();

// ✅ After: Wait for state change
await button.click();
await expect(page.getByTestId('result')).toBeVisible();
await expect(page.getByTestId('result')).toContainText('Success');
```

---

## Guidelines

### Code Quality
- ✅ Fix root causes, not symptoms
- ✅ Prefer backend fixes over test workarounds
- ✅ Keep selector changes minimal and specific
- ✅ Add data-testid attributes when missing
- ❌ Don't over-engineer tests
- ❌ Don't add unnecessary delays/waits

### Git Hygiene
- ✅ Commit after each test fix (atomic commits)
- ✅ Use descriptive commit messages
- ✅ Document non-obvious fixes
- ✅ Stay on same branch throughout
- ❌ Don't batch commits
- ❌ Don't push until full suite passes

### Agent Coordination
- ✅ Use TodoWrite to track progress
- ✅ Agents work on different files (no conflicts)
- ✅ Report back when suite complete
- ✅ Share common fix patterns
- ❌ Don't work on same file in parallel

---

## Completion Checklist

**Before marking complete:**

- [ ] All tests in failed-tests.json are passing
- [ ] `node scripts/run-failed-tests.mjs` shows 0 remaining failures
- [ ] Iterative runner passes (no flaky tests)
- [ ] Full suite runs clean: `npx playwright test`
- [ ] All fixes committed with descriptive messages
- [ ] No console errors during test runs
- [ ] Backend logs show no errors
- [ ] failed-tests.json is empty or removed

---

## Example Usage

```bash
# User runs command
/fix-e2e-tests

# Agent loads failed tests
54 failing tests found across 12 suites

# Agent presents execution plan
Parallel agents for: api-smoke-test (15), account-management (12), universe-settings (8)
Sequential: story-creation (5), locations (2)
Quick fixes: remaining singles

# User confirms
> Yes, proceed with parallel execution

# Agents launch and work autonomously
Agent 1: Fixing api-smoke-test... ✅ 15/15 complete (45 min)
Agent 2: Fixing account-management... ✅ 12/12 complete (38 min)
Agent 3: Fixing universe-settings... ✅ 8/8 complete (25 min)

# Sequential batch
Fixing story-creation... ✅ 5/5 complete (18 min)
Fixing locations... ✅ 2/2 complete (8 min)

# Verify with iterative runner
Running iterative stability check... ✅ All stable

# Final check
All 54 tests now passing!
failed-tests.json: 0 tests remaining

✅ E2E test suite is green!
```

---

## Scripts Reference

### run-failed-tests.mjs

**Purpose:** Run tests from `failed-tests.json`, update tracking

**Usage:**
```bash
# Run all failing tests
node scripts/run-failed-tests.mjs

# Run first 5 failing tests
node scripts/run-failed-tests.mjs --limit 5
```

**Behavior:**
- Reads `e2e/failed-tests.json`
- Runs each test sequentially
- Removes passing tests from JSON
- Updates failing tests with lastStatus/lastRunAt
- Shows summary at end

### run-iterative.mjs

**Purpose:** Run tests iteratively, detect flaky tests

**Usage:**
```bash
# Run with defaults (chromium, max 5 attempts)
node scripts/run-iterative.mjs

# Run specific project
PW_PROJECT=firefox node scripts/run-iterative.mjs

# Filter tests
PW_GREP="login" node scripts/run-iterative.mjs

# More attempts
PW_MAX_ATTEMPTS=10 node scripts/run-iterative.mjs
```

**Behavior:**
- Runs full suite or grep match
- On failure, reruns that specific test immediately
- If passes on rerun → logs as flaky, continues
- If fails on rerun → exits for inspection
- Repeats until green or max attempts

---

**Remember:** This is systematic, autonomous fixing. Agents should work through ALL tests without stopping until the suite is green.
