# Task Handoff

## Task

- **Date:** 2026-03-15
- **Task slug:** build-plan-workspace-setup-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the new `05k-mcp-setup-workspace.md` spec and the related build-plan/doc registry updates

## Inputs

- User request:
  - Review the updated build-plan files using `.agent/workflows/critical-review-feedback.md`
- Specs/docs referenced:
  - `docs/build-plan/05k-mcp-setup-workspace.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `.agent/context/meu-registry.md`
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/mcp-tool-index.md`
  - `docs/build-plan/mcp-planned-readiness.md`
  - `.agent/context/known-issues.md`
- Constraints:
  - Review-only. No product/doc fixes in this workflow.
  - Findings must be grounded in file state, not change claims.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - No product changes; review-only
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None
- Results:
  - No edits made

## Tester Output

- Commands run:
  - `git status --short`
  - `git diff -- docs/build-plan/05k-mcp-setup-workspace.md docs/build-plan/build-priority-matrix.md docs/build-plan/05-mcp-server.md .agent/context/meu-registry.md`
  - `rg -n "73 tools|74 tools|68 tools|69 tools|10 category files|11 category files|12 tools|11 tools|15 tools minimum|15 tools|37 tools|5\\.H\\b|5\\.H1|5\\.H2|setup_workspace|setup workspace|05k-mcp-setup-workspace|workspace setup" docs/build-plan .agent/context docs/BUILD_PLAN.md`
  - `rg -n "\| \`core\`|Default active|05k|setup_workspace|workspace setup" docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md`
  - Line-numbered file reads for the cited ranges in:
    - `docs/build-plan/05k-mcp-setup-workspace.md`
    - `docs/build-plan/05-mcp-server.md`
    - `docs/build-plan/build-priority-matrix.md`
    - `.agent/context/meu-registry.md`
    - `docs/BUILD_PLAN.md`
    - `docs/build-plan/mcp-tool-index.md`
    - `docs/build-plan/mcp-planned-readiness.md`
- Pass/fail matrix:
  - Claim verification for edited files: PASS
  - Internal consistency in `05k-mcp-setup-workspace.md`: FAIL
  - Cross-file MCP count consistency: FAIL
  - Cross-file MEU/matrix consistency: FAIL
- Repro failures:
  - `validatePath()` in `05k` resolves `path.dirname(fullPath)` before directory creation, so a fresh `.agent/context/...` or `.agent/docs/...` write would fail on the first nested path.
  - Default-tool math is stale after adding the 12th `core` tool.
- Coverage/test gaps:
  - No executable implementation exists yet, so this review only covers spec/document correctness.
  - Template content under `mcp-server/templates/agent/` is described but not yet implemented in the repo.
- Evidence bundle location:
  - Inline in this handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; docs-only review
- Mutation score:
  - Not applicable
- Contract verification status:
  - Failed; the new spec introduces contract drift and stale downstream canon

## Reviewer Output

