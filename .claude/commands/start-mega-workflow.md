# Start Mega-Workflow

Launch autonomous multi-issue workflow orchestration with intelligent batching and parallel conductor execution.

---

## Quick Start

This command discovers GitHub issues, plans optimal execution batches, and launches conductor agents in parallel to handle complete development workflows at scale.

---

## Usage

```bash
/start-mega-workflow [mode] [options]
```

---

## Modes

### Auto-Batch Mode (Default)
Discover all eligible issues, prioritize, batch, and execute:
```bash
/start-mega-workflow auto-batch labels=p0,p1 max=20
```

**Parameters:**
- `labels=p0,p1` - Filter by labels (comma-separated)
- `max=20` - Maximum issues to process
- `milestone=v2.0` - Filter by milestone (optional)
- `exclude-assigned=true` - Exclude assigned issues (default: true)

### Single-Batch Mode
Execute specific issues in one parallel batch:
```bash
/start-mega-workflow single-batch issues=42,51,67,89,103
```

**Parameters:**
- `issues=42,51,67` - Comma-separated issue numbers (required)
- `max-conductors=5` - Max parallel conductors (default: 5)

### Resume Mode
Resume interrupted mega-workflow from saved state:
```bash
/start-mega-workflow resume
```

**Behavior:**
- Loads state from `.claude/state/mega-workflow.json`
- Displays progress summary
- Resumes from incomplete batch
- Skips completed issues
- Retries failed issues

---

## What It Does

### Phase 1: Issue Discovery & Prioritization
- Fetches all open GitHub issues
- Applies filters (labels, milestones, assignees)
- Calculates priority scores (impact, effort, dependencies, clarity)
- Identifies top candidates for execution

### Phase 2: Batch Planning & Conflict Detection
- Groups issues into batches (3-5 issues per batch)
- Analyzes file conflicts within batches
- Detects cross-issue dependencies
- Creates execution plan with optimal parallelization

### Phase 3: Execute Batches (Parallel Conductors)
- Launches 3-5 conductor agents per batch
- Each conductor runs full-cycle workflow:
  - Issue pickup → Architecture → Implementation → Testing → PR
