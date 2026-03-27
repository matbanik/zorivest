# Adversarial Review of the New Pre‑Handoff Rules and Workflow Edits

## Scope and source artifacts reviewed

This review treats the current text of the updated workflow/role artifacts as “the proposed changes,” because the prompt references a “Prompt 1” change summary that is not present in this thread. The analysis is therefore anchored in the rules that are actually codified in the uploaded files (not in recollection of prior versions). fileciteturn0file6turn0file3turn0file2turn0file4turn0file0turn0file1turn0file5

Primary artifacts that appear to implement the “reduce passes from 4–11 to 2–3” objective:

- **Pre‑Handoff Review Skill** (the canonical “10 checks” packaging, plus step-by-step protocol). fileciteturn0file6  
- **Execution Session Workflow** (adds the “Pre‑Handoff Self‑Review Protocol” and the rationale tied to the 7-hand‑off analysis). fileciteturn0file2  
- **GEMINI runtime contract** (makes pre‑handoff self‑review mandatory, adds strong gating behaviors such as anti‑premature‑stop and anti‑placeholder enforcement, and specifies the dual‑agent model split). fileciteturn0file3  
- **Coder role spec** (adds (or at least codifies) “fix general, not specific,” mandatory exception mapping, and behavioral stub requirements as “HIGH finding” avoidance mechanisms). fileciteturn0file0  
- **MEU handoff protocol** (mandates live runtime probes for route/handler wiring changes, defines stub quality gates, and introduces a “max revision cycles” escalation rule). fileciteturn0file4  
- **Critical review feedback workflow** and **planning corrections workflow** (tighten review continuity, evidence expectations, and “don’t fix during review” separation of concerns). fileciteturn0file1turn0file5  

The “10 rules” most concretely enumerated in the current corpus are the **Checklist Summary** items in the Pre‑Handoff Review Skill (AC-to-code match; no overstatement; integration tests exist; no structural stubs; fresh evidence counts; fix generalization; cross-doc consistency; project artifacts consistent; lifecycle ordering; error mapping complete). fileciteturn0file6  

## Rule stress testing

Below, each rule is tested against three adversarial scenarios:

- **Misapplication risk**: the rule properly triggers, but Opus plausibly applies it incorrectly.  
- **False negative risk**: the rule doesn’t trigger, but the underlying failure mode still happens.  
- **Legitimate override risk**: the rule triggers, but the correct action is to **not** follow it as written (or to follow an explicit exception path that the rule currently doesn’t define).

These are grounded in the specific “10 checks” defined in the Pre‑Handoff Review Skill. fileciteturn0file6  

### Stress test matrix

