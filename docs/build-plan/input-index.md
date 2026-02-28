# Input Index — Complete Input Catalog

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Sources: [Domain Model Ref](domain-model-reference.md), [Build Priority Matrix](build-priority-matrix.md)
> Companion indexes: [Output Index](output-index.md) · [GUI Actions Index](gui-actions-index.md)

Canonical registry of **every input** the system accepts — human-entered, agent-invoked, and programmatically triggered. Each row links to the build plan file(s) that define its contract.

---

## Legend

| Column | Meaning |
|--------|---------|
| **Surface** | 🖥️ GUI (React form) · 🤖 MCP (IDE agent tool) · 🔌 API (REST endpoint) · ⏰ Scheduled (cron/timer) · 🔗 Programmatic (auto-import, event-driven) |
| **Status** | ✅ Defined (full surface contract — route/tool/component in phase docs) · 🔶 Domain modeled (entity in Phase 1/2, no REST/MCP/GUI contract yet) · 📋 Planned (in priority matrix, routes/tools not yet specified) |
| **Plan Files** | Which build plan doc(s) define the contract |

---

## 1. Position Calculator

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 1.1 | `balance` | `number` | Account buying power | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 1.2 | `risk_pct` | `number` | Percentage of balance to risk (default 1.0) | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [05](05-mcp-server.md) |
| 1.3 | `entry` | `number` | Entry price | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [05](05-mcp-server.md) |
| 1.4 | `stop` | `number` | Stop-loss price | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [05](05-mcp-server.md) |
| 1.5 | `target` | `number` | Target price | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [05](05-mcp-server.md) |

> **📋 Planned:** Account-aware calculator (`account_id` → auto-resolve balance) is a future enhancement not yet in domain/MCP contracts.

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Happy path | balance=10000, risk=1%, entry=100, stop=95, target=110 | shares=20, risk_amount=100, reward_ratio=2.0 |
| Zero risk | risk_pct=0 | Validation error: risk must be > 0 |
| Entry equals stop | entry=100, stop=100 | Validation error: division by zero prevented |

---

