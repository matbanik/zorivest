# IR-5 Test Rigor Rating Criteria

Opus audit rubric for `2026-03-16-test-rigor-audit`. Synthesized from Gemini 3.1 Pro, GPT-5.4, and Claude Opus 4.6 research.

## Core Principle

> "Tests should be sensitive to behavior changes and insensitive to structure changes."
> — Kent Beck, Test Desiderata

A test is strong when it **proves observable behavior** and would **fail under a real regression**. A test is weak when it passes regardless of whether the production code is correct.

## Rating Dimensions

| Dimension | Weight | Question |
|-----------|--------|----------|
| Behavioral Assertion | Primary | Does the test assert concrete output values or observable state changes? |
| Mutation Resilience | Secondary | Would a realistic bug in production code cause this test to fail? |
| Implementation Coupling | Modifier | Does the test break during a valid refactor (false positive risk)? |

## Rating Thresholds

### 🟢 GREEN — Strong

ALL of:
- Asserts concrete output/behavior values (return values, response bodies, DB state, error messages, computed results)
- Would catch a regression if production code changed behavior
- Tests public contract, not internal implementation

### 🟡 YELLOW — Adequate but Improvable

ANY of:
- Partial assertion: status code without response body, or type check without value check
- Mock verification without argument checking (`assert_called_once()` without `_with(...)`)
- Shape/type assertion that has SOME behavioral value but misses key outputs
- Happy-path only with no error-case coverage on an error-prone interface
- Correct intent but overly coupled to implementation (e.g., testing private method directly)

### 🔴 RED — Weak / Tautological

ANY of:
- Tautological: assertion is always true regardless of implementation (e.g., `issubclass(MyEnum, StrEnum)`)
- Existence-only: `hasattr(obj, "method")` without calling the method
- Private-state testing: asserts on `_internal_attr`, `_loaded_at`, or cache internals
- Protocol-only: `isinstance(obj, Protocol)` without testing the protocol's behavior
- Import-surface-only: tests that a symbol is importable but never exercises it
- Would pass even if the function returned wrong values

## Category-Specific Criteria

### API Route Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts status code AND response body fields/values AND error payloads |
| 🟡 | Status code only, or status code + partial body, or missing error-case validation |
| 🔴 | Only asserts no exception raised, or mock-only with no response verification |

### Domain Model Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts computed values, business rules, state transitions, serialization correctness |
| 🟡 | isinstance/type checks with some behavioral value, partial coverage of business rule |
| 🔴 | Tautological enum checks, hasattr-only, protocol compliance without behavioral test |

### Service Layer Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts service return values with real or well-crafted mock dependencies |
| 🟡 | `assert_called_once()` without argument verification, happy-path only |
| 🔴 | Only verifies mock was called, not that correct result was produced |

### Integration Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts actual database state / repository return values with real SQLCipher/SQLite |
| 🟡 | Partial assertions, or tests only happy path without error recovery |
| 🔴 | Tests internal/private state (KDF params, internal caches), or import-surface only |

### MCP Server Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts tool outputs with concrete expected values, error responses, schema compliance |
| 🟡 | Asserts output shape but not specific values, or structural render checks |
| 🔴 | Mock-only with no output verification, snapshot-only without behavioral assertion |

### UI Tests
| Rating | Criteria |
|--------|----------|
| 🟢 | Asserts rendered content, user interactions produce expected UI changes |
| 🟡 | Structural render checks (component renders without crash), partial interaction testing |
| 🔴 | Snapshot-only, or tests that only verify component existence without interaction |

## Upgrade Path Guidance

Every 🟡/🔴 rating includes a brief note on what change would upgrade it to 🟢. This makes the audit directly actionable for Phase 1 quick-win fixes.

## Sources

- Kent Beck, "Test Desiderata" — behavioral sensitivity principle
- Claude Opus 4.6 research — intent vs correctness testing, four system invariants
- GPT-5.4 research — property-based testing, assertion patterns, API test strength
- Gemini 3.1 Pro research — mutation testing, binary verification patterns
- Implementation plan weakness patterns — tautological, hasattr, status-only, mock-only