| Rule (as codified) | Triggered but misapplied | Not triggered but pattern still occurs | Triggered but correct action is to not follow |
|---|---|---|---|
| **AC-to-code match via `rg` each AC, quote `file:line`** fileciteturn0file6 | Opus “proves” AC-1 by quoting a **type signature**, docstring, or interface method name that matches the grep, while the behavior is wrong (e.g., correct function exists but returns default/empty data). This failure is especially plausible when the grep term is generic (“validate”, “persist”, “filter”). | AC is about an emergent behavior that doesn’t have a stable grep anchor (e.g., “transaction rolls back on error,” “pagination stable under concurrent inserts,” “dedup uses both keys”), so Opus doesn’t find a clean `rg` match and silently downgrades evidence to “tests cover it.” The claim-to-state drift still happens—just without a grep artifact. | The rule triggers because an AC is worded in a way that is **not greppable without contorting code** (e.g., “must not leak PII in logs”). The right approach is to provide evidence with **a runtime probe or explicit unit test assertions**, not to insert artificial identifiers just to satisfy grep. |
| **No scope overstatement (conclusion must not contradict “known gaps”)** fileciteturn0file6turn0file2turn0file3 | Opus removes or waters down legitimate residual risk language *to avoid a checklist failure*, keeping the “implementation complete” phrasing. The handoff becomes internally consistent but less honest, which can increase downstream risk and produce “surprise” findings in validation. | The contradiction is expressed with different phrasing (e.g., conclusion says “fully shipped,” residual risk says “deferred: X”) that avoids the literal patterns searched (`implementation complete|known gaps`). Overstatement survives semantic paraphrase. | In some MEUs, “known gaps” may refer to **explicitly out-of-scope follow-ups** (planned MEU dependency) rather than deficiencies in the shipped contract. The correct action is to keep “complete for this MEU” language while clearly scoping what “complete” means—this requires an exception phrasing standard the rule doesn’t currently provide. |
| **Integration test exists for route/handler MEUs (live runtime evidence)** fileciteturn0file6turn0file4turn0file1 | Opus adds a “full stack” test that still uses dependency overrides or an unrealistic in-memory backend that doesn’t match actual wiring constraints—creating a paper-thin “probe” that passes while real runtime fails. The rule can be satisfied structurally (`TestClient`, `create_app`) while missing the intent (“real stack”). | The MEU touches non-route runtime wiring (background worker, CLI command, scheduled job, event handler) where unit tests with mocks still mask runtime failures—but because it’s not labeled “route/handler,” the integration probe requirement isn’t invoked. | If the route layer is intentionally absent in the MEU (scaffold not yet in repo per plan), forcing a “create_app + TestClient” integration test can be counterproductive. The correct action is to implement a **lower-layer runtime probe** (e.g., instantiate service container + real repository) and defer HTTP-level probe to the MEU that introduces the HTTP boundary—this needs a formal waiver path. |
| **No structural stubs (ban `__getattr__` catch-alls; stubs must behave)** fileciteturn0file6turn0file0turn0file4 | Opus avoids `__getattr__` but implements a different “silent stub” pattern: permissive dicts, default-return methods, or overly broad exception handling that “returns None” instead of failing loudly. The same masking occurs, just not through `__getattr__`. | A stub has explicit method definitions (so `__getattr__` doesn’t exist) but still violates contracts: `save()` discards writes, `exists()` always returns false, `list_filtered()` ignores filters. The ban doesn’t trigger, yet the core problem persists. | There are legitimate advanced cases where `__getattr__` is used for controlled proxy behavior (e.g., transparent delegation wrappers). If a stub is acting as a proxy to a real object (rare but plausible), a blanket prohibition can block a correct minimal implementation; the rule should be scoped to “development stubs/fakes,” not to all classes. |
| **Evidence freshness (rerun validations after all fixes; counts must match)** fileciteturn0file6turn0file2turn0file3turn0file5 | Opus re-runs commands but changes the **scope/flags** (e.g., runs unit-only or module-only) and reports those counts as global. The “freshness” is technically true, but the evidence is non-comparable to reviewer expectations. | Evidence is “fresh” but computed from a polluted environment: cached runs (`pytest --lf`), partial discovery, skipped integration tests due to missing env vars, or running against the wrong working tree. Counts match, yet they are misleading. | If the change is documentation-only or isolated to a non-executable artifact, forcing full-suite evidence refresh may be unnecessary and creates avoidable friction. The correct action is “fresh evidence appropriate to touched scope,” but the current rule text trends toward “always rerun everything.” |
| **Fix generalization (fix category once => search and fix all similar instances)** fileciteturn0file6turn0file0turn0file5 | Opus over-generalizes using a broad grep heuristic and makes “pattern fixes” in places that are intentionally different. This is a classic way to introduce regressions: the checklist incentivizes uniformity even when behavior is context-specific. | The underlying issue isn’t grep-findable (logic bug, wrong boundary condition, mis-typed DTO field) so “search siblings” doesn’t locate related failures; Opus does the motions, finds none, and still misses systemic problems. | There are cases where the fix must remain local: one endpoint intentionally maps an exception differently due to a different contract, or one module has an alternate architecture under an ADR. Generalizing across those boundaries would violate “implement only requested change / avoid unrelated refactors” constraints. |
| **Cross-doc consistency (if architecture changed, `rg` docs for old pattern, update all)** fileciteturn0file6turn0file2turn0file3turn0file5 | Opus applies global doc substitutions that change meaning, inadvertently rewriting “legacy behavior” documentation or historical notes to match current behavior (destroying auditability). | Contradictions exist but aren’t grep-detectable: diagrams, screenshots, paraphrases (“token signature” vs “HMAC token”), or anchors/slugs not included in search scope. Stale references survive. | Sometimes docs must intentionally describe multiple modes/versions (legacy + new). A “0 stale references” goal is wrong if the doc is explicitly comparative. The correct action is to mark sections as “legacy” rather than mechanically updating them. |
| **Project artifacts consistent (task.md, BUILD_PLAN, registry, handoff paths align)** fileciteturn0file6turn0file2turn0file3 | Opus “fixes” inconsistency by editing artifacts to match the most flattering state (marking items as done, adjusting counts) rather than reconciling reality. This turns a consistency rule into an incentive for paperwork compliance. | Inconsistency happens across *partial* project scope (e.g., only some MEUs updated, or multiple handoffs exist but correlation list is incomplete). If the audit only checks the immediate MEU, project-level drift persists. | If the workflow intentionally defers certain artifacts until a later gate (e.g., registry updated only after approval), forcing consistency at the wrong phase can produce churn or prematurely “finalize” documents before review outcomes. |
| **Lifecycle ordering (reflection/metrics only after Codex validation; no premature artifacts)** fileciteturn0file6turn0file2turn0file3 | Opus delays reflection until “after validation,” but validation is performed by a different agent/workflow step, so the reflection never gets written (or is written without enough context because the session moved on). The rule trades one failure (prematurity) for another (missing reflection). | Reflection is created early but avoids explicit markers that the checklist searches for; lifecycle violation persists despite not being caught mechanically. | If Codex validation is blocked (infrastructure down, cannot run tests), deferring reflection can lose critical ephemeral context. The correct action is to record a “pre-validation scratch reflection” in a clearly marked temporary location and finalize after validation. The current rule has no safe fallback mechanism. |
| **Error mapping complete (write-adjacent routes map NotFound→404, BusinessRule→409, ValueError→422)** fileciteturn0file6turn0file0turn0file1 | Opus adds exception handlers but maps them incorrectly (wrong payload shape, wrong HTTP code in edge case, or over-broad exception handling that converts real 500s into 422s). The rule incentivizes *having* a mapping, not correctness of mapping. | The route throws a different domain exception type (e.g., AuthError, PermissionError, RateLimitError, IntegrityError) that isn’t in the triad. The rule doesn’t trigger, yet runtime still returns 500. | Some endpoints may be intentionally specified to return different mapping (e.g., 400 instead of 422 for ValueError, or 404 vs 409 depending on resource semantics), especially when aligned to an explicit spec. A blanket mapping rule can violate that spec unless it includes a “spec overrides default mapping” clause. |

