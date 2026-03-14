# Reflection — IBKR & CSV Import Foundation (MEU-96 + MEU-99)

> Date: 2026-03-13

## What Went Well

- **TDD discipline held**: 66 tests written before implementation, all passing after Green phase
- **Shared foundation design**: Domain types (`RawExecution`, `ImportResult`, Protocols) reused cleanly across XML and CSV adapters
- **Security-first XML parsing**: `defusedxml` integration for XXE prevention was straightforward
- **Protocol-based extensibility**: New broker adapters only need to implement `BrokerFileAdapter` or `CSVBrokerAdapter`

## What Could Be Improved

- **Integer floor division bug (F2)**: The `strike_int // 1000` bug for fractional option strikes was caught by Codex, not by the initial tests. The substring-only assertions (`"200" in symbol`) were too weak to detect `200.5 → 200` truncation
  - **Lesson**: Option symbol tests should always use exact equality, never substring matching
- **Double-BOM test fixture**: Content with embedded `\ufeff` + `utf-8-sig` encoding created a double-BOM that masked a real detection path issue
  - **Lesson**: BOM testing should use `utf-8-sig` encoding OR explicit `\ufeff`, never both
- **Handoff template gaps (F5)**: Missing Role Plan/Reviewer Output/Approval Gate sections — need to reference template when writing handoffs
- **Stale evidence counts**: Test counts drifted after corrections (33→34, 31→32, 1230→1232) — always refresh evidence after any code change

## Rules Checked (Adherence: 85%)

1. ✅ TDD: tests written before implementation
2. ✅ No placeholders/TODOs
3. ✅ Pyright clean
4. ✅ Ruff clean
5. ✅ Anti-placeholder scan clean
6. ⚠️ Handoff template completeness — initially missed 3 sections
7. ✅ ADR-0003 graceful degradation implemented
8. ⚠️ Exact-value test assertions — initially used substring matching
9. ✅ Protocol-based design for extensibility
10. ✅ defusedxml for XML security

## Key Decisions

- **`typing.cast` for Protocol narrowing**: Used `cast(CSVBrokerAdapter, a)` instead of `type: ignore` to satisfy pyright's invariance check on `list[BrokerFileAdapter]` → `Sequence[CSVBrokerAdapter]`
- **True division for strikes**: `int(raw) / 1000` with conditional int formatting preserves fractional strikes while keeping whole strikes clean
- **BOM stripping in auto-detect**: `ImportService` strips BOM before header detection, so CSV parsers don't need to handle it individually
