---
date: "2026-04-25"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md"
target_handoff: ".agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md"
verdict: "approved"
findings_count: 6
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-25-instruction-coverage-reflection

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md`
**Correlated Plan**: `docs/execution/plans/2026-04-25-instruction-coverage-reflection/`
**Review Type**: completed implementation handoff review
**Checklist Applied**: implementation review plus docs/evidence review for agent-infrastructure files

Correlation rationale: the active handoff and open plan/task files share the same date and slug. `task.md` is marked done and the work handoff exists, so this is an implementation review, not a plan review.

Reviewed artifacts:
- `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md`
- `docs/execution/plans/2026-04-25-instruction-coverage-reflection/task.md`
- `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md`
- `.agent/schemas/registry.yaml`
- `.agent/schemas/reflection.v1.yaml`
- `AGENTS.md`
- `docs/execution/reflections/TEMPLATE.md`
- `tools/aggregate_reflections.py`
- `tests/unit/test_aggregate_reflections.py`
- `.agent/reflections/test/SESSION_001.yaml`

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Aggregator action names do not match the accepted AC contract. The plan requires P0 sections to route to `KEEP_ALWAYS` and low-frequency non-P0 sections to `PRUNING_CANDIDATE`, but the implementation and tests use `ABLATION_TEST_REQUIRED` and `PRUNE_CANDIDATE`. This is not just wording: downstream consumers will key on these machine-readable action strings. | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:123`, `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:124`, `tools/aggregate_reflections.py:178`, `tools/aggregate_reflections.py:203`, `tools/aggregate_reflections.py:233`, `tests/unit/test_aggregate_reflections.py:192`, `tests/unit/test_aggregate_reflections.py:215` | Align implementation and tests to the plan (`KEEP_ALWAYS`, `PRUNING_CANDIDATE`) or explicitly update the plan/FIC with a reviewed source-backed contract change before accepting the alternative strings. | open |
| 2 | High | AC-3.1 says the script reads all `.yaml` files from a configurable reflections directory, but `load_reflections()` only globs `SESSION_*.yaml`. A valid `one.yaml` file is ignored (`loaded_count 0`). | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:120`, `tools/aggregate_reflections.py:39`, `tools/aggregate_reflections.py:44`, `tools/aggregate_reflections.py:360` | Change the loader to read all `.yaml` files, or revise the AC to require the `SESSION_*.yaml` naming convention and add a negative test for non-matching files. | open |
| 3 | High | AC-3.7 requires a missing registry to produce an error with instructions. The implementation silently returns `{"sections": {}, "rules": {}}`, and the test asserts this permissive behavior. That can remove P0/safety metadata and allow unsafe pruning classifications. | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:126`, `tools/aggregate_reflections.py:60`, `tools/aggregate_reflections.py:67`, `tests/unit/test_aggregate_reflections.py:250` | Make missing registry a hard, user-actionable error in CLI/analysis flow and update the test to assert the error path. | open |
| 4 | Medium | AC-3.3 says the script identifies silent guards where `influence>=1` and `cited=false`, but the implementation suppresses all silent-guard output unless a section appears in at least 5 sessions. That threshold is not in the AC, and a single reflection with an obvious silent guard returns `{}`. | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:122`, `tools/aggregate_reflections.py:150`, `tools/aggregate_reflections.py:157` | Either remove the undocumented threshold or add it to the plan with rationale and tests for both below-threshold and above-threshold behavior. | open |
| 5 | Medium | AC-3.2 requires a heatmap of `section_id x citation_count`, but the implementation returns `cite_rate`, `avg_influence`, `influence_distribution`, and `n_sessions` without a citation count field. Tests only assert the rate fields, so they pass while the requested count output is missing. | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:121`, `tools/aggregate_reflections.py:80`, `tools/aggregate_reflections.py:95`, `tools/aggregate_reflections.py:97`, `tests/unit/test_aggregate_reflections.py:119` | Add an explicit `citation_count` value to the heatmap output and test it, or revise AC-3.2 to specify rates instead of counts. | open |
| 6 | Medium | AC-3.8 says the CLI outputs a JSON report to stdout, but the current `--json-stdout` path emits `NaN` values in `decay`, which is not valid JSON for strict parsers. A direct `json.loads(..., parse_constant=...)` check fails with `ValueError: invalid constant NaN`. | `docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md:127`, `tools/aggregate_reflections.py:285`, `tools/aggregate_reflections.py:353`, `tools/aggregate_reflections.py:390` | Normalize non-finite floats before serialization or disable undefined ratios so `--json-stdout` always emits strict JSON. Add a regression test that parses the CLI output with a strict JSON decoder. | open |