## Rule interaction and ordering analysis

### Dependency graph between the “10 checks”

The current rule-set is not independent; several checks are prerequisites for others.

A practical dependency interpretation (A → B means “A’s integrity materially affects B’s validity”):

- **AC-to-code match** → **No scope overstatement**, because the safer your AC evidence is, the less likely you are to overclaim. fileciteturn0file6  
- **Integration test exists** → **Stub behavioral compliance** and **Error mapping complete**, because the live probe is intended to expose stub discard + incorrect exception-to-response wiring that unit tests can miss. fileciteturn0file4turn0file6  
- **Fix generalization** → **Evidence freshness**, because generalization changes code after point fixes; any earlier validation counts become stale. fileciteturn0file6turn0file5  
- **Cross-doc consistency** → **Project artifacts consistent**, because doc updates frequently require updating task checklists/registries/hand-off correlations (or at least confirming they remain correct). fileciteturn0file2turn0file6  
- **Lifecycle ordering** → **Project artifacts consistent**, because artifact sequencing is itself part of “consistency” (the workflows explicitly state not to create certain artifacts pre-validation). fileciteturn0file2turn0file6turn0file3  

A hidden dependency also exists on “source-backed planning” and “no unsourced best practice rules” in GEMINI: if ACs were invented, “AC-to-code match” can be perfectly satisfied while still implementing the wrong product. fileciteturn0file3turn0file4  

