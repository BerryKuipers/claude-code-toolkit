# Agent integrations

Verified against official documentation and source on 16 November 2026. Agent Desk runs the installed native agents in a pseudoterminal. Their own tools, authentication, permission prompts, MCP connections, slash commands and skills remain available. Agent Desk indexes existing local history and prepares launches; it does not convert one vendor's agent session into another vendor's session.

The terminal dependency is pinned to `node-pty 1.2.0-beta.18`. The stable 1.1.0 release can block the Windows event loop while connecting its output pipe. The pinned release includes the upstream deferred-connection, worker-timeout and spawn-cleanup fixes. Both platforms run the native lifecycle check and a packaged-application PTY test. Sources: [Windows spawn deadlock](https://github.com/microsoft/node-pty/issues/763), [upstream fixes and releases](https://github.com/microsoft/node-pty/releases).

## Supported session sources

| Agent | History source | Resume |
| --- | --- | --- |
| Claude Code | `CLAUDE_CONFIG_DIR/projects`, normally `~/.claude/projects`; JSONL conversation chains | `claude --resume <id>` in the recorded project |
| Codex | Native `codex app-server` history API; local `sessions` and `archived_sessions` rollouts as a visible compatibility fallback | `codex resume <id>` in the recorded project |
| Gemini CLI | `~/.gemini/tmp/*/chats/session-*.jsonl`, plus legacy `session-*.json` | `gemini --resume <id>` in the recorded project |
| Antigravity CLI | `~/.gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl` | `agy --conversation <id>` |
| Antigravity App and IDE | Corresponding `antigravity` and `antigravity-ide` transcript roots | Native import through `agy` → `/resume` → **Other**; this creates a copy |

History folders can be added in Settings. A folder may contain an exported local history tree; custom roots do not make another computer's project directory available on this computer. Project directories that are missing or unknown disable direct resume and explain why. Agent Desk never guesses a project directory from an opaque folder hash.

### Claude Code

The reader follows `uuid`/`parentUuid` ancestry from the current conversation leaf, so abandoned branches do not appear as current conversation. It recognizes text, tool invocation and tool result blocks, custom session titles, model metadata and cwd. Subagent directories and sidechain records are excluded from the main history list.

The official Agent SDK also exposes `listSessions`, `getSessionMessages`, rename, tag and fork operations. The present filesystem reader keeps history browsing independent of a bundled SDK installation. Native CLI resume remains responsible for restoring the complete agent context.

Sources: [CLI reference](https://code.claude.com/docs/en/cli-reference), [.claude directory](https://code.claude.com/docs/en/claude-directory), [SDK session management](https://code.claude.com/docs/en/agent-sdk/sessions), [official session browser example](https://platform.claude.com/cookbook/claude-agent-sdk-05-building-a-session-browser).

### Codex

Agent Desk owns a local `codex app-server --listen stdio://` child process. It initializes the protocol, pages `thread/list` across active and archived history, and sets `modelProviders: []` to include every configured provider. It reads selected conversations with `thread/read` and `thread/turns/list` using full items. Indexing and reading do not call `thread/resume` or `turn/start` and do not make model inference requests.

Current paginated history can be absent from legacy rollout files. If app-server is unavailable, the interface reports that limitation and uses readable local rollouts. Older server versions that lack paginated turn reads use `thread/read` with `includeTurns: true`, with a visible compatibility notice. `CODEX_HOME` is respected. Archived sessions remain readable; restore them in the native agent before resuming.

Source: [official app-server protocol](https://developers.openai.com/codex/app-server), [rollout implementation](https://github.com/openai/codex/blob/main/codex-rs/rollout/src/recorder.rs). Local command flags were also checked against Codex `0.167.0-alpha.4`.

### Gemini CLI

Both legacy whole-file JSON and current append-only JSONL are recognized. The reader applies metadata updates, message content/tool-result patches, message ordering, removal and `$rewindTo` operations. A rewind removes the referenced message and every later message, matching the upstream reader.

Project locations come from detected `.project_root` files, explicit cwd metadata, or a match between a configured project path and its SHA-256 directory hash. A hash alone is not a project path. `GEMINI_CLI_HOME` is the parent directory that contains `.gemini`, not the `.gemini` directory itself.

Sources: [session management](https://geminicli.com/docs/cli/session-management/), [configuration](https://geminicli.com/docs/reference/configuration/), [record types](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingTypes.ts), [current transcript reader](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingService.ts).

### Antigravity

Antigravity has a native `agy` CLI, headless streaming and an ACP interface. The documented CLI `cache/last_conversations.json` maps absolute project paths to their most recently used conversation IDs. It is used for project mapping, never treated as a complete session index.

Transcript locations are documented, but a versioned public on-disk message schema is not. Agent Desk recognizes text/message records and documented stream event shapes. Unrecognized transcript formats are reported explicitly instead of displaying invented messages. App and IDE histories are labeled separately. Direct CLI resume is enabled only for CLI records with an available project path; desktop import is performed by the native `/resume` picker because it clones history and context.

Sources: [CLI reference](https://antigravity.google/docs/cli/reference), [resume and App import](https://antigravity.google/docs/cli/commands/resume), [transcript paths in hook metadata](https://antigravity.google/docs/hooks), [headless events](https://antigravity.google/docs/cli/headless/), [ACP](https://antigravity.google/docs/cli/acp/).

## Models and provider protocols

An agent and a model provider are separate choices. Provider profiles must use a protocol the selected agent understands. A model appearing in a provider's catalogue does not by itself establish tool or wire-format compatibility.

| Agent | Per-process configuration |
| --- | --- |
| Claude Code | `--model`, `--effort`, `ANTHROPIC_BASE_URL`, bearer `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` |
| Codex | `--model`, TOML config overrides for reasoning effort and custom `model_providers` |
| Gemini CLI | `--model`; Gemini-compatible `GOOGLE_GEMINI_BASE_URL` under API-key authentication |
| Antigravity CLI | `--model`, `--effort`; Gemini-compatible custom endpoint where the installed authentication mode supports it |

Claude Code through a translation proxy to non-Claude models is a compatibility route; Anthropic explicitly does not support that configuration. Gemini-compatible endpoint overrides are not interchangeable with OpenAI chat-completions endpoints. Agent Desk does not claim otherwise or silently convert the protocol.

Sources: [Claude gateway setup](https://code.claude.com/docs/en/llm-gateway-connect), [Claude gateway compatibility scope](https://code.claude.com/docs/en/llm-gateway), [Codex custom providers](https://developers.openai.com/codex/config-advanced), [Gemini endpoint variables](https://geminicli.com/docs/reference/configuration/), [Antigravity authentication](https://antigravity.google/docs/install?tab=cli).

## Local data and limits

Only recognized transcript files and project-mapping sidecars are read. The history reader does not load authentication credentials or API key files. Original source paths remain local to the application. The app neither uploads history nor makes a model call to index or read it. Transcript content may contain material previously printed by an agent; it is the user's existing conversation data.

Filesystem scans do not follow symbolic links and stop at 10 directory levels, 20,000 directories or 10,000 candidate files per root. Session previews are bounded to 2,400 characters. Readable transcripts are limited to 5,000 display messages and 80,000 characters per message. Local files are read up to 32 MiB; larger JSONL files show the first 8 MiB and last 24 MiB with an explicit partial-history warning. Oversized legacy JSON is reported rather than partially parsed. Invalid or incomplete JSONL lines are counted in warnings. Codex requests time out after 10 seconds, paginate at most 10,000 sessions per section, and limit transcript loading to 32 MiB.

Index caches retain metadata and short previews, not every full conversation. Refresh picks up transcript changes. A selected transcript is read again, so history written by an active agent can become visible without restarting Agent Desk.

Additional history folders are readable imports. Direct resume is enabled only for sessions present in the active native history store; copied or exported files elsewhere remain view-only even when their original project still exists. When both a native session and an exported copy share an identifier, the native session wins. Configure an alternative native store through the application's launch environment (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`, or `GEMINI_CLI_HOME`) so indexing and terminal launches use the same store. Per-profile history-home overrides are rejected.
