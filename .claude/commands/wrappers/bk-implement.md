# bk-implement - Toolkit Implementation Wrapper

**Arguments:** [task or plan file] [--dry-run] [--skip-tests]

**Description:** Toolkit wrapper for implementation. Enforces pre/post verification gates and output contract.

---

## Instructions

You are executing the toolkit implementation wrapper. This command:
1. Validates preconditions
2. Delegates to upstream or toolkit implementation agent
3. Runs post-implementation verification
4. Enforces output contract

### Step 1: Pre-Implementation Gates

```bash
# Type check
npx tsc --noEmit

# Lint check
npm run lint 2>/dev/null || npx eslint . --max-warnings=0

# Ensure tests pass before changes
npm test -- --passWithNoTests
```

If any gate fails, STOP and report the issue.

### Step 2: Delegate Implementation

Use Task tool with upstream or toolkit implementation:
```
Task(
  subagent_type: "implementation",  # or "everything-claude-code:implementer" if available
  prompt: "[TASK DESCRIPTION OR PLAN]"
)
```

### Step 3: Post-Implementation Gates (unless --skip-tests)

```bash
# Build check
npm run build 2>/dev/null || npx tsc

# Type check
npx tsc --noEmit

# Test
npm test

# Lint
npm run lint 2>/dev/null || npx eslint . --max-warnings=0
```

### Step 4: Enforce Output Contract

Response MUST include:

```markdown
## Implementation Summary
[What was implemented]

## Files Changed
| File | Change Type | Description |
|------|-------------|-------------|
| path/file.ts | Modified | [What changed] |

## Tests Added/Modified
- `path/to/test.ts` - [What it tests]

## Verification Results
- Build: [PASS/FAIL]
- Tests: [PASS/FAIL] ([X] passed, [Y] failed)
- Lint: [PASS/FAIL]
- Types: [PASS/FAIL]

## Next Steps
- [ ] [Recommended follow-up action]
```

---

## Rollback on Failure

If post-implementation gates fail:
1. Log which gate failed
2. Offer to rollback: `git checkout -- .`
3. Provide actionable fix suggestions
