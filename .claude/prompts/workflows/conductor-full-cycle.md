# Conductor Full-Cycle Workflow

**Purpose:** Complete end-to-end workflow from issue selection → implementation → PR → merge using parallel agents and workflow prompts.

## Overview

This workflow coordinates the complete development cycle using the conductor agent with workflow prompts for consistent, efficient execution.

## Full Cycle Phases

### Phase 1: Issue Selection
### Phase 2: Planning & Decomposition
### Phase 3: Parallel Implementation
### Phase 4: Testing & Validation
### Phase 5: PR Creation
### Phase 6: Review Response
### Phase 7: Merge & Close

## Detailed Workflow

### Phase 1: Issue Selection (5-10 min)

**Goal:** Select the highest-value issue to work on

**Steps:**

1. **Fetch open issues**
```bash
gh issue list --repo {owner}/{repo} --state open --json number,title,labels,body,createdAt --limit 20
```

2. **Apply issue-selection prompt**
```markdown
"Use the issue-selection prompt to analyze these GitHub issues.

Repository: {repo-name}
Current focus: {sprint-goal}
Available time: {hours}
Recent work: {context}

Issues:
[paste gh issue list output]

Please:
1. Analyze top 5 candidates with scoring
2. Recommend best issue
3. Explain reasoning
4. Identify prerequisites"
```

3. **Review recommendation and proceed**

**Output:**
- Selected issue number
- Priority score
- Estimated effort
- Prerequisites identified

---

### Phase 2: Planning & Decomposition (10-15 min)

**Goal:** Break down issue into parallel subtasks

**Steps:**

1. **Read issue details**
```bash
gh issue view {issue-number} --json title,body,comments
```

2. **Analyze and decompose**
```markdown
"Analyze issue #{issue-number} and use parallel-agents coordination prompt to decompose into subtasks.

Issue: {title}
Description: {body}

Please:
1. Break into independent subtasks
2. Analyze dependencies
3. Identify parallelizable work
4. Create execution plan with phases
5. Estimate time per subtask"
```

3. **Create TodoWrite task list**
```markdown
TodoWrite:
- [ ] Subtask 1: {description} (Agent: {agent-name}, Time: {estimate})
- [ ] Subtask 2: {description} (Agent: {agent-name}, Time: {estimate})
- [ ] Subtask 3: {description} (Agent: {agent-name}, Time: {estimate})
```

**Output:**
- Task breakdown
- Dependency graph
- Parallel execution plan
- Time estimate

---

### Phase 3: Parallel Implementation (30-90 min)

**Goal:** Execute subtasks in parallel using specialized agents

**Steps:**

1. **Create feature branch**
```bash
git checkout -b {branch-name}
# Example: feature/user-preferences-#{issue-number}
```

2. **Launch parallel agents (single message with multiple Task calls)**
```markdown
# For independent subtasks, launch in parallel

Task(database, "Create {feature} database schema:
- Table: {table-name}
- Columns: {columns}
- Constraints: {constraints}
Issue: #{issue-number}")

Task(implementation, "Implement {feature} backend API:
- Endpoints: {endpoints}
- Validation: {rules}
- Tests: {test-cases}
Issue: #{issue-number}")

Task(implementation, "Implement {feature} frontend UI:
- Components: {components}
- User flow: {flow}
- Tests: {test-cases}
Issue: #{issue-number}")
```

3. **Monitor parallel execution**
```markdown
# TodoWrite updates as agents complete
✅ Subtask 1: Database schema created
🔄 Subtask 2: Backend API in progress
🔄 Subtask 3: Frontend UI in progress
```

4. **Handle agent completion**
- Collect results from each agent
- Review implementations
- Check for integration issues

**Output:**
- All subtasks completed
- Code changes in feature branch
- Tests passing locally

---

### Phase 4: Testing & Validation (15-30 min)

**Goal:** Comprehensive testing before creating PR

