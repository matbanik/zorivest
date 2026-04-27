# Phase 6k: GUI — Email Template Management

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [MEU-PH6 ✅](09e-template-database.md), [MEU-72 ⏳](06e-gui-scheduling.md)
> Resolves: [GUI-EMAILTMPL]
> Status: ⬜ planned

---

## Goal

Add an **Email Templates** tab to the Scheduling page for template CRUD. Backend API fully implemented at `/api/v1/scheduling/templates`. This MEU is frontend-only + E2E tests.

---

## 6K.1 Tab Bar (MEU-72b)

Follow [`PlanningLayout.tsx`](file:///p:/zorivest/ui/src/renderer/src/features/planning/PlanningLayout.tsx) pattern:

```typescript
const TABS = ['Report Policies', 'Email Templates'] as const;
```

Active styling: `border-b-2 + text-accent`. Default tab: `Report Policies`.

---

## 6K.2 Layout

List+detail split (same as policy layout). Left: template list with name + `is_default` badge. Right: editor with `body_html` code area, `subject_template`, `description`, `required_variables` chips, `body_format` toggle. Below editor: live preview iframe.

---

## 6K.3 Template Detail Fields

| Field | Widget | API Field | Notes |
|-------|--------|-----------|-------|
| Name | `text` (read-only for defaults) | `name` | `^[a-z0-9][a-z0-9_-]*$` |
| Description | `textarea` | `description` | Optional |
| Format | `select` | `body_format` | `html` or `markdown` |
| Subject | `text` | `subject_template` | Jinja2 template |
| Required Variables | chip list | `required_variables` | Add/remove chips |
| Body | code editor | `body_html` | Syntax-highlighted Jinja2/HTML |

---

## 6K.4 Default Template Protection

- Editor fields **read-only** for `is_default: true`
- Banner: "Default templates cannot be modified. Duplicate to create a custom version."
- Delete button **disabled** (**G2**), Duplicate button enabled

---

## 6K.5 Action Buttons

| Button | Behavior | Guard |
|--------|----------|-------|
| **Save** | `PATCH /templates/{name}` or `POST /templates` | **G1** visible borders |
| **Duplicate** | Creates `{name}-custom` copy | All templates |
| **Delete** | `DELETE /templates/{name}` | **G20** portaled modal, **G15** 403 surfaced |
| **Preview** | `POST /templates/{name}/preview` → `<iframe srcDoc>` | **UX2** always visible, disabled if empty |

**G22**: "New Template" provides valid default body (not empty).

---

## 6K.6 Live Preview

Always visible below editor (**UX2**). Calls `POST /templates/{name}/preview`, renders in sandboxed `<iframe srcDoc>`. Disabled with tooltip when `body_html` empty. Auto-refresh on save.

---

## 6K.7 REST Endpoints (all exist — MEU-PH6 ✅)

`POST /templates`, `GET /templates`, `GET /templates/{name}`, `PATCH /templates/{name}`, `DELETE /templates/{name}`, `POST /templates/{name}/preview`

---

## 6K.8 Standards: G1, G2, G5, G6, G15, G20, G22, UX2

**G5**: `refetchInterval: 5_000` on template list (MCP can create externally).

---

## 6K.9 Test IDs

`scheduling-tab-report-policies`, `scheduling-tab-email-templates`, `template-list`, `template-detail`, `template-preview-btn`, `template-preview-iframe`, `template-new-btn`, `template-save-btn`, `template-duplicate-btn`, `template-delete-btn`, `template-default-badge`

---

## 6K.10 E2E Tests (Wave 8, +3)

| Test | Assertion |
|------|-----------|
| `test_email_templates_tab_accessible` | Tab click → template list visible |
| `test_default_template_readonly` | Default template → editor disabled, banner visible |
| `test_template_preview_renders` | Preview button → iframe contains rendered HTML |

---

## 6K.11 Components

New: `EmailTemplateList.tsx`, `EmailTemplateDetail.tsx`, `EmailTemplatePreview.tsx`
Modified: `SchedulingLayout.tsx` — add tab bar

---

## 6K.12 Exit Criteria

- [ ] Two-tab SchedulingLayout ("Report Policies" + "Email Templates")
- [ ] Template list with `is_default` badge, `refetchInterval: 5_000`
- [ ] Detail editor with all fields, default protection banner
- [ ] Duplicate creates `{name}-custom` copy
- [ ] Delete via themed modal, 403 surfaced for defaults
- [ ] Preview in sandboxed iframe via POST preview endpoint
- [ ] New Template provides valid default body
- [ ] All test IDs assigned, 3 E2E tests pass
