# bk-architect - Toolkit Architecture Review Wrapper

**Arguments:** [--scope=whole|backend|frontend|db] [--strict]

**Description:** Toolkit wrapper around upstream architect agent. Enforces layer rules and output contract.

---

## Instructions

### Step 1: Load Project Rules

Read and apply:
- `.claude/rules/00-global-architecture.mdc`
- `.claude/rules/02-backend-http-layer.mdc`
- `.claude/rules/03-backend-persistence.mdc`
- `.claude/rules/04-frontend-react-architecture.mdc`

### Step 2: Delegate to Upstream Architect

```
Task(
  subagent_type: "everything-claude-code:architect",
  prompt: "Architectural review with scope: [SCOPE]\n\nValidate:\n- Layer boundaries\n- Dependency direction\n- SOLID principles\n- Domain isolation"
)
```

### Step 3: Enforce Output Contract

```markdown
## Architecture Review Report

### Summary
[Overall architectural health: HEALTHY | NEEDS_ATTENTION | CRITICAL]

### Layer Violations
| File | Expected Layer | Actual Usage | Severity |
|------|----------------|--------------|----------|

### Dependency Direction Issues
| Source | Target | Problem | Fix |
|--------|--------|---------|-----|

### SOLID Violations
- [Principle]: [Violation] in [File]

### Recommendations
1. [Prioritized improvements]

### Diagram (if applicable)
```mermaid
graph TD
  [Architecture diagram]
```
```

---

## Fallback

If upstream unavailable, use toolkit's `architect` agent.