- Findings by severity:
  - **High:** `validatePath()` as specified breaks clean `standard`/`full` scaffolds. The function falls back to `fs.realpath(path.dirname(fullPath))` for new files at `docs/build-plan/05k-mcp-setup-workspace.md:74-85`, but the first nested writes are `.agent/context/...` and `.agent/docs/...` at `docs/build-plan/05k-mcp-setup-workspace.md:228-241`. On a fresh workspace those parent directories do not exist yet, so `realpath()` would throw before `safeWrite()` reaches its later `mkdir()`. As written, the advertised nested scaffold flow cannot succeed from a clean project root.
  - **High:** The authoritative MCP tool-count math is now self-contradictory after adding `05k`. `docs/build-plan/05-mcp-server.md:738` correctly raises `core` to 12 tools, but the same section still says the default active set is 37 at `docs/build-plan/05-mcp-server.md:748-753` and that `core` + `discovery` is 15 tools minimum at `docs/build-plan/05-mcp-server.md:770`. Those numbers should be 38 and 16 respectively. The stale duplicate remains in `docs/build-plan/mcp-tool-index.md:117-127`, so the canonical MCP inventory now disagrees with itself.
  - **High:** The `05k` safety/content contract is not represented by the implementation sketch. The doc promises preserved user rules and generated provenance headers at `docs/build-plan/05k-mcp-setup-workspace.md:20-22` and `docs/build-plan/05k-mcp-setup-workspace.md:363-366`, and says the tool "never throws" at `docs/build-plan/05k-mcp-setup-workspace.md:324`. But the implementation only reads raw templates (`docs/build-plan/05k-mcp-setup-workspace.md:154-155`), writes them directly (`docs/build-plan/05k-mcp-setup-workspace.md:214-220`, `docs/build-plan/05k-mcp-setup-workspace.md:271-273`), and does not wrap template load / validate / write operations in a catch-all path. As specified, there is no mechanism to inject the header, preserve a `USER RULES` section, or convert write failures into `warnings[]`.
  - **Medium:** The change set leaves the planning canon split across old and new MEU identities. `build-priority-matrix.md` defines `5.H1` and `5.H2` at `docs/build-plan/build-priority-matrix.md:272-273`, and `.agent/context/meu-registry.md:168-173` adds `MEU-165a` / `MEU-165b`, but `docs/BUILD_PLAN.md:441` still declares a single `MEU-165 | mcp-ide-config | 5.H`. `docs/build-plan/mcp-planned-readiness.md:161-170` is also stale (`All 68 tools`, `05a-05j`, `core: 11 tools`). A planning agent reading the top-level build plan, MCP readiness summary, and registry would not get one coherent source of truth for this feature.
  - **Medium:** `minimal` scope is internally inconsistent in the same file. The scope table says `minimal` creates `AGENTS.md` plus the detected IDE shim at `docs/build-plan/05k-mcp-setup-workspace.md:28`, but the implementation loop explicitly writes all four IDE shims at `docs/build-plan/05k-mcp-setup-workspace.md:217-220`. The test stub then expects no `.agent/` directory while also expecting `.scaffold-meta.json` creation at `docs/build-plan/05k-mcp-setup-workspace.md:483-488`, which is impossible because the metadata file lives under `.agent/`.
- Open questions:
  - Assumed review scope includes downstream canonical docs affected by the new tool count and MEU split, even though they were not listed in the user's edited-file summary. That assumption follows the build-plan review workflow and the explicit "review all changes" request.
- Verdict:
  - `changes_required`
- Residual risk:
  - This is a docs/spec review only. Actual TypeScript implementation, packaging, and template content were not present to execute or test.
- Anti-deferral scan result:
  - Findings are actionable now; none depend on future implementation work to validate

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this docs-only review
- Blocking risks:
  - None beyond the reviewer findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Correct the `05k` scaffold flow so clean nested writes, provenance/header handling, and error behavior are internally consistent.
  - Recompute and update the MCP tool-count canon (`05-mcp-server.md`, `mcp-tool-index.md`, readiness summary).
  - Normalize top-level build-plan / registry / readiness docs to the new `5.H1` / `5.H2`, `MEU-165a` / `MEU-165b` split.

---

## Corrections Applied — 2026-03-15

### Findings Resolved

All 5 findings from the initial review have been corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F1 | High | Rewrote `validatePath()` to walk up path hierarchy to nearest existing ancestor instead of calling `realpath(dirname)` which throws ENOENT on fresh scaffolds |
| F2 | High | Updated stale MCP tool counts across 5 files: `core` 11→12, default 37→38, always-loaded 15→16, total 68→69 |
| F3 | High | Added provenance header injection in `loadTemplate()`, `writeTemplate()` wrapper with per-file `try/catch`, outer catch-all around entire tool handler body |
| F4 | Medium | Updated `mcp-tool-index.md` (new catalog row, reference map entry, category file range 05a–05k) and `mcp-planned-readiness.md` (file count, annotations count, core description) |
| F5 | Medium | Fixed `minimal` scope table ("all IDE shims"), moved `.scaffold-meta.json` to project root, fixed test stub expectations |

