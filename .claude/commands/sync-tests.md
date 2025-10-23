# Sync and Fix Tests

**Arguments:** $ARGUMENTS (test patterns, files, or specific issues to focus on)

**Success Criteria:** All tests pass (0 failures), tests accurately reflect current code behavior, new tests added for untested functionality

**Description:** AI-driven intelligent test synchronization tool that uses critical thinking to analyze code changes holistically, identify root causes of test failures, fix broken tests systematically, and ensure comprehensive test coverage matches current implementation reality.

## 🧠 Critical Thinking Framework

**Before making any changes, Claude Code MUST think through these questions:**

### **Context Analysis:**
1. **What changed?** - Not just what files, but WHY the code changed and what the original intent was
2. **Test philosophy alignment** - Do the tests reflect the actual business logic or outdated assumptions?
3. **Architecture consistency** - Are test failures revealing deeper architectural misalignments?
4. **Error patterns** - Are similar failures across multiple tests indicating a systematic issue?

### **Root Cause Investigation:**
1. **Surface vs Deep Issues** - Is this a test expectation problem or actual code regression?
2. **Dependency chain impact** - How do changes in one component affect dependent components' tests?
3. **Test data validity** - Are test mocks/fixtures still representative of real data structures?
4. **Timing and async issues** - Are failures due to race conditions or changed async patterns?

### **Holistic Impact Assessment:**
1. **Regression risk** - Will fixing this test mask a real bug or prevent future regressions?
2. **Maintenance burden** - Are we creating brittle tests that will break with every change?
3. **Coverage gaps** - What edge cases are we missing that could cause production issues?
4. **Integration implications** - How do unit test fixes affect integration and E2E test scenarios?

## Test Sync Workflow (6 Steps)

### Step 1: Analyze Current Test Status
```bash
# Get comprehensive test status
cd services/api && npm test --verbose

# Count current test status
echo "=== Test Status Summary ==="
npm test 2>&1 | grep -E "(failed|passed|skipped)" | tail -1

# Identify specific failing tests
npm test 2>&1 | grep -E "FAIL|×" | head -20
```

### Step 2: Compare Code Changes vs Tests
```bash
# Get all changed files since branch point
BRANCH=${1:-development}
git diff $BRANCH..HEAD --name-only

# Find code files that changed but tests might not be updated
echo "=== Changed Code Files ==="
git diff $BRANCH..HEAD --name-only | grep -E "\.(ts|js)$" | grep -v "\.test\." | grep -v "\.spec\."

echo "=== Changed Test Files ==="
git diff $BRANCH..HEAD --name-only | grep -E "\.(test|spec)\.(ts|js)$"

# Check for new functions/methods that need tests
echo "=== New Functions Added ==="
git diff $BRANCH..HEAD | grep -E "^\+.*function|^\+.*async.*\(|^\+.*=.*=>" | head -10
```

### Step 3: Identify Test-Code Mismatches

**🔍 Common Mismatch Patterns:**

1. **Changed Method Signatures:**
```bash
# Find methods with changed parameters
git diff $BRANCH..HEAD | grep -E "^\-.*\(.*\)" -A1 | grep -E "^\+.*\(.*\)"
```

2. **Changed Return Types/Structures:**
```bash
# Look for changed return statements
git diff $BRANCH..HEAD | grep -E "^\-.*return|^\+.*return"
```

3. **New Error Handling:**
```bash
# Find new error cases
git diff $BRANCH..HEAD | grep -E "^\+.*throw|^\+.*error|^\+.*catch"
```

4. **Changed Dependencies:**
```bash
# Check for new imports or dependency changes
git diff $BRANCH..HEAD | grep -E "^\+.*import|^\-.*import"
```

### Step 4: Intelligent Test Repair with Critical Analysis

**🧠 Think First, Then Fix:**

For each failing test, **STOP and analyze:**

```
🤔 CRITICAL THINKING PROMPT:

1. **Intent Analysis:**
   - What was this test originally trying to verify?
   - Has the underlying business logic actually changed, or just the implementation?
   - Should the test behavior change, or should the code behavior change?

2. **Implementation Reality Check:**
   - What does the actual code do RIGHT NOW?
   - Read the implementation carefully - don't assume based on test names
   - Are there discrepancies between test expectations and actual behavior?

3. **Architectural Alignment:**
   - Does this test failure reveal a violation of our architectural principles?
   - Are we testing the right layer? (Controller vs Service vs Repository)
   - Is the test too coupled to implementation details?

4. **Risk Assessment:**
   - If I "fix" this test, am I hiding a real bug?
   - What happens in production if this test passes but the behavior is wrong?
   - Are there integration scenarios this unit test isn't covering?
```

