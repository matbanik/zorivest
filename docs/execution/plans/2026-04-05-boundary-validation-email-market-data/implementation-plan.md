# Boundary Validation: Email Settings + Market Data (F5+F6)

Harden the remaining orphan write boundaries identified in handoff 096 (findings F5 and F6). These routes have no pending GUI/feature MEU that naturally touches them, so they are addressed as a standalone boundary-validation project.

**Project slug:** `2026-04-05-boundary-validation-email-market-data`
**MEUs:** MEU-BV4 (`boundary-validation-market-data`), MEU-BV5 (`boundary-validation-email`)
**Build plan sections:** bp08s8.4 (market data), bp06fs6f (email settings)
**Pattern reference:** MEU-BV1–BV3 (handoffs 098–100)

---

## User Review Required

> [!IMPORTANT]
> **Email `security` field constraint:** The service code (`email_provider_service.py` L119) checks `if security == "SSL"` and defaults to `"STARTTLS"`. The schema will be constrained to `Literal["STARTTLS", "SSL"]` — matching the spec (`06f-gui-settings.md` L236), the input index (`input-index.md` L430), and the GUI radio control (`EmailSettingsPage.tsx` L167).

> [!IMPORTANT]
> **Email `provider_preset` field constraint:** The spec (`06f-gui-settings.md` L233, L245–250) and the GUI (`EmailSettingsPage.tsx` L22–27) define `provider_preset` as a closed choice set: `Gmail`, `Brevo`, `SendGrid`, `Outlook`, `Yahoo`, `Custom`. The schema will constrain this field to a `Literal` of these 6 values to reject unknown presets at the boundary.

> [!IMPORTANT]
> **Email `password` field:** The `password` field uses `Optional[str] = ""` with "empty = keep existing" semantics. Unlike other string fields, `password` will **NOT** use `StrippedStr` because whitespace-in-passwords is valid. This is an intentional exception to the BV pattern.

> [!IMPORTANT]
> **Market data `ProviderConfigRequest` is partial-update:** All fields are `Optional` — omitted fields are left unchanged. This is correct for the PATCH-like semantics of `PUT /providers/{name}`. No create-path exists, so create/update parity doesn't apply.

---

## Spec Sufficiency

### Boundary Inventory

| Boundary | Route | Schema | Extra-Field Policy | Invalid-Input Error | Create/Update Parity | Source |
|----------|-------|--------|--------------------|---------------------|---------------------|--------|
| F5: Market Data provider config | `PUT /providers/{name}` | `ProviderConfigRequest` | Missing → add `extra="forbid"` | Pydantic 422 | N/A (partial update only) | Spec (08-market-data.md §8.4) |
| F5: Market Data test | `POST /providers/{name}/test` | No body | N/A | N/A | N/A | Spec |
| F5: Market Data remove key | `DELETE /providers/{name}/key` | No body | N/A | N/A | N/A | Spec |
| F6: Email save config | `PUT /settings/email` | `EmailConfigRequest` | Missing → add `extra="forbid"` | Pydantic 422 | N/A (single-row upsert) | Spec (06f-gui-settings.md §Email) |
| F6: Email test connection | `POST /settings/email/test` | No body | N/A | N/A | N/A | Spec |

### Sufficiency Table

| Behavior | Source Type | Source | Resolved? |
|----------|------------|--------|-----------|
| `ProviderConfigRequest` rejects unknown fields | Local Canon | BV pattern (MEU-BV1–BV3 handoffs 098–100) | ✅ |
| `ProviderConfigRequest.rate_limit` must be ≥ 1 | Research-backed | Pydantic `Field(ge=1)` — zero/negative rate limits are nonsensical | ✅ |
| `ProviderConfigRequest.timeout` must be ≥ 1 | Research-backed | Same reasoning | ✅ |
| `ProviderConfigRequest.api_key` rejects whitespace-only | Local Canon | BV pattern `StrippedStr` | ✅ |
| `EmailConfigRequest` rejects unknown fields | Local Canon | BV pattern | ✅ |
| `EmailConfigRequest.port` must be 1–65535 | Research-backed | IANA port range standard | ✅ |
| `EmailConfigRequest.security` constrained to STARTTLS/SSL | Spec + Local Canon | GUI radio: `['STARTTLS', 'SSL']` (L167); spec: `STARTTLS / SSL` (06f L236); input-index: `radio STARTTLS / SSL` (L430) | ✅ |
| `EmailConfigRequest.provider_preset` constrained to 6 known presets | Spec + Local Canon | GUI PRESETS map: `Gmail, Brevo, SendGrid, Outlook, Yahoo, Custom` (L22–27); spec preset table (06f L245–250) | ✅ |
| `EmailConfigRequest.password` keeps empty-string semantics | Spec | `email_settings.py` L48 comment: `"empty = keep existing"` | ✅ |
| `EmailConfigRequest.password` NOT stripped | Research-backed | Passwords may legitimately contain leading/trailing whitespace | ✅ |
| `EmailConfigRequest` string fields use `StrippedStr` (except password) | Local Canon | BV pattern | ✅ |

