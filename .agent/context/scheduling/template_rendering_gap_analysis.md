# Template Rendering Gap Analysis

## The Problem

The email body shows `daily_quote_summary` as literal text because `SendStep._send_emails()` never resolves the `body_template` name against the Jinja2 template registry. The rendering pipeline has **three disconnected layers** that were never wired together.

## Architecture Trace

```
Policy JSON
  └─ send step params: { body_template: "daily_quote_summary", html_body: {"ref": "ctx.render.html"} }
      │
      ├─ RefResolver resolves {"ref": ...} → actual value from prior step output
      │   BUT: if no render step ran (or it failed), html_body stays None
      │
      └─ SendStep._send_emails() line 151-153:
            html_body = params.html_body or params.body_template or "<p>Report attached</p>"
            │
            ├─ html_body is None (no render step / render failed)
            ├─ body_template = "daily_quote_summary" (the STRING, not rendered HTML)  ← BUG
            └─ Result: literal "daily_quote_summary" sent as email body
```

## What Exists (3 disconnected layers)

### Layer 1: Template Registry ✅ Exists, 0 tests
- **File:** `zorivest_infra/rendering/email_templates.py`
- **Content:** `EMAIL_TEMPLATES` dict with `daily_quote_summary` and `generic_report` — beautiful, well-styled Jinja2 HTML templates
- **Tests:** **ZERO** — no test imports or references this module

### Layer 2: Template Engine ✅ Exists, 2 tests
- **File:** `zorivest_infra/rendering/template_engine.py`
- **Content:** `create_template_engine()` → Jinja2 `Environment` with `currency`/`percent` filters
- **Tests:** `test_store_render_step.py` tests `AC-SR8` (filters registered) and `AC-SR17b` (render step uses engine)
- **Gap:** Uses `BaseLoader()` (no filesystem templates) — only `from_string()` works, no `get_template()` by name

### Layer 3: SendStep body resolution ❌ No template lookup
- **File:** `send_step.py` line 151-153
- **Logic:** `html_body = params.html_body or params.body_template or default`
- **Problem:** `body_template` is used as **raw text fallback**, not as a template name lookup
- **Missing:** No call to `EMAIL_TEMPLATES.get(body_template)`, no Jinja2 render, no context injection

## The Wiring Gap

```
EMAIL_TEMPLATES["daily_quote_summary"]  ←── Never queried by SendStep
                                             SendStep doesn't import it
                                             SendStep doesn't know it exists

template_engine (Jinja2 Environment)    ←── Available in context.outputs["template_engine"]
                                             SendStep never reads it
                                             RenderStep uses it, but only for report rendering

body_template = "daily_quote_summary"   ←── Used as literal string, not template key
```

## Test Coverage Gaps

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|-----------|-------------------|-----------|
| `EMAIL_TEMPLATES` registry | ❌ None | ❌ None | ❌ None |
| `body_template` → registry lookup | ❌ None | ❌ None | ❌ None |
| Template rendering with context data | ❌ None | ❌ None | ❌ None |
| Rendered HTML → SMTP handoff | ❌ None | ❌ None | ❌ None |
| `create_template_engine()` filters | ✅ 1 test | ❌ None | ❌ None |
| RenderStep uses template_engine | ✅ 1 test | ❌ None | ❌ None |
| SMTP credential passthrough | ✅ 3 tests | ✅ 1 test | ❌ None |
| Dedup key computation | ✅ 4 tests | ❌ None | ❌ None |

## Required Fix

`SendStep._send_emails()` must:

1. Check if `body_template` is a known template name in `EMAIL_TEMPLATES`
2. If found, render it via `template_engine.from_string(template_source)` with pipeline context data
3. Use the rendered HTML as `html_body`
4. Fall back to raw `body_template` string only if template not found AND no `html_body`

### Context data for template variables

Templates expect variables like `quotes`, `generated_at`, `title`, `records`. These come from:
- `context.outputs` — populated by prior pipeline steps (fetch_data, transform, etc.)
- Step output data flows through `context.outputs[step_id]` after each step completes

## Test Plan (TDD)

1. `test_body_template_resolves_from_registry` — verify `daily_quote_summary` produces HTML, not raw string
2. `test_template_rendered_with_context_data` — verify template variables (`quotes`, `generated_at`) are injected
3. `test_unknown_template_falls_back_to_raw` — unknown template name used as literal text
4. `test_html_body_still_takes_precedence` — existing test, html_body overrides template
5. `test_template_render_error_falls_back_gracefully` — bad template data doesn't crash delivery
