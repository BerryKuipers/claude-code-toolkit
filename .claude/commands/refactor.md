# Clean Code Refactor Command

**Arguments:**
- `target` *(required)*: file/class/function path to refactor
- `strategy` *(optional)*: extract|rename|simplify|auto (default: auto)
- `dryRun` *(boolean)*: analysis only, no commits (default: false)
- `maxSteps` *(int)*: max refactor iterations (default: 1)

**Success Criteria:** Zero test failures, improved audit score, atomic commits with clear improvements

**Description:** Scoped, safe refactoring following Uncle Bob's Clean Code principles. Refactors small units (≤30 lines) with automated validation gates (tests + audit + build).

---

## ⚠️ Important: Scoped Refactoring Tool Only

**This command performs SCOPED REFACTORING ONLY** - it does NOT orchestrate other commands.

**Scope:**
- ✅ Read target file/function
- ✅ Apply refactoring strategy (≤30 lines per iteration)
- ✅ Validate tests + audit + build after each change
- ✅ Create atomic commits for successful refactorings
- ❌ Does NOT orchestrate other commands
- ❌ Does NOT analyze broader architecture (use `/architect` for that)

**Intended to be called by:** OrchestratorAgent, workflows, or direct user invocation

---

## Refactoring Strategies

### **extract**: Extract Method/Function
Identify code blocks doing one thing, extract to well-named function

### **rename**: Rename for Clarity
Replace cryptic names with intention-revealing names

### **simplify**: Simplify Logic
Remove unnecessary nesting, replace complex conditionals with guard clauses

### **auto**: Auto-Select Strategy (Default)
Analyze code and choose optimal strategy

---

## Usage

```bash
# Basic refactoring
/refactor --target=UserService.ts

# Multiple iterations
/refactor --target=UserService.ts --maxSteps=3

# Dry run analysis
/refactor --target=UserService.ts --dryRun=true

# Specific strategy
/refactor --target=UserService.ts --strategy=extract
```

---

## Refactoring Workflow

### Step 1: Pre-Refactor Validation

**Run baseline tests:**
```bash
npm run test
```

**Expected**: All tests passing

**If tests fail:**
```markdown
❌ Cannot proceed - tests failing before refactoring
**Action**: Fix existing test failures first
```

**Run baseline audit:**
```bash
npm run audit:code
```

**Record baseline score** for comparison after refactoring.

### Step 2: Target Analysis

**Read target file:**
```bash
cat ${targetFile}
```

**Analyze complexity:**
- Lines of code (LOC)
- Cyclomatic complexity
- Nesting depth
- Function length
- Code smells

**Example analysis:**
```markdown
### Target: `MatchService.ts`
- **LOC**: 450 lines
- **Functions**: 18 (3 over 50 lines)
- **Max Nesting**: 5 levels
- **Complexity**: High
- **Smells**: Long functions, deep nesting, duplicate logic
```

### Step 3: Identify Refactor Scope

**Scope to ≤30 lines per iteration:**

```markdown
### Refactor Target: `MatchService.createMatch()` (Lines 45-78)
**Issue**: 34 lines, nested 4 levels deep
**Strategy**: Extract validation logic to `validateMatchCriteria()`
**Expected**: Reduce nesting to 2 levels, improve readability
```

**Important**: If file >200 lines, break into multiple iterations

### Step 4: Execute Refactor

**Read current implementation:**
```typescript
// Before refactoring
async createMatch(userId: string, targetId: string): Promise<Match> {
  if (!userId) throw new Error('User ID required');
  if (!targetId) throw new Error('Target ID required');

  const user = await this.userRepo.findById(userId);
  if (!user) throw new Error('User not found');

  const target = await this.userRepo.findById(targetId);
  if (!target) throw new Error('Target not found');

  // ... 25 more lines of nested logic
}
```

**Apply refactoring:**
```typescript
// After refactoring
async createMatch(userId: string, targetId: string): Promise<Match> {
  const { user, target } = await this.validateMatchParticipants(userId, targetId);
  const criteria = await this.buildMatchCriteria(user, target);
  return await this.matchRepo.create(criteria);
}

private async validateMatchParticipants(userId: string, targetId: string) {
  if (!userId) throw new Error('User ID required');
  if (!targetId) throw new Error('Target ID required');

  const user = await this.userRepo.findById(userId);
  if (!user) throw new Error('User not found');

  const target = await this.userRepo.findById(targetId);
  if (!target) throw new Error('Target not found');

  return { user, target };
}
```

**Use Edit tool for precise changes:**
```typescript
Edit({
  file_path: targetFile,
  old_string: "... exact old code ...",
  new_string: "... exact new code ..."
});
```

### Step 5: Validation (Critical!)

**Run tests immediately:**
```bash
npm run test
```

**Expected**: All tests still passing

**If tests fail:**
```markdown
❌ Refactor broke tests - REVERT CHANGES
**Action**: git restore ${targetFile}
```

**Run audit comparison:**
```bash
npm run audit:code
```

**Compare scores:**
```markdown
### Audit Score Comparison
**Before**: 7.2/10
**After**: 8.1/10
**Improvement**: +0.9 points ✅
```

**If audit score decreased:**
```markdown
⚠️  Audit score decreased - review refactor quality
**Action**: Review and adjust or revert
```

**Run build validation:**
```bash
npm run build
```

**Expected**: Clean build, no type errors

### Step 6: Commit Atomic Change

