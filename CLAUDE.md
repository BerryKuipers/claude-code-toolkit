# Claude Code Toolkit

Reusable, agnostic architectural rules and agentic workflow tooling for Claude Code.

## Quick Start

```bash
# Add as submodule
git submodule add https://github.com/BerryKuipers/claude-code-toolkit .claude-toolkit

# Sync core components (default: lightweight, essential only)
bash .claude-toolkit/scripts/sync-claude-toolkit.sh

# Sync with additional tier
bash .claude-toolkit/scripts/sync-claude-toolkit.sh --tier workflow

# Sync everything (legacy behavior)
bash .claude-toolkit/scripts/sync-claude-toolkit.sh --all

# List available tiers
bash .claude-toolkit/scripts/sync-claude-toolkit.sh --list
```

## Sync Tiers

The sync script only copies **core** components by default, keeping consuming projects lean:

| Tier | What's included |
|------|----------------|
| **core** (default) | 8 agents, 21 commands, 11 skill dirs, quality hooks, rules |
| **workflow** | + loops, mega-workflows, gemini delegation, harness |
| **infra** | + DNS, VPS, deploy, capture-pages |
| **debug** | + meta-validators, architecture tests, debug tools |
| **specialized** | + DB, security, e2e, browser, design, QA agents |
| **all** | Everything in the toolkit |

Use `/retrieve <tier>` in-session to pull additional components on demand.

## Core Commands

| Command | Purpose |
|---------|---------|
| `/conductor` | Full workflow orchestration (issue to PR) |
| `/audit` | Code quality audit |
| `/architect` | Architecture review |
| `/refactor` | Safe refactoring |
| `/review-pr` | PR code review |
| `/deploy` | Deployment |
| `/test-all` | Comprehensive testing |
| `/help` | Command documentation |
| `/retrieve` | Pull extended toolkit components on demand |

### Wrapper Commands (bk-*)

```bash
/bk-plan "implement feature X"    # Planning with verification gates
/bk-review --staged               # Code review with output contract
/bk-implement "task description"  # Implementation with pre/post gates
/bk-architect --scope=backend     # Architecture review
/bk-security --create-issues      # Security audit
/bk-fix --type=build              # Build error resolution
/bk-doc --scope=api               # Documentation updates
```

## Agent Teams

Agent Teams are enabled by default. Use teams for complex multi-step work:

```
"Create a team with a researcher, implementer, and reviewer"
```

Core agents (always synced):
- **orchestrator**, **conductor**, **implementation**, **build-error-resolver**
- **code-reviewer**, **architect**, **refactor**, **researcher**

Extended agents (via `/retrieve specialized`):
- **database**, **security-pentest**, **e2e-test-maintainer**, **browser-testing**
- **design**, **qa-triage**, **infrastructure**, **page-capture**

## Architecture Rules

Rules in `.claude/rules/` apply to all consuming projects:
- `00-global-architecture.mdc` - Layered architecture, dependency direction
- `01-typescript-style.mdc` - TypeScript/JavaScript conventions
- `02-backend-http-layer.mdc` - HTTP routes as thin adapters
- `03-backend-persistence.mdc` - Repository patterns, data access
- `04-frontend-react-architecture.mdc` - React component organization

## Project Overlays

Project-specific configs in `.claude/overlays/<project>/`:
```
.claude/overlays/
├── wescobar/config.yml
├── cophusher/config.yml
├── flowerguy/config.yml
├── tuenscout/config.yml
└── tribevibe/config.yml
```

## Overriding Rules

Create a `CLAUDE.md` in your project root to override or extend toolkit rules. Claude Code merges in order:
1. `~/.claude/CLAUDE.md` (user-level)
2. `.claude-toolkit/CLAUDE.md` (this toolkit)
3. `CLAUDE.md` (project root - most authoritative)
4. `src/module/CLAUDE.md` (module-specific)

## Disk hygiene (hard rule - D: has filled up repeatedly)

- Worktrees live ONLY at `<repo>/.claude/worktrees/<branch-slug>`. Never a sibling dir (`../Repo-fix`, `Repo.worktrees`) and never shared dirs like `D:\berry\Projects\_worktrees`, `_scratch`, `_tmp`, `_codex_worktrees`.
- Remove the worktree in the same turn its branch lands or is abandoned. Check `git status --porcelain` and unpushed commits first; salvage real work, then plain `git worktree remove` (no `--force`).
- Scratch/temp output goes in `$env:TEMP` or `<repo>/.claude/tmp` (gitignored), never loose in `D:\berry\Projects`. Delete it before you finish.
- Never copy or clone a repo per task. Junction `node_modules` to the main checkout; never run `npm ci` inside a worktree.
- Renders, captures, models, datasets and VM images go in one named folder and are deleted at the end unless the user asked to keep them.
- At session start and before handoff run `git worktree list`, stop processes you started, and report D: free space. Below 20 GB free: stop and clean up first.

