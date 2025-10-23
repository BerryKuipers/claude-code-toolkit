# Agent Workflow Analysis - Skill Extraction Report

**Analysis Date**: 2025-10-21
**Analyzed**: Conductor, Orchestrator, Implementation, Audit, Refactor agents + AGENTS.md

---

## Executive Summary

After deep analysis of your existing agent workflows, I found **23 repetitive patterns** that should be extracted into skills. The current 4 skills I created are only partially aligned with your actual workflows.

### Critical Findings

✅ **Good**: `gemini-api-rate-limiting` skill accurately captures patterns from your AGENTS.md
❌ **Gap**: Missing GitHub CLI patterns repeated in conductor
❌ **Gap**: Missing state management patterns for workflow resumption
❌ **Gap**: Missing architecture validation patterns from implementation agent
❌ **Gap**: Missing quality baseline patterns from refactor agent

---

## Pattern Analysis by Category

### Category 1: GitHub Integration (6 patterns)

#### Found In: Conductor, Agent-Creator

**Pattern 1.1: Fetch Issue with AI Analysis**
```bash
# Used in: conductor.md Phase 1, Step 1
# Frequency: Every workflow start with issue number

gh issue view [ISSUE_NUMBER] --json labels,title,body
LABELS=$(gh issue view [ISSUE_NUMBER] --json labels --jq '[.labels[].name] | join(",")')

if echo "$LABELS" | grep -q "ai-analyzed"; then
  AI_ANALYSIS=$(gh api repos/$(gh repo view --json nameWithOwner --jq .nameWithOwner)/issues/[ISSUE_NUMBER]/comments --jq '.[] | select(.user.login == "github-actions[bot]" and (.body | contains("AI Issue Analysis"))) | .body')
fi
```

**Should be skill**: `fetch-github-issue-analysis`
**Why**: Repeats in conductor Phase 1, could be used by orchestrator for issue routing

---

**Pattern 1.2: Check Existing PR**
```bash
# Used in: conductor.md Phase 4, resumption logic
# Frequency: Every PR creation phase

gh pr list --head [BRANCH_NAME] --json number,title,url
```

**Should be skill**: `check-existing-pr`
**Why**: Used in resumption logic and before PR creation

---

**Pattern 1.3: Create PR with Structured Body**
```bash
# Used in: conductor.md Phase 4, Step 3
# Frequency: Every feature workflow

gh pr create --title "feat: [TITLE]" --body "[PR_BODY]" --base development --head [BRANCH_NAME]
```

**Already exists**: ✅ `create-pull-request` skill (good!)

---

**Pattern 1.4: Extract AI Analysis Sections**
```markdown
# Used in: conductor.md Phase 1
# Parse AI analysis for:
- Architectural Alignment section
- Technical Feasibility section
- Implementation Suggestions section
- Files/components that will need changes
- Testing strategy suggestions
```

**Should be skill**: `parse-ai-analysis`
**Why**: Complex parsing logic, reusable across orchestrator and conductor

---

**Pattern 1.5: Issue Backlog Selection**
```bash
# Used in: conductor.md Phase 1 (when no issue specified)
# Delegate to orchestrator for:
- Priority levels (p0, p1, p2)
- Cross-feature dependencies
- Sprint alignment
```

**Should be skill**: `select-optimal-issue`
**Why**: Decision logic that could be standardized

---

**Pattern 1.6: Create GitHub Issues for Findings**
```bash
# Used in: audit.md
# Create issues for critical/high findings
gh issue create --title "..." --body "..." --label "tech-debt,critical"
```

**Should be skill**: `create-tracking-issue`
**Why**: Standardize issue creation from audit findings

---

### Category 2: Git Workflow (4 patterns)

#### Found In: Conductor

**Pattern 2.1: Create Feature Branch**
```bash
# Used in: conductor.md Phase 2, Step 1
# Frequency: Every feature workflow

BRANCH_NAME="feature/issue-[ISSUE_NUMBER]-[short-description]"
git checkout development
git pull origin development
git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"
```

**Should be skill**: `create-feature-branch`
**Why**: Naming convention, remote tracking setup

---

**Pattern 2.2: Check Branch Exists (Resumption)**
```bash
# Used in: conductor.md Phase 2, Step 1 (resumption check)
# Frequency: Every workflow start

BRANCH_NAME="feature/issue-$ISSUE_NUMBER-[short-description]"
if git rev-parse --verify "$BRANCH_NAME" 2>/dev/null; then
  echo "✅ Branch already exists: $BRANCH_NAME"
  git checkout "$BRANCH_NAME"
fi
```

**Should be skill**: `check-resume-branch`
**Why**: Part of smart resumption system

---

**Pattern 2.3: Single Atomic Commit**
```bash
# Used in: conductor.md Phase 4, Step 2
# Frequency: Every feature completion

git commit -m "$(cat <<'EOF'
feat: [FEATURE DESCRIPTION]

- Implementation details
- Architecture changes

Fixes #[ISSUE_NUMBER]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Should be skill**: `commit-with-validation`
**Why**: Standardize commit message format, ensure hooks run

---

**Pattern 2.4: Push with Retry**
```bash
# From: CLAUDE.md Git Operations section
# Use exponential backoff for network failures