### Sibling Fixes (Step 2b generalizations)

- `00-overview.md:107,111` — "37 tools" → "38 tools" in MCP Rollout Stages table and note
- `mcp-tool-index.md:135` — "05a–05j" → "05a–05k" in Reference Map heading

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F1: validatePath ancestor walk. F3: provenance header, writeTemplate wrapper, catch-all. F5: scope table, meta location, test stub |
| `docs/build-plan/05-mcp-server.md` | F2: 37→38 (×3), 15→16 (×1) |
| `docs/build-plan/mcp-tool-index.md` | F2+F4: header range, catalog row, unique count, core toolset, default count, reference map entry+heading |
| `docs/build-plan/mcp-planned-readiness.md` | F4: 68→69 tools, 10→11 files, core 11→12 |
| `docs/build-plan/00-overview.md` | Sibling: 37→38 (×2) in rollout stages |

### Verification Results

```
# V1: Stale patterns (expect 0)
rg -n "37 tools|15 tools minimum|All 68 tools|05a.*05j" docs/build-plan/
→ 0 matches ✅

# V2: New counts confirmed
rg -n "38 tools|16 tools minimum|All 69 tools" docs/build-plan/
→ All matches show correct updated values ✅

# V3: New tool in downstream docs
rg -n "zorivest_setup_workspace|setup.workspace" docs/build-plan/mcp-tool-index.md
→ 3 matches (catalog row, reference map, header) ✅
```

Cross-doc sweep: 7 files checked, 5 updated.

### Verdict

`corrections_applied` — ready for recheck

---

## Recheck 2 — 2026-03-15

### Scope

Re-reviewed:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- `docs/BUILD_PLAN.md`
- supporting downstream MCP canon already corrected in prior pass

### Commands Executed

- `git status --short`
- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md docs/build-plan/05-mcp-server.md docs/build-plan/00-overview.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md docs/build-plan/build-priority-matrix.md .agent/context/meu-registry.md docs/BUILD_PLAN.md`
- direct file reads for:
  - `docs/build-plan/05k-mcp-setup-workspace.md`
  - `docs/BUILD_PLAN.md`
- `rg -n "USER_RULES_MARKER|new URL\\(|mcpRoots|pathname|preserve" docs/build-plan/05k-mcp-setup-workspace.md`
- `node -e "console.log(new URL('file:///P:/zorivest').pathname); console.log(new URL('file:///C:/Users/Test').pathname)"`

### Findings

- **High:** The new MCP-roots fallback is still incorrect on Windows. The spec now uses `new URL(mcpRoots[0].uri).pathname` at `docs/build-plan/05k-mcp-setup-workspace.md:218-220` to derive the project root from `file:///P:/...`. On Windows that yields `/P:/zorivest`, not `P:/zorivest` (verified with Node during review), so `fs.access(root)` at `docs/build-plan/05k-mcp-setup-workspace.md:223` would fail for valid workspace roots. The fallback exists now, but it is not platform-correct.

- **High:** The USER RULES preservation flow still does not satisfy the stated contract. The doc promises that content below `<!-- USER RULES BELOW -->` is preserved across updates at `docs/build-plan/05k-mcp-setup-workspace.md:22`, but `safeWrite()` still returns early on any hash mismatch at `docs/build-plan/05k-mcp-setup-workspace.md:138-147` before it reaches the splice logic at `docs/build-plan/05k-mcp-setup-workspace.md:161-170`. That means actual user edits below the marker are treated as “user-modified, backed up but not overwritten,” not preserved into the updated template. The hash tracking is also still based on the pre-splice `contentHash` at `docs/build-plan/05k-mcp-setup-workspace.md:177-178`, so even if preservation happens in a force/update path, the stored hash can diverge from the actual written file.

### Resolved From Prior Pass

