# Composite Synthesis: Pipeline Step Chain Design (Prompt 2)

## Scope
Reviewed:
- `_inspiration/scheduling_research/2/chatgpt-prompt-2_Pipeline Step Chain Design.md`
- `_inspiration/scheduling_research/2/claude-prompt-2_Pipeline Step Chain Design.md`
- `_inspiration/scheduling_research/2/gemini-prompt-2_Pipeline Step Chain Design.md`

Compared against:
- `_inspiration/scheduling_research/2/2_opus-46-pipeline-steps-research-synthesis.md`

Date: 2026-02-19

## Executive Summary
All three papers converge on a local-first, single-process architecture with a policy-driven async pipeline and strong DB/runtime safeguards.  
The largest divergence is implementation strictness and scope depth:
- ChatGPT: strongest governance and standards framing (policy compilation, cache contracts, SQL sandbox boundaries).
- Claude: strongest implementation blueprint (specific libraries, concrete stage contracts, runnable architecture patterns).
- Gemini: strongest architectural framing for autonomy and schema evolution under unknown sources (generic HTTP adapter, mapping loop, temporal history).

The practical composite direction is: implement Claude’s concrete baseline, harden it with ChatGPT’s security/standards controls, and selectively add Gemini’s generic-source and temporal-history ideas where risk/complexity is acceptable.

## 1. True 3/3 Agreement
These are explicitly present in all three sources.

- Local-first, single-process desktop model (Electron + Python/FastAPI + SQLite/SQLCipher).
- Policy-driven orchestration with scheduled execution and missed-run handling concerns (`coalesce`/misfire semantics).
- Runtime criteria resolution (watchlist/positions/date-relative selectors, not hardcoded symbol lists).
- Provider abstraction via interface/protocol concepts (behavior contracts instead of ad hoc fetch code).
- Async fetch with rate-control + bounded concurrency + retries for transient API failures.
- Hybrid transform/storage pattern: strict typed tables for core entities plus flexible JSON storage for novel fields.
- Rejection of pure EAV as the primary model for this use case.
- SQLite/SQLCipher write-performance discipline (batching/transactions, WAL awareness).

## 2. Majority Agreement (2/3, Not Universal)

- Structured report versioning and snapshot-first reproducibility:
  - Strong in ChatGPT + Claude.
  - Gemini focuses more on temporal table history than report-snapshot schema.
- Detailed render stack recommendations:
  - Strong in Claude.
  - ChatGPT proposes Electron `printToPDF`.
  - Gemini provides little render-stage implementation detail.
- Send-stage operational contract (async SMTP, delivery ledger, idempotent send):
  - Strong in Claude.
  - ChatGPT discusses side-effect discipline and retry semantics.
  - Gemini under-specifies the send stage.
- Plugin/extensibility mechanics:
  - ChatGPT prefers entry-point discovery.
  - Claude favors decorator registry simplicity.
  - Gemini emphasizes generic HTTP policy adaptation over plugin mechanics.

## 3. Core Divergences

## 3.1 Novel Source Strategy
- ChatGPT: extensible provider ecosystem with explicit capability metadata and plugin discovery.
- Claude: decorator registry + built-ins + optional auto-provider selection.
- Gemini: generic HTTP adapter as first-class path for unknown APIs, with policy-authored mappings.

Implication:
- Gemini’s approach maximizes flexibility with zero code changes, but requires tighter policy guardrails.

## 3.2 Schema Evolution Control
- ChatGPT + Claude: controlled promotion path (raw JSON -> generated/indexed fields -> typed tables).
- Gemini: runtime `dlt`-driven schema evolution (auto type inference and `ALTER TABLE`).

Implication:
- Controlled promotion is safer operationally for desktop reliability.
- Runtime schema mutation is more autonomous but can increase migration unpredictability.

## 3.3 Render Architecture
- ChatGPT: Electron-native `webContents.printToPDF`.
- Claude: WeasyPrint + Plotly/Kaleido dual-target rendering.
- Gemini: no equivalent concrete stack.

