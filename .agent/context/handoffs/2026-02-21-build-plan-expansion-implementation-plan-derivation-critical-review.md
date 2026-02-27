# Critical Review: Build Plan Expansion Implementation Plan Derivation

## Scope
- Source doc: `_inspiration/import_research/Build Plan Expansion Ideas.md`
- Derived doc: `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md`
- Goal: validate how faithfully and safely the implementation plan was derived from the ideas document.

## Executive Verdict
- Coverage is complete at headline level: all 26 idea sections are represented in the implementation mapping table.
- Derivation quality is mixed: the plan introduces major priority and contract shifts without explicit rationale, and several mapped features are under-specified in downstream sections.

## Findings (Severity-Ordered)

### Critical
1. Priority model was materially changed without decision rationale.
- Evidence:
  - Ideas mark features 1-3 as `P0` (`_inspiration/import_research/Build Plan Expansion Ideas.md:41`, `_inspiration/import_research/Build Plan Expansion Ideas.md:111`, `_inspiration/import_research/Build Plan Expansion Ideas.md:160`).
  - Implementation downgrades them to `P1` (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:11`, `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:12`, `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:13`).
  - Ideas mark Alpaca/Tradier as `P1` (`_inspiration/import_research/Build Plan Expansion Ideas.md:1232`, `_inspiration/import_research/Build Plan Expansion Ideas.md:1277`), implementation moves both to `P2` (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:34`, `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:35`).
  - Ideas mark Monthly P&L and Broker Constraint Modeling as `P3` (`_inspiration/import_research/Build Plan Expansion Ideas.md:1063`, `_inspiration/import_research/Build Plan Expansion Ideas.md:1179`), implementation promotes to `P2` (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:30`, `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:33`).
- Impact: execution order can drift from original research intent and from previously reviewed risk posture.
- Recommendation: add an explicit "Priority Change Log" section listing each reprioritization with rationale and owner decision.

2. Multiple mapped features are not fully carried into detailed implementation sections.
- Evidence:
  - Feature 16 (Bidirectional Trade-Journal) is mapped once (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:26`) but has no dedicated service, API, MCP, or index change block.
  - Feature 22 (Cost of Free) is mapped once (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:32`) but is not defined in output group details (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:295`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:306`).
  - Feature 15 (SQN) appears in mapping (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:25`) and output groups (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:299`), but no dedicated service or MCP tool is defined in service/tool tables (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:108`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:175`).
- Impact: implementers cannot unambiguously build these features end-to-end.
- Recommendation: add per-feature "contract completeness" rows (Domain, Service, REST, MCP, GUI, Indexes, Tests).

3. Tax-lot feature was compressed from core accounting scope to mostly GUI alignment.
- Evidence:
  - Ideas define Tax-Lot in `core/accounting/` (`_inspiration/import_research/Build Plan Expansion Ideas.md:210`).
  - Implementation maps Tax-Lot as "MERGE with existing Phase 3A" targeting `06g` (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:14`).
- Impact: risk of documenting tax-lot UX before hardening accounting contracts.
- Recommendation: re-anchor feature 4 in domain/service layers first, then keep GUI as a consumer.

### High
4. Internal contract mismatches exist inside the implementation plan.
- Evidence:
  - REST section includes `POST /import/pdf` and `GET /analytics/sqn` (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:143`, `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:141`).
  - MCP section has no PDF import tool or SQN tool (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:158`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:175`).
- Impact: later docs can validly diverge in different directions.
- Recommendation: add an endpoint-to-tool parity table in the plan itself.

5. Primary mapping table uses ambiguous target identifiers.
- Evidence: shorthand targets like ``01``, ``03``, ``domain-model-ref`` in `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:11`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:36`.
- Impact: increases interpretation variance and review overhead.
- Recommendation: use exact file paths in mapping rows, not aliases.

### Medium
6. Verification plan is mostly manual and does not gate cross-file consistency.
- Evidence: manual checks only in `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:337`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:342`.
- Impact: drift is likely when edits are applied in batches.
- Recommendation: add deterministic checks (route/tool parity, feature-to-file matrix completeness, index sync checks).

## Positive Notes
- 26/26 feature rows are present in the mapping table.
- Bank import is correctly treated as phased in the priority section.
- Rate-limit and probabilistic caveats (OpenFIGI, PFOF) are reflected in service-level wording.

## Recommended Next Actions
1. Add a short "Design Decisions" addendum capturing priority changes and scope cuts.
2. Expand under-specified features (#15, #16, #22) into full layer-by-layer contracts.
3. Add a machine-checkable parity checklist before updating `docs/build-plan/`.
