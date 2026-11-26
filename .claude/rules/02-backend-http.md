---
paths:
  - '**/routes/**/*.{ts,js}'
  - '**/controllers/**/*.{ts,js}'
  - '**/handlers/**/*.{ts,js}'
  - '**/api/**/*.{ts,js}'
---

# HTTP boundaries

Use the existing route/service boundary. Validate request input and authorization, call application behavior, map safe DTOs/status codes and use centralized typed error handling. Do not leak database models, credentials or internal flags into responses. Keep business calculations, transactions and provider orchestration in the appropriate application/adapters layer.

Respect documented health-check, API-proxy or small single-layer exceptions already chosen by the project. An architectural default does not create a new permission gate or justify an unrelated rewrite.
