# Phase 8a Session Reflection — MEU-207 + Ad-Hoc Pipeline Hardening

**Date**: 2026-05-05/06
**Session**: MEU-207 execution (TDD cycle + post-MEU deliverables) + ad-hoc pipeline hardening
**Duration**: ~25 turns (across 2 sessions)

---

## What Went Well

1. **Registry-first principle** was the correct design call. Mechanically deriving capability tuples from the 4 normalizer registries (`NORMALIZERS`, `QUOTE_NORMALIZERS`, `NEWS_NORMALIZERS`, `SEARCH_NORMALIZERS`) eliminated all ambiguity about which providers support which data types.

2. **Clean TDD cycle**: 19 tests written → 13 failed (RED) → 2 production files changed → 19 passed (GREEN) → 2699 full suite pass. Zero test modifications during GREEN phase.

3. **Plan correction rounds** (9 iterations) caught a subtle contract error: the plan initially advertised capability tuples from the research consensus matrix, which did not match what the runtime normalizers actually support. The iterative correction process eliminated this drift before any code was written.

4. **Live pipeline testing uncovered 6 production bugs** (AH-1 through AH-6) that unit tests alone could not catch — including cross-layer issues like the API key name mismatch (registry key vs display name) and the Alpaca validator-endpoint schema mismatch. These were promptly fixed and documented.

## What Went Poorly

1. **Previous session's handoff quality** — The MEU-192/193/194 handoff was minimal (89 lines, no design rationale, no detailed FAIL_TO_PASS evidence). This violated the evidence-first completion rule and required a full rewrite.

2. **MEU-207 was identified late** — Capability contract drift should have been caught during MEU-184 (when provider_capabilities.py was first created). The gap between "spec-derived" and "normalizer-derived" capabilities was only noticed during post-implementation user review.

3. **Ad-hoc fixes were not immediately documented** — Six production hardening fixes were done reactively during pipeline testing but were not tracked in task.md or the plan until explicit review. This created a documentation gap.

4. **Alpaca validator mismatch** (AH-4) was a spec-vs-runtime mismatch that existed since the original provider connection service was built. The test endpoint (`/v2/stocks/AAPL/snapshot`) and the validator schema (`{"id": "..."}`) were never cross-referenced.

## Technical Decisions

### AC-2: Capability Tuple Derivation Method

For each of the 8 normalizer-backed providers, I mechanically checked all 4 registries:

| Registry | Keys/Values checked | Result |
|----------|-------------------|--------|
| `NORMALIZERS` | `data_type → {provider: normalizer_fn}` | Mapped to `supported_data_types` |
| `QUOTE_NORMALIZERS` | `provider → normalizer_fn` | Provider gets `quote` |
| `NEWS_NORMALIZERS` | `provider → normalizer_fn` | Provider gets `news` |
| `SEARCH_NORMALIZERS` | `provider → normalizer_fn` | Provider gets `ticker_search` |

### AH-3: API Key Lookup Architecture

The Polygon.io → Massive rebrand exposed a latent architecture issue: `config.name` (display name) vs registry key (storage key) were conflated. The fix passes the registry key explicitly through the adapter methods, establishing a clean separation between UI-facing names and internal lookup keys.

### AH-4: Validator-Endpoint Alignment

The root cause was that the Alpaca `test_endpoint` points to the Market Data API (`data.alpaca.markets/v2/stocks/AAPL/snapshot`) while the validator was written for the Trading API (`api.alpaca.markets/v2/account`). These return completely different JSON schemas. The fix aligns the validator with the actual test endpoint.

### Three carry-forward providers (unchanged from MEU-184)

- **Nasdaq Data Link**: `("fundamentals",)` — no normalizer registry entry
- **OpenFIGI**: `("identifier_mapping",)` — structural POST-body resolver
- **Tradier**: `("ohlcv", "quote")` — no normalizer registry entry

---

## Instruction Coverage Reflection

```yaml
schema: v1
session:
  id: 6e344715-8f31-4ad5-9153-50b36a95c5ba
  task_class: debug
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 25
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 3
  - id: session_discipline
    cited: true
    influence: 2
  - id: planning_contract
    cited: true
    influence: 2
  - id: communication_policy
    cited: true
    influence: 1
loaded:
  workflows: [execution_session]
  roles: [coder, tester, reviewer]
  skills: [terminal_preflight, quality_gate, completion_preflight]
  refs:
    - docs/execution/plans/2026-05-05-api-surface-pipeline-automation/implementation-plan.md
    - docs/execution/plans/2026-05-05-api-surface-pipeline-automation/task.md
    - .agent/schemas/reflection.v1.yaml
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:redirect-to-file-pattern"
  - "P1:evidence-first-completion"
  - "P2:anti-premature-stop"
  - "P1:no-deferral-rule"
conflicts: []
note: "Ad-hoc pipeline testing surfaced 6 production bugs that unit tests missed — live integration testing remains essential for cross-layer issues."
```

---

🕐 Updated: 2026-05-06T09:15 (EDT)
