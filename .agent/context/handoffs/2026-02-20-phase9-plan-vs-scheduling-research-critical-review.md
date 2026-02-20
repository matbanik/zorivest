# Critical Review: Phase 9 Plan vs Scheduling Research

## Scope
- Reviewed handoff plan: `.agent/context/handoffs/2026-02-19-phase9-build-plan.md`
- Reviewed research baseline: `_inspiration/scheduling_research/` (roadmap + composite syntheses)
- Reviewed implementation plan artifact: `docs/build-plan/09-scheduling.md` and linked contracts

## Findings (Severity-Ordered)

### Critical
- MCP contract is internally broken for schedule updates.
  Evidence: `docs/build-plan/09-scheduling.md:2377` (`PolicyResponse` does not expose `policy_json`) vs `docs/build-plan/09-scheduling.md:2662` (MCP tool parses `current.policy_json`).
  Impact: `update_policy_schedule` cannot safely round-trip policy content and can corrupt updates.
  Fix: Add a dedicated schedule-patch endpoint (`PATCH /scheduling/policies/{id}/schedule`) or include canonical policy payload in a separate read model.

- MCP tools/resources call REST endpoints that are not defined in the same plan.
  Evidence: `docs/build-plan/09-scheduling.md:2690` (`/scheduling/runs?limit=`), `docs/build-plan/09-scheduling.md:2710` (`/scheduling/policies/schema`), `docs/build-plan/09-scheduling.md:2721` (`/scheduling/step-types`) while declared routes are only at `docs/build-plan/09-scheduling.md:2488`, `docs/build-plan/09-scheduling.md:2504`, `docs/build-plan/09-scheduling.md:2514`, `docs/build-plan/09-scheduling.md:2523`, `docs/build-plan/09-scheduling.md:2531`.
  Impact: MCP surface cannot be implemented without undocumented API expansion.
  Fix: Either add the missing REST routes to Step 9.10 or remove these MCP calls and keep tools/resources aligned to existing endpoints.

- Resume/replay design is inconsistent with persistence model.
  Evidence: `docs/build-plan/09-scheduling.md:495` (`pipeline_runs.policy_id` FK to `policies.id`) vs runtime creation using name `docs/build-plan/09-scheduling.md:869`; resume load uses current run id `docs/build-plan/09-scheduling.md:889`.
  Impact: foreign-key drift risk and resume-from-failure cannot reliably load prior outputs.
  Fix: pass canonical `policy.id` into runner and make resume target explicit (`resume_run_id` + `resume_from_step_id`).

- SQL safety posture is contradicted by dynamic SQL construction in write paths.
  Evidence: `docs/build-plan/09-scheduling.md:1807`, `docs/build-plan/09-scheduling.md:1818`, `docs/build-plan/09-scheduling.md:1820`.
  Impact: policy-authored table/column values can become SQL injection vectors.
  Fix: enforce strict table/column allowlists and use SQLAlchemy expression API (not f-string SQL for identifiers/values).

### High
- Cron validator rejects valid cron syntax such as `*/5`.
  Evidence: `docs/build-plan/09-scheduling.md:377`, `docs/build-plan/09-scheduling.md:420`.
  Impact: valid schedules will be rejected.
  Fix: use `apscheduler` parser validation directly or replace regex with tested cron parser rules.

- SQL blocklist check is shallow and bypassable.
  Evidence: `docs/build-plan/09-scheduling.md:461`, `docs/build-plan/09-scheduling.md:464`.
  Impact: nested SQL strings in `data_queries` can bypass validation.
  Fix: recursively scan nested params or remove blocklist dependence and rely on authorizer + query-only + strict query source controls.

- Prior handoff verdict materially underestimates risk.
  Evidence: `.agent/context/handoffs/2026-02-19-phase9-build-plan.md:56`, `.agent/context/handoffs/2026-02-19-phase9-build-plan.md:58`.
  Impact: "none blocking" is not defensible against current contract defects.
  Fix: re-open review gate and require adversarial API/MCP contract audit before implementation.

### Medium
- Research-recommended phased rollout (9A-9D with early parallelization) is not preserved as execution gates.
  Evidence: `_inspiration/scheduling_research/scheduling-integration-roadmap.md:30`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:65`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:83`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:105`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:167` vs monolithic prerequisite block `docs/build-plan/09-scheduling.md:3`.
  Impact: harder incremental delivery and weaker test gate boundaries.
  Fix: split Step 9 execution into explicit sub-phase gates with per-gate entry/exit criteria.

## Where The Plan Correctly Matches Research
- `ref`-object data reference style is adopted (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:42`, `docs/build-plan/09-scheduling.md:104`).
- `skip_if` is used as v1 branching model (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:43`, `docs/build-plan/09-scheduling.md:147`).
- Registry-first model and `__init_subclass__` auto-registration are adopted (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:45`, `docs/build-plan/09-scheduling.md:249`, `docs/build-plan/09-scheduling.md:304`).
- Step version is registry-side, not policy-side (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:44`; no policy `type_version` field in `docs/build-plan/09-scheduling.md:141`).
- `dlt` runtime dependency is avoided (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:54`; no runtime `dlt` in `docs/build-plan/09-scheduling.md`).
- WeasyPrint + SQLCipher APScheduler persistence + `httpx` align with locked decisions (`_inspiration/scheduling_research/scheduling-integration-roadmap.md:55`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:56`, `_inspiration/scheduling_research/scheduling-integration-roadmap.md:59`; `docs/build-plan/09-scheduling.md:2118`, `docs/build-plan/09-scheduling.md:1149`, `docs/build-plan/09-scheduling.md:1504`).

## What I Would Do Differently
- Add a REST↔MCP contract table that is test-checked in docs (every MCP call must map to declared route).
- Introduce explicit 9A/9B/9C/9D gates in `09-scheduling.md` with separate exit criteria per gate.
- Add an "adversarial policy payload" test section for SQL injection, schedule abuse, and malformed ref chains before any implementation starts.

## Verdict
- The strategic direction is strong and mostly aligned with research.
- The current detailed plan is not implementation-ready due to contract and safety defects marked Critical/High.

