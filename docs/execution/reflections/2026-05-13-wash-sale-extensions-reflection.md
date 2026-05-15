---
project: "2026-05-13-wash-sale-extensions"
meus: ["MEU-133", "MEU-134", "MEU-135", "MEU-136"]
date: "2026-05-13"
---

# Reflection — Wash Sale Extensions

## Session Narrative

Executed Phase 3B Session 2 implementing four wash sale engine extensions. All four MEUs (133-136) completed in a single continuous execution pass with full TDD discipline. The session benefited from strong foundation laid in Session 1 (MEU-130–132) — the existing `detect_wash_sales()` and `WashSaleChainManager` interfaces were designed for extensibility, which kept change scope narrow.

### What Went Well
- **Domain function isolation**: `check_conflicts()` as a pure function (no UoW coupling) made testing straightforward and the service-level wiring trivial
- **Backward compatibility**: All new fields use nullable/default patterns — zero breaking changes to existing callers
- **Sentinel test caught field drift**: The `test_stored_field_count` sentinel correctly flagged when `acquisition_source` changed TaxLot's field count from 13 to 14

### What Could Improve
- **Hardcoded NOW in tests**: Initial RED tests used a hardcoded `NOW` constant but `simulate_impact()` internally called `datetime.now()`. Fixed by making `now` injectable, but this should have been anticipated during test design
- **Task 16 sequencing**: The `check_wash_sale_conflicts()` service method was logically part of MEU-135 but felt like it belonged with MEU-136's pre-trade flow. The plan's task ordering was correct but the naming could have been clearer

### Risks and Open Items
- None. All implementation complete and verified.

## Instruction Coverage

```yaml
schema: v1
session:
  id: 0ab3eb64-ac72-4d71-80ed-087d96576af2
  task_class: tdd
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 4
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
  - id: p0_system_constraints
    cited: true
    influence: 3
loaded:
  workflows: [execution_session, create_plan]
  roles: [coder, tester]
  skills: [terminal_preflight]
  refs: [reflection.v1.yaml]
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:never-modify-tests-to-pass"
  - "P0:redirect-to-file-pattern"
  - "P1:fic-before-code"
  - "P1:anti-premature-stop"
conflicts: []
note: "Injectable now parameter was the right fix for test determinism vs modifying assertions."
```
