---
name: test-ui
description: Test browser UI with visual validation, regression testing, and zero-tolerance for false positives
---

# Test UI Command - Browser Testing with Visual Validation

**User-facing command for comprehensive browser UI testing.**

## ⚠️ Important: Command Purpose

**This command is a USER INTERFACE** - it delegates all actual work to the **browser-testing agent**.

**What this command does:**
- ✅ Parse user arguments (feature, URL, flow)
- ✅ Validate MCP chrome-devtools availability
- ✅ Delegate to browser-testing agent with context

**What this command does NOT do:**
- ❌ Does NOT perform browser testing itself
- ❌ Does NOT take screenshots itself
- ❌ Does NOT analyze UI itself

**All actual work is done by:** `.claude/agents/browser-testing.md`

## Usage

```bash
# Test specific feature
/test-ui --feature="user login" --url="http://localhost:3000/login"

# Test user flow
/test-ui --flow="registration -> profile setup -> dashboard"

# Regression testing
/test-ui --feature="checkout" --baseline --url="http://localhost:3000"

# With specific success criteria
/test-ui --feature="form submission" --expect="success message visible"
```

## Arguments

### Required (at least one):
- `--feature=<name>` - Feature to test (e.g., "login", "checkout", "profile")
- `--flow=<description>` - User flow to test (e.g., "login -> dashboard -> settings")

### Optional:
- `--url=<url>` - URL to test (defaults to localhost:3000 or inferred from repo)
- `--expect=<criteria>` - Success criteria (e.g., "submit button visible")
- `--baseline` - Capture baseline for regression testing
- `--compare=<baseline-path>` - Compare with existing baseline
- `--screenshots=<path>` - Directory to save screenshots (defaults to /tmp/test-evidence/)

## Examples

### Example 1: Test Login Feature
```bash
/test-ui --feature="login" --url="http://localhost:3000/login" --expect="dashboard visible after login"
```

**What happens:**
1. Command parses arguments
2. Delegates to browser-testing agent with:
   - Feature: login
   - URL: http://localhost:3000/login
   - Expected: dashboard visible after login
3. Agent performs actual browser testing with visual validation
4. Returns comprehensive test report

### Example 2: Regression Testing
```bash
/test-ui --feature="checkout" --baseline
# ... make changes ...
/test-ui --feature="checkout" --compare=/tmp/test-evidence/baseline-checkout.png
```

**What happens:**
1. First command captures baseline screenshots
2. After changes, second command compares current state with baseline
3. Agent detects any visual regressions
4. Returns regression analysis

### Example 3: Full User Flow
```bash
/test-ui --flow="register -> verify email -> create profile -> upload photo -> complete onboarding"
```

**What happens:**
1. Command parses multi-step flow
2. Agent tests each step with screenshots
3. Validates visual transitions between steps
4. Returns flow completion report

## Workflow

### Step 1: Validate MCP Connection

Check if MCP chrome-devtools is available:
- If available: proceed
- If not available: inform user and exit

**DO NOT proceed without MCP chrome-devtools.**

### Step 2: Parse Arguments

Extract and validate:
- Feature name or flow description
- Target URL
- Expected outcomes
- Testing mode (baseline vs comparison)

### Step 3: Delegate to Browser Testing Agent

Use natural language delegation to browser-testing agent:

```markdown
"I need comprehensive browser UI testing with visual validation.

Test Request:
- **Feature**: ${FEATURE_NAME}
- **URL**: ${TARGET_URL}
- **Flow**: ${USER_FLOW}
- **Expected Outcome**: ${SUCCESS_CRITERIA}
- **Testing Mode**: ${baseline|comparison|standard}

Requirements:
- Actual browser testing (no shortcuts)
- Screenshot evidence for all tests
- Compare with baseline if regression testing
- Zero tolerance for errors

Provide detailed test report with visual proof."
```

### Step 4: Return Results

Present agent's test report to user with:
- Test summary (passed/failed/regressions)
- Screenshots locations
- Console error summary
- Network request summary
- Recommendations

## Testing Principles

### Zero-Tolerance Policy

This command (via browser-testing agent) has **ZERO TOLERANCE** for:
- ❌ Reporting success without screenshot proof
- ❌ Assuming elements work without interaction testing
- ❌ Ignoring console errors
- ❌ Skipping visual validation
- ❌ Making excuses for failed tests
- ❌ Taking shortcuts to finish faster
- ❌ Reporting false positives

