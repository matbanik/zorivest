---
date: "2026-04-27"
project: "approval-security"
meus: ["MEU-PH11", "MEU-PH12", "MEU-PH13"]
plan_source: "docs/execution/plans/2026-04-27-approval-security/implementation-plan.md"
template_version: "2.0"
---

# 2026-04-27 Meta-Reflection

> **Date**: 2026-04-27
> **MEU(s) Completed**: MEU-PH11 (CSRF Approval Token), MEU-PH12 (MCP Scheduling Gap Fill), MEU-PH13 (Emulator Validate Hardening)
> **Plan Source**: docs/execution/plans/2026-04-27-approval-security/implementation-plan.md

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   The PH11 wiring bug surfaced by the user *after* all three MEUs were marked complete, and it required post-hoc diagnosis of a cross-process env var propagation failure. The root cause (Electron sets `ZORIVEST_APPROVAL_CALLBACK_PORT` in its own process memory, but the API is a sibling process via `concurrently`) was an architectural blindspot that the TDD tests, the pre-handoff review, and the MEU gate all failed to catch. Fixing it post-completion took ~30 minutes of context recovery plus 3 file edits.

2. **What instructions were ambiguous?**
   None of the instructions are ambiguous — the failure was not one of unclear spec. The problem was a gap between the acceptance criteria and the actual system behavior. AC-5 through AC-7 tested the *middleware* in isolation (mock `app.state`), and AC-10/AC-11 tested the *renderer* IPC flow in isolation (mock IPC bridge). No AC tested the **startup wiring** — i.e., that `main.py` actually instantiates `ApprovalTokenValidator` and sets it on `app.state`.

3. **What instructions were unnecessary?**
   N/A — all instructions were appropriate for the session scope.

4. **What was missing?**
   Five gaps identified:

   (a) **No integration-level AC for startup wiring.** The implementation plan (L89–102) lists `packages/api/src/zorivest_api/main.py` as a "modify" target (line 94: "pass port to FastAPI") but this never became an AC. The plan said it should happen, but since there was no testable acceptance criterion, the TDD cycle never wrote a test for it, and the implementation never did it.

   (b) **No test for the full approval round-trip.** Every PH11 test mocked either the Electron side or the API side. There was no integration test that starts the API, generates a real token, and calls the approve endpoint end-to-end.

   (c) **Handoff lied by omission.** The handoff (L86-88) states "Risks / Known Issues: None identified. All quality gates green." — but the `main.py` wiring was never done. The handoff explicitly omits PH11 from its Changed Files section (only PH12 and PH13 are listed). This should have been caught by pre-handoff review Step 1 (Contract Verification): *"For each AC, verify it against actual code with both a test reference AND an implementation reference."*

   (d) **`outcome: success` in the instruction coverage YAML was false.** The session ended with a broken feature that the user discovered immediately upon testing. The YAML should have flagged the known issue.

   (e) **Reflection was skeletal.** The original reflection contained only the instruction coverage YAML block — no friction log, no quality signal log, no pattern extraction, no efficiency metrics. This violated the Template-First Rule (AGENTS.md L436-448) and RULE-ICR1 from the prior reflection.

5. **What did you do that wasn't in the prompt?**
   The post-mortem fix for the approval wiring (3 files: `main.py`, `index.ts`, `package.json`) was done as an ad-hoc hotfix when the user reported 403 errors.

### Quality Signal Log

6. **Which tests caught real bugs?**
   - `test_emulator_validate_hardening.py` caught a schema version mismatch — policies with only `FetchStep` needed `schema_version: 2` for the `PolicyDocument` model_validator, which was not in the original test fixture.
   - `scheduling-gap-fill.test.ts` caught that `z.object().strict()` blocks direct `.shape` access for field validation — tests had to use `.unwrap()` or adapt the assertion strategy.

   **No test caught the PH11 wiring failure.** This is the critical quality signal miss.

7. **Which tests were trivially obvious?**
   AC-8 (cleanup interval removes expired tokens) and AC-12 (ADR document exists) were low-signal tests — they verified trivial implementation details rather than behavioral contracts.

