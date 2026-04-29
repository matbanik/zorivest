---
date: "2026-04-28"
project: "pipeline-remediation"
meu: "MEU-PW14, MEU-72b"
status: "draft"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-04-28-pipeline-remediation/implementation-plan.md"
build_plan_section: "bp09hs49.29, bp06ks35b.2"
agent: "antigravity"
reviewer: "codex"
predecessor: "2026-04-27-approval-security-handoff.md"
---

# Handoff: 2026-04-28-pipeline-remediation-handoff

> **Status**: `draft`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-PW14 — Pipeline Markdown Migration (drop PDF rendering, switch to Markdown output, remove Playwright dependency)
**MEU**: MEU-72b — Email Templates GUI (tabbed SchedulingLayout with template CRUD, preview, default protection)
**Build Plan Section**: §09h Pipeline Markdown Migration, §06k GUI Email Template Management
**Predecessor**: [2026-04-27-approval-security-handoff.md](2026-04-27-approval-security-handoff.md)

---

## Acceptance Criteria

### MEU-PW14

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-PW14-1 | `pdf_renderer.py` deleted | Spec | `test_pipeline_markdown_migration.py::test_pdf_renderer_removed` | ✅ |
| AC-PW14-2 | Playwright dep removed from pyproject.toml | Spec | `test_pipeline_markdown_migration.py::test_playwright_dependency_removed` | ✅ |
| AC-PW14-3 | `output_format` rejects `"pdf"` and `"both"` | Spec | `test_pipeline_markdown_migration.py::test_output_format_rejects_pdf` | ✅ |
| AC-PW14-4 | `_render_markdown()` produces `.md` | Spec | `test_pipeline_markdown_migration.py::test_render_markdown_produces_md_file` | ✅ |
| AC-PW14-5 | `pdf_path` removed; optional `attachment_path` for `.md` added | Spec §9H.2 | `test_pipeline_markdown_migration.py::test_F2a_*` through `test_F2e_*` (5 tests) | ✅ |
| AC-PW14-6 | Email sender supports optional `.md` MIME attachment, rejects `.pdf` | Spec §9H.6 | `test_pipeline_markdown_migration.py::test_F2c_*`, `test_F2d_*` | ✅ |
| AC-PW14-7 | Model/repo defaults changed to `"html"` | Spec | `test_pipeline_markdown_migration.py::test_model_default_format_is_html` | ✅ |
| AC-PW14-8 | Zero `pdf_renderer`/`render_pdf`/`pdf_path` references | Spec | `rg` scan → 0 matches | ✅ |

### MEU-72b

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-72b-1 | Tabbed layout with "Report Policies" + "Email Templates" | Spec §6K.1 | `email-templates.test.tsx::AC-72b-1 *` (3 tests) | ✅ |
| AC-72b-2 | Template list with `is_default` badge, `refetchInterval: 5s` | Spec §6K.2 | `email-templates.test.tsx::AC-72b-2 *` (4 tests) | ✅ |
| AC-72b-3 | Detail editor with name, description, subject, body | Spec §6K.3 | `email-templates.test.tsx::AC-72b-3 *` (3 tests) | ✅ |
| AC-72b-4 | Default protection: read-only banner, disabled fields | Spec §6K.4 | `email-templates.test.tsx::AC-72b-4 *` (2 tests) | ✅ |
| AC-72b-5 | CRUD buttons: Save, Duplicate, Delete, Preview with G2 guard | Spec §6K.5 | `email-templates.test.tsx::AC-72b-5 *` (8 tests) | ✅ |
| AC-72b-6 | Sandboxed iframe preview | Spec §6K.6 | `email-templates.test.tsx::AC-72b-6 *` (3 tests) | ✅ |
| AC-72b-7 | All 11 test IDs defined | Spec §6K.9 | `email-templates.test.tsx::AC-72b-7` | ✅ |
| AC-72b-8 | React Query key factory + cache invalidation | Spec §6K.8 | `email-templates.test.tsx::AC-72b-8 *` (4 tests) | ✅ |
| AC-72b-9 | New Template button | Spec §6K.2 | `email-templates.test.tsx::AC-72b-9 *` (2 tests) | ✅ |

<!-- CACHE BOUNDARY -->

---

## Evidence

### FAIL_TO_PASS

