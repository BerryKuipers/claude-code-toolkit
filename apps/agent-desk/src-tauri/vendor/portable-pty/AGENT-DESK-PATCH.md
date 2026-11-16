# Agent Desk Windows terminal patch

This is the published `portable-pty` 0.9.0 crate from WezTerm, retained under its upstream MIT license in `LICENSE.md`. `UPSTREAM.json` records the original archive checksum, upstream revision, original file hashes, and the hash of the modified file. The downloaded crate's checksum was verified against the registry entry in Agent Desk's Cargo lockfile before extraction.

The single source change is in `src/win/psuedocon.rs`: `CreatePseudoConsole` receives flags `0`, the documented standard creation mode. Agent Desk opens a new embedded terminal with its own empty screen; it has no parent terminal cursor to inherit. The upstream combination requests cursor inheritance and additional terminal-host modes that this application does not need.

Microsoft documents that cursor inheritance requires an asynchronous response to the startup cursor-position request. Subsequent pseudoconsole operations, including closing, can otherwise block. Removing that request makes immediate resize and early close independent of a mounted renderer or xterm startup replies. Normal application terminal queries still reach xterm.

No process, encoding, argument, environment, pipe, or exit implementation has been changed in this vendored dependency. Agent Desk separately owns process teardown and keeps the output reader active while closing the Windows pseudoconsole.

Verification lives in `src/terminals.rs`: the real native PTY tests cover input, resize, final Unicode output, natural exit, immediate resize, and early close without an xterm query responder. Windows execution is required to validate the Windows branch; a passing Linux test does not establish Windows runtime correctness.

Primary references:

- [Microsoft: CreatePseudoConsole flags and cursor response requirements](https://learn.microsoft.com/en-us/windows/console/createpseudoconsole)
- [Microsoft: pseudoconsole setup and teardown](https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session)
- [Microsoft: ClosePseudoConsole and output draining](https://learn.microsoft.com/en-us/windows/console/closepseudoconsole)
- [Upstream portable-pty documentation](https://docs.rs/portable-pty/0.9.0/portable_pty/)

When updating this dependency, review the new upstream source and rerun the Windows runtime lifecycle tests. Do not copy the patch into a new version without checking the changed implementation.