8. **Did pyright/ruff catch anything meaningful?**
   No. Both passed clean. The wiring bug was a runtime-only issue — `getattr(app.state, "approval_token_validator", None)` returns `None` silently, which is syntactically valid but functionally broken.

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Partially. The FIC correctly specified 12 acceptance criteria for PH11 and caught the IPC token format, single-use, TTL, and policy-scoping requirements. However, it had a critical gap: **no AC covered API startup wiring**. The files-modified table listed `main.py` as a target, but this was a description of planned changes, not a testable criterion. The FIC-to-code traceability broke at the seam between "what the plan says to modify" and "what the ACs actually validate."

10. **Was the handoff template right-sized?**
    The handoff was ~90 lines (~2,000 tokens), within the standard verbosity tier. However, it was **structurally dishonest** — it listed "Risks / Known Issues: None identified" while the PH11 Changed Files section was entirely absent. The pre-handoff review skill should have flagged this: Step 1 requires *"For each AC, verify it against actual code"* — if the agent had verified AC-7 (approve with valid token succeeds) against `main.py`, it would have found the validator was never instantiated.

11. **How many tool calls did this session take?**
    Approximately 90+ tool calls across planning corrections, 3 MEU TDD cycles, and post-completion admin tasks. The session also consumed significant context on plan review corrections (3 rounds of `/plan-corrections`).

---

## Root Cause Analysis: PH11 Wiring Failure

### The Bug

After implementing all PH11 components (token manager, IPC handlers, middleware, renderer flow, internal HTTP server), the `POST /policies/{id}/approve` endpoint returned 403 Forbidden for all requests. The API log showed:

```
No approval_token_validator configured in app state.
Rejecting token — validator must be initialized at startup.
```

### Why It Happened: 3-Layer Failure Chain

**Layer 1: Acceptance Criteria Gap**

The implementation plan (L89–102) correctly identified `main.py` as a file to modify, with the summary "pass port to FastAPI." But this was never converted to a testable AC. The 12 ACs (AC-1 through AC-12) all test individual components in isolation:

| AC Range | What's tested | What's NOT tested |
|----------|--------------|-------------------|
| AC-1..4, 8 | Token manager (Electron, in-memory) | N/A |
| AC-5..7 | FastAPI middleware (mock `app.state`) | Whether `app.state` is actually populated |
| AC-9 | HTTP server binding (127.0.0.1) | Whether API knows the port |
| AC-10..11 | Renderer IPC flow (mock Electron) | N/A |
| AC-12 | ADR document exists | N/A |

**No AC tests the wiring seam:** "When the app starts, `ApprovalTokenValidator` is created and set on `app.state`."

This is a violation of AGENTS.md §Boundary Input Contract, which requires enumerating "all write surfaces" and their "schema owner." The approval token flow crosses a process boundary (Electron → API via env var → HTTP callback) that was never inventoried as a boundary surface.

**Layer 2: TDD Cycle Faithfully Followed a Defective Spec**

The TDD cycle (Red → Green → Refactor) worked perfectly — *for the ACs that existed.* All 10 PH11 tests passed. The MEU gate (8/8 checks) passed. But TDD can only catch what the FIC specifies. Since the FIC had a wiring gap, TDD could not catch a wiring failure.

This is a known limitation of TDD documented in the testing literature: unit tests with mocked dependencies verify contracts, not integration. The instruction set addresses this in AGENTS.md L251 ("Prefer real objects over mocks when feasible. Heavy mocking masks real failures") — but this guidance was not followed for PH11. The `test_approval_token_middleware.py` mocks `app.state` to inject the validator, which is exactly the code path that broke in production.

**Layer 3: Pre-Handoff Review Skipped or Shallow**

AGENTS.md §285-297 requires: *"For each AC, verify the claim against actual file state (quote file:line, not memory)."*

The pre-handoff review skill (Step 1) requires: *"Each AC must map to a test assertion covering the behavior AND an implementation reference."*

If AC-7 ("approve with valid token succeeds") had been verified against `main.py`, the reviewer would have found that `main.py` has zero references to `approval_token_validator` — it's never instantiated. The handoff claiming "Risks / Known Issues: None identified" while `main.py` was never modified is a Step 1 failure.

