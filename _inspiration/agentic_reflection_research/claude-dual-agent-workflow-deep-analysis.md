# Deep Analysis: Dual-Agent Workflow Rule Changes

## Implementer's Perspective — Claude Opus 4.6

*Analysis of whether workflow changes will reduce review passes from 4–11 to 2–3*

---

## Reconstructed Pattern Inventory

Before diving into the five tasks, I need to establish the 10 patterns as inferred from the pre-handoff-review skill, execution-session 4b, and meu-handoff documents:

| # | Pattern Name | Frequency | Primary Documents Addressing It |
|---|---|---|---|
| 1 | Claim-to-state drift | 7/7 | Pre-handoff Step 1, Execution 4b.1 |
| 2 | Artifact incompleteness | 6/7 | Pre-handoff Step 6, Execution 4b.6 |
| 3 | Evidence staleness | 6/7 | Pre-handoff Step 3, Execution 4b.2 |
| 4 | Mock masking / test coverage gaps | 5/7 | Pre-handoff Step 2, meu-handoff Live Probe |
| 5 | Scope overstatement | 5/7 | Pre-handoff Step 1 (contradiction check) |
| 6 | Fix-specific-not-general | meta | Coder rule 8, Execution 4b.3, Corrections 2b |
| 7 | Canonical doc contradiction | 3/7 | Pre-handoff Step 5, Execution 4b.5 |
| 8 | Stub inadequacy | 5/7 | Coder rule 10, meu-handoff Stub Quality Gate |
| 9 | Error mapping gaps | 3/7 | Coder rule 9, Pre-handoff Step 7 |
| 10 | Lifecycle ordering (premature artifacts) | 3/7 | Pre-handoff Step 6, Execution 4b.6 |

---

## Task 1: Implementer Impact Assessment

### 1.1 Time Overhead per New Rule

For a typical 4-MEU project session (estimated baseline: ~200 tool calls, ~90 minutes of agent time):

| Rule / Protocol Step | Added Tool Calls | Added Time (est.) | Quality Gain |
|---|---|---|---|
| Pre-handoff Step 1: AC-to-code rg per AC | 3–8 per MEU (depends on AC count) | 3–8 min | HIGH — directly prevents the most common pattern |
| Pre-handoff Step 2: Test coverage audit | 4–6 rg commands | 3–5 min | HIGH — catches mock masking before submission |
| Pre-handoff Step 3: Evidence refresh | 3–5 command re-runs | 2–4 min | HIGH — trivially automatable, high ROI |
| Pre-handoff Step 4: Fix generalization | 2–6 rg commands per fix | 2–8 min (varies wildly) | HIGH but unbounded — see §4.5 |
| Pre-handoff Step 5: Cross-reference sweep | 2–4 rg commands | 2–3 min | MEDIUM — only triggers on arch changes |
| Pre-handoff Step 6: Project closeout | 3–4 rg commands + file reads | 2–3 min | MEDIUM — mechanical check |
| Pre-handoff Step 7: Error mapping sweep | 3–6 rg commands | 2–4 min | HIGH for API MEUs, N/A for entity MEUs |
| Coder rule 8 (fix-general) | Amortized into Step 4 | 0 additional | N/A — duplicate of Step 4 |
| Coder rule 9 (error mapping) | Amortized into Step 7 | 0 additional | N/A — duplicate of Step 7 |
| Coder rule 10 (stub contracts) | 1–2 rg commands | 1–2 min | HIGH for route MEUs |

**Total overhead per MEU**: ~20–40 tool calls, ~15–35 minutes.
**Total overhead for 4-MEU project**: ~80–160 additional tool calls, ~60–140 minutes.

**Is it proportional?** For a project that previously needed 11 passes (rest-api-foundation), each review cycle with Codex likely costs 30–60 minutes of combined agent time. Eliminating 5–8 passes saves 150–480 minutes. The 60–140 minute investment is proportional *if* it actually eliminates those passes. The concern is that the overhead is front-loaded (paid on every MEU) while the savings are probabilistic (some MEUs would have passed in 1–2 passes anyway).

