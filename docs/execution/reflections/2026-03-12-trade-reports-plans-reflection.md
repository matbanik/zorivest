# Reflection — Trade Reports & Plans (MEU-53, MEU-66, MEU-67)

**Date:** 2026-03-12
**MEUs:** MEU-53 (TradeReport MCP tools), MEU-66 (TradePlan entity+service+API), MEU-67 (Plan↔Trade linking)

## What Went Well

- **TDD discipline held**: RED→GREEN→REFACTOR cycle followed for all 3 MEUs. Entity tests written first, then service, then API.
- **Cross-surface awareness**: MCP `create_trade_plan` payload uses compact field names (`entry/stop/target/conditions`) — caught during critical review and resolved with `model_validator` alias mapping.
- **Dedup pattern**: Added duplicate active-plan rejection (409) — a real-world concern that the critical review surfaced. Pattern can be reused for watchlists.

## What Could Be Improved

- **Canon URL drift**: Implemented `/api/v1/plans` instead of canonical `/api/v1/trade-plans`. Root cause: the 04a spec reference in the implementation plan docstring was ambiguous. Lesson: always grep canon docs for the URL pattern before coding the router prefix.
- **Linking route gap**: `link_plan_to_trade()` service method was implemented but not routed from API — PUT used `update_plan()` which bypassed trade-exists validation. Lesson: when adding validation logic to service methods, verify the API layer actually calls them.
- **Closeout tracking lag**: BUILD_PLAN.md summary counts and MEU status rows fell behind. Lesson: update tracking artifacts atomically with code changes, not as a separate pass.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `model_validator` for MCP aliases | Cleaner than Pydantic `Field(alias=...)` — allows both short and long names without breaking existing clients |
| Dedup via `list_all` scan | Simple for current scale; can optimize with a `get_active_for_ticker` repo query when plan volume grows |
| PATCH `/status` endpoint | Canonical (gui-actions-index.md 5.4) — separates status transitions from general field updates |
| DELETE endpoint | Canonical (gui-actions-index.md 5.3) — needed for plan lifecycle management |

## Test Coverage

| Suite | Count | Scope |
|-------|-------|-------|
| test_entities.py | 10 | TradePlan dataclass + compute_risk_reward |
| test_report_service.py | 24 | Plan CRUD + linking + dedup + delete |
| test_api_plans.py | 20 | REST endpoints + MCP compat + real-wiring |
| test_repositories.py | 5 | SqlAlchemy repo integration |
| analytics-tools.test.ts | 15 | MCP create_report + get_report_for_trade |
| Full regression | 974 + 150 | Python + TypeScript |

## Codex Review Stats

- **Rounds:** 3 (initial review + recheck + recheck 2)
- **Findings:** 2 High + 2 Medium → all resolved
- **Final verdict:** `approved`
