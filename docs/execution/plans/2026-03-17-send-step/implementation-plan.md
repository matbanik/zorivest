# MEU-88: SendStep + Async Email Delivery

**Project slug**: `2026-03-17-send-step`
**MEU**: MEU-88 (`send-step`)
**Spec**: [09-scheduling.md §9.8a–c](../../build-plan/09-scheduling.md)
**Dependencies**: MEU-85/86/87 ✅ (pipeline steps), Phase 9 domain ✅

---

## Goal

Implement the final pipeline step type — `SendStep` — which delivers rendered reports via email (aiosmtplib) or local file copy. Includes the async email sender, SHA-256 delivery deduplication (persisted via `ReportDeliveryModel`), and integration with the existing `RegisteredStep` auto-registration pattern.

---

## Spec Sufficiency

| Behavior / Contract | Source | Resolved? |
|---|---|---|
| SendStep `type_name="send"`, `side_effects=True` | Spec §9.8a | ✅ |
| SendStep.Params: channel, recipients (max 5), subject, body_template | Spec §9.8a | ✅ |
| `execute()` dispatches to email or local_file channel | Spec §9.8a | ✅ |
| Returns deliveries list with sent/failed counts | Spec §9.8a | ✅ |
| `send_report_email()`: aiosmtplib, MIME, TLS, PDF attachment | Spec §9.8b | ✅ |
| `compute_dedup_key()`: SHA-256 idempotency | Spec §9.8c | ✅ |
| Report data from prior step context | Local Canon (render_step.py) | ✅ |
| `ReportDeliveryModel` for persistence | Spec §9.2f | ✅ (model exists at `models.py:523`; MEU-88 adds `DeliveryRepository` + UoW exposure) |
| Optional ref-resolved Params fields (report_id, snapshot_hash, pdf_path, html_body) | Local Canon (PipelineRunner §9.3a pattern: `resolved_params` → `Params(**params)`) | ✅ |

---

## Feature Intent Contract (FIC)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-S1 | SendStep auto-registers with `type_name="send"` in `STEP_REGISTRY` | Spec §9.8a |
| AC-S2 | `SendStep.side_effects` is `True` | Spec §9.8a |
| AC-S3 | `SendStep.Params` requires `channel` field | Spec §9.8a |
| AC-S4 | `SendStep.Params.recipients` enforces `max_length=5` | Spec §9.8a |
| AC-S5 | `SendStep.Params.subject` and `body_template` default to empty string | Spec §9.8a |
| AC-S6 | `execute()` returns FAILED for unknown channel | Spec §9.8a |
| AC-S7 | `execute()` dispatches to `_send_emails` for `channel="email"` | Spec §9.8a |
| AC-S8 | `execute()` dispatches to `_save_local` for `channel="local_file"` | Spec §9.8a |
| AC-S9 | `execute()` returns `sent`/`failed` counts in output | Spec §9.8a |
| AC-S10 | `compute_dedup_key` produces deterministic SHA-256 hex string | Spec §9.8c |
| AC-S11 | `compute_dedup_key` changes when any input field changes | Spec §9.8c |
| AC-S12 | `send_report_email` builds correct MIME multipart structure | Spec §9.8b |
| AC-S13 | `send_report_email` attaches PDF when `pdf_path` is provided | Spec §9.8b |
| AC-S14 | `send_report_email` returns `(False, error_msg)` on SMTP failure | Spec §9.8b |
| AC-S15 | `params_schema()` returns non-empty dict | Local Canon |
| AC-S16 | `SendStep._send_emails` checks `DeliveryRepository.get_by_dedup_key()` and skips send if key already exists | Spec §9.8c + §9.2f |
| AC-S17 | `SendStep._send_emails` records `ReportDeliveryModel` row via `DeliveryRepository.create()` after successful send | Spec §9.8c + §9.2f |
| AC-S18 | `DeliveryRepository.get_by_dedup_key()` returns `None` for unknown key and model for known key | Spec §9.2f |
| AC-S19 | `DeliveryRepository.create()` persists row with correct `dedup_key`, `channel`, `recipient`, `status` | Spec §9.2f |
| AC-S20 | `SendStep.Params` accepts optional ref-resolved fields (`report_id`, `snapshot_hash`, `pdf_path`, `html_body`) without validation error | Local Canon (PipelineRunner §9.3a) |

---

## Proposed Changes

### Pipeline Steps (Core Package)

#### [NEW] [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py)

