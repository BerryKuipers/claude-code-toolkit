---
paths:
  - '**/repositories/**/*.{ts,js}'
  - '**/infra/db/**/*'
  - '**/infrastructure/database/**/*'
  - '**/data-access/**/*'
  - '**/persistence/**/*'
  - '**/migrations/**/*'
---

# Persistence

Keep database access in the existing persistence boundary and return the domain/application contract rather than leaking ORM details. Use parameterized queries, explicit not-found behavior and transactions when several writes form one operation. Preserve the project's mappings, isolation, idempotency and recovery guarantees.

Verify the actual database target before migrations, seeds or destructive operations. Preserve user data and credentials and use the project's disposable test database for automated tests. Keep small-app tradeoffs explicit; introduce mapping/interfaces when they protect a real boundary, not as boilerplate.