Implication:
- `printToPDF` reduces moving parts if Electron owns rendering.
- WeasyPrint decouples PDF generation from Electron runtime lifecycle.

## 3.4 Job Store Placement
- ChatGPT + Gemini: scheduler persistence inside encrypted DB context.
- Claude: separate plain SQLite job store to avoid SQLCipher/PRAGMA complexity.

Implication:
- Separate store simplifies ops but leaves schedule metadata unencrypted.

## 3.5 SQL Safety Depth
- ChatGPT: strongest explicit double-lock posture (`query_only` + authorizer + no `load_extension`).
- Claude: strong practical controls and validation budgets.
- Gemini: emphasizes bounded declarative execution model, less detailed SQL-sandbox mechanics.

## 4. Unique High-Value Contributions

## 4.1 ChatGPT
- Criteria-to-run-graph compilation framing before side effects.
- Standards-grade HTTP caching/revalidation posture (ETag/If-Modified-Since).
- Clear warning on `load_extension` risk with untrusted SQL.
- JsonLogic/JMESPath split for report gating vs JSON reshaping.
- Strong fetch provenance envelope design (cache state, schema hash/version hints, warnings).

## 4.2 Claude
- Most implementation-ready full stack (library matrix + stage contracts + code patterns).
- Strong generated-column strategy (`GENERATED ALWAYS AS ... VIRTUAL`) with indexing workflow.
- Practical fail-fast vs quarantine model and stage criticality (`required` vs `optional`).
- Complete report DSL including `ai_narrative`, renderer registry, and delivery tracking model.
- Best MCP surface proposal (minimal tool set + resources + stdio production transport).

## 4.3 Gemini
- Strong declarative-security framing (AI authors config, deterministic engine executes bounded paths).
- Generic HTTP adapter + mapping-schema loop for unknown source adaptation.
- Strong financial precision emphasis (`Decimal`, integer micros/cents storage strategy).
- Temporal/history-table orientation for time-travel and audit reconstruction.
- Useful SQLCipher operational tuning awareness (pooling, memory-security tradeoffs).

## 5. Comparison to Opus-46 Synthesis

## 5.1 Where Opus Is Strong
- Good decision matrix and clear recommended picks.
- Correctly identifies major divergence axes:
  - provider registry style,
  - schema evolution strategy,
  - render stack choice,
  - scheduler store tradeoff.
- Good practical open questions for build planning.

## 5.2 Where Opus Overstates “Universal Agreement”
The main issue is that several “all three converge” items are better classified as 2/3 consensus or uneven coverage:

- `Jinja2` as universal render choice.
  - Gemini does not substantively define render internals to support this as 3/3.
- `aiosmtplib` + delivery-table + idempotent-send as universal send contract.
  - Gemini does not provide comparable send-stage specificity.
- Provider-declared capability metadata as universal.
  - Explicit capability-contract depth is strongest in ChatGPT/Claude, not equally detailed in Gemini.
- Data-snapshot SHA-256 integrity hashing as universal.
  - Not clearly evidenced in Gemini at the same specificity as ChatGPT/Claude.
- “All three reject Prefect for weight/complexity.”
  - Explicit anti-Prefect argument is strongest in Claude; not equally explicit in Gemini.

## 5.3 Net Assessment of Opus
- Strategically useful and directionally correct.
- Should relabel several “universal” rows to “majority (2/3)” to avoid false certainty.

## 6. Composite Recommendation

Recommended baseline for implementation planning:

1. Use Claude’s concrete runtime model for v1.
2. Add ChatGPT’s SQL/report safety controls as mandatory guardrails.
3. Add Gemini’s generic HTTP + mapping loop behind strict allowlists and quotas.
4. Treat runtime `dlt` schema mutation as optional/experimental, not default.
5. Decide early on scheduler job-store encryption posture (simplicity vs confidentiality).

Decision checkpoints before build:

1. Novel-source policy freedom boundary (what generic HTTP is allowed to do).
2. Schema evolution mode (controlled promotion vs autonomous mutation).
3. Render ownership (Electron-native PDF vs Python-native PDF).
4. Send pipeline strictness (must-send vs optional stage behavior by policy type).