**Recommendation**: The protocol should be severity-tiered. Entity/DTO MEUs (like domain-entities-ports, which already passed in 1) should use a lighter checklist. Route/API MEUs should use the full protocol.

### 1.2 Cognitive Load

**Conflict zones identified:**

1. **Coder rule 8 vs Pre-handoff Step 4**: These are identical instructions in different documents. No conflict, but the duplication means I'd need to track whether I already ran the generalization sweep during coding vs. during pre-handoff review. The risk is doing it twice (wasted time) or assuming I already did it (missed instances from later fixes).

2. **"Fix the implementation, not the test" (TDD immutability) vs "Stubs must honor behavioral contracts" (Coder rule 10)**: These can genuinely conflict. If a test expects `save()` to persist and the stub's `save()` discards, the TDD rule says fix the stub (implementation). But what if the *test setup* created the stub with a mock framework and the mock is the fixture? The line between "test assertion" and "test setup/fixture" becomes blurry with stub behavior.

3. **No-deferral rule vs fix-general scope**: If I find 12 instances of a pattern during generalization (Step 4), fixing all of them could consume the rest of my context window. The anti-premature-stop rule says "don't terminate early," but the practical constraint is that I might not have enough context to fix all 12 AND complete the remaining MEUs.

4. **Spec sufficiency gate vs execution momentum**: The gate says "resolve thin specs before coding," but the pre-handoff review says "if you can't verify an AC against code, the AC might be under-specified." These create a loop where I could bounce between planning and execution indefinitely.

**Decision paralysis risk**: MODERATE. The rules are largely orthogonal, but the edge cases above are real. The biggest paralysis risk is Step 4 (fix-general) — "how many similar files is enough?" has no clear stopping criterion.

### 1.3 False Positive Rates for rg Commands

| Command Pattern | Estimated False Positive Rate | Rationale |
|---|---|---|
| `rg "__getattr__"` in stubs | LOW (~5%) | Very specific pattern, rarely appears legitimately in stubs |
| `rg "TestClient\|create_app"` in tests | LOW (~10%) | Might match comments or imports, but easy to distinguish |
| `rg "NotFoundError\|BusinessRuleError"` in routes | LOW (~5%) | These are domain-specific names, unlikely false matches |
| `rg "404\|409\|422"` in tests | MODERATE (~25%) | Will match status codes in unrelated contexts (pagination, etc.) |
| `rg "TODO\|FIXME\|NotImplementedError"` | LOW-MODERATE (~15%) | Will match comments discussing the pattern, doc references |
| `rg "implementation complete\|all ACs"` in handoffs | HIGH (~40%) | Will match template text, previous iterations, quoted patterns |
| `rg "residual\|deferred\|partial"` in handoffs | MODERATE (~30%) | Will match historical sections in rolling review files |
| `rg "✅\|🟡\|📋"` in BUILD_PLAN | LOW (~5%) | Very specific emoji markers |
| `rg "<old-pattern>"` across docs | VARIABLE | Depends entirely on pattern specificity |

**Highest risk**: The handoff consistency checks (Steps 1 and 6) will match across all historical sections in rolling review files. Since the planning-corrections workflow appends to the same canonical file, `rg "implementation complete"` will match every previous iteration. The agent would need to filter by section/date, which `rg` alone can't do — requiring additional file reads to disambiguate.

---

## Task 2: Structural vs Behavioral Classification

