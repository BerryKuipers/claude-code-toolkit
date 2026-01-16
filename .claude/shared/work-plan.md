# WorkPlan - Parallel Orchestration Abstraction

**Purpose**: Define a structured representation of parallelizable work for conductor-style orchestration.

---

## Overview

A WorkPlan represents a set of tasks that can be executed with understood dependencies and parallelization opportunities. The conductor and other orchestrators use this abstraction to:

1. **Plan** - Break work into phases and steps
2. **Parallelize** - Identify independent tasks that can run concurrently
3. **Track** - Monitor progress through structured state
4. **Verify** - Ensure all steps complete before moving to dependent phases

---

## WorkPlan Schema

```typescript
interface WorkPlan {
  /** Unique identifier for this work plan */
  id: string

  /** Human-readable description */
  description: string

  /** GitHub issue number (if applicable) */
  issueNumber?: number

  /** Ordered list of phases */
  phases: Phase[]

  /** Current execution state */
  state: 'pending' | 'in_progress' | 'completed' | 'failed'

  /** Timestamp when plan was created */
  createdAt: string

  /** Timestamp of last update */
  updatedAt: string
}

interface Phase {
  /** Unique phase identifier (e.g., "phase-1", "analysis") */
  id: string

  /** Human-readable name */
  name: string

  /** Can steps in this phase run in parallel? */
  parallel: boolean

  /** Phase IDs that must complete before this phase starts */
  dependsOn?: string[]

  /** Steps to execute in this phase */
  steps: Step[]

  /** Phase execution state */
  state: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'
}

interface Step {
  /** Unique step identifier */
  id: string

  /** Agent to delegate to (e.g., "architect", "implementation", "audit") */
  agent: string

  /** Task description for the agent */
  task: string

  /** Other step IDs in same phase that can run concurrently */
  canRunWith?: string[]

  /** Step IDs that must complete before this step (within same phase) */
  blockedBy?: string[]

  /** Step execution state */
  state: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'

  /** Result summary from agent */
  result?: string

  /** Error message if failed */
  error?: string
}
```

---

## Standard Phase Templates

### Template: Full Feature Development

```json
{
  "id": "wp-feature-dev",
  "description": "Full feature development from issue to PR",
  "phases": [
    {
      "id": "phase-1-analysis",
      "name": "Analysis & Planning",
      "parallel": true,
      "steps": [
        {
          "id": "arch-review",
          "agent": "architect",
          "task": "Validate architecture for issue #${issueNumber}",
          "canRunWith": ["audit-baseline"]
        },
        {
          "id": "audit-baseline",
          "agent": "audit",
          "task": "Establish code quality baseline for affected areas",
          "canRunWith": ["arch-review"]
        }
      ]
    },
    {
      "id": "phase-2-implementation",
      "name": "Implementation",
      "parallel": false,
      "dependsOn": ["phase-1-analysis"],
      "steps": [
        {
          "id": "implement",
          "agent": "implementation",
          "task": "Implement feature following architecture plan"
        }
      ]
    },
    {
      "id": "phase-3-validation",
      "name": "Validation",
      "parallel": true,
      "dependsOn": ["phase-2-implementation"],
      "steps": [
        {
          "id": "run-tests",
          "agent": "implementation",
          "task": "Run test suite and report results",
          "canRunWith": ["run-audit", "run-build"]
        },
        {
          "id": "run-audit",
          "agent": "audit",
          "task": "Audit code quality for changes",
          "canRunWith": ["run-tests", "run-build"]
        },
        {
          "id": "run-build",
          "agent": "implementation",
          "task": "Validate production build",
          "canRunWith": ["run-tests", "run-audit"]
        }
      ]
    },
    {
      "id": "phase-4-delivery",
      "name": "Delivery",
      "parallel": false,
      "dependsOn": ["phase-3-validation"],
      "steps": [
        {
          "id": "create-pr",
          "agent": "conductor",
          "task": "Create PR with proper issue linking"
        }
      ]
    }
  ]
}
```

### Template: Quality Gate Only

```json
{
  "id": "wp-quality-gate",
  "description": "Quality validation only (no implementation)",
  "phases": [
    {
      "id": "phase-1-validation",
      "name": "Quality Validation",
      "parallel": true,
      "steps": [
        {
          "id": "arch-audit",
          "agent": "architect",
          "task": "Validate architecture compliance",
          "canRunWith": ["code-audit", "test-run"]
        },
        {
          "id": "code-audit",
          "agent": "audit",
          "task": "Comprehensive code quality audit",
          "canRunWith": ["arch-audit", "test-run"]
        },
        {
          "id": "test-run",
          "agent": "implementation",
          "task": "Run full test suite",
          "canRunWith": ["arch-audit", "code-audit"]
        }
      ]
    }
  ]
}
```

### Template: Bug Fix

```json
{
  "id": "wp-bug-fix",
  "description": "Bug investigation and fix",
  "phases": [
    {
      "id": "phase-1-investigation",
      "name": "Investigation",
      "parallel": false,
      "steps": [
        {
          "id": "investigate",
          "agent": "debugger",
          "task": "Investigate bug root cause"
        }
      ]
    },
    {
      "id": "phase-2-fix",
      "name": "Fix",
      "parallel": false,
      "dependsOn": ["phase-1-investigation"],
      "steps": [
        {
          "id": "implement-fix",
          "agent": "implementation",
          "task": "Implement fix based on investigation"
        }
      ]
    },
    {
      "id": "phase-3-verify",
      "name": "Verification",
      "parallel": true,
      "dependsOn": ["phase-2-fix"],
      "steps": [
        {
          "id": "regression-test",
          "agent": "implementation",
          "task": "Run regression tests",
          "canRunWith": ["audit-check"]
        },
        {
          "id": "audit-check",
          "agent": "audit",
          "task": "Verify fix doesn't introduce issues",
          "canRunWith": ["regression-test"]
        }
      ]
    }
  ]
}
```

