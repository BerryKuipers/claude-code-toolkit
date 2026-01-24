# Continuous Learning Skill

Automatically extract reusable patterns from Claude Code sessions and save them as learned skills for future use.

## Purpose

Transform ad-hoc solutions discovered during sessions into documented, reusable patterns that improve future work.

## When to Use

- After solving a tricky problem
- When discovering a useful pattern
- After successful debugging sessions
- When finding project-specific conventions
- After completing complex refactoring

## Pattern Extraction Process

### Step 1: Identify Learnable Moment

Recognize when something valuable was discovered:

```markdown
**Triggers:**
- "That was tricky but I figured out..."
- "The solution was to..."
- "This pattern works well for..."
- "I should remember this approach..."
- Error resolved after multiple attempts
```

### Step 2: Document the Pattern

Create a structured learning entry:

```markdown
## Learning: [Pattern Name]

**Date**: YYYY-MM-DD
**Context**: [What problem was being solved]
**Project**: [Where discovered]

### Problem
[What wasn't working or was unclear]

### Solution
[The approach that worked]

### Code Example
```[language]
// Before (problematic)
[code]

// After (working)
[code]
```

### Why It Works
[Explanation of why this solution is correct]

### When to Apply
[Conditions when this pattern should be used]

### Related
- [Links to docs, issues, or other learnings]
```

### Step 3: Store the Learning

Save to appropriate location:

```bash
# Project-specific learning
echo "$LEARNING" >> .claude/learnings/$(date +%Y-%m).md

# Toolkit-wide learning (if generalizable)
echo "$LEARNING" >> .claude/skills/learnings/patterns.md
```

### Step 4: Index for Retrieval

Add to searchable index:

```markdown
# .claude/learnings/INDEX.md

## Error Resolution
- [TS2322 type mismatch with generics](./2024-01.md#ts2322-generics)
- [Prisma client regeneration](./2024-01.md#prisma-client)

## Patterns
- [Optional chaining with defaults](./2024-02.md#optional-chaining)
- [Service layer error handling](./2024-02.md#service-errors)

## Project-Specific
- [AI pipeline integration](./2024-01.md#ai-pipeline)
```

## Categories of Learnings

### Error Resolution
```markdown
**Error**: [Error message or code]
**Cause**: [What caused it]
**Fix**: [How to resolve]
**Prevention**: [How to avoid in future]
```

### Code Patterns
```markdown
**Pattern**: [Name]
**Use When**: [Conditions]
**Implementation**: [Code]
**Gotchas**: [Things to watch out for]
```

### Tool Usage
```markdown
**Tool**: [Tool name]
**Use Case**: [When to use]
**Command**: [How to invoke]
**Options**: [Useful flags/parameters]
```

### Project Conventions
```markdown
**Convention**: [Name]
**Applies To**: [Files/areas]
**Rule**: [What to do]
**Example**: [Code example]
```

## Automatic Pattern Detection

Look for these signals during work:

| Signal | Learning Type |
|--------|---------------|
| Same error fixed twice | Error Resolution |
| Code copied between features | Code Pattern |
| "This is how we do X here" | Project Convention |
| Workaround found for limitation | Tool Usage |
| Performance fix discovered | Optimization Pattern |

## Integration with Session End

At session end, review for learnings:

```markdown
## Session Learning Review

**Tasks Completed**: [List]

**Learnings Captured**:
1. [Learning 1] - Saved to [location]
2. [Learning 2] - Saved to [location]

**Potential Learnings** (not yet documented):
- [ ] [Observation that might be worth documenting]
```

## Retrieval

Before starting similar work, check learnings:

```bash
# Search learnings
grep -r "prisma" .claude/learnings/
grep -r "TS2322" .claude/learnings/

# Check index
cat .claude/learnings/INDEX.md | grep "error"
```

## Quality Criteria

A good learning entry:
- ✅ Specific enough to be actionable
- ✅ Includes working code example
- ✅ Explains the "why" not just the "what"
- ✅ Identifies when to apply
- ✅ Searchable by error code or keyword

A learning to skip:
- ❌ Too generic ("always write good code")
- ❌ One-time workaround (not reusable)
- ❌ Already documented elsewhere
- ❌ Project-specific hack (not a pattern)

## Output Contract

When documenting a learning:

```markdown
## Learning Captured

**Title**: [Pattern name]
**Type**: [Error Resolution | Code Pattern | Tool Usage | Convention]
**Location**: [File path where saved]

**Summary**: [One sentence description]

**Searchable Tags**: [tag1, tag2, tag3]
```
