---
date: "2026-04-13"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex (GPT-5.4)"
---

# Critical Review: 2026-04-14-market-data-schemas

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md`  
**Review Type**: handoff review  
**Checklist Applied**: IR + DR

### Correlation Rationale

- The user supplied an explicit PW3 work handoff, so this was reviewed in implementation mode rather than auto-discovery mode.
- The handoff correlates directly to `docs/execution/plans/2026-04-14-market-data-schemas/` by matching date + slug.
- No sibling PW3 work handoffs were present, so scope stayed single-handoff plus the correlated plan, changed source/tests, and shared closeout artifacts (`docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `docs/execution/metrics.md`, `docs/execution/reflections/2026-04-14-market-data-schemas-reflection.md`, `.agent/context/current-focus.md`).

### Commands Executed

```powershell
git status --short *> C:\Temp\zorivest\git-status.txt
git diff -- packages/core/src/zorivest_core/services/validation_gate.py packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py tests/unit/test_market_data_models.py tests/unit/test_validation_schemas.py tests/unit/test_field_mappings.py tests/unit/test_models.py docs/BUILD_PLAN.md docs/execution/reflections/2026-04-14-market-data-schemas-reflection.md docs/execution/metrics.md .agent/context/current-focus.md .agent/context/meu-registry.md *> C:\Temp\zorivest\git-diff-pw3.txt
uv run pytest tests/unit/test_market_data_models.py tests/unit/test_validation_schemas.py tests/unit/test_field_mappings.py tests/unit/test_models.py tests/unit/test_transform_step.py tests/unit/test_db_write_adapter.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw3-review.txt
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-pw3-review.txt
@'
import pandas as pd
from zorivest_core.services.validation_gate import validate_dataframe

quote_df = pd.DataFrame([{'ticker': 'AAPL', 'last': None}])
print(validate_dataframe(quote_df, schema_name='quote'))

fund_df = pd.DataFrame([{'ticker': 'AAPL', 'metric': 'pe_ratio', 'value': None, 'period': '2026-Q1'}])
print(validate_dataframe(fund_df, schema_name='fundamentals'))
'@ | uv run python - *> C:\Temp\zorivest\repro-validation-gaps.txt
@'
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from zorivest_infra.database.models import Base, MarketQuoteModel

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as session:
    ts = datetime(2026, 1, 15, 14, 30)
    session.add(MarketQuoteModel(ticker='AAPL', last=150.0, timestamp=ts, provider='polygon'))
    session.flush()
    session.add(MarketQuoteModel(ticker='AAPL', last=151.0, timestamp=ts, provider='polygon'))
    try:
        session.flush()
        print('duplicate_quote_flush=allowed')
    except IntegrityError:
        print('duplicate_quote_flush=integrity_error')
'@ | uv run python - *> C:\Temp\zorivest\repro-quote-unique.txt
```

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The new schema/model contracts are materially weaker than the approved PW3 plan. The plan requires quote `last`, `timestamp`, and `provider`; news `published_at`; and fundamentals `value` to be enforced as required fields. The implementation instead makes quote `last` nullable, omits quote `timestamp` and `provider` from `QUOTE_SCHEMA`, omits `published_at` from `NEWS_SCHEMA`, and makes fundamentals `value` nullable in both schema and ORM. Reproduced with the current code: a quote row containing only `ticker` + `last=None` and a fundamentals row with `value=None` both validate as fully valid. Current tests never assert those missing-field/null-field cases, so the gap ships green. | `docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:78-82,122-141`; `packages/core/src/zorivest_core/services/validation_gate.py:42-50,60-80,90-103`; `packages/infrastructure/src/zorivest_infra/database/models.py:661-668,700-706`; `tests/unit/test_validation_schemas.py:41-89,95-170`; `C:\Temp\zorivest\repro-validation-gaps.txt:1-2` | Tighten the ORM and Pandera definitions to the approved contract, then add negative tests for missing `timestamp`/`provider`/`published_at` and for `last=None` / `value=None`. | open |
| 2 | High | `MarketQuoteModel` introduces a uniqueness rule that the approved plan explicitly rejected. The plan says quotes are append-only snapshots and must have an index only, with no `UniqueConstraint`. The implementation adds `UniqueConstraint("ticker", "timestamp", "provider")`, and the repro shows a second quote snapshot at the same natural key raises `IntegrityError`. That changes runtime write semantics and can reject legitimate repeat snapshots even though the handoff presents quote support as complete. | `docs/execution/plans/2026-04-14-market-data-schemas/implementation-plan.md:78-82`; `packages/infrastructure/src/zorivest_infra/database/models.py:655-659`; `tests/unit/test_market_data_models.py:134-162,233-280`; `C:\Temp\zorivest\repro-quote-unique.txt:1` | Remove the quote uniqueness constraint or update the plan with a source-backed reason for deduping quote snapshots, then add a regression that proves the intended duplicate-snapshot behavior. | open |
| 3 | Medium | The work handoff does not satisfy the repo’s evidence-bundle contract and overstates closeout confidence. The MEU gate advisory reports the handoff is missing `Evidence/FAIL_TO_PASS`, `Pass-fail/Commands`, and `Commands/Codex Report`. The handoff still declares `Residual Risk: None` even though the two contract/runtime gaps above remain open. | `.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md:53-87`; `C:\Temp\zorivest\validate-pw3-review.txt:15-18` | Repair the handoff headings/content to match the validator’s required evidence sections, and do not claim zero residual risk until the contract gaps above are closed and revalidated. | open |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | The targeted suite is green (`103 passed`), but repros show invalid quote/fundamentals payloads still validate and duplicate quote snapshots still error at flush time. |
| IR-2 Stub behavioral compliance | pass | PW3 scope does not introduce new stub behavior or placeholder runtime branches. |
| IR-3 Error mapping completeness | n/a | PW3 does not add REST/MCP boundary handling. |
| IR-4 Fix generalization | fail | The implementation added schemas/models, but did not generalize the required-field/nullability contract across quote/news/fundamentals. |
| IR-5 Test rigor audit | fail | Current tests cover positive paths and some negatives, but miss the plan-critical nullability/required-field cases and quote duplicate-snapshot semantics. |
| IR-6 Boundary validation coverage | n/a | PW3 is internal pipeline schema work, not an external-input boundary MEU. |