**If all validations pass:**
```bash
git add ${targetFile}

git commit -m "$(cat <<'EOF'
refactor: extract validation logic in MatchService.createMatch

- Extracted validateMatchParticipants() for clarity
- Reduced nesting from 4 to 2 levels
- Improved readability (audit score: +0.9)
- All tests passing
- No behavior change

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Important**: One commit per successful refactor iteration

### Step 7: Iterate or Complete

**If more refactoring needed (maxSteps not reached):**
```markdown
✅ Iteration 1 complete
📊 Progress: 1/3 functions refactored
🎯 Next: Refactor `MatchService.updateMatch()` (Lines 120-165)
```

Repeat steps 3-6 for next iteration.

**If refactoring complete:**
```markdown
✅ Refactoring complete
📊 Total improvements:
- 3 functions refactored
- Complexity reduced: High → Medium
- Audit score improved: 7.2 → 8.8 (+1.6)
- All tests passing
- 3 atomic commits created
```

---

## Iteration Control

### Max Steps
Default: 1 iteration

**Example with 3 iterations:**
```bash
/refactor --target=MatchService.ts --maxSteps=3

# Results in:
# Iteration 1: Extract validateMatchParticipants() → Commit
# Iteration 2: Extract buildMatchCriteria() → Commit
# Iteration 3: Simplify error handling → Commit
```

### Dry Run
Analysis only, no code changes:
```bash
/refactor --target=MatchService.ts --dryRun=true

# Output:
# 📋 Refactor Analysis (Dry Run)
# Would refactor:
# 1. createMatch() - Extract validation (Lines 45-78)
# 2. updateMatch() - Simplify conditionals (Lines 120-165)
# Estimated impact: Audit score +1.5, complexity reduction 30%
```

---

## Refactoring Patterns

### Pattern 1: Extract Method
**When**: Function >30 lines or doing multiple things
**How**: Extract cohesive blocks to named functions

### Pattern 2: Replace Conditionals with Polymorphism
**When**: Large switch/if-else chains
**How**: Create strategy classes or use function maps

### Pattern 3: Introduce Parameter Object
**When**: Function has >3 parameters
**How**: Group related parameters into object

### Pattern 4: Replace Magic Numbers with Named Constants
**When**: Unexplained literals in code
**How**: Extract to named constants

### Pattern 5: Consolidate Duplicate Code
**When**: Same logic in multiple places
**How**: Extract to shared utility function

---

## Success Criteria

A refactoring is successful when:
1. ✅ All tests pass before and after
2. ✅ Audit score improves (or stays same for renames)
3. ✅ Build completes without errors
4. ✅ Code is more readable/maintainable
5. ✅ Behavior unchanged (no functional changes)
6. ✅ Atomic commit created with clear message

---

## Critical Rules

### ❌ NEVER Do These:
1. Refactor without passing tests
2. Change behavior (refactoring preserves functionality)
3. Large refactors (keep iterations ≤30 lines)
4. Skip validation (always test + audit + build)
5. Batch commits (one commit per iteration)
6. Orchestrate other commands (let OrchestratorAgent do that)

### ✅ ALWAYS Do These:
1. Run tests first (establish passing baseline)
2. Small iterations (atomic, focused changes)
3. Validate after each (tests + audit + build)
4. Commit immediately (don't accumulate changes)
5. Improve scores (audit score should increase)

---

## Error Handling

### Tests Fail After Refactor
```markdown
❌ Tests broken by refactor
**Action**: git restore ${targetFile}
**Next**: Analyze why tests failed, adjust strategy
```

### Audit Score Decreased
```markdown
⚠️  Audit score worsened
**Before**: 8.2/10
**After**: 7.5/10 (-0.7)
**Action**: Review refactor, consider different approach or revert
```

### Build Fails
```markdown
❌ TypeScript compilation errors
**Action**: Fix type errors or revert
**Common Causes**: Renamed function not updated everywhere, type mismatches
```

---

## Integration Points

### Called by OrchestratorAgent
```typescript
// OrchestratorAgent invokes this for refactoring tasks
await delegate("/refactor", { target: "UserService.ts", maxSteps: 3 });
```

### Called by Users
```bash
/refactor --target=UserService.ts --maxSteps=3
```

### Does NOT Invoke Other Commands
This command is self-contained and does not delegate to other commands.

---

## Configuration

Settings in `.claude/config.yml`:

```yaml
validation:
  requireTestsBeforeRefactor: true
  requireAuditBaseline: true
  requireBuildValidation: true
  autoRevertOnFailure: true

safety:
  maxRefactorFileSizeBytes: 100000  # 100KB max file size
```

---

## Examples

### Example 1: Basic Refactoring
```bash
/refactor --target=UserService.ts
# Output: 1 iteration, audit score improved
```

### Example 2: Multiple Iterations
```bash
/refactor --target=UserService.ts --maxSteps=3
# Output: 3 iterations, 3 commits, significant improvement
```

### Example 3: Dry Run
```bash
/refactor --target=UserService.ts --dryRun=true
# Output: Analysis only, no changes made
```

---

## Related Documentation

- **Clean Code Principles**: Robert C. Martin's "Clean Code"
- **Agent Architecture**: `docs/agents-architecture.md`
- **Refactor Agent**: `.claude/agents/refactor.md`

---

## Summary

**This is a scoped refactoring tool.** It refactors specific files/functions with validation.

**It does NOT:** Orchestrate workflows, analyze broader architecture, or coordinate other commands.

**For orchestration:** Use OrchestratorAgent or invoke this command as part of a workflow.

**For architecture analysis:** Use `/architect` command.
