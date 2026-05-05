---
project: "2026-05-03-service-methods-layer4"
date: "2026-05-04"
---

# Reflection — Phase 8a Layer 4: Service Methods + Polygon Migration

## Session Summary

3-MEU project (MEU-195/190/191) implementing Phase 8a Layer 4 service methods and Polygon → Massive migration. Core TDD cycle (tasks 3–16) completed cleanly in first session. Second session (ad-hoc) addressed live user testing — Massive API 403 errors drove discovery of auth method mismatch (bearer → query param), free-tier test endpoint limitation, and display name requirements.

## Lessons Learned

1. **Provider auth methods must be verified empirically**: The original Polygon.io config used `BEARER_HEADER` which was never tested against the live API. Massive's documented auth is `QUERY_PARAM` — switching resolved the 403.

2. **Test endpoints must work on all subscription tiers**: The `/aggs/ticker/AAPL/prev` endpoint requires a paid plan. Switching to `/v3/reference/tickers?limit=1` works on free tier.

3. **URL template placeholders are easy to miss**: The `{api_key}` placeholder in the test endpoint is essential for `QUERY_PARAM` auth. Without it, the `.format(api_key=...)` call has no effect and the request goes unauthenticated.

4. **Base URL version prefixes can cause double-stacking**: When the base URL included `/v2` and the URL builder also prepended `/v2/`, the result was `/v2/v2/aggs/...`. Removing the version from base URL and adding it to each builder path was the correct fix.

5. **Display name vs internal key separation is a common pattern**: Adding `display_name` to the DTO rather than renaming the key preserves backward compat with DB entries, encrypted key storage, and API paths.

## Instruction Coverage

```yaml
schema: v1
session:
  id: 929dd479-311f-4dce-9f28-e36cb5e9c1c9
  task_class: tdd
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 9
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 2
  - id: session_discipline
    cited: true
    influence: 2
  - id: operating_model
    cited: true
    influence: 1
loaded:
  workflows: [execution_session, create_plan, issue_triage]
  roles: [coder, tester, reviewer]
  skills: [terminal_preflight]
  refs: [provider_registry.py, url_builders.py, provider_connection_service.py, MarketDataProvidersPage.tsx]
decisive_rules:
  - "P0:redirect-to-file-pattern"
  - "P1:tests-first-implementation-after"
  - "P1:never-modify-tests-to-pass"
  - "P1:anti-premature-stop"
  - "P2:evidence-first-completion"
conflicts: []
note: "Ad-hoc user-driven testing revealed auth configuration gaps that TDD alone would not have caught — live API validation is essential for provider integrations."
```
