# bk-architect - Toolkit Architecture Review Wrapper

**Arguments:** [--scope=whole|backend|frontend|db] [--strict]

**Description:** Toolkit wrapper that DELEGATES architecture review via Task tool.

---

## CRITICAL: This is a DELEGATION command

**DO NOT perform the review yourself. You MUST delegate via Task tool.**

This command spawns an architecture agent - preserving your context.

---

## Instructions

### Step 1: Load Project Rules (quick reference)

Note rules to pass to agent:
- Layer boundaries (00-global-architecture.mdc)
- Backend patterns (02-backend-http-layer.mdc)
- Persistence rules (03-backend-persistence.mdc)

### Step 2: IMMEDIATELY Spawn Architect Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "everything-claude-code:architect",
  description: "Architecture review",
  prompt: "Architectural review with scope: [SCOPE]

Validate:
- Layer boundaries (HTTP → Service → Repository)
- Dependency direction (outer → inner only)
- SOLID principles
- Domain isolation

Check for:
- Controllers calling repositories directly (violation)
- Business logic in HTTP layer (violation)
- Circular dependencies
- God classes/modules"
)
```

### Step 3: Format Output

After agent returns, ensure report includes:

```markdown
## Architecture Review Report

### Summary
**Health**: [HEALTHY ✅ | NEEDS_ATTENTION ⚠️ | CRITICAL ❌]

### Layer Violations
| File | Expected | Actual | Severity |
|------|----------|--------|----------|

### SOLID Violations
- [Principle]: [Issue] in [File]

### Recommendations
1. [Priority fixes]
```

---

## Fallback

If upstream unavailable:
```
Task(subagent_type: "architect", prompt: "[same]")
```

**NEVER perform architecture review inline.**