**🛠️ Systematic Test Repair After Analysis:**

1. **Evidence-Based Mock Updates:**
   - VERIFY what the actual method signatures are NOW
   - CONFIRM what the actual return structures are NOW
   - UPDATE mocks to reflect current reality, not past assumptions

2. **Realistic Assertion Updates:**
   - STATUS CODES: Check actual controller implementation for real status codes
   - ERROR MESSAGES: Use exact error messages from actual code
   - RESPONSE STRUCTURES: Match actual response shapes, not ideal ones

3. **Architecture-Aware Test Data:**
   - UUID FORMATS: Use proper UUIDs that match validation rules
   - FIELD MAPPINGS: Ensure test data matches actual entity field names
   - BUSINESS RULES: Test data should respect current validation constraints

4. **Comprehensive Edge Case Coverage:**
   - Add tests for error paths that actually exist in the code
   - Test boundary conditions that could cause production issues
   - Verify async/await patterns match actual implementation

### Step 5: Generate Missing Tests

**📝 Test Generation Strategy:**

For each untested file/function:

1. **Analyze Function Signature:**
   - Input parameters and types
   - Return type and possible values
   - Error conditions and exceptions

2. **Generate Test Cases:**
   - Happy path test
   - Error/edge case tests
   - Validation tests
   - Integration tests if applicable

3. **Follow Existing Patterns:**
   - Use same test structure as similar existing tests
   - Follow project's testing conventions
   - Use consistent mock patterns

### Step 6: Validate All Tests Pass

**✅ Final Validation:**

```bash
# Run full test suite
npm test

# Verify specific test files that were fixed
npm test -- --testPathPattern="Profile|Auth|Controller"

# Check coverage for new/changed code
npm run test:coverage || npm test -- --coverage

# Integration test validation
npm test -- --testPathPattern="Integration"
```

## Command Options

**Primary Flags:**
- `--focus <pattern>` - Focus on specific test files or patterns
- `--fix-only` - Only fix existing tests, don't generate new ones
- `--generate-only` - Only generate missing tests, don't fix existing
- `--coverage` - Include coverage analysis and ensure new code is tested
- `--integration` - Include integration test updates

**Advanced Options:**
- `--branch <name>` - Compare against specific branch (default: development)
- `--verbose` - Show detailed analysis of each test fix
- `--dry-run` - Show what would be fixed without making changes

## Usage Examples

```bash
# Full test sync and fix for current branch
/sync-tests

# Focus on specific component tests
/sync-tests --focus Profile --coverage

# Fix only existing failing tests
/sync-tests --fix-only --verbose

# Generate tests for new untested code
/sync-tests --generate-only --branch development

# Integration test sync
/sync-tests --integration --focus Integration
```

## Expected Output Format

```
🔧 TEST SYNCHRONIZATION REPORT
===============================

📊 Initial Status:
✗ 10 failed tests
✓ 98 passed tests
⏭ 6 skipped tests

📋 Analysis Results:
✅ 5 code files changed since development branch
❌ 3 test files need updates
🆕 7 new functions need tests
🔄 4 existing tests need fixing

🛠️ Fixes Applied:
✅ Updated ProfileController mocks (3 tests fixed)
✅ Fixed AuthController status code expectations (2 tests fixed)
✅ Added tests for new Profile validation methods (5 tests added)
✅ Updated integration test app setup (1 test fixed)

📈 Final Status:
✅ 0 failed tests (100% pass rate)
✓ 113 passed tests
⏭ 1 skipped test

⏱️ Time to Fix: 8 minutes
🎯 Success Rate: 100% - All tests now pass
```

## Integration Points

**Test Framework:** Works with Vitest, Jest, and other testing frameworks
**Coverage Tools:** Integrates with built-in coverage reporting
**Git Analysis:** Uses git diff to understand code changes
**AI Code Analysis:** Analyzes function signatures and generates appropriate tests

---

**Note:** This command ensures that test suites stay in sync with code changes, preventing the common issue of working code with broken tests during development cycles.