---
paths:
  - '**/*.{ts,tsx,js,jsx,mjs,cjs,cs,rs,py}'
---

# Architecture defaults

Follow the project's chosen architecture and keep each change in the relevant vertical slice. UI, HTTP and CLI boundaries parse/validate input, delegate application work and map results. Keep business rules out of transport and presentation code; isolate database/provider access behind the existing adapters.

Domain code should not depend on UI or concrete infrastructure. Adapters implement the domain/application contracts. Inspect existing boundaries before adding abstractions; a small project does not need an invented repository/service layer for every operation. Propose only refactors that materially help the authorized task.
