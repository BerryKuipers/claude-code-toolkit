# Agent Desk

One desktop workspace for Claude Code, Codex, Gemini CLI and Antigravity. Find a conversation, choose a connection and model, resume the original agent, and manage your configuration and skills without switching between directories and terminals.

Agent Desk is a native Rust/Tauri application with a React interface and interactive terminals. Version 0.2 replaces the Electron application shell and all Node backend services; the installed app does not bundle Electron or a Node sidecar. It runs the installed coding agents and retains their permissions, slash commands, tools, status lines, hooks and authentication flows. It is an independent project, not an Anthropic, OpenAI or Google product.

## Start

Install the desktop package for your platform, or build from this directory:

```bash
npm ci
npm run build
./src-tauri/target/release/agent-desk
```

For development:

```bash
npm run dev
```

Building requires Node.js 24 or newer, Rust 1.90 or newer, and the [Tauri platform prerequisites](https://v2.tauri.app/start/prerequisites/). On Windows the compiled program is `src-tauri/target/release/agent-desk.exe`. Installed release packages do not require Node or Rust for Agent Desk itself. Install the CLI agents you want to use on the same computer. Agent Desk detects them on the executable search path and common user installation paths. Full executable paths can be set in **Settings → General**. It supports native binaries and standard npm JavaScript launchers on Windows; arbitrary shell command strings are not executed.

**On first launch:** select **New session**, choose an installed agent and a project folder, then start with its native configuration. Existing sign-in is reused by that CLI. Sessions already stored on this computer appear in **Sessions**. Missing agents are shown as unavailable instead of being installed or authenticated automatically.

## What is included

| Area | Behavior |
| --- | --- |
| Sessions | Unified history, agent/project/model filters, text search over indexed titles and previews, date grouping, Markdown conversation reader, export and native resume. |
| Workspace | Multiple interactive terminals with persistent tabs, real keyboard input, resize, ordered output, exit status and explicit process stop. Navigating elsewhere keeps sessions running. |
| Connections | Saved profiles for native configuration, local proxy, direct OpenRouter, direct DeepSeek and compatible custom endpoints. Agent, provider, protocol and model remain separate. |
| Models | Catalog discovery from the selected endpoint, search, context information and a free-model filter. Model IDs can also be entered directly. |
| Proxy | Start the configured local proxy, inspect its monitor, check liveness and run its provider sign-in flows in an interactive terminal. Only a process started by the app can be stopped by the app. |
| Skills | Discover personal/project/shared/plugin skills; read Markdown; create, edit, disable and restore editable skills; launch an agent to improve a selected skill. Source paths and linked/plugin status remain visible. |
| Configuration | Native JSON/TOML/instruction-file editors, Claude quick fields for model/effort/output style/status line/plugins, format validation, revision checks and backups. |
| Appearance | System/light/dark themes, terminal font and scrollback settings, keyboard navigation and app shortcuts that leave focused terminal shortcuts intact. |

The transcript reader shows saved history. Live interaction uses the original CLI inside the Workspace terminal, so native capabilities do not depend on a partial reimplementation of the agent interface.

## Choose a connection

**Native configuration** follows the installed CLI's existing configuration and inherited environment, including any provider routing already configured there. It does not force a subscription or silently change the CLI's default provider.

**Local proxy** defaults to the existing `claude-code-proxy` Anthropic-compatible listener at `http://127.0.0.1:18765`. Start it from the app or use an already-running instance. Fetch its catalog to choose a model the proxy actually routes. Proxy health confirms the service is alive; it does not prove an upstream account is authenticated.

**Direct OpenRouter** uses `https://openrouter.ai/api` with Claude's Anthropic-compatible interface. **Direct DeepSeek** uses `https://api.deepseek.com/anthropic`. These are distinct from selecting a similarly named model on a local proxy. Add a key or reference a key already present in the environment. Catalog or connection checks do not request model generation.

**Custom connections** must speak the protocol required by the agent: Anthropic Messages for Claude, Responses for Codex, and Gemini API for Gemini/Antigravity. A model's presence in a catalog does not establish full tool compatibility. The proxy's native Codex Responses endpoint must be enabled in its own configuration before using it with Codex.

Profiles can override model, supported reasoning effort, Claude's small helper model, its separate subagent model, context window and extra nonsecret environment settings. These overrides apply to the launched child process, not the operating system or another open session. Leave fields blank to use the agent's default.

## Session locations and resume

- Claude: `~/.claude/projects` or `CLAUDE_CONFIG_DIR/projects`.
- Codex: the native app-server history API, with recognized local rollouts as an explicitly reported compatibility source.
- Gemini: legacy JSON and current JSONL beneath `~/.gemini/tmp`; `GEMINI_CLI_HOME` is the parent of `.gemini`.
- Antigravity: the documented CLI/App/IDE transcript roots beneath `~/.gemini`.

Add other history directories in Settings to inspect copied or exported histories. **Copies outside the active native store are view-only**: their IDs alone cannot make the original CLI resume a file it does not own. Sessions with missing or unknown project folders also show their limitation instead of launching into the wrong project.

Antigravity App/IDE history is distinguished from CLI history. The documented native `/resume` → **Other** import clones the conversation; it is not advertised as direct CLI resume. Its on-disk transcript schema is not a stable public versioned contract. Recognized records are displayed, while unknown formats produce a visible warning.

The index is bounded to protect responsiveness on large stores. Truncated histories and scan limits are reported. Search covers indexed metadata and previews, not an unlimited full-text database of every message. This release manages local sessions; it does not remotely control another computer.

## Configuration, credentials and skills

The app edits selected original settings and instruction files. It does not copy your entire agent home or overwrite unknown keys. Each content edit uses a revision hash, stages the write, verifies the source again and saves a backup. An external change requires reloading the file before saving. Backups remain under the app data directory's `backups` folder.

Keys can be stored in Windows Credential Manager, macOS Keychain or the Linux Secret Service through Rust's OS-keyring integration, or kept only in memory until the app closes. On Linux, persistent saving is disabled if an appropriate system secret store is unavailable. Profile files contain environment variable names and credential-presence metadata, never saved key values. Native CLI credentials remain owned by their CLI.

Upgrading from 0.1 reuses the existing `agent-desk` settings, profiles and backups directory. Electron-encrypted credentials cannot be silently converted to another platform credential API: their original file remains untouched, and a visible notice explains that saved keys need to be entered again or supplied through an existing environment variable. Native CLI logins are unaffected.

Installed plugin skills are read-only in this editor. Their source package can be managed through the native CLI or its source repository. Personal skills can be disabled by renaming `SKILL.md` to `SKILL.md.disabled` and restored without losing their contents. Linked skills retain their actual source and are editable only within a registered writable source root.

“Improve with an agent” starts a real selected agent with the skill path and an improvement prompt; it does not silently rewrite a skill or claim that an improvement has already happened.

## Build and verify

```bash
npm run typecheck
npm test
npm run build
node scripts/setup-webdriver.mjs
npm run test:desktop
```

On Linux CI, run the desktop tests with `xvfb-run -a npm run test:desktop`. Tests use isolated homes, synthetic transcripts, fake CLI executables and a loopback model endpoint; they do not use personal conversations, credentials or paid model requests. The Rust test suite runs the actual native PTY, including input, Unicode output, resizing, natural exit and early termination. Native GUI tests use tauri-driver and the platform WebDriver.

On Windows, run local desktop tests from a non-administrator terminal. [WebView2 ignores environment debugging overrides in elevated host processes](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security#for-an-elevated-host-app-use-appropriate-override-flags). The harness launches the real application with its fixture-local WebView2 profile and attaches EdgeDriver through an ephemeral loopback debugging port. On elevated GitHub-hosted Windows runners only, it temporarily sets the documented app-scoped `HKLM\SOFTWARE\Policies\Microsoft\Edge\WebView2\AdditionalBrowserArguments` value for `agent-desk.exe`, preserving and restoring its prior value and type after each test. It does not change machine policy during local runs or enable debugging in the shipped application.

Package for the current target system:

```bash
npm run dist:win
npm run dist:linux
npm run dist:mac
```

The GitHub workflow checks Windows and Ubuntu 24.04 and produces installers/archives plus desktop test evidence. After packaging, it launches the actual packaged application and checks session resume and native terminal input/output again through the Rust PTY implementation. Windows builds are unsigned. macOS packaging is provided for local builds on a Mac; it is not covered by this workflow.

For a browser-only visual preview, start Vite and explicitly add `?demo=1`. This view is labeled as sample data and refuses live mutations. Opening the renderer without the native Tauri bridge or that explicit flag shows a desktop-required screen.

## Runtime and resource use

The native backend owns session parsing, filesystem access, provider HTTP requests, OS credentials, executable resolution and PTYs. React runs in the operating system's webview. The app therefore still has webview processes; the coding agents it starts are separate processes with their own resource use. Changing the shell language does not make remote model inference faster or eliminate GPU compositor memory.

Blocking operations run off the UI thread. Session caches retain bounded metadata and previews, not whole transcripts. Terminal replay is limited to two million UTF-8 bytes per tab, and hidden/exited terminal cursors stop blinking. Codex app-server history helpers close at the end of a scan or transcript read; the next fresh operation starts a new helper. This saves idle residency at the cost of a startup for each such batch.

CI records package sizes and actual process-tree memory and idle CPU in `test-results/resources/comparison.json`. It can compare the retained 0.1 Electron artifact when that artifact is available; a missing historical artifact is reported explicitly. These are observations on CI machines, not guarantees for every computer or GPU. See the measurement protocol in [native runtime](docs/native-runtime.md).

## Project boundary

This directory is a standalone package inside `claude-code-toolkit`. It has its own dependencies, lockfile, build, tests, license and documentation. It can be extracted into a separate repository without bringing configuration snapshots or the proxy source with it.

- `claude-config-backup` remains the private backup/restore project.
- `claude-code-proxy` remains the independently updated provider bridge.
- Agent Desk manages the installed tools and selected local configuration.

The video provided during development linked [REA](https://github.com/morluto/rea), a reverse-engineering toolkit, rather than a verified public repository of its demonstrated Claude-style app. Agent Desk is an original implementation and does not contain that demo's source or extracted proprietary assets.

See [configuration details](docs/configuration.md), [integration contracts and sources](docs/integrations.md), and [runtime and performance measurement](docs/native-runtime.md).
