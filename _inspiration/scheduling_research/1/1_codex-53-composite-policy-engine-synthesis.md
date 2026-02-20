# Composite Synthesis: Agentic JSON Policy Engine (ChatGPT + Claude + Gemini)

## Scope
Reviewed:
- `_inspiration/scheduling_research/chatgpt-prompt-1_Agentic JSON Policy Engine.md`
- `_inspiration/scheduling_research/claude-prompt-1_Agentic JSON Policy Engine.md`
- `_inspiration/scheduling_research/gemini-prompt-1_Agentic JSON Policy Engine.md`

Compared conclusions against:
- `_inspiration/scheduling_research/opus-46-policy-engine-research-synthesis.md`

Date: 2026-02-19

## Executive Summary
All three papers agree on the same high-level target: a local-first, single-process pipeline engine where policies are AI-authored JSON but execution is deterministic, validated, and guardrailed by the backend.

The main disagreement is not about goals. It is about language power and complexity:
- ChatGPT: schema-first, sequential, strongly typed JSON contract.
- Claude: implementation-first, pragmatic patterns ready to ship.
- Gemini: full state-machine DSL with richer control flow and domain-heavy examples.

Best composite direction: ship a constrained v1 (ChatGPT + Claude baseline), then add selective Gemini features (zombie recovery, sleep/wake handling, optional Choice/Map states) only when needed.

## 1. True Agreement (Present In All Three)
These points appear consistently across all three, with only minor syntax differences.

- Local-first and single-process assumptions are explicit.
- JSON Schema-backed policy validation is required (not optional).
- Step registry is the source of truth for executable capabilities.
- Pydantic (or equivalent typed models) drives step input schemas.
- Registry should be exposed to MCP so agents discover valid tool contracts.
- Sequential async execution is the default runtime model.
- Scheduler needs `coalesce`, `misfire` handling, and overlap control.
- SQLite/SQLCipher should use WAL + busy timeout for practical concurrency.
- SQL must be sandboxed with backend-enforced controls (allowlist posture preferred).
- Auditability is mandatory (authorship + run/step trail).
- Email is the highest-risk side effect and must be explicitly guarded.

## 2. Where They Differ (And Why It Matters)

### 2.1 Policy Topology
- ChatGPT: ordered `steps` array with explicit reference objects (for example, `{ "ref": "ctx.x" }`).
- Claude: ordered `steps` array with mustache expressions (`{{steps.a.output}}`) and lightweight conditions.
- Gemini: named `states` graph (ASL-style) with `start_at`, `Choice`, `Map`, `Pass`, `next` transitions.

Impact:
- Step-array model is easier for LLM authoring and static validation.
- State-machine model is more expressive but significantly harder to validate, migrate, and debug.

### 2.2 Data Reference Language
- ChatGPT: structured ref objects, strongest static validation.
- Claude: template interpolation, strongest readability.
- Gemini: JSONPath/ASL paths, strongest expressiveness.

Impact:
- This is a core product decision. It affects parser complexity, static safety checks, and LLM error rate.

### 2.3 Registry Construction Pattern
- ChatGPT: Protocol + explicit registration + versioned resolver.
- Claude: `__init_subclass__` auto-registration + Pydantic `Params` models.
- Gemini: decorator-based function registration + plugin scanning emphasis.

Impact:
- Claude pattern minimizes ceremony and is easiest to adopt in current Python stack.
- ChatGPT pattern has strongest explicit contracts for version/migration handling.

### 2.4 Branching Strategy
- ChatGPT: mostly sequential; branching de-emphasized.
- Claude: pragmatic `skip_if`/`conditions` for common cases.
- Gemini: first-class branching/iteration with `Choice` and `Map`.

Impact:
- `skip_if` covers many real workloads with much lower complexity.
- Full branching should be feature-gated until real use cases demand it.

### 2.5 Saga and Compensation Depth
- ChatGPT: minimal saga; compensation only where needed.
- Claude: strongest argument for "email as pivot transaction" and incremental compensation.
- Gemini: heavier saga stance with explicit `saga_log` and broad compensating-action framing.

Impact:
- In a single-process app, full saga infrastructure is usually unnecessary until multiple irreversible side effects appear before terminal steps.

## 3. Unique Contributions By Model

