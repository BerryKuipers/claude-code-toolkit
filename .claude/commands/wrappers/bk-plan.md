# bk-plan - Toolkit Planning Wrapper

**Arguments:** [task description] [--skip-gates]

**Description:** Toolkit wrapper that DELEGATES to upstream planner agent via Task tool.

---

## CRITICAL: This is a DELEGATION command

**DO NOT create the plan yourself. You MUST delegate via Task tool.**

This command spawns a subagent for planning - preserving your context.

---

## Instructions

### Step 1: Pre-flight Checks (quick, inline - unless --skip-gates)

```bash
git status --porcelain
npx tsc --noEmit 2>/dev/null || echo "No TS"
```

### Step 2: IMMEDIATELY Spawn Planning Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "everything-claude-code:planner",
  description: "Create implementation plan",
  prompt: "Create a detailed implementation plan for:

[USER'S TASK DESCRIPTION]

Include:
- Step-by-step approach with file paths
- Files to modify and why
- Risks and mitigations
- Verification steps (tests, build, lint)"
)
```

### Step 3: Format Output

After agent returns, ensure response includes:

```markdown
## Plan Summary
[1-3 sentences from agent]

## Steps
1. [Step with file paths]

## Files to Modify
- `path/file.ts` - [reason]

## Risks & Mitigations
- [Risk]: [Mitigation]

## Verification
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Lint clean
```

---

## Fallback

If `everything-claude-code:planner` unavailable:
```
Task(subagent_type: "architect", prompt: "[same]")
```

**NEVER create the plan inline in the main conversation.**
