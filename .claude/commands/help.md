# Help - Unified Command System Guide

**Arguments:** [command] [--quick] [--patterns] [--examples]

**Success Criteria:** Clear understanding of command system, collaboration patterns, and usage examples

**Description:** Comprehensive help system explaining the hub-and-spoke architecture, command collaboration patterns, and intelligent workflows.

---

## ⚡ Quick Reference - What to Use When

### "I want to..."

| Goal | Command | Notes |
|------|---------|-------|
| **Work on a GitHub issue** | `/conductor` or `/issue-pickup` | Full workflow: issue → PR |
| **Run an autonomous task loop** | `/loop <task>` | Loops until done or max iterations |
| **Review architecture** | `/architect` | SOLID, layers, patterns |
| **Improve code quality** | `/refactor` | Safe, atomic improvements |
| **Harden TypeScript types** | `/harden-types` | Strings → enums, `any` → specific types |
| **Run all tests** | `/test-all` | Comprehensive test suite |
| **Test UI in browser** | `/test-ui` | Chrome-based UI testing |
| **Audit code quality** | `/audit` | Scores code 0-10 |
| **Review a PR** | `/review-pr` | Code review with recommendations |
| **Create a PR** | `/pr-process` | PR creation workflow |
| **Save credits (delegate to Gemini)** | `/delegate-gemini` | Optional, requires approval |
| **Capture page screenshots** | `/capture-pages` | Visual documentation |
| **Fix failing E2E tests** | `/fix-e2e-tests` | Automated test fixing |
| **Update dependencies** | `/update-deps` | Safe dependency updates |
| **Fix vulnerabilities** | `/fix-vulns` | Security vulnerability fixes |
| **General task routing** | `/orchestrator` | Routes to appropriate agent |
| **Deploy to staging/prod** | `/deploy` | Docker compose deployment |
| **VPS operations** | `/vps` | Container logs, restart, health |
| **DNS/Cloudflare** | `/dns` | DNS records, SSL, cache |
| **Pre-deploy validation** | `/verify-deploy` | Check config before deploy |

### Quick Decision Tree

```
Start here: What's your task?
    │
    ├─ Full feature from issue? ──────→ /conductor or /loop implement <feature>
    │
    ├─ Fix something? ────────────────→ /loop fix <problem>
    │
    ├─ Improve existing code? ────────→ /refactor <target>
    │
    ├─ Check code quality? ───────────→ /audit
    │
    ├─ Repetitive bulk work? ─────────→ /delegate-gemini (saves credits)
    │
    ├─ Run tests? ────────────────────→ /test-all or /test-ui
    │
    ├─ Deploy to staging/prod? ───────→ /verify-deploy then /deploy
    │
    ├─ VPS issues? ───────────────────→ /vps logs or /vps health
    │
    └─ Not sure? ─────────────────────→ /orchestrator task="<describe it>"
```

### Agent Specializations

| Agent | Specialty | Use When |
|-------|-----------|----------|
| **conductor** | Full workflows | Issue → implementation → PR → merge |
| **orchestrator** | Task routing | Unsure which agent to use |
| **architect** | Architecture | Reviewing design, SOLID, layers |
| **implementation** | Feature dev | Building new features |
| **refactor** | Code improvement | Cleaning up, simplifying |
| **audit** | Quality checks | Pre-deployment, PR reviews |
| **design** | UI/UX | Styling, accessibility |
| **database** | DB operations | Migrations, schema changes |
| **security-pentest** | Security | Vulnerability scanning |
| **gemini-delegation** | Credit saving | Bulk repetitive work |
| **infrastructure** | DevOps | VPS, Docker, Cloudflare, deployments |

---

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

### Workflow Orchestration
- `/loop <task>` - Autonomous task loop (runs until done or max iterations)
- `/conductor` - Full-cycle workflow: issue → implementation → PR → merge
- `/orchestrator` - Central task routing hub
- `/issue-pickup` - Smart GitHub issue selection with resumption

### Analysis & Debugging
- `/debug` - Multi-source issue analysis (Loki + Chrome DevTools + System)
- `/audit` - Comprehensive code quality audit (scores 0-10)
- `/architect` - Architecture analysis, SOLID/VSA validation

### Development & Refactoring
- `/refactor` - Safe code improvement with quality gates
- `/harden-types` - Replace string literals with enums, narrow `any` to specific types
- `/design-review` - UI/UX component analysis
- `/delegate-gemini` - Credit-saving delegation to Gemini (optional)

### Testing & Validation
- `/test-all` - Comprehensive testing orchestration
- `/test-ui` - Browser-based UI testing with Chrome
- `/test-user-flow` - End-to-end user workflow validation
- `/fix-e2e-tests` - Automated E2E test fixing

### Pull Requests & Code Review
- `/review-pr` - Comprehensive PR code review
- `/pr-process` - Pull request creation workflow
- `/pick-next-pr` - Intelligently select safest PR to work on

### Security & Dependencies
- `/fix-vulns` - Automated security vulnerability remediation
- `/update-deps` - Safe dependency update workflow

### Visual & Documentation
- `/capture-pages` - Automated page screenshot capture

### Database & Infrastructure
- `/db-manage` - Database operations and management

### Infrastructure & Deployment
- `/deploy` - Deploy to staging or production via Docker compose
- `/vps` - VPS operations: container logs, restart, health checks
- `/dns` - Cloudflare DNS, SSL, cache, tunnels, Access
- `/verify-deploy` - Pre-flight validation before deployment

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

### Scenario 5: "I want to deploy to staging"
```bash
/verify-deploy staging           # Pre-flight checks first
# → Validates Docker, env vars, ports, DNS
# → Reports errors and warnings
# → Generates checklist

/deploy staging                  # Then deploy
# → Backs up database
# → Pulls Docker images
# → Deploys via docker compose
# → Verifies health checks
```

### Scenario 6: "Something's wrong on the VPS"
```bash
/vps logs api                    # Check API logs
/vps health                      # Run health checks
/vps restart api                 # Restart if needed
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