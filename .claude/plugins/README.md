# TribeVibe Claude Code Plugins

This directory contains modular Claude Code plugins that organize **specialized agents** into logical groups for TribeVibe development.

## Architecture

**Plugin System Purpose**: Organize agents into toggleable, composable modules

**Structure**:
```
.claude/
├── plugins/           ← Organized agent groups (THIS)
│   ├── tribevibe-core/
│   │   ├── .claude-plugin/plugin.json
│   │   └── agents/*.md (architect, implementation, database, infrastructure, debugger)
│   ├── tribevibe-workflow/
│   │   └── agents/*.md (orchestrator, conductor, audit, refactor, researcher)
│   └── ...
├── commands/          ← Slash commands that invoke plugin agents
│   └── *.md (test-ui, architect, debug, etc.)
└── agents/            ← Original agent files (preserved)
```

**How It Works**:
1. **Plugins organize agents** into logical groups (core, workflow, testing, design, meta)
2. **Commands invoke agents** via Task tool (e.g., `/test-ui` calls `ui-frontend-agent`)
3. **Toggle plugins** to enable/disable agent groups based on current work

## Available Plugins

### 🔧 tribevibe-core (Enabled by default)
**Purpose**: Essential TribeVibe development agents

**Agents**:
- `architect` - Architecture review and VSA validation
- `implementation` - Feature implementation
- `database` - Database operations and migrations
- `infrastructure` - VPS and Docker management
- `debugger` - Bug investigation and debugging

**Triggers**: architecture, VSA, SOLID, database, migration, debug, bug, error, implement

**When to enable**: Always (core functionality)

---

### 🔄 tribevibe-workflow (Enabled by default)
**Purpose**: Complete workflow orchestration and automation

**Agents**:
- `orchestrator` - Central task routing hub
- `conductor` - Full-cycle feature development (issue → PR → merge)
- `audit` - Comprehensive quality audits
- `refactor` - Safe refactoring with quality gates
- `researcher` - Research and documentation

**Triggers**: orchestrate, route, workflow, full cycle, end-to-end, audit, refactor, research

**When to enable**: Always (workflow coordination)

---

### 🧪 tribevibe-testing (Disabled by default)
**Purpose**: Comprehensive testing and QA suite

**Agents**:
- `ui-frontend-agent` - Browser automation and UI testing
- `system-validator` - System validation

**Triggers**: UI test, browser test, E2E test, validate system, health check

**MCP Requirements**: `chrome-devtools` (for browser automation)

**When to enable**: During QA phases, testing cycles, or UI work

---

### 🎨 tribevibe-design (Disabled by default)
**Purpose**: UI/UX design review and accessibility

**Agents**:
- `design` - Design review and accessibility audits

**Triggers**: design review, UI review, UX, accessibility, component design

**MCP Requirements**: `chrome-devtools` (for visual inspection)

**When to enable**: Frontend/design work, accessibility audits

---

### 🛠️ tribevibe-meta (Disabled by default)
**Purpose**: Meta-development tools for creating agents/commands

**Agents**:
- `agent-creator` - Create new agents
- `meta-agent-example` - Example meta-agent patterns
- `test-slash-command` - Test command system

**Triggers**: create agent, new agent, delegation pattern, test command

**When to enable**: Developing new agents or commands

---

## Usage

### Enable/Disable Plugins

```bash
# Enable a plugin
/plugin enable tribevibe-testing

# Disable a plugin
/plugin disable tribevibe-testing

# List all plugins
/plugin list

# Show plugin status
/plugin status
```

### How Commands Invoke Plugin Agents

Commands in `.claude/commands/` can invoke plugin agents via the Task tool:

**Example**: `/test-ui` command
```markdown
# In .claude/commands/test-ui.md
Execute UI testing using the ui-frontend-agent from tribevibe-testing plugin
```

**Behind the scenes**:
```typescript
Task({
  subagent_type: "ui-frontend-agent",  // From tribevibe-testing plugin
  description: "Test UI functionality",
  prompt: "Run comprehensive UI tests..."
})
```

### Plugin Composition

Plugins are designed to work together:

| Work Type | Enabled Plugins |
|-----------|----------------|
| Bug fixing | `core`, `workflow` |
| New feature | `core`, `workflow`, `testing` |
| UI/UX work | `core`, `design`, `testing` |
| Architecture review | `core`, `workflow` |
| Agent development | `meta` |
| Pre-deployment QA | `core`, `workflow`, `testing` |

## Benefits

### Before Plugins (Flat Structure)
```
.claude/agents/ → 16 agents always loaded
```
**Issues**: All agents loaded at once, cluttered context, slower responses

### After Plugins (Modular Structure)
```
plugins/
├── tribevibe-core/ (5 agents) [always on]
├── tribevibe-workflow/ (5 agents) [always on]
├── tribevibe-testing/ (2 agents) [toggleable]
├── tribevibe-design/ (1 agent) [toggleable]
└── tribevibe-meta/ (3 agents) [toggleable]
```
**Benefits**:
- ✅ Load only needed agents
- ✅ Cleaner AI context
- ✅ Faster responses
- ✅ Easier to maintain
- ✅ Shareable with team

## Plugin Manifest Spec

Each plugin includes a `plugin.json` manifest:

```json
{
  "name": "tribevibe-core",
  "version": "1.0.0",
  "description": "Core development agents",
  "author": { "name": "Berry", "email": "berry@tribevibe.io" },
  "capabilities": ["architecture-review", "debugging"],
  "agents": [
    {
      "name": "architect",
      "description": "Architecture review agent",
      "triggers": ["architecture", "VSA", "SOLID"]
    }
  ],
  "enabledByDefault": true,
  "scope": "project",
  "mcpServers": { ... }  // Optional
}
```

**Key Fields**:
- `agents[].triggers` - Keywords that activate the agent
- `enabledByDefault` - Auto-enable on startup
- `mcpServers` - Required MCP integrations (e.g., chrome-devtools)

## Validation

All plugins follow the official Claude Code Plugin System specification:
- ✅ Required `.claude-plugin/plugin.json` manifest
- ✅ Standard directory structure (`agents/` only)
- ✅ Proper YAML frontmatter in agent files
- ✅ Agent trigger keywords in manifest
- ✅ MCP server definitions where applicable
- ✅ Version control and metadata

## Distribution

These plugins can be shared via:
1. **Project Repository**: Committed to TribeVibe repo (current setup)
2. **GitHub Marketplace**: Published as public/private marketplace
3. **Direct Copy**: Share plugin folders with team members

## References

- **Plugin System Documentation**: `docs/researched/Claude Code Plugin System_ Architecture, Usage, and Integration.pdf`
- **Original Agent Files**: `.claude/agents/` (preserved for reference)
- **Commands**: `.claude/commands/` (invoke plugin agents)

---

**Created**: 2025-10-12
**Author**: Berry
**Purpose**: Modular, toggleable agent organization for TribeVibe development
**Note**: Commands remain in `.claude/commands/` and invoke these plugin agents via Task tool
