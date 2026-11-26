# Agent context and tool discovery

Verified against Anthropic documentation on 26 November 2026. Keep repository intent and actual client behavior separate.

## Loading policy

Use a small shared project policy for the facts, decisions and failure modes that an agent needs across tasks. Keep valid build commands, subtle environment requirements and destructive-data boundaries even when they cost tokens. Link to detailed procedures with a clear trigger. Do not replace useful rules with an arbitrary word target or assume every discoverable fact is cheap to rediscover.

Claude's [memory documentation](https://code.claude.com/docs/en/memory) describes native `AGENTS.md` support with version/settings/precedence exceptions, `CLAUDE.md` imports and `.claude/rules/*.md` with `paths`. A real `@AGENTS.md` import is different from a prose request to read it. Imported files still contribute their contents. Files combine as instructions; filenames do not enforce a conflict-resolution hierarchy. Check the installed client before assuming loader behavior.

The toolkit now ships small native Markdown rules. Architecture, TypeScript, HTTP, persistence and React guidance have path scopes; quality and delivery invariants remain generally applicable. Old `.mdc` versions are retained under `docs/archive/2026-11-26-rules/` as historical material, not an active policy source. They do not establish native Claude loading and their older approval/model/architecture wording is superseded.

## Sync migration

`sync-claude-toolkit.sh` calls `sync-rule-files.sh`. It installs current native rules and records their hashes in `.claude/.toolkit-rule-hashes.sha256`. Subsequent runs update unchanged toolkit-owned copies; custom edits and pre-existing filename conflicts stay intact with a visible message. It moves only known unchanged legacy `.mdc` files to `.claude/reference/retired-toolkit-rules/`, outside the native rule directory. The checked-in manifest recognizes both LF and CRLF copies. Modified legacy files, symlinks and conflicting archive files remain intact. Running the migration again is idempotent. SHA-256 support is required to identify owned content safely.

The full sync no longer adds global Git `safe.directory` entries. If a checkout already exists and its submodule update fails, the fallback stops with its path instead of deleting that checkout and cloning over it. Inspect its local changes and update/recover it before retrying.

The root new-project template remains standalone. If a project adopts shared `AGENTS.md`, move its actual policy there and make its root `CLAUDE.md` a small import; do not copy toolkit-maintainer instructions into the application.

## MCP behavior

Prefer native tool discovery when the actual client and provider support it; adding another broker is not automatically useful. The existing toolkit broker remains an optional custom runtime. Its `broker.search` discovers configured servers even with a cold cache, reads paginated tool lists and returns summaries. `broker.describe` loads the chosen full definition, including its input/output schemas and annotations. `broker.invoke` keeps the original upstream result and error flag. Partial discovery failures are visible rather than presented as a complete empty catalog.

Use upstream filters, fields, pagination and bounded existing scripts for large read operations. Return the data required for the task plus totals, errors and truncation indicators. Do not silently discard rows, change permissions or claim that masking happens merely because a prompt says so. Retain complete diagnostic output in an appropriate local artifact when needed; give the model a useful bounded summary.

Anthropic's [MCP code-execution article](https://www.anthropic.com/engineering/code-execution-with-mcp) shows a particular large-tool/data workflow. Its 150,000-to-2,000-token example is not a general Claude subscription saving. A custom execution sandbox, native tool search and API [programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) are different integration surfaces. Their availability, isolation and supported tools must be checked separately.

## Verify before expanding

1. Inspect the actual installed version, active imports/rules, enabled MCP servers and provider route. In Claude Code inspect `/context all`, then read a matching source file and inspect the loaded rule set again.
2. Repeat representative tasks: one small code fix, one docs change and one larger read/search. Keep the repository revision, input task, model/effort and tool configuration comparable.
3. Record completion/quality, tool calls, returned bytes, actual input/output/cache tokens where reported, elapsed time and any pricing basis. Include corrections and failed attempts in the comparison.
4. Expand only when the task result stays correct and the measured overhead improves. Byte reductions alone do not prove token, rate-limit or cash savings; prompt caching can change the accounting.

The broker regression suite uses synthetic local MCP servers without account access. It proves cold discovery, pagination, scoped search, full schema retrieval, output-schema enforcement across pages and lossless invoke behavior through stdio and HTTP. The sync suite covers custom rules, migration, symlinks, failed-update preservation and a real linked Git worktree. One path-filtered Linux PR job runs these tests with a five-minute cap and no platform matrix, paid model calls or extra push-to-main run. These checks do not measure a user's native loader, subscription quota or production workload.
