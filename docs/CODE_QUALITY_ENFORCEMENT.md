# Code Quality Enforcement System

This toolkit includes a **layered enforcement system** that ensures Claude Code follows your coding principles (DRY, SOLID, SOC, typed, modular, centralized, Clean Code) and uses specialized agents when appropriate.

## The Problem

Claude Code often "forgets" to:
- Use specialized agents (refactor, architect, database, etc.)
- Follow coding principles in CLAUDE.md
- Validate code quality before writing

## The Solution: Layered Enforcement

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 1: UserPromptSubmit - enforce-agent-routing.sh           │
│ • Detects task type from user prompt                           │
│ • Injects MANDATORY agent delegation context                   │
│ • Makes Claude AWARE it should use specific agents             │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ Layer 2: PreToolUse - validate-code-quality.sh                 │
│ • Intercepts Edit/Write BEFORE execution                       │
│ • Checks for principle violations (untyped, magic strings)     │
│ • BLOCKS if violations detected                                │
│ • Suggests appropriate agent to use                            │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ Layer 3: PostToolUse - post-tool-quality-gate.sh               │
│ • Runs AFTER Edit/Write completes                              │
│ • Validates TypeScript types, ESLint                           │
│ • Reports quality issues to Claude                             │
│ • Logs to .claude/logs/quality-gate.log                        │
└────────────────────────────────────────────────────────────────┘
```

## Hooks Overview

### 1. `enforce-agent-routing.sh` (UserPromptSubmit)

**Purpose**: Force Claude to use specialized agents based on task keywords.

**Triggers on keywords**:
| Keywords | Recommended Agent |
|----------|-------------------|
| database, migration, schema | `database` agent |
| refactor, clean up, simplify | `refactor` agent |
| architect, solid, structure | `architect` agent |
| implement, create, build | `implementation` agent |
| review, validate, audit | `code-reviewer` agent |
| security, vulnerability | `security-pentest` agent |
| ui, frontend, component | `design` / `ui-frontend-agent` |
| workflow, coordinate | `orchestrator` / `conductor` |

**Example injection**:
```
MANDATORY: Agent Delegation Required

This task matches patterns that REQUIRE specialized agents:
- Database operation detected

You MUST use these agents:
- database agent: Safe database operations with schema validation
```

### 2. `validate-code-quality.sh` (PreToolUse)

**Purpose**: Block code that violates principles BEFORE it's written.

**Checks performed**:
- **Typed Code**: Functions with untyped parameters, `any` usage
- **DRY**: Hardcoded strings (>3 magic strings)
- **SOLID/SRP**: Code blocks >50 lines
- **Layer Violations**: Direct database access outside repository layer
- **Robustness**: Async functions without error handling

**Behavior**:
- **Block** + suggest agent if critical violations
- **Allow with warning** for minor issues
- **Allow** if all checks pass

### 3. `post-tool-quality-gate.sh` (PostToolUse)

**Purpose**: Validate code quality AFTER changes are made.

**Checks performed**:
- TypeScript type checking (`tsc --noEmit`)
- ESLint validation
- File size warnings (>300 lines)
- Function count per file (>15)
- Tech debt markers (TODO/FIXME/HACK)

**Output**: Quality report injected as additional context for Claude.

## Installation

### For New Repositories (Using Submodule)

1. Add the toolkit as a submodule:
```bash
git submodule add https://github.com/your-org/claude-code-toolkit.git .claude-toolkit
```

2. Copy the settings template:
```bash
cp .claude-toolkit/templates/settings-with-hooks.json .claude/settings.json
```

3. Run sync to copy hooks:
```bash
bash .claude-toolkit/scripts/sync-claude-toolkit.sh
```

### For Existing Repositories

If hooks aren't configured, the sync script will warn you:

```
⚠️  HOOKS NOT CONFIGURED in settings.json!
   Your code quality enforcement hooks exist but aren't wired up.

   To enable enforcement, add hooks to your settings.json:
   - See template: .claude-toolkit/templates/settings-with-hooks.json
```

**To enable hooks manually**, merge this into your `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/enforce-agent-routing.sh\" \"$CLAUDE_USER_PROMPT\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/validate-code-quality.sh\" \"$CLAUDE_TOOL_NAME\" \"$CLAUDE_TOOL_ARGS\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-quality-gate.sh\" \"$CLAUDE_TOOL_NAME\" \"$CLAUDE_TOOL_ARGS\""
          }
        ]
      }
    ]
  }
}
```

## Principles Enforced

| Principle | Description | Enforcement |
|-----------|-------------|-------------|
| **DRY** | Don't Repeat Yourself | Detect magic strings, duplicate patterns |
| **SOLID** | Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion | File/function size limits, layer violations |
| **SOC** | Separation of Concerns | Layer boundary validation |
| **Typed** | TypeScript strict types | No `any`, explicit types |
| **Modular** | Small, focused modules | File size warnings |
| **Centralized** | Shared utilities/constants | Magic string detection |
| **Clean Code** | Uncle Bob's principles | All of the above |

## Logs and Audit Trail

All hook activity is logged to `.claude/logs/`:

- `quality-gate.log` - PostToolUse quality check results
- `agent-invocations.log` - Agent delegation tracking
- `command-invocations.log` - Slash command usage
- `delegation-transparency.log` - Full delegation audit

## Customizing Enforcement

### Disable Specific Checks

Edit the hook scripts in `.claude/hooks/` to:
- Comment out checks you don't want
- Adjust thresholds (e.g., change `LINE_COUNT > 50` to `> 100`)
- Add project-specific patterns

### Add Project-Specific Rules

Create `.claude/hooks/project-rules.sh` and source it from the main hooks:

```bash
# In validate-code-quality.sh, add:
if [ -f "$PROJECT_DIR/.claude/hooks/project-rules.sh" ]; then
  source "$PROJECT_DIR/.claude/hooks/project-rules.sh"
fi
```

## Troubleshooting

### Hooks Not Running

1. Check settings.json has hooks configured:
```bash
cat .claude/settings.json | grep -E "PreToolUse|PostToolUse|UserPromptSubmit"
```

2. Verify hooks are executable:
```bash
chmod +x .claude/hooks/*.sh
```

3. Test hook manually:
```bash
bash .claude/hooks/validate-code-quality.sh "Edit" '{"file_path": "test.ts"}'
```

### Too Many False Positives

Adjust thresholds in the hook scripts:
- `MAGIC_COUNT > 3` → Increase for projects with many strings
- `LINE_COUNT > 50` → Increase for complex functions
- Skip specific file patterns in the `case` statement

### Claude Ignoring Agent Suggestions

If Claude still doesn't use agents after injection:
1. Make the context more assertive in `enforce-agent-routing.sh`
2. Use **blocking** instead of advisory in PreToolUse hooks
3. Add rules to your `CLAUDE.md` that reference the hooks

## Summary

| Hook | When | Purpose |
|------|------|---------|
| `enforce-agent-routing.sh` | Before Claude sees prompt | Inject agent routing context |
| `validate-code-quality.sh` | Before Edit/Write | Block principle violations |
| `post-tool-quality-gate.sh` | After Edit/Write | Validate quality, report issues |

This layered approach ensures Claude follows your principles at every step of code creation.
