# Hub-and-Spoke Command Architecture

## 🎯 Core Principle: Orchestrator as Central Hub

**All inter-command delegation MUST go through the orchestrator to prevent conflicts, overlaps, and ensure intelligent coordination.**

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                            │
│                      (Central Hub)                             │
│   • Task Analysis        • Command Discovery                   │
│   • Smart Routing        • Conflict Prevention                 │
│   • Resource Management  • Learning & Optimization             │
└─────────────────┬───────────────────────────────┬─────────────┘
                  │                               │
         ┌────────▼────────┐                ┌────▼──────────┐
         │  Specialized    │                │ Specialized   │
         │   Commands      │                │   Commands    │
         │                 │                │               │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐    ┌────▼────┐
    │ debug   │      │refactor │      │test-all │    │design-  │
    │         │      │         │      │         │    │review   │
    │ ├─logs  │      │         │      │         │    │         │
    │ ├─trace │      │         │      │         │    │         │
    │ ├─ports │      │         │      │         │    │         │
    │ └─chrome│      │         │      │         │    │         │
    │ devtools│      │         │      │         │    │         │
    └─────────┘      └─────────┘      └─────────┘    └─────────┘
```

## 🚨 STRICT RULES

### ✅ ALLOWED Patterns
- **User** → `/command` (direct invocation)
- **Command** → `/orchestrator` task="..." mode=advisory (delegation request)
- **Orchestrator** → Multiple commands (intelligent routing)
- **Commands** use MCP tools directly (chrome-devtools, loki, etc.)

### ❌ FORBIDDEN Patterns
- **Command A** → **Command B** (direct command-to-command)
- **Command** → Multiple other commands (bypassing orchestrator)
- **Circular delegation** (Command A → Orchestrator → Command A)

## 📋 Implementation Guidelines

### For Specialized Commands (debug, refactor, test-all, etc.)

#### 1. **Self-Contained Execution**
Commands should handle their primary responsibility independently:
```bash
# ✅ GOOD - debug handles its own analysis
/debug inspect .auth-form    # Uses chrome-devtools MCP directly
/debug logs auth --last 1h   # Uses loki MCP directly
```

#### 2. **Orchestrator Delegation for Follow-up Actions**
When additional commands are needed, delegate through orchestrator:
```bash
# ✅ GOOD - debug delegates follow-up actions
# After root cause analysis, delegate fix recommendations:
SlashCommand "/orchestrator" "task=\"fix authentication issue: token validation error\" mode=advisory"
```

#### 3. **Advisory Mode Usage**
Always use `mode=advisory` for background task spawning:
```bash
# ✅ GOOD - Non-blocking advisory delegation
/orchestrator task="resolve database performance issues" mode=advisory

# ❌ BAD - Direct blocking calls
/db-manage --performance-test
/migrate-analysis --fix-slow-queries
```

### For Entry Point Commands (issue-pickup-smart, etc.)

#### 1. **Task Context Analysis**
Analyze the task before delegating:
```bash
# ✅ GOOD - Analyze issue type first
ISSUE_TYPE=$(analyze_github_issue "$ISSUE_ID")
TASK_DESCRIPTION="work on $ISSUE_TYPE issue: $ISSUE_TITLE"
```

#### 2. **Single Orchestrator Delegation**
Make one intelligent delegation call:
```bash
# ✅ GOOD - Single delegation with context
SlashCommand "/orchestrator" "task=\"$TASK_DESCRIPTION\" mode=advisory"

# ❌ BAD - Multiple separate delegations
SlashCommand "/design-review" "$ISSUE_ID"
SlashCommand "/refactor" "$COMPONENT"
SlashCommand "/test-all" "relevant"
```

## 🔄 Workflow Examples

### Example 1: Issue Pickup with Smart Delegation
```bash
# 1. User starts issue pickup
/issue-pickup-smart

# 2. Issue picker analyzes and creates branch
create_branch_for_issue "$SELECTED_ISSUE"

# 3. Issue picker delegates to orchestrator
TASK="work on UI component redesign: improve user profile layout"
SlashCommand "/orchestrator" "task=\"$TASK\" mode=advisory"