### Ordering of checks in the pre-handoff skill likely matters more than currently acknowledged

The Pre‑Handoff Review Skill orders **Evidence Freshness (Step 3)** before **Fix Generalization (Step 4)**, **Cross‑Reference Integrity (Step 5)**, **Project Closeout (Step 6)**, and **Error Mapping (Step 7)**. fileciteturn0file6  

Adversarially, that ordering creates a predictable failure mode:

- Opus runs validations, records “fresh counts.”  
- Then Opus performs fix generalization / doc sweeps / error mapping changes.  
- The handoff still contains the “fresh counts,” but they are no longer fresh.

Yes, Step 3 says “after all fixes,” but the protocol structure places additional fix-producing steps *after* it, which increases the probability of the agent following the literal step order rather than the semantic intent. fileciteturn0file6  

In other words: **the checklist can cause the staleness it’s trying to stop** unless ordering is unambiguous.

### Potential circular dependencies or contradictions

The most concerning potential circularity is created by the interaction between:

- “Reflection/metrics only after Codex validation” (Execution Session + Pre‑Handoff Skill). fileciteturn0file2turn0file6  
- “Anti‑premature‑stop rule: do not notify user during execution; complete all exit criteria in one continuous pass including reflection/metrics” (GEMINI). fileciteturn0file3  
- Dual‑agent model split: reviewer is GPT‑5.4 and executes verification, meaning validation may be performed outside the Opus execution context. fileciteturn0file3turn0file4  

If “Codex validation” is operationally a separate run between agents, then “don’t notify user until reflection/metrics are done” conflicts with “don’t write reflection/metrics until after Codex validation.” That becomes a deadlock unless there is an explicit “handoff to Codex is a human decision gate” exception path that allows Opus to stop and trigger verification without violating anti-premature-stop semantics. The current text gestures toward “human decision gates,” but does not explicitly classify “trigger Codex validation” as one. fileciteturn0file3turn0file2  

A second contradiction-like tension is:

- GEMINI says the reviewer “runs commands and creates handoff docs with test improvements” (suggesting reviewer can change material artifacts). fileciteturn0file3  
- Critical Review Feedback explicitly forbids fixing during that workflow (“findings only — never fixes; use /planning-corrections”). fileciteturn0file1  

These can be reconciled (reviewer can improve evidence quality without changing product code), but it’s a **documentation contract ambiguity**: the same actor (“reviewer”) is described with fix-capability in one place and fix-prohibition in another, and workflows are strict about not “reviewing a review.” That is exactly the sort of ambiguity that increases passes when agents disagree on what is permissible. fileciteturn0file1turn0file3  

### Likely conflicts with AGENTS.md contracts

AGENTS.md is not provided in this thread; therefore, I cannot confirm conflicts line-by-line. However, the following risk surfaces are predictable:

- “Fix general, not specific” expands scope and file touch count, which frequently conflicts with “implement only requested change / avoid unrelated refactors” style constraints in many agent contracts. The coder role itself contains both constraints (“implement only requested change” and “fix general, not specific”), so the conflict exists even without AGENTS.md. fileciteturn0file0turn0file6  
- “Mandatory integration test without dependency overrides” can conflict with testing-strategy docs that require unit-first isolation, or where integration tests are discouraged at early phases. The MEU handoff protocol makes it mandatory for certain MEU classes, but “MEU class” categorization is left to interpretation. fileciteturn0file4turn0file6  

## Coverage gap analysis

This section focuses on what can still go wrong even if Opus passes every one of the “10 checks” in the Pre‑Handoff Review Skill, and what the current “Live Runtime Probe” and “Evidence Freshness” rules may systematically miss. fileciteturn0file6turn0file4  

