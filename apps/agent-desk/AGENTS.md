# Agent Desk

Agent Desk is a standalone Electron, React and TypeScript application inside this toolkit. All application dependencies and release tooling belong in this directory. It can be moved into its own repository without the rest of the toolkit.

Use the real CLI and documented integration surfaces. Keep native agent permissions, hooks, login flows, status lines and session ownership intact. Profiles distinguish the agent, endpoint protocol, provider and model. Native configuration follows the installed CLI configuration; it does not imply a particular subscription or provider.

Keep the main-process boundary narrow. The renderer has no Node access. Credentials stay in the operating-system store or memory. Never put machine configuration, real session transcripts or API keys in this repository.

Preserve unknown configuration keys. File edits require a current revision and a backup. Index only recognized session formats, and display limitations and read failures. Antigravity App/IDE import is different from resuming a CLI conversation.

Use single quotes, strict TypeScript, small feature modules and no unnecessary comments. Avoid hardcoded model releases; discover catalogs from the selected endpoint.

Run `npm run typecheck`, `npm test` and `npm run build`. For changes to the Electron boundary, terminal lifecycle or UI flows, run `npm run test:desktop` on a desktop-capable machine (`xvfb-run -a` on Linux CI). Package Windows on Windows and Linux on Linux for release validation. Never report a platform runtime check as passed merely because its installer was produced.
