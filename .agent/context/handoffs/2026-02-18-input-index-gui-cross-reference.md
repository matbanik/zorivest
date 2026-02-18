# Input Index ↔ GUI Spec Cross-Reference Validation

> **Date**: 2026-02-18
> **Scope**: Cross-reference every input from [input-index.md](file:///p:/zorivest/docs/build-plan/input-index.md) against GUI specs [06-gui.md](file:///p:/zorivest/docs/build-plan/06-gui.md) through [06h-gui-calculator.md](file:///p:/zorivest/docs/build-plan/06h-gui-calculator.md)
> **Objective**: Find coverage gaps, untracked GUI inputs, surface flag errors, and status mismatches

---

## Executive Summary

| Category | Count |
|----------|-------|
| ✅ Fully covered (index ↔ GUI aligned) | 73 input fields |
| 🔴 Critical: GUI inputs missing from index | 19 fields |
| 🟡 Medium: Surface flag mismatches | 6 fields |
| 🟠 High: Status should be upgraded | 8 fields |
| ℹ️ Correctly domain-only / planned (no GUI yet) | 28 fields |

---

## Finding 1 — Critical: Calculator Mode-Specific Inputs Not in Index

> [!CAUTION]
> The input index Section 1 (Position Calculator) lists only 5 common fields (`balance`, `risk_pct`, `entry`, `stop`, `target`). However, [06h-gui-calculator.md](file:///p:/zorivest/docs/build-plan/06h-gui-calculator.md) defines **15+ additional mode-specific inputs** that are fully specified with types, defaults, and computations.

### Missing Futures Mode Inputs (06h §Futures)

| Input | Type | Default | Index Row | Status |
|-------|------|---------|-----------|--------|
| `instrument_mode` | `select` | `Equity` | **MISSING** | Common to all modes |
| `account_id` | `dropdown` | All Accounts | **MISSING** | Common; noted as "planned" in index callout but not a row |
| `contract_multiplier` | `number` | preset/symbol | **MISSING** | Futures-specific |
| `tick_size` | `number` | preset/symbol | **MISSING** | Futures-specific |
| `margin_per_contract` | `number` | user input | **MISSING** | Futures-specific |

### Missing Options Mode Inputs (06h §Options)

| Input | Type | Default | Index Row | Status |
|-------|------|---------|-----------|--------|
| `option_type` | `select` | Call | **MISSING** | Options-specific |
| `premium` | `number` | user input | **MISSING** | Options-specific |
| `delta` | `number` | user input | **MISSING** | Options-specific |
| `underlying_price` | `number` | user input | **MISSING** | Options-specific |
| `contracts_multiplier` | `number` | 100 | **MISSING** | Options-specific |

### Missing Forex Mode Inputs (06h §Forex)

| Input | Type | Default | Index Row | Status |
|-------|------|---------|-----------|--------|
| `currency_pair` | `text` | user input | **MISSING** | Forex-specific |
| `lot_type` | `select` | Standard | **MISSING** | Forex-specific |
| `pip_value` | `number` | auto-calc | **MISSING** | Forex-specific (auto but overridable) |
| `leverage` | `number` | 50 | **MISSING** | Forex-specific |

### Missing Crypto Mode Inputs (06h §Crypto)

| Input | Type | Default | Index Row | Status |
|-------|------|---------|-----------|--------|
| `leverage` | `number` | 1 (spot) | **MISSING** | Crypto-specific |
| `funding_rate` | `number` | 0.01% | **MISSING** | Crypto-specific |

**Recommendation**: Add Section 1 sub-tables (1a Futures, 1b Options, 1c Forex, 1d Crypto) with all mode-specific inputs, plus common rows for `instrument_mode` (1.6) and `account_id` (1.7). All should be **✅ Defined** since `06h` has full contracts.

---

## Finding 2 — Critical: Backup/Restore & Config Export GUI Inputs Not in Index

> [!CAUTION]
> [06f-gui-settings.md](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) §6f.5 and §6f.6 define actionable GUI inputs that have no entry in the input index at all.

### Missing Backup/Restore Inputs (06f §6f.5)

| GUI Input | Type | Index Row | Status |
|-----------|------|-----------|--------|
| Create Backup Now | `action` (button) | **MISSING** | REST: `POST /backups` fully defined |
| Auto-backup interval | `number` (seconds) | **MISSING** | Setting: `backup.auto_interval_seconds` |
| Change threshold | `number` | **MISSING** | Setting: `backup.change_threshold` |
| Compression toggle | `bool` | **MISSING** | Setting: `backup.compression` |
| Auto-backup enabled | `bool` | **MISSING** | Setting: `backup.auto_enabled` |
| Select Backup File | `file` (picker) | **MISSING** | For restore flow |
| Verify Backup | `action` | **MISSING** | REST: `POST /backups/verify` |
| Restore Backup | `action` | **MISSING** | REST: `POST /backups/restore` |

### Missing Config Export/Import Inputs (06f §6f.6)

| GUI Input | Type | Index Row | Status |
|-----------|------|-----------|--------|
| Export Config | `action` | **MISSING** | REST: `GET /config/export` |
| Select Import File | `file` (picker) | **MISSING** | File selection for import |
| Preview Changes | `action` | **MISSING** | REST: `POST /config/import?dry_run=true` |
| Apply Import | `action` | **MISSING** | REST: `POST /config/import` |

**Recommendation**: Add new Section 20 (Backup & Restore) and Section 21 (Config Export/Import) to the input index. All have REST endpoints defined in Phase 2A, so status should be **✅ Defined**.

---

## Finding 3 — Critical: Logging Settings GUI Inputs Not in Index

> [!CAUTION]
> [06f-gui-settings.md](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) §6f.4 defines per-component log level dropdowns and rotation settings with implementation hooks — none appear in the input index.

| GUI Input | Type | Index Row | Status |
|-----------|------|-----------|--------|
| Per-component log level (9 components) | `dropdown` each | **MISSING** | Settings keys: `logging.{component}.level` |
| Log rotation max file size | `number` (MB) | **MISSING** | Setting: `logging.rotation_mb` |
| Log rotation backup count | `number` | **MISSING** | Setting: `logging.backup_count` |

**Recommendation**: Add as Section 22 (Logging Settings). Status: **✅ Defined** — uses `usePersistedState` hook with REST contract.

---

## Finding 4 — High: Tax GUI Inputs Present in GUI Spec but Status May Need Upgrading

The tax GUI spec ([06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md)) defines detailed layouts, summary cards, filter dropdowns, and form inputs. Several input-index entries are marked 📋 Planned but the GUI spec now provides concrete wireframes.

| Index Row | Input | Current Status | GUI Spec Evidence | Recommended Status |
|-----------|-------|---------------|-------------------|-------------------|
| 11.1 | `ticker` (What-If) | 📋 | 06g §What-If Simulator: full wireframe with ticker input | 🔶 or ✅ |
| 11.2 | `quantity` (What-If) | 📋 | 06g §What-If: quantity field shown | 🔶 or ✅ |
| 11.3 | `lot_selection_method` | 📋 | 06g §What-If: "Cost Basis: [FIFO ▼]" dropdown | 🔶 or ✅ |
| 12.1 | `ticker` (Lot Matcher) | 📋 | 06g §Tax Lot Viewer: ticker filter | 🔶 |
| 12.2 | `lot_ids` (Specific Lot) | 📋 | 06g §Tax Lot Viewer: checkbox selection column | 🔶 |
| 13.1 | `quarter` | 📋 | 06g §Quarterly Payments: quarter selector | 🔶 |
| 13.2 | `actual_payment` | 📋 | 06g §Quarterly Payments: payment input field | 🔶 |
| 13.3 | `estimation_method` | 📋 | 06g §Quarterly Payments: method dropdown | 🔶 |

**Recommendation**: Upgrade these 8 rows from 📋 to at minimum 🔶 (domain modeled with GUI wireframe), or ✅ if the corresponding REST endpoints are also fully specified. Verify REST contract existence before upgrading to ✅.

---

## Finding 5 — Medium: GUI Surface Flag (🖥️) Mismatches

Some input-index rows lack 🖥️ but the GUI spec defines a GUI form for that input, or vice versa.

| Index Row | Input | Index Surface | GUI Spec Evidence | Issue |
|-----------|-------|--------------|-------------------|-------|
| 2.7 | `commission` | 🖥️🔌🔗 | 06b: Not shown in TradeDetailPanel form fields | GUI spec omits — may be auto-filled only |
| 2.8 | `realized_pnl` | 🖥️🔌🔗 | 06b: Read-only display column, not an input field | Not actually a GUI *input* — it's display-only |
| 3.6 | `mime_type` | 🤖🔌 | 06b §ScreenshotPanel: auto-detected, no GUI input | Correct — no 🖥️ |
| 15a.1 | `provider` (OAuth) | 🖥️🤖🔌 | 06f: No OAuth section in current GUI spec | 06f mentions OAuth as P3/future |
| 15b.1 | `provider` (Static) | 🖥️🤖🔌 | 06f: Not an input — provider name is from registry | Pre-populated dropdown, technically correct |
| 7.5 | `currency` | 🖥️🔌 | 06d §AccountPage: Listed as form field | Missing 🤖 flag — should MCP support this? |

**Recommendation**: 
- Row 2.8 (`realized_pnl`): Clarify in index that this is "display-only on GUI; input via API/import only"
- Row 2.7 (`commission`): Verify whether GUI allows manual commission entry or if it's auto-only
- Row 15a.1: Confirm OAuth is P3 and add note to index  
- Row 7.5: Decide if MCP `create_account` tool should accept `currency`

---

## Finding 6 — Medium: Tax Lot Viewer Filter Inputs Not Tracked

[06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md) §Tax Lot Viewer defines several filter/control inputs that are not in the index:

| GUI Control | Type | Purpose | Index Row |
|-------------|------|---------|-----------|
| Cost Basis Method dropdown | `select` | Override default method per view | **MISSING** (overlaps 10.10 but separate context) |
| Open/Closed filter | `select` | Filter lot status | **MISSING** |
| Ticker filter | `text` | Filter by symbol | **MISSING** |
| Account filter | `select` | Filter by account | **MISSING** |
| "Apply to All" action | `button` | Apply selected cost basis to all lots | **MISSING** |

> [!NOTE]
> These are UI-level filter controls rather than data-mutation inputs. The index may intentionally exclude read-only/filter inputs. **Decide policy**: should filter/view controls be tracked in the input index?

**Recommendation**: Add a policy note to the index legend clarifying whether filter/view controls are in scope. If in scope, add them to Section 12 or a new sub-section.

---

## Finding 7 — Medium: What-If Simulator Has Additional GUI Inputs

[06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md) §What-If Simulator defines inputs beyond what Section 11 tracks:

| GUI Input | Type | Purpose | Index Row |
|-----------|------|---------|-----------|
| `sell_price` | `number` | Hypothetical sale price | **MISSING** |
| "Compare" toggle/button | `action` | Multi-scenario comparison mode | **MISSING** |
| Save Scenario | `action` | Persist a what-if scenario | **MISSING** |

**Recommendation**: Add `sell_price` as row 11.4. Actions (Compare, Save) may be out of scope per index policy but should be documented.

---

## Finding 8 — Loss Harvesting Tool GUI Inputs Not in Index

[06g-gui-tax.md](file:///p:/zorivest/docs/build-plan/06g-gui-tax.md) §Loss Harvesting defines actionable GUI inputs:

| GUI Input | Type | Purpose | Index Row |
|-----------|------|---------|-----------|
| Scan / Refresh | `action` | Trigger loss harvesting scan | **MISSING** |
| Minimum loss threshold | `number` | Filter out small losses | **MISSING** |
| Execute Harvest | `action` | Generate orders for selected lots | **MISSING** |
| Replacement ticker selection | `dropdown` | Choose substantially non-identical replacement | **MISSING** |

**Recommendation**: Add as new Section 23 (Loss Harvesting Inputs) or extend Section 12. Status: 📋 (no REST endpoint contracts yet).

---

## Verified Coverage Matrix

The following sections are **fully aligned** between input-index and GUI specs:

| Index Section | GUI Spec | Status | Notes |
|--------------|----------|--------|-------|
| §2 Trade Logging | 06b §TradesTable, §TradeDetailPanel | ✅ | All 9 fields match |
| §3 Screenshots | 06b §ScreenshotPanel | ✅ | File, caption, base64 all covered |
| §4 Trade Report | 06b §TradeReportForm | ✅ | All 8 fields match |
| §5 Trade Plan | 06c §TradePlanPage | ✅ | GUI wireframe matches 13 fields (status 🔶 correct — no REST) |
| §6 Watchlists | 06c §WatchlistPage | ✅ | 4 fields match |
| §7 Account CRUD | 06d §AccountPage | ✅ | 7 fields match |
| §8 Account Review | 06d §AccountReviewWizard | ✅ | 3 fields match |
| §9 Display Toggles | 06f §Display Preferences | ✅ | 3 fields match |
| §9a UI/Notification | 06a §Notifications, §State | ✅ | 2 groups match |
| §10 Tax Profile | 06f §Tax Profile (stub) | ✅ | Correctly 🔶 — P3 placeholder in GUI |
| §14 Security | 06a §Passphrase prompt | ✅ | Passphrase GUI-only correctly flagged |
| §15m Market Data | 06f §Market Data Providers | ✅ | 7 fields match |
| §19 MCP Guard | 06f §MCP Guard | ✅ | 7 fields match |

---

## Summary of Recommended Changes

| Priority | Action | Affected Index Sections |
|----------|--------|----------------------|
| 🔴 Critical | Add calculator mode-specific inputs (15+ fields) | §1 → §1a–1d |
| 🔴 Critical | Add backup/restore inputs (8 fields) | New §20 |
| 🔴 Critical | Add config export/import inputs (4 fields) | New §21 |
| 🔴 Critical | Add logging settings inputs (11 fields) | New §22 |
| 🟠 High | Upgrade tax GUI input statuses (📋 → 🔶/✅) | §11, §12, §13 |
| 🟡 Medium | Fix surface flag mismatches | §2.7, §2.8, §7.5, §15a.1 |
| 🟡 Medium | Add what-if `sell_price` field | §11 |
| 🟡 Medium | Add loss harvesting inputs | New §23 or extend §12 |
| ℹ️ Policy | Decide: are filter/view controls in scope? | §Legend, §12 |
| ℹ️ Stats | Update summary statistics after all additions | §Summary |

### Estimated New Field Count

| Category | Current | After Remediation |
|----------|---------|-------------------|
| Total human-entered inputs | 115 | ~155 (+40) |
| ✅ Defined | 55 | ~85 (+30) |
| Feature groups | 23 | ~27 (+4 new sections) |

---

## Next Steps

1. **User decision**: Should filter/view controls be tracked in the index? (Finding 6)
2. **User decision**: Should action buttons (Create Backup, Execute Harvest) be tracked? (Findings 2, 8)
3. **Implement**: Update `input-index.md` per accepted recommendations
4. **Verify**: Re-run cross-reference after update to confirm 100% coverage