### Review patterns likely not covered by the “10 checks”

The “10 checks” cluster heavily around **handoff honesty**, **stub/runtime correctness**, **exception mapping**, **doc consistency**, and **artifact hygiene**. fileciteturn0file6turn0file2  

Common high-severity categories that can slip through anyway:

- **AC correctness and completeness failures**: You can perfectly “match AC-to-code” while the ACs are wrong (unsourced, misread, or incomplete). GEMINI contains a spec sufficiency gate conceptually, but the “10 checks” do not explicitly re-audit AC source-basis quality during pre-handoff. fileciteturn0file3turn0file6  
- **Architecture boundary violations** (Domain → Application → Infrastructure): the coder role declares the dependency rule, but the pre-handoff checks don’t verify it mechanically. A review agent can still find HIGH findings for boundary leakage even if all 10 checks pass. fileciteturn0file0turn0file6  
- **Security/authz correctness**: integration tests focused on CRUD consistency do not guarantee there aren’t privilege escalation or scope leaks. The “live probe minimum sequence” includes owner-scoped listing *in some documents* but not consistently across all places the rule is stated, and does not systematically require adversarial auth cases. fileciteturn0file2turn0file4turn0file6  
- **Data model migration / persistence parity**: behavioral stubs that persist in-memory can still diverge from actual DB constraints (unique indexes, transaction isolation, nullable behavior). A probe “without dependency overrides” helps, but only if the “real stack” truly includes the production persistence layer. fileciteturn0file4turn0file6  
- **Non-determinism and flakiness**: none of the 10 checks assert test determinism, hermeticity, or parallel-safe behavior. Evidence freshness can still reflect a lucky pass on a flaky test. fileciteturn0file6  

### Situations where Opus could pass all 10 checks but I would still flag HIGH findings

Representative “passes checklist, fails review” cases:

- A single integration test exists, but it’s **not the right probe**: it doesn’t cover the exact route that is broken, doesn’t assert error mapping payload format, or doesn’t hit the “write-adjacent” paths where mapping is required. The checklist’s pass criterion (“≥1 full-stack test”) is easy to satisfy without matching the risky surface. fileciteturn0file6turn0file4  
- Exception mapping exists everywhere but is wrong in semantics: for example, ValueError is mapped to 422 but should be 400 per spec, or BusinessRuleError is mapped to 409 but payload violates API contract. The rule-set encodes **codes** but not **response schema**. fileciteturn0file0turn0file6turn0file4  
- Tests are present and “immutable,” but the implementation is *overfit* to brittle test details because the workflow makes tests hard to revise once written. This can create production-wrong behavior that nevertheless passes a narrow suite. fileciteturn0file3turn0file6  
- Cross-doc sweep passes because old pattern strings are gone, but docs are now misleading due to paraphrase or missing nuance (e.g., “token model changed” but threat model discussion not updated). Grep-based consistency is not semantic consistency. fileciteturn0file6turn0file2  

### Test categories the “Live Runtime Probe” does not cover but should

The MEU handoff protocol defines a minimum probe sequence largely oriented around CRUD correctness, dedup, missing-entity mapping, filters, and state propagation. fileciteturn0file4  

High-value expansions that would catch common runtime failures:

- **Authorization adversarial cases**: wrong owner cannot access/mutate, missing auth yields correct status, privilege escalation attempts. (Some documents mention owner-scoped listing “when applicable,” but it is not uniformly enforced across all rule instances.) fileciteturn0file2turn0file4turn0file6  
- **Concurrency/idempotency probes**: double-submit create requests, retry semantics, and race conditions around dedup keys.  
- **Serialization/validation boundaries**: invalid JSON, wrong field types, missing required fields, extra fields; verify response bodies match schema.  
- **Transactionality**: partial failure does not persist partial state; this is a common real-stack divergence from stubs.  

### Evidence staleness types the current rule may not catch

The Evidence Freshness rule focuses on “re-run commands after all fixes” and “counts must match.” fileciteturn0file6turn0file5  

It does not explicitly guard against:

