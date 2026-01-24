# bk-doc - Toolkit Documentation Wrapper

**Arguments:** [--scope=api|readme|all] [--update-only]

**Description:** Toolkit wrapper that DELEGATES documentation updates via Task tool.

---

## CRITICAL: This is a DELEGATION command

**DO NOT write documentation yourself. You MUST delegate via Task tool.**

This command spawns a doc-updater agent - keeping your context for review.

---

## Instructions

### Step 1: Assess Current State (quick, inline)

```bash
find . -name "*.md" -not -path "./node_modules/*" | wc -l
ls docs/ 2>/dev/null || echo "No docs/"
```

### Step 2: IMMEDIATELY Spawn Doc Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "everything-claude-code:doc-updater",
  description: "Update documentation",
  prompt: "Update documentation with scope: [SCOPE]

Requirements:
- Clear titles and purpose
- Usage examples for all APIs
- Keep existing structure
- Update 'last updated' dates

[--update-only]: Only modify existing docs, don't create new files"
)
```

### Step 3: Format Output

```markdown
## Documentation Update Summary

### Files Updated
| File | Type | Changes |
|------|------|---------|

### Files Created
| File | Purpose |
|------|---------|

### Coverage
- API endpoints: X/Y documented
- Components: X/Y documented
- Examples: [Yes/No]

### Gaps
- [Missing documentation areas]
```

---

## Fallback

If upstream unavailable, use general-purpose agent for doc updates.

**NEVER write documentation inline in main conversation.**
