# bk-doc - Toolkit Documentation Wrapper

**Arguments:** [--scope=api|readme|all] [--update-only]

**Description:** Toolkit wrapper around upstream doc-updater. Enforces documentation standards.

---

## Instructions

### Step 1: Assess Documentation State

```bash
# Find documentation files
find . -name "*.md" -not -path "./node_modules/*" | head -20

# Check for API docs
ls -la docs/ 2>/dev/null || echo "No docs/ directory"

# Check README freshness
stat -c %y README.md 2>/dev/null
```

### Step 2: Delegate to Upstream Doc Updater

```
Task(
  subagent_type: "everything-claude-code:doc-updater",
  prompt: "Update documentation with scope: [SCOPE]\n\n--update-only means only modify existing docs, don't create new ones."
)
```

### Step 3: Enforce Documentation Standards

All documentation must include:
- Clear title and purpose
- Usage examples
- API reference (if applicable)
- Last updated date

### Step 4: Enforce Output Contract

```markdown
## Documentation Update Summary

### Files Updated
| File | Type | Changes |
|------|------|---------|
| README.md | Overview | Updated installation section |

### Files Created (if not --update-only)
| File | Purpose |
|------|---------|

### Coverage
- API endpoints documented: X/Y
- Components documented: X/Y
- Examples provided: [Yes/No]

### Recommendations
- [Missing documentation areas]
```

---

## Fallback

If upstream unavailable, use Read/Write tools to update docs directly.
