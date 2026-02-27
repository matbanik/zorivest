# Critical Review — MCP Category File Split (Docs Build Plan)

Date: 2026-02-26  
Scope: Review of the MCP category-file split work described in `.agent/context/handoffs/2026-02-26-mcp-category-file-split.md`, plus validation of Planned/Future MCP tool drafts in `docs/build-plan/05a`–`05i`.  
Method: local doc review + structural consistency checks + web validation against official MCP documentation/spec.

## Validation Summary

- Category files exist and are populated: `05a`–`05i` contain **63 tool headings** (`50 Specified + 11 Planned + 2 Future`).
- `mcp-tool-index.md` catalog also lists **63 tools** (counts match category files).
- Structural drift remains significant:
  - `docs/build-plan/05-mcp-server.md` still contains **36** `server.tool(...)` blocks.
  - `docs/build-plan/08-market-data.md` still contains **7** `server.tool(...)` blocks.
  - `docs/build-plan/09-scheduling.md` still contains **6** `server.tool(...)` blocks.
  - `docs/build-plan/10-service-daemon.md` still contains **3** `server.tool(...)` blocks.
- `mcp-tool-index.md` reference map is stale: parsed **63 tools**, and **0/63** include any `05a`–`05i` category-file references.

## Findings (Severity Ordered)

### 1. High — `05-mcp-server.md` claims “hub/shared infra only” but still embeds extensive tool specs and old registration pattern

- `docs/build-plan/05-mcp-server.md:15` says the hub “retains shared infrastructure only”.
- The same file still starts tool registrations immediately after the “Moved” note (`docs/build-plan/05-mcp-server.md:31`, `docs/build-plan/05-mcp-server.md:43`) and continues with many more tool blocks through the file (e.g. `docs/build-plan/05-mcp-server.md:1313`).
- Registration still imports/uses monolithic expansion registration (`docs/build-plan/05-mcp-server.md:1566`, `docs/build-plan/05-mcp-server.md:1569`) instead of category registrations.

Impact:
- Creates dual-authority specs (hub + category files), increasing drift risk.
- Contradicts the executed design intent in the split handoff.
- Misleads future edits back toward the monolithic file.

Recommendation:
- Either complete the hub-only extraction (preferred) or explicitly re-scope the design to “hub + implementation reference archive” and update all related docs/indexes accordingly.

### 2. High — `mcp-tool-index.md` is internally inconsistent and not safe as an agent-facing reference map after the split

- Header declares category files are the tool spec locations (`docs/build-plan/mcp-tool-index.md:5`).
- Reference map section begins at `docs/build-plan/mcp-tool-index.md:103`, but entries still point to old locations only (e.g. `calculate_position_size` at `docs/build-plan/mcp-tool-index.md:105`, `create_policy` at `docs/build-plan/mcp-tool-index.md:292`) and omit the new category files entirely.
- Consistency check found **0/63** tools with any `05a`–`05i` reference in the map.

Impact:
- Agents/readers using the reference map will be sent to stale/secondary locations.
- Undermines the stated goal of reliable tool selection/invocation.

Recommendation:
- Regenerate the reference map to include category files, and make the generator fail if a tool lacks its primary category-file mention.
- Add a validation rule: every tool must have exactly one primary category-file reference in the map.

### 3. High — `mcp-planned-readiness.md` is stale after the split and now points future specification work back to the wrong file(s)

- Multiple rows still say planned tools need `server.tool()` blocks in `05-mcp-server.md` (`docs/build-plan/mcp-planned-readiness.md:23`, `docs/build-plan/mcp-planned-readiness.md:38`, `docs/build-plan/mcp-planned-readiness.md:51`, `docs/build-plan/mcp-planned-readiness.md:66`).
- Tax row references a nonexistent/obsolete file name (`05a-mcp-tax-tools.md`) or inline hub placement (`docs/build-plan/mcp-planned-readiness.md:82`).

Impact:
- Future planning work will reintroduce monolith drift.
- Readiness guidance is no longer aligned with the split architecture.

Recommendation:
- Rewrite owner-file/gap columns to point to `05c`, `05d`, `05f`, `05h`, etc.
- Update readiness status now that draft `server.tool(...)` blocks already exist in the category files.

### 4. Medium — Cross-reference “authoritative spec” pattern was applied to `09` and `10`, but not `08`, leaving asymmetric duplication risk

- `09-scheduling.md` and `10-service-daemon.md` both clearly mark category files as authoritative while retaining code examples (`docs/build-plan/09-scheduling.md:2653`, `docs/build-plan/10-service-daemon.md:742`).
- `08-market-data.md` still has the full MCP tools section (`docs/build-plan/08-market-data.md:565`) and tool registrations (`docs/build-plan/08-market-data.md:577`) but no equivalent “Primary spec location” note.

