# Claude Code Toolkit - Internal Documentation

This toolkit provides **reusable Claude Code configuration** for multiple projects.

## Structure

```
.claude/
├── CLAUDE.md              # This file - toolkit internal docs
├── rules/                 # Generic architectural rules
│   ├── 00-global-architecture.mdc
│   ├── 01-typescript-style.mdc
│   ├── 02-backend-http-layer.mdc
│   ├── 03-backend-persistence.mdc
│   └── 04-frontend-react-architecture.mdc
├── agents/                # Specialized agent definitions
├── commands/              # Slash commands
├── skills/                # Domain-specific skills
├── hooks/                 # Pre/post tool execution hooks
├── config.yml             # Central configuration
└── settings.json          # SessionStart hooks and environment
```

## Rules Directory

The `rules/` folder contains **generic, reusable architectural guidelines** designed for:
- TypeScript/JavaScript projects (Node.js backends, React frontends)
- Layered/clean architecture patterns
- Framework-agnostic principles

### Rule File Format

Files use `.mdc` (Markdown with Configuration) format:
```yaml
---
description: Short description of rule purpose
globs:
  - '**/*.ts'
  - '!**/node_modules/**'
alwaysApply: true
targets: ['*']
---

# Rule Content in Markdown
```

**Note:** Claude Code reads only the markdown content; Cursor reads both YAML and markdown.

### Current Rules

1. **00-global-architecture.mdc** - Layered architecture, dependency direction, separation of concerns
2. **01-typescript-style.mdc** - TypeScript/JavaScript style conventions
3. **02-backend-http-layer.mdc** - HTTP routes/controllers as thin adapters, no direct DB access
4. **03-backend-persistence.mdc** - Repository patterns, data access boundaries
5. **04-frontend-react-architecture.mdc** - React component organization, data fetching, state management

## Using This Toolkit in Projects

### Integration Approaches

**Git Submodule (recommended):**
```bash
cd your-project
git submodule add https://github.com/YourOrg/claude-code-toolkit .claude-toolkit
ln -s .claude-toolkit/.claude .claude
```

**Direct Copy:**
```bash
cp -r /path/to/claude-code-toolkit/.claude ./your-project/
```

**Selective Rules:**
```bash
mkdir -p your-project/.claude/rules
cp claude-code-toolkit/.claude/rules/00-*.mdc your-project/.claude/rules/
```

### Rule Composition Strategy

Projects using this toolkit can layer rules:

```
Project Structure:
├── .claude-toolkit/          # This toolkit (submodule)
│   ├── CLAUDE.md            # Toolkit-level rules
│   └── .claude/
│       └── rules/           # Generic rules
│
├── CLAUDE.md                # Project-specific rules (override toolkit)
├── .claude/
│   └── rules/               # Optional: project-specific .mdc files
│
└── src/
    └── billing/
        └── CLAUDE.md        # Module-specific rules
```

**Discovery order** (Claude Code merges in this sequence):
1. User-level: `~/.claude/CLAUDE.md`
2. Toolkit: `.claude-toolkit/CLAUDE.md`
3. Project: `/CLAUDE.md` ← **Most authoritative**
4. Module: `/src/billing/CLAUDE.md`

Projects can **override** toolkit rules by specifying conflicting guidance in their own `CLAUDE.md`.

## Maintaining Generic Rules

### Guidelines

**Keep rules agnostic:**
- ❌ Don't hardcode project names, specific paths, or business domains
- ✅ Use generic patterns: `routes/`, `controllers/`, `repositories/`
- ✅ Provide examples for multiple frameworks (Express, NestJS, Next.js)

**Keep rules concise:**
- Target < 100 lines per rule file
- Rules are loaded in every interaction - token efficiency matters
- Focus on principles, not exhaustive documentation

**Structure by concern:**
- One rule file per architectural layer or topic
- Number prefixes for loading order (00-, 01-)
- Descriptive names: `backend-http-layer.mdc`, not `backend.mdc`

### Adding New Rules

1. Create `.claude/rules/XX-descriptive-name.mdc`
2. Add YAML frontmatter with `description`, `globs`, `alwaysApply`
3. Write concise markdown content with examples
4. Test with both Claude Code and Cursor
5. Update `CLAUDE.md` in project root to reference new rule

### Editing Existing Rules

When updating rules:
- Preserve generic, reusable nature
- Update examples to cover more frameworks if needed
- Keep file size < 100 lines
- Test changes don't break project-specific overrides

## Cross-Tool Compatibility

These rules work with:
- **Claude Code**: Reads markdown, ignores YAML frontmatter
- **Cursor**: Reads both YAML frontmatter and markdown
- **GitHub Copilot**: Treats as standard markdown documentation
- **Other AI assistants**: Standard markdown

This dual format ensures maximum compatibility without file duplication.

## Integration with Existing Toolkit Features

This rules system complements existing toolkit features:

- **Agents** (`agents/`): Specialized agents can reference rules when making architectural decisions
- **Commands** (`commands/`): Slash commands can enforce rules (e.g., `/audit` checks compliance)
- **Hooks** (`hooks/`): Pre-tool-use hooks can validate against architectural rules
- **Config** (`config.yml`): Central config can enable/disable rule enforcement

Example integration:
```yaml
# config.yml
validation:
  architecture_rules:
    enabled: true
    enforce_on_commit: true
    rule_files:
      - .claude/rules/02-backend-http-layer.mdc
      - .claude/rules/03-backend-persistence.mdc
```

## FAQ

### Why .mdc instead of .md?
The `.mdc` extension signals "Markdown with Configuration" and indicates YAML frontmatter presence. This helps tools distinguish between plain documentation and rule files.

### Do projects need all rule files?
No. Projects can selectively copy only the rules relevant to their stack (e.g., only frontend rules for a React-only project).

### Can projects modify toolkit rules?
Projects should NOT modify toolkit rules directly. Instead, create project-specific CLAUDE.md files that override or extend toolkit guidance.

### How do I test rule changes?
1. Make changes to `.mdc` file
2. In a test project using the toolkit, ask Claude to create code that would violate the rule
3. Verify Claude follows the updated guidance
4. Test with both Claude Code and Cursor if possible

## See Also

- [Root CLAUDE.md](../CLAUDE.md) - User-facing documentation
- [Toolkit Modernization Guide](../docs/TOOLKIT_MODERNIZATION_2025.md)
- [Code Quality Enforcement](../docs/CODE_QUALITY_ENFORCEMENT.md)