| Phase | Test Count | Result |
|-------|-----------|--------|
| MEU-PW14 Red | 8 tests | All FAIL (expected) |
| MEU-PW14 Green | 8 tests | All PASS |
| MEU-72b Red | 33 tests | All FAIL (expected) |
| MEU-72b Green | 33 tests | All PASS |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v` | 0 | 8 passed |
| `rg "pdf_renderer\|render_pdf\|_render_pdf\|pdf_path" packages/` | 1 | 0 matches |
| `rg "playwright" packages/infrastructure/pyproject.toml` | 1 | 0 matches |
| `npx vitest run src/.../email-templates.test.tsx` | 0 | 33 passed |
| `npx vitest run` (full UI) | 0 | 469 passed, 29 files |
| `npx tsc --noEmit` | 0 | 0 errors |
| `npx eslint` (new files only) | 0 | 0 warnings |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | 8/8 blocking checks PASS |

### Quality Gate Results

```
pyright: 0 errors
ruff: 0 violations
pytest: all unit tests pass
vitest: 469 passed (29 files)
tsc: 0 errors
eslint: 0 new warnings
anti-placeholder: 0 matches
anti-deferral: 0 matches
```

---

## Changed Files

### MEU-PW14

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py` | deleted | Entire PDF renderer removed |
| `packages/infrastructure/pyproject.toml` | modified | Removed playwright dependency |
| `packages/core/src/zorivest_core/pipeline_steps/render_step.py` | modified | Removed `_render_pdf()`, added `_render_markdown()`, constrained `output_format` |
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modified | `pdf_path` removed; optional `attachment_path` added to Params; wired to `_send_emails()` |
| `packages/infrastructure/src/zorivest_infra/email/email_sender.py` | modified | `pdf_path` removed; optional `attachment_path` param + `.md`-only MIME attachment logic |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modified | `format` default `"pdf"` → `"html"` |
| `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | modified | `format` kwarg default `"pdf"` → `"html"` |
| `tests/unit/test_pipeline_markdown_migration.py` | new | 8 FIC tests |

### MEU-72b

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/template-api.ts` | new | 6 API functions |
| `ui/src/renderer/src/features/scheduling/template-hooks.ts` | new | 7 React Query hooks + key factory |
| `ui/src/renderer/src/features/scheduling/EmailTemplateList.tsx` | new | Template list sidebar |
| `ui/src/renderer/src/features/scheduling/EmailTemplateDetail.tsx` | new | Template editor with default protection |
| `ui/src/renderer/src/features/scheduling/EmailTemplatePreview.tsx` | new | Sandboxed iframe preview |
| `ui/src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx` | new | 33 FIC tests |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modified | Added tab bar + template state management |
| `ui/src/renderer/src/features/scheduling/test-ids.ts` | modified | 11 new template test IDs |
| `ui/tests/e2e/email-templates.test.ts` | new | 3 Wave 8 E2E tests |
| `ui/tests/e2e/test-ids.ts` | modified | 11 template E2E test IDs |

### Ad-Hoc GUI Hardening (post-MEU)

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/PolicyDetail.tsx` | modified | AH-1: MCP execution status indicator (lock/unlock icon + text next to state pill). AH-5/AH-6: Dirty-state tracking + portal inline styles |
| `ui/src/renderer/src/features/scheduling/EmailTemplateDetail.tsx` | modified | AH-2: Save button fix for non-default templates. AH-4: Inline pencil-edit name (rename-as-recreate). AH-5: Dirty-state `onDirtyChange` callback. AH-7: Interactive variable autocomplete dropdown with template body parsing + 20 curated pipeline variables |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modified | AH-3: Preview rendering wired to POST endpoint. AH-5: Navigation guard portal modal. AH-6: Inline styles for Electron portal fix. AH-8: Collapsible Run History with +/− toggle. AH-9: Flex layout restructure keeping action buttons always visible |
| `ui/src/renderer/src/components/layout/NavRail.tsx` | modified | AH-10: Settings nav moved to bottom-pinned section above Collapse toggle |
| `ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx` | modified | CodeMirror mock fix (updateListener extension) |
| `ui/src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx` | modified | Updated tests for pencil-edit, dirty tracking, save button changes |

---

## Codex Validation Report

_Left blank for reviewer agent._

---

## Deferred Items

| Item | Reason | Follow-up |
|------|--------|-----------|
| E2E test execution | Requires running Electron app | Run Wave 8 E2E tests when Electron is available |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-04-28 | antigravity | Initial handoff with 2 MEUs |
| Updated | 2026-04-28 | antigravity | Added 10 ad-hoc GUI hardening items (AH-1 through AH-10). Test count 464→469. |
