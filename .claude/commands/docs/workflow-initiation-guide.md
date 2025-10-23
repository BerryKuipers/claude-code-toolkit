# Workflow Initiation Guide

How to start GitHub issue → full agent workflow → PR creation in TribeVibe.

## 🎯 The Challenge

You want to:
1. Pick up a GitHub issue
2. Have conductor orchestrate ALL agents (architect, design, implementation, audit, refactor)
3. Follow complete 6-phase workflow
4. End with merged PR

## ✅ Solution: Three Workflow Options

### **Option 1: Direct Conductor (RECOMMENDED)**

**Use when:** You want full automation from issue selection to PR.

```bash
# Auto-select optimal issue and run full workflow
/start-workflow

# Work on specific issue
/start-workflow issue=137

# Resume existing conductor workflow
/start-workflow resume
```

**What happens:**
1. Conductor agent takes full control
2. Shows comprehensive todo list (all 6 phases)
3. Delegates to ALL agents autonomously:
   - architect agent → validates architecture
   - design agent → analyzes UI/UX (if applicable)
   - implementation agent → writes code
   - audit agent → quality checks
   - refactor agent → improves code quality if needed
   - debugger agent → investigates failures
4. Creates PR with proper issue linking
5. Requests Gemini review
6. Applies suggestions
7. Reports final status

**Pros:**
- ✅ Fully automated - no manual intervention
- ✅ All agents properly delegated
- ✅ Todo list shows progress
- ✅ Complete workflow visibility

**Cons:**
- ⚠️ Less granular control over each step
- ⚠️ Conductor makes all decisions

---

### **Option 2: Issue-Pickup + Manual Conductor**

**Use when:** You want to select the issue first, then delegate to conductor.

```bash
# Step 1: Pick up issue (creates branch, analyzes requirements)
/issue-pickup issue=137

# Step 2: Delegate to conductor for full workflow
I need the conductor agent to implement issue #137 following the complete 6-phase workflow.

Context:
- Issue: #137 - User dark mode preference toggle
- Branch: feature/issue-137-user-dark-mode-preference (already created)
- Requirements: [paste issue requirements]

Please run all 6 phases with full agent delegation.
```

**What happens:**
1. Issue-pickup creates branch and does initial analysis
2. You manually delegate to conductor
3. Conductor runs phases 2-6 with all agents
4. Creates PR at the end

**Pros:**
- ✅ More control over issue selection
- ✅ Can review requirements before starting
- ✅ Still gets full conductor orchestration

**Cons:**
- ⚠️ Requires manual delegation step
- ⚠️ Two-step process

---

### **Option 3: Natural Language (SIMPLEST)**

**Use when:** You just want to ask Claude Code to do the work.

```bash
# Just ask naturally - Claude Code routes to conductor
"Pick up issue #137 and implement it fully using all agents.
Work autonomously through the entire workflow without stopping
between steps. Use conductor to orchestrate architect, design,
implementation, audit, and refactor agents as needed."
```

**What happens:**
1. Claude Code's main conversation acts as orchestrator
2. Routes to conductor agent automatically
3. Conductor delegates to all specialized agents
4. Full workflow runs autonomously

**Pros:**
- ✅ Simplest - just natural language
- ✅ No command syntax needed
- ✅ Full flexibility in description

**Cons:**
- ⚠️ Less structured than explicit commands
- ⚠️ Routing depends on clear phrasing

---

## 🔍 Workflow Comparison

| Feature | Option 1: /start-workflow | Option 2: /issue-pickup + conductor | Option 3: Natural Language |
|---------|---------------------------|-------------------------------------|----------------------------|
| **Automation** | Fully automated | Semi-automated | Fully automated |
| **Control** | Conductor decides | You pick issue first | Flexible |
| **Agent Usage** | All agents | All agents | All agents |
| **Todo List** | ✅ Automatic | ✅ Manual delegation | ✅ Automatic |
| **Simplicity** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Structure** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 📋 What You Should See

