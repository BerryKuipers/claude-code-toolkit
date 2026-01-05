# Reflect - Analyze and Apply Learned Patterns

**Arguments:** [--apply] [--include=low] [--scope=auto|project|toolkit] [--promote]

**Description:** Analyze the current session to extract patterns, corrections, and learnings. Optionally apply them to rule files.

---

## Purpose

The `/reflect` command is the core of the self-improving skills system. It:
1. Analyzes what happened during the session
2. Identifies corrections, patterns, and preferences
3. Classifies them by confidence level
4. Optionally applies them to appropriate rule files

---

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--apply` | Apply candidates to rule files (HIGH → 20-*, MEDIUM → 19-*) | Off (report only) |
| `--include=low` | Include LOW confidence candidates in analysis | Exclude LOW |
| `--scope=auto\|project\|toolkit` | Where to write rules | `auto` (detect) |
| `--promote` | Alias for `/promote-learnings` | Off |

---

## Workflow

### Step 1: Gather Context

Collect information from multiple sources:

```bash
echo "🔍 Gathering session context..."

# 1. Git changes in this session
GIT_DIFF=$(git diff --stat HEAD~5 2>/dev/null || echo "No recent commits")
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "No commits")

# 2. Recent ai_memory events
MEMORY_FILE="ai_memory/events.jsonl"
if [ -f "$MEMORY_FILE" ]; then
  RECENT_EVENTS=$(tail -20 "$MEMORY_FILE" 2>/dev/null || echo "[]")
fi

# 3. Existing candidates
CANDIDATES_FILE=".claude/state/reflection-candidates.jsonl"
PENDING_CANDIDATES=$(grep '"status":"pending"' "$CANDIDATES_FILE" 2>/dev/null | wc -l || echo "0")

echo "  → Git changes: $GIT_DIFF"
echo "  → Recent commits: $(echo "$RECENT_COMMITS" | wc -l) commits"
echo "  → Pending candidates: $PENDING_CANDIDATES"
```

### Step 2: Analyze for Patterns

Analyze the current conversation and context for:

**HIGH Confidence (User Explicit):**
- User explicitly corrected Claude's approach
- User said "always do X" or "never do Y"
- User provided a specific pattern to follow
- User rejected an approach and provided alternative

**MEDIUM Confidence (User Implicit):**
- Claude adjusted after feedback without explicit correction
- A pattern was repeated successfully multiple times
- User accepted a change after initial resistance

**LOW Confidence (Observation):**
- Repeated patterns without user feedback
- Assumptions that weren't challenged
- Default behaviors that might be preferences

```markdown
Analyze the conversation history for patterns. Look for:

1. **Corrections**: Where did the user correct my approach?
   - What was I doing wrong?
   - What should I do instead?
   - Is this specific to this project or general?

2. **Preferences**: What preferences did the user express?
   - Code style preferences
   - Workflow preferences
   - Communication preferences

3. **Successful patterns**: What worked well?
   - Approaches that were praised
   - Patterns that avoided issues
   - Techniques that were efficient

For each pattern found, classify:
- Type: correction | preference | pattern
- Confidence: HIGH | MEDIUM | LOW
- Scope: project | toolkit
- Evidence: What specifically indicated this pattern?
```

### Step 3: Generate Candidates

For each identified pattern, create a candidate:

```json
{
  "id": "refl-YYYYMMDD-NNN",
  "timestamp": "ISO8601",
  "session_token": "hash",
  "type": "correction|preference|pattern",
  "confidence": "HIGH|MEDIUM|LOW",
  "source": "user_explicit|user_implicit|observation",
  "description": "Short description of the pattern",
  "evidence": ["List of supporting evidence from conversation"],
  "proposed_rule": "The actual rule text to add to .mdc file",
  "scope": "project|toolkit",
  "status": "pending"
}
```

### Step 4: Report Results

Without `--apply`, output a report:

```markdown
## 🔍 Reflection Analysis

### Session Summary
- Analyzed: [N] conversation turns
- Git changes: [N] files modified
- Memory events: [N] recent events

### Candidates Found

#### HIGH Confidence (Ready to Apply)
1. **[ID]** - [Description]
   - Type: [correction|preference|pattern]
   - Evidence: [summary]
   - Proposed rule: `[rule text]`

#### MEDIUM Confidence (Draft)
1. **[ID]** - [Description]
   - Type: [correction|preference|pattern]
   - Evidence: [summary]
   - Proposed rule: `[rule text]`

