# bk-review - Toolkit Code Review Wrapper

**Arguments:** [PR_NUMBER | --staged | --diff] [--strict] [--security-focus]

**Description:** Toolkit wrapper around upstream code-reviewer agent. Adds verification gates and house-style enforcement.

---

## Instructions

You are executing the toolkit code review wrapper. This command:
1. Gathers changes to review (PR, staged, or diff)
2. Delegates to upstream `code-reviewer` agent from everything-claude-code plugin
3. Enforces toolkit output contract
4. Optionally invokes security-reviewer for --security-focus

### Step 1: Gather Review Context

Determine what to review:
- If PR_NUMBER: `gh pr view $PR_NUMBER --json files,body,title`
- If --staged: `git diff --cached`
- If --diff: `git diff`
- Default: staged changes

### Step 2: Delegate to Upstream Reviewer

Use the Task tool:
```
Task(
  subagent_type: "everything-claude-code:code-reviewer",
  prompt: "Review these changes for quality, security, and best practices:\n[CHANGES]"
)
```

If --security-focus:
```
Task(
  subagent_type: "everything-claude-code:security-reviewer",
  prompt: "Security review these changes:\n[CHANGES]"
)
```

### Step 3: Enforce Output Contract

Response MUST include:

```markdown
## Review Summary
[Overall assessment: APPROVE / REQUEST_CHANGES / COMMENT]

## Findings

### Critical (Must Fix)
- [ ] [File:Line] [Issue description]

### Warnings (Should Fix)
- [ ] [File:Line] [Issue description]

### Suggestions (Nice to Have)
- [ ] [File:Line] [Suggestion]

## Security Concerns
- [None | List of concerns]

## Test Coverage
- [Assessment of test coverage for changes]

## Files Reviewed
- `path/to/file.ts` - [OK | Issues found]
```

### Step 4: House Style Validation

Verify reviewed code follows toolkit rules:
- No console.log in production code
- Proper error handling
- Type safety (no `any` without justification)
- Consistent naming conventions

---

## Fallback Behavior

If upstream plugin unavailable:
1. Use toolkit's `code-reviewer` agent
2. Still enforce output contract