| # | Pattern | Classification | Rationale |
|---|---|---|---|
| 1 | Claim-to-state drift | **Behavioral** | Requires the agent to *distrust its own memory* and verify claims against file state. No linter can catch "the handoff says X but the code does Y." |
| 2 | Artifact incompleteness | **Structural** | A script could diff task.md checkmarks against handoff existence, BUILD_PLAN counts against row data. |
| 3 | Evidence staleness | **Process + Structural** | Process: must re-run commands *after* all fixes. Structural: a wrapper script could compare handoff counts against fresh command output. |
| 4 | Mock masking | **Behavioral** | Requires judgment about *which* tests are meaningful. A rule can mandate integration tests exist, but can't assess whether they exercise real behavior. |
| 5 | Scope overstatement | **Behavioral** | Requires the agent to evaluate the *semantic* relationship between its conclusion and its risk section. |
| 6 | Fix-specific-not-general | **Behavioral + Process** | The `rg` sweep is structural, but deciding "what category does this fix belong to?" and "where are all similar locations?" requires reasoning. |
| 7 | Canonical doc contradiction | **Structural** | Can be fully automated: given a list of changed patterns, `rg` across docs and flag mismatches. |
| 8 | Stub inadequacy | **Structural** | `__getattr__` prohibition is a simple grep. Behavioral contract verification is harder but could be partially automated with AST analysis. |
| 9 | Error mapping gaps | **Structural** | AST analysis of route handlers could verify exception-to-status-code mapping. A custom linter rule would catch this. |
| 10 | Lifecycle ordering | **Process** | Entirely about *when* artifacts are created relative to Codex validation. |

### Automated Check Proposals for Structural Patterns

**Pattern 2 (Artifact incompleteness)**:
```python
# Script: verify_project_consistency.py
# - Parse task.md for [x] items, verify each has a corresponding handoff file
# - Parse BUILD_PLAN.md summary row, verify counts match row-level ✅/🟡/📋
# - Compare meu-registry statuses against handoff statuses
```

**Pattern 3 (Evidence staleness)**:
```python
# Script: evidence_freshness_check.py
# - Run pytest/pyright/ruff, capture output
# - Parse handoff for claimed counts
# - Diff and report mismatches
```

**Pattern 7 (Canonical doc contradiction)**:
```python
# Script: cross_reference_check.py
# Input: list of changed patterns (old → new)
# For each: rg old pattern across docs/, flag any matches
```

**Pattern 8 (Stub inadequacy — partial)**:
```bash
# Simple prohibition check
rg "__getattr__" packages/*/src/**/*stub* packages/*/src/**/*fake*
# Exits non-zero if matches found
```

**Pattern 9 (Error mapping gaps)**:
```python
# Script: verify_error_mapping.py
# AST-parse route handlers
# For each handler with write operations, verify try/except blocks
# map NotFoundError→404, BusinessRuleError→409, ValueError→422
# Flag any handler missing mappings
```

### Sufficiency of Instruction Changes for Behavioral Patterns

**Pattern 1 (Claim-to-state drift)**: Instructions alone are **insufficient**. The fundamental issue is that the agent builds a mental model during implementation and then writes the handoff from that model rather than re-reading the code. The instruction to "rg each AC" is a good forcing function, but it requires the agent to *actually distrust its memory*, which is a metacognitive shift. A more effective approach would be a **mandatory structured template** where each AC has a required `verified_at: file:line` field that can only be filled by tool output, not free-text.

**Pattern 4 (Mock masking)**: Instructions are **partially sufficient**. The mandate for integration tests with `TestClient` is concrete enough. But the deeper issue — *choosing meaningful test scenarios* — requires domain understanding that instructions can't fully encode. The live probe minimum list helps but is necessarily incomplete.

**Pattern 5 (Scope overstatement)**: Instructions are **insufficient**. This is fundamentally a calibration problem — the agent's completion detector fires too early. The contradiction check ("do conclusion and risk section agree?") is a patch, not a fix. The root issue is that the agent writes the conclusion *first* and then adds risks as an afterthought. Reversing the order (write risks first, then derive the conclusion from the risk section) would be more effective.

**Pattern 6 (Fix-specific-not-general)**: Instructions are **partially sufficient**. The `rg` sweep is a good mechanical habit, but categorizing fixes requires abstract reasoning that varies by domain. A more effective approach would be maintaining a **running category log** during the session: every time a fix is applied, append `{category}: {file}:{line}` to a session log, then at pre-handoff, group by category and verify each group is complete.

---

## Task 3: Root Cause Depth Analysis

### 3.1 Is claim-to-state drift caused by TDD itself?

**Partially yes.** The TDD protocol creates a dangerous confidence gradient:

1. Tests pass → agent concludes "the behavior is correct"
2. But tests may be testing a subset of the AC (mock masking)
3. Agent writes handoff with confidence from step 1, not from re-reading code
4. The handoff claims completeness based on test results, not code inspection