# Retry logic: 2s, 4s, 8s, 16s for up to 4 attempts
git push -u origin <branch-name>
```

**Should be skill**: `push-with-retry`
**Why**: Network failure handling, exponential backoff

---

### Category 3: State Management (3 patterns)

#### Found In: Conductor

**Pattern 3.1: Save Workflow State**
```bash
# Used in: conductor.md after each phase
# Frequency: 6 times per workflow (after each phase)

mkdir -p .claude/state

cat > .claude/state/conductor.json << EOF
{
  "conductor_version": "1.0",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "workflow": "full-cycle",
  "issue": {
    "number": $ISSUE_NUMBER,
    "title": "$ISSUE_TITLE"
  },
  "currentPhase": $CURRENT_PHASE,
  "completedPhases": [$COMPLETED_PHASES],
  "context": {
    "branchName": "$BRANCH_NAME",
    "prNumber": $PR_NUMBER
  }
}
EOF
```

**Should be skill**: `save-workflow-state`
**Why**: Critical for resumption, repeated 6+ times per workflow

---

**Pattern 3.2: Load Resumption State**
```bash
# Used in: conductor.md at workflow start
# Frequency: Every workflow start

STATE_FILE=".claude/state/conductor.json"

if [ -f "$STATE_FILE" ]; then
  echo "📋 Found previous conductor session"
  cat "$STATE_FILE" | jq '.'
fi

# Analyze git state
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" =~ feature/issue-[0-9]+ ]]; then
  BRANCH_ISSUE=$(echo "$CURRENT_BRANCH" | sed -n 's/.*issue-\([0-9]\+\).*/\1/p')
  # Check commits, PR existence
fi
```

**Should be skill**: `load-resumption-state`
**Why**: Complex logic combining state file + git analysis

---

**Pattern 3.3: Determine Resumption Point**
```bash
# Used in: conductor.md smart resumption
# Decision logic:
- Branch exists + commits + no PR → Phase 3
- Branch exists + no commits → Phase 2 Step 3
- Branch + PR exists → Phase 5
- No branch → Phase 1
```

**Should be skill**: `determine-resumption-phase`
**Why**: Decision tree that repeats

---

### Category 4: Quality Validation (5 patterns)

#### Found In: Refactor, Audit, Conductor

**Pattern 4.1: Run Baseline Tests**
```bash
# Used in: refactor.md Step 1
# Used in: conductor.md Phase 3
# Frequency: Before refactoring, quality gates

npm run test
```

**Already exists**: ✅ `run-comprehensive-tests` skill (good!)

---

**Pattern 4.2: Record Quality Baseline**
```bash
# Used in: refactor.md Step 1
# Frequency: Before any refactoring

npm run audit:code
# Save baseline score for comparison
```

**Should be skill**: `record-quality-baseline`
**Why**: Pre-refactor validation pattern

---

**Pattern 4.3: Validate Quality Gates**
```bash
# Used in: refactor.md Step 3, conductor.md Phase 3
# Frequency: After every code change

npm run test    # Must pass
npm run build   # Must succeed
npm run lint    # Must pass
# Compare audit score to baseline
```

**Already exists**: ✅ `quality-gate` skill (good!)

---

**Pattern 4.4: Type Check Validation**
```bash
# Used in: audit.md, conductor.md Phase 3
# Frequency: Quality gates

npm run type-check
# Or: npx tsc --noEmit
```

**Should be skill**: `validate-typescript`
**Why**: Specific TypeScript validation

---

**Pattern 4.5: Check Coverage Threshold**
```bash
# Used in: audit.md, conductor.md Phase 3
# Parse coverage report, check thresholds