**If you can't prove it visually, you can't claim it works.**

### What Gets Tested

**Visual Validation:**
- ✅ Elements actually visible (not just in DOM)
- ✅ Correct positioning and layout
- ✅ No layout breaks or overlaps
- ✅ Loading states and transitions

**Interaction Testing:**
- ✅ Button clicks produce visual feedback
- ✅ Form submissions work end-to-end
- ✅ Navigation changes URL and displays new page
- ✅ Modals open and close correctly

**Error Detection:**
- ✅ Console errors = test failure
- ✅ Network 4xx/5xx errors = test failure
- ✅ Missing elements = test failure
- ✅ Broken layouts = test failure

**Regression Testing:**
- ✅ Baseline vs current screenshot comparison
- ✅ New console errors detection
- ✅ Layout shift detection
- ✅ Functionality preservation

## MCP Chrome DevTools Integration

This command requires **MCP chrome-devtools** to be connected.

**Setup:**
1. Install MCP chrome-devtools server
2. Start Chrome with remote debugging:
   ```bash
   chrome --remote-debugging-port=9222
   ```
3. Connect MCP server to Claude Code
4. Verify with: `/test-ui --feature="simple test"`

**If MCP is not connected:**
```markdown
❌ ERROR: MCP chrome-devtools not connected

Cannot proceed with browser testing. This command requires:
- MCP chrome-devtools server running
- Chrome/Chromium browser available
- Valid connection to browser instance

Please verify MCP connection and retry.
```

## Output Format

### Success Report

```markdown
# Browser Test Report - {Feature Name}

**Status**: ✅ PASS
**Duration**: 45s
**Tests**: 5 passed, 0 failed

## Test Cases

### 1. Page Load
✅ PASS - Login page loaded successfully
- Screenshot: /tmp/test-evidence/login-page.png
- Load time: 1.2s
- Console errors: 0

### 2. Form Interaction
✅ PASS - Email and password fields functional
- Screenshot: /tmp/test-evidence/login-filled.png
- Fields accept input correctly

### 3. Submit Button
✅ PASS - Login successful
- Screenshot: /tmp/test-evidence/dashboard.png
- Navigated to /dashboard
- User avatar visible

## Visual Evidence

All screenshots saved to: /tmp/test-evidence/
- login-page.png
- login-filled.png
- dashboard.png

## Console/Network

- Console errors: 0
- Network errors: 0
- API calls: 1 (POST /api/login - 200 OK)
```

### Failure Report

```markdown
# Browser Test Report - {Feature Name}

**Status**: ❌ FAIL
**Duration**: 23s
**Tests**: 2 passed, 1 failed

## Failed Tests

### Test Case 3: Submit Button
❌ FAIL - Submit button not visible

**Evidence**: /tmp/test-evidence/login-attempt.png

**Expected**: Submit button at bottom of form
**Actual**: Button missing from viewport (display: none in CSS?)

**Screenshot shows**:
- Email field visible
- Password field visible
- Submit button NOT visible

## Recommendations

1. Check CSS for submit button (may be hidden)
2. Verify button element exists in DOM
3. Check responsive layout (may be offscreen)
4. Re-test after fix applied
```

## Benefits

✅ **Trustworthy Results** - Zero-tolerance for false positives
✅ **Visual Proof** - Screenshots for every test assertion
✅ **Regression Detection** - Automatic before/after comparison
✅ **No Manual Testing** - Eliminates need for manual browser testing
✅ **Developer Workflow** - Integrates into development/debugging flow
✅ **Evidence-Based** - All claims backed by visual evidence

## Integration

**Orchestrator Integration:**
Orchestrator routes browser testing requests to this command:

Keywords: browser test, UI test, visual validation, regression test, screenshot verification, UI automation

**Workflow Integration:**
```bash
# After implementing feature
/test-ui --feature="new feature" --baseline

# After bug fix
/test-ui --feature="fixed bug" --compare=/tmp/baseline.png

# Before PR
/test-ui --flow="critical user paths"
```

## Notes

- This command uses the browser-testing agent for all actual testing
- MCP chrome-devtools is required (not optional)
- Screenshots are saved to /tmp/test-evidence/ by default
- Console errors always cause test failure
- Visual validation is mandatory for all tests
- No shortcuts or assumptions allowed

## See Also

- `.claude/agents/browser-testing.md` - The agent that does the actual work
- `/test-all` - Run all test types (unit, integration, browser)
- `/test-user-flow` - API-level user flow testing