- `docs/BUILD_PLAN.md` MEU split drift: resolved
- MCP count drift (`38` / `16` / `69`) in downstream docs: still resolved
- marker-preservation logic presence: resolved, but the behavior is still incorrect as described above

### Recheck 2 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or tests were present to execute.

---

## Recheck 4 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- `docs/BUILD_PLAN.md`

### Commands Executed

- `git status --short`
- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md docs/BUILD_PLAN.md docs/build-plan/05-mcp-server.md docs/build-plan/00-overview.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md docs/build-plan/build-priority-matrix.md .agent/context/meu-registry.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/BUILD_PLAN.md`
- `rg -n "USER RULES|marker|template_hash|same-template|below marker|preserve" docs/build-plan/05k-mcp-setup-workspace.md`

### Findings

- **High:** The USER RULES preservation path is still incomplete across the full update lifecycle. The current `safeWrite()` flow now computes `templateHash` before splice and `contentHash` after splice at `docs/build-plan/05k-mcp-setup-workspace.md:129-146`, and the user-modified guard checks both `meta.hash` and `meta.template_hash` at `docs/build-plan/05k-mcp-setup-workspace.md:157-161`. But the same-content early return at `docs/build-plan/05k-mcp-setup-workspace.md:151-154` still does not refresh metadata. Inference from the current flow: if the user edits only below `<!-- USER RULES BELOW -->`, then reruns the same template version, the file is skipped as intended, but `meta.hash` remains stale. On the next template update, `existingHash` no longer matches either stored hash, so the code falls into the "user-modified outside marker" branch and skips the template update instead of preserving the user section into the new template. That still violates the design promise at `docs/build-plan/05k-mcp-setup-workspace.md:22`.

### Resolved From Prior Pass

- Windows `project_root` fallback: resolved
- `project_root` input-table default: resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 4 Verdict

`changes_required`

### Residual Risk

The spec still has no test stub covering the sequence: user edits only below marker → same-template rerun → later template update. That is the exact path still at risk.

---

## Recheck 3 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- `docs/BUILD_PLAN.md`

### Commands Executed

- `git status --short`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/BUILD_PLAN.md`
- `rg -n "USER RULES BELOW|new URL\\(|mcpRoots|project_root|contentHash|existingMeta && existingHash !== existingMeta.hash|markerIdx|meta.files\\[relPath\\]" docs/build-plan/05k-mcp-setup-workspace.md`
- `node -e "console.log(new URL('file:///P:/zorivest').pathname)"`

### Findings

- **High:** The USER RULES preservation flow is still not correct across template updates. The current code now splices marker content before hashing at `docs/build-plan/05k-mcp-setup-workspace.md:129-143`, which fixes the previous ordering problem, but the full-file hash in `meta.files[relPath]` is still used as the user-modification guard at `docs/build-plan/05k-mcp-setup-workspace.md:154-163` and stored again at `docs/build-plan/05k-mcp-setup-workspace.md:181-182`. Inference from the current flow: if a user edits only the section below `<!-- USER RULES BELOW -->`, a same-template rerun will skip without refreshing `meta.hash`; the next template update will then hit the `existingHash !== existingMeta.hash` branch and skip the update instead of preserving the user section into the new template. That still falls short of the design promise at `docs/build-plan/05k-mcp-setup-workspace.md:22`.

- **Low:** The runtime logic now resolves `project_root` as explicit param → MCP roots[0] → CWD at `docs/build-plan/05k-mcp-setup-workspace.md:215-225`, but the input summary table still says the default is just `CWD` at `docs/build-plan/05k-mcp-setup-workspace.md:366`. The contract text should match the current behavior.

### Resolved From Prior Pass

- Windows MCP-root conversion: resolved via `url.fileURLToPath(...)`
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 3 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or tests were present to execute.

---

## Recheck — 2026-03-15

### Scope

Re-reviewed:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- `docs/build-plan/05-mcp-server.md`
- `docs/build-plan/00-overview.md`
- `docs/build-plan/mcp-tool-index.md`
- `docs/build-plan/mcp-planned-readiness.md`
- `docs/build-plan/build-priority-matrix.md`
- `.agent/context/meu-registry.md`
- `docs/BUILD_PLAN.md`

