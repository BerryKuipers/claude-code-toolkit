# TribeVibe Project Overlay

This overlay configures the toolkit for the TribeVibe project (social/community platform).

## Prefix

All TribeVibe-specific commands use the `tv-` prefix.

## Configuration

See `config.yml` for:
- Allowed baseline agents
- Enabled MCP servers
- Project-specific thresholds
- Custom commands

## Project Context

TribeVibe is a social/community platform with:
- Next.js frontend
- Node.js/Express backend
- PostgreSQL database
- VPS infrastructure access via MCP

## Usage

When working in TribeVibe:
1. Baseline commands (from everything-claude-code) work as normal
2. Toolkit wrappers (`/bk-*`) add verification gates
3. Project commands (`/tv-*`) are TribeVibe-specific
