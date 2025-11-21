---
name: pick-next-pr
description: Intelligently evaluate and pick the safest next open PR to work on, considering recent architectural changes and conflict risk
---

# Automated PR Evaluation & Pickup Workflow

You are conducting a comprehensive PR triage and autonomous pickup workflow.

## Context Awareness

The user may provide context about recent merges that could affect open PRs:
- Recent architectural changes (middleware, refactors, type safety)
- Breaking changes in services, controllers, DTOs
- Infrastructure changes (database, API routes)
- Pattern updates (SOLID, DRY improvements)

**Always ask the user if they want to provide context about recent merges before proceeding.**

---

## Phase 0: Sync Toolkit & Prepare Environment

**CRITICAL: Always sync toolkit first to use latest agents**

```bash
# Sync toolkit submodule
git submodule update --remote --merge

# Pull latest agent updates
cd path/to/toolkit && git pull origin main

# Return to project root
cd -
```

**Verify branch state:**
```bash
# Ensure we're starting from clean state
git status

# Update development/main branch
git checkout development
git pull origin development
```

---

## Phase 1: Fetch & Catalog Open PRs

**Use GitHub CLI to get all open PRs:**

```bash
gh pr list --state open --json number,title,headRefName,createdAt,updatedAt,additions,deletions,changedFiles,author --limit 100
```

**Create a catalog with:**
- PR number
- Title
- Branch name
- Created date
- Last updated date
- Size (additions + deletions)
- Changed files count
- Author

**Save to:** `.claude/agent-sessions/pr-catalog-$(date +%Y%m%d-%H%M%S).json`

---

## Phase 2: Evaluate Each PR

**For EACH open PR, analyze:**

### 2.1 Age & Staleness
```bash
# Get branch divergence from development
git fetch origin
git rev-list --left-right --count origin/{branch}...origin/development
```

**Questions:**
- How many commits behind development?
- Was it created BEFORE recent architectural changes?
- Has it been updated recently?

### 2.2 Conflict Risk Analysis

**Check for potential conflicts:**
```bash
# Simulate merge (don't commit)
git checkout {branch}
git merge --no-commit --no-ff origin/development

# Check conflict files
git diff --name-only --diff-filter=U

# Abort simulation
git merge --abort
```

**Analyze conflict areas:**
- Are conflicts in core files (services, controllers, repositories)?
- Do they touch recently refactored code?
- Are conflicts simple (whitespace, imports) or complex (logic)?

### 2.3 Architectural Compatibility

**Check if PR touches recently changed patterns:**

Based on user-provided context (e.g., universeId middleware), check:
```bash
# Search for old patterns that conflict with new architecture
grep -r "old-pattern" {branch-files}

# Check if PR uses new patterns
grep -r "new-pattern" {branch-files}
```

**Example checks:**
- Does PR manually pass `universeId` (old) vs using middleware injection (new)?
- Does PR use loose typing (old) vs strict DTOs (new)?
- Does PR violate SOLID principles that were recently fixed?

### 2.4 Dependency Analysis

**Check if PR depends on or blocks other PRs:**
```bash
# Check PR description and comments for dependencies
gh pr view {number} --json body,comments

# Look for "depends on", "blocked by", "prerequisite" mentions
```

---

## Phase 3: Risk Scoring

**Score each PR on multiple dimensions:**

### Conflict Risk (0-10, lower is better)
- 0-2: No conflicts, clean merge
- 3-5: Minor conflicts (imports, formatting)
- 6-8: Moderate conflicts (logic changes)
- 9-10: Severe conflicts (core architecture)

### Staleness (0-10, lower is better)
- 0-2: Created after recent changes, up to date
- 3-5: Created before recent changes, small divergence
- 6-8: Old branch, significant divergence
- 9-10: Very stale, massive divergence

### Complexity (0-10, lower is better)
- 0-2: Small PR (<100 lines), focused changes
- 3-5: Medium PR (100-500 lines), well-scoped
- 6-8: Large PR (500-1000 lines), multiple concerns
- 9-10: Huge PR (>1000 lines), refactor or feature

### Architecture Alignment (0-10, higher is better)
- 0-2: Violates new patterns, needs major refactor
- 3-5: Partially aligned, needs updates
- 6-8: Mostly aligned, minor updates needed
- 9-10: Fully aligned with new architecture

### Strategic Value (0-10, higher is better)
- 0-2: Low priority, nice-to-have
- 3-5: Normal priority
- 6-8: Important, unblocks other work
- 9-10: Critical, blocks multiple PRs