`SendStep(RegisteredStep)` with:
- `type_name = "send"`, `side_effects = True`
- `Params(BaseModel)`: channel, recipients, subject, body_template, report_id (Optional), snapshot_hash (Optional), pdf_path (Optional), html_body (Optional)
- `execute()`: dispatch to `_send_emails()` or `_save_local()`
- `_send_emails()`: iterate recipients, compute dedup key, check `DeliveryRepository` for existing key, skip if found, call email_sender, record `ReportDeliveryModel` row on success
- `_save_local()`: copy rendered output to local path

> [!IMPORTANT]
> **Prior-step output contract**: `SendStep` consumes upstream step outputs via
> ref params in policy JSON, using the standard `RefResolver` contract (§9.3b):
> `{"ref": "ctx.<step_id>.output.<key>"}`. `PipelineRunner` resolves these refs
> into the params dict before calling `execute()`, so the resolved values pass
> through `Params(**params)` validation. Delivery-input fields (`report_id`,
> `snapshot_hash`, `pdf_path`, `html_body`) are declared as `Optional[str]` in
> `Params` to accept ref-resolved values.
> Typical pipeline: `store_report` → `render` → `send`.
> - From `store_report` step: `report_id`, `snapshot_hash`, `report_name`
> - From `render` step: `html`, `pdf_path`

#### [MODIFY] [__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/__init__.py)

Add `from zorivest_core.pipeline_steps import send_step` import for auto-registration.

---

### Email Infrastructure

> [!NOTE]
> **Architecture exception**: Pipeline steps in core may import infra modules
> via `try/except ImportError` for optional integration (PDF rendering,
> field mapping, email sending). This follows the established pattern in
> `render_step.py:144` and `transform_step.py:148`. The import is deferred
> and guarded — core remains usable without infra installed.

#### [NEW] [email/\_\_init\_\_.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/email/__init__.py)

Empty package init.

#### [NEW] [email_sender.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/email/email_sender.py)

`send_report_email()`: async function using `aiosmtplib` with:
- MIME multipart construction (From, To, Subject, Date, HTML body)
- Optional PDF attachment via `MIMEApplication`
- STARTTLS support
- Returns `tuple[bool, str]` (success, message)

#### [NEW] [delivery_tracker.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/email/delivery_tracker.py)

`compute_dedup_key()`: SHA-256 of `"{report_id}|{channel}|{recipient}|{snapshot_hash}"`.

---

### Delivery Persistence (Infrastructure Package)

#### [MODIFY] [scheduling_repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py)

Add `DeliveryRepository` class with:
- `get_by_dedup_key(key: str) -> ReportDeliveryModel | None` — lookup for idempotency check
- `create(*, report_id, channel, recipient, status, dedup_key) -> str` — record successful delivery

Import `ReportDeliveryModel` from `models`.

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Add `deliveries: DeliveryRepository` property to `SqlAlchemyUnitOfWork`.

---

### Configuration

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/infrastructure/pyproject.toml)

Add `aiosmtplib>=3.0` to `[project] dependencies` (alongside `aiolimiter`, `httpx`, etc.).

---

### Tests

#### [NEW] [test_send_step.py](file:///p:/zorivest/tests/unit/test_send_step.py)

20 tests covering AC-S1 through AC-S20. Pattern follows `test_store_render_step.py` with:
- AC-numbered test functions
- Comment banners between tests
- Spec section references in docstring

---

### Post-MEU Deliverables

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- MEU-88 status: ⬜ → ✅
- P2.5 Phase 9 completed: 11 → 12
- Total completed: 76 → 77

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Add MEU-88 row to Phase 9 section.

#### [NEW] [075-2026-03-17-send-step-bp09s9.8.md](file:///p:/zorivest/.agent/context/handoffs/075-2026-03-17-send-step-bp09s9.8.md)

Execution handoff per meu-handoff protocol.

---

## Verification Plan

### Automated Tests

```bash
# Run send-step tests only (fast feedback)
uv run pytest tests/unit/test_send_step.py -v

# Run all pipeline step tests (regression)
uv run pytest tests/unit/test_fetch_step.py tests/unit/test_transform_step.py tests/unit/test_store_render_step.py tests/unit/test_send_step.py -v

# Full regression
uv run pytest tests/ -v

# Type check
uv run pyright packages/core/src/zorivest_core/pipeline_steps/send_step.py packages/infrastructure/src/zorivest_infra/email/ packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Verification Checks

1. `STEP_REGISTRY` contains `"send"` key after import
2. All 20 AC tests pass
3. Full regression green (no breakage to existing steps)
4. Type check clean
5. No `...` or `pass` placeholders in production code (excluding `compensate()` default)
