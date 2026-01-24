# bk-fix - Toolkit Build/Error Fix Wrapper

**Arguments:** [--type=build|test|lint|types] [--auto-commit]

**Description:** Toolkit wrapper that DELEGATES error fixing via Task tool with minimal diff policy.

---

## CRITICAL: This is a DELEGATION command

**DO NOT fix the errors yourself. You MUST delegate via Task tool.**

This command spawns a build-error-resolver agent - keeping fixes isolated.

---

## Instructions

### Step 1: Capture Error Output (quick, inline)

```bash
# Detect error type
npm run build 2>&1 | head -50 > /tmp/errors.txt || TYPE="build"
npx tsc --noEmit 2>&1 | head -50 >> /tmp/errors.txt || TYPE="types"
npm test 2>&1 | head -50 >> /tmp/errors.txt || TYPE="test"
```

### Step 2: IMMEDIATELY Spawn Fix Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "everything-claude-code:build-error-resolver",
  description: "Fix build/type errors",
  prompt: "Fix [TYPE] errors with MINIMAL changes only.

RULES:
- NO refactoring
- NO architecture changes
- NO 'while I'm here' improvements
- ONLY fix the specific errors

Error output:
[PASTE ERRORS]"
)
```

### Step 3: Verify Fix

After agent returns:
```bash
npm run build && npm test
```

### Step 4: Check Diff Size

```bash
git diff --stat
# Warn if > 50 lines changed
```

### Step 5: Format Output

```markdown
## Fix Summary

### Error Type
[build | test | lint | types]

### Root Cause
[What was wrong]

### Changes Made
| File | Lines | Description |
|------|-------|-------------|

### Verification
- [TYPE] check: [PASS ✅ / FAIL ❌]

### Diff Size
[X lines changed] [OK ✅ / LARGE ⚠️]
```

---

## Fallback

If upstream unavailable:
```
Task(subagent_type: "build-error-resolver", prompt: "[same]")
```

**NEVER fix errors inline in main conversation.**
