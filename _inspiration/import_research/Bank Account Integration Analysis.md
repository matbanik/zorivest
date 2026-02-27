# Bank Account Integration Analysis for Zorivest

> Analysis of how Zorivest can import bank account balances and transactions from the 15 institutions identified in [Trader Banking Preferences: 2025 Analysis](file:///p:/zorivest/_inspiration/import_research/Trader%20Banking%20Preferences_%202025%20Analysis.md). Covers CSV import, direct API access, aggregator services, and manual entry.

---

## Executive Summary

Bank account integration in Zorivest differs fundamentally from broker integration. Banks rarely offer direct REST APIs to individual consumers — the dominant access methods are:

1. **Aggregator APIs** (Plaid, Finicity, Yodlee) — unified interface to 12,000+ institutions
2. **File Export** (CSV, OFX/QFX, QBO) — manual download from bank dashboard
3. **Direct REST APIs** — only available from FinTech-native banks (Wise, Mercury, Revolut, Starling)
4. **Open Banking Standards** — PSD2 (UK/EU), CDR (Australia), Account Aggregator (India)
5. **Manual Entry** — always available as fallback for any institution

**Recommended Architecture:** A tiered approach where **manual entry** is the baseline, **file import** is the standard, and **aggregator/API** connections are premium features.

---

## Integration Methods Per Institution

### Tier 1: Full API Access (Direct REST + Aggregator)

| # | Institution | Direct API | Aggregator (Plaid) | File Export | Manual | Notes |
|---|-------------|-----------|-------------------|-------------|--------|-------|
| 1 | **Fidelity** (CMA) | ❌ No public API | ✅ Full (balance + txns) | ✅ CSV, QFX | ✅ | QFX includes positions + balances; CSV via `Accounts_History.csv` export; Plaid integration is mature and reliable |
| 2 | **Charles Schwab** | ❌ No public API | ✅ Full (balance + txns) | ✅ CSV, OFX | ✅ | OFX export available for Investor Checking; Plaid connectivity confirmed |
| 3 | **IBKR** | ✅ Client Portal API + Flex Reports | ✅ Partial (varies) | ✅ CSV, XML (Flex) | ✅ | Already covered by broker integration (§24 Alpaca-style); Flex Reports cover transactions comprehensively |
| 4 | **Wise** | ✅ **Full REST API** | ✅ Supported via Plaid | ✅ CSV, PDF statements | ✅ | **Best API** — `GET /v4/profiles/{id}/balances` for balances, `GET /v1/profiles/{id}/balance-statements/{balanceId}/statement.json` for transactions by date range; Bearer token auth; sandbox available |
| 5 | **Wealthfront** | ❌ No public API | ✅ Full (balance + txns) | ✅ CSV | ✅ | Plaid is the primary automated access path |

### Tier 2: Aggregator + File Export Only

| # | Institution | Direct API | Aggregator (Plaid) | File Export | Manual | Notes |
|---|-------------|-----------|-------------------|-------------|--------|-------|
| 7 | **Relay** | ❌ No public API | ✅ Via Finicity (Mastercard) | ✅ CSV, QBO exports | ✅ | Relay integrates with Plaid and Yodlee for third-party access; native QuickBooks/Xero sync; CSV export of all sub-accounts |
| 10 | **Mercury** | ❌ No public API to individuals | ✅ Supported via Plaid | ✅ CSV (QuickBooks format, NetSuite format) | ✅ | Export via Documents & Data → Monthly CSV with pre-formatted accounting columns |
| 11 | **TD Bank** (Canada) | ❌ No public API | ✅ Supported via Plaid CA | ✅ CSV, OFX | ✅ | Standard Canadian bank; Plaid has Canadian coverage |
| 13 | **Ally Bank** | ❌ No public API | ✅ Full | ✅ CSV, OFX, QFX | ✅ | Well-supported by Plaid; OFX/QFX for Quicken integration |
| 14 | **J.P. Morgan Chase** | ❌ No public API | ✅ Full (balance + txns) | ✅ CSV, OFX, QFX | ✅ | Largest US bank; excellent Plaid coverage |

### Tier 3: Open Banking API (UK/EU/AU/IN)

| # | Institution | Direct API | Open Banking Standard | File Export | Manual | Notes |
|---|-------------|-----------|---------------------|-------------|--------|-------|
| 6 | **Starling Bank** | ✅ **Developers API** | ✅ PSD2 (UK Open Banking) | ✅ CSV, PDF | ✅ | Full developer API: `GET /api/v2/accounts/{accountUid}/balance` and `GET /api/v2/feed/account/{accountUid}/category/{categoryUid}` — personal access tokens available |
| 8 | **HDFC Bank** (India) | ❌ No public API | ✅ Account Aggregator (SEBI/RBI) | ✅ CSV from NetBanking | ✅ | India's Account Aggregator framework (Setu, Finvu) provides consent-based account data sharing; Zorivest could integrate via AA |
| 9 | **Macquarie Bank** (AU) | ❌ No public API | ✅ CDR (Consumer Data Right) | ✅ CSV, OFX | ✅ | Australia's CDR mandates Open Banking APIs from all ADIs; balance + transaction access |
| 12 | **Revolut** | ✅ **Open Banking API** | ✅ PSD2 | ✅ CSV, PDF | ✅ | Full PSD2 API: `GET /accounts/{accountId}/balances` and `GET /accounts/{accountId}/transactions`; also has Business API with personal access tokens |
| 15 | **IDFC First Bank** (India) | ❌ | ✅ Account Aggregator | ✅ CSV from NetBanking | ✅ | Similar to HDFC — accessible via India's AA framework |

---

## Integration Architecture

### Method 1: Manual Entry (Always Available — P0)

Every bank account in Zorivest must support manual balance updates and manual transaction entry. This is **non-negotiable** because:
- Some institutions will never have API access (small local banks, credit unions)
- Users may not want to share credentials
- Privacy-conscious traders want full control

**Implementation:**

```
GUI:
  Settings → Accounts → [Bank Name] → "Update Balance" button
    → Form: Balance amount, As-of date, Notes
  
  Transactions → "Add Manual Transaction" button
    → Form: Date, Description, Amount, Category, Account, Notes

MCP Tools:
  update_account_balance(account_id, balance, as_of_date, notes?)
  add_manual_transaction(account_id, date, description, amount, category?, notes?)
```

**Schema:**

```python
class BankAccount:
    id: str
    name: str                    # "Chase Business Checking"
    institution: str             # "chase"
    account_type: AccountType    # CHECKING, SAVINGS, CMA, MONEY_MARKET
    currency: str                # "USD"
    last_balance: Decimal
    last_balance_date: datetime
    balance_source: BalanceSource  # MANUAL, CSV_IMPORT, API_SYNC, PLAID
    is_primary: bool             # For net-worth rollup ordering

class BankTransaction:
    id: str
    account_id: str
    date: datetime
    description: str
    amount: Decimal              # Positive = inflow, Negative = outflow
    category: TransactionCategory  # DEPOSIT, WITHDRAWAL, TRANSFER, FEE, INTEREST, DIVIDEND, OTHER
    source: TransactionSource    # MANUAL, CSV_IMPORT, API_SYNC, PLAID
    reference_id: str?           # Dedup key from source system
    notes: str?
```

### Method 2: CSV/OFX File Import (Standard — P1)

Support importing bank statements exported from bank dashboards. Three format families:

| Format | Extension | Used By | Structure |
|--------|-----------|---------|-----------|
| **CSV** | `.csv` | All banks | Varies per institution — needs per-bank parsers |
| **OFX/QFX** | `.ofx`, `.qfx` | US banks (Fidelity, Schwab, Chase, Ally) | XML-based Open Financial Exchange — standardized schema |
| **QBO** | `.qbo` | QuickBooks exports (Mercury, Relay) | QuickBooks-specific XML format |

**Implementation:**

```python
class BankStatementParser(ABC):
    @abstractmethod
    def detect(self, file_path: str) -> bool:
        """Can this parser handle this file?"""
    
    @abstractmethod
    def parse(self, file_path: str) -> BankStatementResult:
        """Parse into standardized transactions + balance."""

class BankStatementResult:
    transactions: List[BankTransaction]
    closing_balance: Decimal?
    as_of_date: datetime?
    account_identifier: str?  # Last 4 digits, account number, etc.
```

**OFX is the ideal format** — it's structured XML with a standard schema used by Quicken, Moneydance, and GnuCash. Python's `ofxparse` and `ofxtools` libraries handle parsing. OFX contains:
- Account info (type, routing, last 4)
- Transaction list (date, amount, type, memo, FITID for dedup)
- Ledger balance + available balance with as-of timestamp

**CSV requires per-bank header detection** (reuse the same `CSVParser` architecture from broker imports):

| Bank | Key CSV Columns | Balance Included? |
|------|----------------|-------------------|
| Fidelity | `Date`, `Transaction`, `Name`, `Memo`, `Amount` | No (separate file) |
| Schwab | `Date`, `Type`, `Description`, `Withdrawal`, `Deposit`, `Balance` | ✅ Running balance |
| Chase | `Transaction Date`, `Post Date`, `Description`, `Category`, `Type`, `Amount`, `Memo` | No |
| Mercury | `Date`, `Description`, `Amount`, `Category` | ✅ In QBO format |
| Wealthfront | `Date`, `Description`, `Amount` | No |

### Method 3: Aggregator API (Plaid — P2/P3)

**Plaid** is the dominant bank data aggregator, covering 12,000+ institutions in US, Canada, UK, and EU. One integration covers the majority of banks from the research file.

**Plaid Products for Zorivest:**

| Product | Purpose | Zorivest Use |
|---------|---------|-------------|
| **Auth** | Account + routing numbers | Account identification |
| **Transactions** | Categorized transaction history (2+ years) | Bank transaction import |
| **Balance** | Real-time account balance | Balance sync |
| **Investments** | Brokerage holdings/transactions | Alternative to direct broker API |

**Plaid Architecture:**

```
User → Zorivest GUI → Plaid Link (embedded widget) → User authenticates with bank
                                                      ↓
Plaid returns access_token → Zorivest stores encrypted
                                                      ↓
Zorivest MCP tools call Plaid API:
  GET /accounts/balance/get    → Update account balance
  GET /transactions/sync       → Pull new transactions (webhook-driven)
```

**Pricing Consideration:** Plaid charges per-connection. For a desktop-first tool like Zorivest, this may be cost-prohibitive unless:
- Zorivest offers a paid tier with Plaid integration
- Or, the user provides their own Plaid developer credentials (free tier: 100 items)

**Alternative Aggregators:**
- **Finicity (Mastercard)** — Used by Relay; covers US/CA banks
- **Yodlee (Envestnet)** — Legacy aggregator; wider international coverage
- **Teller** — US-only; developer-friendly; real-time connections
- **MX** — Financial data platform with categorization engine

### Method 4: Direct Bank APIs (FinTech Banks Only — P2)

Only a handful of banks offer REST APIs accessible to individual users:

#### Wise API (Highest Value)

```
Base URL: https://api.wise.com
Auth: Personal API token (from Settings → API tokens)
Sandbox: https://api.wise-sandbox.com

Key Endpoints:
  GET /v4/profiles/{profileId}/balances
    → All currency balances (40+ currencies)
  
  GET /v1/profiles/{profileId}/balance-statements/{balanceId}/statement.json
    ?currency=USD&intervalStart=2025-01-01T00:00:00Z&intervalEnd=2025-02-01T00:00:00Z
    → Full transaction history with running balance

Zorivest MCP Tools:
  sync_bank_balance(bank="wise")         → GET /v4/profiles/{id}/balances
  import_bank_transactions(bank="wise")  → GET /v1/.../statement.json
```

#### Starling Bank API (UK Users)

```
Base URL: https://api.starlingbank.com/api/v2
Auth: Personal access token (from Developer settings)

Key Endpoints:
  GET /api/v2/accounts/{accountUid}/balance
    → Available balance, cleared balance, effective balance
  
  GET /api/v2/feed/account/{accountUid}/category/{categoryUid}
    ?changesSince=2025-01-01T00:00:00Z
    → Transaction feed with categories

Zorivest MCP Tools:
  sync_bank_balance(bank="starling")         → GET .../balance
  import_bank_transactions(bank="starling")  → GET .../feed
```

#### Revolut Open Banking API

```
Base URL: https://oba.revolut.com
Auth: PSD2 consent flow (OAuth 2.0 + eIDAS certificate)

Key Endpoints:
  GET /accounts/{accountId}/balances  → Balance
  GET /accounts/{accountId}/transactions  → Transactions

Note: Requires AISP (Account Information Service Provider) registration
      under PSD2 — complex for a desktop app. Better to use Plaid or TrueLayer
      as an intermediate aggregator for Revolut.
```

### Method 5: Open Banking Standards (Regional — P3)

| Standard | Region | Coverage | Complexity | Zorivest Approach |
|----------|--------|----------|------------|-------------------|
| **PSD2 / UK Open Banking** | UK, EU | All UK banks (CMA9 + challengers) | High (requires AISP registration) | Use **TrueLayer** or **Plaid** as intermediary |
| **CDR (Consumer Data Right)** | Australia | All ADIs (Macquarie, CBA, etc.) | High (requires CDR registration) | Use **Basiq** or **Frollo** as intermediary |
| **Account Aggregator** | India | All SEBI/RBI-registered FIs | Medium (via Setu or Finvu SDK) | Use **Setu AA** or **Finvu** as intermediary |

> **Key insight:** Zorivest should NOT directly implement Open Banking protocols. Instead, use regional aggregators (TrueLayer → UK/EU, Basiq → AU, Setu → India) that handle the regulatory complexity, and consume their simplified REST APIs.

---

## Recommended Priority Roadmap

| Phase | Feature | Effort | Coverage |
|-------|---------|--------|---------|
| **P0** | Manual balance update + manual transaction entry (GUI + MCP) | Low | 100% of all banks |
| **P1** | OFX/QFX file import (standardized format) | Medium | ~60% of US banks (Fidelity, Schwab, Chase, Ally) |
| **P1** | CSV file import with auto-detect (per-bank parsers) | Medium | ~90% of all banks |
| **P2** | Wise direct API integration | Low | Wise multi-currency (40+ currencies) |
| **P2** | Starling direct API integration | Low | UK market |
| **P3** | Plaid aggregator integration | High | 12,000+ institutions globally |
| **P3** | TrueLayer / CDR / AA aggregator stubs | High | UK/EU, Australia, India respectively |

---

## Insights from the Research File

### 1. Bank Accounts Are Not Just Storage — They're Trading Infrastructure

The research reveals that traders treat bank accounts as **active components of their trading system**, not passive savings. Key implications for Zorivest:

- **Balance tracking is time-critical:** Traders near the $25K PDT threshold need to see bank + brokerage balances combined in real-time
- **Transfer velocity matters:** Zorivest should track pending transfers between bank and brokerage as a "cash in transit" state
- **Multi-account architecture is standard:** The average trader in the research uses 2-3 bank accounts + 1-2 brokerages. Zorivest needs a "net worth dashboard" that aggregates all accounts

### 2. The Fidelity/Schwab "Walled Garden" Problem

Fidelity and Schwab (the top 2 institutions) are actively consolidating banking + brokerage into closed ecosystems. Their CMAs sweep idle cash into money market funds (SPAXX, etc.), blurring the line between "bank balance" and "investment balance."

**Zorivest implication:** The account model needs a `sweep_fund` field. When the user's "checking balance" is actually parked in SPAXX, Zorivest should:
- Track the money market fund balance as part of the CMA
- Include the yield earned on idle cash as a separate line item
- Show the combined CMA total (cash + sweep fund) on the dashboard

### 3. Multi-Currency Is a First-Class Requirement

Wise (Rank #4) and Revolut (#12) are used specifically because they hold **40+ currencies simultaneously**. A single Wise account might have USD, EUR, GBP, CHF, and SGD balances.

**Zorivest implication:**
- `BankAccount` should support `List[CurrencyBalance]` rather than a single `balance` field
- Currency conversion tracking is essential (shows FX costs as a separate expense category)
- The Wise API already returns per-currency balances — Zorivest should display these as sub-balances

### 4. Trading LLC Sub-Account Segmentation

Relay (#7) users create **up to 20 sub-accounts** to segment trading capital, tax reserves, data feed costs, and platform fees. Mercury (#10) users similarly segment by purpose.

**Zorivest implication:**
- Support a "parent account + sub-accounts" hierarchy
- Each sub-account has its own balance and transaction history
- Aggregation: parent account total = sum of all sub-accounts
- Tags/categories on sub-accounts: "Trading Capital," "Tax Reserve," "Operating Expenses," "Emergency Fund"

### 5. The Frozen Account Risk — Impact on Portfolio

The research's most alarming finding: **algorithmic account freezes** are increasingly common — especially for traders with high-frequency transfers. A frozen bank account means:
- No margin call coverage
- No new trade funding
- Vendor checks (data feeds, platform fees) bounce

**Zorivest implication:**
- Consider a "health status" indicator per account (Active / Frozen / Pending Review)
- When an account is marked frozen, Zorivest should alert the user that their effective buying power has decreased
- Track "time since last successful transaction" as a soft health signal

### 6. Tax Integration Is Mandatory for Trading LLCs

The research explicitly calls out that traders need **clean, auto-categorized, exportable** bank data for Schedule D, Form 8949, and wash-sale tracking. Banks that don't provide clean CSV/API data force manual statement transcription.

**Zorivest implication:**
- Bank transactions should feed into the Transaction Ledger (§9) for cost/income categorization
- Categories like `data_feed`, `platform_fee`, `margin_interest`, `deposit`, `withdrawal` from §9 should be available for bank transactions too — creating a unified ledger view
- Export: bank + brokerage transactions → combined CSV for tax accountant or TurboTax import

### 7. The "Cash in Transit" Gap

Traders complain about T+1 to T+3 ACH delays. During transit, money appears to be "missing" — debited from the bank but not yet credited to the brokerage. This is a real accounting gap.

**Zorivest implication:**
- Track **pending transfers** as a distinct asset class: `TransferInTransit`
- When a user initiates a transfer (manual or detected from bank transactions), create a pending record
- Auto-reconcile when the brokerage shows a matching deposit
- Show "Total Liquidity" = Bank Balance + Brokerage Balance + Cash in Transit

---

## Manual Entry Design — GUI + MCP

### GUI: Update Account Balance

```
┌── Update Balance ─────────────────────────┐
│                                           │
│  Account: [Chase Business Checking ▼]     │
│                                           │
│  Current Balance: $47,231.89              │
│  Last Updated: 2026-02-18 via Plaid       │
│                                           │
│  New Balance:    [$____________]           │
│  As of Date:     [2026-02-20]             │
│  Notes:          [Monthly reconciliation] │
│                                           │
│  [Cancel]                    [Update]     │
└───────────────────────────────────────────┘
```

### GUI: Add Manual Transaction

```
┌── Add Bank Transaction ───────────────────┐
│                                           │
│  Account: [Fidelity CMA ▼]               │
│                                           │
│  Date:        [2026-02-20]                │
│  Type:        [● Deposit  ○ Withdrawal]   │
│  Amount:      [$5,000.00]                 │
│  Description: [ACH from Chase]            │
│  Category:    [Transfer ▼]                │
│  Reference:   [Optional ref #]            │
│  Notes:       [Funding for AAPL trade]    │
│                                           │
│  [Cancel]                       [Save]    │
└───────────────────────────────────────────┘
```

### MCP Tool Definitions

```python
# Balance management
update_account_balance(
    account_id: str,
    balance: Decimal,
    as_of_date: str,           # ISO date
    currency: str = "USD",
    notes: str? = None
) -> AccountBalanceResult

# Manual transaction entry
add_bank_transaction(
    account_id: str,
    date: str,                 # ISO date
    amount: Decimal,           # Positive = inflow, negative = outflow
    description: str,
    category: str = "other",   # deposit, withdrawal, transfer, fee, interest, dividend, other
    reference_id: str? = None,
    notes: str? = None
) -> TransactionResult

# Bulk import from file
import_bank_statement(
    file_path: str,
    format: str = "auto",      # auto, csv, ofx, qfx, qbo
    account_id: str? = None,   # If not provided, detect from file
    bank: str? = None          # If CSV, specify bank for parser selection
) -> ImportResult

# Aggregator sync
sync_bank_account(
    account_id: str,
    provider: str = "plaid",   # plaid, wise_api, starling_api
    full_refresh: bool = False
) -> SyncResult
```

---

## Reference

- **Source:** [Trader Banking Preferences: 2025 Analysis](file:///p:/zorivest/_inspiration/import_research/Trader%20Banking%20Preferences_%202025%20Analysis.md)
- **Related:** [Build Plan Expansion Ideas](file:///p:/zorivest/_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §9 (Transaction Ledger & Fee Cataloging)
- **Aggregator docs:** [Plaid API](https://plaid.com/docs/), [Wise API](https://docs.wise.com/api-reference), [Starling API](https://developer.starlingbank.com/)
- **Date:** 2026-02-20
