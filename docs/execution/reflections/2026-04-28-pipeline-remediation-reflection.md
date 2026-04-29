# Reflection: Pipeline Markdown Migration + Email Templates GUI

> **Project**: `2026-04-28-pipeline-remediation`
> **Date**: 2026-04-28
> **MEUs**: MEU-PW14, MEU-72b

## Summary

Two complementary hardening tasks completed in a single session:

1. **MEU-PW14** — Removed PDF rendering from the pipeline, replacing it with Markdown output. Deleted `pdf_renderer.py`, removed Playwright dependency, renamed `pdf_path` → `attachment_path` through the send chain, and updated defaults. 8 FIC tests, all passing.

2. **MEU-72b** — Added an "Email Templates" tab to SchedulingLayout with full template CRUD, default protection, and sandboxed preview. Created 6 new TypeScript files (API, hooks, 3 components, 1 test file) plus 3 E2E test stubs. 33 Vitest tests, all passing. Zero regressions across the full 464-test UI suite.

## Key Design Decisions

1. **Tab-based navigation** (not route-based): Used conditional rendering within SchedulingLayout to switch between "Report Policies" and "Email Templates" tabs. This avoids adding new routes and keeps the feature contained within the scheduling page.

2. **Default template protection**: Read-only banner + disabled Save/Delete buttons for `is_default` templates. Duplicate remains enabled to allow creating custom copies.

3. **Sandboxed iframe for preview**: Uses `<iframe srcDoc={html} sandbox="" />` to prevent script execution in rendered templates.

4. **Generic MIME attachment** (PW14): Changed from `application/pdf` to `mimetypes.guess_type()` to support `.md`, `.html`, and any future format.

## Instruction Coverage

```yaml
schema: v1
session:
  id: b7b50ac7-470f-43e2-ad7b-355220f25d02
  task_class: tdd+adhoc
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 12
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 3
  - id: planning_contract
    cited: true
    influence: 2
  - id: session_discipline
    cited: true
    influence: 2
  - id: operating_model
    cited: true
    influence: 2
loaded:
  workflows: [create_plan, plan_corrections, tdd_implementation, execution_corrections]
  roles: [coder, tester, reviewer]
  skills: [terminal_preflight, quality_gate]
  refs:
    - docs/build-plan/09h-pipeline-markdown-migration.md
    - docs/build-plan/06k-gui-email-templates.md
    - .agent/context/sessions/2026-04-27-known-issues-remediation-proposal.md
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:never-modify-tests-to-pass"
  - "P1:fic-before-code"
  - "P0:redirect-to-file-pattern"
  - "P1:anti-premature-stop"
conflicts: []
note: >
  Clean two-MEU session + 10 ad-hoc GUI UX improvements. PW14 was mechanical;
  72b required creativity for tab layout. Ad-hoc work addressed user-reported
  issues (save button, preview, portal rendering) and proactive UX hardening
  (variable dropdown, collapsible history, nav restructure). All 469 Vitest
  tests green throughout.
```

## Ad-Hoc GUI Hardening (post-MEU)

Following MEU completion, 10 additional GUI improvements were made in response to user feedback and proactive UX refinement:

| # | Change | Key Decision |
|---|--------|-------------|
| AH-1 | MCP execution status indicator | Lock/unlock icon next to state pill reflects approval status |
| AH-2 | Template save button fix | Save visible for all non-default templates, gated on dirty state |
| AH-3 | Template preview rendering | Wired to existing `POST /templates/{name}/preview` endpoint |
| AH-4 | Template name inline pencil-edit | Rename = create-new + delete-old (backend uses name as identifier) |
| AH-5 | Unsaved changes navigation guard | Portal confirmation modal prevents accidental data loss |
| AH-6 | Portal rendering fix | Inline styles with CSS variable fallbacks for Electron compatibility |
| AH-7 | Interactive variable autocomplete | Regex-extracts `{{ var }}` from template body + 20 curated suggestions with keyboard nav |
| AH-8 | Collapsible Run History | +/− toggle lets policy editor fill viewport when history not needed |
| AH-9 | Action buttons always visible | Flex layout restructure prevents buttons from being pushed off-screen |
| AH-10 | Settings nav moved to bottom | Pinned above Collapse toggle, separated from primary nav items |

**Files touched (ad-hoc):** `PolicyDetail.tsx`, `EmailTemplateDetail.tsx`, `SchedulingLayout.tsx`, `NavRail.tsx`, `scheduling.test.tsx`, `email-templates.test.tsx`

**Test results:** 469/469 Vitest pass, 29/29 test files pass. Zero regressions.
