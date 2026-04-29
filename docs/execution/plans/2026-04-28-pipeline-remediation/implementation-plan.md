---
project: "2026-04-28-pipeline-remediation"
date: "2026-04-28"
source: "docs/build-plan/09h-pipeline-markdown-migration.md, docs/build-plan/06k-gui-email-templates.md"
meus: ["MEU-PW14", "MEU-72b"]
status: "pending_review"
---

# Implementation Plan: Pipeline Markdown Migration + Email Templates GUI

> **Project**: `2026-04-28-pipeline-remediation`
> **Build Plan Section(s)**: §09h Pipeline Markdown Migration, §06k GUI Email Template Management
> **Status**: `pending_review`

---

## Goal

Two discrete hardening tasks for the pipeline and scheduling subsystems:

1. **MEU-PW14** — Drop PDF rendering (and the Playwright/Chromium dependency it requires) from the pipeline. Replace with lightweight, AI-consumable Markdown output. This resolves known issue `PIPE-DROPPDF`.

2. **MEU-72b** — Add an "Email Templates" tab to the `SchedulingLayout` GUI page, enabling template CRUD, default protection, and live preview via the existing `/api/v1/scheduling/templates` endpoints. This resolves known issue `GUI-EMAILTMPL`.

---

## User Review Required

> [!IMPORTANT]
> **MEU-PW14 is a breaking change for any pipelines with `output_format: "pdf"` or `"both"`.** After this change, `"pdf"` and `"both"` are no longer valid values. Existing policy documents that reference these values will fail validation. The recommended migration is to change to `"html"` (default) or `"markdown"`.
>
> **MEU-72b is frontend-only.** All 6 API endpoints already exist and are tested. No backend changes required.

---

## Proposed Changes

### MEU-PW14: Pipeline Markdown Migration

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| RenderStep.Params | `RenderStep.Params` (Pydantic) | `output_format`: `"html"` (default) or `"markdown"` only | `extra="forbid"` |
| SendStep.Params | `SendStep.Params` (Pydantic) | `pdf_path` → `attachment_path` (optional str) | `extra="forbid"` |
| `send_report_email()` | function signature | `pdf_path` → `attachment_path` (optional str) | N/A |
| ReportModel.format | SQLAlchemy Column | default changes `"pdf"` → `"html"` | N/A |
| ReportRepository.create | method signature | `format` kwarg default `"pdf"` → `"html"` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `pdf_renderer.py` deleted and no import references remain | Spec §9H.2 | `import zorivest_infra.rendering.pdf_renderer` raises ImportError |
| AC-2 | Playwright dependency removed from `packages/infrastructure/pyproject.toml` | Spec §9H.2 | N/A (grep verification) |
| AC-3 | `RenderStep._render_pdf()` removed | Spec §9H.2 | N/A (method no longer exists) |
| AC-4 | `RenderStep._render_markdown()` added; converts dict data to Markdown tables | Spec §9H.3 | Empty data returns `"*No data available.*"` |
| AC-5 | `output_format` only accepts `"html"` or `"markdown"`; `"pdf"` and `"both"` rejected | Spec §9H.4 | `output_format="pdf"` raises Pydantic `ValidationError` |
| AC-6 | `SendStep.Params.pdf_path` renamed to `attachment_path` | Spec §9H.2 | N/A (schema change) |
| AC-7 | `SendStep._save_local()` writes `.md` files, not PDF copies | Spec §9H.2 | Local file channel produces `.md` extension |
| AC-8 | `send_report_email()` accepts `attachment_path` instead of `pdf_path`; no PDF MIME attachment | Spec §9H.2 | Email sent without `MIMEApplication(pdf)` part |
| AC-9 | `ReportModel.format` default changed to `"html"` | Spec §9H.2 | New reports default to `"html"` format |
| AC-10 | `ReportRepository.create()` format default changed to `"html"` | Spec §9H.2 | N/A (code inspection) |
| AC-11 | All existing send_step and render_step tests updated and pass | Spec §9H.5 | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Delete pdf_renderer.py | Spec | §9H.2 explicit |
| Remove Playwright from deps | Spec | §9H.2 explicit |
| `_render_markdown()` implementation | Spec | §9H.3 with code example |
| output_format enum values | Spec | §9H.4 table |
| pdf_path → attachment_path rename | Spec | §9H.2, inferred from "remove pdf_path" + "add .md attachment" |
| `_save_local()` → `.md` files | Spec | §9H.2 explicit |
| Email attachment MIME type for .md | Research-backed | RFC 2046 — `text/markdown` (RFC 7763) |
| ReportModel default change | Spec | §9H.2 explicit |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py` | delete | Remove entire file |
| `packages/infrastructure/pyproject.toml` | modify | Remove `playwright>=1.50` dependency |
| `packages/core/src/zorivest_core/pipeline_steps/render_step.py` | modify | Remove `_render_pdf()`, add `_render_markdown()`, constrain `output_format` |
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modify | Rename `pdf_path` → `attachment_path`, update `_save_local()` for `.md`, update email call |
| `packages/infrastructure/src/zorivest_infra/email/email_sender.py` | modify | Rename `pdf_path` → `attachment_path`, change from PDF MIME to generic file attachment |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | `ReportModel.format` default `"pdf"` → `"html"` |
| `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | modify | `ReportRepository.create()` format default `"pdf"` → `"html"` |
| `tests/unit/test_store_render_step.py` | modify | Update tests for markdown, remove PDF tests |
| `tests/unit/test_send_step.py` | modify | Update for `attachment_path`, `.md` local save |
| `tests/unit/test_pipeline_markdown_migration.py` | new | Dedicated migration test file per §9H.5 |