### Commands Executed

- `git status --short`
- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md docs/build-plan/build-priority-matrix.md docs/build-plan/05-mcp-server.md .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md`
- `rg -n "USER_RULES_MARKER|USER RULES BELOW|preserved|preserve|detected IDE shim|IDE shim|never throws|scaffold-meta|mcp roots\\[0\\]|all IDE shims" docs/build-plan/05k-mcp-setup-workspace.md`
- `rg -n "MEU-165a|MEU-165b|5.H1|5.H2|MEU-165|5.H\\b" docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/build-plan/build-priority-matrix.md`
- `rg -n "37 tools|38 tools|15 tools minimum|16 tools minimum|68 tools|69 tools" docs/build-plan/00-overview.md docs/build-plan/05-mcp-server.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md docs/BUILD_PLAN.md`

### Findings

- **High:** The default project-root behavior still does not match the tool contract. The schema says `project_root` defaults to `CWD or MCP roots[0]` at `docs/build-plan/05k-mcp-setup-workspace.md:187-189`, but the implementation sketch only does `const root = project_root ?? process.cwd();` at `docs/build-plan/05k-mcp-setup-workspace.md:201-202`. There is no access path to MCP roots in the handler. For a workspace-scaffolding tool, that means the no-argument path can still target the server process directory rather than the user workspace.

- **Medium:** The top-level build plan is still on the old research-item identity. `build-priority-matrix.md` and `.agent/context/meu-registry.md` now use `5.H1` / `5.H2` and `MEU-165a` / `MEU-165b` at `docs/build-plan/build-priority-matrix.md:272-273` and `.agent/context/meu-registry.md:172-173`, but `docs/BUILD_PLAN.md:441` still declares a single `MEU-165 | mcp-ide-config | 5.H`. The planning canon is still split.

- **Medium:** The file still promises `<!-- USER RULES BELOW -->` preservation without specifying any preservation logic. The contract remains in `docs/build-plan/05k-mcp-setup-workspace.md:22`, and `USER_RULES_MARKER` is defined at `docs/build-plan/05k-mcp-setup-workspace.md:172`, but the template-loading/writing flow in `docs/build-plan/05k-mcp-setup-workspace.md:174-290` only prepends a provenance header and writes whole-file content. There is no merge or splice behavior around the marker, so the preservation guarantee is still undocumented in executable terms.

### Resolved From Prior Pass

- `validatePath()` clean-workspace failure: resolved
- 37/15/68 tool-count drift in MCP docs: resolved
- `minimal` scope vs metadata-path contradiction: resolved
- Downstream MCP index/readiness updates: resolved

### Recheck Verdict

`changes_required`

### Residual Risk

This remains a docs/spec review only. No implementation or tests were present to execute.

---

## Corrections Applied — Round 2 — 2026-03-15

### Findings Resolved

All 3 recheck findings corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F6 | High | Added MCP roots fallback: `project_root > server.server?.roots[0] > process.cwd()` |
| F7 | Medium | Split `BUILD_PLAN.md:441` single MEU-165 into MEU-165a + MEU-165b rows with 05k spec links |
| F8 | Medium | Added USER RULES marker splice logic in `safeWrite()` — preserves content below `<!-- USER RULES BELOW -->` during updates. Clarified Design Principles table. |

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F6: MCP roots fallback. F8: USER RULES splice in safeWrite(), Design Principles clarification |
| `docs/BUILD_PLAN.md` | F7: MEU-165 → MEU-165a + MEU-165b |

### Verification Results

```
V1: mcpRoots in 05k → 3 matches ✅
V2: MEU-165a/165b in BUILD_PLAN → 2 matches ✅
V3: USER_RULES logic in 05k → 6 matches ✅
V4: Stale "MEU-165 |" in BUILD_PLAN → 0 matches ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Corrections Applied — Round 3 — 2026-03-15