### 3.1 Unique Strengths From ChatGPT
- `inputs_schema` at policy level (good for external/manual triggers).
- Per-step `type_version` directly in policy JSON.
- Per-step `guardrails` block in policy payload.
- Explicit `concurrency.mode` policy setting (`skip|queue|reject_manual_when_running`).
- Strong two-stage validation split (creation-time vs execution-time).

### 3.2 Unique Strengths From Claude
- `__init_subclass__` registry pattern that is low-friction and production-friendly.
- Clear `on_error` enum (`fail_pipeline`, `log_and_continue`, `retry_then_fail`).
- Strong SQL sandbox implementation details with default-deny authorizer example.
- Practical SQLCipher setup nuance: `PRAGMA key` ordering before WAL-related pragmas.
- Concrete rate-limit budgets and immutable audit-table trigger pattern.
- Best articulation of human-approval gates for first run of changed policies.

### 3.3 Unique Strengths From Gemini
- Most complete state-machine DSL treatment (ASL-flavored).
- Investment-domain workflow examples (volatility guard, tax-loss harvesting).
- Startup zombie-run recovery logic is clearly spelled out.
- Sleep/resume handling via Electron power events + backend heartbeat check.
- CPU-bound offload guidance (process/thread pool) for UI responsiveness.

## 4. Composite Recommendation

### 4.1 V1 (Recommended now)
- Policy shape: ordered `steps` array.
- Reference language: structured ref objects (ChatGPT style).
- Error model: Claude `on_error` enum.
- Conditional execution: Claude `skip_if` only.
- Registry: Claude `__init_subclass__` auto-registration + ChatGPT-style type/version resolver.
- Safety baseline:
  - SQL authorizer + read-only query connection.
  - Recipient allowlists and limits.
  - Policy content hash verification.
  - Immutable audit trail.
  - First-run approval for changed policies with side effects.
- Runtime resilience:
  - APScheduler `coalesce` + overlap controls.
  - Persisted run/step status.
  - Resume from failed step with cached outputs.

### 4.2 V1.5 (Targeted hardening)
- Add Gemini zombie-run startup scan.
- Add Gemini sleep/resume drift correction path.
- Add optional idempotency key templates for side-effect steps.

### 4.3 V2 (Only if demanded)
- Introduce optional state-machine mode (`Choice`, `Map`) for advanced policies.
- Keep simple sequential mode as default authoring surface.

## 5. Comparison Against Opus 4.6 Synthesis

The Opus synthesis is strong overall and captures many useful tradeoffs. It is directionally correct in most areas.

### 5.1 Where Opus Matches This Review
- Correctly identifies data-reference syntax as the biggest decision axis.
- Correctly highlights Claude implementation pragmatism.
- Correctly preserves Gemini strengths around branching/state-machine expressiveness.
- Correctly surfaces ChatGPT strengths in schema discipline and versioning.
- Correctly recommends a pragmatic middle path (`skip_if` before full state graph).

### 5.2 Where Opus Overstates "Universal Agreement"
The largest quality issue in Opus is that several "all three agree" rows are too strong.

- "Steps as flat array" is not universally true:
  - Gemini primarily models workflows as named `states` with `start_at` and transitions.
- "Enabled flag" is not clearly universal:
  - Explicit `enabled` appears in ChatGPT/Claude schedule examples, not as a Gemini core pattern.
- "Optional `compensate()` method" is not universal:
  - Gemini emphasizes compensating actions/saga flow, not executor `compensate()` method shape.
- "Full saga is overkill" is not universal:
  - Claude/ChatGPT argue this directly; Gemini presents a stronger saga-orchestration posture.
- "All three use the same execution persistence shape" is overstated:
  - Claude and ChatGPT are close on run/step tracking, Gemini stresses state-machine persistence and adds explicit `saga_log`.

### 5.3 Net Assessment Of Opus
- Good strategic synthesis and good recommended picks.
- Needs wording tightened from "universal" to "majority" on several rows.
- With those corrections, it remains a useful decision document.

## 6. Practical Decision Frame For Next Step
If the next action is implementation planning, the most risk-reducing decision order is:

1. Lock reference syntax (`ref` object vs mustache vs JSONPath).
2. Lock workflow topology for v1 (sequential only vs optional state graph).
3. Lock error/compensation contract (`on_error`, pivot-side-effect policy).
4. Lock SQL sandbox and approval gate requirements as non-negotiable controls.
