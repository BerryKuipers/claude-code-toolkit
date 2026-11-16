---
name: aaa-3d-production
description: Use for substantial AAA-quality 3D production in Blender, Unreal Engine, MetaHuman, Three.js, WebGPU or game environments: character design, animation, facial performance, material/shader look-dev, level art, FX, reference matching, visual-quality review, and cost-aware model/effort routing. Prefer real rendered evidence over model prestige. Refresh benchmarks when a new relevant model becomes available.
---

# AAA 3D Production

Deliver convincing, editable, high-end assets **in the actual target runtime**, not just pleasing source renders or passing builds. Use this skill when the task involves substantive 3D or visually demanding 3D-related work. Ordinary backend/UI tasks do not trigger it.

## 1. Reuse project authority and existing production tools

Read the relevant project's `AGENTS.md`, current task and its specific visual, technical, hardware and licensing requirements. Preserve the project's established pipelines and creative authority:
- For MokumLife, the project-specific `docs/AUTONOMOUS_3D_PIPELINE.md` already defines its complete production loop.
- For Unspoken, use its MetaHuman and FACS/face pipeline; a beautiful static face does not validate micro-expressions or spoken performance.
- For SpeedOrb, ArenaFriends, Veilwood and PinballDreaming, use their own world/character/physics, renderer and verification requirements.
- Apply to FlowerGuy only for substantial visual/FX design work, not routine DJ-library code.

If the personal `visual-ground-truth` skill is available, reuse it for side-by-side comparison instead of inventing a second image-review process.

## 2. Choose a model and reasoning effort for the task

The single source of evidence and refresh policy is [Adaptive 3D Model Routing](https://github.com/BerryKuipers/claude-code-toolkit/blob/main/docs/3D_MODEL_ROUTING.md).

- Find which models and effort levels **this agent can actually use**. Do not infer availability from a release post, another CLI or a model name in older docs.
- Use economical low/medium reasoning for coordination, routine code, tests, asset importing, exports and capture. Use capable coding/creative models for substantive mesh, material, shader, rig or engine work; use high/extra-high specialist reasoning for difficult spatial/creative decisions, visual adjudication or failures of lower-effort iterations.
- **Escalate the hard subtask, not the entire workforce.** Do not assume a costly model or maximum effort produces better art. Optimize for observed quality, iterations and cost.
- Do **not** run benchmark research on each session. When a new, relevant model/effort is genuinely available, material benchmark/pricing evidence changes, or the shared evidence is stale and a major creative task warrants review, inspect **task-matched** primary benchmarks and the provider's actual prices. Compare a representative local scene in the real pipeline if it could change the recommendation. Update the shared guide with date, sources, scope and uncertainty when you can write there; otherwise record concise evidence in the current project's handoff for subsequent shared update. Continue useful production work.

## 3. Build, see, compare, improve

Work autonomously in meaningful increments:
1. Identify the actual user-visible quality target and the strongest relevant visual reference, including character identity and anatomy where applicable.
2. Build or improve real editable assets, materials, lighting, animation and integration.
3. Render/record the **target engine and delivery path** (e.g. UE native versus browser UE/WebGPU versus Three.js are distinct). Capture representative matched views **and movement**, not just a beauty still; include expressions, camera distances and interaction where relevant.
4. Compare specific shortcomings (silhouette, eye/lash/brow readability, topology, skin, lighting, hair, motion, timing, material realism, occlusion, FX, scale and performance) and revise the highest-impact defect.
5. Retain reproducible evidence and source assets. Be accurate about device, renderer, FPS, version and untested limitations. Passing compilation and automated validators is necessary where required, never proof of AAA visual fidelity.

If several genuinely different attempts fail, change the hypothesis or surface the specific bottleneck instead of spending indefinitely on the same tweak. Where visual comparison cannot run, report **implemented, not visually validated**.

## 4. Keep the handoff lean

Report the actual model/effort used if meaningful, what was materially changed, before/after evidence, what improved or remains poor, and whether the shared model-routing guide was refreshed. Respect existing project worktree/branch/deployment rules. No new scheduler, model-pinned agents, paid-provider activation, heavyweight approval chain or automatic production release is implied by this skill.
