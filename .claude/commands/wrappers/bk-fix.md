# bk-fix - Toolkit Build/Error Fix Wrapper

**Arguments:** [--type=build|test|lint|types] [--auto-commit]

**Description:** Toolkit wrapper around upstream build-error-resolver. Enforces minimal diff policy.

---

## Instructions

### Step 1: Identify Error Type

Detect error type if not specified:
```bash
# Try build
npm run build 2>&1 | tee /tmp/build-output.txt
if [ $? -ne 0 ]; then TYPE="build"; fi

# Try types
npx tsc --noEmit 2>&1 | tee /tmp/type-output.txt
if [ $? -ne 0 ]; then TYPE="types"; fi

# Try tests
npm test 2>&1 | tee /tmp/test-output.txt
if [ $? -ne 0 ]; then TYPE="test"; fi
```

### Step 2: Delegate to Upstream Fixer

```
Task(
  subagent_type: "everything-claude-code:build-error-resolver",
  prompt: "Fix [TYPE] errors. MINIMAL DIFFS ONLY. No refactoring.\n\nError output:\n[ERROR OUTPUT]"
)
```

### Step 3: Enforce Minimal Diff Policy

After fix:
```bash
# Check diff size
LINES_CHANGED=$(git diff --shortstat | grep -oP '\d+(?= insertions)' || echo 0)
if [ "$LINES_CHANGED" -gt 50 ]; then
  echo "WARNING: Large diff detected. Review changes carefully."
fi
```

### Step 4: Verify Fix

Re-run the failing command:
```bash
# Based on TYPE
npm run build  # or npx tsc --noEmit, npm test, etc.
```

### Step 5: Enforce Output Contract

```markdown
## Fix Summary

### Error Type
[build | test | lint | types]

### Root Cause
[What was wrong]

### Changes Made
| File | Lines Changed | Description |
|------|---------------|-------------|

### Verification
- [TYPE] check: [PASS/FAIL]

### Diff
```diff
[Actual diff]
```
```

### Step 6: Auto-commit (if --auto-commit and fix successful)

```bash
git add -A
git commit -m "fix: resolve [TYPE] errors

- [Brief description]

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Fallback

If upstream unavailable, use toolkit's generic fix approach with Edit tool.
