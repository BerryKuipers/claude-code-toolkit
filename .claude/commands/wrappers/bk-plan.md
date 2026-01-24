# bk-plan - Toolkit Planning Wrapper

**Arguments:** [task description] [--skip-gates]

**Description:** Toolkit wrapper around upstream planner agent. Adds verification gates and output contract enforcement.

---

## Instructions

You are executing the toolkit planning wrapper. This command:
1. Validates preconditions (clean git state, no failing tests)
2. Delegates to upstream `planner` agent from everything-claude-code plugin
3. Enforces toolkit output contract on the response
4. Validates the plan against project rules

### Step 1: Pre-flight Checks (unless --skip-gates)

Run verification gates:
```bash
# Check git state
git status --porcelain

# Quick type check if TypeScript
npx tsc --noEmit 2>/dev/null || true
```

### Step 2: Delegate to Upstream Planner

Use the Task tool to invoke the upstream planner:
```
Task(
  subagent_type: "everything-claude-code:planner",
  prompt: "[USER'S TASK DESCRIPTION]"
)
```

If the upstream agent is unavailable, fall back to the toolkit's architect agent.

### Step 3: Enforce Output Contract

The response MUST include these sections:

```markdown
## Plan Summary
[1-3 sentences describing the approach]

## Steps
1. [Step with file paths and rationale]
2. ...

## Files to Modify
- `path/to/file.ts` - [reason]

## Risks & Mitigations
- [Risk]: [Mitigation]

## Verification Steps
- [ ] Tests pass
- [ ] Build succeeds
- [ ] No lint errors
```

### Step 4: Validate Against Project Rules

If `.claude/rules/` exists, verify plan doesn't violate:
- Layer boundaries (00-global-architecture.mdc)
- TypeScript style (01-typescript-style.mdc)
- Backend patterns (02-backend-http-layer.mdc)

---

## Fallback Behavior

If upstream plugin unavailable:
1. Log warning: "Upstream planner unavailable, using toolkit architect"
2. Use Task with `subagent_type: "architect"` instead
3. Still enforce output contract
