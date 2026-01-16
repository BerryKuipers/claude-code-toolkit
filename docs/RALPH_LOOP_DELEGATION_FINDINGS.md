# RALPH Loop Delegation Architecture - Findings Report

**Date**: 2026-01-16
**Status**: Analysis Complete
**Recommendation**: Option B (Conductor as Dispatch-Only)

---

## Executive Summary

The RALPH loop and conductor currently have a blurred responsibility boundary where the conductor, intended as a workflow coordinator, also executes implementation work directly. This analysis identifies the root causes and proposes a minimal fix to enforce proper delegation.

---

## 1. Current Flow Diagram

```
User → /ralph-loop
       ↓
       GitHub Issue Selection
       ↓
       PRD JSON Generation
       ↓
       Ralph TUI (external) → Claude Code Agent
                              ↓
                              detect_executor() → Maps to agent/command
                              ↓
                              ┌────────────────────────────────────────────┐
                              │ Keyword Routing (ralph-loop.md:292-315)   │
                              │ • "architect|design|structure" → /architect│
                              │ • "test|validate" → /test-all             │
                              │ • "audit|review" → /audit                  │
                              │ • "refactor|cleanup" → /refactor           │
                              │ • DEFAULT → /conductor  ←── PROBLEM HERE   │
                              └────────────────────────────────────────────┘
```

**The Problem**: `/conductor` is the default executor for most tasks, and the conductor does BOTH delegation AND direct implementation work.

---

## 2. Where Conductor Executes Work Directly

### 2.1 Direct Bash Commands (Should Be Delegated)

**File**: `.claude/agents/conductor.md`

| Line Range | Action | Should Delegate To |
|------------|--------|-------------------|
| 1040-1080 | Database migrations (`npm run migrate`) | database agent |
| 1085-1115 | Prisma client regeneration (`npx prisma generate`) | database agent |
| 1355-1360 | Run tests (`npm run test`) | implementation agent or /test-all |
| 1740-1750 | Validate build (`npm run build`) | implementation agent |
| 1896-1908 | Create PR (`gh pr create`) | OK - orchestration boundary |
| 1950-2030 | Gemini review monitoring | OK - orchestration boundary |

### 2.2 State File Management (OK - Orchestration Responsibility)

The conductor manages `.claude/state/conductor.json` - this is appropriate for a coordinator.

### 2.3 Tool Access That Enables Direct Work

**Conductor tools**: `Task, TodoWrite, SlashCommand, Bash, Read`

The `Bash` and `Read` tools allow the conductor to:
- Run npm commands directly
- Read code files (should delegate to specialist agents)

---

## 3. Why This Happens

### 3.1 RALPH Loop Default Executor

From `ralph-loop.md` lines 292-315:

```bash
detect_executor() {
  # ... keyword checks ...
  else
    echo "/conductor"  # DEFAULT
  fi
}
```

Most tasks without specific keywords go to `/conductor`.

### 3.2 Conductor's Dual Role

The conductor is designed as a "complete workflow orchestrator" (conductor.md:10) that:

1. **Orchestrates** (correct): Dispatches to specialist agents via natural language
2. **Executes** (incorrect): Runs bash commands directly for migrations, tests, builds

### 3.3 Natural Language Delegation Pattern

The agent-delegation-pattern.md documents the correct pattern:
```markdown
I need the [agent-name] agent to [task-description].
[Context]
```

However, the conductor's implementation also includes direct bash blocks that bypass this pattern.

---

## 4. Root Cause Analysis

### Primary Cause: Tool Access Without Enforcement

The conductor has `Bash` tool access and uses it for:
- ✅ gh CLI operations (orchestration boundary) - OK
- ✅ State file management - OK
- ❌ npm run migrate/test/build - Should delegate
- ❌ npx prisma generate - Should delegate

### Secondary Cause: No Runtime Guard