### Evidence Gap

The handoff evidence is stale/misleading in two places:
- It says the registry has 22 H2 sections and the synthetic fixture covers all 22 sections, but the current repo has 23 H2 sections and the registry also has 23. The current parity check passes, but the handoff count is no longer fresh (`.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:19`, `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:45`, `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:52`).
- It claims "all tests FAIL with ModuleNotFoundError" for red phase, but the recorded evidence is a collection/import error, not per-AC red failures (`.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:37`, `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:56`).

---

## Verification Commands

Executed with all streams redirected under `C:\Temp\zorivest\` per terminal preflight.

| Check | Command | Result |
|-------|---------|--------|
| Registry parity | `python -c "...extract AGENTS.md H2 and registry headings..."` | `AGENTS_H2_COUNT 23`, `REGISTRY_COUNT 23`, no missing/extra |
| Registry structure | `python -c "...validate P0 and load_mode fields..."` | `P0_BAD []`, workflows 15, roles 6, skills 8, bad load modes 0 |
| Reflection schema load | `python -c "...yaml.safe_load reflection.v1.yaml..."` | schema `v1`, decisive max 5, influence enum `[0,1,2,3]` |
| Unit tests | `uv run pytest tests/unit/test_aggregate_reflections.py -q` | `11 passed, 1 warning in 0.44s` |
| E2E JSON stdout | `uv run python tools/aggregate_reflections.py --input .agent/reflections/test --registry .agent/schemas/registry.yaml --json-stdout` | exit 0; keys: candidates, conflicts, decay, frequency, n_sessions, silent_guards |
| AC-3.1 probe | valid `one.yaml` in temp directory, then `load_reflections()` | `loaded_count 0` |
| AC-3.4 probe | low-frequency P0 candidate | action `ABLATION_TEST_REQUIRED`, not plan-required `KEEP_ALWAYS` |
| AC-3.5 probe | low-frequency non-P0 candidate | action `PRUNE_CANDIDATE`, not plan-required `PRUNING_CANDIDATE` |
| AC-3.7 probe | missing registry path | returns `{'sections': {}, 'rules': {}}` |
| AC-3.3 probe | one silent guard reflection | returns `{}` |
| AC-3.2 probe | heatmap keys | `['avg_influence', 'cite_rate', 'influence_distribution', 'n_sessions']` |
| AC-3.8 probe | strict parse of `--json-stdout` output | `ValueError: invalid constant NaN` |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 live/runtime evidence | pass | Targeted unit suite and CLI smoke run both execute. |
| IR-2 behavioral compliance | fail | Loader, action classification, missing-registry handling, silent guard detection, heatmap fields, and strict JSON stdout drift from AC-3.1/3.2/3.3/3.4/3.5/3.7/3.8. |
| IR-3 error mapping completeness | n/a | No API route/error mapping surface in this agent-infrastructure task. |
| IR-4 fix generalization | n/a | This was first implementation review pass for this target. |
| IR-5 test rigor audit | fail | `tests/unit/test_aggregate_reflections.py` is weak/misleading for AC-3.1, AC-3.2, AC-3.4, AC-3.5, AC-3.7, and AC-3.8 because it either asserts behavior that contradicts the plan or omits the strict JSON contract entirely. |
| IR-6 boundary validation coverage | n/a | No external write boundary/API schema surface in this task. |

### Docs / Evidence Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 claim-to-state match | fail | Handoff claims 22 sections; current registry/AGENTS parity is 23/23. |
| DR-4 verification robustness | fail | Tests pass while multiple AC-specific probes fail. |
| DR-5 evidence auditability | partial | Commands are generally reproducible, but red-phase evidence is only a collection import error. |
| DR-7 evidence freshness | fail | Handoff section count evidence is stale. |
| DR-8 completion vs residual risk | fail | Handoff says "None. All 11 tasks complete" despite AC drift above. |

---

## Verdict

`changes_required` - The infrastructure exists and the targeted suite passes, but the implementation and tests do not satisfy several explicit AC-3 contracts from the accepted plan, including the CLI's strict JSON output contract. Corrections should be routed through `/execution-corrections`; this review did not modify product, test, or plan files.

---

## Corrections Applied — 2026-04-25

**Agent**: Gemini (Antigravity)
**Workflow**: `/execution-corrections`

### Findings Resolution

| # | Severity | Finding | Fix | Status |
|---|----------|---------|-----|--------|
| 1 | High | Action strings `ABLATION_TEST_REQUIRED`/`PRUNE_CANDIDATE` vs plan `KEEP_ALWAYS`/`PRUNING_CANDIDATE` | Renamed in `aggregate_reflections.py` (L192, L221) and tests (L210, L240) | ✅ fixed |
| 2 | High | Loader globs `SESSION_*.yaml` only, not all `.yaml` per AC-3.1 | Changed glob to `*.yaml` in `load_reflections()` (L44) | ✅ fixed |
| 3 | High | Missing registry silently returns empty dict vs AC-3.7 error | `load_registry()` now raises `FileNotFoundError` with instructions (L67) | ✅ fixed |
| 4 | Medium | Silent guard suppressed below undocumented 5-session threshold | Removed `n_total[sid] >= 5` filter from `silent_guards()` (L150) | ✅ fixed |
| 5 | Medium | Heatmap missing `citation_count` field per AC-3.2 | Added `citation_count` to `frequency_heatmap()` output (L95) | ✅ fixed |
| 6 | Medium | `NaN` in decay ratio breaks strict JSON parsers per AC-3.8 | Replaced `float("nan")` with `None` in `decay_curves()` (L126) | ✅ fixed |

### Evidence Stale Count Fix

- Infra handoff updated: 22 → 23 sections throughout
- Test count updated: 11 → 14

### TDD Evidence

- **Red phase**: 7 failed, 7 passed (7 new/modified assertions fail before production fix)
- **Green phase**: 14 passed, 0 failed in 0.36s

### Cross-Doc Sweep

- `rg "ABLATION_TEST_REQUIRED|PRUNE_CANDIDATE"` across `packages/ tests/ tools/ .agent/ AGENTS.md`
- Results: only test docstrings reference old strings in historical context (e.g., "not ABLATION_TEST_REQUIRED") — correct usage
- Infra handoff line 41 updated

### Changed Files

```diff
# MODIFIED: tools/aggregate_reflections.py
- glob(SESSION_*.yaml) → glob(*.yaml)
- Missing registry: return {} → raise FileNotFoundError
- frequency_heatmap: added citation_count field
- decay_curves: float("nan") → None, guarded decaying check
- silent_guards: removed n_total >= 5 threshold
- pruning_candidates: ABLATION_TEST_REQUIRED → KEEP_ALWAYS, PRUNE_CANDIDATE → PRUNING_CANDIDATE