**Calculate Total Risk Score:**
```
Risk Score = (Conflict Risk * 0.3) + (Staleness * 0.2) + (Complexity * 0.2) - (Architecture Alignment * 0.15) - (Strategic Value * 0.15)
```

**Lower risk score = better candidate**

---

## Phase 4: Ranking & Selection

**Create ranked list:**

1. Sort by Risk Score (ascending)
2. Group by risk tier:
   - **Safe** (Risk Score < 3.0)
   - **Moderate** (Risk Score 3.0-5.0)
   - **Risky** (Risk Score 5.0-7.0)
   - **High Risk** (Risk Score > 7.0)

**Present to user:**

```markdown
## PR Evaluation Results

### Safe Candidates (Risk Score < 3.0)
1. PR #123: feat: Add user profile settings (Risk: 2.1)
   - Conflicts: None
   - Staleness: Low (2 days old)
   - Complexity: Small (87 lines)
   - Architecture: Fully aligned
   - Strategic: Normal priority

2. PR #456: fix: Resolve character duplication bug (Risk: 2.5)
   ...

### Moderate Risk (Risk Score 3.0-5.0)
...

### Recommended Pick: PR #{number}

**Reasoning:**
- Lowest conflict risk among open PRs
- Created after recent architectural changes
- Small, focused scope
- Doesn't block other PRs
- Good strategic value
```

**Wait for user confirmation before proceeding.**

---

## Phase 5: Autonomous PR Pickup & Resolution

**Once user confirms the PR to work on:**

### 5.1 Create TodoWrite Plan

```javascript
[
  { content: "Checkout and sync PR branch", status: "pending", activeForm: "Checking out PR branch" },
  { content: "Merge development and resolve conflicts", status: "pending", activeForm: "Merging and resolving conflicts" },
  { content: "Run architect agent for structural validation", status: "pending", activeForm: "Running architect validation" },
  { content: "Update code for new architecture patterns", status: "pending", activeForm: "Updating architecture patterns" },
  { content: "Run code-reviewer agent for quality check", status: "pending", activeForm: "Running code review" },
  { content: "Run tests and validate build", status: "pending", activeForm: "Running tests" },
  { content: "Generate PR update summary", status: "pending", activeForm: "Generating summary" }
]
```

### 5.2 Checkout & Sync Branch

```bash
# Checkout PR branch
git checkout {branch-name}

# Merge development
git pull origin development

# Check for conflicts
if git diff --name-only --diff-filter=U | grep -q .; then
  echo "⚠️  Conflicts detected - will resolve"
else
  echo "✅ Clean merge"
fi
```

**Mark first todo as completed, second as in_progress.**

### 5.3 Resolve Conflicts (If Any)

**For each conflicted file:**

1. **Read the conflict:**
   ```bash
   cat {conflicted-file}
   ```

2. **Understand both sides:**
   - What did the PR change?
   - What changed in development?
   - Which takes precedence?

3. **Resolve intelligently:**
   - Apply new architecture patterns (e.g., universeId middleware)
   - Preserve PR's functionality
   - Remove old patterns
   - Ensure type safety

4. **Mark resolved:**
   ```bash
   git add {resolved-file}
   ```

**Mark conflict resolution todo as completed.**

### 5.4 Architect Agent Review

**Invoke architect agent for structural validation:**

> I need the architect agent to validate PR #{number} against our current architecture.
>
> **PR Context:**
> - Title: {pr-title}
> - Branch: {branch-name}
> - Changes: {summary-of-changes}
>
> **Recent Architecture Updates:**
> {user-provided-context}
>
> **Validation Required:**
> - VSA structure compliance
> - SOLID principles adherence
> - Layer boundary enforcement
> - Contract-first development
> - Integration with new patterns (e.g., universeId middleware)
>
> **Files to Review:**
> {list-of-changed-files}
>
> Please identify any architectural violations and recommend fixes.

**Wait for architect agent completion. Mark todo as completed.**

### 5.5 Apply Architecture Updates

**Based on architect recommendations:**

1. Update services to use new patterns
2. Fix layer boundary violations
3. Improve type safety
4. Apply SOLID/DRY improvements
5. Integrate with new middleware/infrastructure

**Example updates:**
```typescript
// Before (old pattern)
async getProfile(userId: string, universeId: string) {
  const profile = await this.prisma.profile.findUnique({
    where: { userId, universeId }
  });
}

// After (new pattern with middleware injection)
async getProfile(userId: string) {
  // universeId injected via middleware in req.universeId
  const profile = await this.prisma.profile.findUnique({
    where: { userId, universeId: this.universeId }
  });
}
```