---

### MEU-72b: Email Templates GUI

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| UI form payload → POST /templates | `EmailTemplateCreateRequest` (Pydantic, existing) | `name`: `^[a-z0-9][a-z0-9_-]*$`, `body_html`: required | `extra="forbid"` |
| UI form payload → PATCH /templates/{name} | `EmailTemplateUpdateRequest` (Pydantic, existing) | All fields optional | `extra="forbid"` |
| DELETE /templates/{name} | N/A | 403 for `is_default=true` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | Two-tab layout: "Report Policies" (default) + "Email Templates" | Spec §6K.1 | N/A |
| AC-2 | Tab bar follows `PlanningLayout.tsx` pattern with `border-b-2 + text-accent` active styling | Spec §6K.1, Local Canon | N/A |
| AC-3 | Template list shows `name` + `is_default` badge, refreshes every 5s | Spec §6K.2, §6K.8 (G5) | N/A |
| AC-4 | Detail editor shows all 6 fields from §6K.3 | Spec §6K.3 | N/A |
| AC-5 | Default templates: editor read-only, banner visible, delete disabled | Spec §6K.4 | Attempting to modify default template → fields disabled |
| AC-6 | Save: PATCH for existing, POST for new templates | Spec §6K.5 | N/A |
| AC-7 | Duplicate creates `{name}-custom` copy via POST | Spec §6K.5 | N/A |
| AC-8 | Delete via portaled modal (G20), 403 surfaced for defaults (G15) | Spec §6K.5 | Delete default → 403 error toast |
| AC-9 | Preview: `POST /templates/{name}/preview` → sandboxed `<iframe srcDoc>` | Spec §6K.6 | Preview disabled when `body_html` empty |
| AC-10 | New Template provides valid default body, not empty (G22) | Spec §6K.5 | N/A |
| AC-11 | All test IDs from §6K.9 assigned to components | Spec §6K.9 | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Tab bar layout | Spec + Local Canon | §6K.1 + existing PlanningLayout pattern |
| List+detail split | Spec | §6K.2 explicit |
| Field definitions | Spec | §6K.3 table |
| Default protection | Spec | §6K.4 explicit |
| Action buttons | Spec | §6K.5 table |
| Live preview | Spec | §6K.6 explicit |
| API endpoints | Spec (existing) | §6K.7 — all 6 endpoints already implemented |
| Test IDs | Spec | §6K.9 explicit list |
| Duplicate naming | Spec | §6K.5: `{name}-custom` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | modify | Add tab bar: "Report Policies" + "Email Templates" |
| `ui/src/renderer/src/features/scheduling/EmailTemplateList.tsx` | new | Template list sidebar with `is_default` badge, selection |
| `ui/src/renderer/src/features/scheduling/EmailTemplateDetail.tsx` | new | Detail editor with all fields, default protection, save/duplicate/delete |
| `ui/src/renderer/src/features/scheduling/EmailTemplatePreview.tsx` | new | Live preview component with sandboxed iframe |
| `ui/src/renderer/src/features/scheduling/template-api.ts` | new | API functions for template CRUD + preview |
| `ui/src/renderer/src/features/scheduling/template-hooks.ts` | new | React Query hooks for template operations |
| `ui/src/renderer/src/features/scheduling/test-ids.ts` | modify | Add template-related test IDs |
| `ui/src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx` | new | Vitest component/hook tests for template CRUD, default protection, preview |
| `ui/tests/e2e/email-templates.test.ts` | new | Wave 8 E2E tests (3 tests per §6K.10) |