### Cross-Process Env Var Propagation

Even if `main.py` had read `ZORIVEST_APPROVAL_CALLBACK_PORT`, the dev-mode startup (`npm run dev` via `concurrently`) launches API and Electron as **sibling** processes. The Electron process sets the env var at runtime (`process.env.ZORIVEST_APPROVAL_CALLBACK_PORT = String(port)` at index.ts L274), but this only affects its own process memory — it is never visible to the API process.

In production, Electron starts the API as a child process via `pythonManager.start()`, so env vars would inherit. The implementation plan assumed the production model without testing the dev-mode model. This is a classic environment-parity gap.

### Instruction-Level Responsibility

| Instruction | Should Have Caught | Why It Didn't |
|------------|-------------------|----------------|
| §Boundary Input Contract | `env/config input` boundary not inventoried | Plan boundary table only listed REST headers and IPC args, not the env var bridge |
| §Pre-Handoff Self-Review L289 | AC-7 → `main.py` has no validator init | Review was shallow — handoff omits PH11 Changed Files entirely |
| §Testing (L251) "Prefer real objects over mocks" | `test_approval_token_middleware.py` mocks `app.state` | Guidance is advisory, not enforced by workflow step |
| §Evidence-first completion (L259) | "implementation complete" claim without `main.py` evidence | MEU gate checks test results, not implementation completeness |

---

## Root Cause Analysis: Skeletal Reflection

### The Bug

The reflection file contained only the instruction coverage YAML — 47 lines total. No frontmatter, no friction log, no quality signals, no pattern extraction, no metrics, no rules adherence table. Previous reflections average 150-260 lines.

### Why It Happened

**Template-First Rule violation.** AGENTS.md L436-448 states:

> **Before creating ANY handoff, reflection, or review file, `view_file` its canonical template.** Do NOT write artifacts from memory.

The agent never called `view_file` on `docs/execution/reflections/TEMPLATE.md` before writing the reflection. It wrote the instruction coverage YAML from memory and treated that as the complete artifact.

**Contributing factor: AGENTS.md L486-506 says "Output exactly one ```yaml ... ``` block. No prose around it."** This instruction, placed in the §Instruction Coverage Reflection section at EOF, creates a conflict with the Template-First Rule. The agent followed the narrow EOF instruction ("emit YAML, no prose") without consulting the template which shows the YAML is only one section of a 7-section document.

**Contributing factor: Context pressure.** The session was long (3 MEUs + plan corrections) and the reflection was written at the tail end, likely under context window pressure. The completion-preflight skill checks for structural markers (`sections:`, `loaded:`, `decisive_rules:`) in the YAML — but it does NOT check for the template-mandated prose sections (Friction Log, Pattern Extraction, etc.).

### Instruction-Level Responsibility

| Instruction | Should Have Caught | Why It Didn't |
|------------|-------------------|----------------|
| Template-First Rule (L436-448) | Must `view_file` TEMPLATE.md before writing | Rule was not followed — wrote from memory |
| RULE-ICR1 (prior reflection) | "Always view_file schema AND template" | Session-local rule from prior session, not in AGENTS.md core |
| Completion-preflight skill | Should check for template sections | Only checks for YAML structural markers, not prose sections |
| §Instruction Coverage (L486-506) | "No prose around it" creates ambiguity | This instruction is about the YAML block specifically, but reads as "the reflection is just YAML" |

---

## Pattern Extraction

### Patterns to KEEP
1. **Backward-compatible constructor defaults.** Adding `email_config_checker: Callable | None = None` avoided breaking 12 existing emulator tests. This pattern should be standard for any new dependency injection.
2. **`.strict()` Zod schemas for MCP tools.** Prevents field injection attacks and caught test fixture issues early.
3. **FIC boundary inventory table.** The PH12 and PH13 boundary tables correctly identified all write surfaces — the failure was PH11-specific.