**Mark architecture updates todo as completed.**

### 5.6 Code Reviewer Agent

**Invoke code-reviewer agent:**

> I need the code-reviewer agent to review the updated PR #{number}.
>
> **Changes Made:**
> - Merged development
> - Resolved conflicts
> - Applied architecture updates
>
> **Review Focus:**
> - Code quality
> - Bug risks
> - Missing error handling
> - Test coverage
> - Documentation completeness
>
> **Files to Review:**
> {list-of-changed-files}

**Wait for code-reviewer completion. Mark todo as completed.**

### 5.7 Apply Code Quality Fixes

**Based on code-reviewer recommendations:**

1. Fix identified bugs
2. Add error handling
3. Improve variable names
4. Add missing tests
5. Update documentation

**Mark code quality todo as completed.**

### 5.8 Run Tests & Validate Build

```bash
# Run tests
npm test

# Run build
npm run build

# Run lint
npm run lint

# Run type check
npm run type-check
```

**If tests fail:**
- Investigate failures
- Fix issues
- Re-run tests
- Don't proceed until all pass

**Mark tests todo as completed.**

### 5.9 Generate Summary

**Create comprehensive summary:**

```markdown
## PR #{number} Update Summary

### Original PR
- **Title:** {title}
- **Author:** {author}
- **Created:** {created-date}
- **Branch:** {branch-name}

### Recent Context
{user-provided-context-about-recent-merges}

### Conflicts Resolved
- {file1}: {conflict-description} → {resolution}
- {file2}: {conflict-description} → {resolution}

### Architecture Updates Applied
- ✅ Integrated universeId middleware injection
- ✅ Updated service layer to use strict types
- ✅ Fixed SOLID principle violations
- ✅ Applied DRY improvements

### Code Quality Improvements
- ✅ Added error handling for {scenario}
- ✅ Improved type safety in {component}
- ✅ Added missing tests for {feature}

### Test Results
- ✅ All tests passing ({count} tests)
- ✅ Build successful
- ✅ Lint clean
- ✅ Type check passed

### Files Modified
{list-of-files-changed}

### Next Steps
1. Review the changes manually if desired
2. Push updated branch: `git push origin {branch-name}`
3. Update PR description with migration notes
4. Request re-review from team
5. Merge when approved

### Recommendations
{any-additional-recommendations}
```

**Mark summary todo as completed.**

---

## Phase 6: Completion & Next Steps

**Present summary to user and ask:**

1. **Do you want to push the changes?**
   ```bash
   git push origin {branch-name}
   ```

2. **Do you want to update the PR description?**
   ```bash
   gh pr edit {number} --body "{updated-description}"
   ```

3. **Do you want to pick another PR?**
   - Re-run evaluation excluding completed PR
   - Continue with next safest PR

4. **Do you want to run parallel PR updates?**
   - Identify multiple safe PRs
   - Launch parallel agents for each
   - Monitor progress
   - Merge in sequence

---

## Important Rules

### Branch Management
- ✅ Stay on the same branch during entire execution
- ✅ Never create new branches
- ✅ Never switch branches mid-execution
- ❌ DON'T merge PRs automatically (user approval required)

### Agent Coordination
- ✅ Use TodoWrite throughout to track progress
- ✅ Run agents sequentially (architect → code-reviewer → tests)
- ✅ Wait for agent completion before proceeding
- ✅ Apply agent recommendations systematically

### Parallel Execution
When user requests parallel PR updates:
- Launch separate agent per PR
- Each agent follows this workflow
- Agents work on different branches (no conflicts)
- Coordinate merges sequentially after all complete

### Conflict Resolution
- ✅ Prioritize new architecture patterns
- ✅ Preserve PR's functional intent
- ✅ Remove deprecated patterns
- ✅ Ensure type safety and SOLID compliance

### Quality Gates
- ✅ All tests must pass before completion
- ✅ Build must succeed
- ✅ Lint must be clean
- ✅ Type checks must pass
- ✅ Architect validation must approve

---

## Example Usage

```bash
# User runs the command
/pick-next-pr

# Agent asks for context
> Any recent merges I should know about that might affect open PRs?

# User provides context
> Yes, we just merged:
> - feat: Auto-inject universeId via middleware
> - refactor: Remove mockApiService
> - feat: Tailwind theme generation

# Agent proceeds with evaluation...
# Presents ranked PRs...
# User selects PR #123...
# Agent executes autonomous pickup...
# Presents summary...
# Done!
```

---

**Remember:** This is a powerful automation - always present findings and wait for user confirmation before executing major changes.