npm run test -- --coverage
# Check: overall ≥ 80%, statement ≥ 80%, branch ≥ 75%
```

**Should be skill**: `validate-coverage-threshold`
**Why**: Threshold checking logic

---

### Category 5: Architecture Validation (3 patterns)

#### Found In: Implementation Agent

**Pattern 5.1: Validate VSA Layer Boundaries**
```typescript
// From: implementation.md
// Controllers CANNOT import Repository implementations
// Services CANNOT import Repository implementations
// Check imports follow VSA rules
```

**Should be skill**: `validate-vsa-boundaries`
**Why**: Critical architecture enforcement

---

**Pattern 5.2: Validate Contract-First**
```bash
# From: implementation.md
# Check that types are defined in @tribevibe/types BEFORE implementation
# Verify no inline types, no `any` types
```

**Should be skill**: `validate-contract-first`
**Why**: Shared pattern across repositories (auto-detects current repo context)

---

**Pattern 5.3: Runtime Dependency Validation**
```typescript
// From: implementation.md
// Every controller must call validateControllerDependencies()
```

**Should be skill**: `check-runtime-validation`
**Why**: Architecture enforcement pattern

---

### Category 6: Domain Knowledge (2 patterns)

#### Found In: AGENTS.md

**Pattern 6.1: Gemini API Sequential Queue**
```typescript
// Already documented in AGENTS.md Gemini API Interaction Guardrails
// Sequential async queue with for...of loop
// 2-second delays between calls
// Promise.race() timeouts
```

**Already exists**: ✅ `gemini-api-rate-limiting` skill (excellent!)

---

**Pattern 6.2: Gemini API Caching Strategy**
```typescript
// From: AGENTS.md Section 3
// Cache versioning: CACHE_VERSION = 'v1'
// Entity-stable keys: `character-portrait:core-pablo`
// Cache busting: forceRebuild flag
```

**Should be skill**: `gemini-api-caching`
**Why**: Complement rate-limiting skill with caching patterns

---

## Priority Skills to Create

### High Priority (Immediate Value)

1. **fetch-github-issue-analysis** - Used in every workflow start
2. **save-workflow-state** - Used 6x per workflow
3. **load-resumption-state** - Used every workflow start
4. **create-feature-branch** - Used every feature workflow
5. **record-quality-baseline** - Used before all refactoring
6. **commit-with-validation** - Used every feature completion

### Medium Priority (Frequent Use)

7. **parse-ai-analysis** - Parse GitHub AI analysis sections
8. **check-existing-pr** - PR resumption logic
9. **validate-typescript** - Type checking
10. **validate-coverage-threshold** - Coverage validation
11. **gemini-api-caching** - Complement rate-limiting

### Lower Priority (Specialized)

12. **select-optimal-issue** - Issue selection logic
13. **create-tracking-issue** - Create issues from findings
14. **determine-resumption-phase** - Decision tree logic
15. **push-with-retry** - Network failure handling
16. **validate-vsa-boundaries** - Architecture enforcement
17. **check-runtime-validation** - Runtime validation checks

---

## Gap Analysis: Current Skills vs Needed

### What We Have (4 skills)

✅ **run-comprehensive-tests** - Matches conductor Phase 3, refactor baseline
✅ **quality-gate** - Matches conductor Phase 3 complete workflow
✅ **create-pull-request** - Matches conductor Phase 4
✅ **gemini-api-rate-limiting** - Matches AGENTS.md patterns perfectly

### What's Missing (High Priority)

❌ **GitHub integration skills** (6 patterns)
❌ **State management skills** (3 patterns)
❌ **Git workflow skills** (4 patterns)
❌ **Quality validation details** (2 patterns)
❌ **Architecture validation** (3 patterns)

---

## Recommendations

### Immediate Actions

1. **Create GitHub Integration Skills**
   - `fetch-github-issue-analysis` - Critical for conductor Phase 1
   - `parse-ai-analysis` - Extract structured data from AI comments
   - `check-existing-pr` - Resumption logic

2. **Create State Management Skills**
   - `save-workflow-state` - Repeats 6x per workflow
   - `load-resumption-state` - Every workflow start
   - `determine-resumption-phase` - Smart resumption logic

3. **Create Git Workflow Skills**
   - `create-feature-branch` - Standard branch creation
   - `commit-with-validation` - Atomic commit pattern
   - `push-with-retry` - Network failure handling

### Next Wave

4. **Quality Validation Details**
   - `record-quality-baseline` - Pre-refactor baseline
   - `validate-typescript` - Type checking
   - `validate-coverage-threshold` - Coverage checks

5. **Architecture Validation** (if applicable to WescoBar)
   - `validate-vsa-boundaries` - Layer enforcement
   - `validate-contract-first` - Contract-first checks

### Long Term

6. **Gemini API Expansion**
   - `gemini-api-caching` - Cache patterns
   - `gemini-api-error-handling` - Error recovery
   - `gemini-api-image-generation` - Complete workflow

---

## Usage Impact Analysis

### Conductor Agent

**Current**: 2,433 lines with inline patterns
**With Skills**: Estimated ~1,800 lines (26% reduction)

**Phases Affected**:
- Phase 1: Use `fetch-github-issue-analysis`, `parse-ai-analysis`
- Phase 2: Use `create-feature-branch`, `check-resume-branch`
- Phase 3: Already uses `quality-gate` ✅
- Phase 4: Already uses `create-pull-request` ✅
- Throughout: Use `save-workflow-state`

### Refactor Agent

**Current**: Inline quality baseline logic
**With Skills**: Use `record-quality-baseline`, `quality-gate`

### Audit Agent

**Current**: Multiple npm commands
**With Skills**: Use `validate-typescript`, `validate-coverage-threshold`

---

## Conclusion

**Current Skills**: 4 created, 2 well-aligned (50%)
**Needed Skills**: 23 patterns identified
**Priority Gap**: 6 high-priority skills missing
**Impact**: Could reduce conductor from 2,433 to ~1,800 lines

### Next Steps

1. ✅ Acknowledge analysis findings
2. Create 6 high-priority skills first
3. Update conductor to reference new skills
4. Test end-to-end workflow
5. Create remaining skills iteratively

---

**Generated**: 2025-10-21
**Analyzed Lines**: ~8,000 across 5 agents
**Patterns Found**: 23 repetitive operations
**Skills Recommended**: 17 additional skills
