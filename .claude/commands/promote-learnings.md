# Promote Learnings - Consolidate Draft Patterns

**Arguments:** [--auto] [--all] [--id=PATTERN_ID]

**Description:** Review and promote patterns from `19-learned-draft.mdc` (MEDIUM confidence) to `20-learned-patterns.mdc` (HIGH confidence).

---

## Purpose

Over time, draft patterns (MEDIUM confidence) prove themselves through repeated use. This command helps:
1. Review accumulated draft patterns
2. Consolidate similar patterns
3. Promote validated patterns to HIGH confidence
4. Clean up the draft file

---

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--auto` | Auto-promote patterns seen 3+ times | Off (interactive) |
| `--all` | Promote all draft patterns without review | Off |
| `--id=ID` | Promote specific pattern by ID | All patterns |

---

## Workflow

### Step 1: Load Draft Patterns

```bash
DRAFT_FILE=".claude/rules/19-learned-draft.mdc"
PROMOTED_FILE=".claude/rules/20-learned-patterns.mdc"

# Check if draft file exists and has patterns
if [ ! -f "$DRAFT_FILE" ]; then
  echo "ℹ️  No draft patterns file found."
  echo "   Run /reflect --apply to add patterns first."
  exit 0
fi

# Parse patterns from draft file
# Patterns are in format: ### [ID] - [Description]
```

### Step 2: Analyze Patterns

For each pattern in the draft file:

```markdown
## Pattern Review

### [Pattern ID] - [Description]
<!-- Added: YYYY-MM-DD | Source: reflect session -->

[Pattern text]

**Analysis:**
- Times seen: [count from candidates file]
- Days since added: [days]
- Related patterns: [any similar patterns in 20-*]

**Recommendation:**
- [ ] Promote to HIGH confidence
- [ ] Keep as draft (needs more evidence)
- [ ] Merge with existing pattern
- [ ] Remove (no longer relevant)
```

### Step 3: Interactive Review (Default)

Present patterns for review:

```
📋 Draft Pattern Review

Pattern 1 of N:
─────────────────────────────────────────
ID: refl-20260105-003
Description: Use Prisma transactions for batch operations
Added: 2026-01-05 (3 days ago)
Times reinforced: 2

Pattern Text:
  When performing multiple database inserts or updates,
  always use Prisma transactions to ensure atomicity.

─────────────────────────────────────────

Options:
  [P] Promote to HIGH confidence
  [K] Keep as draft
  [M] Merge with existing pattern
  [R] Remove (no longer relevant)
  [S] Skip for now
  [Q] Quit review

Your choice: _
```

### Step 4: Apply Promotions

For promoted patterns:

```bash
# 1. Add to promoted file with updated metadata
cat >> "$PROMOTED_FILE" << EOF

### $PATTERN_ID - $DESCRIPTION
<!-- Added: $ORIGINAL_DATE | Promoted: $(date +%Y-%m-%d) | Source: promote-learnings -->

$PATTERN_TEXT

**Evidence:**
$EVIDENCE
EOF

# 2. Remove from draft file (mark as promoted)
# Replace pattern section with promotion marker
sed -i "s/### $PATTERN_ID/### $PATTERN_ID [PROMOTED]/g" "$DRAFT_FILE"
```

### Step 5: Consolidate and Clean

After review:

```bash
# Remove promoted patterns from draft file
# Keep only patterns that weren't promoted

# Consolidate similar patterns in promoted file
# Merge duplicates, update evidence lists

# Update candidates file
# Mark promoted candidates as "promoted"
```

### Step 6: Commit Changes

```bash
git add "$DRAFT_FILE" "$PROMOTED_FILE"
git commit -m "reflex: promote learned patterns

Promoted patterns:
$(list_promoted_patterns)

Remaining drafts: $(count_remaining_drafts)

🤖 Generated with Claude Code reflex system"
```

---

## Auto-Promote Mode

With `--auto`, automatically promote patterns that meet criteria:

```bash
# Criteria for auto-promotion:
# 1. Seen 3+ times in candidates (reinforced)
# 2. OR older than 7 days and not contradicted
# 3. AND no existing similar pattern in 20-*

THRESHOLD=3  # From config.yml: reflection.autoPromoteThreshold

for pattern in draft_patterns:
  times_seen = count_in_candidates(pattern.id)
  days_old = days_since(pattern.added_date)

  if times_seen >= THRESHOLD:
    auto_promote(pattern)
    echo "✅ Auto-promoted: $pattern.id (seen $times_seen times)"
  elif days_old >= 7:
    auto_promote(pattern)
    echo "✅ Auto-promoted: $pattern.id (stable for $days_old days)"
```

---

## Examples

### Interactive Review
```bash
/promote-learnings
# Reviews each draft pattern interactively
```

### Auto-Promote
```bash
/promote-learnings --auto
# Automatically promotes patterns meeting criteria
```

### Promote All
```bash
/promote-learnings --all
# Promotes all drafts without review (use with caution)
```

### Promote Specific Pattern
```bash
/promote-learnings --id=refl-20260105-003
# Promotes only the specified pattern
```

---

## Merge Detection

When promoting, check for similar existing patterns:

```markdown
⚠️  Similar Pattern Detected

Draft Pattern:
  "Use transactions for batch operations"

Existing HIGH Pattern (refl-20260101-007):
  "Wrap multiple database writes in transactions"

Options:
  [M] Merge into existing (add evidence)
  [A] Add as separate pattern
  [S] Skip this pattern
```

---

## Expected Output

### Success
```
✅ Promotion Complete

Promoted: 3 patterns
  - refl-20260105-003: Use Prisma transactions
  - refl-20260104-001: Prefer named exports
  - refl-20260103-002: Add error boundaries

Remaining drafts: 2 patterns
Merged: 1 pattern (into refl-20260101-007)

Changes committed to git.
```

### Nothing to Promote
```
ℹ️  No patterns ready for promotion

Draft patterns: 2
  - All are less than 3 days old
  - Consider using --auto after patterns stabilize

Run /reflect to add more patterns.
```

---

## Safety

1. **Interactive by default**: Review before promoting
2. **Merge detection**: Avoid duplicate patterns
3. **Evidence preserved**: Original evidence carried forward
4. **Git commit**: All changes tracked
5. **Rollback**: Use `git revert` if needed

---

## Related Commands

- `/reflect` - Analyze session and add patterns
- `/reflect-enable` - Enable reflection logging
- `/reflect-disable` - Disable reflection logging

---

## Files

| File | Purpose |
|------|---------|
| `.claude/rules/19-learned-draft.mdc` | Source (MEDIUM confidence) |
| `.claude/rules/20-learned-patterns.mdc` | Destination (HIGH confidence) |
| `.claude/state/reflection-candidates.jsonl` | Pattern metadata |