Impact:
- Readers may continue treating Phase 8 as authoritative for market-data tool contracts while the split intends `05e` to be primary.

Recommendation:
- Add the same authoritative-spec callout used in `09`/`10` to `08`, or remove the inline tool block per original split plan.

### 5. Medium — `harvest_losses` draft has a concrete REST method contract mismatch (`POST` in code vs `GET` in dependency note)

- Draft code calls `POST /tax/harvest` (`docs/build-plan/05h-mcp-tax.md:240`, `docs/build-plan/05h-mcp-tax.md:241`).
- REST dependency line says `GET /api/v1/tax/harvest` (`docs/build-plan/05h-mcp-tax.md:261`).

Impact:
- Implementation will drift depending on which line a future contributor follows.
- Tool/index/API docs can become incompatible.

Recommendation:
- Pick one method and align all references (`05h`, `04-rest-api`, `gui-actions-index`, `input-index`).
- If filters stay body-based, `POST` is defensible; if query-only, convert schema/examples to query params and use `GET`.

### 6. Medium — Several tool specs encode error cases as plain text without `isError`, reducing agent reliability

Examples:
- `create_policy` validation failure returns text only (`docs/build-plan/05g-mcp-scheduling.md:62`).
- `run_pipeline` failure returns text only (`docs/build-plan/05g-mcp-scheduling.md:121`).
- `update_policy_schedule` “Policy not found” returns text only (`docs/build-plan/05g-mcp-scheduling.md:182`).
- `get_report_for_trade` missing report returns plain text message (`docs/build-plan/05c-mcp-trade-analytics.md:489`).

Contrast:
- `05b` service/diagnostics tools already use `isError: true` in some failure paths (`docs/build-plan/05b-mcp-zorivest-diagnostics.md:178`, `docs/build-plan/05b-mcp-zorivest-diagnostics.md:234`).

Impact:
- MCP clients/models lose a reliable machine signal for failure handling and retries.
- Mixed “JSON on success / free-form text on failure” outputs make downstream planning brittle.

Recommendation:
- Standardize failure signaling across category files:
  - set `isError: true` for real failures
  - return a stable JSON shape (or `structuredContent` when adopted)
  - reserve plain text for human-oriented summaries only

### 7. Medium — `quarterly_estimate` draft mixes read and write behavior behind an optional parameter, which is a poor MCP tool boundary

- Tool is named/described as compute/track (`docs/build-plan/05h-mcp-tax.md:180`, `docs/build-plan/05h-mcp-tax.md:186`).
- Optional `actual_payment` changes behavior from read-only compute to a write (`docs/build-plan/05h-mcp-tax.md:194`, `docs/build-plan/05h-mcp-tax.md:219`).

Impact:
- Side effects become conditional and harder for agents to reason about.
- Complicates idempotency, retries, and safety controls.

Recommendation:
- Split into two tools:
  - `get_quarterly_estimate` (read-only)
  - `record_quarterly_tax_payment` (write)
- If not split, require explicit `mode` and a confirmation field for write paths.

### 8. Medium — Destructive/operational tools lack explicit confirmation parameters despite being high-impact

Examples:
- `zorivest_service_restart` uses empty input schema (`docs/build-plan/05b-mcp-zorivest-diagnostics.md:197`–`docs/build-plan/05b-mcp-zorivest-diagnostics.md:201`) for a restart action (`docs/build-plan/05b-mcp-zorivest-diagnostics.md:251`).
- `disconnect_market_provider` deletes credentials with only `provider_name` (`docs/build-plan/05e-mcp-market-data.md:150`–`docs/build-plan/05e-mcp-market-data.md:155`) and is correctly marked destructive (`docs/build-plan/05e-mcp-market-data.md:162`), but has no extra confirmation/idempotency guard.

Impact:
- Higher risk of accidental execution by autonomous agents.

Recommendation:
- Add an explicit confirmation token/phrase (similar to `zorivest_emergency_unlock`) or a `confirm_destructive: true` flag.
- When implementation starts, add MCP tool annotations (`destructiveHint`, `idempotentHint`) for client-side safety UX.

### 9. Low — `start_account_review` is correctly flagged as a design risk, but the current draft still encodes an implementation shape that likely should not ship

- The file itself notes the stateless-workflow mismatch (`docs/build-plan/05f-mcp-accounts.md:165`) and re-raises the open question (`docs/build-plan/05f-mcp-accounts.md:234`).
- Draft code also uses `any` in TypeScript example mappings (`docs/build-plan/05f-mcp-accounts.md:191`, `docs/build-plan/05f-mcp-accounts.md:194`).