### Findings Resolved

All 2 Recheck 2 findings corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F9 | High | Replaced `new URL().pathname` with `url.fileURLToPath()` which correctly handles Windows `file://` URIs (no leading `/`). Added `import * as url from 'url'`. |
| F10 | High | Restructured `safeWrite()`: USER RULES splice moved before hash comparison and early returns. `contentHash` now computed from post-splice content. Added `!force` guard to user-modified branch. |

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F9: `url.fileURLToPath()` + import. F10: safeWrite flow reorder, post-splice hash. |

### Verification Results

```
V1: fileURLToPath + import → 2 matches ✅
V2: Stale new URL().pathname → 0 matches ✅
V3: Splice-before-hash comments confirmed ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Corrections Applied — Round 4 — 2026-03-15

### Findings Resolved

All 2 Recheck 3 findings corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F11 | High | Separated `templateHash` (pre-splice) from `contentHash` (post-splice). User-modified guard now checks both `meta.hash` AND `meta.template_hash` — edits only below marker no longer trigger false-positive skip. |
| F12 | Low | Input summary table default updated from "CWD" to "CWD or MCP roots[0]" |

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F11: dual-hash tracking + guard. F12: input table. |

### Verification Results

```
V1: templateHash refs → 4 matches ✅
V2: "CWD or MCP" in input table → confirmed ✅
V3: template_hash in guard + meta + flowchart → 3 matches ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Corrections Applied — Round 5 — 2026-03-15

### Findings Resolved

1 Recheck 4 finding corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F13 | High | Added `meta.files[relPath]` refresh on same-content skip path — `meta.hash` and `meta.template_hash` now stay current even when file is skipped (user edited below marker). Also added lifecycle test stub covering: initial scaffold → user edit below marker → same-template rerun → template update. |

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F13: meta refresh on skip (L153–156) + lifecycle test stub (L628–636) |

### Verification Results

```
V1: "Refresh meta" comment → L153 ✅
V2: lifecycle test stub → found ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Recheck 5 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- related MCP planning docs touched in this review thread

### Commands Executed

- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md docs/build-plan/build-priority-matrix.md docs/build-plan/05-mcp-server.md docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`
- `rg -n "USER RULES BELOW|USER_RULES_MARKER|templateHash|contentHash|meta.files\\[relPath\\]|project_root|MCP roots\\[0\\]|skip" docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `.agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`

### Findings

- **High:** The USER RULES marker contract is still internally inconsistent. The feature promise remains at `docs/build-plan/05k-mcp-setup-workspace.md:22`, and the lifecycle test stub assumes the initial scaffold already gives the user a `<!-- USER RULES BELOW -->` section to edit at `docs/build-plan/05k-mcp-setup-workspace.md:627-635`. But `loadTemplate()` only prepends a provenance header at `docs/build-plan/05k-mcp-setup-workspace.md:203-207`, and the AGENTS content outline at `docs/build-plan/05k-mcp-setup-workspace.md:431-439` never specifies where the marker appears in the generated file. Meanwhile `safeWrite()` unconditionally appends a fresh marker when it finds one in the existing file at `docs/build-plan/05k-mcp-setup-workspace.md:135-142`. Inference from the current spec: either the template does not contain the marker, in which case first-run files do not expose the promised preservation section, or the template does contain it, in which case the current splice logic duplicates the marker on update. The template model is still not implementation-ready.

- **Low:** The explanatory sections still describe the old one-hash behavior. The defense summary says `Backup before overwrite; skip user-modified` at `docs/build-plan/05k-mcp-setup-workspace.md:481`, and the idempotency flow still uses the older `hash matches meta` / `current ≠ meta.hash` description at `docs/build-plan/05k-mcp-setup-workspace.md:498-502`. That no longer matches the current dual-hash and below-marker-preservation logic in `safeWrite()`.

### Resolved From Prior Pass

- same-content metadata refresh on skip: resolved
- lifecycle test stub for below-marker update path: resolved
- Windows `project_root` fallback: remains resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 5 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or executable tests were present to run.

---

## Recheck 6 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`

