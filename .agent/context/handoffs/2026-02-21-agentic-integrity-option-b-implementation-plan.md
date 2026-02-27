# Agentic Integrity — Option B Implementation

Add process-hardening controls and automated guards to prevent drift, false completion, and silent deferral during agentic execution. All changes are documentation/script only — no application code is modified.

**Source:** [Handoff: Feature Validation + Agentic Integrity Research](file:///p:/zorivest/.agent/context/handoffs/2026-02-21-docs-build-plan-feature-validation-and-agentic-integrity-research.md)

---

## Proposed Changes

### Build Plan — Overview & Testing

#### [MODIFY] [00-overview.md](file:///p:/zorivest/docs/build-plan/00-overview.md)

Add `## Execution Integrity Gates` section after the existing `## Cross-References` section (after line 95). Contents:

1. **Feature Intent Contract (FIC)** requirement — every planned feature must have:
   - Intent statement (what must be true for users)
   - Acceptance criteria (concrete, testable)
   - Negative cases (what must NOT happen)
   - Observable outputs (what evidence proves correctness)
   - Test mapping (exact test/eval proving each criterion)
2. Phase-exit criterion: "all FIC criteria mapped to passing tests/evals with evidence links"

---

#### [MODIFY] [testing-strategy.md](file:///p:/zorivest/docs/build-plan/testing-strategy.md)

Add `## Drift-Resistant Feature Validation` section at the end of the file (after line 282). Contents:

1. **Contract Tests** — CDC provider verification (Pact) for REST API contracts between Python backend and TypeScript MCP/GUI
2. **Property-Based Tests** — Hypothesis for domain invariants and calculator edge cases
3. **Mutation Testing** — mutmut (Python core), StrykerJS (TypeScript) with threshold ratcheting starting at 60%
4. **Feature Eval Suites** — FAIL_TO_PASS (intended changes must now pass) + PASS_TO_PASS (unchanged behavior must still pass) regression tracking
5. Per-feature validation matrix template

> [!NOTE]
> This section documents the *planned* validation stack. Actual tooling installation (Tier 3) is deferred until source code exists.

---

### Distribution

#### [MODIFY] [07-distribution.md](file:///p:/zorivest/docs/build-plan/07-distribution.md)

Add `## 7.18 Branch Protection Required Checks` section at the end of the file (after line 648). Contents:

1. Required status checks before merge to `main`:
   - `lint-python` / `lint-mcp-server` / `lint-ui` (existing ci.yml jobs)
   - `test-python` / `test-mcp-server` / `test-ui` (existing ci.yml jobs)
   - `feature-eval` (new: FAIL_TO_PASS + PASS_TO_PASS regression suite)
   - `contract-verify` (new: Pact provider verification)
   - `mutation-score` (new: mutmut/StrykerJS threshold check)
   - `evidence-manifest` (new: verify evidence bundle in handoff)
2. Note that new jobs are planned for Phase 7+ and will be added to ci.yml as code arrives

---

### Agent Workflow & Configuration

#### [MODIFY] [orchestrated-delivery.md](file:///p:/zorivest/.agent/workflows/orchestrated-delivery.md)

Add two new sections before the existing `## Completion Criteria`:

1. **Evidence-First Completion Protocol** (after line 43):
   - Task cannot be marked `done` without an attached evidence bundle
   - Evidence bundle must include: changed files, command list executed, test/eval results, artifact references, independent reviewer verdict
   - Narrative status alone cannot close a task

2. **No-Deferral Without Replan** (immediately after):
   - If implementation is blocked, task status becomes `blocked`, never `done`
   - Must create replacement scoped task with `owner_role`, `deliverable`, `validation`, `status`
   - Ban unresolved placeholders (`TODO`, `NotImplementedError`, empty catches, `pass # placeholder`, skeleton stubs) in completed tasks

---

#### [MODIFY] [GEMINI.md](file:///p:/zorivest/GEMINI.md)

Add rules to the existing `## Execution Contract` section (after line 75):

- `task.md` items may never be marked `[x]` if the implementation contains `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs
- Blocked items must use status `blocked` + linked follow-up task in handoff
- Completion requires evidence bundle (changed files + commands + test results) in handoff or walkthrough

---

### Handoff Template

#### [MODIFY] [TEMPLATE.md](file:///p:/zorivest/.agent/context/handoffs/TEMPLATE.md)

Add evidence fields under the existing Tester and Reviewer output sections:

**Under Tester Output** (after line 36):
- `Evidence bundle location:`
- `FAIL_TO_PASS / PASS_TO_PASS result:`
- `Mutation score:`
- `Contract verification status:`

**Under Reviewer Output** (after line 43):
- `Anti-deferral scan result:`

---

### Reviewer Role

#### [MODIFY] [reviewer.md](file:///p:/zorivest/.agent/roles/reviewer.md)

Add `## Adversarial Verification Checklist` section after the existing `## Must Do` section (after line 25). Items:

1. Confirm claimed behavior with failing-then-passing proof (test existed that failed → now passes)
2. Verify no bypass hacks (monkeypatching tests, forced early exits, mocked-out assertions)
3. Verify changed code paths are exercised by assertions (not just executed without checks)
4. Verify no skipped/xfail-only masking (tests exist but are marked `skip` or `xfail`)
5. Verify no unresolved `TODO`/`FIXME`/`NotImplementedError` in completed deliverables

---

### Validation Script

#### [MODIFY] [validate.ps1](file:///p:/zorivest/validate.ps1)

Add two new blocking checks after the existing 6 blocking checks and before the advisory section (after line 47):

1. **Anti-Placeholder Scan** (`[7/8]`): Use `rg` (ripgrep) to scan `packages/` and `src/` for `TODO`, `FIXME`, `NotImplementedError`, `pass  # placeholder`, `...  # placeholder`. Fail if any matches found. Renumber existing advisory section header.
2. **Evidence Bundle Check** (`[8/8]`): Parse the most recent handoff file in `.agent/context/handoffs/` for required fields (`Evidence bundle location`, `Pass/fail matrix`, `Commands run`). Warn (advisory, not blocking) if fields are empty or missing. This is advisory because handoff files may not exist during early development.

> [!IMPORTANT]
> The anti-placeholder scan is **blocking** (exit 1 on match). The evidence bundle check is **advisory** (report only).

---

## Verification Plan

### Automated

1. **PowerShell syntax check** — verify `validate.ps1` parses without errors:
   ```powershell
   pwsh -NoProfile -Command "& { $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw 'validate.ps1'), [ref]$null) }"
   ```
2. **Anti-placeholder scan dry run** — test the new check against a clean codebase:
   ```powershell
   rg -c "TODO|FIXME|NotImplementedError" packages/ src/
   ```
   Expected: zero matches (or expected matches in comments/docs only)

### Manual

1. **Markdown rendering** — Open each modified `.md` file in VS Code preview and verify:
   - New sections have correct heading hierarchy
   - Tables render properly
   - No broken links or formatting
2. **Workflow completeness** — Read the updated `orchestrated-delivery.md` end-to-end and confirm:
   - Evidence-First Completion Protocol is clear and actionable
   - No-Deferral Without Replan is unambiguous
   - Completion Criteria references the new protocols
