# WescoBar Project Overlay

This overlay configures the toolkit for the WescoBar project.

## Prefix

All WescoBar-specific commands use the `wsc-` prefix.

## Configuration

See `config.yml` for:
- Allowed baseline agents
- Enabled MCP servers
- Project-specific thresholds
- Custom commands

## Usage

When working in the WescoBar project:
1. Baseline commands (from everything-claude-code) work as normal
2. Toolkit wrappers (`/bk-*`) add verification gates
3. Project commands (`/wsc-*`) are WescoBar-specific

## Overlay Priority

```
WescoBar CLAUDE.md > Toolkit rules > Upstream plugin
```
