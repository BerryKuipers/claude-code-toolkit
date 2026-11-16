# Connections, configuration and skills

Agent Desk keeps its own settings and launch profiles in Electron's application data directory. Agent authentication, original settings and transcripts remain with their native tools. The app does not copy a Claude home directory into Git or replace the user's settings with a template.

## Connections

The initial profiles are Claude, Codex, Gemini and Antigravity using their native configuration, plus Claude Code connections to a local proxy, OpenRouter and DeepSeek. Native means the installed CLI's existing configuration and inherited environment, including a configured API provider, gateway or subscription login. It does not force subscription authentication. Models are deliberately not pinned to a generation of model names. Choose an available model from the connection's live catalogue, or enter an exact ID supported by the installed tool and endpoint.

| Connection | Agent protocol | Default endpoint | Catalogue |
| --- | --- | --- | --- |
| Native Claude / Codex / Gemini / Antigravity | Installed CLI | CLI-managed | Agent's own model picker |
| Claude local proxy | Anthropic Messages | `http://127.0.0.1:18765` | `/v1/models` |
| Claude OpenRouter | Anthropic Messages | `https://openrouter.ai/api` | `https://openrouter.ai/api/v1/models` |
| Claude DeepSeek | Anthropic Messages | `https://api.deepseek.com/anthropic` | `https://api.deepseek.com/models` |

The native model list is not simulated. A native profile retains its configured model ID or the CLI's current default. The CLI's own account, provider configuration and environment remain the source of truth for model access and availability. For example, Codex's existing `model_provider` configuration is preserved.

OpenRouter exposes an Anthropic-compatible entry point directly. This profile uses an OpenRouter key as `ANTHROPIC_AUTH_TOKEN` and clears `ANTHROPIC_API_KEY` for that child process. DeepSeek also documents an Anthropic-compatible entry point. Neither direct profile needs a local translation proxy. Third-party model compatibility with Claude Code features can differ even when a model appears in the catalogue.

Provider catalogues are read with a bounded response size and timeout. Redirects are not followed with credentials. OpenRouter's public catalogue is fetched without a key; the connection test uses its authenticated key endpoint. Prices returned by OpenRouter are converted from per-token prices to prices per million tokens. A zero input and output token price is labelled free; this is catalogue metadata, not a guarantee about account limits or other features.

The local proxy connection test checks `/healthz`. A successful response means the process is alive, not that any upstream account is logged in. Its `/monitor` view reports proxy activity without request bodies. The current proxy accepts monitor reads from loopback peers only, so use a local SSH tunnel when monitoring a remote instance. There is no remote administrative HTTP API to start, stop or authenticate the service.

The proxy chooses a provider from registered model IDs and uses its own provider credentials. A model selected from OpenRouter's catalogue is not necessarily routed to OpenRouter by this proxy. Agent Desk keeps the endpoint and provider explicit; it does not strip vendor prefixes and present that as proof of OpenRouter routing.

## Keys and environment

Profile files contain connection metadata, model IDs, an optional environment-variable name and non-secret environment settings. API key values belong in the app's protected credential facility or an existing environment variable. `hasSecret` is computed at runtime and is not written into `profiles.json`.

Extra environment settings reject credential fields and variables that can replace the runtime, shell or executable search path. The launcher composes a child environment for each session. It does not set machine-wide environment variables. Native profiles preserve inherited route/authentication pairs; explicit custom/provider routes clear conflicting credentials and route settings before applying the selected connection. Main-session, small/background and subagent model settings are separate. Proxy-wide effort or service-tier overrides may still take precedence at the proxy; inspect that service's configuration when actual behavior differs from a session's requested setting.

## Original configuration files

The configuration editor discovers:

- Claude settings, keybindings, global instructions and `.claude/profiles/*.json` overlays.
- Codex `config.toml` and global `AGENTS.md`.
- Gemini settings and global `GEMINI.md`.
- Antigravity CLI settings and keybindings in `.gemini/antigravity-cli`.
- Corresponding project configuration and instructions for projects added in Agent Desk.
- Explicit JSON profile overlays inside the Claude profile directory or a configured project.