- Monitors progress across all conductors
- Handles failures gracefully (don't block entire batch)
- Saves state after each batch for resumption

### Phase 4: Integration Validation
- Checks for merge conflicts across all feature branches
- Identifies cross-PR file modifications
- Recommends merge order to minimize conflicts
- Validates integration feasibility

### Phase 5: Comprehensive Reporting
- Aggregates metrics (time saved, success rate, quality scores)
- Documents successes and failures
- Provides merge recommendations
- Generates actionable next steps

---

## State Management

### State File Location
`.claude/state/mega-workflow.json`

### Resumption Support
If workflow is interrupted:
- State is automatically saved after each batch
- Resume with `/start-mega-workflow resume`
- Conductor status is detected automatically:
  - Has PR → Completed ✅
  - Has branch but no PR → In progress (will resume)
  - No branch → Not started (will retry)

### State Archive
On successful completion:
- State moved to `.claude/state/archive/mega-workflow-[TIMESTAMP].json`
- Audit trail preserved

---

## Examples

### Example 1: Process All P0 and P1 Issues
```bash
/start-mega-workflow auto-batch labels=p0,p1 max=20
```

**What happens:**
1. Discovers all p0 and p1 labeled issues (up to 20)
2. Prioritizes by impact, effort, dependencies
3. Creates 4 batches of 5 issues each
4. Executes Batch 1 (5 parallel conductors)
5. Executes Batch 2 (5 parallel conductors)
6. Executes Batch 3 (5 parallel conductors)
7. Executes Batch 4 (5 parallel conductors)
8. Validates integration across all PRs
9. Generates comprehensive report

**Typical duration:** 2-3 hours (depending on issue complexity)
**Time saved:** 60-70% faster than sequential execution

### Example 2: Execute Sprint Backlog
```bash
/start-mega-workflow auto-batch milestone=Sprint-42 max=15
```

**What happens:**
1. Discovers all issues in Sprint-42 milestone (up to 15)
2. Batches and executes in parallel
3. Reports progress throughout

### Example 3: Quick Batch of Related Issues
```bash
/start-mega-workflow single-batch issues=42,51,67
```

**What happens:**
1. Validates issues 42, 51, 67 exist
2. Checks for conflicts between them
3. Launches 3 parallel conductors
4. Monitors and reports results

**Typical duration:** 30-45 minutes for 3 issues

### Example 4: Resume After Interruption
```bash
/start-mega-workflow resume
```

**What happens:**
1. Loads previous session state
2. Shows progress: "Batch 2 of 4 incomplete (3/5 issues done)"
3. Resumes conductors for 2 pending issues
4. Continues with Batches 3 and 4
5. Completes workflow

---

## Quality Gates

All conductors must pass these gates before PR creation:

✅ **Architecture Validation**
- VSA compliance
- SOLID principles
- Layer boundaries respected

✅ **Testing**
- Unit tests passing
- Integration tests passing
- UI tests (if applicable)
- Coverage >= 70%

✅ **Quality Audit**
- Audit score >= 8.0/10
- No critical findings
- Build passes
- No TypeScript errors

✅ **Code Review Ready**
- Single atomic commit
- PR body comprehensive
- Issue linked (`Fixes #ISSUE`)
- CI passing

---

## Parallel Execution Limits

### Resource Constraints
- **Max parallel conductors per batch:** 5
- **Max batches:** Unlimited (sequential)
- **Min issue time:** 15 minutes (smaller tasks not worth parallelization overhead)

### Safety Mechanisms
- **Conflict detection:** Issues modifying same files are separated or warned
- **Failure isolation:** One conductor failure doesn't block entire batch
- **Progress monitoring:** Real-time updates for all conductors
- **State persistence:** Resume capability if interrupted

---

## Success Metrics

A successful mega-workflow execution achieves:

- ✅ **High success rate:** 80%+ issues completed
- ✅ **Significant time savings:** 60-70% faster than sequential
- ✅ **Quality maintained:** All quality gates passed
- ✅ **No integration conflicts:** PRs merge cleanly
- ✅ **Comprehensive tracking:** State saved and metrics collected

---

## Common Scenarios

### Scenario 1: Weekly Sprint Planning
**Goal:** Execute all sprint issues in parallel batches

```bash
/start-mega-workflow auto-batch milestone=Sprint-42 labels=p0,p1,p2
```

**Expected outcome:**
- All sprint issues processed in 2-3 hours
- PRs ready for review at start of week
- Integration conflicts identified early

### Scenario 2: Bug Bash
**Goal:** Fix multiple critical bugs quickly

```bash
/start-mega-workflow auto-batch labels=bug,critical max=10
```

**Expected outcome:**
- 10 critical bugs fixed in parallel
- PRs created within 1-2 hours
- CI validation complete

### Scenario 3: Technical Debt Cleanup
**Goal:** Tackle multiple refactoring tasks

```bash
/start-mega-workflow auto-batch labels=tech-debt,refactor max=15
```

**Expected outcome:**
- 15 refactoring tasks completed
- Code quality improved across codebase
- Test coverage increased

---

## Failure Handling

### Conductor Failures
If a conductor fails during execution:
- ✅ Error logged with details
- ✅ Issue marked as failed in state
- ✅ Other conductors continue (not blocked)
- ✅ Failed issues added to retry queue
- ✅ Retry in next batch OR separate session

### Too Many Failures (>50% of batch)
If more than half the batch fails:
- ⚠️ Batch execution paused
- 🔍 Common failure patterns analyzed
- 📊 Report to user for investigation
- ❓ Offer to continue or abort

### Critical Failures
If build breaks or system-wide issue:
- 🛑 All conductors stopped immediately
- 🔄 Rollback if needed
- 🔧 Fix critical issue first
- ▶️ Resume with `--resume` after fix

---

## Integration with Other Agents

### Conductor Agent
Mega-workflow launches conductor agents for each issue:
```
/start-mega-workflow → Mega-Workflow Agent
                              ↓
                    Launches 5 conductors in parallel:
                    - Conductor 1 (Issue #42)
                    - Conductor 2 (Issue #51)
                    - Conductor 3 (Issue #67)
                    - Conductor 4 (Issue #89)
                    - Conductor 5 (Issue #103)
                              ↓
                    Each runs full-cycle workflow
```

### Orchestrator Agent
For very large operations, orchestrator may delegate to mega-workflow:
```
User: "Process entire backlog (100+ issues)"
           ↓
   Orchestrator Agent (analyzes scale)
           ↓
   Delegates to Mega-Workflow (batch execution)
           ↓
   Mega-Workflow coordinates conductors
```

---

## Tips & Best Practices

### 1. Start Small
First time using mega-workflow? Start with a small batch:
```bash
/start-mega-workflow single-batch issues=42,51,67
```

### 2. Use Labels Effectively
Ensure your issues have clear labels (p0, p1, p2, bug, feature):
```bash
/start-mega-workflow auto-batch labels=p0,p1
```

### 3. Monitor State Files
Check state during execution:
```bash
cat .claude/state/mega-workflow.json | jq
```

### 4. Resume on Interruption
If interrupted, always resume instead of restarting:
```bash
/start-mega-workflow resume
```

### 5. Review Reports
After completion, review the comprehensive report:
```bash
cat .claude/reports/mega-workflow-*.md
```

---

## Troubleshooting

### "No eligible issues found"
**Cause:** Filters too restrictive or no matching issues
**Fix:** Broaden filters or check issue labels

### "Conflict detected in batch"
**Cause:** Multiple issues modifying same files
**Fix:** Mega-workflow will warn you - approve to continue or adjust batch

### "Conductor failed repeatedly"
**Cause:** Issue has blocking problems (missing dependencies, unclear requirements)
**Fix:** Review failure log, fix issue manually, retry

### "State file corrupted"
**Cause:** Workflow interrupted during state save
**Fix:** Restore from `.claude/state/archive/` or start fresh

---

## Performance Expectations

### Typical Issue Times (with parallelization)
- **Simple bug fix:** 15-20 minutes
- **Medium feature:** 25-35 minutes
- **Complex feature:** 40-60 minutes

### Batch Times (5 issues per batch)
- **Simple batch:** 20-25 minutes (parallel execution)
- **Medium batch:** 35-40 minutes
- **Complex batch:** 60-70 minutes

### Full Workflow (20 issues, 4 batches)
- **Sequential estimate:** 6-8 hours
- **Parallel actual:** 2-3 hours
- **Time saved:** 60-70% (4-5 hours)

---

## What Gets Created

After successful execution:

### Per Issue
- ✅ Feature branch (`feature/issue-{N}-{title}`)
- ✅ Atomic commit with proper message
- ✅ Pull request with comprehensive body
- ✅ Issue link in PR (`Fixes #ISSUE`)

### Per Batch
- ✅ Batch state in `.claude/state/mega-workflow.json`
- ✅ Progress metrics
- ✅ Conductor status tracking

### Final Output
- ✅ Comprehensive report (`.claude/reports/mega-workflow-*.md`)
- ✅ Metrics JSON (`.claude/reports/mega-workflow-metrics.json`)
- ✅ Archived state (`.claude/state/archive/`)
- ✅ Actionable next steps

---

## Advanced Usage

### Custom Batch Size
Override default batch size:
```bash
/start-mega-workflow auto-batch labels=p0 max=20 batch-size=3
```

### Exclude Specific Issues
Process all except certain issues:
```bash
/start-mega-workflow auto-batch labels=p1 exclude=42,51,67
```

### Dry Run (Planning Only)
See execution plan without running:
```bash
/start-mega-workflow auto-batch labels=p0 dry-run=true
```

---

## When NOT to Use Mega-Workflow

❌ **Single issue** - Use `/start-workflow` or conductor directly
❌ **Issues with tight dependencies** - Execute sequentially
❌ **Database migrations** - Must be sequential
❌ **Breaking changes** - Need coordinated rollout
❌ **< 3 issues** - Overhead not worth it

---

## Related Commands

- `/start-workflow` - Single issue full-cycle workflow
- `/issue-pickup` - Smart issue selection and implementation
- `/conductor` - Direct conductor agent invocation
- `/parallel-worktree` - Parallel development with git worktrees

---

## Delegation Pattern

When you use this command, Claude will:

1. **Invoke mega-workflow agent** with your parameters
2. **Mega-workflow agent** discovers, plans, and executes batches
3. **Conductor agents** handle individual issue workflows
4. **Specialized agents** perform analysis and implementation
5. **You receive** comprehensive report and next steps

---

**Ready to process multiple issues in parallel? Use `/start-mega-workflow` to supercharge your development velocity!** 🚀