---

## Proposed Changes

### MEU-BV4: Market Data Provider Config Boundary

#### FIC — Feature Intent Contract

| AC | Description | Source | Test |
|----|-------------|--------|------|
| AC-MD1 | `ProviderConfigRequest` rejects payloads with unknown fields → 422 | Local Canon | `test_extra_field_rejected` |
| AC-MD2 | Whitespace-only `api_key` → 422 (via `StrippedStr` + `min_length=1`) | Local Canon | `test_whitespace_only_api_key_rejected` |
| AC-MD3 | Whitespace-only `api_secret` → 422 | Local Canon | `test_whitespace_only_api_secret_rejected` |
| AC-MD4 | `rate_limit=0` → 422 | Research-backed | `test_zero_rate_limit_rejected` |
| AC-MD5 | `timeout=0` → 422 | Research-backed | `test_zero_timeout_rejected` |
| AC-MD6 | Negative `rate_limit` → 422 | Research-backed | `test_negative_rate_limit_rejected` |
| AC-MD7 | Valid partial payload (only `is_enabled`) still accepted → 200 | Spec (regression guard) | `test_valid_partial_payload_accepted` |

#### [MODIFY] [market_data.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/market_data.py)

- Import `StrippedStr` (define `_strip_whitespace` helper or import from shared module)
- Add `model_config = ConfigDict(extra="forbid")` to `ProviderConfigRequest`
- Change `api_key: Optional[str]` → `Optional[StrippedStr] = Field(None, min_length=1)`
- Change `api_secret: Optional[str]` → `Optional[StrippedStr] = Field(None, min_length=1)`
- Change `rate_limit: Optional[int]` → `Optional[int] = Field(None, ge=1)`
- Change `timeout: Optional[int]` → `Optional[int] = Field(None, ge=1)`
- `is_enabled: Optional[bool] = None` — no change needed

#### [MODIFY] [test_market_data_api.py](file:///p:/zorivest/tests/unit/test_market_data_api.py)

- Add `TestProviderConfigBoundaryValidation` class with 7 negative tests (AC-MD1 through AC-MD7)

---

### MEU-BV5: Email Settings Config Boundary

#### FIC — Feature Intent Contract

| AC | Description | Source | Test |
|----|-------------|--------|------|
| AC-EM1 | `EmailConfigRequest` rejects payloads with unknown fields → 422 | Local Canon | `test_extra_field_rejected` |
| AC-EM2 | Whitespace-only `smtp_host` → 422 | Local Canon | `test_whitespace_only_smtp_host_rejected` |
| AC-EM3 | Whitespace-only `username` → 422 | Local Canon | `test_whitespace_only_username_rejected` |
| AC-EM4 | Unknown `provider_preset` (e.g. `"NotARealPreset"`) → 422 | Spec | `test_unknown_provider_preset_rejected` |
| AC-EM5 | Whitespace-only `from_email` → 422 | Local Canon | `test_whitespace_only_from_email_rejected` |
| AC-EM6 | `port=0` → 422 | Research-backed (IANA) | `test_zero_port_rejected` |
| AC-EM7 | `port=99999` → 422 | Research-backed (IANA) | `test_port_above_65535_rejected` |
| AC-EM8 | `security="INVALID"` → 422 (only `STARTTLS`/`SSL` accepted) | Spec | `test_invalid_security_rejected` |
| AC-EM9 | `password=" "` (whitespace-only) is **accepted** (not stripped) | Research-backed | `test_whitespace_password_accepted` |
| AC-EM10 | Valid full payload still accepted → 200 | Spec (regression guard) | `test_valid_full_payload_accepted` |
| AC-EM11 | Whitespace-only `provider_preset` → 422 (stripped to empty, fails Literal) | Local Canon | `test_whitespace_only_provider_preset_rejected` |

#### [MODIFY] [email_settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/email_settings.py)