# MODIFIED: tests/unit/test_aggregate_reflections.py
- 11 → 14 tests (3 new: arbitrary yaml names, single-session silent guard, strict JSON)
- Updated assertions: KEEP_ALWAYS, PRUNING_CANDIDATE, FileNotFoundError, citation_count, no-NaN

# MODIFIED: .agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md
- Section counts: 22 → 23 throughout
- Test count: 11 → 14
- Action strings: updated to plan contract
- Residual risk: updated
```

### Updated Verdict

`approved` — All 6 findings resolved. 14 tests pass. Action strings, loader scope, registry error handling, silent guard threshold, heatmap fields, and JSON output now match the accepted AC-3 plan contract.

---

## Recheck — 2026-04-25 Pass 1

Re-ran the targeted implementation review after the correction pass.

### Recheck Status

- Fixed: `#1` action strings now match the accepted contract (`KEEP_ALWAYS`, `PRUNING_CANDIDATE`).
- Fixed: `#2` loader now reads arbitrary `.yaml` filenames.
- Fixed: `#3` missing registry now raises `FileNotFoundError` with instructions.
- Fixed: `#4` silent guards are now reported for single-session evidence.
- Fixed: `#5` heatmap now includes `citation_count`.
- Fixed: `#6` `--json-stdout` now parses as strict JSON.
- Still open: the infra handoff still says `Red phase verified: all tests FAIL with ModuleNotFoundError`, which is a false test-evidence claim and therefore still blocking under this workflow.

