# Native runtime and performance

Version 0.2 uses Tauri and Rust for the desktop host and all backend services. React, TypeScript and xterm remain in the system webview. Node is a development/test dependency and may be required by an installed CLI, but no Node runtime or sidecar is bundled with Agent Desk. Version 0.1's Electron implementation remains in Git history at `3cd2b97cef95cc33b62b77ea5948871420669eeb`.

## Ownership and boundaries

`src-tauri/src/services.rs` validates and dispatches the existing UI operations. `desktop.rs` restricts them to the local main window and sends blocking work to the runtime's worker pool. External navigation and new webview windows are rejected. CSP excludes remote scripts, images, frames and direct provider network access from the renderer. Provider requests and credentials stay in Rust.

The frontend uses one Tauri channel for ordered terminal output. Every terminal retains a monotonically increasing sequence and a bounded snapshot. Subscribing before launch/snapshot, then replaying only events beyond the snapshot sequence, avoids losing or duplicating output while views mount.

Filesystem edits preserve their original text and unknown configuration fields. Canonical roots, source revision checks, staged replacement and backups remain in force. Native session identifiers are resolved by the backend; an imported path does not automatically become resumable native history.

## Terminals and cleanup

`portable-pty` creates native Unix PTYs and Windows ConPTY sessions. The output reader continues draining while the process handle is waited on and the pseudoconsole is closed. Exit is emitted once, after the actual exit status and output closure are both known. Incremental UTF-8 decoding preserves characters split across native read boundaries.

The pinned vendored `portable-pty` 0.9.0 uses standard Windows creation flags `0`: a new embedded terminal has no parent cursor to inherit, so immediate resize and early close do not depend on startup cursor replies. The [patch note](../src-tauri/vendor/portable-pty/AGENT-DESK-PATCH.md) explains the single upstream code change; [UPSTREAM.json](../src-tauri/vendor/portable-pty/UPSTREAM.json) records the verified source archive, revision and file checksums.

Replay storage is capped at two million bytes per terminal. Up to 24 tabs can be open, and explicit close releases the tab's state. Hidden and exited terminal cursors do not blink; live output and native agent behavior continue while navigating between views.

Stopping a terminal terminates only its owned live process tree. Closing the app prompts for unsaved edits/running agents, then performs native cleanup. Forced operating-system termination is outside that graceful UI flow. Tests exercise natural exit with final output, immediate stop, and process cleanup rather than only removing a tab from the list.

## Resource decisions

| Area | Decision |
| --- | --- |
| Desktop host | Rust executable with the system webview; no bundled Electron/Node application runtime. |
| Session index | Cache only metadata and bounded previews, release parsed transcript bodies after use. |
| Codex history | Close app-server after each index/transcript batch; subsequent fresh work pays startup again. |
| Files and HTTP | Bounded scans, read sizes, response sizes and timeouts; no work on the UI thread. |
| Native tools | Cache executable/version detection briefly instead of spawning all CLIs on every bootstrap refresh. |
| Terminal rendering | Ordered channel, bounded replay and inactive cursor suspension. |
| Release | Native optimized build with thin LTO, a single codegen unit and stripped symbols. |

Tauri is not an all-native widget toolkit: the React interface still runs in WebView2/WebKit. System webview processes, graphics composition and agent children can dominate memory. A Rust host alone does not establish lower GPU utilization or faster model responses. The app neither runs model inference itself nor adds a GPU compute pipeline.

## Measurement protocol

Build a release executable, then run:

```bash
node scripts/measure-resources.mjs --binary src-tauri/target/release/agent-desk --output test-results/resources.json
```

Use `.exe` on Windows and `xvfb-run -a` on headless Linux. Optional `--baseline <electron-executable>` and `--baseline-root <directory>` compare the preserved prior application. The helper uses separate isolated homes and the same fixture settings. It waits for the renderer to initiate the fixture history request and for a browser process to appear before starting the warm-up period and finite idle sample. It records this readiness time, platform/runtime identity, the full descendant process tree, RSS/working set, available private/PSS measurements, CPU time and file sizes. Sum-of-RSS can double-count shared pages; use PSS/private figures where supplied and preserve that distinction in reports.

Windows UI tests start the real executable and attach the matching EdgeDriver to its isolated WebView2 instance through a temporary loopback debugging port. This follows Microsoft's supported attach method and avoids the observed WebView2 driver launch regression. The shipped app does not enable that test-only port. Linux uses tauri-driver's native WebKit launch method. The Linux comparison runs the verified Ubuntu 24.04 AppImage and the older Electron package together on Ubuntu 26.04 because that older binary requires newer glibc.

No real accounts, model requests or coding jobs are used in the idle baseline. A busy agent, a large personal history or another webview version is a different workload. The benchmark does not measure GPU utilization, battery drain or inference latency. CI keeps its observations alongside native UI test evidence. Historical artifact availability is recorded; missing baseline data must not become an invented percentage improvement.

## References

- [Tauri architecture](https://v2.tauri.app/concept/architecture/)
- [Tauri process model](https://v2.tauri.app/concept/process-model/)
- [Tauri channels](https://v2.tauri.app/develop/calling-frontend/#channels)
- [Native WebDriver testing](https://v2.tauri.app/develop/tests/webdriver/)
- [Microsoft WebView2 WebDriver launch and attach methods](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webdriver)
- [portable-pty](https://docs.rs/portable-pty/latest/portable_pty/)
- [Rust keyring](https://docs.rs/keyring/4.2.0/keyring/)
