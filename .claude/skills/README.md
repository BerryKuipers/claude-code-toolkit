# WescoBar Universe Storyteller - Agent Skills

**Agent Skills** are modular capabilities that extend Claude Code's functionality for the WescoBar project. Each Skill packages domain expertise, workflows, and best practices that Claude uses automatically when relevant.

---

## What are Agent Skills?

Skills are **filesystem-based directories** containing:
- `SKILL.md` - Main skill definition (required)
- `REFERENCE.md` - Supplemental reference material (optional)
- `examples.md` - Usage examples (optional)
- `scripts/` - Script resources (optional)
- `templates/` - Template files (optional)

### How Skills Work (Progressive Disclosure)

1. **Startup**: Claude loads `name` + `description` from all skills (lightweight)
2. **Task Analysis**: Claude checks if skill is relevant to current task
3. **Skill Loading**: If relevant, Claude reads full `SKILL.md` body
4. **On-Demand**: Claude reads additional files only when needed

This progressive loading keeps context efficient while providing deep expertise when needed.

---

## Skills vs Agents

### Agents (Your Existing Setup)
- **Purpose**: Workflow orchestration and delegation
- **Location**: `.claude/agents/`
- **Examples**: conductor, orchestrator, architect, implementation
- **Role**: Coordinate tasks and delegate to specialists

### Skills (New Addition)
- **Purpose**: Domain expertise and atomic operations
- **Location**: `.claude/skills/`
- **Examples**: run-tests, rate-limiting, quality-gate, create-pr
- **Role**: Provide how-to knowledge for specific tasks

**Think of it as:** Agents are conductors, Skills are sheet music for specific instruments.

---

## Skill Directory Structure

```
.claude/skills/
├── testing/                    # Test execution skills
│   ├── run-comprehensive-tests/
│   │   ├── SKILL.md
│   │   └── examples.md
│   └── validate-coverage/
│       └── SKILL.md
├── quality/                    # Quality assurance skills
│   ├── quality-gate/
│   │   ├── SKILL.md
│   │   └── examples.md
│   └── audit-code/
│       └── SKILL.md
├── git-workflows/              # Git and PR skills
│   ├── create-pull-request/
│   │   ├── SKILL.md
│   │   └── REFERENCE.md
│   └── commit-changes/
│       └── SKILL.md
├── gemini-api/                 # Gemini API best practices
│   ├── rate-limiting/
│   │   ├── SKILL.md
│   │   └── REFERENCE.md
│   ├── error-handling/
│   │   └── SKILL.md
│   └── image-generation/
│       └── SKILL.md
├── react-patterns/             # React/Frontend patterns
│   ├── component-structure/
│   │   └── SKILL.md
│   └── state-management/
│       └── SKILL.md
└── meta/                       # Meta skills (skills about skills)
    └── skill-creator/
        └── SKILL.md
```

---

## Available Skills

### Testing

**`run-comprehensive-tests`**
Execute comprehensive test suite with validation, coverage reporting, and failure analysis.

**When to use:** Quality Assurance phase, before PRs, after refactoring

**`validate-coverage`**
Deep dive into test coverage metrics and gap analysis.

**When to use:** Coverage analysis, identifying untested code

---

### Quality

**`quality-gate`**
Complete quality validation workflow (tests + audit + build + coverage + lint).

**When to use:** Conductor Phase 3, before PR creation, pre-merge validation

**`audit-code`**
Code quality audit with scoring and SOLID principles validation.

**When to use:** Quality assurance, refactoring validation

---

### Git Workflows

**`create-pull-request`**
Create GitHub PRs with proper issue linking and comprehensive descriptions.

**When to use:** Conductor Phase 4, after all quality gates pass

**`commit-changes`**
Single atomic commit with validation and proper formatting.

**When to use:** Before PR creation, after all changes complete

---

### Gemini API

**`gemini-api-rate-limiting`**
Best practices for handling Gemini API rate limits and preventing 429 errors.

**When to use:** Implementing Gemini API features, debugging rate limit errors

**`gemini-api-error-handling`**
Comprehensive error handling patterns for Gemini API.

**When to use:** Implementing error recovery, debugging API issues

**`gemini-api-image-generation`**
Complete image generation workflows with caching and queue management.

**When to use:** Implementing image generation features

---

### React Patterns

**`component-structure`**
Best practices for React component organization in WescoBar.

**When to use:** Creating new components, refactoring existing ones

**`state-management`**
React Context and state management patterns for WescoBar.

**When to use:** Implementing state logic, refactoring state

---

### Meta

**`skill-creator`**
Interactive wizard that helps create new Claude Skills with proper structure, YAML frontmatter, progressive disclosure, and validation.

**When to use:** Creating new skills from workflow patterns, standardizing skill format, bootstrapping skill structure

---

## How to Use Skills

### Method 1: Automatic (Recommended)

