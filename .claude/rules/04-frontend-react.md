---
paths:
  - '**/*.tsx'
  - '**/*.jsx'
---

# React

Use the project's framework and data layer. Pages compose features; reusable UI presents typed state. Keep server data in the existing query/loader layer and local UI state near its owner. Extract shared behavior when it has a real caller; avoid a parallel cache or state store.

Preserve loading, empty, error and success states, accessible interactions and responsive behavior. Measure before adding memoization. Inspect positioning/stacking/scroll context before changing sticky, fixed or overlay behavior. Verify affected visual states in a browser when the task changes their behavior; respect the project's visual quality target.
