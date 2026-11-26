---
paths:
  - '**/*.{ts,tsx,js,jsx,mjs,cjs}'
---

# TypeScript and JavaScript

Match the repository's existing conventions. Default to single quotes, async/await and strict types. Use explicit public API contracts and infer ordinary local values. Validate external input, preserve typed errors and expose real failures; do not use casts or fallback data to hide a broken contract.

Keep the diff focused: no unrelated formatting, logging, comments or type annotations. Run the relevant typecheck and behavior tests after code changes, including affected callers and composite-project references. Do not report an unrelated baseline failure as either fixed or caused by the patch without evidence.