---

## Out of Scope

- Database migration (Alembic) — default change only affects new rows
- MCP tool changes — no MCP tool modifications needed
- CodeMirror integration — spec says "code editor" but standard `<textarea>` with monospace font is acceptable as MVP; CodeMirror is a P3 enhancement

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. Validation:

```powershell
rg "pipeline-remediation" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Python Quality Gate (MEU-PW14)
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 2. Unit Tests (MEU-PW14)
```powershell
uv run pytest tests/unit/test_store_render_step.py tests/unit/test_send_step.py tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw14.txt; Get-Content C:\Temp\zorivest\pytest-pw14.txt | Select-Object -Last 40
```

### 3. TypeScript Type Check (MEU-72b)
```powershell
cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck.txt; Get-Content C:\Temp\zorivest\ui-typecheck.txt | Select-Object -Last 30
```

### 3b. Vitest Unit Tests (MEU-72b)
```powershell
cd ui; npx vitest run --reporter=verbose *> C:\Temp\zorivest\ui-vitest.txt; Get-Content C:\Temp\zorivest\ui-vitest.txt | Select-Object -Last 40
```

### 3c. ESLint (MEU-72b)
```powershell
cd ui; npm run lint *> C:\Temp\zorivest\ui-lint.txt; Get-Content C:\Temp\zorivest\ui-lint.txt | Select-Object -Last 20
```

### 4. PDF Artifact Cleanup Verification
```powershell
rg "pdf_renderer|render_pdf|_render_pdf|pdf_path" packages/ *> C:\Temp\zorivest\pdf-cleanup.txt; Get-Content C:\Temp\zorivest\pdf-cleanup.txt
```
Expected: 0 matches (complete removal confirmed)

### 5. Playwright Dependency Removal
```powershell
rg "playwright" packages/infrastructure/pyproject.toml *> C:\Temp\zorivest\playwright-check.txt; Get-Content C:\Temp\zorivest\playwright-check.txt
```
Expected: 0 matches

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/pipeline_steps/ packages/infrastructure/src/zorivest_infra/email/ packages/infrastructure/src/zorivest_infra/rendering/ ui/src/renderer/src/features/scheduling/ *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt
```
Expected: 0 matches

### 7. E2E Tests — Wave 8 (MEU-72b)
```powershell
cd ui; npx playwright test tests/e2e/email-templates.test.ts --reporter=list *> C:\Temp\zorivest\e2e-templates.txt; Get-Content C:\Temp\zorivest\e2e-templates.txt | Select-Object -Last 30
```
Expected: 3 tests pass (§6K.10)

---

## Open Questions

> [!WARNING]
> **None.** Both build plan sections are fully specified with explicit file lists, code examples, and test assertions.

---

## Research References

