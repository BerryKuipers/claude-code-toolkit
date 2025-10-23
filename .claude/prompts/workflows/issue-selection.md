# GitHub Issue Selection Prompt

**Purpose**: Intelligently select the best next GitHub issue to work on based on multiple factors.

## Context

You are helping prioritize and select the optimal GitHub issue from a repository's issue backlog. Consider multiple dimensions to make the best choice.

## Selection Criteria

### Priority Factors (Weighted)

1. **Impact (40%)**
   - User-facing improvements (high)
   - Bug fixes affecting many users (high)
   - Technical debt that blocks other work (high)
   - Nice-to-have features (medium)
   - Minor improvements (low)

2. **Effort (25%)**
   - Quick wins (<2 hours) preferred
   - Medium effort (2-8 hours) acceptable
   - Large effort (>8 hours) requires high impact justification

3. **Dependencies (20%)**
   - No blockers (preferred)
   - Has prerequisites (requires context)
   - Blocks other issues (prioritize)

4. **Context Availability (15%)**
   - Clear requirements and acceptance criteria (preferred)
   - Needs clarification (deprioritize unless critical)
   - Has implementation hints (bonus)

## Analysis Template

For each candidate issue, analyze:

```markdown
## Issue #[NUMBER]: [TITLE]

**Impact**: [High/Medium/Low]
- User impact: [description]
- Technical impact: [description]

**Effort**: [Quick Win/Medium/Large] (~[X] hours)
- Implementation complexity: [assessment]
- Testing requirements: [assessment]
- Risk level: [Low/Medium/High]

**Dependencies**:
- Blocks: [list of issues]
- Blocked by: [list of issues]
- Related: [list of issues]

**Context Clarity**: [Clear/Needs Clarification/Ambiguous]
- Requirements: [assessment]
- Acceptance criteria: [present/missing]
- Implementation hints: [available/not available]

**Priority Score**: [calculated score out of 100]
```

## Decision Framework

### Selection Rules

1. **Prefer quick wins with high impact**
   - Score: Impact × 0.4 + (1/Effort) × 0.25 + Dependencies × 0.2 + Context × 0.15

2. **Avoid unclear requirements unless critical**
   - If Impact = High AND Context = Ambiguous → Ask for clarification first

3. **Consider flow and momentum**
   - Related issues in same area → Better context, faster progress
   - Context switching → Additional overhead

4. **Balance short-term and long-term value**
   - Don't only pick quick wins
   - Allocate time for technical debt

## Prompt Template

```markdown
I need to select the best next GitHub issue to work on.

Repository: [REPO_NAME]
Current sprint/milestone: [MILESTONE]
Team focus: [FOCUS_AREAS]

Available issues (from gh issue list):
[PASTE ISSUE LIST]

Additional context:
- Recent work: [DESCRIPTION]
- Team capacity: [AVAILABLE_HOURS]
- Upcoming deadlines: [DEADLINES]

Please:
1. Analyze top 5 candidate issues using the analysis template
2. Calculate priority scores
3. Recommend the best issue to work on next
4. Explain the reasoning
5. Identify any prerequisites or clarifications needed
```

## Example Output

```markdown
# Issue Selection Analysis

## Top 5 Candidates

### 1. Issue #42: Fix login redirect loop (RECOMMENDED)
**Priority Score: 92/100**
- Impact: High (affects all users, critical bug)
- Effort: Quick Win (~1.5 hours)
- Dependencies: None, blocks issue #45
- Context: Clear with reproduction steps

**Recommendation**: START NOW
- High impact bug affecting production users
- Quick to fix (redirect logic in auth middleware)
- Unblocks premium feature issue #45
- Clear reproduction and acceptance criteria

### 2. Issue #38: Add user profile export
**Priority Score: 68/100**
- Impact: Medium (requested feature, GDPR compliance)
- Effort: Medium (~4 hours)
- Dependencies: None
- Context: Clear requirements

**Recommendation**: NEXT IN QUEUE
- Good feature for next session
- Well-defined scope

### 3. Issue #51: Refactor database queries
**Priority Score: 65/100**
- Impact: High (performance, technical debt)
- Effort: Large (~8 hours)
- Dependencies: None, but provides foundation for #52, #53
- Context: Needs investigation

**Recommendation**: SCHEDULE DEDICATED TIME
- High value but requires focused time block
- Consider breaking into smaller issues

### 4. Issue #29: Dark mode toggle
**Priority Score: 45/100**
- Impact: Medium (nice-to-have)
- Effort: Medium (~5 hours)
- Dependencies: Blocked by #38 (theme system)
- Context: Clear

**Recommendation**: WAIT
- Blocked by theme system work
- Revisit after #38 complete

### 5. Issue #67: Add webhook notifications
**Priority Score: 40/100**
- Impact: Low (requested by 1 user)
- Effort: Large (~10 hours)
- Dependencies: None
- Context: Ambiguous (needs clarification on use case)

**Recommendation**: DEFER
- Request more details from user
- Low priority vs other work

## Selected Issue: #42 - Fix login redirect loop

**Why this issue:**
✅ Critical bug affecting all users (high impact)
✅ Quick to implement (1.5 hours estimated)
✅ Clear reproduction steps and acceptance criteria
✅ Unblocks premium feature work (#45)
✅ Low risk (isolated to auth middleware)

**Next steps:**
1. Assign issue to self
2. Create feature branch: fix/login-redirect-loop
3. Reproduce bug locally
4. Implement fix in auth middleware
5. Add regression test
6. Create PR with fix
```

## Usage in Conductor Workflow

```markdown
# In conductor agent or workflow

Step 1: Fetch open issues
gh issue list --repo [REPO] --state open --json number,title,labels,body --limit 20

Step 2: Use this prompt template to analyze issues

Step 3: Get recommendation with priority scores

Step 4: Proceed with selected issue
- Create branch
- Invoke implementation agent
- Run tests
- Create PR
```

## Customization

Adjust weights based on your project needs:

```markdown
# For bug-focused projects
Impact: 50% (prioritize bugs)
Effort: 20%
Dependencies: 20%
Context: 10%

# For feature velocity projects
Impact: 30%
Effort: 35% (prefer quick wins)
Dependencies: 20%
Context: 15%

# For technical debt paydown
Impact: 35%
Effort: 15% (accept larger work)
Dependencies: 35% (unblock work)
Context: 15%
```

## Notes

- This prompt is reusable across all repos
- Update weights based on project phase
- Consider team capacity and sprint goals
- Balance quick wins with strategic work
- Don't always pick the highest score (context switching has cost)