## 2. Trade Logging

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 2.1 | `exec_id` | `string` | Execution ID (auto from IBKR or manual) | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.2 | `instrument` | `string` | e.g. "SPY STK" | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.3 | `action` | `enum` | `BOT` / `SLD` | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.4 | `quantity` | `number` | Number of shares/contracts | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.5 | `price` | `number` | Execution price | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.6 | `account_id` | `string` | FK → Account | 🖥️🤖🔌🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [05](05-mcp-server.md) |
| 2.7 | `commission` | `number` | Optional (auto from IBKR) | 🖥️🔌🔗 | ✅ | [04](04-rest-api.md) |
| 2.8 | `realized_pnl` | `number` | Optional (auto from IBKR) | 🖥️🔌🔗 | ✅ | [04](04-rest-api.md) |
| 2.9 | `notes` | `string` | Optional free text | 🖥️🔌 | ✅ | [04](04-rest-api.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create trade | Valid CreateTradeRequest | 201 + `exec_id` echoed |
| Deduplication | Same `exec_id` twice | `409 Conflict` with existing `exec_id` |
| Missing account | account_id="INVALID" | 422 or business error |
| IBKR auto-import | 🔗 Batch of FlexQuery records | Each record → `create_trade`, deduped |
| Update trade | PUT with new notes | 200 + updated record |
| Delete trade | DELETE /{exec_id} | 204 No Content |

---

## 3. Screenshot / Image Attachment

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 3.1 | `file` | `UploadFile` | Image binary (file picker, paste, drag-drop) | 🖥️🔌 | ✅ | [04](04-rest-api.md) |
| 3.2 | `image_base64` | `string` | Base64-encoded image (MCP-only) | 🤖 | ✅ | [05](05-mcp-server.md) |
| 3.3 | `caption` | `string` | Image caption (default empty) | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 3.4 | `owner_type` | `string` | Service-internal: `"trade"` / `"report"` / `"plan"` | — | ✅ | [01](01-domain-layer.md) |
| 3.5 | `owner_id` | `string` | Service-internal: resolved from route path (e.g. `/trades/{exec_id}/images`) | — | ✅ | [01](01-domain-layer.md) |
| 3.6 | `mime_type` | `string` | MIME type (auto-detected from file; all images standardized to WebP on ingestion, default `image/webp`) | 🤖🔌 | ✅ | [05](05-mcp-server.md) |

> **Note:** `owner_type`/`owner_id` are service-layer parameters, not API-consumer inputs. Current REST surface is trade-scoped: `POST /trades/{exec_id}/images`.

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Upload valid PNG | POST multipart with PNG file | 200 + `image_id` |
| Upload to missing trade | owner_id="NONEXIST" | 404 TradeNotFoundError |
| MCP base64 attach | base64 string + caption | Decoded → multipart → 200 |
| Get thumbnail | GET /images/{id}/thumbnail?max_size=200 | 200 + `image/webp` bytes |
| Oversized file | >10MB image | 413 Payload Too Large |

---

## 4. Trade Report (Post-Trade Journal)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 4.1 | `trade_id` | `string` | Links to a specific trade | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.2 | `setup_quality` | `int` | 1–5 star rating | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.3 | `execution_quality` | `int` | 1–5 star rating | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.4 | `followed_plan` | `bool` | Plan adherence flag | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.5 | `emotional_state` | `string` | Free text or dropdown | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.6 | `lessons_learned` | `text` | Free-form reflection | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.7 | `tags` | `string[]` | e.g. ["momentum", "reversal"] | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 4.8 | `screenshots` | `file[]` | Review-specific screenshots | 🖥️🔌 | ✅ | [01](01-domain-layer.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create report | All fields valid | Report created with ID |
| Rating bounds | setup_quality=0 or 6 | Validation error: 1–5 only |
| Missing trade | trade_id="GONE" | 404 error |
| Tags roundtrip | tags=["a","b"] | GET returns same array |

---

## 5. Trade Plan

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 5.1 | `ticker` | `string` | From watchlist or typed | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.2 | `direction` | `enum` | `BOT` / `SLD` | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.3 | `conviction` | `enum` | LOW / MEDIUM / HIGH / MAX | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.4 | `strategy_name` | `string` | e.g. "Gap & Go" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.5 | `strategy_description` | `text` | Rich text reasoning (the thesis) | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.6 | `entry_price` | `number` | Planned entry | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.7 | `stop_loss` | `number` | Risk boundary | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.8 | `target_price` | `number` | Profit target | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.9 | `entry_conditions` | `text` | Technical triggers | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.10 | `exit_conditions` | `text` | Close conditions | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.11 | `timeframe` | `string` | "intraday", "swing 2-5 days" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.12 | `account_id` | `string` | Optional account association | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |
| 5.13 | `chart_screenshots` | `file[]` | Annotated chart images | 🖥️🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06c](06c-gui-planning.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create plan | All required fields | Plan created with ID & DRAFT status |
| Status transition | ACTIVE → EXECUTED | Status updated |
| Invalid conviction | conviction="EXTREME" | Validation error |
| Populate from watchlist | ticker from existing watchlist item | Pre-fills available data |

---

## 6. Watchlist Management

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 6.1 | `name` (watchlist) | `string` | e.g. "Momentum Plays" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [02](02-infrastructure.md), [06c](06c-gui-planning.md) |
| 6.2 | `description` | `string` | Purpose of the list | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 6.3 | `ticker` (item) | `string` | e.g. "AAPL" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [02](02-infrastructure.md), [06c](06c-gui-planning.md) |
| 6.4 | `notes` (item) | `text` | Why watching this ticker | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [02](02-infrastructure.md), [06c](06c-gui-planning.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create watchlist | name="Test List" | Watchlist created with ID |
| Add item | ticker="AAPL", notes="earnings play" | Item added with `added_at` |
| Duplicate ticker | Same ticker to same list | Error or idempotent |
| Delete watchlist | delete watchlist with items | Cascade deletes items |
| Bulk add | comma-separated "AAPL,MSFT,GOOG" | 3 items created |

---

## 7. Account CRUD

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 7.1 | `account_id` | `string` | User-defined identifier | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [02](02-infrastructure.md) |
| 7.2 | `name` | `string` | Display name | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [02](02-infrastructure.md) |
| 7.3 | `account_type` | `enum` | BROKER / BANK / REVOLVING / INSTALLMENT / IRA / K401 | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 7.4 | `institution` | `string` | e.g. "Interactive Brokers" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md) |
| 7.5 | `currency` | `string` | Default "USD" | 🖥️🔌 | ✅ | [01](01-domain-layer.md) |
| 7.6 | `is_tax_advantaged` | `bool` | Auto from type but overridable | 🖥️🔌 | ✅ | [01](01-domain-layer.md) |
| 7.7 | `notes` | `text` | Free-form notes | 🖥️🔌 | ✅ | [01](01-domain-layer.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create account | All fields valid | Account created |
| IRA auto-flag | account_type=IRA | `is_tax_advantaged` defaults to true |
| Duplicate ID | Same `account_id` twice | Conflict error |

---

## 8. Account Review (Balance Update Wizard)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 8.1 | `update_method` | `choice` | API fetch / Manual entry (per account) | 🖥️🤖 | ✅ | [06d](06d-gui-accounts.md) |
| 8.2 | `new_balance` | `number` | Manual balance entry (pre-filled from last) | 🖥️🤖 | ✅ | [06d](06d-gui-accounts.md) |
| 8.3 | Skip / Update | `action` | Per-account decision | 🖥️🤖 | ✅ | [06d](06d-gui-accounts.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Manual update | new_balance=50000 | Account balance snapshot saved |
| Skip account | Skip action | Balance unchanged, next account shown |
| API fetch | update_method=API | Triggers broker API call, stores balance |

---

## 9. Display Mode Toggles

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 9.1 | `hide_dollars` | `bool` | Toggle $ display (privacy mode) | 🖥️🤖🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 9.2 | `hide_percentages` | `bool` | Toggle % display (privacy mode) | 🖥️🤖🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 9.3 | `percent_mode` | `string` | Percentage display mode (daily/total) | 🖥️🤖🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Toggle dollar off | hide_dollars=true | Setting persisted |
| Roundtrip | Set all three → GET | Values match |
| Session persistence | Set → restart → GET | Values survive restart |

---

## 9a. UI & Notification Settings

> Settings persisted via the `SettingModel` key-value store (see [Phase 2](02-infrastructure.md)). Accessed via `GET/PUT /api/v1/settings` (see [04d-api-settings.md](04d-api-settings.md)) and `get_settings`/`update_settings` MCP tools (see [Phase 5 §5.5](05-mcp-server.md)).

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 9a.1 | `ui.*` settings | `string` | Theme, active page, sidebar width, panel collapse states (namespaced dot notation) | 🖥️🤖🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06a](06a-gui-shell.md) |
| 9a.2 | `notification.*.enabled` | `string` | Per-category notification suppression (success, info, warning, confirmation; error is locked) | 🖥️🤖🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [05](05-mcp-server.md), [06a](06a-gui-shell.md) |

> **Convention**: All setting values are strings at the API/MCP boundary. Consumers parse to native types.

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Set theme | PUT `{"ui.theme": "dark"}` | Setting persisted |
| Suppress info | PUT `{"notification.info.enabled": "false"}` | Info toasts suppressed |
| Error locked | PUT `{"notification.error.enabled": "false"}` | Ignored — errors always show |
| Roundtrip | PUT → GET all | All values match |

---

## 10. Tax Profile (Settings)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 10.1 | `filing_status` | `enum` | SINGLE / MARRIED_JOINT / MARRIED_SEPARATE / HEAD_OF_HOUSEHOLD | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.2 | `tax_year` | `int` | e.g. 2026 | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.3 | `federal_bracket` | `float` | Marginal rate, e.g. 0.37 | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.4 | `state_tax_rate` | `float` | e.g. 0.05 | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.5 | `state` | `string` | e.g. "NY", "TX" | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.6 | `prior_year_tax` | `decimal` | For safe harbor calculation | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.7 | `agi_estimate` | `decimal` | For NIIT threshold check | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.8 | `capital_loss_carryforward` | `decimal` | From prior year | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.9 | `wash_sale_method` | `enum` | CONSERVATIVE / AGGRESSIVE | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.10 | `default_cost_basis` | `enum` | FIFO / LIFO / HIFO / SPEC_ID / etc. | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.11 | `include_drip_wash_detection` | `bool` | DRIP wash sale detection (default true) | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.12 | `include_spousal_accounts` | `bool` | Include spousal accounts (default false) | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.13 | `section_475_elected` | `bool` | Mark-to-Market election | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 10.14 | `section_1256_eligible` | `bool` | Futures 60/40 treatment | 🖥️🤖🔌 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md), [06g](06g-gui-tax.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Save full profile | All fields valid | Profile persisted in settings table |
| Invalid bracket | federal_bracket=1.5 | Validation: must be 0.0–1.0 |
| Roundtrip | Save → GET | All values match |
| Sections exclusivity | Both 475 and 1256 true | Warning: unusual combination |

---

## 11. Tax "What-If" Simulator

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 11.1 | `ticker` | `string` | What to sell | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 11.2 | `quantity` | `number` | How many shares | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 11.3 | `lot_selection_method` | `enum` | Cost basis method to simulate | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| FIFO simulation | ticker="SPY", qty=50, method=FIFO | Estimated tax breakdown |
| No position | ticker="NONE" | Error: no open position |
| Compare methods | Same sale, FIFO vs HIFO | Different tax amounts |

---

## 12. Lot Matcher (Specific Lot Close)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 12.1 | `ticker` | `string` | Position to close | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 12.2 | `lot_ids` | `string[]` | Specific lot IDs selected | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Close specific lots | lot_ids=[1, 3] | Lots marked closed |
| Invalid lot ID | lot_ids=[999] | Error: lot not found |
| Mixed lots | Lots from different accounts | Error or grouped result |

---

## 13. Quarterly Estimated Tax

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 13.1 | `quarter` | `int` | 1–4 | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 13.2 | `actual_payment` | `decimal` | Amount actually paid | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |
| 13.3 | `estimation_method` | `enum` | safe_harbor_100 / 110 / current_year_90 / annualized | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06g](06g-gui-tax.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Estimate Q1 | quarter=1, method=safe_harbor_100 | Amount owed + due date |
| Out-of-range | quarter=5 | Validation error |
| Underpayment | Payment < required | Penalty accrual calculated |

---

## 14. Database Passphrase & API Key Auth (Security)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 14.1 | `passphrase` | `password` | SQLCipher key derivation (Argon2id) — GUI unlock | 🖥️ | ✅ | [02](02-infrastructure.md) |
| 14.2 | `api_key` | `password` | Envelope encryption unlock — MCP auth | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Correct passphrase | Valid password | DB unlocked, app starts |
| Wrong passphrase | Invalid password | Decryption error, retry prompt |
| Empty passphrase | "" | Validation error |
| Valid API key | zrv_sk_... via POST /auth/unlock | 200 + session_token + role |
| Invalid API key | Wrong key | 401 Unauthorized |
| Revoked API key | Revoked key | 403 Forbidden |
| Key management | POST /auth/keys | New key generated (admin only) |
| Key revocation | DELETE /auth/keys/{id} | Key removed, wrapped DEK deleted |

> **Dual-access architecture:** GUI uses passphrase → KDF → DEK directly. MCP uses API key → envelope encryption (KEK unwraps DEK) via `POST /api/v1/auth/unlock`. See [04c-api-auth.md](04c-api-auth.md) and [Phase 5 §5.7](05-mcp-server.md).

---

## 15. API Credential Management

### 15a. OAuth Token Connections

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 15a.1 | `provider` | `dropdown` | E*Trade, Coinbase, PayPal, Plaid, etc. | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 15a.2 | Connect / Disconnect | `action` | Launch OAuth flow or revoke | 🖥️ | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 15a.3 | `auto_refresh` | `bool` | Auto-refresh before expiry | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |

### 15b. Static API Key Credentials

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 15b.1 | `provider` | `dropdown` | IBKR, TradingView, etc. | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 15b.2 | `api_key` | `string` | API key / Client ID | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 15b.3 | `secret` | `password` | Fernet-encrypted at rest | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 15b.4 | Test connection | `action` | Verify credentials | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### 15b-market. Market Data API Keys (12 Providers)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 15m.1 | `provider_name` | `dropdown` | Pre-populated from 12-provider registry | 🖥️🤖🔌 | ✅ | [08](08-market-data.md) |
| 15m.2 | `api_key` | `password` | Fernet-encrypted (`ENC:` prefix) | 🖥️🔌 | ✅ | [08](08-market-data.md), [02](02-infrastructure.md) |
| 15m.3 | `rate_limit` | `number` | Requests per minute | 🖥️🔌 | ✅ | [08](08-market-data.md) |
| 15m.4 | `timeout` | `number` | Seconds (default 30) | 🖥️🔌 | ✅ | [08](08-market-data.md) |
| 15m.5 | `is_enabled` | `bool` | Toggle provider | 🖥️🔌 | ✅ | [08](08-market-data.md) |
| 15m.6 | Test connection | `action` | Lightweight provider test | 🖥️🤖🔌 | ✅ | [08](08-market-data.md) |
| 15m.7 | Remove API key | `action` | Delete key and disable provider | 🖥️🤖🔌 | ✅ | [08](08-market-data.md) |

### Test Strategy (Credentials)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Configure provider | PUT /providers/{name} with api_key | Key encrypted + stored |
| Test connection | POST /providers/{name}/test | success: true/false + message |
| Remove key | DELETE /providers/{name}/key | Key cleared |
| List providers | GET /providers | All 9 with status indicators |
| Invalid key | Key that fails auth | success=false, message explains |

> **Security:** Key entry is GUI-only. MCP can list, test, disconnect — never set keys.

---

## 15d. Market Data Queries (Consumer Surface)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 15d.1 | `ticker` | `string` | Stock symbol or company name | 🖥️🤖🔌 | ✅ | [08](08-market-data.md) |
| 15d.2 | `count` (news) | `number` | Number of articles (default 5) | 🤖🔌 | ✅ | [08](08-market-data.md) |
| 15d.3 | `query` (search) | `string` | Company name or partial ticker | 🤖🔌 | ✅ | [08](08-market-data.md) |

> **📋 Planned:** `provider_preference` (select a specific provider vs auto-routing) is not yet exposed by REST or MCP contracts.

### Test Strategy (Market Queries)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Get quote | ticker="AAPL" | MarketQuote with price, volume, change |
| Search ticker | query="apple" | List of TickerSearchResult |
| Get news | ticker="SPY", count=3 | 3 MarketNewsItem objects |
| SEC filings | ticker="TSLA" | List of SEC filing records |
| No enabled providers | All disabled | Error: no providers available |
| Provider fallback | Primary 429 → secondary | Auto-routes to next provider |

---

## 16. Email Provider Configuration

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 16.1 | `provider_preset` | `dropdown` | Gmail, Brevo, SendGrid, etc. | 🖥️🤖🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.2 | `smtp_host` | `string` | Auto-filled from preset | 🖥️🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.3 | `port` | `number` | Default 587 | 🖥️🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.4 | `security` | `radio` | STARTTLS / SSL | 🖥️🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.5 | `username` | `string` | Provider-specific | 🖥️🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.6 | `password` | `password` | Fernet-encrypted at rest | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [06f](06f-gui-settings.md) |
| 16.7 | `from_email` | `string` | Sender address | 🖥️🔌 | ✅ | [06f](06f-gui-settings.md) |
| 16.8 | Test & Save | `action` | Sends test email | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Gmail preset | provider_preset="Gmail" | Auto-fills smtp.gmail.com:587:STARTTLS |
| Test connection | Valid SMTP creds | Test email sent, success response |
| Invalid password | Wrong SMTP password | Error with provider-specific message |

---

## 17. Schedule Management

> **⛔ Superseded by Section 17a (Pipeline Policy Authoring).** The inputs below represent the legacy schedule model. Phase 9 replaces them with policy-driven scheduling. Field migration map:
>
> | Section 17 (Legacy) | Section 17a (Phase 9 Equivalent) |
> |---|---|
> | 17.1 `schedule_name` | 17a.1 `policy_json.name` |
> | 17.2 `pipeline_type` | 17a.2 `policy_json.steps[].type` |
> | 17.3 `cron_expression` | 17a.3 `policy_json.trigger.cron_expression` |
> | 17.4 `timezone` | 17a.3 `policy_json.trigger.timezone` |
> | 17.5 `recipients` | 17a.2 Send step `params.recipients` |
> | 17.6 `enabled` | 17a.3 `policy_json.trigger.enabled` |
> | 17.7 `skip_if_running` | 17a.3 `policy_json.trigger.max_instances=1` |
> | 17.8 `misfire_grace` | 17a.3 `policy_json.trigger.misfire_grace_time` |
> | 17.9 Run Now | 17a.5 `run_pipeline` MCP tool / `POST /policies/{id}/run` |

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 17.1 | `schedule_name` | `string` | e.g. "Daily Performance Report" | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.2 | `pipeline_type` | `dropdown` | `daily_report` / `data_refresh` / custom | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.3 | `cron_expression` | `string` | 5-field cron (e.g. `0 8 * * *`) | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.4 | `timezone` | `dropdown` | Default UTC | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.5 | `recipients` | `string[]` | Email addresses | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.6 | `enabled` | `bool` | Active / paused toggle | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |
| 17.7 | `skip_if_running` | `bool` | Prevent overlapping runs | 🖥️🔌 | ⛔ | [09](09-scheduling.md) |
| 17.8 | `misfire_grace` | `number` | Seconds (default 3600) | 🖥️🔌 | ⛔ | [09](09-scheduling.md) |
| 17.9 | Run Now | `action` | Trigger immediate execution | 🖥️🤖🔌 | ⛔ | [09](09-scheduling.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------
| Create schedule | Valid cron + recipients | Schedule created, next run calculated |
| Invalid cron | "* * *" (3 fields) | Validation error |
| Run Now | Trigger pipeline | Pipeline execution started |
| Disable schedule | enabled=false | Next run nullified |
| Misfire recovery | Missed run within grace period | Late execution triggered |

---

## 17a. Pipeline Policy Authoring (Phase 9 — Scheduling)

> Policy documents define scheduled data pipelines (fetch → transform → store → render → send).
> Domain: [`PolicyDocument`](09-scheduling.md) | REST: [§9.10](09-scheduling.md) | MCP: [§9.11](09-scheduling.md) | GUI: [§9.12](09-scheduling.md)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 17a.1 | Policy JSON document | `json` | Full PolicyDocument with steps, trigger, retry config | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |
| 17a.2 | Cron expression | `string` | 5-field cron for scheduling (e.g. `0 7 * * 1-5`) | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |
| 17a.3 | Timezone | `string` | IANA timezone for schedule (e.g. `America/New_York`) | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |
| 17a.4 | Enable/disable toggle | `bool` | Enable or disable a policy's schedule | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |
| 17a.5 | Dry-run flag | `bool` | Skip steps with side effects during execution | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |
| 17a.6 | Policy approval | `action` | Approve a policy for execution (human-in-the-loop) | 🖥️ | ✅ | [09](09-scheduling.md) |
| 17a.7 | Manual run trigger | `action` | Trigger a pipeline run immediately | 🖥️🤖🔌 | ✅ | [09](09-scheduling.md) |

---

## 18. Programmatic / Scheduled Inputs (No Direct Human Entry)

These inputs are triggered automatically by the system, IDE agent calls, or scheduled jobs rather than user-initiated forms.

| # | Trigger | Input | Type | Description | Surface | Status | Plan Files |
|---|---------|-------|------|-------------|---------|--------|------------|
| 18.1 | IBKR FlexQuery Import | Trade execution records | `batch` | Bulk trade import from IBKR FlexQuery XML/CSV | ⏰🔗 | ✅ | [01](01-domain-layer.md), [04](04-rest-api.md) |
| 18.2 | IBKR TWS Live Feed | Execution / position events | `event` | Real-time trade capture from TWS API socket | 🔗 | ✅ | [01](01-domain-layer.md) |
| 18.3 | Scheduled Data Refresh | Market data cache refresh | `cron` | Periodic refresh of quotes/news for watchlist tickers | ⏰ | ✅ | [08](08-market-data.md) |
| 18.4 | Scheduled Report Pipeline | Report generation + email | `cron` | Fetches data → processes → renders → sends email | ⏰ | ✅ | [09](09-scheduling.md) |
| 18.5 | Plaid Webhook | Account balance update | `webhook` | Plaid sends balance/transaction updates | 🔗 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 18.6 | OAuth Token Refresh | Token renewal | `timer` | Background refresh before token expiry | 🔗 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 18.7 | Agent Quote Lookup | `get_stock_quote` via MCP | `agent_call` | IDE agent queries a ticker price on behalf of user | 🤖 | ✅ | [08](08-market-data.md), [05](05-mcp-server.md) |
| 18.8 | Agent Tax Simulation | `simulate_tax_impact` via MCP | `agent_call` | IDE agent runs tax what-if during chat | 🤖 | ✅ | [05h](05h-mcp-tax.md) |
| 18.9 | Agent Loss Harvesting | `harvest_losses` via MCP | `agent_call` | IDE agent identifies loss harvesting opportunities | 🤖 | ✅ | [05h](05h-mcp-tax.md) |
| 18.10 | Agent Trade Plan | `create_trade_plan` via MCP | `agent_call` | IDE agent creates a plan during research | 🤖 | ✅ | [05d](05d-mcp-trade-planning.md) |
| 18.11 | Agent Pipeline Trigger | `run_pipeline` via MCP | `agent_call` | IDE agent triggers a report pipeline on demand | 🤖 | ✅ | [09](09-scheduling.md), [05](05-mcp-server.md) |
| 18.12 | Quarterly Deadline Alert | Auto-generated notification | `timer` | System alerts when IRS quarterly deadline approaches | ⏰ | ✅ | [06g](06g-gui-tax.md), [04](04-rest-api.md) |
| 18.13 | Wash Sale Auto-Detect | Trade triggers wash check | `event` | Every new trade auto-checks 61-day wash sale window | 🔗 | ✅ | [01](01-domain-layer.md), [matrix](build-priority-matrix.md) |
| 18.14 | NIIT Threshold Alert | MAGI approaches $200K/$250K | `event` | Auto-triggered when AGI nears NIIT threshold | 🔗 | ✅ | [01](01-domain-layer.md), [06g](06g-gui-tax.md) |

### Test Strategy (Programmatic Inputs)

| Test | Input | Expected Output |
|------|-------|-----------------|
| FlexQuery import | 50-record XML batch | 50 trades created, deduped |
| Data refresh cron | Watchlist with 10 tickers | 10 quote cache entries updated |
| Report pipeline | daily_report trigger | Email sent with rendered report |
| Token refresh | Token expiry in 5 min | Auto-refreshed before expiry |
| Wash sale on trade | New SLD within 30 days of BUY | Wash sale flagged |
| NIIT threshold | AGI=$245K (near $250K married) | Alert generated |
| Agent quote | MCP `get_stock_quote("AAPL")` | MarketQuote returned via REST |
| Missed cron | Server down during schedule | Misfire recovery within grace |

---

## 19. MCP Guard (Circuit Breaker + Panic Button)

> Protects against runaway MCP tool calls. Opt-in; disabled by default.
> Model: [`McpGuardModel`](02-infrastructure.md) | REST: [04g-api-system.md](04g-api-system.md) | MCP: [§5.6](05-mcp-server.md) | GUI: [§6f.8](06f-gui-settings.md)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 19.1 | `is_enabled` | `bool` | Enable/disable circuit breaker | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 19.2 | `calls_per_minute_limit` | `number` | Max MCP calls/min (default 60) | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 19.3 | `calls_per_hour_limit` | `number` | Max MCP calls/hr (default 500) | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 19.4 | Lock (panic) | `action` | Immediately lock all MCP tools | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 19.5 | Unlock | `action` | Re-enable MCP tools | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 19.6 | `reason` | `string` | Lock reason (free-text; convention: manual, rate_limit_exceeded, agent_self_lock) | 🤖🔌 | ✅ | [05](05-mcp-server.md) |
| 19.7 | `confirm` | `literal` | Unlock confirmation token (`"UNLOCK"`) | 🤖 | ✅ | [05](05-mcp-server.md) |

---

## 20. MCP Diagnostics & GUI Launch

> Agent-facing tools for debugging connectivity and launching the GUI.
> MCP: [§5.8](05-mcp-server.md), [§5.10](05-mcp-server.md)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 20.1 | `verbose` | `bool` | Include per-tool latency percentiles in diagnose output (default false) | 🤖 | ✅ | [05](05-mcp-server.md) |
| 20.2 | `wait_for_close` | `bool` | Block until GUI process exits (default false) | 🤖 | ✅ | [05](05-mcp-server.md) |

---

## 21. Build Plan Expansion Inputs

> Inputs for features from the [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1–§26.

### 21a. Broker Connection (§1, §24, §25)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21a.1 | `broker_id` | `string` | Broker adapter ID (e.g. "ibkr_pro", "alpaca_paper") | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21a.2 | `api_key` | `password` | Broker API key (Fernet-encrypted) | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 21a.3 | `api_secret` | `password` | Broker API secret (Alpaca requires both) | 🖥️🔌 | ✅ | [02](02-infrastructure.md), [04](04-rest-api.md) |
| 21a.4 | `environment` | `enum` | `live` / `paper` | 🖥️🔌 | ✅ | [04](04-rest-api.md) |

### 21b. CSV Import (§18)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21b.1 | `file` | `UploadFile` | Broker CSV file | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21b.2 | `broker_hint` | `string` | Broker name hint for format detection (default "auto") | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21b.3 | `account_id` | `string` | Target account for imported trades | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### 21c. Bank Statement Import (§26)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21c.1 | `file` | `UploadFile` | Bank statement file (CSV, OFX, QIF) | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21c.2 | `format_hint` | `enum` | `auto` / `csv` / `ofx` / `qif` | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21c.3 | `account_id` | `string` | Target bank account | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21c.4 | `bank_hint` | `string` | Bank name hint for field mapping | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### 21d. Manual Bank Transaction (§26)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21d.1 | `account_id` | `string` | Target bank account | 🖥️🔌 | ✅ | [04](04-rest-api.md) |
| 21d.2 | `date` | `date` | Transaction date | 🖥️🔌 | ✅ | [04](04-rest-api.md) |
| 21d.3 | `amount` | `number` | Transaction amount (negative for debit) | 🖥️🔌 | ✅ | [04](04-rest-api.md) |
| 21d.4 | `description` | `string` | Transaction description | 🖥️🔌 | ✅ | [04](04-rest-api.md) |
| 21d.5 | `category` | `enum` | TransactionCategory (deposit, withdrawal, etc.) | 🖥️🔌 | ✅ | [04](04-rest-api.md) |

### 21e. Mistake Tag (§17)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21e.1 | `trade_exec_id` | `string` | Trade to tag | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21e.2 | `category` | `enum` | MistakeCategory (EARLY_EXIT, REVENGE_TRADE, etc.) | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21e.3 | `estimated_cost` | `number` | Estimated cost of mistake | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21e.4 | `notes` | `text` | Free-form notes | 🖥️🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### 21f. AI Review Request (§12)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21f.1 | `trade_exec_id` | `string` | Trade to review | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21f.2 | `review_type` | `enum` | `single` / `weekly` | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21f.3 | `budget_cap` | `number` | Max spend in cents (opt-in) | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

### 21g. Identifier Resolution (§5)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 21g.1 | `id_type` | `enum` | `cusip` / `isin` / `sedol` / `figi` | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |
| 21g.2 | `id_value` | `string` | Identifier value to resolve | 🤖🔌 | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md) |

---

## 22. Service Daemon Controls (Phase 10)

> Backend service lifecycle management. GUI controls via Electron IPC; MCP tools via REST.
> Source: [Phase 10](10-service-daemon.md) | REST: [§10.3](10-service-daemon.md) | MCP: [§10.4](10-service-daemon.md) | GUI: [§10.5](10-service-daemon.md)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 22.1 | Start service | `action` | Start the backend service via OS service wrapper | 🖥️ | ✅ | [10](10-service-daemon.md) |
| 22.2 | Stop service | `action` | Stop the backend service | 🖥️ | ✅ | [10](10-service-daemon.md) |
| 22.3 | Restart service | `action` | Graceful restart via `POST /service/graceful-shutdown` | 🖥️🤖 | ✅ | [10](10-service-daemon.md) |
| 22.4 | Toggle auto-start | `bool` | Enable/disable auto-start at login | 🖥️ | ✅ | [10](10-service-daemon.md) |
| 22.5 | Open log folder | `action` | Open service log directory in file explorer | 🖥️ | ✅ | [10](10-service-daemon.md) |
| 22.6 | Service status query | `agent_call` | `zorivest_service_status` via MCP | 🤖 | ✅ | [10](10-service-daemon.md), [05](05-mcp-server.md) |
| 22.7 | Service log listing | `agent_call` | `zorivest_service_logs` via MCP | 🤖 | ✅ | [10](10-service-daemon.md), [05](05-mcp-server.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| Start service | Start action | Service state → running, PID visible |
| Stop service | Stop action | Service state → stopped, PID cleared |
| Restart service | Restart action | Service restarts, new PID |
| Toggle auto-start | Toggle on/off | Auto-start config updated per platform |
| Open logs | Open folder action | File explorer opens log directory |
| MCP status (up) | `zorivest_service_status` | Health + process metrics returned |
| MCP status (down) | `zorivest_service_status` (backend unreachable) | Error state returned |

---

## 23. MCP Discovery & Toolset Management

> Toolset discovery, inspection, and activation for adaptive MCP clients.
> Source: [05j-mcp-discovery.md](05j-mcp-discovery.md) | Architecture: [§5.11–§5.14](05-mcp-server.md)

| # | Input | Type | Description | Surface | Status | Plan Files |
|---|-------|------|-------------|---------|--------|------------|
| 23.1 | (none) | — | `list_available_toolsets` is parameterless | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |
| 23.2 | `toolset_name` | `string` | Toolset to describe (e.g. `"trade-analytics"`) | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |
| 23.3 | `toolset_name` | `string` | Toolset to enable/disable | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |
| 23.4 | `enable` | `bool` | Enable (`true`) or disable (`false`) toolset | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |
| 23.5 | `tool_name` | `string` | Tool requiring confirmation (destructive ops) | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |
| 23.6 | `parameters` | `object` | Tool parameters to hash for token generation | 🤖 | ✅ | [05j](05j-mcp-discovery.md) |

### Test Strategy

| Test | Input | Expected Output |
|------|-------|-----------------|
| List toolsets | `list_available_toolsets` | Array with all 8 toolsets, each with name/description/enabled/tool_count |
| Describe valid | `describe_toolset("core")` | Tool list with annotations for each core tool |
| Describe invalid | `describe_toolset("nonexistent")` | Error: toolset not found |
| Enable toolset | `enable_toolset("tax", true)` | Confirmation with enabled=true |
| Disable toolset | `enable_toolset("tax", false)` | Confirmation with enabled=false |
| Confirm token | `get_confirmation_token("zorivest_emergency_stop", {...})` | Valid HMAC token string |
| Token for non-destructive | `get_confirmation_token("list_trades", {...})` | Error: tool is not destructive |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total input fields (human-entered) | 155 |
| Programmatic/scheduled triggers | 16 |
| MCP discovery inputs | 6 |
| Feature groups | 34 (incl. sub-sections 9a, 15a, 15b, 15m, 15d, 17a, 21a–21g, 23) |
| ✅ Defined (full surface contract) | 161 inputs |
| 🔶 Domain modeled (no REST/MCP/GUI contract) | 0 inputs |
| 📋 Planned (matrix-only, no routes/tools) | 0 inputs |
| GUI-only inputs (security) | 2 (passphrase, API key entry) |
| MCP-only input parameters | 10 (`image_base64`, `confirm`, `verbose`, `wait_for_close`, `toolset_name`, `enable`, `tool_name`, `parameters`) |
| MCP-only tool calls (no GUI equivalent) | 6 (`zorivest_service_status`, `zorivest_service_logs`, `list_available_toolsets`, `describe_toolset`, `enable_toolset`, `get_confirmation_token`) |
| Files referenced | 12 build plan docs |


