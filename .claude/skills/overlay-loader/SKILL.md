# Overlay Loader Skill

Loads project-specific overlay configuration from `.claude/overlays/<project>/config.yml`.

## When to Use

- At session start (via session-start hook)
- When switching project context
- When initializing wrapper commands

## Execution

### Step 1: Detect Project

Determine project name from:
1. `$CLAUDE_PROJECT` environment variable
2. Git remote URL parsing (e.g., `wescobar` from `github.com/.../Wescobar`)
3. Directory name as fallback

### Step 2: Load Overlay Config

```bash
PROJECT_NAME=$(basename "$(git remote get-url origin 2>/dev/null | sed 's/\.git$//')" | tr '[:upper:]' '[:lower:]')
OVERLAY_PATH=".claude/overlays/${PROJECT_NAME}/config.yml"

if [ -f "$OVERLAY_PATH" ]; then
  echo "Loading overlay: $PROJECT_NAME"
  cat "$OVERLAY_PATH"
else
  echo "No overlay found for: $PROJECT_NAME"
fi
```

### Step 3: Apply Configuration

From the loaded config, extract and apply:

- **allowed_agents**: List of upstream agents permitted for this project
- **disabled_agents**: Agents that should warn if invoked
- **enabled_mcp_servers**: MCP servers to activate
- **thresholds**: Quality gate thresholds (coverage, complexity)
- **verification_gates**: Pre/post implementation checks

### Output

Return a summary for the session context:

```
Project: wescobar
Prefix: wsc
Allowed agents: planner, architect, code-reviewer, security-reviewer, e2e-runner, tdd-guide
MCP servers: supabase, vercel
Test coverage min: 70%
```

## Integration

This skill is called by:
- `session-start.sh` hook (optional)
- `bk-*` wrapper commands (to validate agent usage)
- Orchestrator when delegating to agents