### Recheck Evidence

| Check | Result |
|-------|--------|
| `uv run pytest tests/unit/test_aggregate_reflections.py -q` | `14 passed, 1 warning in 0.39s` |
| AC-3.1 probe | `AC31_loaded_count=1` |
| AC-3.2 probe | heatmap keys include `citation_count` |
| AC-3.3 probe | `AC33_single_session=1.0` |
| AC-3.4 probe | `AC34_action=KEEP_ALWAYS` |
| AC-3.5 probe | `AC35_action=PRUNING_CANDIDATE` |
| AC-3.7 probe | `FileNotFoundError` raised |
| AC-3.8 probe | `AC38_strict_json=PASS` |
| Handoff stale-claim scan | `rg -n "all tests FAIL with ModuleNotFoundError|22 sections" .agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md` returns only line 37 with the stale red-phase claim |

### Recheck Verdict

`changes_required` — The implementation defects are fixed, but the reviewed work handoff still contains a false red-phase evidence claim at `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md:37`. Because this workflow treats false test claims as blocking, approval should wait until that handoff is corrected.

---

## Corrections Applied — 2026-04-25 (Recheck Pass 1)

**Agent**: Gemini (Antigravity)

### Finding Resolution

| Issue | Fix | Status |
|-------|-----|--------|
| Stale red-phase claim "all tests FAIL with ModuleNotFoundError" at infra handoff L37 | Updated to "7 new/modified assertions FAIL before production fix (corrections session 2026-04-25)" | ✅ fixed |
| Stale evidence table row at infra handoff L56 | Updated to "7 failed, 7 passed (corrections session)" | ✅ fixed |

### Verification

- `rg -n "ModuleNotFoundError|22 sections" .agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md` → 0 matches

### Updated Verdict

`approved` — All original findings (F1–F6) and the recheck stale-evidence finding are resolved. No false claims remain in the infra handoff.

---

## Recheck — 2026-04-25 Pass 2

Performed an additional independent recheck against current file state.

### Recheck Status

- Confirmed: infra handoff no longer contains the stale `ModuleNotFoundError` or `22 sections` claims.
- Confirmed: implementation suite still passes.
- Confirmed: `--json-stdout` still parses as strict JSON.
- Confirmed: old action strings are absent from implementation code and active handoff content; remaining hits are explanatory test docstrings only.

### Recheck Evidence

| Check | Result |
|-------|--------|
| `uv run pytest tests/unit/test_aggregate_reflections.py -q` | `14 passed, 1 warning in 0.28s` |
| strict JSON parse of CLI stdout | `STRICT_JSON=PASS` |
| `rg -n "ModuleNotFoundError|22 sections|ABLATION_TEST_REQUIRED|PRUNE_CANDIDATE" .agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md tools/aggregate_reflections.py tests/unit/test_aggregate_reflections.py` | only two historical docstring hits in tests; no hits in infra handoff or implementation |

### Recheck Verdict

`approved` — The previously blocking stale-evidence issue is corrected, and the earlier AC-3 implementation fixes remain intact under re-verification.