### IR-5 Test Rigor Audit

| Test File | Rating | Evidence |
|-----------|--------|----------|
| `tests/unit/test_market_data_models.py` | Weak | Verifies quote columns exist and fundamentals insert, but never asserts quote duplicate-snapshot behavior or `last`/`value` non-null enforcement. |
| `tests/unit/test_validation_schemas.py` | Weak | Covers missing `ticker`, negative price, invalid URL, and invalid period, but never tests missing quote `timestamp`/`provider`, missing news `published_at`, or `last=None` / `value=None`. |
| `tests/unit/test_field_mappings.py` | Adequate | Mapping coverage is broad and matches the implemented tuple-key registry. |
| `tests/unit/test_models.py` | Adequate | Correctly catches table-count drift and schema creation regressions. |

### Docs / Evidence Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | The handoff says data quality is hardened and residual risk is `None`, but the approved required-field/nullability contract is not actually enforced. |
| DR-4 Verification robustness | fail | Passing tests do not exercise the missing required-field/null-field paths or quote duplicate behavior. |
| DR-7 Evidence freshness | pass | The cited MEU gate and targeted pytest results reproduced cleanly in this review pass. |
| PR Evidence bundle complete | fail | `validate_codebase.py --scope meu` reports the work handoff is missing required evidence sections. |

---

## Follow-Up Actions

1. Route fixes through `/planning-corrections`; do not patch product code from this review workflow.
2. Align `validation_gate.py` and the new ORM models with the approved PW3 nullability/required-field contract.
3. Decide quote duplicate-snapshot behavior explicitly, then make model + tests match that decision.
4. Repair the work handoff so the MEU gate sees `FAIL_TO_PASS`, command evidence, and `Codex Validation Report` in the expected shape.

---

## Verdict

`changes_required` — PW3 added the intended files and passes the current suite, but two runtime contract gaps remain: required fields/nullability are under-enforced, and quote persistence semantics diverge from the approved plan. The work handoff is also not evidence-complete by the repo’s own validator.

---

## Recheck (2026-04-13)

**Workflow**: `/critical-review-feedback` recheck
**Agent**: Codex (GPT-5.4)

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Schema/model required-field and nullability contract was under-enforced | open | ✅ Fixed |
| Quote persistence semantics contradicted the approved append-only plan | open | ✅ Fixed |
| Work handoff evidence bundle was incomplete | open | ✅ Fixed |

### Confirmed Fixes