# 4. Orchestrator analyzes and routes
# → Determines: UI task, medium complexity
# → Delegates to: /design-review + /test-user-flow (in background)

# 5. User gets immediate feedback, background work continues
echo "✅ Branch created. Design analysis running in background..."
```

### Example 2: Debug Command with Fix Delegation
```bash
# 1. User runs debug
/debug

# 2. Debug analyzes using MCP tools directly
# - Loki MCP for logs
# - Chrome DevTools MCP for frontend
# - System analysis for ports/config

# 3. Debug identifies root cause
ROOT_CAUSE="Authentication middleware field mismatch"
CONFIDENCE="95%"

# 4. Debug delegates fix to orchestrator
TASK="fix authentication issue: middleware sets request.user.id but controller expects request.user.userId"
SlashCommand "/orchestrator" "task=\"$TASK\" mode=advisory"

# 5. Orchestrator routes to appropriate fix commands
# → Analyzes: authentication, fixing category, medium risk
# → Delegates to: /refactor (field alignment) + /test-user-flow (validation)
```

### Example 3: Design Review with Implementation Delegation
```bash
# 1. User runs design review
/design-review component-name

# 2. Design review analyzes component
# - Reviews current implementation
# - Identifies improvement opportunities
# - Generates design recommendations

# 3. Design review delegates implementation
TASK="implement design improvements for UserProfile component: add responsive layout and improve accessibility"
SlashCommand "/orchestrator" "task=\"$TASK\" mode=advisory"

# 4. Orchestrator routes to implementation commands
# → Analyzes: frontend, refactoring, medium complexity
# → Delegates to: /refactor + /test-all (validation)
```

## 🛡️ Conflict Prevention

### Resource Coordination
The orchestrator prevents conflicts by:
- **Port management:** Ensuring only one command uses specific ports
- **File locking:** Coordinating access to critical files
- **Process coordination:** Preventing simultaneous builds/tests
- **Database access:** Managing concurrent database operations

### Execution Patterns
- **Sequential:** High-risk operations run one after another
- **Parallel:** Independent analysis tasks run concurrently
- **Conditional:** Support commands only run if primary fails
- **Collaborative:** Commands share workspace for data exchange

## 📊 Benefits of Hub-and-Spoke

### ✅ Advantages
- **No Overlaps:** Central coordination prevents conflicting operations
- **Smart Routing:** Orchestrator learns optimal command combinations
- **Resource Efficiency:** Prevents duplicate work and resource contention
- **Unified Reporting:** Single point for consolidated results
- **Fault Tolerance:** Failed delegations don't cascade to other commands
- **Learning System:** Improves recommendations based on success patterns

### 🚫 Problems Prevented
- **Command Conflicts:** Multiple commands modifying same files
- **Resource Contention:** Competing for ports, database connections
- **Circular Dependencies:** Command A calls B calls C calls A
- **Duplicate Work:** Multiple commands doing the same analysis
- **Inconsistent State:** Commands working with stale or conflicting data

## 🔧 Implementation Checklist

### For Each Specialized Command:
- [ ] **Self-contained:** Handles primary responsibility independently
- [ ] **MCP Integration:** Uses MCP tools directly when needed
- [ ] **Orchestrator Delegation:** Routes follow-up actions through orchestrator
- [ ] **Advisory Mode:** Uses non-blocking mode=advisory for delegations
- [ ] **No Direct Calls:** Never calls other slash commands directly

### For Orchestrator:
- [ ] **Task Analysis:** Analyzes natural language task descriptions
- [ ] **Command Discovery:** Dynamically discovers available commands
- [ ] **Smart Routing:** Maps tasks to optimal command combinations
- [ ] **Conflict Prevention:** Manages resources and execution order
- [ ] **Learning System:** Improves routing based on success metrics

## 📚 Reference Implementation

See these commands for proper hub-and-spoke patterns:
- `orchestrator.md` - Central hub implementation
- `issue-pickup-smart.md` - Entry point with orchestrator delegation
- `debug.md` - Specialized command with orchestrator routing
- `_orchestrator-interface-standard.md` - Integration standards

---

**🎯 Remember: The orchestrator is the ONLY command that should coordinate multiple other commands. All other commands should focus on their specific domain and delegate coordination needs to the orchestrator.**