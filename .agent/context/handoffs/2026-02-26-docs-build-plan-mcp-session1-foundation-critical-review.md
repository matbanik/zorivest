# Task Handoff Template

## Task

- **Date:** 2026-02-26
- **Task slug:** docs-build-plan-mcp-session1-foundation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of Session 1 MCP handoff artifacts against full `docs/build-plan/*.md` scope (41 markdown files), including cross-doc local links/anchors and MCP contract consistency

## Inputs

- User request: "do full review of all files in @docs\\build-plan folder"
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session1-plan.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session1-walkthrough.md`
  - `docs/build-plan/*.md`
- Constraints:
  - Review-only (no silent fixes)
  - Findings-first reporting
  - Full-folder structural audit (local markdown links + anchors)

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (optional, not used)
- Optional roles: researcher, guardrail

## Coder Output

- Changed files: `.agent/context/handoffs/2026-02-26-docs-build-plan-mcp-session1-foundation-critical-review.md` (this review handoff only)
- Design notes: No product/docs files modified; review-only pass
- Commands run:
  - Session discipline/context: `Get-Content -Raw SOUL.md`, `Get-Content -Raw .agent/context/current-focus.md`, `Get-Content -Raw .agent/context/known-issues.md`
  - MCP health: `pomera_diagnose`
  - Prior memory lookup: `pomera_notes search "Zorivest"`
  - Scope inventory: `rg --files docs/build-plan`, `Get-ChildItem docs/build-plan -File`
  - Evidence sweeps: `git status --short`, `git diff -- docs/build-plan/05j-mcp-discovery.md docs/build-plan/05-mcp-server.md docs/build-plan/mcp-tool-index.md`
  - Cross-doc checks: inline Python markdown link/anchor audit (local links only; fenced code ignored; URL-decoded relative paths)
  - Targeted consistency sweeps: `rg`, `Select-String`, `Get-Content` on MCP files + Session 1 handoffs
- Results:
  - Full-folder local markdown link/anchor audit passed after URL-decoding (`%20`) support
  - Multiple docs consistency/contract issues found in MCP Session 1 content
  - Walkthrough evidence quality gaps found (placeholder diff markers + weak verification command)

## Tester Output

- Commands run:
  - `rg --files docs/build-plan`
  - Inline Python audit script (markdown inline local links + anchor fragment resolution across `docs/build-plan/*.md`)
  - `rg -n "list_toolsets" docs/build-plan`
  - `Select-String -Path docs/build-plan/05-mcp-server.md -Pattern '^## Step 5\\.'`
  - `Select-String` / `rg -n` sweeps for `05a–05j` vs `05a–05i`, toolset rows, and discovery tool names
  - Targeted line-window reads from Session 1 plan/walkthrough handoffs
- Pass/fail matrix:
  - Local markdown target files exist (within `docs/build-plan` scope): **PASS**
  - Markdown anchor fragments resolve to headings (within `docs/build-plan` scope): **PASS**
  - Session 1 discovery tool names consistent across MCP docs: **FAIL** (`list_toolsets` typo in `05-mcp-server.md`)
  - `05-mcp-server.md` section numbering consistency: **FAIL** (duplicate `5.11` and `5.12`)
  - `mcp-tool-index.md` internal references consistent after `05j` addition: **FAIL** (stale `05a`–`05i` note)
  - Session 1 walkthrough verification evidence robustness: **FAIL** (placeholder diff markers and weak `rg -c` pattern)
- Repro failures:
  - `docs/build-plan/05-mcp-server.md:797` uses `list_toolsets` but canonical tool is `list_available_toolsets`
  - `docs/build-plan/05-mcp-server.md:555` + `docs/build-plan/05-mcp-server.md:727` duplicate `## Step 5.11`
  - `docs/build-plan/05-mcp-server.md:589` + `docs/build-plan/05-mcp-server.md:782` duplicate `## Step 5.12`
  - `docs/build-plan/mcp-tool-index.md:134` stale `05a`–`05i` reference after `05j` introduction
  - `docs/build-plan/05j-mcp-discovery.md:213` references `getAuthHeaders()` without local snippet import/definition
- Coverage/test gaps:
  - External `http(s)` link reachability was not checked (structure-only local audit)
  - Markdown reference-style links were not explicitly parsed (none detected in scanned scope)
  - No semantic execution of TypeScript snippets (docs/spec review only)
- Evidence bundle location:
  - Terminal outputs captured in session; key stats: `41` files scanned, `1082` inline links seen, `1074` local links checked, `0` missing files, `0` missing anchors
- FAIL_TO_PASS / PASS_TO_PASS result: N/A (review task)
- Mutation score: N/A
- Contract verification status: **Partial pass** — link/anchor integrity passes; MCP Session 1 doc consistency requires changes

## Reviewer Output

- Findings by severity:
  - **High:** Wrong discovery meta-tool name in adaptive client detection flowchart. `05-mcp-server.md` lists `list_toolsets` under dynamic-client meta-tools, but the canonical tool defined in `05j` and indexed in `mcp-tool-index` is `list_available_toolsets`. This is contract drift and will mislead implementers/agents following the flowchart. Evidence: `docs/build-plan/05-mcp-server.md:797`, `docs/build-plan/05j-mcp-discovery.md:10`, `docs/build-plan/mcp-tool-index.md:83`.
  - **High:** `05-mcp-server.md` has duplicate section numbers (`5.11` and `5.12` each appear twice), which makes numeric cross-references ambiguous and increases downstream drift risk. Evidence: `docs/build-plan/05-mcp-server.md:555`, `docs/build-plan/05-mcp-server.md:727`, `docs/build-plan/05-mcp-server.md:589`, `docs/build-plan/05-mcp-server.md:782`. Impact example: `05j` references "§5.11" textually (`docs/build-plan/05j-mcp-discovery.md:329`) and the section number is no longer unique.
  - **Medium:** Toolset source mapping for `trade-planning` is incomplete in the Toolset Definitions tables. The row claims `Category File(s) = 05d` with `Tools = 3`, but one of the three tools (`create_trade`) is dual-tagged into `trade-planning` and specified in `05c`. This makes the source column misleading and makes the count hard to audit from the listed file(s). Evidence: `docs/build-plan/05-mcp-server.md:735`, `docs/build-plan/05-mcp-server.md:740`, `docs/build-plan/mcp-tool-index.md:20`, `docs/build-plan/mcp-tool-index.md:120`.
  - **Medium:** `mcp-tool-index.md` still contains a stale internal note that says primary tool contracts are in `05a`–`05i`, contradicting the updated top-of-file `05a`–`05j` range and omitting the new discovery file. Evidence: `docs/build-plan/mcp-tool-index.md:5`, `docs/build-plan/mcp-tool-index.md:134`.
  - **Medium:** `05j-mcp-discovery.md` includes a non-self-contained code snippet for `get_confirmation_token`: it calls `getAuthHeaders()` but the snippet imports only `McpServer`, `z`, and `toolsetRegistry`. As written, the example cannot be copied into a file and compiled without hidden context. Evidence: `docs/build-plan/05j-mcp-discovery.md:17`, `docs/build-plan/05j-mcp-discovery.md:19`, `docs/build-plan/05j-mcp-discovery.md:213`.
  - **Low:** Canonical build-plan doc `05j-mcp-discovery.md` links to a `.agent/context/handoffs/...` research handoff as "Architecture rationale". This is repo-internal and less stable/portable than a docs-level reference, which weakens long-term documentation durability. Evidence: `docs/build-plan/05j-mcp-discovery.md:6`.
  - **Low (artifact quality):** The Session 1 walkthrough uses placeholder diff markers (`render_diffs(...)`) instead of reproducible diff evidence and includes a weak tool-name verification command (`...` placeholder and escaped alternation), so the verification section overstates auditability. Evidence: `.agent/context/handoffs/2026-02-26-mcp-session1-walkthrough.md:22`, `.agent/context/handoffs/2026-02-26-mcp-session1-walkthrough.md:36`, `.agent/context/handoffs/2026-02-26-mcp-session1-walkthrough.md:51`.
- Open questions:
  - For the `trade-planning` toolset tables, do you want `Category File(s)` to list all spec sources (`05c, 05d`) or remain "primary" only with a note explaining cross-tagged counts?
  - Should `.agent/context/handoffs/*` be considered acceptable references inside canonical `docs/build-plan/*`, or should those be moved to `docs/` summaries to avoid portability drift?
- Verdict:
  - **changes_required**
- Residual risk:
  - Low risk for local navigation (all local markdown links/anchors in `docs/build-plan` currently resolve).
  - Medium risk for implementation drift because the dynamic-loading flowchart and section numbering inconsistencies affect MCP architectural guidance and reviewer traceability.
- Anti-deferral scan result:
  - All identified issues are doc-only and fast to fix (rename one tool reference, renumber sections, clarify one table row/source mapping, update one stale note, add/import helper in snippet or annotate omitted import, and tighten walkthrough evidence).

## Guardrail Output (If Required)

- Safety checks: Not applicable (docs review only)
- Blocking risks: None runtime-related
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Review complete for all `docs/build-plan/*.md` files (41-file structural audit + targeted MCP Session 1 consistency checks); changes required
- Next steps:
  - Fix MCP doc contract drift in `05-mcp-server.md` (`list_toolsets` typo + duplicate step numbering)
  - Update Toolset Definitions source mapping for `trade-planning` in both `05-mcp-server.md` and `mcp-tool-index.md`
  - Remove stale `05a`–`05i` note and make `05j` snippet self-contained (or explicitly annotate omitted imports/helpers)
  - Tighten Session 1 walkthrough evidence (replace `render_diffs(...)`, use exact reproducible verification commands)