#### LOW Confidence (Observations)
[Only shown if --include=low]

### Actions Available
- Run `/reflect --apply` to add patterns to rule files
- Run `/reflect --apply --scope=project` to force project-local rules
- Run `/promote-learnings` to consolidate draft patterns
```

### Step 5: Apply Candidates (if --apply)

When `--apply` is specified:

```bash
# Determine target files based on confidence and scope
for candidate in candidates:
  if candidate.confidence == "HIGH":
    target = ".claude/rules/20-learned-patterns.mdc"
  elif candidate.confidence == "MEDIUM":
    target = ".claude/rules/19-learned-draft.mdc"
  else:
    continue  # Skip LOW unless --include=low

  # Check scope
  if candidate.scope == "toolkit" and scope_arg != "project":
    # Requires extra confirmation for toolkit changes
    prompt_user_for_confirmation()
    if confirmed:
      target = ".claude-toolkit/.claude/rules/[appropriate-file]"
    else:
      target = ".claude/rules/[appropriate-file]"

  # Append pattern to target file
  append_pattern_to_file(target, candidate)
  mark_candidate_applied(candidate.id)
```

**Pattern Format in Rule Files:**

```markdown
### [Pattern ID] - [Short Description]
<!-- Added: YYYY-MM-DD | Source: reflect session | Confidence: [HIGH|MEDIUM] -->

[Pattern description - what to do and when]

**Evidence:**
- [Evidence item 1]
- [Evidence item 2]
```

### Step 6: Commit Changes (if --apply)

After applying patterns:

```bash
# Stage changed rule files
git add .claude/rules/19-learned-draft.mdc
git add .claude/rules/20-learned-patterns.mdc

# Commit with descriptive message
git commit -m "reflex: add learned patterns from reflection

Patterns added:
$(list_applied_patterns)

Source: /reflect session $(date +%Y-%m-%d)
Confidence levels: HIGH=[N], MEDIUM=[N]

🤖 Generated with Claude Code reflex system"
```

---

## Examples

### Report Only (Default)
```bash
/reflect
# Outputs analysis report without making changes
```

### Apply Patterns
```bash
/reflect --apply
# Applies HIGH → 20-learned-patterns.mdc
# Applies MEDIUM → 19-learned-draft.mdc
# Commits changes
```

### Include Low Confidence
```bash
/reflect --include=low
# Shows LOW confidence observations in report
```

### Force Project Scope
```bash
/reflect --apply --scope=project
# All patterns go to project rules, even if they seem generic
```

### Promote Drafts
```bash
/reflect --promote
# Alias for /promote-learnings
# Consolidates 19-* into 20-*
```

---

## Confidence Classification

| Level | Source | Indicators | Destination |
|-------|--------|------------|-------------|
| **HIGH** | User explicit | "always", "never", explicit correction, rejected approach | `20-learned-patterns.mdc` |
| **MEDIUM** | User implicit | Adjusted without explicit feedback, repeated success | `19-learned-draft.mdc` |
| **LOW** | Observation | Pattern noticed, no user feedback | Excluded by default |

---

## Scope Detection (auto mode)

When `--scope=auto`, determine scope based on:

**Project-specific if:**
- References specific file paths (e.g., `src/services/`)
- References project-specific technologies not in toolkit
- User said "for this project" or similar

**Toolkit (global) if:**
- Generic coding pattern
- Applies to any TypeScript/React project
- User said "always" without project qualifier

**When uncertain:** Default to project (safer)

---

## Safety Guardrails

1. **No auto-apply**: Must explicitly use `--apply`
2. **Confirmation for toolkit**: Extra prompt before modifying toolkit
3. **Deduplication**: Check for similar existing rules
4. **Max per session**: Limit to 5 patterns per reflection
5. **Evidence required**: Each pattern must have evidence

---

## Related Commands

- `/reflect-enable` - Enable reflection logging
- `/reflect-disable` - Disable reflection logging
- `/promote-learnings` - Consolidate draft patterns

---

## Files

| File | Purpose |
|------|---------|
| `.claude/state/reflection-candidates.jsonl` | Accumulated candidates |
| `.claude/rules/19-learned-draft.mdc` | MEDIUM confidence patterns |
| `.claude/rules/20-learned-patterns.mdc` | HIGH confidence patterns |
| `.claude/config.yml` | Reflection settings |
