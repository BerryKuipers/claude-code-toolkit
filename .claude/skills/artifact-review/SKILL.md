---
name: artifact-review
description: Present work as an interactive review page, comparison, explainer or status board with editable feedback that can return to the agent. Use when visual interaction improves review; supports local HTML and available native Claude Artifacts.
---

# Artifact review

Make the result easy to inspect, change and discuss. Reuse an existing project view when it already does the job. A short answer needs no page.

## Choose the surface

- If the user requests a Claude Artifact and a native Artifact tool is available, use it only when uploading the content is authorized. Read [Claude capabilities](references/claude-artifacts.md) before publishing or adapting local controls. Discover the actual tool; do not invent an API or call a different account's CLI. Preserve the artifact URL for updates.
- Otherwise produce a standalone HTML page in a project-local directory that is already ignored by version control. Confirm the directory is ignored before writing. If no suitable directory exists, use a local temporary directory outside the repository; do not change ignore rules just for a review page. This is the portable default for private work across hosts. Use an available inline HTML surface when supported; otherwise provide a clickable file link and open it with an available browser tool. Do not claim a skill creates an IDE side panel.
- Prefer existing project styles and libraries. The optional [review template](assets/review.html) needs no server, dependencies, network or account. Copy it to the chosen review directory, assign `data-review-id` a stable unique value, and replace the demonstration content. Keep its id stable across updates; use a new revision when evidence changes.

## Build only the needed interaction

Show the deliverable first: a map, screenshot, diagram, comparison or explorable result. Put concise status, evidence date/revision and remaining uncertainty beside it. For a comparison, align the alternatives. For a status board, distinguish completed work, current work and blockers; a static snapshot must say when it was gathered. Update the same page at meaningful milestones rather than starting another app.

Offer relevant controls only. The template includes per-item comments, a proposed review decision, local draft saving, and JSON import/export. Native HTML/SVG controls are sufficient for many diagrams and maps; preserve keyboard access, labels and readable narrow-screen layout. Treat user-entered feedback as text, never HTML.

## Return feedback to the agent

Local template drafts stay in that browser profile and location where storage is available. They are not automatically visible to an agent. The user can export a JSON file and provide its path to the agent; import restores that feedback in another browser. The feedback includes artifact id and revision; mismatched revisions must be identified rather than silently approving changed work. The agent reads the exported data, applies requested changes, updates the same page and records what it actually verified. A review decision is feedback, not authorization to publish, deploy or spend.

Keep private data local unless the user authorizes upload. Do not add remote images, analytics, external scripts or third-party viewers to a private page. Export only what the user entered and the minimum artifact identity; never include credentials. Local storage is convenience, not a backup: the visible save message must report failures and offer export. No background watcher/server is needed for this default workflow.

## Optional live local feedback

When the user requests a fixed local URL or direct feedback without exporting, reuse a small existing project bridge instead of building another app. Bind only to `127.0.0.1`, serve an explicit file/API allowlist, reject foreign Host/Origin requests, require a same-origin token for writes, and bound JSON types, text sizes, normalized point coordinates and queue size. Persist notes atomically with an id, map revision, point or room, text and status. Keep the agent's status-update authority separate from browser submissions; submitting a note must not mark work applied or approved.

Point review can use edit mode, click plus comment, and equivalent keyboard controls. Poll for notes/status and map revision updates; preserve unsent drafts and their original revision before refreshing. Do not silently attach older notes or acceptance to a new map. A stopped service should report disconnection while retaining drafts. Keep JSON export as an offline backup when useful.

Start one tracked local process only when requested or needed for the authorized feature; record its PID, URL and durable queue path in the existing checkpoint. The active agent can read the queue directly and update statuses. Local persistence does not wake a stopped model or guarantee an immediate AI reply: show saved/waiting until an agent actually handles the note. Close owned test processes and ephemeral browsers; leave the intended review service only while requested. A local service for direct feedback is not permission to bypass a browser/tool policy rejection.

## Check and deliver

Open the real page in a browser, inspect it, exercise its primary control and one plausible failure case (for feedback: reload persistence and wrong-file import). Use installed browser tools/dependencies; do not install a stack just for review. Include the page link, how feedback returns, checks actually run and remaining limits. Keep task status in the existing checkpoint; the page supplements it.

Example invocation in either host: `Use artifact-review to show this result with a status summary and editable review notes. Keep it local.` Codex also supports `$artifact-review`; Claude Code supports `/artifact-review` once the skill is discovered. Discovery may require a new session. This skill does not synchronize Claude accounts, comments or browser profiles.
