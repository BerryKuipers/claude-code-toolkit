# Help - Unified Command System Guide

**Arguments:** [command] [--patterns] [--examples]

**Success Criteria:** Clear understanding of command system, collaboration patterns, and usage examples

**Description:** Comprehensive help system explaining the hub-and-spoke architecture, command collaboration patterns, and intelligent workflows.

## 🎯 Command System Overview

### Hub-and-Spoke Architecture
```
                    ORCHESTRATOR (Central Hub)
                           |
        ┌─────────────────┼─────────────────┐
        |                 |                 |
    SPECIALIZED       SPECIALIZED       SPECIALIZED
    COMMANDS          COMMANDS          COMMANDS
    /debug            /refactor         /design-review
    /test-all         /architect        /issue-pickup
```

**Core Principle:** All command coordination goes through the orchestrator to prevent conflicts and enable intelligent collaboration.

## 🚀 Quick Start

### Basic Commands
```bash
/debug                          # Comprehensive issue analysis
/debug inspect .auth-form       # Chrome DevTools DOM inspection
/debug logs auth --last 1h      # Backend log analysis

/issue-pickup-smart             # Smart GitHub issue selection
/refactor component-name        # Code refactoring with intelligence
/test-all                       # Comprehensive testing suite
/orchestrator task="description" # Central workflow coordination
```

### Getting Help
```bash
/help                           # This comprehensive guide
/help debug                     # Specific command help
/orchestrator help              # Orchestrator patterns and usage
```

## 🤝 Collaboration Patterns

The orchestrator intelligently determines when commands should collaborate:

### Pattern 1: Refactor + Architect Collaboration
**When:** Complex architectural changes detected (complexity >70)
**How:** Shared workspace with scoped architectural guidance
**Example:**
```bash
User: /refactor authentication-system
→ Refactor detects complexity
→ Orchestrator brings in /architect
→ Architect provides structural guidance
→ Refactor proceeds with constraints
→ Result: Architecturally sound refactoring
```

### Pattern 2: Debug + Test-All Intelligence
**When:** Specific issue types identified
**How:** Focused testing instead of full suite
**Example:**
```bash
User: /debug
→ Debug finds "authentication field mismatch"
→ Orchestrator coordinates auth-focused testing
→ Test-All runs authentication-specific tests
→ Result: Faster, targeted validation
```

### Pattern 3: Issue-Pickup + Design-First Workflow
**When:** UI-related GitHub issues selected
**How:** Sequential design → refactor → validation
**Example:**
```bash
User: /issue-pickup-smart
→ Selects UI redesign issue
→ Orchestrator creates design-first pipeline
→ Design-Review → Refactor → Test-User-Flow
→ Result: Design-aligned implementation
```

### Pattern 4: Database Performance Pipeline
**When:** Performance issues detected
**How:** Sequential high-risk operations with validation
**Example:**
```bash
User: /debug (finds DB performance issue)
→ Orchestrator creates sequential pipeline
→ DB-Manage → Migrate-Analysis → Test-All
→ Each step validates before proceeding
→ Result: Safe performance optimization
```

## 🛠️ Command Categories

### Analysis & Debugging
- `/debug` - Multi-source issue analysis (Loki + Chrome DevTools + System)
- `/architecture-tester` - Validate command system architecture
- `/command-analyzer` - Analyze command performance and patterns

### Development & Refactoring
- `/refactor` - Intelligent code refactoring with architectural awareness
- `/architect` - System architecture analysis and recommendations
- `/design-review` - UI/UX component analysis and improvements

### Testing & Validation
- `/test-all` - Comprehensive testing orchestration
- `/test-user-flow` - End-to-end user workflow validation
- `/ci-test-fixer` - Continuous integration test resolution

### Workflow & Project Management
- `/issue-pickup-smart` - Intelligent GitHub issue selection
- `/pr-process` - Pull request creation and management
- `/orchestrator` - Central workflow coordination hub

### Database & Infrastructure
- `/db-manage` - Database operations and management
- `/migrate-analysis` - Database migration analysis

## 🎛️ Orchestrator Modes

### Advisory Mode (Recommended)
```bash
/orchestrator task="description" mode=advisory
```
- Non-blocking background execution
- Commands run independently
- Results aggregated and reported
- Best for most workflows

