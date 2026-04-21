# Reflection: Pipeline Data-Flow Hardening (2026-04-21)

> **Project**: `2026-04-21-pipeline-dataflow-hardening`
> **MEUs**: MEU-PW12 (data-flow chain fix), MEU-PW13 (integration tests)
> **Duration**: ~2 hours across 2 sessions

## What Worked

1. **Integration tests as bug detectors**: The PW13 E2E tests immediately surfaced 3 production bugs that unit tests couldn't catch — output loss on WARNING status, extractor slug mismatch, and test fixture incompatibility. This validates the TDD strategy of layering integration tests after unit completion.

2. **Incremental debugging**: Running integration tests one-at-a-time let us isolate failures quickly. Each fix was verified independently before moving on.

3. **Plan-critical-review → corrections cycle**: The plan review caught the boundary validation gap (AC-9) before implementation started, saving rework.

## What Didn't Work

1. **Pre-existing test fixture fragility**: The `_DummyParams` fixture in `test_scheduling_service.py` was a plain class that broke when `policy_validator` started calling `params_cls(**step.params)`. Test fixtures that don't mirror production class interfaces are time bombs.

2. **Slug normalization gap**: The response extractor registry used lowercase provider slugs, but `FetchStep` passed human-readable display names ("Yahoo Finance"). This mismatch was invisible to unit tests because they tested components in isolation.

## Emerging Standards Applied

- **M7**: Presentation mapping is a TransformStep concern — tests assert presentation-friendly field names.
- **G15**: Integration tests mock only infrastructure boundaries (HTTP, DB, SMTP), not inter-step data flow.
- **G19**: Bug fixes start with a failing test before production changes.

## Metrics

| Metric | Value |
|--------|-------|
| Production files changed | 5 |
| Test files changed/created | 6 |
| Unit tests (PW12) | 142 pass |
| Integration tests (PW13) | 7 pass |
| Full suite | 2152 pass, 15 skip, 0 fail |
| Production bugs found by integration tests | 3 |
| Pyright errors | 0 |
| Ruff violations | 0 |
| MEU gate | 8/8 pass |