### Patterns to DROP
1. **Mocking `app.state` in middleware tests without a corresponding integration test.** The mock hid the fact that `app.state.approval_token_validator` was never set. At minimum, one test should use `create_app()` / `TestClient` and verify the real startup wiring.
2. **Omitting Changed Files sections from handoffs.** PH11's changed files were entirely absent from the handoff, which made the pre-handoff review unable to cross-reference implementation claims.

### Patterns to ADD
1. **Startup wiring AC for any feature that registers on `app.state`.** If the plan says "modify main.py to wire X," there must be an AC that asserts `app.state.X is not None` after startup.
2. **Dev-mode environment parity testing.** Any feature that relies on env var propagation between processes must be tested under both production (child process) and dev (sibling process) models.
3. **Reflection prose check in completion-preflight.** The skill should verify that the reflection file contains `## Execution Trace`, `## Pattern Extraction`, and `## Efficiency Metrics` — not just YAML markers.

### Calibration Adjustment
- Estimated time for 3 MEUs: ~4 hours
- Actual time: ~6 hours (3 rounds of plan corrections + 3 MEU TDD cycles + post-completion hotfix + investigation)
- Adjusted estimate for similar cross-process security MEUs: 5 hours + 1 hour buffer for integration gaps

---

## Next Session Design Rules

```
RULE-WIRING1: Every AC set that modifies main.py must include a startup wiring AC
SOURCE: PH11 wiring failure — plan listed main.py as modified but no AC validated the wiring
EXAMPLE: BEFORE → AC-5..7 test middleware in isolation | AFTER → AC-N: "After app startup, app.state.X is not None"
```

```
RULE-ENVPROP1: Features crossing process boundaries must inventory the transport mechanism as a boundary surface
SOURCE: PH11 env var propagation — ZORIVEST_APPROVAL_CALLBACK_PORT set in Electron, invisible to sibling API process
EXAMPLE: BEFORE → boundary table lists only REST headers | AFTER → boundary table includes "env/config input: ZORIVEST_APPROVAL_CALLBACK_PORT"
```

```
RULE-REFL1: Completion-preflight must verify reflection contains template-mandated sections
SOURCE: Skeletal reflection — YAML-only file passed completion-preflight structural checks
EXAMPLE: BEFORE → check for "sections:" marker | AFTER → also check for "## Execution Trace", "## Pattern Extraction", "## Efficiency Metrics"
```

---

## Next Day Outline

1. **Target MEU(s)**: Codex validation of PH11/PH12/PH13 handoff, then next project selection
2. **Scaffold changes needed**: None
3. **Patterns to bake in**: RULE-WIRING1 (startup AC), RULE-ENVPROP1 (boundary inventory for env vars), RULE-REFL1 (reflection prose check)
4. **Codex validation scope**: PH11 wiring fix verification (approve flow works end-to-end), PH12 MCP tools, PH13 emulator hardening
5. **Time estimate**: 1 hour for Codex validation handoff + corrections
6. **Risk**: PH11 wiring fix needs manual verification (the approval buttons must work in the running app)

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~90 |
| Time to first green test | ~20 min (PH11 token manager) |
| Tests added | 19 (5 TS token + 3 Py middleware + 2 TS renderer + 9 MCP + 8 emulator) |
| Codex findings | Pending |
| Handoff Score (X/7) | 3/7 (see table below) |
| Rule Adherence (%) | 55% (see table below) |
| Prompt→commit time | Not committed (pending Codex validation) |

### Rules Sampled for Adherence Check

| Rule | Source | Followed? |
|------|--------|-----------|
| Template-First Rule for reflection | AGENTS.md §436-448 | **No** — wrote YAML-only reflection without reading TEMPLATE.md |
| Pre-handoff review Step 1 (AC-to-code match) | pre-handoff-review SKILL.md §Step 1 | **No** — handoff omits PH11 Changed Files; AC-7 never verified against main.py |
| Prefer real objects over mocks | AGENTS.md §251 | **No** — PH11 middleware tests mock app.state, hiding the wiring gap |
| Boundary Input Contract | AGENTS.md §200-211 | **No** — env var bridge not inventoried as boundary surface |
| Terminal redirect pattern | AGENTS.md §P0 | **Yes** — all commands used `*>` redirect pattern |
| Tests first, implementation after | AGENTS.md §215 | **Yes** — Red→Green cycle followed for all 3 MEUs |
| Anti-premature-stop | AGENTS.md §264-271 | **Partial** — all tasks marked [x], but completion was premature (wiring bug shipped) |
| Evidence-first completion | AGENTS.md §259 | **No** — "Risks: None identified" was false; main.py wiring missing |
| FIC-before-code | AGENTS.md §232 | **Yes** — FICs written for all 3 MEUs before implementation |
| Anti-placeholder enforcement | AGENTS.md §261 | **Yes** — `rg` scan clean |

