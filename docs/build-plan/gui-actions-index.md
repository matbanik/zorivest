# GUI Actions Index — Complete Action Catalog

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Companion: [Input Index](input-index.md) · [Output Index](output-index.md)

Canonical registry of **every GUI action** (buttons, triggers, keyboard shortcuts) the system exposes. Actions are non-data-input interactions — they invoke operations, navigate, or mutate state.

---

## Legend

| Column | Meaning |
|--------|---------|
| **Trigger** | 🔘 Button · ⌨️ Keyboard · 🖱️ Context (right-click/hover) · 🔀 Toggle · 📂 File (picker/drag-drop) |
| **REST** | HTTP method + endpoint invoked (if any) |
| **MCP** | Equivalent MCP tool (if any) |
| **Status** | ✅ Defined (full contract) · 🔶 Domain modeled · 📋 Planned |
| **Plan Files** | Which build plan doc(s) define the contract |

---

## 1. Position Calculator

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 1.1 | Calculate position size | 🔘⌨️ `Enter` | `POST /api/v1/calculator/position-size` | `calculate_position_size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.2 | Clear form | 🔘 | — (client-side) | — | ✅ | [06h](06h-gui-calculator.md) |
| 1.3 | Save Scenario | 🔘⌨️ `Ctrl+S` | — (session state) | — | ✅ | [06h](06h-gui-calculator.md) |
| 1.4 | Load from History | 🔘 | — (session state) | — | ✅ | [06h](06h-gui-calculator.md) |
| 1.5 | Copy to Plan | 🔘 | navigates → creates TradePlan | — | ✅ | [06h](06h-gui-calculator.md), [06c](06c-gui-planning.md) |
| 1.6 | Close Modal | 🔘⌨️ `Escape` | — | — | ✅ | [06h](06h-gui-calculator.md) |
| 1.7 | Open Calculator | ⌨️ `Ctrl+Shift+C` | — | — | ✅ | [06h](06h-gui-calculator.md) |

---

## 2. Trade Management

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 2.1 | Save trade (create) | 🔘 | `POST /api/v1/trades` | `create_trade` | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md), [06b](06b-gui-trades.md) |
| 2.2 | Update trade | 🔘 | `PUT /api/v1/trades/{exec_id}` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 2.3 | Delete trade | 🔘 | `DELETE /api/v1/trades/{exec_id}` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |

---

## 3. Screenshot Management

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 3.1 | Upload via file picker | 📂 | `POST /api/v1/trades/{exec_id}/images` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 3.2 | Paste from clipboard | ⌨️ `Ctrl+V` | `POST /api/v1/trades/{exec_id}/images` | — | ✅ | [06b](06b-gui-trades.md) |
| 3.3 | Drag & drop upload | 🖱️ | `POST /api/v1/trades/{exec_id}/images` | — | ✅ | [06b](06b-gui-trades.md) |
| 3.4 | Delete screenshot | 🔘 | `DELETE /api/v1/images/{id}` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 3.5 | Open lightbox | 🖱️ click | — (client-side) | — | ✅ | [06b](06b-gui-trades.md) |
| 3.6 | MCP base64 attach | — (MCP only) | — | `attach_screenshot` | ✅ | [05](05-mcp-server.md) |

---

## 4. Trade Report (Journal)

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 4.1 | Save report | 🔘 | `POST /api/v1/reports` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 4.2 | Update report | 🔘 | `PUT /api/v1/reports/{id}` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 4.3 | Delete report | 🔘 | `DELETE /api/v1/reports/{id}` | — | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |

---

## 5. Trade Planning

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 5.1 | Create plan | 🔘 | `POST /api/v1/trade-plans` | `create_trade_plan` | ✅ | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 5.2 | Update plan | 🔘 | `PUT /api/v1/trade-plans/{id}` | — | 🔶 | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 5.3 | Delete plan | 🔘 | `DELETE /api/v1/trade-plans/{id}` | — | 🔶 | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 5.4 | Change status (DRAFT→ACTIVE→EXECUTED) | 🔘 | `PATCH /api/v1/trade-plans/{id}/status` | — | 🔶 | [06c](06c-gui-planning.md) |
| 5.5 | Link plan to trade | 🔘 | `PUT /api/v1/trade-plans/{id}` (set trade_id) | — | 🔶 | [06c](06c-gui-planning.md) |

---

## 6. Watchlist Management

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 6.1 | Create watchlist | 🔘 | `POST /api/v1/watchlists` | — | 🔶 | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 6.2 | Delete watchlist | 🔘 | `DELETE /api/v1/watchlists/{id}` | — | 🔶 | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 6.3 | Add item | 🔘 | `POST /api/v1/watchlists/{id}/items` | — | 🔶 | [01](01-domain-layer.md), [06c](06c-gui-planning.md) |
| 6.4 | Remove item | 🔘 | `DELETE /api/v1/watchlists/{id}/items/{ticker}` | — | 🔶 | [06c](06c-gui-planning.md) |
| 6.5 | Bulk add (comma-separated) | 🔘 | `POST /api/v1/watchlists/{id}/items/bulk` | — | 🔶 | [06c](06c-gui-planning.md) |

---

## 7. Account Management

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 7.1 | Create account | 🔘 | `POST /api/v1/accounts` | — | ✅ | [04](04-rest-api.md), [06d](06d-gui-accounts.md) |
| 7.2 | Update account | 🔘 | `PUT /api/v1/accounts/{id}` | — | ✅ | [04](04-rest-api.md), [06d](06d-gui-accounts.md) |
| 7.3 | Delete account | 🔘 | `DELETE /api/v1/accounts/{id}` | — | ✅ | [04](04-rest-api.md), [06d](06d-gui-accounts.md) |

---

## 8. Account Review Wizard

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 8.1 | Start wizard | 🔘 | — (client-side flow) | — | 🔶 | [06d](06d-gui-accounts.md) |
| 8.2 | Skip account | 🔘 | — (advance to next) | — | 🔶 | [06d](06d-gui-accounts.md) |
| 8.3 | Update balance (manual) | 🔘 | `POST /api/v1/accounts/{id}/balances` | — | 🔶 | [06d](06d-gui-accounts.md) |
| 8.4 | Fetch balance via API | 🔘 | broker-specific API call | — | 🔶 | [06d](06d-gui-accounts.md) |

---

## 9. Settings — Reset

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 9.1 | Reset individual setting | 🔘 ↻ icon | `DELETE /api/v1/settings/{key}` | — | ✅ | [06f](06f-gui-settings.md) |
| 9.2 | Reset all to defaults | 🔘 | bulk `DELETE /api/v1/settings/{key}` | — | ✅ | [06f](06f-gui-settings.md) |

---

## 10. Settings — Market Data Providers

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 10.1 | Test connection | 🔘 | `POST /api/v1/market-data/providers/{name}/test` | `test_market_provider` | ✅ | [08](08-market-data.md), [06f](06f-gui-settings.md) |
| 10.2 | Remove API key | 🔘 | `DELETE /api/v1/market-data/providers/{name}/key` | `disconnect_market_provider` | ✅ | [08](08-market-data.md), [06f](06f-gui-settings.md) |
| 10.3 | Save provider config | 🔘 | `PUT /api/v1/market-data/providers/{name}` | — | ✅ | [08](08-market-data.md), [06f](06f-gui-settings.md) |

---

## 11. Settings — Email Provider

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 11.1 | Select preset | 🔘 dropdown | — (client auto-fill) | — | 📋 | [06f](06f-gui-settings.md) |
| 11.2 | Test & Save | 🔘 | `POST /api/v1/email/test` | — | 📋 | [06f](06f-gui-settings.md) |

---

## 12. Settings — Backup & Restore

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 12.1 | Create backup | 🔘 | `POST /api/v1/backups` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |
| 12.2 | Verify backup | 🔘 | `POST /api/v1/backups/verify` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |
| 12.3 | Restore from backup | 🔘 | `POST /api/v1/backups/restore` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |
| 12.4 | Open backup in explorer | 🔘 ↗ icon | — (Electron `shell.showItemInFolder`) | — | ✅ | [06f](06f-gui-settings.md) |

---

## 13. Settings — Config Export/Import

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 13.1 | Export config | 🔘 | `GET /api/v1/config/export` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |
| 13.2 | Select import file | 📂 | — (client file picker) | — | ✅ | [06f](06f-gui-settings.md) |
| 13.3 | Preview import | 🔘 | `POST /api/v1/config/import?dry_run=true` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |
| 13.4 | Apply import | 🔘 | `POST /api/v1/config/import` | — | ✅ | [02a](02a-backup-restore.md), [06f](06f-gui-settings.md) |

---

## 14. Settings — MCP Guard

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 14.1 | Emergency Stop (lock) | 🔘 | `POST /api/v1/mcp-guard/lock` | `zorivest_emergency_stop` | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 14.2 | Unlock MCP tools | 🔘 | `POST /api/v1/mcp-guard/unlock` | `zorivest_emergency_unlock` | ✅ | [04](04-rest-api.md), [05](05-mcp-server.md), [06f](06f-gui-settings.md) |
| 14.3 | Save threshold config | 🔘 | `PUT /api/v1/mcp-guard` | — | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |

---

## 15. Schedule Management

> **⛔ Superseded by Section 25 (Scheduling & Pipeline).** The `/api/v1/schedules` endpoints below are replaced by the Phase 9 policy-driven scheduling at `/api/v1/scheduling/policies`. See Section 25 for the canonical contracts.

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 15.1 | ~~Create schedule~~ | 🔘 | ~~`POST /api/v1/schedules`~~ | — | ⛔ | [09](09-scheduling.md) §25.1 |
| 15.2 | ~~Update schedule~~ | 🔘 | ~~`PUT /api/v1/schedules/{id}`~~ | — | ⛔ | [09](09-scheduling.md) §25.2 |
| 15.3 | ~~Delete schedule~~ | 🔘 | ~~`DELETE /api/v1/schedules/{id}`~~ | — | ⛔ | [09](09-scheduling.md) §25.1 |
| 15.4 | ~~Run Now~~ | 🔘 | ~~`POST /api/v1/schedules/{id}/run`~~ | ~~`run_pipeline_now`~~ | ⛔ | [09](09-scheduling.md) §25.4 |
| 15.5 | ~~Enable/Disable toggle~~ | 🔀 | ~~`PATCH /api/v1/schedules/{id}`~~ | — | ⛔ | [09](09-scheduling.md) §25.3 |

---

## 16. Tax — Lot Viewer

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 16.1 | Close specific lot | 🔘 | `POST /api/v1/tax/lots/{lot_id}/close` | — | 📋 | [06g](06g-gui-tax.md) |
| 16.2 | Reassign cost basis method | 🔘 | `PUT /api/v1/tax/lots/{lot_id}/reassign` | — | 📋 | [06g](06g-gui-tax.md) |
| 16.3 | View linked trades | 🔘 | — (navigate to trade detail) | — | 📋 | [06g](06g-gui-tax.md) |
| 16.4 | Apply method to all lots | 🔘 | batch reassign | — | 📋 | [06g](06g-gui-tax.md) |

---

## 17. Tax — Wash Sale Monitor

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 17.1 | Scan Now | 🔘 | `POST /api/v1/tax/wash-sales/scan` | — | 📋 | [06g](06g-gui-tax.md) |

---

## 18. Tax — What-If Simulator

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 18.1 | Simulate | 🔘 | `POST /api/v1/tax/simulate` | `simulate_tax_impact` | ✅ | [06g](06g-gui-tax.md) |
| 18.2 | Save scenario | 🔘 | — (session state) | — | 📋 | [06g](06g-gui-tax.md) |
| 18.3 | Compare scenarios | 🔘 | — (client-side) | — | 📋 | [06g](06g-gui-tax.md) |

---

## 19. Tax — Loss Harvesting

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 19.1 | Scan portfolio | 🔘 | `GET /api/v1/tax/harvest` | `harvest_losses` | ✅ | [06g](06g-gui-tax.md) |
| 19.2 | Simulate (per row) | 🔘 | `POST /api/v1/tax/simulate` | — | 📋 | [06g](06g-gui-tax.md) |
| 19.3 | Sell (per row) | 🔘 | — (opens order flow) | — | 📋 | [06g](06g-gui-tax.md) |

---

## 20. Tax — Quarterly Payments

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 20.1 | Record payment | 🔘 | `POST /api/v1/tax/quarterly` | — | 📋 | [06g](06g-gui-tax.md) |

---

## 21. Tax — Transaction Audit

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 21.1 | Run audit | 🔘 | `POST /api/v1/tax/audit` | — | 📋 | [06g](06g-gui-tax.md) |

---

## 22. Shell — Command Palette

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 22.1 | Open command palette | ⌨️ `Ctrl+K` | — | — | ✅ | [06a](06a-gui-shell.md) |
| 22.2 | Execute command | ⌨️ `Enter` / 🖱️ click | varies by command | — | ✅ | [06a](06a-gui-shell.md) |
| 22.3 | Close palette | ⌨️ `Escape` | — | — | ✅ | [06a](06a-gui-shell.md) |

---

## 23. Navigation

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 23.1 | Navigate to Accounts | 🔘 nav rail / ⌨️ `Ctrl+1` | — | — | ✅ | [06](06-gui.md), [06a](06a-gui-shell.md) |
| 23.2 | Navigate to Trades | 🔘 nav rail / ⌨️ `Ctrl+2` | — | — | ✅ | [06](06-gui.md), [06a](06a-gui-shell.md) |
| 23.3 | Navigate to Planning | 🔘 nav rail / ⌨️ `Ctrl+3` | — | — | ✅ | [06](06-gui.md), [06a](06a-gui-shell.md) |
| 23.4 | Navigate to Scheduling | 🔘 nav rail | — | — | ✅ | [06](06-gui.md), [06a](06a-gui-shell.md) |
| 23.5 | Navigate to Settings | 🔘 nav rail | — | — | ✅ | [06](06-gui.md), [06a](06a-gui-shell.md) |
| 23.6 | Navigate to Tax Estimator | 🔘 nav rail | — | — | 📋 | [06](06-gui.md), [06g](06g-gui-tax.md) |
| 23.7 | Collapse/expand nav rail | 🔘 | — | — | ✅ | [06](06-gui.md) |

---

## 24. Settings — MCP Server Status

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 24.1 | Copy IDE config JSON | 🔘 | — (client-side generation) | — | ✅ | [06f](06f-gui-settings.md) |
| 24.2 | Refresh status | 🔘 | `GET /health` + `GET /version` | `zorivest_diagnose` | ✅ | [06f](06f-gui-settings.md), [05](05-mcp-server.md) |

---

## 25. Scheduling & Pipeline

> Policy management, pipeline execution, and approval flow.
> Source: [06e-gui-scheduling.md](06e-gui-scheduling.md), [Phase 9](09-scheduling.md)

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 25.1 | Create/save policy | 🔘 | `POST/PUT /api/v1/scheduling/policies` | `create_policy` | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.2 | Enable/disable schedule | 🔘 toggle | `PUT /api/v1/scheduling/policies/{id}` | `update_policy_schedule` | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.3 | Run now | 🔘 | `POST /api/v1/scheduling/policies/{id}/run` | `run_pipeline` | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.4 | Dry-run / preview report | 🔘 | `POST /api/v1/scheduling/policies/{id}/run` (dry_run=true) | `preview_report` | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.5 | Approve policy | 🔘 | `POST /api/v1/scheduling/policies/{id}/approve` | — | ✅ | [09](09-scheduling.md) |
| 25.6 | Delete policy | 🔘 | `DELETE /api/v1/scheduling/policies/{id}` | — | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.7 | View run history | 🔘 table row | `GET /api/v1/scheduling/policies/{id}/runs` | `get_pipeline_history` | ✅ | [06e](06e-gui-scheduling.md), [09](09-scheduling.md) |
| 25.8 | View run detail (step progress) | 🔘 table row | `GET /api/v1/scheduling/runs/{id}` | — | ✅ | [09](09-scheduling.md) |

---

## 26. Settings — Service Manager

> Backend service lifecycle controls.
> Source: [10-service-daemon.md §10.5](10-service-daemon.md)

| # | Action | Trigger | REST | MCP | Status | Plan Files |
|---|--------|---------|------|-----|--------|------------|
| 26.1 | Start service | 🔘 | — (Electron IPC → OS command) | — (GUI-only: requires OS privilege escalation) | ✅ | [10](10-service-daemon.md) |
| 26.2 | Stop service | 🔘 | — (Electron IPC → OS command) | — (GUI-only: requires OS privilege escalation) | ✅ | [10](10-service-daemon.md) |
| 26.3 | Restart service | 🔘 | `POST /api/v1/service/graceful-shutdown` | `zorivest_service_restart` | ✅ | [10](10-service-daemon.md) |
| 26.4 | Toggle auto-start | 🔀 | — (Electron IPC → OS command) | — (GUI-only: requires OS privilege escalation) | ✅ | [10](10-service-daemon.md) |
| 26.5 | Open log folder | 🔘 | — (Electron `shell.openPath`) | `zorivest_service_logs` (returns content; GUI opens folder) | ✅ | [10](10-service-daemon.md) |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total GUI actions | 97 (incl. 5 superseded) |
| Sections | 26 |
| ✅ Defined (full contract) | 62 |
| 🔶 Domain modeled | 14 |
| 📋 Planned | 21 |
| ⛔ Superseded | 5 |
| Actions with REST endpoints | 66 |
| Actions with MCP equivalents | 19 |
| Keyboard-triggered actions | 11 |
| Client-side only (no REST) | 31 |