Assessment:
- The current “stateless checklist” return shape is much better than a hidden multi-turn workflow and can work if renamed (e.g. `get_account_review_checklist`).
- As currently named (`start_*`), it still implies stateful workflow/session semantics.

Recommendation:
- Rename toward a read-only checklist/assessment tool, then add separate explicit update tools.
- Remove `any` from draft snippets to stay aligned with the project’s TypeScript standards.

### 10. Low — New category snippets still use `any` in TypeScript examples (`05b`, `05f`)

- `docs/build-plan/05b-mcp-zorivest-diagnostics.md:67`
- `docs/build-plan/05f-mcp-accounts.md:191`
- `docs/build-plan/05f-mcp-accounts.md:194`

Impact:
- Violates the repo’s stated TypeScript quality bar for MCP-server docs/spec examples.

Recommendation:
- Replace with small local interfaces (e.g. `ProviderStatus`, `BrokerSummary`, `BankAccountSummary`) in examples.

## Planned/Future Tool Draft Soundness (Focused Assessment)

Overall verdict: **Mostly sound directionally**, with good progress on schema scaffolding and side-effect/error documentation. The highest-value corrections are boundary/behavioral, not wholesale redesign.

- `05c` planned (`create_report`, `get_report_for_trade`): sound and implementable; main gap is standardized error signaling and stable output shape for “not found”.
- `05d` planned (`create_trade_plan`): sound draft, but endpoint/REST/service dependencies still need synchronized specification in `04-rest-api.md` / `03-service-layer.md`.
- `05f` planned (`start_account_review`): concept is only sound if kept stateless and likely renamed (current file already points to this).
- `05h` tax planned batch: generally the strongest draft set; main corrections are:
  - `harvest_losses` method mismatch
  - `quarterly_estimate` mixed read/write semantics
  - endpoint consistency across API/index docs
- `05a` future logging tools: reasonable future additions, but should define valid feature namespace source (enum or discovered list) before moving to Specified.

## Web Validation (Official MCP Guidance) and Implications

The following points are supported by current official MCP docs/spec and should inform the final doc shape for these tools:

1. Tools are model-controlled and should expose clear, safe executable actions.
- Official docs describe tools as “model-controlled” and highlight annotations for read-only/destructive/idempotent hints.
- Implication for Zorivest: destructive tools like `zorivest_service_restart` and `disconnect_market_provider` should be extra explicit in schema and annotations.

2. Tool annotations exist specifically for safety and planning hints.
- MCP docs define `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
- Implication: your category-file split is a good place to standardize these hints per tool category before implementation starts.

3. Error signaling should be machine-readable.
- Official tool docs show `isError: true` usage for errors and structured content support.
- Implication: current text-only error strings in `05g`/`05c` should be normalized.

4. Long operations should report progress.
- MCP spec utility supports progress notifications; official tool best practices recommend progress reporting for long operations.
- Implication: plan progress behavior for `sync_broker`, file imports, and possibly `zorivest_service_restart` / `run_pipeline` polling paths.

5. Prompts/resources are better than hidden “guided workflows” for some interactions.
- Official docs distinguish prompts/resources as user/application-controlled primitives.
- Implication: `start_account_review` should avoid hidden stateful tool semantics; a stateless checklist tool + prompt can satisfy the UX more cleanly.

## Sources (Web)

Official MCP docs/spec pages reviewed:

- https://modelcontextprotocol.io/legacy/concepts/tools
- https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress
- https://modelcontextprotocol.io/learn/server-concepts/prompts
- https://modelcontextprotocol.io/learn/server-concepts/resources
- https://modelcontextprotocol.io/specification/2025-11-05/server/tasks (experimental; reviewed for long-running task patterns)

## Suggested Fix Order

1. Resolve structural authority drift:
   - `05-mcp-server.md` hub-only vs reference-archive decision
   - `mcp-tool-index.md` reference map regeneration
   - `mcp-planned-readiness.md` owner-file/readiness updates
2. Fix concrete contract mismatches:
   - `05h` `harvest_losses` POST/GET mismatch
   - `08` authoritative-spec callout parity with `09`/`10`
3. Standardize MCP behavior semantics across category files:
   - `isError` usage
   - stable JSON error payloads
   - confirmation/schema safety for destructive operations
4. Refine planned draft boundaries:
   - split/rename `start_account_review`
   - split `quarterly_estimate` read vs write behavior
5. Cleanup examples:
   - remove `any` in TypeScript snippets
   - add annotation placeholders/comments for future implementation

