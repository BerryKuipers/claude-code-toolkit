# Adaptive model routing for high-quality 3D and visual work

Updated: **2026-11-16**. Scope: Blender, Unreal, browser 3D, characters, environments, animation, rendering, and visually demanding UI/FX when relevant. **This is guidance, not a model-name lock or a scheduled monitoring job.**

## Routing rule for coding agents

1. For a substantial visual/3D task, inspect **which models and reasoning/effort levels are actually available in this session and provider**. Never assume access from a different account, machine, CLI or model announcement.
2. Match the capability to the task: inexpensive/low-medium effort for coordination, exports, routine wiring, fixtures and tests; a capable coding model at medium/high for nontrivial asset/shader/engine implementation; stronger visual/spatial specialists at high/extra-high **only when the creative complexity, failed iteration or consequential judgment warrants it**. A cheap model need not make the final artistic call. Escalate the hard subtask, not every worker.
3. **AAA is an output standard, not a model setting.** Iterate on actual editable assets and moving output in the target renderer (browser/UE/Blender as appropriate), with matched references, character identity, animation, lighting, camera and representative device performance. Do not equate a green build, attractive still, benchmark rank or a high effort setting with AAA acceptance.
4. Prefer the **lowest-cost combination of model + effort that demonstrably reaches the quality target**. An expensive model needs a credible quality or iteration-speed advantage on the relevant task, not just a higher name or parameter setting.

## Refresh only when there is a reason

While already working on a relevant project, compare the **available model IDs and effort settings** against the dated candidate evidence below. **Do not re-search benchmarks on every session or for every repository.**

Refresh this shared document when (a) a previously unassessed model/effort becomes available to the coding agents, (b) a relevant benchmark or pricing change materially affects the choice, or (c) the evidence is over ~30 days old **and** you are beginning substantial 3D/visual work. Otherwise keep coding with the current advice.

On refresh:
- Verify actual availability and pricing in the relevant provider/CLI. Read the latest task-matched **primary** benchmarks, their methods, dates and differences in agent harness/effort; avoid comparing scores with different tasks as though they share one scale.
- Prefer [Frontier3DBench](https://lab.einsia.ai/frontier3dbench/) for Blender objects/scenes and UE interactive worlds; [BlenderWorld](https://blenderworld.github.io/) for reference-driven Blender projects. Add newer, better-aligned evidence when available. Neither substitutes for a MetaHuman, browser-renderer or specific project's own A/B test.
- Where the choice could change actual spend or quality, compare a small matched task in **our real asset/render pipeline** at practical effort settings. Judge visible output, correctness, number of iterations, time and relative cost. Record limitations; never invent a win from a model release announcement.
- Update **this one document** with the date, verified candidate/effort, evidence links, task-specific recommendation and cost/quality caveat. Use a small change/PR in the project only if its local notes are stale or its real task requires an exception. If this repo is not writable in the current session, record the evidence in the active project's handoff and flag the shared update for its owner; don't block production work.

## Evidence snapshot (informative; not mandatory defaults)

*Last comparison: 2026-11-16. Check fresh provider pricing and account availability before spending.*

| Task signal | What the currently published evidence shows | Confidence / caveat |
| --- | --- | --- |
| Blender objects + scenes / mixed UE worlds | [Frontier3DBench](https://lab.einsia.ai/frontier3dbench/) (145 tasks, models on **max** effort): GPT-6.1 Sol 66.02 overall; GPT-6 Astra 63.85; Claude Opus 5.5 62.29. For its *UE interactive-world subset*, Astra 61.28 vs Sol 58.89. | Averages vary by task type and agent harness. Not evidence that max is cost-effective for every task. |
| Visual references and editable Blender deliverables | [BlenderWorld](https://blenderworld.github.io/) (223 tasks): GPT-6 Astra 79.9; comparison uses older OpenAI/Claude versions and does **not** establish a win over the newest available models. | Strong relevant benchmark, different task suite and older comparison cohort. |
| Character performance / MetaHuman / browser AAA | No listed public benchmark establishes an overall winner for our real rigs, shaders, speech, FACS or target browser hardware. | Choose by matched rendered motion and real project results. |

**Tracked candidates in this snapshot:** GPT-6.1 Sol, GPT-6 Astra, Claude Opus 5.5, and Claude Fable 5.2 (no directly comparable 3D result established here). New names/versions/effort modes should trigger the targeted refresh above, **not** an automatic promotion.

## Repository adoption

For a reusable agent workflow, see the [global AAA 3D production skill](../skills/aaa-3d-production/SKILL.md). Its user-scope Codex/Claude installation is documented in the [toolkit README](../README.md); repository links alone do not install skills.

Project `AGENTS.md` should link here and keep only a short routing rule. Preserve each project's existing gameplay, visual acceptance, resource, branch and ownership requirements; these override generic scheduling/coordination suggestions. Do not copy this entire benchmark table into multiple repositories. FlowerGuy-style non-3D apps apply the rule **only** to demanding visual design, Canvas/FX or asset-production work, using task-appropriate evidence rather than 3D scores alone.
