# Retrieve Extended Toolkit Components

Pull optional commands, agents, and skills from `.claude-toolkit` into the current project's `.claude/` directory on demand.

## Usage

```
/retrieve                    # List available tiers and what they contain
/retrieve workflow           # Pull workflow tier (loops, mega-workflows, gemini)
/retrieve infra              # Pull infrastructure tier (DNS, VPS, deploy)
/retrieve debug              # Pull debug/meta tier (validators, architecture tests)
/retrieve specialized        # Pull specialized tier (DB, security, e2e, browser, design)
/retrieve all                # Pull everything
/retrieve agent <name>       # Pull a specific agent (e.g. "database")
/retrieve command <name>     # Pull a specific command (e.g. "fix-e2e-tests")
/retrieve skill <path>       # Pull a specific skill dir (e.g. "memory")
```

## Instructions

You are a toolkit retrieval assistant. The user wants to pull extended components from the `.claude-toolkit` submodule into their project's `.claude/` directory.

### Parse the argument: $ARGUMENTS

If no argument or "list":
- Show the available tiers with descriptions:
  - **core** (already synced): orchestrator, conductor, implementation, build-error-resolver, code-reviewer, architect, refactor, researcher + essential commands/skills
  - **workflow**: loop, ralph-loop, reflect, mega-workflow, gemini-delegation, parallel-worktree, harness
  - **infra**: dns, vps, verify-deploy, capture-pages, infrastructure agent, page-capture agent
  - **debug**: system-discovery, system-review, test-agent-system, architecture-tester, command-analyzer, agent-creator, system-validator
  - **specialized**: fix-e2e-tests, pick-next-pr, design-review, test-ui, database, security-pentest, e2e-test-maintainer, browser-testing, qa-triage + memory/styling/github skills
  - **all**: everything

If a tier name (workflow/infra/debug/specialized/all):
- Run the sync script with the appropriate tier flag:
  ```bash
  bash .claude-toolkit/scripts/sync-claude-toolkit.sh --tier <tier>
  ```
- If `.claude-toolkit` doesn't exist, try `./scripts/sync-claude-toolkit.sh --tier <tier>`
- Report what was synced

If "agent <name>":
- Copy `.claude-toolkit/.claude/agents/<name>.md` to `.claude/agents/<name>.md`
- Report success/failure

If "command <name>":
- Copy `.claude-toolkit/.claude/commands/<name>.md` to `.claude/commands/<name>.md`
- Report success/failure

If "skill <path>":
- Copy `.claude-toolkit/.claude/skills/<path>/` to `.claude/skills/<path>/`
- Report success/failure

### Important
- Always check that `.claude-toolkit` exists first. If not, inform the user to run `git submodule update --init`
- Preserve any project-specific files already in `.claude/` - never delete existing files
- After retrieval, list exactly what was added so the user knows what's now available
