# bk-review - Toolkit Code Review Wrapper

**Arguments:** [PR_NUMBER | --staged | --diff] [--strict] [--security-focus]

**Description:** Toolkit wrapper that DELEGATES to upstream code-reviewer agent via Task tool.

---

## CRITICAL: This is a DELEGATION command

**DO NOT perform the review yourself. You MUST delegate via Task tool.**

This command exists to spawn a subagent - not to do the work inline.

---

## Instructions

### Step 1: Gather Review Context (quick, inline)

Determine what to review:
```bash
# If PR_NUMBER provided
gh pr diff $PR_NUMBER 2>/dev/null || git diff --cached

# If --staged or default
git diff --cached

# If --diff
git diff HEAD~1
```

Capture the diff output (max 500 lines for agent prompt).

### Step 2: IMMEDIATELY Spawn Review Agent

**YOU MUST CALL THE TASK TOOL NOW.** Do not continue without spawning the agent.

```
Task(
  subagent_type: "everything-claude-code:code-reviewer",
  description: "Code review for current changes",
  prompt: "Review these code changes. Provide findings categorized as Critical/Warning/Suggestion with file:line references.

CHANGES TO REVIEW:
[PASTE DIFF HERE]

Focus on:
- Security vulnerabilities
- Logic errors
- Missing error handling
- Type safety issues
- Test coverage gaps"
)
```

### Step 3: If --security-focus, spawn ADDITIONAL agent

```
Task(
  subagent_type: "everything-claude-code:security-reviewer",
  description: "Security review for current changes",
  prompt: "Security-focused review of these changes. Check for OWASP Top 10, injection risks, auth issues.

CHANGES:
[PASTE DIFF HERE]"
)
```

### Step 4: Compile Results

After agent(s) return, format the combined output:

```markdown
## Review Summary
**Verdict**: [APPROVE ✅ | REQUEST_CHANGES ❌ | COMMENT ⚠️]

## Critical Issues (Must Fix)
- [ ] `file:line` - Issue description

## Warnings (Should Fix)
- [ ] `file:line` - Issue description

## Suggestions
- [ ] `file:line` - Suggestion

## Security Concerns
[From security-reviewer if --security-focus]

## Files Reviewed
- `path/file.ts` - [✅ OK | ❌ Issues]
```

---

## Fallback

If `everything-claude-code:code-reviewer` unavailable:
```
Task(
  subagent_type: "code-reviewer",
  prompt: "[same prompt]"
)
```

**NEVER do the review inline in the main conversation.**