**Steps:**

1. **Run test suite**
```bash
npm test                    # Unit + integration tests
npm run test:e2e           # E2E tests (if applicable)
npm run lint               # Linting
npm run type-check         # TypeScript (if applicable)
```

2. **Browser testing (if UI changes)**
```markdown
/test-ui --feature="{feature-name}" --baseline

# If regression testing
/test-ui --feature="{feature-name}" --compare=/tmp/baseline.png
```

3. **Manual testing checklist**
```markdown
TodoWrite:
- [ ] Feature works as expected
- [ ] No console errors
- [ ] No visual regressions
- [ ] Accessibility checks pass
- [ ] Mobile responsive (if applicable)
```

4. **Fix any issues discovered**

**Output:**
- All tests passing
- No console errors
- Feature validated

---

### Phase 5: PR Creation (10-15 min)

**Goal:** Create high-quality PR with comprehensive description

**Steps:**

1. **Review changes**
```bash
git status
git diff
```

2. **Commit changes**
```bash
git add .
git commit -m "{type}: {description}

{detailed explanation}

Closes #{issue-number}

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

3. **Push branch**
```bash
git push -u origin {branch-name}
```

4. **Create PR with comprehensive description**
```bash
gh pr create --title "{type}: {title}" --body "$(cat <<'EOF'
## Summary
{Brief overview}

## Changes
{List of changes}

## Testing
{Testing performed}

## Screenshots (if UI)
{Screenshots}

## Checklist
- [x] Tests added/updated
- [x] Documentation updated
- [x] No breaking changes
- [x] Backwards compatible

Closes #{issue-number}

🤖 Generated with Claude Code
EOF
)"
```

**Output:**
- PR created
- PR URL
- Issue linked to PR

---

### Phase 6: Review Response (Variable)

**Goal:** Monitor PR and respond to review comments

**Steps:**

1. **Monitor for reviews**
```bash
# Check PR status
gh pr view {pr-number} --json reviews,comments,state,mergeable
```

2. **When reviews received, use pr-review-response prompt**
```markdown
"Use pr-review-response prompt to analyze PR #{pr-number} in {repo}.

Please:
1. Fetch all review comments (including Gemini AI)
2. Analyze each comment (type, priority, validity)
3. Create action plan with TodoWrite
4. Recommend fixes and draft responses"
```

3. **Address feedback**
```markdown
TodoWrite from prompt:
- [x] Fix: SQL injection vulnerability (Critical)
- [x] Add: Error handling (Important)
- [ ] Respond to comment 1
- [ ] Respond to comment 2
- [ ] Push fixes
```

4. **Push fixes**
```bash
git add .
git commit -m "fix: Address review feedback

- Fixed SQL injection using parameterized queries
- Added comprehensive error handling
- Improved type safety with interfaces

Addresses review comments from @reviewer and Gemini-AI"

git push
```

5. **Respond to comments**
```markdown
# For each comment, post response
gh pr comment {pr-number} --body "Comment response..."
```

6. **Re-request review**
```bash
gh pr review {pr-number} --request-review
```

7. **Repeat until approved**

**Output:**
- All review feedback addressed
- PR approved
- Ready to merge

---

### Phase 7: Merge & Close (5 min)

**Goal:** Merge PR and close issue

**Steps:**

1. **Verify CI/CD passing**
```bash
gh pr checks {pr-number}
```

2. **Merge PR**
```bash
gh pr merge {pr-number} --squash --delete-branch
```

3. **Verify issue closed automatically**
```bash
gh issue view {issue-number}
# Should show: State: CLOSED
```

4. **Celebrate! 🎉**

**Output:**
- PR merged
- Issue closed
- Feature in main branch

---

## Complete Workflow Template

```markdown
# Conductor Full-Cycle Execution

## Phase 1: Issue Selection
"Use issue-selection prompt to select best issue from {repo}.

