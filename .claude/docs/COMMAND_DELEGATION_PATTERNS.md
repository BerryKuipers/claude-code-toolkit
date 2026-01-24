# Command Delegation Patterns

Understanding when slash commands delegate to subagents vs execute inline.

## The Two Types

### Type 1: INLINE Commands (fills context)

These expand into instructions that Claude follows in the main conversation.

**Characteristics:**
- No Task tool invocation
- Work happens in your context window
- Results immediately visible
- Consumes your context budget

**Example - Inline Command:**
```markdown
# /format-code

## Instructions
1. Read the file
2. Apply formatting rules
3. Write the formatted result

[Claude does all this work inline, filling your context]
```

**When to use inline:**
- Quick, simple tasks (<2 min work)
- Tasks needing conversation context
- Interactive back-and-forth needed

---

### Type 2: DELEGATION Commands (preserves context)

These spawn subagents via Task tool - work happens in isolated context.

**Characteristics:**
- MUST use Task tool
- Subagent has own context window
- Only summary returns to main conversation
- Preserves your context budget

**Example - Delegation Command:**
```markdown
# /bk-review

## CRITICAL: DELEGATION COMMAND
**DO NOT perform work inline. MUST use Task tool.**

## Instructions

### Step 1: Quick prep (inline, <30 sec)
Gather the diff to review.

### Step 2: IMMEDIATELY DELEGATE
**CALL TASK TOOL NOW:**
Task(
  subagent_type: "everything-claude-code:code-reviewer",
  prompt: "Review these changes: [DIFF]"
)

### Step 3: Format results
Compile subagent's response into standard format.
```

**When to use delegation:**
- Complex, multi-step analysis
- Large codebases or diffs
- Tasks that would fill context
- Parallel work (multiple agents)

---

## How to Identify Command Type

### Signs of INLINE command:
- No mention of Task tool
- Says "analyze", "review", "implement" without delegation
- Provides detailed step-by-step for Claude to follow
- No "subagent" or "delegate" keywords

### Signs of DELEGATION command:
- Contains `Task(subagent_type: ...)`
- Says "MUST delegate", "spawn agent", "DO NOT do inline"
- Has "CRITICAL: DELEGATION" header
- Light on details (subagent handles complexity)

---

## Converting Inline → Delegation

**Before (inline, fills context):**
```markdown
# /code-review

Review the staged changes:
1. Check for security issues
2. Check for type safety
3. Check for error handling
4. Generate report

[Claude does all 4 steps, consuming context]
```

**After (delegation, preserves context):**
```markdown
# /code-review

## CRITICAL: DELEGATION COMMAND

### Step 1: Get diff (quick)
git diff --cached

### Step 2: DELEGATE NOW
Task(
  subagent_type: "code-reviewer",
  prompt: "Review: [DIFF]"
)

### Step 3: Return summary
[Only the summary enters main context]
```

---

## Toolkit Wrapper Pattern

All `bk-*` commands follow this pattern:

```
┌─────────────────────────────────────┐
│  /bk-review invoked                 │
├─────────────────────────────────────┤
│  1. Quick context gathering (inline)│
│     - Get diff, PR info             │
│     - ~50 tokens added to context   │
├─────────────────────────────────────┤
│  2. Task tool spawns subagent       │
│     ┌───────────────────────────┐   │
│     │  Subagent context (200K)  │   │
│     │  - Full review work       │   │
│     │  - All analysis           │   │
│     │  - Detailed findings      │   │
│     └───────────────────────────┘   │
├─────────────────────────────────────┤
│  3. Summary returns (~200 tokens)   │
│     - Verdict + key findings        │
└─────────────────────────────────────┘
```

**Result:** Complex review uses ~250 tokens in main context instead of ~10,000+

---

## Visual Indicator for Status Line

Commands can signal their type in status line output:

- `[inline]` - Work happening in main context
- `[agent:name]` - Delegated to subagent
- `[agents:3]` - Multiple parallel agents working

This helps you understand where your context is going.
