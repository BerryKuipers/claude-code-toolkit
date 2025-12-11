# Claude Code Toolkit - Generic Architecture Rules

This repository contains **reusable, agnostic architectural rules** for Claude Code and other AI coding assistants.

## Purpose

The `.claude/rules/` folder provides generic coding guidelines designed for:
- Node.js/TypeScript backend services
- React/TypeScript frontend applications
- Full-stack projects using layered architecture

These rules are **framework-agnostic** and can be used across multiple projects via git submodules or direct inclusion.

## Rule Files

### Core Architecture
- **[00-global-architecture.mdc](.claude/rules/00-global-architecture.mdc)**: Layered architecture principles, dependency direction, separation of concerns
- **[01-typescript-style.mdc](.claude/rules/01-typescript-style.mdc)**: TypeScript/JavaScript coding conventions and style guidelines

### Backend Rules
- **[02-backend-http-layer.mdc](.claude/rules/02-backend-http-layer.mdc)**: HTTP routes/controllers must be thin adapters; no direct DB access
- **[03-backend-persistence.mdc](.claude/rules/03-backend-persistence.mdc)**: Repository patterns, data access boundaries, ORM encapsulation

### Frontend Rules
- **[04-frontend-react-architecture.mdc](.claude/rules/04-frontend-react-architecture.mdc)**: React component organization, data fetching, state management

## Using This Toolkit in Your Projects

### Option 1: As a Git Submodule (Recommended)

```bash
# Add toolkit as submodule
git submodule add https://github.com/YourOrg/claude-code-toolkit .claude-toolkit

# Symlink or reference the rules
ln -s .claude-toolkit/.claude .claude
```

### Option 2: Direct Copy

```bash
# Copy the .claude folder to your project
cp -r /path/to/claude-code-toolkit/.claude ./
```

### Option 3: Selective Rules

Copy only the rules you need:
```bash
mkdir -p .claude/rules
cp claude-code-toolkit/.claude/rules/00-global-architecture.mdc .claude/rules/
cp claude-code-toolkit/.claude/rules/01-typescript-style.mdc .claude/rules/
```

## Overriding or Extending Rules

Projects can extend these toolkit rules with project-specific guidance:

### For Claude Code

Create a `CLAUDE.md` in your project root:
```markdown
# Project-Specific Rules

## This Project Uses

This is a multi-tenant SaaS billing platform using:
- Backend: NestJS + Prisma + PostgreSQL
- Frontend: Next.js 14 (App Router) + React Query
- Deployment: Docker + Kubernetes

## Toolkit Rules Apply

All rules from `.claude-toolkit/.claude/rules/` apply globally.

## Project-Specific Overrides

### Database
- ALWAYS use `prisma.tenant.findMany()` with tenantId filter
- NEVER skip tenant isolation checks

### Authentication
- All routes require JWT middleware except /health
- Admin routes require role check: `requireRole('admin')`

### Critical Paths
- `/src/billing/**` - Payment processing (no modifications without review)
- `/src/tenant/**` - Tenant isolation (security-critical)
```

### For Cursor

Create `.cursor/rules/99-project-overrides.mdc`:
```yaml
---
description: Project-specific overrides for this application
globs:
  - 'src/**/*'
alwaysApply: true
---

# Project Overrides

## Specific to This Project
...
```

## Rule Composition

Claude Code discovers and merges CLAUDE.md files in this order:
1. `~/.claude/CLAUDE.md` (user-level, if exists)
2. `/project/.claude-toolkit/CLAUDE.md` (this toolkit)
3. `/project/CLAUDE.md` (project-specific, most authoritative)
4. `/project/src/module/CLAUDE.md` (module-specific)

Later files override or extend earlier ones.

## Guidelines for Maintaining This Toolkit

### Keep Rules Generic
- ❌ Don't reference specific project names or paths
- ❌ Don't assume specific frameworks (Express, NestJS, etc.)
- ✅ Use generic folder patterns: `routes/`, `controllers/`, `repositories/`
- ✅ Provide examples for multiple frameworks where applicable

### Keep Rules Concise
- Each rule file should be **< 100 lines** where possible
- Focus on principles, not exhaustive details
- Rules are loaded in every Claude Code interaction - token efficiency matters

### Structure Rules by Concern
- One rule file per architectural layer or concern
- Use numbered prefixes (00-, 01-) to indicate loading order
- Use descriptive names: `backend-http-layer`, not `http-stuff`

## Cross-Tool Compatibility

These `.mdc` files work with:
- **Claude Code**: Reads markdown content (ignores YAML frontmatter)
- **Cursor**: Reads YAML frontmatter + markdown content
- **Other AI assistants**: Read as standard markdown

This dual format ensures maximum compatibility without duplication.

## Contributing

When adding new rules to this toolkit:
1. Ensure they're generic and reusable across projects
2. Provide examples for multiple frameworks (Express, NestJS, Next.js, etc.)
3. Keep files concise (< 100 lines)
4. Test with both Claude Code and Cursor
5. Document with clear examples of good/bad patterns

## Further Reading

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
- [CLAUDE.md Best Practices](https://github.com/steipete/agent-rules)
- [Toolkit Modernization Guide](./docs/TOOLKIT_MODERNIZATION_2025.md)
