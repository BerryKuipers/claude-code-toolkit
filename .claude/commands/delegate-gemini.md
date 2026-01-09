# Delegate to Gemini Command

**Arguments:** [task description] [--scope=PATH] [--verify-only] [--force-score=N]

**Description:** Optionally delegate high-volume, low-risk work to Gemini to save Cloud credits while maintaining quality guardrails.

---

## Purpose

Reduce Cloud API credit consumption by identifying and offloading repetitive, low-risk work to Gemini while keeping architecture decisions and verification in Cloud.

**This is always optional** - you decide whether to delegate or proceed normally.

---

## ⚠️ Important: This is NOT Auto-Delegation

**This command proposes delegation and asks for your approval:**
- ✅ Analyzes work and shows triage score
- ✅ Presents delegation proposal with scope
- ✅ Waits for your explicit approval
- ✅ Only generates Handoff Pack if you approve
- ❌ Never auto-delegates without consent

---

## Workflow

### Step 1: Gather Context

```bash
# Understand repo state
git status --porcelain
git remote get-url origin 2>/dev/null || echo "Local repo"

# Check for package.json (Node/TS project)
if [ -f "package.json" ]; then
  echo "Node.js project detected"
  cat package.json | jq '{scripts: .scripts | keys}' 2>/dev/null
fi
```

### Step 2: Analyze Task for Delegation Suitability

**Parse arguments:**
- `$ARGUMENTS` - Task description
- `--scope=PATH` - Optional path restriction
- `--verify-only` - Skip to verification phase (user returning with Gemini results)
- `--force-score=N` - Override minimum triage score (for edge cases)

**Triage the work using these dimensions (1-5 scale):**

| Dimension | 5 (Best) | 1 (Worst) |
|-----------|----------|-----------|
| Repetitiveness | Same pattern across many files | Unique per-file logic |
| Risk Level | Format/style only | Business logic changes |
| Verifiability | Lint/typecheck catches all issues | Requires manual review |
| Pattern Clarity | Crystal clear with examples | Ambiguous, needs judgment |
| Scope Isolation | Single folder, no cross-refs | Cross-cutting changes |

**Calculate total score (out of 25):**
- **≥ 18**: Good candidate for delegation
- **13-17**: Consider carefully, discuss with user
- **≤ 12**: Keep in Cloud

### Step 3: Present Delegation Proposal

**Show the user:**

```markdown
## 🔄 Delegation Proposal

**Task**: [task description]
**Scope**: [scope path or "auto-detected"]

### Triage Score: X/25

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Repetitiveness | ?/5 | [why] |
| Risk Level | ?/5 | [why] |
| Verifiability | ?/5 | [why] |
| Pattern Clarity | ?/5 | [why] |
| Scope Isolation | ?/5 | [why] |

### Recommendation: [Delegate / Consider / Keep in Cloud]

### If Delegated, Gemini Will:
- [specific action 1]
- [specific action 2]
- Run: lint, typecheck, tests

### Cloud Will Verify:
- Diff review for unexpected changes
- Spot-check pattern compliance
- Final acceptance criteria

---

**Proceed with delegation?** (Yes/No)
```

**STOP and wait for user response.**

### Step 4: Generate Handoff Pack (If Approved)

If user approves, delegate to the gemini-delegation agent to generate the Handoff Pack:

```markdown
I need the gemini-delegation agent to generate a Handoff Pack.

Task: [task description]
Scope: [scope path]
Triage Score: [score]/25
User Approval: Confirmed

Generate a complete Handoff Pack with:
- Scoped file list
- Task instructions with before/after examples
- Acceptance criteria (lint/typecheck/tests)
- Required output format for Gemini
- Guardrails and escalation triggers
```

### Step 5: Provide Handoff Instructions

After generating pack:

```markdown
## 📋 Next Steps

1. **Copy the Handoff Pack** above (everything in the code block)
2. **Paste into Gemini** (CLI, AI Studio, or IDE)
3. **Let Gemini complete the work**
4. **Copy Gemini's Completion Report**
5. **Return here** and run: `/delegate-gemini --verify-only`
6. **Paste the report** when prompted

I'll verify the results and either accept or generate a fix-up prompt.
```

### Step 6: Verification Phase (--verify-only)

When user returns with `--verify-only`:

```markdown
Please paste Gemini's Completion Report below.

Expected format:
- Files Modified list
- Commands Run with status
- Diff Summary
- Any Notes or Escalations
```

**After user pastes report:**

```bash
# Run verification commands
npm run lint 2>&1 || echo "Lint issues detected"
npx tsc --noEmit 2>&1 || echo "TypeScript issues detected"
npm test 2>&1 || echo "Test issues or no tests"

# Check for unexpected changes
git status --porcelain
git diff --stat
```

**Spot-check 2-3 modified files** to verify pattern compliance.

**Issue verdict:**

```markdown
## ✅ Verification Passed

All checks pass. Changes are ready for normal workflow (commit, PR, etc.).

---

## ⚠️ Verification Failed

Issues found:
1. [issue description]

Generating fix-up prompt...

[Fix-Up Handoff Pack]
```

---

## Usage Examples

### Basic Delegation Proposal
```bash
/delegate-gemini add JSDoc comments to all exported functions in src/utils/
```

### With Explicit Scope
```bash
/delegate-gemini rename userId to memberId --scope=src/features/membership/
```

### Verify Gemini Results
```bash
/delegate-gemini --verify-only
# Then paste Gemini's completion report
```

### Force Lower Threshold (Edge Case)
```bash
/delegate-gemini complex task description --force-score=15
# Allows delegation even if score is 15-17
```

---

## What Gets Delegated vs. Kept

### ✅ Good for Gemini
- Repetitive renames across many files
- Adding consistent documentation/comments
- Boilerplate generation (CRUD, test stubs)
- Format/lint auto-fixes
- Type definition generation from schemas
- Expanding test cases with patterns

### ❌ Keep in Cloud
- Architecture and design decisions
- Complex business logic implementation
- Security-sensitive code (auth, validation, crypto)
- Cross-cutting refactors
- API contract changes
- Novel problem-solving

---

## Related Commands & Agents

**Agent:**
- `gemini-delegation` - Core delegation orchestrator

**Related Commands:**
- `/loop` - May suggest delegation for repetitive iterations
- `/orchestrator` - Routes to delegation when appropriate
- `/refactor` - For code improvements (Cloud-based)

**Related Skills:**
- `gemini-workflows/handoff-pack` - Structured prompt generator

---

## Important Notes

1. **Always Optional**: You can always say "No" and proceed with normal Cloud work
2. **User Approval Required**: No auto-delegation ever
3. **Verification Mandatory**: Always verify Gemini's output
4. **Fix-Up Loop**: If verification fails, get targeted fix-up prompt
5. **Escalation Path**: Gemini reports blockers, Cloud handles them

---

**Generated**: 2025-01-09 (Gemini Delegation System)