The deeper root cause is **the conflation of "tests pass" with "contract is met."** TDD is designed for *development guidance*, not *verification completeness*. The tests the agent writes are bounded by its understanding at write-time, which may not cover the full AC.

**Upstream fix**: Separate the "implementation confidence" signal from the "contract verification" signal. After Green phase, add an explicit **Verification phase** (distinct from TDD refactoring) where the agent re-reads the ACs *without looking at the tests* and verifies each one against code. This is essentially what the pre-handoff protocol does, but framing it as part of the TDD cycle (Red → Green → Refactor → **Verify**) would be more natural than a post-hoc checklist.

### 3.2 Is fix-specific-not-general caused by MEU scoping?

**Yes, strongly.** The MEU model encourages tunnel vision:

1. Agent receives a scoped task (MEU-7: REST API routes)
2. Codex reports "trades.py line 45 missing error mapping"
3. Agent opens trades.py, fixes line 45, closes trades.py
4. Agent's mental scope is "I'm fixing the Codex finding for MEU-7"
5. Checking portfolios.py feels like it's "outside the finding"

The MEU boundary creates a psychological frame where "fixing the cited instance" = "resolving the finding." The agent needs to reframe from "fix this finding" to "eliminate this category of defect across the codebase." The instruction to `rg` for siblings is the right mechanical intervention, but the deeper issue is that the MEU scope model trains the agent to think locally.

**Upstream fix**: The corrections workflow (planning-corrections.md) already includes Step 2b (categorize and generalize), but this only applies *during corrections*. The same categorization discipline should be embedded in the initial TDD cycle — when the agent writes error mapping for trades.py, it should immediately check all sibling route files. This is proactive rather than reactive.

### 3.3 Is evidence staleness caused by the handoff format?

**Yes, directly.** The handoff format asks for prose sections ("Commands Executed", "FAIL_TO_PASS Evidence") that are typically written once during or after implementation. The agent naturally writes these as it goes, then doesn't update them after subsequent fixes. The format incentivizes "write once, submit" rather than "write last, from fresh data."

**Upstream fix**: Change the handoff template to include a **machine-parseable evidence section** that can only be populated by a script. For example:

```markdown
## Evidence (auto-generated — do not edit manually)
<!-- Run: python tools/generate_evidence.py <handoff-path> -->
```

This script would run all validation commands and embed the output directly. The agent can't fake fresh evidence if the evidence section is generated by a tool.

### 3.4 Are there upstream planning phase changes that would help?

**Yes, three specific ones:**

1. **FIC should include a "verification plan" section**: For each AC, specify *how* it will be verified (which rg command, which test, which integration probe). This forces the agent to think about verification during planning, not after implementation.

2. **Build plan should tag MEUs by "review risk level"**: Entity MEUs (low risk) vs API/route MEUs (high risk) vs infrastructure MEUs (medium risk). The pre-handoff protocol intensity should scale with risk level.

3. **Build plan should list "known sibling patterns"**: If the build plan says "all route handlers need error mapping," this creates a cross-MEU checklist that survives MEU scope boundaries.

---

## Task 4: Detrimental Effect Analysis

### 4.1 Over-verification paralysis

The 7-step protocol could absolutely cause this. My estimate:

- **Entity/DTO MEUs** (like domain-entities-ports): Steps 2, 4, 7 are largely irrelevant. Running the full protocol wastes ~15 minutes per MEU with minimal quality gain.
- **Route/API MEUs** (like rest-api-foundation): All 7 steps are relevant and would likely have prevented 6-8 of the 11 passes. The time is well-spent.
- **Infrastructure MEUs** (like settings-backup-foundation): Steps 1, 3, 5 are relevant. Steps 2, 7 depend on whether the MEU includes API exposure.

**Right balance**: The protocol should have a **risk-tier gate** at the top:

- **Tier 1 (Entity/DTO)**: Steps 1, 3, 6 only (~10 min)
- **Tier 2 (Service/Infrastructure)**: Steps 1, 3, 5, 6 (~20 min)
- **Tier 3 (Route/API/MCP)**: All 7 steps (~35 min)