When conductor runs properly, you'll see:

```
🎯 Phase 1: Issue Discovery and Planning
→ Analyzing backlog for optimal issue selection...

📋 Workflow Plan Created

Agents that will be involved:
  → architect agent (architecture validation)
  → researcher agent (if research needed)
  → design agent (if UI/UX changes)
  → implementation agent (feature development)
  → audit agent (quality checks)
  → refactor agent (if quality < 8.0)
  → debugger agent (if tests fail)

Following 6-phase conductor workflow...

✅ Issue #137 selected: User dark mode preference
→ Consulting architect agent for architecture validation...

I need the architect agent to validate the architecture for issue #137...

● architect(Validate architecture)           ← NEW AGENT APPEARS!
  ⎿ Read(services/api/src/features/...)
  ⎿ Grep(pattern="VSA")
  ✅ Architecture validated

● conductor(Architecture approved)            ← CONDUCTOR RESUMES
  → Moving to Phase 2: Implementation...

● design(Analyze UI changes)                  ← DESIGN AGENT
  ⎿ Read(apps/web/src/components/...)
  ✅ Design reviewed

● implementation(Build feature)               ← IMPLEMENTATION AGENT
  ⎿ Write(services/api/src/features/...)
  ✅ Feature implemented

● conductor(Run quality gates)
  → Delegating to audit agent...

● audit(Quality check)                        ← AUDIT AGENT
  ⎿ Bash(npm run test)
  ⎿ Bash(npm run lint)
  ✅ Quality score: 9.2/10

● conductor(Create PR)
  ⎿ Bash(git push)
  ⎿ Bash(gh pr create)
  ✅ PR #138 created

✅ Workflow complete!
```

**Key indicators delegation is working:**
1. ✅ Todo list appears with 6 phases
2. ✅ Multiple agent names: `● architect(...)`, `● audit(...)`, `● design(...)`
3. ✅ Clear handoffs: conductor → agent → conductor
4. ✅ Agents do the work, not conductor

---

## 🚨 If Delegation Doesn't Work

**Symptoms:**
- Only see `● conductor(busy)` - no other agents
- Conductor reads files itself instead of delegating
- No todo list appears

**Fixes:**
1. **Check tools field** - Conductor needs:
   ```yaml
   tools: Task, TodoWrite, Read, Grep, Glob, Bash, Write, SlashCommand
   ```

2. **Verify delegation pattern** - Should see:
   ```markdown
   I need the architect agent to validate...
   ```
   NOT:
   ```markdown
   **Describe the task:**
   "I need the architect agent to..."
   ```

3. **Restart session** - Config changes require restart

4. **Test delegation**:
   ```bash
   /test-delegation-flow
   ```

---

## 🎯 Recommended Workflow for New Features

**For best results:**

1. **Use `/start-workflow` for full automation:**
   ```bash
   /start-workflow issue=137
   ```

2. **Let conductor work autonomously:**
   - Don't interrupt between phases
   - Only intervene if conductor asks questions
   - Trust the agent delegation

3. **Monitor progress via todo list:**
   - See which phase is active
   - Track agent invocations
   - Verify quality gates pass

4. **Review PR when complete:**
   - Conductor creates PR automatically
   - Check PR description has "Fixes #137"
   - Review agent work in PR diff

---

## 📚 Related Documentation

- **Conductor Agent**: `.claude/agents/conductor.md`
- **Delegation Pattern**: `.claude/commands/docs/agent-delegation-pattern.md`
- **Delegation Fix Summary**: `.claude/test-results/conductor-delegation-fix-summary.md`
- **Issue Pickup**: `.claude/commands/issue-pickup.md`

---

## 🎬 Quick Start

**Just want to get started? Use this:**

```bash
# For new issues
/start-workflow

# For specific issue
/start-workflow issue=137

# Natural language (simplest)
"Pick up issue #137 and run the full conductor workflow with all agents"
```

**That's it!** Conductor handles everything from issue selection to PR creation. 🎉