### Commands Executed

- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md .agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`
- `rg -n "USER RULES BELOW|USER_RULES_MARKER|loadTemplate|templateMarkerIdx|indexOf\\(|lastIndexOf\\(|contentHash|templateHash|skip user-modified|Idempotency Flow" docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`
- tail read of `.agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`

### Findings

- **High:** The new marker-dedup logic is still brittle because it strips from the first marker occurrence, not the terminal scaffold marker. In `safeWrite()`, the update path now does `const templateMarkerIdx = content.indexOf(USER_RULES_MARKER)` and truncates `content` at that point at `docs/build-plan/05k-mcp-setup-workspace.md:142-145`. That only works if the template body never contains the literal marker string anywhere except the final appended marker from `loadTemplate()` at `docs/build-plan/05k-mcp-setup-workspace.md:208-212`. As specified, that assumption is not guaranteed. If a template ever mentions `<!-- USER RULES BELOW -->` in prose or an example, the file would be truncated at the first occurrence during update. The spec should either use `lastIndexOf()` / terminal-marker stripping or explicitly constrain templates to a single trailing marker occurrence.

### Resolved From Prior Pass

- marker existence / duplication ambiguity: resolved
- stale defense summary and idempotency flow: resolved
- same-content metadata refresh on skip: remains resolved
- Windows `project_root` fallback: remains resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 6 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or executable tests were present to run.

---

## Corrections Applied — Round 6 — 2026-03-15

### Findings Resolved

All 2 Recheck 5 findings corrected. 0 refuted.

| # | Severity | Fix Applied |
|---|----------|-------------|
| F14 | High | `loadTemplate()` now appends `USER_RULES_MARKER` to every generated file. `safeWrite()` splice strips marker from new template before appending user section (prevents duplication). AGENTS.md content outline adds item 8 for marker placement. |
| F15 | Low | Defense summary table updated with dual-hash description and below-marker preservation. Idempotency flow diagram rewritten as 6-step process reflecting splice → dual-hash → guard logic. |

### Files Changed

| File | Changes |
|------|---------|
| `docs/build-plan/05k-mcp-setup-workspace.md` | F14: loadTemplate marker append, splice dedup (templateMarkerIdx), outline item 8. F15: defense table, flow diagram. |

### Verification Results

```
USER_RULES_MARKER refs → 6 ✅
templateMarkerIdx refs → 3 ✅
"User rules marker" in outline → 1 ✅
"dual-hash" in defense table → 1 ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Corrections Applied — Round 7 — 2026-03-15

### Findings Resolved

| # | Severity | Fix Applied |
|---|----------|-------------|
| F16 | High | `indexOf(USER_RULES_MARKER)` → `lastIndexOf(USER_RULES_MARKER)` — strips only the terminal marker, not earlier prose occurrences |

### Verification

```
lastIndexOf at L142 ✅
```

### Verdict

`corrections_applied` — ready for recheck

---

## Recheck 7 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`

### Commands Executed

- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md .agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`
- `rg -n "USER_RULES_MARKER|indexOf\\(|lastIndexOf\\(|IDE shim|all IDE shims|minimal \\(AGENTS\\.md \\+ IDE shim\\)|getDetectedClient" docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`

### Findings

- **Low:** The schema text for `scope` is still out of sync with the specified behavior. The scope table says `minimal` creates `AGENTS.md` plus **all IDE shims** at `docs/build-plan/05k-mcp-setup-workspace.md:28`, and the implementation sketch always generates all four shim files at `docs/build-plan/05k-mcp-setup-workspace.md:289-295`, but the Zod description still says `minimal (AGENTS.md + IDE shim)` at `docs/build-plan/05k-mcp-setup-workspace.md:225-226`. The input contract should match the actual scaffold behavior.

### Resolved From Prior Pass

- terminal-marker stripping now uses `lastIndexOf()`: resolved
- marker existence / duplication ambiguity: remains resolved
- stale defense summary and idempotency flow: remains resolved
- same-content metadata refresh on skip: remains resolved
- Windows `project_root` fallback: remains resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 7 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or executable tests were present to run.

---

## Corrections Applied — Round 8 — 2026-03-15

### Findings Resolved

| # | Severity | Fix Applied |
|---|----------|-------------|
| F17 | Low | Zod `scope` description: `IDE shim` → `all IDE shims` to match scope table and implementation |

### Verdict

`corrections_applied` — ready for recheck

---

## Recheck 8 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`

