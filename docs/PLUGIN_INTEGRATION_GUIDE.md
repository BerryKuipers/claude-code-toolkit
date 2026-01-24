# Plugin Integration Guide: everything-claude-code

This document defines the integration strategy for adopting the upstream `everything-claude-code` plugin as a baseline while maintaining the toolkit as a thin orchestration + policy layer.

## Layering Model

```
┌─────────────────────────────────────────────────────────────┐
│  PROJECT OVERLAYS (wsc-*, cph-*)                           │
│  Project-specific commands, rules, allowed agents          │
├─────────────────────────────────────────────────────────────┤
│  TOOLKIT POLICY LAYER (bk-*)                               │
│  Orchestration wrappers, output contracts, verification    │
│  gates, house-style rules, project configurations          │
├─────────────────────────────────────────────────────────────┤
│  UPSTREAM BASELINE (everything-claude-code plugin)         │
│  Core agents: planner, architect, code-reviewer,           │
│  security-reviewer, e2e-runner, tdd-guide, doc-updater,    │
│  build-error-resolver, refactor-cleaner                    │
│  Core skills: coding-standards, backend-patterns,          │
│  frontend-patterns, tdd-workflow, security-review          │
└─────────────────────────────────────────────────────────────┘
```

## Naming Convention (Collision-Proof)

To avoid collisions between toolkit commands/agents and upstream plugin names:

| Prefix    | Owner                  | Purpose                                    |
|-----------|------------------------|--------------------------------------------|
| (none)    | Upstream plugin        | Baseline agents/commands from plugin       |
| `bk-`     | This toolkit           | Toolkit wrappers with policy enforcement   |
| `wsc-`    | WescoBar project       | WescoBar-specific overlays                 |
| `cph-`    | CoPhusher project      | CoPhusher-specific overlays                |
| `legacy-` | Deprecated toolkit     | Old names pending removal                  |

### Examples

- `/plan` → Upstream plugin command (baseline)
- `/bk-plan` → Toolkit wrapper (adds verification gates + output contract)
- `/wsc-deploy` → WescoBar-specific deployment command
- `/legacy-architect` → Old toolkit architect command (deprecated)

## Integration Rules

### 1. Use Upstream as Baseline
- Upstream agents (planner, architect, code-reviewer, etc.) provide core functionality
- Do NOT duplicate upstream agent logic in toolkit
- Reference upstream agents through Task tool with `subagent_type`

### 2. Toolkit Wrappers Add Policy
Toolkit `bk-*` commands wrap upstream agents to add:
- Output contract templates (standard report format)
- Verification gates (test, lint, build checks before/after)
- House-style enforcement
- Quality thresholds

### 3. Project Overlays Add Context
Project-specific overlays (`wsc-*`, `cph-*`) configure:
- Which baseline agents are allowed
- Which MCP servers are enabled
- Project-specific rules and thresholds
- Deployment targets

### 4. Legacy Migration Path
Items marked `legacy-*` will be:
1. Kept functional during transition
2. Emit deprecation warnings in output
3. Removed after 30 days or 2 major releases

## Adding New Commands Without Collisions

1. **Check upstream first**: Search if upstream plugin provides the functionality
2. **If upstream exists**: Create a `bk-*` wrapper that orchestrates it with your policy
3. **If toolkit-specific**: Use `bk-*` prefix for toolkit-level commands
4. **If project-specific**: Use project prefix (`wsc-*`, `cph-*`, etc.)
5. **Never create un-prefixed commands** that might collide with future upstream additions

## Configuration

### Toolkit config (`.claude/config.yml`)
```yaml
integration:
  upstream_plugin: everything-claude-code
  collision_prefix: bk

policy:
  verification_gates:
    pre_implement: [validate-typescript, validate-lint]
    post_implement: [validate-build, run-tests]

  output_contract:
    include_summary: true
    include_files_changed: true
    include_next_steps: true
```

### Project overlay config (`overlays/<project>/config.yml`)
```yaml
project: wescobar
prefix: wsc

allowed_agents:
  - architect
  - code-reviewer
  - security-reviewer
  - e2e-runner

enabled_mcp_servers:
  - supabase
  - vercel

disabled_commands:
  - deploy  # Use wsc-deploy instead
```

## Verification Checklist

Before using integrated system:

- [ ] Upstream plugin installed: `claude /plugins`
- [ ] No duplicate command names: `claude /help | grep -E "^/(plan|review|architect)"`
- [ ] Wrapper commands work: `/bk-plan "test feature"`
- [ ] Upstream agents accessible: Run `Task` with upstream `subagent_type`
- [ ] Project overlay loads: Check CLAUDE.md for project context

## Rollback Plan

If integration causes issues:

1. **Immediate**: Disable toolkit hooks in `.claude/settings.json`
2. **Quick**: Rename conflicting `bk-*` commands back to original names
3. **Full rollback**: Uninstall upstream plugin: `/plugin uninstall everything-claude-code`
4. **Restore**: Git revert changes to `.claude/` directory

---

*Generated: 2026-01-24*
*Toolkit Version: main*