Without tiering, the agent spends equal effort on low-risk and high-risk MEUs, which is a misallocation.

### 4.2 Checklist-driven behavior (Goodhart's Law)

**This is a real and significant risk.** Specific failure modes:

1. **Surface-level rg matching**: The agent runs `rg "NotFoundError" routes/` and sees matches, checks the box, but doesn't verify that the mapping is *correct* (e.g., it maps to 500 instead of 404). The checklist asks "does the pattern exist?" but the real question is "is the pattern correct?"

2. **Evidence theater**: The agent re-runs pytest and pastes "47 passed" into the handoff. But if 3 tests were skipped due to missing fixtures, the count is technically accurate but misleading. The checklist doesn't distinguish "47 passed, 0 skipped" from "47 passed, 3 skipped."

3. **Category gaming**: For fix generalization, the agent categorizes a fix narrowly ("missing 404 mapping in trades.py") rather than broadly ("missing error mapping in any route handler") to minimize the rg scope.

**Mitigation**: The checklist should require *negative evidence* (what was NOT found) alongside positive evidence. Instead of "Checked N locations," require "Checked N locations, found M instances. Verified each instance maps to the correct status code. No locations without mapping remain."

### 4.3 `__getattr__` prohibition scope

**There are legitimate uses the prohibition would block:**

1. **Proxy/wrapper patterns**: If a stub wraps a real implementation for testing purposes, `__getattr__` delegation is standard Python. Forcing explicit delegation of every method is verbose and fragile (new methods on the interface require stub updates).

2. **Dynamic attribute access for configuration objects**: Settings objects that delegate to environment variables or config files commonly use `__getattr__`.

3. **Protocol/interface stubs in test doubles**: When implementing a Protocol with 15+ methods where only 2-3 are relevant to the test, `__getattr__` with `raise AttributeError(f"Stub does not implement {name}")` is *better* than silently returning None but *also better* than requiring 15 explicit `raise NotImplementedError` methods.

**The prohibition should be narrowed**: Instead of "no `__getattr__`," the rule should be "no `__getattr__` that silently returns values (None, empty collections, etc.) for undefined methods." An explicit-error `__getattr__` is actually *safer* than a stub with missing methods (which would raise `AttributeError` anyway, but with a less helpful message).

**Proposed revision**:
```
Prohibited: `__getattr__` that returns None, empty values, or no-op callables for undefined methods.
Permitted: `__getattr__` that raises AttributeError or NotImplementedError with the method name.
```

### 4.4 Integration test mandate for pure entity MEUs

**The mandate adds overhead without proportional value for pure entity/DTO MEUs.** Here's why:

- Domain entities have no routes, no handlers, no DI wiring.
- The `create_app() + TestClient` pattern tests HTTP stack behavior — irrelevant for entities.
- Entity validation is fully testable with unit tests (construct entity, assert properties, check invariants).
- The only integration-like test that would add value is verifying that the entity works with the persistence layer — but that's the *next* MEU's responsibility (e.g., repository implementation).

**However**: The meu-handoff document scopes the live probe requirement to "any MEU that touches routes, handlers, or service wiring." This is correctly scoped. The risk is if the pre-handoff checklist (Step 2) is applied blindly without reading the scoping condition.

**Recommendation**: Pre-handoff Step 2 should have a gate: "If this MEU does not include route/handler/wiring code, skip the Live Probe Minimum and verify only that unit tests cover all ACs."

### 4.5 Fix-general scope creep

**This is the most dangerous detrimental effect.** The stopping criterion problem:

1. I fix a missing error mapping in `trades.py`.
2. I categorize it: "missing error mapping in route handler."
3. I `rg` for all route handlers: find `portfolios.py`, `watchlists.py`, `settings.py`.
4. I check each one — `portfolios.py` is also missing the mapping. Fixed.
5. But now I notice `settings.py` uses a different error class (`ConfigurationError`) that isn't in the standard mapping. Do I add a mapping for that too?
6. And `watchlists.py` has the mapping but the status code is wrong (409 instead of 404 for NotFoundError). Is that "the same category" or a different one?
7. And there's a MCP handler file that uses a completely different error mapping convention...