- [docs/build-plan/09h-pipeline-markdown-migration.md](file:///p:/zorivest/docs/build-plan/09h-pipeline-markdown-migration.md) — MEU-PW14 spec
- [docs/build-plan/06k-gui-email-templates.md](file:///p:/zorivest/docs/build-plan/06k-gui-email-templates.md) — MEU-72b spec
- [.agent/context/sessions/2026-04-27-known-issues-remediation-proposal.md](file:///p:/zorivest/.agent/context/sessions/2026-04-27-known-issues-remediation-proposal.md) — Originating remediation proposal
- RFC 7763 — `text/markdown` MIME type

---

## Ad-Hoc GUI Hardening (Session 2026-04-28, post-MEU)

> These changes were made as ad-hoc UX improvements during the session, outside the formal MEU scope. All changes are frontend-only and verified with the full Vitest suite (469/469 pass).

### Changes Summary

| # | Change | Files Modified | Verification |
|---|--------|---------------|--------------|
| AH-1 | **MCP execution status indicator**: Lock/unlock icon + "MCP can/cannot execute" text next to state pill based on policy approval state | `PolicyDetail.tsx` | Visual + tsc clean |
| AH-2 | **Template save button fix**: Save button now visible on all non-default templates with dirty-state gating | `EmailTemplateDetail.tsx` | Visual + Vitest green |
| AH-3 | **Template preview rendering**: Preview button wired to `POST /templates/{name}/preview` with rendered HTML in bottom panel | `SchedulingLayout.tsx`, `EmailTemplateDetail.tsx` | Visual |
| AH-4 | **Template name inline pencil-edit**: Template names editable via click-to-edit inline heading (matching PolicyDetail pattern). Rename implemented as create-new + delete-old to preserve backend identifier integrity | `EmailTemplateDetail.tsx`, `SchedulingLayout.tsx` | Vitest green |
| AH-5 | **Unsaved changes navigation guard**: Global dirty-state tracking via `onDirtyChange` callback. Portal-based confirmation modal when navigating between items with unsaved changes | `SchedulingLayout.tsx`, `PolicyDetail.tsx`, `EmailTemplateDetail.tsx` | Vitest green |
| AH-6 | **Portal rendering fix**: Migrated confirmation modals from Tailwind CSS to inline styles with CSS variable fallbacks to fix Electron portal rendering regression | `SchedulingLayout.tsx`, `PolicyDetail.tsx` | Visual + Vitest green |
| AH-7 | **Interactive variable autocomplete dropdown**: Replaced free-text required_variables input with combobox that auto-extracts `{{ var }}` from template body, combines with 20 curated pipeline variables, supports keyboard navigation (Arrow Up/Down/Enter/Escape), shows "in template" badge for detected variables | `EmailTemplateDetail.tsx` | Visual + tsc + Vitest green |
| AH-8 | **Collapsible Run History**: Added +/− toggle icon to Run History header. When collapsed, PolicyDetail fills the full viewport. When expanded, history panel renders with independent scroll | `SchedulingLayout.tsx` | Visual + tsc + Vitest green |
| AH-9 | **Action buttons always visible**: Restructured PolicyDetail/RunHistory flex layout so Save/Test Run/Run Now/Delete buttons never get pushed off-screen by the Run History panel | `SchedulingLayout.tsx` | Visual |
| AH-10 | **Settings nav moved to bottom**: Separated Settings from primary nav items (Accounts, Trades, Planning, Scheduling) and pinned it to the sidebar footer above the Collapse toggle | `NavRail.tsx` | tsc + Vitest green |

### Files Modified (Ad-Hoc)

| File | Changes |
|------|---------|
| `ui/src/renderer/src/features/scheduling/PolicyDetail.tsx` | MCP status indicator, portal inline styles |
| `ui/src/renderer/src/features/scheduling/EmailTemplateDetail.tsx` | Pencil-edit name, save button fix, variable autocomplete dropdown, dirty tracking |
| `ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx` | Tab wiring, dirty guard, portal modal, collapsible run history, layout restructure |
| `ui/src/renderer/src/components/layout/NavRail.tsx` | Settings moved to bottom-pinned section |
| `ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx` | CodeMirror mock fix (updateListener) |
| `ui/src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx` | Updated for pencil-edit, dirty tracking, save button changes |