There's no mechanism to prevent the conductor from executing implementation commands. The rules say "delegate" but nothing enforces it.

### Tertiary Cause: Missing Specialist Coverage

Some operations (migrations, builds) don't have a clear specialist agent:
- `database agent` - exists, handles schema changes
- `implementation agent` - exists, but doesn't explicitly cover builds/tests

---

## 5. Proposed Solution: Option B (Dispatch-Only Conductor)

### 5.1 Strategy

Keep the conductor but enforce "dispatch-only" behavior through:

1. **Explicit delegation rules** in conductor.md
2. **WorkPlan abstraction** for parallelizable steps
3. **Specialist coverage** for all implementation work
4. **Verification script** to detect conductor doing direct work

### 5.2 What Conductor CAN Do (Dispatch)

- ✅ Use Task tool to delegate to specialist agents
- ✅ Use SlashCommand to invoke commands
- ✅ Use Bash for gh CLI (PR creation, issue management)
- ✅ Use Bash for state file management (read/write JSON)
- ✅ Use TodoWrite for progress tracking
- ✅ Aggregate and report results from delegated tasks

### 5.3 What Conductor MUST NOT Do (Implementation)

- ❌ Run npm scripts (test, build, migrate, lint)
- ❌ Run npx commands (prisma generate)
- ❌ Read code files for analysis (delegate to architect)
- ❌ Write production code (delegate to implementation)
- ❌ Fix test failures (delegate to debugger/implementation)

---

## 6. Implementation Plan

### Phase 1: Add WorkPlan Abstraction

Create `.claude/shared/work-plan.md` defining:

```markdown
## WorkPlan Schema

{
  "id": "wp-001",
  "phases": [
    {
      "id": "phase-1",
      "name": "Analysis",
      "parallel": true,
      "steps": [
        { "agent": "architect", "task": "...", "canRunWith": ["audit"] },
        { "agent": "audit", "task": "...", "canRunWith": ["architect"] }
      ]
    },
    {
      "id": "phase-2",
      "name": "Implementation",
      "parallel": false,
      "dependsOn": ["phase-1"],
      "steps": [...]
    }
  ]
}
```

### Phase 2: Update Conductor Rules

Add explicit "NEVER" section to conductor.md:

```markdown
### ❌ EXECUTION BOUNDARY - NEVER Cross These Lines

The conductor MUST NOT execute these directly:

1. **Build/Test Commands**: ALWAYS delegate to implementation agent
   - ❌ `npm run test` → ✅ delegate to implementation or /test-all
   - ❌ `npm run build` → ✅ delegate to implementation agent
   - ❌ `npm run lint` → ✅ delegate to implementation agent

2. **Database Commands**: ALWAYS delegate to database agent
   - ❌ `npm run migrate` → ✅ delegate to database agent
   - ❌ `npx prisma generate` → ✅ delegate to database agent

3. **Code Analysis**: ALWAYS delegate to specialist agents
   - ❌ Reading .ts/.tsx files → ✅ delegate to architect/implementation
   - ❌ Analyzing patterns → ✅ delegate to architect agent
```

### Phase 3: Extend Implementation Agent

Add explicit support for:
- Running test suite and reporting results
- Running build and reporting results
- Running lint and reporting results

### Phase 4: Add Verification Script

Create `.claude/scripts/verify-delegation.sh`:

```bash
#!/bin/bash
# Detect conductor doing direct implementation work in session logs
```

---

## 7. Parallel Orchestration Structure

### Current State

No formal TaskGraph exists. Parallelization is described in prompts but not enforced.

### Proposed WorkPlan Structure

```typescript
interface WorkPlan {
  id: string
  description: string
  phases: Phase[]
}

interface Phase {
  id: string
  name: string
  parallel: boolean
  dependsOn?: string[]
  steps: Step[]
}

interface Step {
  id: string
  agent: string  // Agent to delegate to
  task: string   // Task description
  canRunWith?: string[]  // Other step IDs that can run in parallel
  blockedBy?: string[]   // Step IDs that must complete first
}
```