Context:
- Sprint focus: {focus}
- Available time: {hours}
- Recent work: {context}"

## Phase 2: Planning
"Analyze selected issue #{number} and use parallel-agents prompt to create execution plan."

## Phase 3: Parallel Implementation
Task(agent1, "subtask 1 description")
Task(agent2, "subtask 2 description")
Task(agent3, "subtask 3 description")

## Phase 4: Testing
- Run test suite
- Browser testing if needed
- Manual validation

## Phase 5: PR Creation
- Commit and push
- Create PR with description
- Link to issue

## Phase 6: Review Response
"Use pr-review-response prompt to analyze PR #{number} and address feedback."

## Phase 7: Merge
- Verify checks
- Merge PR
- Verify issue closed
```

## Time Estimates

**By Phase:**
- Issue Selection: 5-10 min
- Planning: 10-15 min
- Implementation: 30-90 min (depends on complexity)
- Testing: 15-30 min
- PR Creation: 10-15 min
- Review Response: Variable (10 min - hours)
- Merge: 5 min

**Total (without review):** 70-165 min (~1-3 hours)
**With review cycles:** +30 min - days (depends on reviewers)

**Parallel Speedup:**
If 3 subtasks @30min each:
- Sequential: 90 min
- Parallel: 30 min
- Savings: 60 min (67% faster)

## Error Handling

### Issue Selection Fails
- No suitable issues → Ask user for priorities
- All issues blocked → Work on unblocking issues
- Unclear requirements → Request clarification

### Implementation Fails
- Tests failing → Debug and fix before PR
- Agent errors → Retry or implement manually
- Merge conflicts → Resolve before pushing

### Review Process Stalls
- No review after 24h → Ping reviewers
- Blocked by comments → Address promptly
- Disagreement → Discuss and resolve

## Conductor Agent Integration

The conductor agent should:

1. **Use TodoWrite throughout** - Track all phases
2. **Apply prompts automatically** - Reference workflow prompts
3. **Handle failures gracefully** - Retry or escalate
4. **Provide status updates** - Keep user informed
5. **Adapt to context** - Adjust based on project needs

## Success Metrics

Track these to improve workflow:

- **Time to merge**: Issue selection → merge
- **Parallel efficiency**: Time saved by parallelization
- **Review cycles**: Number of fix/review iterations
- **Quality**: Issues found post-merge
- **Velocity**: Issues completed per week

## Continuous Improvement

**After each cycle:**
1. What went well?
2. What could be improved?
3. Were estimates accurate?
4. Did parallel execution work?
5. How was review feedback?

**Update prompts based on learnings**

## Example Execution

```markdown
# User request:
"Use conductor to pick and implement the best GitHub issue"

# Conductor executes:

Phase 1: Issue Selection ✅
- Fetched 20 open issues
- Applied scoring framework
- Selected: Issue #42 "Add user preferences" (Score: 85/100)

Phase 2: Planning ✅
- Decomposed into 3 subtasks
- Identified parallel execution opportunity
- Created execution plan

Phase 3: Parallel Implementation 🔄
- Task 1: Database schema (agent: database) - ✅ Complete (12 min)
- Task 2: Backend API (agent: implementation) - 🔄 In progress
- Task 3: Frontend UI (agent: implementation) - 🔄 In progress

Phase 4: Testing ⏸️
- Waiting for implementation to complete

Phase 5: PR Creation ⏸️
- Waiting for tests to pass

Phase 6: Review Response ⏸️
- PR not created yet

Phase 7: Merge ⏸️
- Not ready to merge

Current Status: Implementing in parallel (estimated 18 min remaining)
```

## Notes

- This workflow is fully automatable with conductor agent
- Use TodoWrite to track each phase
- Apply workflow prompts at each step
- Parallel execution dramatically speeds up work
- Review response is often the longest phase (external dependency)
- Continuous improvement makes workflow more efficient over time
