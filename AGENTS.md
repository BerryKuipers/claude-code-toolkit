# Claude Code Toolkit maintenance

This repository distributes agent configuration to other projects. Change the source here when fixing shared behavior, and verify generated/copied output before claiming consumers are updated.

- Root `AGENTS.md` describes toolkit maintenance. `.claude/CLAUDE.md` and `.claude/rules/` are copied into consuming projects; keep them project-neutral and preserve the consuming project's explicit decisions.
- `scripts/sync-claude-toolkit.sh` selects installation tiers. Core is the default; `/retrieve <tier>` adds capabilities on demand. Verify actual tool/plugin availability instead of requiring every session to preload the catalog.
- Native Claude rules are `.md` with `paths` frontmatter for scoped guidance. Keep generally applicable instructions short; task recipes and historical evidence belong in linked references. Do not assume Cursor `.mdc` metadata is a native Claude loader contract.
- A project that shares policy between clients can use `AGENTS.md` plus `CLAUDE.md` containing `@AGENTS.md`. Imports load the referenced text; they are not a token-saving boundary or an override mechanism. Do not create a dangling import in a new-project template.
- Preserve project customizations during sync and report migration conflicts. Do not edit installed user/global configuration as part of a repository-only change.
- For broker changes, read `submodules/mcp-broker/README.md` and run `npm test` there. Its stdio and HTTP entry points share discovery behavior. Keep tool definitions discoverable, fetch full schemas before invocation and preserve upstream results/errors.
- For sync changes, run `node --test scripts/tests/sync-rule-files.test.mjs` and shell syntax checks. For docs/rule changes, verify imports and that scoped globs match real paths. Use the affected project's additional gates when testing adoption.
- Record measured bytes separately from context tokens, cache usage, task success, latency and billing. Compare representative tasks before expanding runtime optimization; do not introduce a general sandbox or paid benchmark merely to reproduce a social-media claim.

See `docs/CONTEXT_POLICY.md` for loading semantics, migration behavior and the measurement procedure; `README.md` is the installation and capability catalog.