---

## Instruction Coverage

<!-- Emit a single fenced YAML block matching .agent/schemas/reflection.v1.yaml -->
<!-- See AGENTS.md § Instruction Coverage Reflection for rules -->

```yaml
schema: v1
session:
  id: "738f04c0-5c69-42ab-997e-3ac615a592f1"
  task_class: "tdd"
  outcome: "partial"
  tokens_in: 0
  tokens_out: 0
  turns: 11
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3  # Red→Green cycle driven by this section; but mocking guidance (L251) was not followed for PH11
  - id: execution_contract
    cited: true
    influence: 3  # MEU gate, anti-placeholder scan, evidence-first rule — all followed, but pre-handoff review was shallow
  - id: session_discipline
    cited: true
    influence: 2  # Session-end checklist followed for context files, but reflection was skeletal
  - id: operating_model
    cited: true
    influence: 2  # Mode transitions (PLANNING→EXECUTION→VERIFICATION) followed
  - id: planning_contract
    cited: true
    influence: 2  # Boundary Input Contract applied to PH12/PH13 but missed env var bridge for PH11
  - id: pre_handoff_self_review_mandatory
    cited: false
    influence: 0  # NOT consulted — this is the primary failure. Step 1 would have caught the AC-to-main.py gap
  - id: priority_0_system_constraints_non_negotiable
    cited: true
    influence: 2  # Terminal redirect followed on all commands
  - id: code_quality
    cited: true
    influence: 1  # Docstrings, error handling, structured logging applied
  - id: architecture
    cited: true
    influence: 1  # Dependency rule followed; cross-process boundary not analyzed
  - id: project_context
    cited: false
    influence: 0
  - id: communication_policy
    cited: false
    influence: 0
  - id: dual_agent_workflow
    cited: true
    influence: 1  # Handoff structured for Codex validation
  - id: validation_pipeline
    cited: true
    influence: 2  # MEU gate ran 8/8 — but MEU gate does not check startup wiring
  - id: artifact_naming_convention
    cited: true
    influence: 1  # Template-First Rule violated for reflection
  - id: skills
    cited: true
    influence: 2  # terminal-preflight, quality-gate invoked; completion-preflight invoked but insufficient
  - id: commits
    cited: false
    influence: 0  # No git operations
  - id: mcp_servers
    cited: false
    influence: 0
loaded:
  workflows: [tdd_implementation, plan_corrections]
  roles: [orchestrator, coder, tester, reviewer]
  skills: [terminal_preflight, quality_gate, completion_preflight]
  refs:
    - docs/execution/plans/2026-04-27-approval-security/implementation-plan.md
    - docs/execution/plans/2026-04-27-approval-security/task.md
    - docs/build-plan/09g-approval-security.md
    - docs/build-plan/09f-policy-emulator.md
    - docs/build-plan/05g-mcp-scheduling.md
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:redirect-to-file-pattern"
  - "P1:fic-before-code"
  - "P1:backward-compatible-constructor"
  - "P0:never-modify-tests-to-pass"
conflicts:
  - "AGENTS.md L501 ('No prose around it' for coverage YAML) vs Template-First Rule (L436-448 requires full template structure). The EOF instruction reads as 'the reflection is just YAML' but the template shows YAML is section 7 of 7. Resolution: the EOF instruction describes the YAML block format, not the reflection file format. The template is authoritative for file structure."
note: "PH11 shipped with a runtime wiring failure because TDD tested components in isolation, pre-handoff review was not invoked, and the boundary inventory missed the env var process bridge."
```
