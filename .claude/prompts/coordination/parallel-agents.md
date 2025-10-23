# Parallel Agent Coordination Prompt

**Purpose**: Coordinate multiple agents running in parallel to maximize efficiency and avoid conflicts.

## Overview

When tasks can be decomposed into independent subtasks, running agents in parallel dramatically reduces total execution time. This prompt helps identify parallelizable work and coordinate agents effectively.

## Parallel Execution Rules

### When to Use Parallel Agents

✅ **Good candidates for parallel execution:**
- Independent code reviews (different files/modules)
- Multiple test suites (unit, integration, e2e)
- Multi-repo operations (deployments, updates)
- Data processing (different data sets)
- Documentation generation (different sections)
- Multiple bug investigations (unrelated issues)
- Feature implementations in different modules

❌ **Bad candidates (must be sequential):**
- Dependent operations (A must complete before B)
- Shared resource modifications (database schema changes)
- Operations requiring previous results as input
- Mutex-protected resources

### Dependency Analysis

**Before parallelizing, check:**

```markdown
For each subtask:
1. **Reads from**: [files/resources/data]
2. **Writes to**: [files/resources/data]
3. **Depends on**: [other subtasks]
4. **Blocks**: [other subtasks]

Conflict detection:
- Do any tasks write to the same file? → CONFLICT
- Do any tasks depend on each other's output? → SEQUENTIAL
- Are resources independent? → PARALLEL OK
```

## Parallel Agent Patterns

### Pattern 1: Fork-Join (Map-Reduce)

**Use case**: Process multiple independent items, aggregate results

```markdown
# Example: Review multiple PRs

Parallel phase (Fork):
- Agent 1: Review PR #42
- Agent 2: Review PR #43
- Agent 3: Review PR #44

Sequential phase (Join):
- Aggregate all reviews
- Generate summary report
- Post consolidated feedback
```

### Pattern 2: Pipeline (Producer-Consumer)

**Use case**: Chain of processing stages with parallel workers per stage

```markdown
# Example: Multi-stage test pipeline

Stage 1 (Parallel):
- Agent 1: Lint code
- Agent 2: Type check
- Agent 3: Security scan

Stage 2 (Parallel, after Stage 1):
- Agent 1: Unit tests
- Agent 2: Integration tests
- Agent 3: E2E tests

Stage 3 (Sequential, after Stage 2):
- Agent 1: Generate coverage report
```

### Pattern 3: Broadcast (All-at-Once)

**Use case**: Same operation across multiple targets

```markdown
# Example: Update all repositories

Parallel execution:
- Agent 1: Update repo-1 dependencies
- Agent 2: Update repo-2 dependencies
- Agent 3: Update repo-3 dependencies
- Agent 4: Update repo-4 dependencies

Each agent:
1. Run npm audit
2. Apply safe updates
3. Run tests
4. Create PR if tests pass
```

### Pattern 4: Race Condition (First-Win)

**Use case**: Multiple approaches, use first successful result

```markdown
# Example: Bug investigation

Parallel execution:
- Agent 1: Search error logs for patterns
- Agent 2: Review recent code changes
- Agent 3: Check similar known issues

First agent with findings:
- Share results
- Other agents terminate
```

## Coordination Template

```markdown
# Parallel Agent Coordination Plan

## Objective
[High-level goal]

## Task Decomposition

### Subtask 1: [NAME]
- **Agent**: [agent-name]
- **Reads**: [resources]
- **Writes**: [resources]
- **Estimated time**: [duration]
- **Dependencies**: [none/list]
- **Can run in parallel with**: [subtask IDs]

### Subtask 2: [NAME]
- **Agent**: [agent-name]
- **Reads**: [resources]
- **Writes**: [resources]
- **Estimated time**: [duration]
- **Dependencies**: [none/list]
- **Can run in parallel with**: [subtask IDs]

[... more subtasks ...]

## Execution Plan

### Phase 1: Parallel Execution
- Start agents: [list]
- Wait for: [all/any/specific agents]

### Phase 2: Sequential (if needed)
- Agent: [agent-name]
- Input: [results from Phase 1]

### Phase 3: Aggregation
- Collect results from all agents
- Generate unified output

## Conflict Resolution

- **File conflicts**: [strategy]
- **Resource contention**: [strategy]
- **Failure handling**: [continue/abort/retry]

## Success Criteria
- [ ] All parallel agents complete successfully
- [ ] Results aggregated correctly
- [ ] No resource conflicts
- [ ] Total time < sequential execution
```

## Example: Feature Implementation Across Modules

