# bk-implement - Toolkit Implementation Wrapper

**Arguments:** [task or plan file] [--dry-run] [--skip-tests]

**Description:** Toolkit wrapper that DELEGATES implementation via Task tool with verification gates.

---

## CRITICAL: This is a DELEGATION command

**DO NOT implement the task yourself. You MUST delegate via Task tool.**

This command spawns a subagent - preserving your context for verification.

---

## Instructions

### Step 1: Pre-Implementation Gates (quick, inline)

```bash
npx tsc --noEmit 2>/dev/null || echo "No TS"
npm test -- --passWithNoTests 2>/dev/null || echo "Tests skipped"
```

If gates fail, STOP and report - don't delegate broken state.

### Step 2: IMMEDIATELY Spawn Implementation Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "implementation",
  description: "Implement feature/fix",
  prompt: "Implement the following:

[TASK DESCRIPTION OR PLAN]

Requirements:
- Follow existing code patterns
- Add/update tests for changes
- No unrelated refactoring
- Keep changes minimal and focused"
)
```

### Step 3: Post-Implementation Gates

After agent returns, run verification:
```bash
npm run build 2>/dev/null || npx tsc
npm test
npm run lint 2>/dev/null || true
```

### Step 4: Format Output

```markdown
## Implementation Summary
[What was implemented - from agent]

## Files Changed
| File | Change | Description |
|------|--------|-------------|

## Verification Results
- Build: [PASS/FAIL]
- Tests: [PASS/FAIL]
- Lint: [PASS/FAIL]

## Next Steps
- [ ] [Follow-up if any]
```

---

## Fallback

If implementation agent unavailable, use Task with general-purpose agent.

**NEVER implement inline in the main conversation.**