- `QUOTE_SCHEMA` now requires `last`, `timestamp`, and `provider`; `NEWS_SCHEMA` now requires `published_at`; and `FUNDAMENTALS_SCHEMA` now requires `value`. See [validation_gate.py](/P:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py:42), [validation_gate.py](/P:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py:62), [validation_gate.py](/P:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py:93). The original negative repros now quarantine all four invalid payloads: `quote_null_last 0 1`, `quote_missing_timestamp 0 1`, `news_missing_published_at 0 1`, `fund_null_value 0 1` (`C:\\Temp\\zorivest\\recheck-pw3-validation-repros.txt:1-4`).
- `MarketQuoteModel` is now index-only with no uniqueness constraint, while `last` and fundamentals `value` are non-null at the ORM layer. See [models.py](/P:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py:655), [models.py](/P:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py:664), [models.py](/P:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py:702). The duplicate-quote repro now allows two snapshots at the same natural key (`duplicate_quote_count 2`) (`C:\\Temp\\zorivest\\recheck-pw3-quote-repro.txt:1`).
- The targeted regression tests were strengthened to cover the prior gaps: missing quote `timestamp`/`provider`, missing news `published_at`, null fundamentals `value`, ORM nullability, and append-only quote duplicates. See [test_validation_schemas.py](/P:/zorivest/tests/unit/test_validation_schemas.py:91), [test_validation_schemas.py](/P:/zorivest/tests/unit/test_validation_schemas.py:175), [test_market_data_models.py](/P:/zorivest/tests/unit/test_market_data_models.py:164), [test_market_data_models.py](/P:/zorivest/tests/unit/test_market_data_models.py:245), [test_market_data_models.py](/P:/zorivest/tests/unit/test_market_data_models.py:287).
- The work handoff now includes the validator-recognized evidence sections `FAIL_TO_PASS Evidence`, `Commands Executed`, and `Codex Validation Report`. See [115-2026-04-14-market-data-schemas-bp09s49.6.md](/P:/zorivest/.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md:53), [115-2026-04-14-market-data-schemas-bp09s49.6.md](/P:/zorivest/.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md:69), [115-2026-04-14-market-data-schemas-bp09s49.6.md](/P:/zorivest/.agent/context/handoffs/115-2026-04-14-market-data-schemas-bp09s49.6.md:85). The MEU gate now reports `All evidence fields present in 115-2026-04-14-market-data-schemas-bp09s49.6.md` (`C:\\Temp\\zorivest\\recheck-pw3-meu-gate.txt:15`).

### Verification

- Targeted suite: `75 passed, 2 warnings` (`C:\\Temp\\zorivest\\recheck-pw3-targeted.txt`)
- Regression suite: `36 passed, 2 warnings` (`C:\\Temp\\zorivest\\recheck-pw3-regression.txt`)
- MEU gate: `8/8` blocking checks passed; evidence bundle clean (`C:\\Temp\\zorivest\\recheck-pw3-meu-gate.txt`)

### Remaining Findings

- None.

### Verdict

`approved` — The three prior findings are closed. The schema/model contracts now match the approved PW3 plan, quote snapshots are append-only as specified, and the work handoff satisfies the repo’s evidence-bundle validator.

---

## Corrections Applied — 2026-04-14

### Findings Resolved

| # | Severity | Finding | Resolution | Verified |
|---|----------|---------|------------|----------|
| 1 | High | Schema/model nullability weaker than plan | Tightened `last`→not-null, `value`→not-null in both ORM and Pandera; added `timestamp`, `provider` to QUOTE_SCHEMA; added `published_at` to NEWS_SCHEMA; 5 negative schema tests + 2 ORM nullable tests added | ✅ 75 passed |
| 2 | High | Quote UniqueConstraint contradicts plan | Removed `UniqueConstraint` from `MarketQuoteModel`, kept index-only; replaced `test_ohlcv_duplicate_raises` → restored + added `test_quote_duplicate_snapshot_allowed` proving append-only works | ✅ 75 passed |
| 3 | Medium | Handoff missing evidence sections | Restructured with `FAIL_TO_PASS Evidence`, `Commands Executed`, `Codex Validation Report` headings matching validator regex patterns | ✅ A3 clean |

### Changes Made

```diff
# validation_gate.py
- "last": pa.Column(float, pa.Check.gt(0), nullable=True, coerce=True),
+ "last": pa.Column(float, pa.Check.gt(0), nullable=False, coerce=True),
+ "timestamp": pa.Column("datetime64[ns]", nullable=False, coerce=True),
+ "provider": pa.Column(str, nullable=False),
+ "published_at": pa.Column("datetime64[ns]", nullable=False, coerce=True),  # NEWS_SCHEMA
- "value": pa.Column(float, nullable=True, coerce=True),
+ "value": pa.Column(float, nullable=False, coerce=True),

# models.py
- UniqueConstraint("ticker", "timestamp", "provider", name="uq_quote_ticker_ts_provider"),
- last = Column(Numeric(15, 6), nullable=True)
+ last = Column(Numeric(15, 6), nullable=False)
- value = Column(Numeric(15, 6), nullable=True)
+ value = Column(Numeric(15, 6), nullable=False)
```

### Verification

```
Targeted suite: 75 passed in 1.17s (67 original + 8 new correction tests)
Regression suite: 36 passed in 0.88s
MEU gate: 8/8 blocking + A3 evidence bundle clean (25.22s)
```

### Updated Verdict

`corrections_applied` — All 3 findings resolved. Schema/model contracts now match the approved plan. Quote model is append-only (index-only, no UniqueConstraint). Handoff evidence sections pass the validator. Ready for re-review.
