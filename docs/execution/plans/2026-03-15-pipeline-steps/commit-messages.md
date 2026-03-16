# Pipeline Steps — Commit Messages

## Commit 1: Core pipeline steps implementation (MEU-85/86/87)

```
feat(core): implement pipeline steps — fetch, transform, store-report, render

- FetchStep: provider adapter delegation, cache check, per-field criteria resolution
- TransformStep: field mapping, validation gate, quality threshold, db_writer delegation
- StoreReportStep: sandboxed SQL execution, snapshot hashing, report persistence
- RenderStep: Jinja2 template rendering, PDF generation via Playwright
- CriteriaResolver: per-field resolution with static passthrough (relative, incremental, db_query)
- All hooks raise ValueError when required collaborators are missing
- RenderStep returns FAILED when PDF requested but Playwright unavailable

Tests: 64 pipeline step tests (AC-F1..F19, AC-T1..T16, AC-SR1..SR20, AC-CR1)
Gate: pyright clean, ruff clean, 1373 passed / 1 skipped
```

## Commit 2: Closeout artifacts

```
docs(pipeline-steps): add reflection, metrics, commit messages

- Session reflection with key lesson on degraded-behavior testing
- Metrics row for MEU-85/86/87 session
- Commit message templates
- task.md rows 6-9 marked done
```
