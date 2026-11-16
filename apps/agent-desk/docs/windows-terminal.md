# Windows terminal lifecycle

Agent Desk pins `node-pty` to `1.2.0-beta.18`. Windows uses the bundled ConPTY runtime through the public `useConptyDll` option. Linux and macOS keep their existing native PTY backend.

The Windows inbox ConPTY path can retain a console host after a shell exits naturally: the native exit watcher removes the pseudoconsole handle record before the JavaScript exit callback, so a later public `kill()` cannot release that handle. The bundled runtime releases its host reference after spawning the child. This avoids relying on a second kill after natural exit. The bundled DLL and OpenConsole executable must be shipped alongside the selected native module.

`scripts/prepare-native.mjs` verifies the JavaScript patch and, on Windows, copies the pinned package's architecture-specific `conpty.dll` and `OpenConsole.exe` beside a rebuilt `build/Release/conpty.node`. This runs after `install-app-deps` during installation and through electron-builder's `afterExtract` hook after its dependency rebuild, before application copying and ASAR creation. The prebuilt native module retains its bundled adjacent assets. This preparation matters because a native rebuild can remove files previously copied by node-pty's own installation script.

## Pinned JavaScript patch

`scripts/patch-node-pty.mjs` runs after dependency installation and native dependency preparation. It requires the exact package name/version and verifies SHA-256 hashes of the original published JavaScript files. It recognizes its own fully patched output, so running it twice is safe. Unknown versions, altered upstream files and partial patches stop installation with an explicit error. Updating the dependency requires reviewing the patch against the new published sources.

The patch modifies two Windows-only dependency modules:

- `windowsPtyAgent.js` disposes the output worker and closes the input socket when the output socket has closed. Output has already drained at that point. It also exposes the existing native process-exit notification to the terminal wrapper.
- `windowsTerminal.js` emits one exit event only after both output closure and the native exit code are available. Native completion can arrive before or after output closure; neither ordering discards the final output or invents an exit code. Connection failures keep the upstream error/exit behavior.
- Terminal cancellation waits for an established connection, instead of waiting for the first output byte. Repeated cancellation is ignored, and deferred input/resize requests are cleared before stopping the process. This prevents a silent child from surviving a closed terminal tab.

The application does not access private node-pty fields at runtime. The patch changes dependency source at installation, and no native binary is modified. The application's normal close/dispose path still stops only running terminals.

## Verification

The targeted tests execute the actual patched Windows JavaScript with controlled native/socket boundaries to verify final-output ordering, exactly one exit notification, failed connections and worker cleanup. These tests do not replace the Windows runtime smoke test.

The native smoke test runs node-pty inside Electron and starts a real Node console process as its child. A headless xterm instance supplies the bundled ConPTY terminal-query replies and checks rendered output. It waits for the child's ready message before sending input. An external process watchdog bounds failures that block the native event loop or leave referenced handles alive. Packaged Windows testing must exercise the same lifecycle with the packaged native module and its adjacent runtime assets.

An isolated Electron 45.3.3 main-process check successfully loaded a worker through both an `app.asar` path and the corresponding physical `app.asar.unpacked` path. Agent Desk therefore retains the library's worker-path behavior; the entire node-pty directory is included in `asarUnpack`.

## Evidence and scope

The original Windows smoke failure reached an output assertion before hanging. It did not establish an initial spawn deadlock. Upgrading node-pty also brings upstream connection fixes, but those fixes alone do not resolve natural-exit worker cleanup. Missing child output and post-exit process retention are checked separately.

Primary upstream references:

- [node-pty release history](https://github.com/microsoft/node-pty/releases): deferred connection, startup error propagation and connection timeout fixes.
- [Natural-exit pseudoconsole and worker retention, issue 965](https://github.com/microsoft/node-pty/issues/965).
- [Referenced worker handles preventing process exit, issue 887](https://github.com/microsoft/node-pty/issues/887).
- [Windows agent source](https://github.com/microsoft/node-pty/blob/main/src/windowsPtyAgent.ts) and [native ConPTY source](https://github.com/microsoft/node-pty/blob/main/src/win/conpty.cc).
- [Electron ASAR behavior](https://www.electronjs.org/docs/latest/tutorial/asar-archives).
