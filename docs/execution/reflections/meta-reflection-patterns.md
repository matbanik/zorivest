# Meta-Reflection — Cross-Project Pattern Analysis

> Scope: All 7 implementation critical review handoffs (2026-03-07 through 2026-03-11)
> Total review passes analyzed: 37+
> Date: 2026-03-11

## Purpose

This reflection synthesizes recurring patterns across ALL implementation critical reviews to date. Individual project reflections capture per-project lessons; this document captures the **systemic** patterns that the individual reflections don't fully address because they span multiple projects.

## The 10 Recurring Patterns

### Pattern 1: Claim-to-State Drift (7/7 reviews)

**What it is**: The handoff claims an AC is "met" or "verified" but the actual code doesn't satisfy it.

**Examples**:
- MEU-6: Missing defaults for `caption` and `snapshot_datetime` despite "all 20 ACs covered"
- MarketDataPort: Returns `Any` instead of typed DTOs
- MEU-8: Claims "all Decimal arithmetic" when code uses floats internally

**Root cause**: Opus validates against test greenness and memory of what was implemented, not against the actual spec text and file state.

**Rule**: For each AC, `rg` the actual code and quote `file:line`. Never rely on memory alone.

---

### Pattern 2: Project Artifact Incompleteness (6/7 reviews)

**What it is**: Post-project artifacts (BUILD_PLAN.md counts, task.md completion, reflection, metrics) don't match actual state.

**Examples**:
- BUILD_PLAN.md summary says Phase 5 has "1 completed MEU" when rows show all MEUs complete
- task.md marks MEU gate complete while `validate_codebase.py` still exits non-zero
- Multiple projects had reflections created before Codex validation finished

**Root cause**: Opus treats implementation code as the finish line, not the full project lifecycle.

**Rule**: Don't create lifecycle artifacts (reflection, metrics) until after Codex validation completes.

---

### Pattern 3: Evidence Staleness (6/7 reviews)

**What it is**: Test counts, lint warnings, or regression totals in the handoff are wrong.

**Examples**:
- Toolset-registry: 5 different evidence count mismatches across 9 rechecks
- Market-data: "690 passed" when actual repo shows 692
- Multiple projects: commit message says "35 new tests" when actual count is 39

**Root cause**: Opus records counts at write time but doesn't re-verify after code changes.

**Rule**: Re-run ALL commands after ALL fixes and paste fresh counts into the handoff.

---

### Pattern 4: Mock-Based Test Masking (5/7 reviews)

**What it is**: Unit tests pass because services are mocked, but the live runtime is broken.

**Examples**:
- REST API: 9 extra passes because mocks hid unlock state propagation, stub completeness, exception mapping
- Commands: import-surface ACs only asserted symbol exports, not forbidden imports
- Settings-backup: Tests used fake doubles, not real SQLAlchemy infrastructure

**Root cause**: Opus writes tests that prove the happy path but not the runtime contract.

**Rule**: Every route MEU must include at least one `TestClient(raise_server_exceptions=False)` integration test without dependency overrides.

---

### Pattern 5: Scope Overstatement (5/7 reviews)

**What it is**: Handoff says "implementation complete" while residual risk acknowledges known incomplete items.

**Examples**:
- Toolset-registry: "Implementation complete" while `wrapRegister()` discards all handles
- REST API: MEU-26 labeled "Full 04c Envelope-Encryption Contract" when it was a stub
- Settings-backup: "Complete" while PBKDF2 used instead of spec'd Argon2id

**Root cause**: Opus conflates "code exists" with "contract satisfied."

**Rule**: If residual risk acknowledges gaps, conclusion MUST NOT say "implementation complete."

---

### Pattern 6: Fix-Specific-Not-General (meta-pattern)

**What it is**: Opus fixes the specific instance cited by Codex but doesn't check all other instances of the same category.

**Examples**:
- REST API: Codex says "this route returns 500 for NotFoundError" → Opus fixes that route but not the 5 others with the same bug
- Toolset-registry: Codex finds stale evidence count in body → Opus fixes body but not commit message or task.md

**Root cause**: Opus treats each finding as a point fix rather than a category to sweep.

