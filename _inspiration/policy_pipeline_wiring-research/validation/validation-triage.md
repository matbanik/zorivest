# Validation Triage — Effort-Ranked Adoption Plan

> **Effort metric:** Agentic token consumption + human decision involvement  
> **Not estimated:** Wall-clock hours. Instead: "Can an agent do this in one session with zero/one human confirmation?"

> [!NOTE]
> **STATUS: ALL SPEC UPDATES APPLIED.** All 16 triage items from Buckets A–D have been integrated into `retail-trader-policy-use-cases.md` as spec-level changes. The 3-session execution sequence below describes the *implementation* work remaining. See the updated Gap Summary Matrix and Implementation Priority tables in the spec doc for the canonical deliverable list.

---

## Bucket A: DO NOW — Paste-Ready, Zero Human Decisions

These items have ready-to-paste code from Claude's PoCs, need no design decisions, and will need to exist regardless. Skipping means guaranteed rework later.

| # | Item | What | Net New Code | Why Now |
|---|------|------|-------------|---------|
| S3 | HardenedSandbox | `ImmutableSandboxedEnvironment` with filter allowlist, output/timeout caps, `_DENY_ATTRS` | ~50 lines (Claude's `secure_jinja.py`) | SSTI → RCE is a one-shot compromise. Paste-ready. |
| S6 | Secret + safe_deepcopy | `Secret` carrier class (raises on `__str__`/`__deepcopy__`) + depth/byte-guarded deepcopy | ~35 lines (Claude's `safe_copy.py`) | Prevents credentials in StepContext. Independent of everything else. |
| S7 | Markdown sanitization | `nh3` + `markdown-it-py(html=False)` render chain | ~30 lines (Claude's `safe_markdown.py`) | Ships naturally with S3. Email templates render Markdown → HTML. |
| S11 | Secrets scanning | `re.search(r'(sk-\|AKIA\|ghp_\|Bearer\s)', policy_json)` | ~5 lines in PolicyDocument validator | Catches accidentally embedded credentials. Trivial. |
| S12 | Policy content IDs | `policy_id = sha256(canonical_json)` | ~1 line + test | Audit trail, TOCTOU prevention. Free. |
| S13 | mode=ro URI | `create_engine('sqlite:///file:db.sqlite?mode=ro', uri=True)` | 1 line change | C-level read-only. Co-delivers with S1. |
| S17 | Step-count cap | `if len(self.steps) > 20: raise` | 1 line Pydantic validator | Prevents DoS via mega-policies. |
| S20 | Template size cap | 64 KiB source reject | Already inside S3's `HardenedSandbox` | Zero marginal cost — ships free. |
| S15 | Frozen dataclass note | Doc paragraph about future refactor to `frozen=True` | Zero code | Captures Gemini's insight for later. |
| S16 | MVP-3 milestone | Doc update to implementation priority | Zero code | Sharpens execution plan. |

**Agent effort:** Single session. ~120 lines of net new production code + test derivations from Claude PoCs.  
**Human involvement:** None. All decisions are deterministic.

---

## Bucket B: DO NOW — Slight Integration Work, Light Human Input

These need one design confirmation each but are still single-session deliverables.

| # | Item | What | Integration Point | Human Decision |
|---|------|------|--------------------|----------------|
| S1 | set_authorizer | `sqlite3.Connection.set_authorizer` callback denying READ on sensitive tables, ATTACH, PRAGMA, load_extension | Sandbox connection factory in `zorivest_infra` | ✅ Table deny-list is obvious — confirm: `{encrypted_keys, auth_users, sqlite_master, sqlite_schema, sqlite_temp_master}` |
| S10 | SQL AST allowlist | Replace sqlglot blocklist with `find_all` walk; reject `exp.Command`, any non-`{Select,With,Union,Subquery,CTE,Paren}` | `validate_sql` tool/function | ✅ Allowlist types from Claude's poc_f11 — confirm list |
| S14 | FetchStep MIME check | `if response_content_type != expected_mime: reject` | FetchStep execution path | ❓ Define expected MIME per provider (most are `application/json`) |
| S18 | FetchStep fan-out cap | Max URLs per step, global pool limit | FetchStep params validation | ❓ Default 5 URLs/step? Configurable? |
| S8 | Error schema | Pydantic model: `EmulatorError(phase, step_id, error_type, field, message)` | New model in domain layer | ❓ Confirm field names |
| R3* | Provider capability table | Doc-only table listing each provider's data types (quotes/news/fundamentals) and auth requirements | `retail-trader-policy-use-cases.md` | ✅ Derivable from existing `provider_registry.py` |

**Agent effort:** Single session after human confirms 3 lightweight items.  
**Human involvement:** 3 quick confirmations (MIME mapping, fan-out limit, error schema fields). No design debates.

---

## Bucket C: BAKE INTO PARENT — Cannot Be Standalone

These must ship WITH their parent gap. Adding them to the spec now costs zero tokens; building them standalone is impossible.

| # | Item | Parent Gap | Why Co-Deliverable |
|---|------|-----------|-------------------|
| S4 | Emulator output containment (4 KiB cap, SHA-256 hash, sanitized errors) | Gap H (Emulator) | Without it, the emulator is a net-negative security feature (F33) |
| S5 | Cumulative session byte-budget | Gap H (Emulator) | Per-call caps alone are defeated by chunked iteration (F35) |
| S9 | `get_db_row_samples` MCP tool | Gap C (QueryStep) | Tool is useless until QueryStep exists |

**Action now:** Add these as hard requirements in the parent gap's spec. Zero code, zero tokens beyond doc edits.

---

## Bucket D: SPEC NOW, BUILD WHEN UI EXISTS

| # | Item | Blocker | Interim Mitigation |
|---|------|---------|-------------------|
| S2 | SendStep confirmation gate | Electron UI not scaffolded | Add `requires_confirmation: bool = True` field to SendStep schema. If `True` and no interactive UI available, raise `PolicyExecutionError("SendStep requires user confirmation")`. This ensures the contract exists from day one — when the UI ships, it wires into this field. |

**Agent effort:** ~10 lines of code for the interim flag + schema field.  
**Human involvement:** None for interim. UX design needed when Electron ships.

---

## Bucket E: GENUINELY DEFER

| # | Item | Why Defer | Low-Cost Prep Now |
|---|------|----------|-------------------|
| S19 | Timing side-channel padding (constant-time buckets) | Exotic threat for single-user desktop. Timing oracles are slow, noisy, rate-limitable. No realistic attacker model. | None needed |
| R5* | Full taint tracking (TRUSTED/UNTRUSTED_PROVIDER enforcement) | High complexity, marginal gain when set_authorizer + output caps + SendStep gate already break the lethal trifecta | **Add `source_type: Literal["db", "provider", "computed"]` field to step output metadata.** One field, zero enforcement, creates the foundation if taint tracking is ever needed. (~3 lines) |

---

## Bucket F: CONFIRMED REJECTIONS

| # | Item | Why Reject |
|---|------|-----------|
| R1 | Replace pipeline with LangGraph | Working `PolicyEngine` exists. Pipeline is a declarative DAG, not agentic reasoning. Full rewrite for zero security gain. |
| R2 | Eliminate template DB; use FileSystemLoader | Agent-first requires MCP CRUD boundary, not arbitrary file I/O. |
| R4 | Collapse emulator to 2 phases | Each phase has distinct security properties: PARSE (schema), VALIDATE (semantics), SIMULATE (SQL sandbox), RENDER (output containment). |

---

## Execution Sequence

```
Session 1 (agent-solo):
  └─ Bucket A: All 10 items
     ├─ Create secure_jinja.py (S3 + S20)
     ├─ Create safe_copy.py (S6)
     ├─ Create safe_markdown.py (S7)
     ├─ Add secrets scan to PolicyDocument (S11)
     ├─ Add policy hash ID (S12)
     ├─ Add step-count cap (S17)
     ├─ Update sandbox connection with mode=ro (S13)
     └─ Doc updates (S15, S16)

Session 2 (human confirms 3 items, then agent-solo):
  Human confirms:
  ├─ Provider MIME mapping (S14)
  ├─ Fan-out limit default (S18)
  └─ Error schema field names (S8)
  Agent implements:
  └─ Bucket B: All 6 items
     ├─ set_authorizer callback (S1)
     ├─ SQL AST allowlist (S10)
     ├─ FetchStep MIME + fan-out (S14, S18)
     ├─ EmulatorError Pydantic model (S8)
     └─ Provider capability table in doc (R3*)

Session 3 (agent-solo):
  └─ Bucket C + D: Spec updates
     ├─ Add S4/S5 as hard requirements in Gap H spec
     ├─ Add S9 as requirement in Gap C spec
     ├─ Add SendStep confirmation flag (S2 interim)
     └─ Add source_type field to output metadata (R5* prep)
```

> [!TIP]
> **Net result:** 16 items land across 2 implementation sessions + 1 spec session. 3 human confirmations total, all lightweight. The remaining items (S19, full taint tracking) can be genuinely ignored — they're exotic threats that our primary controls already mitigate.
