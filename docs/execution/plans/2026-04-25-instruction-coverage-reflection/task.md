---
project: "2026-04-25-instruction-coverage-reflection"
source: "docs/execution/plans/2026-04-25-instruction-coverage-reflection/implementation-plan.md"
meus: ["ICR-1", "ICR-2", "ICR-3"]
status: "done"
template_version: "2.0"
---

# Task — Instruction Coverage Reflection System

> **Project:** `2026-04-25-instruction-coverage-reflection`
> **Type:** Infrastructure/Docs
> **Estimate:** 7 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Enumerate all AGENTS.md H2 sections and assign P0–P3 priorities per synthesis §6 heuristic | orchestrator | `.agent/schemas/registry.yaml` | `uv run python -c "import yaml, re, sys; headings=[m.group(1) for m in re.finditer(r'^## (.+)$', open('AGENTS.md').read(), re.MULTILINE)]; expected={re.sub(r'[^a-z0-9]+','_',h.lower()).strip('_') for h in headings}; reg=yaml.safe_load(open('.agent/schemas/registry.yaml')); actual={s['section_id'] for s in reg['sections']}; (print(f'FAIL: duplicate IDs in registry') or sys.exit(1)) if len(actual)!=len(reg['sections']) else None; missing=expected-actual; extra=actual-expected; (print(f'FAIL: missing={missing}, extra={extra}') or sys.exit(1)) if missing or extra else print(f'OK: {len(actual)} sections match')" *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt` | `[x]` |
| 2 | Create reflection schema v1 definition | coder | `.agent/schemas/reflection.v1.yaml` | `uv run python -c "import yaml; yaml.safe_load(open('.agent/schemas/reflection.v1.yaml')); print('OK')" *> C:\Temp\zorivest\schema-check.txt; Get-Content C:\Temp\zorivest\schema-check.txt` | `[x]` |
| 3 | Write and inject meta-prompt at end of AGENTS.md (after `## Context & Docs`, EOF recency zone) | coder | Modified AGENTS.md | `rg "instruction_coverage_reflection" AGENTS.md *> C:\Temp\zorivest\metaprompt-check.txt; Get-Content C:\Temp\zorivest\metaprompt-check.txt` (expect ≥1 match) | `[x]` |
| 4 | Update reflection template with Instruction Coverage section | coder | Modified `docs/execution/reflections/TEMPLATE.md` | `rg "Instruction Coverage" docs/execution/reflections/TEMPLATE.md *> C:\Temp\zorivest\template-check.txt; Get-Content C:\Temp\zorivest\template-check.txt` (expect ≥1 match) | `[x]` |
| 5 | Write aggregator tests (Red phase) — assertions for AC-3.1 through AC-3.8 | tester | `tests/unit/test_aggregate_reflections.py` | `uv run pytest tests/unit/test_aggregate_reflections.py --tb=short *> C:\Temp\zorivest\aggregator-red.txt; Get-Content C:\Temp\zorivest\aggregator-red.txt \| Select-Object -Last 20` (expect all tests to FAIL, proving Red phase) | `[x]` |
| 6 | Implement aggregation script (Green phase) | coder | `tools/aggregate_reflections.py` | `uv run pytest tests/unit/test_aggregate_reflections.py -x --tb=short *> C:\Temp\zorivest\aggregator-green.txt; Get-Content C:\Temp\zorivest\aggregator-green.txt \| Select-Object -Last 20` (expect all PASS) | `[x]` |
| 7 | Create synthetic test reflection and run aggregator end-to-end | tester | Test reflection YAML + aggregator output | `uv run python tools/aggregate_reflections.py --input .agent/reflections/test/ --registry .agent/schemas/registry.yaml *> C:\Temp\zorivest\aggregator-e2e.txt; Get-Content C:\Temp\zorivest\aggregator-e2e.txt` (exits 0 with JSON output) | `[x]` |
| 8 | Anti-placeholder scan | tester | Clean scan | `rg "TODO\|FIXME\|NotImplementedError" .agent/schemas/ tools/aggregate_reflections.py *> C:\Temp\zorivest\placeholder-check.txt; Get-Content C:\Temp\zorivest\placeholder-check.txt` (expect 0 matches) | `[x]` |
| 9 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "instruction-coverage" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` (expect 0 matches) | `[x]` |
| 10 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-instruction-coverage-reflection-2026-04-25` | MCP: `pomera_notes(action="search", search_term="Zorivest-instruction-coverage*")` returns ≥1 result | `[x]` |
| 11 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md` | `Test-Path .agent/context/handoffs/2026-04-25-instruction-coverage-reflection-infra.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` (expect True) | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