### Full Mode (Comprehensive)
```bash
/orchestrator task="description"
```
- Complete workflow orchestration
- Step-by-step execution with validation
- Detailed reporting and analysis
- Best for complex, high-risk tasks

### Collaborative Mode (Smart Teamwork)
```bash
/orchestrator task="description" mode=collaborative
```
- Shared workspace creation
- Multi-command expertise coordination
- Context sharing between specialists
- Best for tasks requiring multiple areas of expertise

## 🔧 Advanced Usage

### MCP Integration
```bash
# Chrome DevTools (Frontend)
/debug inspect .login-form          # DOM inspection
/debug network xhr                  # Network monitoring
/debug console 'localStorage.token' # Console execution
/debug breakpoint set auth.js:42    # Breakpoint management
/debug profile start               # Performance profiling

# Loki (Backend)
/debug logs service --last 30m     # Log analysis
/debug trace req-123456            # Request tracing
```

### Workspace Management
```bash
# Collaborative commands automatically create shared workspaces
# Location: /tmp/orchestrator-{session-id}/collaborative/
# Auto-cleanup: After task completion (configurable timeout)
# Shared files: context.json, guidance files, results
```

### Conflict Resolution
When commands disagree, orchestrator uses these rules:
1. **Primary command authority** - Original command has final say
2. **Risk-based priority** - Higher-risk recommendations override lower-risk
3. **User confirmation** - Complex conflicts prompt user decision
4. **Consensus building** - Multiple iterations until agreement reached

## 🚨 Fallback Modes

### MCP Server Unavailable
- **Chrome DevTools down:** Debug gracefully falls back to Loki + system analysis
- **Loki unavailable:** Uses local log files and system diagnostics
- **Database unreachable:** Reads cached schema and configuration files

### Command Failures
- **Primary command fails:** Orchestrator routes to backup approach
- **Collaboration breakdown:** Falls back to primary command only
- **Workspace issues:** Creates temporary local workspace

## 📊 Usage Examples by Scenario

### Scenario 1: "I have a bug in authentication"
```bash
/debug                           # Comprehensive analysis
# → Chrome DevTools checks frontend
# → Loki analyzes backend logs
# → System checks configuration
# → Orchestrator coordinates fix with /refactor if needed
```

### Scenario 2: "I need to refactor a complex component"
```bash
/refactor UserAuthSystem         # Smart refactoring
# → Analyzes complexity and impact
# → If high complexity: brings in /architect
# → Provides structural guidance
# → Proceeds with architectural constraints
```

### Scenario 3: "I want to work on a GitHub issue"
```bash
/issue-pickup-smart              # Intelligent issue selection
# → Selects optimal issue for current context
# → Creates feature branch
# → Orchestrator determines task type
# → Routes to appropriate specialists (design/refactor/test)
```

### Scenario 4: "I need to validate my changes"
```bash
/test-all                        # Comprehensive testing
# → Determines what changed via git analysis
# → Runs targeted test suites
# → If issues found: coordinates with /debug
# → Provides actionable recommendations
```

## 💡 Pro Tips

### Efficiency
- Use `mode=advisory` for background work while you continue coding
- Combine commands: `/debug` findings automatically inform `/refactor` scope
- Let orchestrator handle command sequencing - don't run commands manually in sequence

### Best Practices
- Start with `/debug` for any issue - it provides the best context for other commands
- Use `/issue-pickup-smart` instead of manual issue selection
- Let complex refactoring trigger architectural consultation automatically
- Trust the orchestrator's collaboration patterns - they prevent conflicts

### Troubleshooting
- If MCP servers aren't connecting: Commands gracefully fall back
- If commands disagree: Orchestrator resolves conflicts automatically
- If workspaces accumulate: Auto-cleanup happens after task completion
- If unsure what to run: `/orchestrator help` provides intelligent suggestions

## 🎯 Getting Started Checklist

1. ✅ **Verify MCP servers:** `claude mcp list` should show chrome-devtools and loki
2. ✅ **Test basic command:** `/debug --dry-run` to validate setup
3. ✅ **Try collaboration:** `/refactor` on a complex file to see orchestrator coordination
4. ✅ **Explore workflows:** `/issue-pickup-smart` for intelligent project workflows
5. ✅ **Use orchestrator:** `/orchestrator task="improve authentication system"` for complex tasks

---

**Remember: The orchestrator is your intelligent assistant that coordinates all command expertise. Let it handle the complexity while you focus on the creative work!** 🚀