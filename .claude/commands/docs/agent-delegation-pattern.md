# Agent Delegation Pattern Documentation

**The definitive guide to natural language delegation in TribeVibe's Agent SDK system.**

## 🎯 Core Principle

**Agents describe WHAT needs to be done in natural language. Claude Code's runtime interprets these descriptions and makes the actual tool calls.**

### Why This Pattern Exists

The Agent SDK uses **markdown files with YAML frontmatter** to define agents. These files are NOT executable code - they are **instructions** that Claude Code reads and interprets. The runtime then decides which tools to invoke based on the natural language descriptions.

## ✅ Correct Delegation Pattern

### **Pattern Structure**

```markdown
I need the [agent-name] agent to [task-description].

[Context that the agent needs to know]
```

### **Real Examples from TribeVibe**

**✅ Architect Agent Delegation:**
```markdown
I need the architect agent to validate the architecture for issue #137: User dark mode preference.

Requirements:
User wants to toggle dark mode in settings and have it persist.

AI analysis suggests: Add dark mode toggle to settings page, store preference in user profile.
```

**✅ Design Agent Delegation:**
```markdown
I need the design agent to improve the UX for SettingsSection component.

Design issues to address:
- Dark mode toggle needs better visual feedback
- Accessibility improvements needed
```

**✅ Implementation Agent Delegation:**
```markdown
I need the implementation agent to implement issue #137: User dark mode preference.

Architecture plan:
- Add darkMode field to User entity
- Create settings API endpoint
- Implement frontend toggle component
```

**✅ Researcher Agent Delegation:**
```markdown
I need the researcher agent to research best practices for: Dark mode implementation in React.

Context: Building PWA with Tailwind, need system preference detection and user override.
```

## ❌ Incorrect Patterns (DO NOT USE)

### **1. Code Syntax in Agent Files**

```markdown
❌ WRONG - This is executable code syntax, not agent markdown:

Task({
  subagent_type: "architect",
  description: "Review architecture",
  prompt: "Please validate the architecture..."
})
```

**Why it's wrong**: Agent markdown files are NOT JavaScript/TypeScript. They are instructions that describe behavior.

### **2. SlashCommand Tool Syntax**

```markdown
❌ WRONG - This is runtime tool syntax, not agent delegation:

SlashCommand("/architect", {
  scope: "backend",
  severity: "critical"
})
```

**Why it's wrong**: SlashCommand is a tool that the runtime uses. Agents describe the need, runtime chooses the tool.

### **3. Vague Delegations Without Agent Name**

```markdown
❌ WRONG - Runtime doesn't know WHO to delegate to:

I need this feature implemented following the approved architecture plan.
```

**Why it's wrong**: No explicit agent mention means runtime can't determine which agent to invoke.

### **4. Redundant Instructions**

```markdown
❌ WRONG - Agent already knows what to check:

I need the architect agent to validate architecture.

Please check:
- VSA compliance (Controller → Service → Repository)
- SOLID principles
- Layer boundaries
- Contract-first development
- DRY violations
[20 more bullet points...]
```

**Why it's wrong**: The architect agent's markdown file already lists all these responsibilities. Repeating them wastes tokens and confuses the delegation.

## 📋 Context vs Responsibilities

### **What Belongs in Delegation (Context)**

✅ Issue number and title
✅ Files to analyze
✅ Previous results from other agents
✅ Specific scope or focus area
✅ User-reported issues

**Example:**
```markdown
I need the architect agent to validate architecture for issue #137.

Files changed:
- apps/web/src/components/Settings.tsx
- services/api/src/features/user/UserEntity.ts

Previous audit score: 6.5/10 (needs improvement)
```

### **What Belongs in Agent Files (Responsibilities)**

✅ What to check (VSA, SOLID, layer boundaries, etc.)
✅ How to perform the analysis
✅ Output format requirements
✅ Validation criteria
✅ Tool restrictions

**Example (from architect.md):**
```yaml
---
name: architect
description: Validates VSA compliance, SOLID principles, layer boundaries
capabilities:
  - Architectural pattern validation
  - Contract-first development checks
  - Layer boundary enforcement
tools: [Read, Grep, Glob, Bash, Write]
---
```

## 🔍 How to Fix Delegation Issues

### **Step 1: Identify the Problem**

**Symptoms:**
- Agent reads files itself instead of delegating
- Workflow stops after one delegation
- "OR" choices causing wrong behavior

**Example from conductor.md (BEFORE fix):**
```markdown
❌ PROBLEM: Vague delegation with OR choice

"I need this feature implemented.

Please implement following the architecture plan.

OR if you need architectural guidance first, consult the architect specialist..."
```

### **Step 2: Simplify to Context Only**

**Remove:**
- All "what to check" instructions (agent already knows)
- OR choices (make delegation mandatory)
- Redundant bullet points

**Keep:**
- Issue number/title
- Files to work with
- Previous results
- Specific context

**Example (AFTER fix):**
```markdown
✅ FIXED: Clear, context-only delegation

I need the implementation agent to implement issue #137: User dark mode preference.

Architecture plan:
- Add darkMode field to User entity
- Create settings API endpoint
- Implement frontend toggle
```

### **Step 3: Add Explicit Agent Mention**

**Pattern:** Always use `"I need the [agent] agent to [task]"`