Credential files such as `.credentials.json`, `auth.json` and `.claude.json` are not part of the editor's file list. Existing settings can nevertheless contain credentials put there by another tool; treat their contents and local backups as private.

Configuration and skills discovery respect `CLAUDE_CONFIG_DIR` and `CODEX_HOME` when set. `GEMINI_CLI_HOME` names the parent of the `.gemini` directory, matching Gemini CLI and the session indexer. An explicit environment override can locate an agent home outside the user's default home; that directory is an approved root, while links from individual files or descendant directories still cannot escape it. Antigravity keeps its separately documented home paths. These environment values are read from the app's process environment; Agent Desk does not rewrite them globally.

The editor saves the complete document the user has edited, preserving all untouched fields and formatting. It validates JSON/TOML first, compares a SHA-256 revision against the current file, writes a local backup of the previous bytes, and atomically replaces the file. A missing-file revision is distinct from an empty file. Concurrent writes to the same canonical path inside Agent Desk are serialized, and the revision is checked again after staging, immediately before replacement. If a detected external edit changes the document, saving is rejected until it is reloaded. This is optimistic conflict detection; other applications do not share a file lock. Missing configuration files can be created only at registered paths. The editor does not follow a destination directory link outside an approved home or project.

Backups are placed below the app data directory's `backups/configs` and `backups/skills` directories. They are not uploaded or committed. The configuration editor does not execute hook commands or status-line scripts merely by opening them. Editing Claude's existing `statusLine`, hooks, plugins, permission settings and other fields in its JSON config preserves the existing native behavior when Claude is launched in the integrated terminal.

## Skills library

Agent Desk scans personal and configured project skills for Claude, Codex, Gemini and Antigravity, shared `.agents/skills` directories, additional directories explicitly added in Settings, and installed Claude/Codex plugin trees. Scans are bounded by directory count, depth, file size and skill count; the UI receives a warning when a limit is reached.

Each entry includes its agent, scope, actual file path, linked status and editability. Name and description are read from YAML frontmatter. Editing supports ordinary Markdown skills that do not have frontmatter too. Invalid YAML frontmatter is rejected before saving.

Personal and project skills can be created and edited. Disabling a normal skill renames `SKILL.md` to `SKILL.md.disabled`; restoring it returns the original filename. No content is deleted. Existing enabled and disabled copies are not silently overwritten.

Installed plugin skills are read-only because a plugin update owns those files. A personal copy provides a place to customize one. A linked skill may be edited when its target is also inside a registered writable skills root, such as a Claude link into `.agents/skills`. The enabled state of a link must be changed at its original entry to avoid unexpectedly disabling a shared skill for other tools. A link into an unregistered external directory stays read-only, and writes re-check the target in case a link changed after scanning.

Agent Desk does not pretend that editing a skill automatically reloads it into an already-running agent. Reload/restart behavior belongs to each CLI. Claude profile `skillOverrides` and plugin-level `enabledPlugins` remain native settings; installed plugin skills do not necessarily support per-skill overrides.

## Official references checked during implementation

- [OpenRouter: Claude Code integration](https://openrouter.ai/docs/guides/coding-agents/claude-code-integration)
- [DeepSeek: Anthropic API](https://api-docs.deepseek.com/guides/anthropic_api/)
- [DeepSeek: Claude Code integration](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/)
- [DeepSeek: model catalogue](https://api-docs.deepseek.com/api/list-models/)
- [Antigravity settings](https://antigravity.google/docs/settings/)
- [Claude Code proxy HTTP API](https://github.com/BerryKuipers/claude-code-proxy/blob/main/docs/src/content/docs/reference/http-api.md)
- [Claude Code proxy models and routing](https://github.com/BerryKuipers/claude-code-proxy/blob/main/docs/src/content/docs/using/models-and-routing.md)

These references establish endpoint contracts, not a fixed list of future models. Live catalogues and installed CLI behavior take precedence over historical model examples.