```markdown
# Parallel Agent Coordination Plan

## Objective
Implement "user preferences" feature across frontend, backend, and database

## Task Decomposition

### Subtask 1: Database Schema
- **Agent**: database
- **Reads**: existing schema
- **Writes**: migrations/001_add_user_preferences.sql
- **Estimated time**: 15 min
- **Dependencies**: none
- **Can run in parallel with**: Subtask 2, 3

### Subtask 2: Backend API
- **Agent**: implementation
- **Reads**: existing API code
- **Writes**: src/api/preferences.ts, tests/api/preferences.test.ts
- **Estimated time**: 30 min
- **Dependencies**: none (can mock DB)
- **Can run in parallel with**: Subtask 1, 3

### Subtask 3: Frontend UI
- **Agent**: implementation
- **Reads**: existing UI components
- **Writes**: src/components/PreferencesPanel.tsx, src/components/PreferencesPanel.test.tsx
- **Estimated time**: 45 min
- **Dependencies**: none (can mock API)
- **Can run in parallel with**: Subtask 1, 2

## Execution Plan

### Phase 1: Parallel Implementation (0-45 min)
Launch in single message with multiple Task tool calls:
- Task(database, "Create user_preferences table with columns: user_id, theme, notifications, language...")
- Task(implementation, "Create preferences API endpoints: GET/PUT /api/user/preferences...")
- Task(implementation, "Create PreferencesPanel component with theme selector, notification toggles...")

Wait for all to complete.

### Phase 2: Integration (45-60 min)
Sequential (needs results from Phase 1):
- Review all implementations
- Wire up frontend → API → database
- Add integration tests
- Verify end-to-end flow

### Phase 3: Testing (60-75 min)
Parallel execution:
- Task(browser-testing, "Test preferences UI with visual validation")
- Task(implementation, "Run API integration tests")
- Task(database, "Verify migration and rollback")

## Conflict Resolution

- **File conflicts**: None expected (different directories)
- **Resource contention**: None (isolated modules)
- **Failure handling**:
  - If database fails: Abort (others need schema)
  - If API fails: Continue (can mock for frontend)
  - If frontend fails: Continue (API still valuable)

## Success Criteria
- [x] All three agents complete successfully
- [x] Integration tests pass
- [x] No file conflicts during merge
- [x] Total time ~75 min (vs ~90 min sequential)

## Actual Execution

Invoke parallel agents:
```

**In conductor agent:**
```markdown
"I need to implement user preferences feature across frontend, backend, and database in parallel.

Task 1: Create database schema for user_preferences
Task 2: Implement backend API for preferences
Task 3: Implement frontend PreferencesPanel UI

These tasks are independent and can run in parallel. Please coordinate their execution."
```

**Or use Task tool directly:**
```
# Single message with multiple Task calls
Task(database, "Create user_preferences table...")
Task(implementation, "Create preferences API endpoints...")
Task(implementation, "Create PreferencesPanel component...")
```

## Anti-Patterns

### ❌ Don't: Sequential Execution of Independent Tasks

```markdown
# BAD - sequential (90 min total)
1. Complete database schema (15 min)
2. Wait...
3. Complete backend API (30 min)
4. Wait...
5. Complete frontend UI (45 min)
```

### ✅ Do: Parallel Execution

```markdown
# GOOD - parallel (45 min total)
1. Start all three agents simultaneously
2. Wait for all to complete (45 min = max of 15, 30, 45)
3. Integrate results
```

### ❌ Don't: Parallelize Dependent Operations

```markdown
# BAD - will fail
Agent 1: Run database migration
Agent 2: Seed data (needs migration first)
# Agent 2 will fail - migration not complete yet!
```

### ✅ Do: Respect Dependencies

```markdown
# GOOD - sequential
1. Agent 1: Run database migration
2. Wait for completion
3. Agent 2: Seed data
```

## Monitoring Parallel Agents

While agents run in background:

```markdown
# Check status
- Agent 1: database (status: in_progress)
- Agent 2: implementation/backend (status: in_progress)
- Agent 3: implementation/frontend (status: in_progress)

# Use TodoWrite to track:
"Creating database schema" - in_progress
"Implementing backend API" - in_progress
"Implementing frontend UI" - in_progress

# When complete, mark done:
"Creating database schema" - completed
"Implementing backend API" - completed
"Implementing frontend UI" - completed
```

## Time Savings Calculation

```markdown
Sequential time = Sum of all task times
Parallel time = Max of all task times (in same phase)

Example:
- Task A: 15 min
- Task B: 30 min
- Task C: 45 min

Sequential: 15 + 30 + 45 = 90 min
Parallel: max(15, 30, 45) = 45 min
Savings: 50% (45 min saved)
```

## Best Practices

1. **Start with dependency analysis** - Don't assume tasks are independent
2. **Use TodoWrite** - Track all parallel tasks for visibility
3. **Single message invocation** - Launch all parallel agents in one message
4. **Plan aggregation** - Know how you'll combine results
5. **Handle failures gracefully** - One agent failing shouldn't break others
6. **Monitor resource usage** - Too many parallel agents can overwhelm system
7. **Document coordination** - Make parallelization explicit in code/PRs

## Limits

**Practical limits:**
- Max ~5 agents in parallel (system resource consideration)
- Each agent should take >2 min (overhead of parallelization)
- Tasks should be truly independent (no hidden dependencies)

## Integration with Conductor

```markdown
# Conductor agent should:
1. Analyze issue/task
2. Break into subtasks
3. Check dependencies
4. Identify parallelizable work
5. Use this prompt to coordinate
6. Launch agents in parallel
7. Aggregate results
8. Proceed to next phase
```

## Templates for Common Scenarios

### Multi-Repo Operation

```markdown
Parallel agents for repos: [repo1, repo2, repo3, ...]
Operation: [update-deps/deploy/test/security-scan]

Launch with:
Task(agent, "operate on repo1")
Task(agent, "operate on repo2")
Task(agent, "operate on repo3")
```

### Code Review Split

```markdown
Parallel review by file type:
Task(code-reviewer, "review backend changes")
Task(code-reviewer, "review frontend changes")
Task(code-reviewer, "review database changes")
```

### Test Suite Parallel Execution

```markdown
Parallel test suites:
Task(implementation, "run unit tests")
Task(implementation, "run integration tests")
Task(browser-testing, "run e2e tests")
```

## Notes

- This prompt is reusable across all repos and workflows
- Always prefer parallel when possible (faster feedback)
- Use TodoWrite to visualize parallel work
- Monitor for hidden dependencies
- Aggregate results thoughtfully