---

## Execution Semantics

### Parallel Execution

When `phase.parallel = true`:

1. All steps with no `blockedBy` dependencies start simultaneously
2. Steps with `blockedBy` wait for those specific steps
3. Phase completes when ALL steps complete
4. Any step failure can optionally fail the phase (configurable)

**Implementation**: Use multiple Task tool calls in a single message:

```markdown
# Parallel execution example
I need to run these analyses in parallel:

Task 1: I need the architect agent to validate architecture for issue #137.
Task 2: I need the audit agent to establish quality baseline.

Both can proceed independently.
```

### Sequential Execution

When `phase.parallel = false`:

1. Steps execute in order
2. Each step waits for previous to complete
3. Step failure stops the phase

### Phase Dependencies

`dependsOn` array specifies which phases must complete:

```json
{
  "id": "phase-2",
  "dependsOn": ["phase-1-a", "phase-1-b"],
  "steps": [...]
}
```

Phase 2 waits for BOTH phase-1-a AND phase-1-b to complete.

---

## State Management

### State File Location

```
.claude/state/work-plan-{id}.json
```

### State Transitions

```
pending → in_progress → completed
                     ↘ failed
                     ↘ skipped
```

### Progress Tracking

The conductor updates the work plan state as steps complete:

```json
{
  "phases": [
    {
      "id": "phase-1",
      "state": "completed",
      "steps": [
        { "id": "step-1", "state": "completed", "result": "Architecture validated" },
        { "id": "step-2", "state": "completed", "result": "Baseline: 7.2/10" }
      ]
    },
    {
      "id": "phase-2",
      "state": "in_progress",
      "steps": [
        { "id": "step-3", "state": "in_progress" }
      ]
    }
  ]
}
```

---

## Integration with Conductor

### Creating a WorkPlan

The conductor creates a WorkPlan at the start of a workflow:

```markdown
## Phase 1: Create WorkPlan

Based on issue analysis, I'm creating a work plan:

1. **Analysis Phase** (parallel)
   - Architect: Validate architecture
   - Auditor: Establish baseline

2. **Implementation Phase** (sequential, depends on Analysis)
   - Implementation: Code the feature

3. **Validation Phase** (parallel, depends on Implementation)
   - Implementation: Run tests
   - Auditor: Quality audit
   - Implementation: Validate build

4. **Delivery Phase** (sequential, depends on Validation)
   - Create PR

Saving work plan to .claude/state/work-plan-wp-001.json
```

### Executing a WorkPlan

The conductor executes phases in order, respecting dependencies:

```markdown
## Executing Phase 1: Analysis (Parallel)

Launching parallel agents:

I need the architect agent to validate architecture for issue #137.
[Context...]

I need the audit agent to establish quality baseline for the affected areas.
[Context...]

---

[After both complete]

✅ Phase 1 Complete
- Architect: Architecture validated, VSA compliant
- Auditor: Baseline score 7.2/10

Proceeding to Phase 2...
```

### Using TodoWrite for Visibility

The conductor reflects WorkPlan state in TodoWrite:

```json
[
  { "content": "Phase 1: Architecture validation", "status": "completed", "activeForm": "Validating architecture" },
  { "content": "Phase 1: Quality baseline", "status": "completed", "activeForm": "Establishing baseline" },
  { "content": "Phase 2: Implementation", "status": "in_progress", "activeForm": "Implementing feature" },
  { "content": "Phase 3: Run tests", "status": "pending", "activeForm": "Running tests" },
  { "content": "Phase 3: Quality audit", "status": "pending", "activeForm": "Auditing changes" },
  { "content": "Phase 4: Create PR", "status": "pending", "activeForm": "Creating PR" }
]
```

---

## Benefits

1. **Explicit Parallelization**: Clear which steps can run concurrently
2. **Dependency Tracking**: Phases wait for dependencies automatically
3. **State Persistence**: Workflows can resume after interruption
4. **Visibility**: TodoWrite reflects structured progress
5. **Future-Proof**: Structure supports true parallel execution when runtime enables it

---

## Constraints

1. **Runtime Limitation**: Claude Code currently executes sequentially within a turn
2. **Parallel Simulation**: Multiple Task calls in one message approximate parallelism
3. **State Recovery**: Work plan state enables resumption but requires conductor to read it

---

## Example: Conductor Using WorkPlan

```markdown
## Workflow Start

Creating WorkPlan for issue #137: User dark mode preference

```json
{
  "id": "wp-137-dark-mode",
  "issueNumber": 137,
  "description": "Implement dark mode toggle feature",
  "phases": [...]
}
```

Saving to .claude/state/work-plan-wp-137-dark-mode.json

## Phase 1: Analysis (Parallel)

I need the architect agent to validate architecture for issue #137: User dark mode preference.

Requirements:
- Add dark mode toggle to settings
- Store preference in user profile

I need the audit agent to establish quality baseline for:
- apps/web/src/features/settings/
- services/api/src/features/user/

[Both agents respond]

Updating work plan state:
- phase-1-analysis.state = "completed"
- arch-review.result = "VSA compliant, no violations"
- audit-baseline.result = "Baseline: 7.5/10"

## Phase 2: Implementation

Dependencies satisfied: [phase-1-analysis ✓]

I need the implementation agent to implement issue #137 following the architecture plan.

[Agent responds]

Updating work plan state:
- phase-2-implementation.state = "completed"
- implement.result = "8 files created/modified"

[Continue to Phase 3, 4...]
```

---

**Last Updated**: 2026-01-16