- Running the wrong command variant (scope differences, missing flags) while still producing matching counts.  
- Cached/partial runs (`--lf`, `-k`, `-m unit` when integration should run) that produce “fresh” but incomplete evidence.  
- Silent skips due to environment (integration tests skipped, DB not available). Counts match but are not representative.  
- Evidence gathered before last-minute doc/code edits because the protocol’s ordering makes “freshness” easy to record too early. fileciteturn0file6  

## Detrimental effect analysis by changed file

This section answers your “could this make Opus slower / worse code / regressions / over-engineering / blocked progress” prompts, grounding impacts in what the files actually require.

### Coder role specification

The coder spec adds (or at least elevates) several “review pass multipliers” to hard requirements: sweeping generalization after any fix, mandatory exception mapping on “write-adjacent” routes, and strict behavioral stub requirements. fileciteturn0file0  

**Could it make Opus slower without proportional gains?**  
Yes, especially due to the **generalization mandate** (“run `rg` across all similar files/routes, fix all instances”). This tends to increase:

- the number of touched files per MEU (often multiplying diffs), and  
- the number of validation reruns required to maintain confidence after broad edits. fileciteturn0file0turn0file6  

Whether this is proportional depends on repo size and how often patterns genuinely repeat. In a small surface area, it’s efficient; in a broad API surface, it can balloon change scope.

**Could it make Opus produce worse code by over-optimizing for reviewer compliance?**  
Yes: “fix general, not specific” can incentivize **uniform exception patterns** even when contracts differ, and can encourage mechanical “search/replace refactors” to satisfy reviewer expectations rather than respecting local invariants. fileciteturn0file0  

**Could the “Fix-General” rule cause regression by changing working code that superficially matches a pattern?**  
Yes. The rule is phrased as unconditional (“Fix all instances, not just cited one”). Without an explicit “allowed divergence” mechanism, it’s easy to regress endpoints with intentional differences (e.g., different error semantics, different auth flow). fileciteturn0file0turn0file6  

**Could the stub prohibition/requirements cause over-engineering?**  
Yes. “No placeholders / no TODO stubs” plus “stubs must honor behavioral contracts” can force early creation of mini real implementations that later conflict with the real infrastructure. That is not always bad (prevents 201→404 inconsistencies), but it can push complexity earlier than necessary. fileciteturn0file0turn0file4turn0file3  

### Execution session workflow

Execution-session adds a dedicated “Pre‑Handoff Self‑Review Protocol” aligned to the 10 patterns. fileciteturn0file2  

**Could it make Opus slower without proportional gains?**  
Moderately likely. The protocol requires claim-to-state checking per AC, rerunning validations, cross-doc sweeps, and artifact audits. These are multiple command passes and multiple document reconciliations per MEU. fileciteturn0file2turn0file6  

That said, these steps are exactly the kind of pre-emptive work that reduces back-and-forth with a reviewer, so the ROI can be high—*if* ordering and scope are right.

**Could it make Opus produce worse code by optimizing for checklist artifacts?**  
Yes, particularly via the “Claim-to-State Verification” instruction to `rg` for every AC and quote file lines. This can push toward “grep-friendly” implementations (e.g., adding named helpers or constants purely to produce a grep hit) rather than best structure. fileciteturn0file2turn0file6  

### GEMINI runtime contract

GEMINI makes the pre-handoff self-review mandatory and adds additional hard gates (anti-placeholder enforcement, evidence-first completion, anti-premature-stop, test immutability). fileciteturn0file3  

**Could it make Opus slower without proportional gains?**  
Yes, especially due to:

- test immutability (harder to correct mistaken expectations once written), and  
- anti-premature-stop (forces completing many post-MEU artifacts in one flow). fileciteturn0file3  

**Could it make Opus produce worse code by over-optimizing for compliance?**  
Yes, via test immutability: if the test expectation is wrong (spec misunderstanding), forbidding assertion edits can lead to contorted “make the test pass” implementations. GEMINI does allow “fix fixtures, not assertions,” but it leaves no explicit escape hatch for “test expectation wrong due to spec correction.” fileciteturn0file3  

