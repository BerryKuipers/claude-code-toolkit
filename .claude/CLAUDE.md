# Claude Code Toolkit

Reusable Claude Code configuration synced to projects via `.claude-toolkit` submodule.

## Bug Fix Protocol

When fixing bugs, follow this order strictly:
1. **Read** the bug description carefully. Restate it in your own words.
2. **Investigate**: Read relevant code, trace data flow, identify root cause.
3. **State** your root cause hypothesis clearly. Wait for confirmation before coding.
4. **Implement** the minimal fix for the confirmed root cause only.
5. **Verify**: Run typecheck and test. Check the fix addresses the EXACT symptom.
6. Do NOT fix unrelated issues unless asked.
7. Do NOT apply fixes to both preview AND production unless explicitly requested.

## TypeScript Quality Gate

Always run `tsc --noEmit` or the project's typecheck command after making changes. Fix ALL TypeScript errors before reporting work as complete. Watch for: removed variables leaving dangling references, import path changes, and composite project references.

## Agent Verification Rules

When using parallel agents (Task tool), verify each agent's output actually resolves the issue before reporting success. Do not trust agent self-reports - check the actual code changes and run relevant checks. If an agent crashes, complete its work manually immediately.

## Agent Teams

This toolkit enables Agent Teams via `settings.json`. Use teams for complex multi-step work:

```
# Tell Claude to create a team with specialized roles:
"Create a team with a researcher, implementer, and reviewer to work on this feature"
```

Custom agents from `.claude/agents/` can be used as team members. Core agents available:
- **orchestrator** - Central routing and task coordination
- **conductor** - Full workflow orchestration (issue to PR)
- **implementation** - Feature implementation with architecture rules
- **build-error-resolver** - Fix build/type errors with minimal changes
- **code-reviewer** - PR and code quality review
- **architect** - Architecture review and validation
- **refactor** - Safe refactoring with test verification
- **researcher** - Research and grounding before implementation

Use `/retrieve` to pull additional specialized agents (database, security, e2e, browser, design, etc.) on demand.

## CSS/Layout Caution

Sticky positioning, z-index stacking, scroll behavior, and gradient overlays are known pain points. Always check surrounding positioning context before changing any position or z-index value. A fix to one (e.g., adding `relative`) can break another (e.g., a `fixed` element).

## Sync Tiers

The sync script (`sync-claude-toolkit.sh`) supports tiers:
- **core** (default): Essential agents, commands, skills, quality hooks
- **workflow**: + autonomous loops, gemini, mega-workflows
- **infra**: + infrastructure, DNS, VPS, deploy
- **debug**: + meta-validators, architecture tests
- **specialized**: + DB, security, e2e, browser, design
- **all**: Everything

Use `/retrieve <tier>` in-session to pull additional components.

## Rules

Architecture rules in `rules/` apply to all projects:
1. `00-global-architecture.mdc` - Layered architecture, dependency direction
2. `01-typescript-style.mdc` - TypeScript/JavaScript conventions
3. `02-backend-http-layer.mdc` - HTTP routes as thin adapters
4. `03-backend-persistence.mdc` - Repository patterns, data access
5. `04-frontend-react-architecture.mdc` - React component organization