**Examples:**
- `I need the architect agent to validate...`
- `I need the design agent to improve...`
- `I need the researcher agent to research...`
- `I need the debugger agent to investigate...`

### **Step 4: Add Guards for DO NOT Behaviors**

**For conductor/orchestrator agents that might try to do work themselves:**

```markdown
⚠️ CRITICAL: DO NOT READ FILES YOURSELF
- ❌ DO NOT use Read tool on code files
- ❌ DO NOT analyze architecture yourself
- ✅ DO delegate to architect agent

I need the architect agent to validate architecture for issue #137.
```

## 🧪 Testing Delegation

### **Test Pattern**

```markdown
### 🧪 Test Delegation Mode

**To verify delegation works, user can request:** "test [agent-name] delegation"

**When you receive this request:**

1. Create test todo list
2. Delegate simple task with explicit agent mention
3. Verify response received
4. Report success/failure
```

### **Example: Conductor Test**

```markdown
1. Create todo:
[
  { content: "Test delegation to researcher agent", status: "in_progress", activeForm: "Testing delegation" }
]

2. Delegate:
I need to test delegation by consulting the researcher agent.

"Please research TypeScript monorepo best practices in 2025.

Focus on: npm workspaces, Nx, Turborepo.
Provide: Brief summary (3-5 sentences)."

3. After response:
✅ Delegation Test Complete

Researcher agent responded successfully with: [SUMMARY]

🎯 Delegation pattern verified:
- Natural language description was interpreted
- Researcher agent invoked
- Response received and processed
```

## 📊 Agent Terminology Standards

### **Use "agent" NOT "specialist"**

**✅ CORRECT:**
- "I need the architect **agent** to..."
- "Consult the researcher **agent** for..."
- "Delegate to the design **agent** with..."

**❌ INCORRECT:**
- "I need the architect **specialist** to..."
- "Consult the researcher **specialist** for..."
- "Delegate to the design **specialist** with..."

**Why "agent":**
- Matches YAML: `name: architect`
- Matches Task tool: `subagent_type: "architect"`
- Matches self-identification: "You are the **Architect Agent**"
- More explicit and technical
- Consistent with Claude Code Agent SDK terminology

## 🛠️ Creating New Agents

### **Agent Creator Pattern Enforcement**

When using agent-creator to generate new agents, ensure it teaches the natural language pattern:

```markdown
## ⚠️ CRITICAL: Natural Language Delegation

**YOU DESCRIBE WHAT NEEDS TO BE DONE - Claude Code's runtime handles execution.**

### Core Principle
Agent markdown uses **natural language descriptions** of tasks, not executable code syntax.

**✅ DO describe tasks in natural language:**
- "For architectural validation, consult the architect agent about..."
- "To analyze design patterns, run the design review command with..."

**❌ DO NOT write code syntax:**
- ❌ `Task({ subagent_type: "architect", ... })`
- ❌ `SlashCommand("/design-review", { ... })`

**✅ DO use bash commands for system operations:**
- ✅ `npm run build`
- ✅ `gh pr create --title "..." --body "..."`
- ✅ `/command-name --arg value` (slash commands)
```

## 🎯 Quick Reference

### **Delegation Checklist**

When writing agent delegation in any agent file:

- [ ] Use explicit agent mention: "I need the [agent] agent to..."
- [ ] Provide only context (issue #, files, results)
- [ ] DO NOT repeat agent's responsibilities
- [ ] DO NOT use OR choices (make delegation mandatory)
- [ ] DO NOT write code syntax (Task, SlashCommand)
- [ ] DO use natural language descriptions
- [ ] Add "DO NOT READ FILES" guards if needed
- [ ] Use "agent" terminology (not "specialist")

### **Valid Delegation Templates**

**Architecture Review:**
```markdown
I need the architect agent to validate architecture for issue #[NUMBER].

Requirements: [ISSUE_SUMMARY]
[Optional: Files to review, previous findings]
```

**Design Improvement:**
```markdown
I need the design agent to improve UX for [COMPONENT_NAME].

[Optional: Specific issues to address]
```

**Implementation:**
```markdown
I need the implementation agent to implement issue #[NUMBER]: [TITLE].

Architecture plan: [SUMMARY]
```

**Research:**
```markdown
I need the researcher agent to research best practices for: [TOPIC].

Context: [BRIEF_CONTEXT]
```

**Debugging:**
```markdown
I need the debugger agent to investigate [ISSUE].

Failed tests: [LIST]
Recent changes: [SUMMARY]
```

**Code Quality:**
```markdown
I need the audit agent to audit code quality for issue #[NUMBER].

Files changed: [LIST]
```

**Refactoring:**
```markdown
I need the refactor agent to improve code quality.

Current audit score: [SCORE]/10
Critical issues: [LIST]
Files to refactor: [LIST]
```

---

## 📚 Related Documentation

- **Agent Architecture**: `docs/agents-architecture.md`
- **Command Inventory**: `docs/command-inventory.md`
- **Slash Command Best Practices**: `.claude/commands/docs/slash-command-best-practices.md`
- **Agent Creator**: `.claude/agents/agent-creator.md`
- **Conductor Agent**: `.claude/agents/conductor.md`
- **Orchestrator Agent**: `.claude/agents/orchestrator.md`

---

**Last Updated**: 2025-10-02
**Pattern Status**: ✅ Enforced system-wide across all agents