**The scope can expand indefinitely** because "same category" is a fuzzy concept. Each additional instance found may itself trigger new categories.

**Proposed stopping criterion**:
- Search is bounded to **files modified in the current MEU + sibling files in the same package**.
- Cross-package searches are logged but not auto-fixed (they become findings for the next MEU or a dedicated cleanup MEU).
- Maximum 3 levels of category expansion per finding (original → siblings → siblings of siblings → stop).
- Document scope boundaries: "Searched within `packages/core/src/routes/`. Cross-package instances in `mcp-server/` noted as follow-up."

---

## Task 5: Synthesis

### 5.1 Most Effectively Reduced (ranked)

1. **Evidence staleness (#3)** — The "re-run after all fixes" rule is mechanical, unambiguous, and directly addresses the root cause. Compliance is nearly guaranteed.
2. **Error mapping gaps (#9)** — The specific exception→status-code mapping list is concrete and greppable. Hard to misinterpret.
3. **Lifecycle ordering (#10)** — "Don't create reflection until after Codex validation" is a simple sequencing rule. Easy to follow.
4. **Stub inadequacy (#8)** — The `__getattr__` prohibition and behavioral contract table are specific enough to enforce. (With the caveat from §4.3.)
5. **Artifact incompleteness (#2)** — The closeout checks are mechanical and automatable.

### 5.2 Least Effectively Reduced (ranked, worst first)

1. **Fix-specific-not-general (#6)** — The instruction helps, but the categorization problem and scope creep issue (§4.5) mean the agent will either under-search or over-search. This pattern will persist at reduced frequency.
2. **Claim-to-state drift (#1)** — Despite being the most frequent pattern, it requires a metacognitive shift that instructions alone can't guarantee. The agent must learn to distrust its own memory, which is fundamentally a behavioral change. The `rg` verification helps but can be performed superficially.
3. **Mock masking (#4)** — The integration test mandate helps, but the deeper issue (choosing meaningful test scenarios) requires domain judgment. The agent may write integration tests that pass trivially without exercising real behavior.
4. **Scope overstatement (#5)** — The contradiction check is a good heuristic but doesn't address the root cause (premature conclusion-writing). The agent can satisfy the check by making the risk section agree with an overoptimistic conclusion.
5. **Canonical doc contradiction (#7)** — The `rg` sweep is effective for known changes, but the agent may not realize it made an architectural change (e.g., subtly changing a return type doesn't feel like "changing an architectural pattern").

### 5.3 Three Improvements to Close Remaining Gaps

**Improvement 1: Structured Evidence Template (addresses #1, #3, #5)**

Replace free-text handoff sections with a machine-parseable format:

```markdown
## AC Verification (auto-populated)
| AC | Claim | Verified At | Command Output |
|---|---|---|---|
| AC-1 | Portfolio CRUD works | `packages/core/src/routes/portfolios.py:45` | `rg "async def create_portfolio" → match` |
| AC-2 | Dedup enforced | `tests/integration/test_portfolios.py:23` | `pytest test_portfolios.py::test_duplicate_rejection → PASS` |

## Conclusion Derivation
- Unresolved risks: {list}
- Conclusion: {MUST be logically consistent with unresolved risks list}
```

This forces the conclusion to be *derived from* the evidence rather than written independently.

**Improvement 2: Risk-Tiered Protocol (addresses over-verification paralysis)**

Add a tier selector at the top of the pre-handoff review skill:

```
MEU Risk Tier:
- TIER 1 (entity/DTO/value objects): Steps 1, 3, 6 only
- TIER 2 (service/infrastructure/config): Steps 1, 3, 5, 6
- TIER 3 (route/API/MCP handler): All steps
```

This prevents the protocol from adding disproportionate overhead to simple MEUs while maintaining full coverage for the MEU types that historically caused the most review passes.

**Improvement 3: Category Log with Bounded Search (addresses #6)**

Replace the open-ended "rg for all instances" with a structured process:

```
When fixing any finding:
1. Log: "{category}: {file}:{line}" to session-categories.md
2. Search scope: same package + explicitly listed sibling packages in meu-registry
3. Maximum search depth: 2 hops from original file's package
4. Cross-package instances → log as "noted, out of scope" with reference
5. At session end: review category log for patterns spanning 3+ files → flag for dedicated cleanup MEU
```

### 5.4 Realistic Pass Reduction Estimate

**Target of 2–3 passes is optimistic. Realistic estimate: 3–5 passes.**

Reasoning:

- **Passes 1–2 will be eliminated** by evidence freshness (no more stale counts), error mapping completeness (concrete checklist), and lifecycle ordering (simple rule).
- **Passes 3–5 will be reduced but not eliminated** because claim-to-state drift and fix-specific-not-general are behavioral patterns that require metacognitive shifts. The first few sessions with the new protocol will see improvement as the novelty effect keeps the agent attentive, but over time, checklist fatigue will degrade compliance.
- **Pass 6+ is unlikely** with the protocol in place, which is still a significant improvement from the 9–11 pass outliers.

**Distribution estimate**:
- Entity/DTO MEUs: 1–2 passes (unchanged — these already passed quickly)
- Service/infrastructure MEUs: 2–4 passes (down from 5–10)
- Route/API MEUs: 3–5 passes (down from 7–11)

**Weighted average**: ~3–4 passes across a mixed 4-MEU project, down from ~6.2. This is a 40–50% improvement, which is substantial even if it doesn't reach the 2–3 target.

### 5.5 Rules That Should Be Removed or Modified

**1. Remove: Duplicate instructions across documents.**

Coder rules 8, 9, 10 duplicate pre-handoff Steps 4, 7, and 2 respectively. The coder.md version runs *during* implementation; the pre-handoff version runs *before submission*. Having both means the agent either does the work twice (waste) or assumes the first pass was sufficient (defeats the pre-handoff purpose). **Recommendation**: Keep only the pre-handoff version. The coder.md version should say "see pre-handoff review protocol" rather than restating the rules.

**2. Modify: `__getattr__` prohibition (Coder rule 10, meu-handoff Stub Quality Gate)**

Narrow from absolute prohibition to: "No `__getattr__` that silently returns values for undefined methods. Explicit-error `__getattr__` (raising `AttributeError` or `NotImplementedError` with method name) is permitted."

**3. Modify: Anti-premature-stop rule (GEMINI.md)**

The current rule ("complete ALL workflow exit criteria in a single continuous pass") conflicts with context window limits on large multi-MEU projects. Add an escape valve: "If context window exceeds 80% capacity, save state to pomera_notes, complete the current MEU's handoff, and notify the human with remaining work. This is not an early termination — it's a planned checkpoint."

**4. Remove: The "Max Revision Cycles: 2" rule in meu-handoff.md is aspirational, not actionable.**

If the pre-handoff protocol is working, the cycle count will naturally decrease. The hard cap of 2 creates a perverse incentive: if the agent knows it only gets 2 chances, it might over-invest in the first pass (paralysis) or rush the second pass (quality degradation). Let the cycle count be an *observed metric*, not a constraint.

---

## Summary Table

| Pattern | Classification | Most/Least Effectively Reduced | Key Risk |
|---|---|---|---|
| 1. Claim-to-state drift | Behavioral | Least (rank 2) | Superficial rg matching |
| 2. Artifact incompleteness | Structural | Most (rank 5) | Low risk |
| 3. Evidence staleness | Process + Structural | Most (rank 1) | Low risk |
| 4. Mock masking | Behavioral | Least (rank 3) | Trivial integration tests |
| 5. Scope overstatement | Behavioral | Least (rank 4) | Conclusion-risk agreement gaming |
| 6. Fix-specific-not-general | Behavioral + Process | Least (rank 1) | Unbounded search scope |
| 7. Canonical doc contradiction | Structural | Least (rank 5) | Unrecognized arch changes |
| 8. Stub inadequacy | Structural | Most (rank 4) | Over-broad prohibition |
| 9. Error mapping gaps | Structural | Most (rank 2) | Low risk |
| 10. Lifecycle ordering | Process | Most (rank 3) | Low risk |