**Rule**: Before fixing, categorize. Then `rg` for all instances of the same category. Fix them all.

---

### Pattern 7: Canonical Doc Contradiction (3/7 reviews)

**What it is**: When Opus changes an architectural pattern, it doesn't update all canonical docs that reference the old pattern.

**Examples**:
- Toolset-registry: MCP-local tokens implemented but 7 build-plan docs still referenced REST/HMAC model — cost 3 extra rechecks just for doc consistency
- REST API: Non-canonical router tags invented without checking spec

**Root cause**: Opus changes the primary file but doesn't grep for cross-references.

**Rule**: After any architectural change, `rg` for the old pattern across all canonical docs.

---

### Pattern 8: Stub Inadequacy (3/7 reviews)

**What it is**: Stubs compile and make tests pass but violate behavioral contracts.

**Examples**:
- REST API: `__getattr__` catch-all made everything compile but silently violated service invariants
- REST API: `save()` discarded writes, creating false 201→404 inconsistency
- REST API: `exists()` returned `None` (falsy), bypassing dedup checks

**Root cause**: Opus uses structural stubs (match interface) rather than behavioral stubs (match contract).

**Rule**: Stubs must honor behavioral contracts. `__getattr__` catch-alls are prohibited.

---

### Pattern 9: Error Mapping Gaps (3/7 reviews)

**What it is**: Routes don't map domain exceptions to proper HTTP status codes.

**Examples**:
- `NotFoundError → 500` instead of 404
- `BusinessRuleError → 500` instead of 409
- `ValueError → 500` instead of 422

**Root cause**: Opus implements the happy path and doesn't add exception handlers for error cases.

**Rule**: Every write-adjacent route must map ALL domain exceptions.

---

### Pattern 10: Lifecycle Ordering (3/7 reviews)

**What it is**: Post-project artifacts created before Codex validation completes.

**Examples**:
- domain-entities-ports: Reflection and metrics created before Codex validated
- Multiple projects: task.md marked complete before gate command exits 0

**Root cause**: Opus wants to complete the session in one pass.

**Rule**: Post-project artifacts (reflection, metrics) MUST be created AFTER Codex validation.

---

## Impact Matrix

| Pattern | Frequency | Avg Extra Passes | Type |
|---------|-----------|-----------------|------|
| Claim-to-State Drift | 7/7 | +2-3 | Behavioral |
| Artifact Incompleteness | 6/7 | +1-2 | Process |
| Evidence Staleness | 6/7 | +1 | Process |
| Mock-Based Test Masking | 5/7 | +3-5 | Structural |
| Scope Overstatement | 5/7 | +1-2 | Behavioral |
| Fix-Specific-Not-General | meta | multiplier | Behavioral |
| Canonical Doc Contradiction | 3/7 | +2-3 | Process |
| Stub Inadequacy | 3/7 | +3-5 | Structural |
| Error Mapping Gaps | 3/7 | +1-2 | Structural |
| Lifecycle Ordering | 3/7 | +1 | Process |

**Behavioral patterns** (1, 5, 6) require instruction/prompt changes.
**Process patterns** (2, 3, 7, 10) require workflow/checklist changes.
**Structural patterns** (4, 8, 9) require code practice changes.

## Actions Taken

1. **execution-session.md**: Added Step 4b Pre-Handoff Self-Review Protocol
2. **meu-handoff.md**: Added Live Runtime Probe Requirements + Stub Quality Gate
3. **critical-review-feedback.md**: Added DR-6/7/8 + IR-1..IR-4 Implementation Review Checklist
4. **planning-corrections.md**: Added Step 2b Categorize + Step 5b Evidence Refresh + Step 5c Cross-Doc Sweep + Hard Rule #8
5. **coder.md**: Added rules 8/9/10 (fix-general, error mapping, stub quality)
6. **GEMINI.md**: Added Pre-Handoff Self-Review subsection + skill registration
7. **`.agent/skills/pre-handoff-review/SKILL.md`**: New skill with 7-step protocol

## Expected Outcome

Average passes without these rules: **6.2** (37 passes / 6 projects with findings).
Target with rules: **2-3 passes** (first pass catches most issues via self-review).