- Import `StrippedStr` (define `_strip_whitespace` helper)
- Import `Literal` from typing, `ConfigDict`, `Field` from pydantic
- Add `model_config = ConfigDict(extra="forbid")` to `EmailConfigRequest`
- Change `provider_preset: Optional[str]` → `Optional[Literal["Gmail", "Brevo", "SendGrid", "Outlook", "Yahoo", "Custom"]] = None`
- Change `smtp_host: Optional[str]` → `Optional[StrippedStr] = Field(None, min_length=1)`
- Change `port: Optional[int]` → `Optional[int] = Field(None, ge=1, le=65535)`
- Change `security: Optional[str]` → `Optional[Literal["STARTTLS", "SSL"]] = None`
- Change `username: Optional[str]` → `Optional[StrippedStr] = Field(None, min_length=1)`
- `password: Optional[str] = ""` — **NO CHANGE** (keep-existing semantics, no stripping)
- Change `from_email: Optional[str]` → `Optional[StrippedStr] = Field(None, min_length=1)`

#### [MODIFY] [test_api_email_settings.py](file:///p:/zorivest/tests/unit/test_api_email_settings.py)

- Add `TestEmailConfigBoundaryValidation` class with 11 negative tests (AC-EM1 through AC-EM11)

---

### Post-MEU Tasks

#### `docs/BUILD_PLAN.md` Update

- Remove the `[BOUNDARY-GAP]` F5 warning note added between MEU-65a and the P2 separator
- Remove the `[BOUNDARY-GAP]` F6 note from MEU-73 description
- Add completion evidence for MEU-BV4 and MEU-BV5

#### `known-issues.md` Update

- Update `[BOUNDARY-GAP]` entry: mark F5 and F6 as resolved (Accounts, Trades, Plans already resolved in BV1–BV3; F4 Scheduling, F7 Watchlists, Settings remain open)

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write BV4 negative tests (AC-MD1–MD7) | coder | `test_market_data_api.py` | `pytest tests/unit/test_market_data_api.py -v` — 7 new tests FAIL (Red) | `[ ]` |
| 2 | Harden `ProviderConfigRequest` schema | coder | `market_data.py` | `pytest tests/unit/test_market_data_api.py -v` — all pass (Green) | `[ ]` |
| 3 | Write BV5 negative tests (AC-EM1–EM11) | coder | `test_api_email_settings.py` | `pytest tests/unit/test_api_email_settings.py -v` — 11 new tests FAIL (Red) | `[ ]` |
| 4 | Harden `EmailConfigRequest` schema | coder | `email_settings.py` | `pytest tests/unit/test_api_email_settings.py -v` — all pass (Green) | `[ ]` |
| 5 | Run full regression | tester | Green suite | `uv run pytest tests/ -x --tb=short -v` | `[ ]` |
| 6 | MEU gate | tester | Clean gate | `uv run python tools/validate_codebase.py --scope meu` | `[ ]` |
| 7 | Update `docs/BUILD_PLAN.md` | coder | Remove F5/F6 gap notes | Visual inspection | `[ ]` |
| 8 | Update `known-issues.md` | coder | Mark F5/F6 resolved | Visual inspection | `[ ]` |
| 9 | Regenerate OpenAPI spec | coder | `openapi.committed.json` | `uv run python tools/export_openapi.py --check openapi.committed.json` | `[ ]` |
| 10 | Create handoff 101 (BV4) | coder | `.agent/context/handoffs/101-…` | File exists | `[ ]` |
| 11 | Create handoff 102 (BV5) | coder | `.agent/context/handoffs/102-…` | File exists | `[ ]` |
| 12 | Update MEU registry | coder | `.agent/context/meu-registry.md` | BV4/BV5 rows present | `[ ]` |
| 13 | Reflection + metrics | reviewer | `docs/execution/reflections/` | File exists | `[ ]` |
| 14 | Save session state | coder | `pomera_notes` | Note saved | `[ ]` |

---

## Verification Plan

### Automated Tests

```bash
# Per-MEU targeted tests
uv run pytest tests/unit/test_market_data_api.py -v *> C:\Temp\zorivest\pytest-bv4.txt
uv run pytest tests/unit/test_api_email_settings.py -v *> C:\Temp\zorivest\pytest-bv5.txt

# Full regression
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt

# MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\meu-gate.txt

# OpenAPI spec check
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt
```

### Manual Verification

- Verify `extra="forbid"` rejects unknown fields by inspection
- Verify `password` field remains un-stripped by reviewing AC-EM9 test
- Verify existing happy-path tests still pass (regression guard tests AC-MD7, AC-EM10)

---

## Handoff Files

- `101-2026-04-05-boundary-market-data-bp08s8.4.md`
- `102-2026-04-05-boundary-email-bp06fs6f.md`