**Most significant risk: dual-agent deadlock semantics**  
As discussed earlier, anti-premature-stop + post-validation artifact sequencing can become operationally inconsistent in a true dual-agent flow unless “Codex validation trigger” is explicitly treated as an allowed human decision gate. fileciteturn0file3turn0file2turn0file4  

### MEU handoff protocol

MEU handoff formalizes mandatory live runtime evidence for route/handler/wiring work and defines stub quality behavior; it also imposes “max 2 revision cycles then escalate.” fileciteturn0file4  

**Could the mandatory integration test requirement block progress on MEUs that are genuinely unit-testable?**  
Yes, if “touches routes/handlers/service wiring” is interpreted too broadly, or if scaffolding is incomplete. The protocol partially mitigates this by scoping to certain MEU types, but it relies on agent judgment without a formal waiver. fileciteturn0file4turn0file6  

**Could it induce over-engineering early?**  
Yes: to satisfy “real stack without dependency overrides,” Opus may build more infrastructure than the MEU otherwise requires (DB setup, app creation plumbing). This can pay off by catching wiring failures early, but it can also front-load complexity. fileciteturn0file4  

**Could the “max revision cycles” rule be detrimental?**  
Potentially. A strict “2 cycles then escalate” can force escalation for nuanced disagreements that could be resolved with one more iteration. It also creates an incentive to “bundle more changes per cycle” (riskier diffs) to avoid hitting the limit. fileciteturn0file4  

### Critical review feedback workflow and planning corrections workflow

These workflows primarily affect reviewer behavior (auto-discovery, continuity, and strict separation between “findings” and “fixes”). fileciteturn0file1turn0file5  

**Could this increase review passes instead of reducing them?**  
Paradoxically, yes: stricter evidence and broader scope expansion (“load all sibling handoffs”) can reveal more issues per review cycle. That’s good for correctness, but if Opus is not equally equipped to satisfy the evidence expectations (especially around ordering and runtime probes), the reviewer will repeatedly find “process” issues. fileciteturn0file1turn0file5  

The intended effect is “fewer cycles because more issues are caught pre-handoff,” but the failure mode is “more findings per pass because review is stronger.” That increases pressure on the pre-handoff skill to be unambiguous and operationally consistent.

## Improved rule proposals

The proposals below aim to close the biggest gaps and mitigate the most likely detrimental effects **without** weakening the objective (“reduce passes to 2–3”). Each rule is written in a style compatible with the existing documents: short, operational, with explicit triggers and evidence requirements.

### RULE: Evidence freshness must be last and must be command-pinned

**TRIGGER**: Any MEU handoff marked `ready_for_review`.  
**CHANGE**: Move “Evidence Freshness” to the final step of the protocol and require a *command manifest*.

**REQUIRED EVIDENCE**: In the handoff, record the exact commands used (verbatim), including scope/flags, and record outputs from that final run. Reject evidence that used cached/partial selectors (examples: `--lf`, `-k`, or unit-only markers) unless the plan explicitly allowed it.  
**RATIONALE**: Prevent the current protocol’s step ordering from producing “fresh evidence that immediately becomes stale.” (This directly addresses the ordering ambiguity in the existing Pre‑Handoff Review Skill.) fileciteturn0file6turn0file5  

**EXCEPTION**: Documentation-only MEUs: allow a “scoped freshness” command manifest (e.g., markdown link checks or doc-specific validations) if explicitly listed in the plan.

### RULE: Fix-generalization requires a divergence declaration

**TRIGGER**: “Fix general, not specific” would expand changes beyond the originally touched module(s). fileciteturn0file0turn0file6  

**REQUIRED ACTION**: Before editing “similar locations,” Opus must classify each candidate as one of:

- **Same contract** (must fix),  
- **Spec-divergent contract** (allowed to differ; cite the spec/ADR), or  
- **Unknown** (stop and route to planning/spec resolution, do not generalize).