### Parallel Capability

At minimum: architect + auditor can run concurrently on the same issue spec.

```markdown
Phase 1 (Parallel):
- architect agent → architecture validation
- audit agent → code quality baseline

Phase 2 (Sequential after Phase 1):
- implementation agent → code changes

Phase 3 (Parallel after Phase 2):
- auditor → verify changes
- browser-testing → UI validation
```

---

## 8. Files to Modify

| File | Change | Priority |
|------|--------|----------|
| `.claude/agents/conductor.md` | Add NEVER rules, delegate all npm/npx | HIGH |
| `.claude/agents/implementation.md` | Add explicit test/build support | HIGH |
| `.claude/shared/work-plan.md` | Create WorkPlan abstraction | MEDIUM |
| `.claude/commands/ralph-loop.md` | Document delegation expectations | LOW |
| `.claude/scripts/verify-delegation.sh` | Create verification script | MEDIUM |

---

## 9. Verification Requirements

### Test 1: Conductor Never Runs npm/npx

**Input**: `test conductor delegation with build task`

**Expected**: Conductor delegates to implementation agent, does not run `npm run build` directly.

### Test 2: Parallel Analysis Works

**Input**: Issue requiring architecture + audit analysis

**Expected**: Both agents invoked in parallel (single message with multiple Task calls).

### Test 3: Loop Cycles Complete

**Input**: Multi-iteration RALPH loop

**Expected**: Loop continues until completion marker or max iterations.

---

## 10. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Conductor still does work | Add runtime detection in verify script |
| Implementation agent missing capability | Extend agent with explicit test/build support |
| Breaking existing workflows | Test with dry-run before full implementation |
| Parallel execution not supported by runtime | Keep parallel structure for future, execute sequentially |

---

## 11. Success Criteria

1. ✅ Conductor produces only: dispatch decisions, aggregation summaries, next-step routing
2. ✅ Conductor never edits files / writes code / runs npm test/build
3. ✅ Specialist agents do the real work (architect, implementation, auditor)
4. ✅ Run output clearly shows multi-agent routing
5. ✅ Loop capable of multiple iterations without stalling
6. ✅ No broken CI / scripts / skills

---

## Appendix A: Code Paths Where Conductor Does Direct Work

### A.1 Database Migrations (conductor.md ~1040-1080)

```bash
# CURRENT: Conductor runs directly
npm run migrate 2>&1 | tee /tmp/migration.log

# SHOULD BE: Delegate to database agent
"I need the database agent to run migrations for the new schema changes.

Verify migrations apply cleanly and generate rollback script."
```

### A.2 Test Execution (conductor.md ~1355)

```bash
# CURRENT: Conductor runs directly
npm run test

# SHOULD BE: Delegate
"I need to run comprehensive tests using the /test-all command."
```

### A.3 Build Validation (conductor.md ~1740)

```bash
# CURRENT: Conductor runs directly
npm run build

# SHOULD BE: Delegate
"I need the implementation agent to validate the production build succeeds."
```

---

## Appendix B: Correct Delegation Examples

### B.1 Architecture Analysis (Correct)

```markdown
"I need the architect agent to validate architecture for issue #137.

Requirements:
- Add dark mode toggle to settings
- Store preference in user profile

Focus: VSA compliance, SOLID principles"
```

### B.2 Implementation (Correct)

```markdown
"I need the implementation agent to implement issue #137: User dark mode preference.

Architecture plan:
- Add darkMode field to User entity
- Create settings API endpoint
- Implement frontend toggle"
```

### B.3 Quality Audit (Correct)

```markdown
"I need the audit agent to audit code quality for issue #137.

Files changed:
- apps/web/src/components/Settings.tsx
- services/api/src/features/user/UserEntity.ts"
```

---

**End of Findings Report**