### Commands Executed

- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md .agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`
- `rg -n "creates or updates an \\.agent/ directory|optional \\.agent/ directory|minimal|all IDE shims|scope: z\\.enum" docs/build-plan/05k-mcp-setup-workspace.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`

### Findings

- **Low:** The overview still overstates `.agent/` creation. The top-level summary says the tool "creates or updates an `.agent/` directory" at `docs/build-plan/05k-mcp-setup-workspace.md:12`, but the scope table and test stubs still define `minimal` as `AGENTS.md` + all IDE shims with no `.agent/` directory at `docs/build-plan/05k-mcp-setup-workspace.md:28-30` and `docs/build-plan/05k-mcp-setup-workspace.md:558-563`. The tool registration text is already more accurate with "optional `.agent/` directory" at `docs/build-plan/05k-mcp-setup-workspace.md:220`; the overview should match that contract.

### Resolved From Prior Pass

- `scope` schema text now matches "all IDE shims": resolved
- terminal-marker stripping now uses `lastIndexOf()`: remains resolved
- marker existence / duplication ambiguity: remains resolved
- stale defense summary and idempotency flow: remains resolved
- same-content metadata refresh on skip: remains resolved
- Windows `project_root` fallback: remains resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 8 Verdict

`changes_required`

### Residual Risk

Docs/spec review only. No implementation or executable tests were present to run.

---

## Corrections Applied — Round 9 — 2026-03-15

### Findings Resolved

| # | Severity | Fix Applied |
|---|----------|-------------|
| F18 | Low | Overview at L12: rewrote to say 'generates AGENTS.md and IDE-specific shim files, and optionally creates an `.agent/` directory' — matches minimal scope behavior |

### Verdict

`corrections_applied` — ready for recheck

---

## Recheck 9 — 2026-03-15

### Scope

Re-reviewed current file state for:

- `docs/build-plan/05k-mcp-setup-workspace.md`
- related MCP planning references touched in this review thread

### Commands Executed

- `git diff -- docs/build-plan/05k-mcp-setup-workspace.md .agent/context/handoffs/2026-03-15-build-plan-workspace-setup-critical-review.md`
- `rg -n "creates or updates an \\.agent/ directory|optional \\.agent/ directory|all IDE shims|IDE shim|lastIndexOf\\(|USER_RULES_MARKER|backup before overwrite|hash matches meta|user modified above marker|tool specs|16 tools minimum|38 tools" docs/build-plan/05k-mcp-setup-workspace.md docs/build-plan/05-mcp-server.md docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/build-plan/build-priority-matrix.md`
- line-numbered reads of `docs/build-plan/05k-mcp-setup-workspace.md`

### Findings

No findings.

### Resolved From Prior Pass

- overview now matches optional `.agent/` creation: resolved
- `scope` schema text now matches "all IDE shims": remains resolved
- terminal-marker stripping now uses `lastIndexOf()`: remains resolved
- marker existence / duplication ambiguity: remains resolved
- stale defense summary and idempotency flow: remains resolved
- same-content metadata refresh on skip: remains resolved
- Windows `project_root` fallback: remains resolved
- `docs/BUILD_PLAN.md` MEU split: remains resolved
- downstream MCP count canon: remains resolved

### Recheck 9 Verdict

`no_findings`

### Residual Risk

Docs/spec review only. No implementation or executable tests were present to run.