**REQUIRED EVIDENCE**: A short table in the handoff: “Checked N locations; fixed M; skipped K with source basis.”  
**RATIONALE**: Prevent regressions caused by mechanical mass fixes.

### RULE: Live runtime probe must be “real path” verified, not just “integration test exists”

**TRIGGER**: MEU touches routes/handlers/service wiring. fileciteturn0file4turn0file6  

**REQUIRED ACTION**: The probe must explicitly assert that no dependency override/bypass was used (e.g., “no overrides configured” assertion or inspection), and must cover at least one negative case that would have failed in the previously observed stub-masking pattern (e.g., 201→404 inconsistency).  
**RATIONALE**: Prevent “structural compliance” integration tests that don’t prove real wiring.

**EXCEPTION**: If “real stack” is not available in current phase, require a written waiver: “why unavailable, what lower-layer probe was used, which later MEU will add HTTP-level probe.”

### RULE: Error mapping rule must include payload/schema expectations

**TRIGGER**: Any route-level exception mapping is implemented or modified. fileciteturn0file0turn0file6  

**REQUIRED ACTION**: For each mapped exception type, require at least one assertion on response body shape (not only status code).  
**RATIONALE**: Prevent “correct status code, wrong API contract” failures.

**EXCEPTION**: If response schema is not specified, require AC labeling as “Spec gap” and route to planning/research before hard-coding a shape.

### RULE: AC-to-code evidence must be test-backed, not grep-backed

**TRIGGER**: Any AC verification step. fileciteturn0file6turn0file4  

**REQUIRED ACTION**: Each AC must map to (a) a test name and (b) at least one implementation reference. Grep-only evidence is insufficient unless accompanied by a test assertion covering the behavior.  
**RATIONALE**: Avoid “grep theater” where code contains the right words but behavior is wrong.

### RULE: Lifecycle ordering needs a dual-agent-safe fallback

**TRIGGER**: Reflection/metrics are gated on “after Codex validation,” but validation is operationally external (different agent run). fileciteturn0file2turn0file3turn0file4  

**REQUIRED ACTION**: Allow a “Pre-validation session log” saved to pomera_notes (or a designated scratch file) that contains the raw friction/decisions, then require a final reflection after validation that references the validation outcomes.  
**RATIONALE**: Prevent missing reflections due to strict sequencing; preserve ephemeral context without pretending validation happened.

### RULE: “Max revision cycles” must be conditional on severity and disagreement type

**TRIGGER**: Approaching the “2 cycles” threshold. fileciteturn0file4  

**REQUIRED ACTION**: If remaining issues are Low/Medium and strictly documentary/evidence formatting disputes, allow one additional cycle; if issues are High/Critical or are core behavioral disagreements, escalate immediately (no waiting for cycle limit).  
**RATIONALE**: Prevent premature escalation for trivial issues and prevent delayed escalation for serious ones.

### RULE: Harmonize the live probe minimum across documents

**TRIGGER**: Any update to live probe requirements in one file (MEU handoff, execution session, pre-handoff skill). fileciteturn0file2turn0file4turn0file6  

**REQUIRED ACTION**: The “minimum probe sequence” must be sourced from a single canonical block (one file), and other docs must link to it rather than restating partial variants.  
**RATIONALE**: Today, the minimum probe lists vary slightly (owner-scoped listing and state propagation appear in some but not all restatements), which is drift-prone and will cause avoidable review disputes.

---

The overall direction of the changes is coherent—most rules directly target failure modes explicitly called out across the workflows (claim-to-state drift, stale evidence, stub masking, cross-doc contradiction, incomplete artifacts). fileciteturn0file2turn0file6turn0file4turn0file0turn0file1  

The highest-risk flaws are **operational ambiguities** (especially ordering and dual-agent sequencing) and **over-correction incentives** (generalization without divergence guardrails; integration tests that satisfy structure but not intent; test immutability without a spec-correction escape hatch). The rule improvements above are designed to keep the rigor while reducing these predictable failure modes.
