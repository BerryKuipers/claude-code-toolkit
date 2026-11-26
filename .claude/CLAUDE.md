# Shared toolkit defaults

Use the consuming project's explicit decisions and conventions. The toolkit supplies reusable defaults, not a replacement for project policy. Native `.claude/rules/*.md` files scope language, backend and frontend guidance by path.

Select the task-relevant existing skill or workflow. Core installation is intentionally limited; use `/retrieve <tier>` when additional capabilities are needed and available. Do not preload every agent, skill or reference.

For large searches or tool reads, filter/paginate at the source and use bounded deterministic code for mechanical work when the environment supports it. Preserve needed results, errors and truncation indicators; never silently discard evidence or change native permissions. Measure actual task quality/context before adopting a more complex runtime.
