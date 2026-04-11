---
project: "2026-04-10-acon-compression-phase1"
date: "2026-04-10"
source: "_inspiration/acon_research/acon-compression-synthesis.md §Phase 1"
meus: ["INFRA-ACON-P1"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: ACON Context Compression — Phase 1

> **Project**: `2026-04-10-acon-compression-phase1`
> **Build Plan Section(s)**: N/A (infrastructure/docs-only — no product code changes)
> **Status**: `draft`

---

## Goal

Implement the five "free-win" Phase 1 actions from the [ACON Compression Synthesis](file:///p:/zorivest/_inspiration/acon_research/acon-compression-synthesis.md) to reduce context rot, improve LLM KV cache hit rates, and lower the average review pass count for MEU handoffs.

Phase 1 targets **prevention through template discipline** — zero infrastructure, zero risk, immediate ROI. This extends the template standardization work completed in handoff 103 (INFRA-TEMPLATES v2.0).

**Expected outcomes:**
- 15–25% token reduction per handoff from structural compression
- 90–95% reduction in test output sections via summarization rules
- 50–70% reduction in code state sections via delta-only diffs
- Improved KV cache hit rates from stable prefix design
- Reviewer verbosity control to prevent boilerplate re-reading

---

## User Review Required

> [!IMPORTANT]
> **Template version bump**: This upgrades `TEMPLATE.md` from v2.0 to v2.1. All future handoffs must use the v2.1 format. Existing handoffs (001–104) are NOT retrofitted — they remain valid under v2.0. The v2.1 changes are backward-compatible (additive fields, reordered sections).

> [!IMPORTANT]
> **New AGENTS.md rules**: Two new mandatory rules will be added to the Execution Contract:
> 1. **Test Output Compression** — agents must output only failing tests in handoffs
> 2. **Delta-Only Code Sections** — handoffs must use unified diff blocks (` ```diff `) instead of full file contents
>
> These are process rules, not code changes. They affect how agents produce artifacts, not how the software works.

---

## Proposed Changes

### ACON Phase 1: Template & Workflow Compression

This is a single cohesive MEU (`INFRA-ACON-P1`) covering all five synthesis actions. All actions modify overlapping files and share the same "context compression" goal.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | Handoff TEMPLATE.md v2.1 has a `<!-- CACHE BOUNDARY -->` marker separating the stable prefix (YAML + Scope + AC table) from variable content (Evidence, Changed Files, Codex Validation, History) | Research-backed (ACON synthesis §1.5 — prefix stability for KV cache) | Template must NOT have dynamic content above the cache boundary |
| AC-2 | Handoff TEMPLATE.md v2.1 has a `verbosity` field in YAML frontmatter defaulting to `"standard"` with documented tier definitions (`summary`, `standard`, `detailed`) | Research-backed (ACON synthesis §Phase 1 — verbosity tiers) | N/A (additive field) |
| AC-3 | "Changed Files" section in TEMPLATE.md instructs use of unified diff blocks (` ```diff `) for delta-only code presentation instead of full file content | Research-backed (ACON synthesis §Phase 1 — delta-only code sections) | Template must NOT contain instructions to inline full source code |
| AC-4 | Evidence section in TEMPLATE.md enforces test output summarization: "N passed, M failed" summary + only failing test details | Research-backed (ACON synthesis §Phase 1 — test output summarization) | Template must NOT instruct inclusion of passing test details |
| AC-5 | History section remains at the very end of the template, after all other sections including Codex Validation | Research-backed (ACON synthesis §1.5 — pin timestamps to end) | No timestamp-bearing section may appear above the cache boundary except YAML `date` |
| AC-6 | AGENTS.md `§Execution Contract` contains a "Context Compression Rules" subsection with the test output and delta-only rules | Research-backed (ACON synthesis §Phase 1) | Rules must NOT contradict existing evidence freshness requirements |
| AC-7 | `meu-handoff.md` workflow references the compression rules and v2.1 template version | Research-backed (ACON synthesis §Phase 1) | Workflow must NOT reference the old v2.0 template without v2.1 upgrade note |
| AC-8 | `tdd-implementation.md` workflow adds test output compression guidance in Red/Green phase steps | Research-backed (ACON synthesis §Phase 1) | Workflow must NOT instruct agents to capture full passing test output |
| AC-9 | REVIEW-TEMPLATE.md adds a `requested_verbosity` field for reviewer to specify tier and bumps `template_version` to `"2.1"` | Research-backed (ACON synthesis §Phase 1 — verbosity tiers) | N/A (additive field, version parity with handoff template) |
| AC-10 | A context compression reference document exists at `.agent/docs/context-compression.md` with full tier definitions and examples | Research-backed (ACON synthesis §Phase 1) | N/A (new file) |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| YAML frontmatter structure | Local Canon (handoff 103) | Already established in TEMPLATE.md v2.0 |
| Cache boundary placement | Research-backed (ACON synthesis §1.5) | Stable prefix = YAML + Scope + AC table; variable = everything below |
| Verbosity tier definitions | Research-backed (ACON synthesis §Phase 1) | Three tiers: `summary` (~500 tokens), `standard` (~2000 tokens), `detailed` (~5000+ tokens) |
| Test output format | Research-backed (ACON synthesis §Phase 1) | "Only output failing test names, assertion messages, and relevant stack frames. Never output passing test details." Direct quote from synthesis. |
| Delta-only enforcement | Research-backed (ACON synthesis §Phase 1) | Use fenced diff blocks (` ```diff ... ``` `) — standard markdown, proven in prior handoffs (ref: 2026-02-26 corrections). For handoffs, include Changed Files table with summary + inline diff excerpts. |
| Timestamp pinning strategy | Research-backed (ACON synthesis §1.5) | YAML `date` at top is OK (deterministic per handoff). History table with event timestamps stays at end. No other timestamp-bearing content above cache boundary. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `.agent/context/handoffs/TEMPLATE.md` | modify | v2.0→v2.1: add cache boundary marker, verbosity field, delta-only guidance, test output compression rules, reorder sections for prefix stability |
| `.agent/context/handoffs/REVIEW-TEMPLATE.md` | modify | Add `requested_verbosity` field, bump `template_version` to `"2.1"` |
| `.agent/workflows/meu-handoff.md` | modify | Update template version reference, add compression rules reference |
| `.agent/workflows/tdd-implementation.md` | modify | Add test output compression guidance in Red/Green phases |
| `.agent/workflows/critical-review-feedback.md` | modify | Add verbosity tier consumption guidance for review output |
| `.agent/context/handoffs/README.md` | modify | Document v2.1 fields and verbosity tiers for both handoff and review templates |
| `.agent/docs/context-compression.md` | new | Canonical reference for all compression rules, verbosity tier definitions, and examples |
| `AGENTS.md` | modify | Add "Context Compression Rules" subsection to Execution Contract |

---

## Out of Scope

- **Phase 2 instrumentation** — Token count logging, artifact size tracking, pass-count correlation. Deferred per synthesis gate rule.
- **Phase 3 middleware** — Test output compressor tooling, tree-sitter diff, Headroom SDK. Conditional on Phase 2 measurement.
- **Retrofitting existing handoffs** — Handoffs 001–104 remain in v2.0 format. No mass migration.
- **Product code changes** — This project modifies only docs, templates, and workflow files.
- **`AGENTS.md` restructuring** — Only additive changes (new subsection). No reorganization of existing sections.

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. It is an infrastructure/docs-only project (like handoff 103 INFRA-TEMPLATES).

```powershell
rg "acon-compression" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Template Structure — Positive Checks
```powershell
rg "CACHE BOUNDARY" .agent/context/handoffs/TEMPLATE.md
rg "verbosity:" .agent/context/handoffs/TEMPLATE.md
rg "template_version.*2.1" .agent/context/handoffs/TEMPLATE.md
```

### 2. Template Structure — Negative Constraint Checks
```powershell
# V-neg-1: No dynamic content above cache boundary (AC-1 negative test)
$c = Get-Content .agent/context/handoffs/TEMPLATE.md -Raw; $b = $c.IndexOf('CACHE BOUNDARY'); $p = $c.Substring(0,$b); if ($p -match 'Commands Executed|Exit Code|Quality Gate|FAIL_TO_PASS') { Write-Error 'FAIL: dynamic content above cache boundary' } else { 'PASS: no dynamic content above cache boundary' }

# V-neg-2: No full-source-code instructions in template (AC-3 negative test)
rg -ic "full file|full source|entire file|inline.*source" .agent/context/handoffs/TEMPLATE.md
# Expected: 0 matches

# V-neg-3: No passing-test instructions in Evidence section (AC-4 negative test)
rg -ic "include.*passing|output.*passing.*test|all test.*detail" .agent/context/handoffs/TEMPLATE.md
# Expected: 0 matches

# V-neg-4: History section is last (AC-5 negative test)
$lines = Get-Content .agent/context/handoffs/TEMPLATE.md; $histIdx = ($lines | Select-String '^## History').LineNumber; $lastH2 = ($lines | Select-String '^## ') | Select-Object -Last 1; if ($histIdx -eq $lastH2.LineNumber) { 'PASS: History is last section' } else { Write-Error 'FAIL: History is not last section' }
```

### 3. Compression Rules in AGENTS.md
```powershell
rg "Context Compression" AGENTS.md
```

### 4. Workflow References Updated
```powershell
rg "2\.1" .agent/workflows/meu-handoff.md
rg -i "test output|compression|summariz" .agent/workflows/tdd-implementation.md
rg -i "verbosity" .agent/workflows/critical-review-feedback.md
```

### 5. New Reference Document
```powershell
Test-Path .agent/docs/context-compression.md
rg "summary" .agent/docs/context-compression.md
```

### 6. Review Template Updated
```powershell
rg "requested_verbosity" .agent/context/handoffs/REVIEW-TEMPLATE.md
rg "template_version.*2.1" .agent/context/handoffs/REVIEW-TEMPLATE.md
```

### 7. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" .agent/context/handoffs/TEMPLATE.md .agent/docs/context-compression.md
```

### 8. No render_diffs References (Finding 1 regression check)
```powershell
rg "render_diffs" .agent/context/handoffs/TEMPLATE.md .agent/docs/context-compression.md AGENTS.md
# Expected: 0 matches
```

---

## Open Questions

_No open questions. All behaviors are fully specified by the ACON synthesis document and existing template v2.0 patterns._

---

## Research References

- [ACON Compression Synthesis](file:///p:/zorivest/_inspiration/acon_research/acon-compression-synthesis.md) — Phase 1 actions (lines 135–148)
- [Handoff 103: Template Standardization](file:///p:/zorivest/.agent/context/handoffs/103-2026-04-06-template-standardization-infra.md) — Predecessor project
- [TEMPLATE.md v2.0](file:///p:/zorivest/.agent/context/handoffs/TEMPLATE.md) — Current baseline being upgraded