Claude Code automatically discovers and uses skills based on task context:

```
User: "Run all tests and validate coverage"
Claude: [Automatically uses `run-comprehensive-tests` skill]
```

### Method 2: Explicit Reference

Reference skills directly in agent workflows:

```markdown
**Phase 3, Step 1**: Run comprehensive tests

Use the `run-comprehensive-tests` skill:
- Execute full test suite
- Validate all tests pass
- Check coverage meets threshold
```

### Method 3: In Commands

Slash commands can reference skills:

```markdown
# In .claude/commands/test-all.md

Execute comprehensive testing using the `run-comprehensive-tests` skill.

Validate results and report status.
```

---

## Creating New Skills

### Basic Skill Structure

```markdown
---
name: skill-name
description: Clear description of what this skill does (max 1024 chars)
---

# Skill Name

## Purpose
What this skill does

## When to Use
Triggers that indicate relevance

## Instructions
Step-by-step how-to

## Examples
Usage examples

## Related Skills
Links to related skills
```

### Best Practices

1. **Keep SKILL.md under 500 lines** - Use additional files for large content
2. **Clear, searchable descriptions** - Help Claude discover when relevant
3. **Concrete examples** - Show real WescoBar use cases
4. **Cross-reference** - Link to related skills and agents
5. **Version control friendly** - Use git for skill updates

### Progressive Disclosure Tips

**Level 1: YAML Frontmatter** (always loaded)
- Concise name (max 64 chars)
- Clear description (max 1024 chars)

**Level 2: SKILL.md Body** (loaded when skill triggered)
- Instructions and workflows
- Common patterns and examples

**Level 3: Additional Files** (loaded on-demand)
- `REFERENCE.md` - Deep reference material
- `examples.md` - Extensive examples
- `scripts/` - Script resources

---

## Integration with Existing Setup

### With Conductor Agent

The Conductor agent references skills for atomic operations:

```markdown
**Phase 3: Quality Assurance**

1. Use `quality-gate` skill for complete validation
2. If quality gate fails, route to appropriate agent
3. Re-run quality gate after fixes
```

### With Orchestrator Agent

The Orchestrator can route simple tasks to skills:

```markdown
User: "run tests"
Orchestrator: Routes to `run-comprehensive-tests` skill (faster than agent delegation)
```

### With Custom Commands

Commands can invoke skills:

```markdown
# .claude/commands/test-all.md

Use the `run-comprehensive-tests` skill to execute and validate tests.
```

---

## Activation

### Skills are Active After Restart

Changes to skills take effect when you:
1. Add new skills to `.claude/skills/`
2. **Restart Claude Code**
3. Skills are auto-discovered and loaded

### No Manual Installation

Skills in `.claude/skills/` are automatically discovered. No need to run `/plugin install`.

---

## Skill Scoping

### Project Skills (Current Setup)

**Location**: `.claude/skills/` (this directory)
**Scope**: Available only in WescoBar-Universe-Storyteller project
**Team Sharing**: Committed to git, shared with all team members

### Personal Skills (Optional)

**Location**: `~/.claude/skills/`
**Scope**: Available in all your Claude Code projects
**Team Sharing**: Not shared (personal only)

**Example personal skills:**
- Your personal coding preferences
- Private templates
- Experimental workflows

---

## Maintenance

### Updating Skills

1. Edit `SKILL.md` or add new files
2. Commit changes to git
3. Restart Claude Code
4. Updated skills are now active

### Version Control

Skills are version controlled with the project:
- Track changes in git
- Review skill updates in PRs
- Share improvements with team

### Cleaning Up

Remove outdated skills:
```bash
rm -rf .claude/skills/old-skill-name/
```

Restart Claude Code to unload removed skills.

---

## Examples and Templates

See individual skill directories for:
- `examples.md` - Real-world usage examples
- `REFERENCE.md` - Deep reference material
- `templates/` - Reusable templates

---

## Troubleshooting

### Skill not being used?

1. Check skill description is clear and searchable
2. Verify `name` and `description` in YAML frontmatter
3. Restart Claude Code to reload skills
4. Make task context explicit ("Use the X skill to...")

### Skill loading too much content?

1. Move detailed content to `REFERENCE.md`
2. Keep SKILL.md focused on common cases
3. Reference additional files only when needed

### Need help creating skills?

Use the `agent-creator` agent to generate new skills with proper structure.

---

## References

- **Official Docs**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- **Agent Delegation Pattern**: `.claude/commands/docs/agent-delegation-pattern.md`
- **CLAUDE.md**: Project rules and patterns
- **AGENTS.md**: Agent system documentation

---

**Created**: 2025-10-21
**Purpose**: Complement agents with domain expertise and reusable capabilities
**Integration**: Works seamlessly with existing conductor/orchestrator agents
**Activation**: Restart Claude Code after adding/modifying skills
