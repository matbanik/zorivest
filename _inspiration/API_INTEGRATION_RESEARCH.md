 # Zorivest — API Integration Research

> Investigation of API capabilities for account balance retrieval, transaction data, and trade information from financial service providers relevant to Zorivest.
>
> **Research date**: February 9, 2026
> **Method**: Web search (Tavily advanced + DuckDuckGo) across official developer documentation
> **Validation**: Anthropic Claude research with web search (see validation notes marked with 🔍)
> **Second validation**: OpenAI GPT-5.2 via Pomera generate (see notes marked with 🤖)
> **Third validation**: OpenAI GPT deep research with source citations (see notes marked with 📚)

---

## Summary Matrix

| Service | Has Public API? | Auth Method | Balance | Transactions | Trades | Direct or Aggregator | Priority |
|---------|:-:|---|:-:|:-:|:-:|---|:-:|
| **PayPal** | ✅ Yes | OAuth 2.0 (Client Credentials) | ✅ | ✅ | N/A | Direct | P1 |
| **Coinbase** | ✅ Yes | OAuth 2.0 + JWT (CDP keys) | ✅ | ✅ | ✅ | Direct | P1 |
| **E\*Trade** | ✅ Yes | OAuth 1.0a | ✅ | ✅ | ✅ | Direct | P0 |
| **Fidelity** | ⚠️ Limited | OAuth (via SnapTrade/Plaid) | ✅ via aggregator | ✅ via aggregator | ❌ | Aggregator only | P2 |
| **Chase (JPMorgan)** | ⚠️ Limited | OAuth (via Plaid) | ✅ via Plaid | ✅ via Plaid | N/A | Aggregator (Plaid) | P2 |
| **Acorns** | ⚠️ Partner only | OAuth 2.0 (Partner API) | ✅ via Plaid | ✅ via Plaid | ❌ | Aggregator (Plaid) | P3 |
| **American Express** | ✅ Yes | OAuth 2.0 (PSD2 certified) | ✅ | ✅ | N/A | Direct (EU/PSD2) | P2 |
| **Citizens Bank** | ✅ Yes | Open Banking API + Plaid | ✅ | ✅ | N/A | Direct + Plaid | P2 |
| **Insperity** | ⚠️ Customer only | API key (developer portal) | ⚠️ Payroll | ⚠️ Payroll | N/A | Direct (employer) | P3 |
| **IRS (irs.gov)** | ⚠️ Tax Pros only | API Client ID (e-Services) | N/A | N/A | N/A | Third-party (TaxStatus) | P3 |
| **TradingView** | ⚠️ Broker API | Password/OAuth Bearer | ✅ Paper | ✅ Paper | ✅ Paper | Broker Integration API | P2 |

---

## Detailed Findings

### 1. PayPal (paypal.com)

**API Status**: ✅ **Full public REST API available**

**Authentication**:
- **Method**: OAuth 2.0 Client Credentials
- **Flow**: Exchange Client ID + Client Secret for Bearer access token
- **Endpoint**: `POST /v1/oauth2/token`
- **Requirement**: PayPal Business account for production; personal sandbox available for testing
- **Token format**: Bearer token in `Authorization` header

**Available API Calls**:
| Endpoint | What it returns |
|----------|----------------|
| `GET /v1/reporting/balances` | All account balances (up to 3 years history) |
| `GET /v1/reporting/transactions` | Transaction history with filters (date range, pagination) |
| `GET /v2/payments/captures/{id}` | Individual payment details |
| `GET /v1/billing/subscriptions` | Subscription/recurring payment info |

**Key Notes**:
- Full sandbox environment available for testing
- OpenAPI specs published on GitHub (`paypal/paypal-rest-api-specifications`)
- Balances may take up to 3 hours to appear in the API
- Supports filtering by date range, pagination, balance-affecting records only

**Integration Effort**: 🟢 Low — well-documented, standard OAuth 2.0, Python SDK available

---

### 2. Coinbase (coinbase.com)

**API Status**: ✅ **Full public API available (Coinbase Developer Platform / CDP)**

**Authentication**:
- **Method 1**: OAuth 2.0 (for third-party access to user accounts)
  - Authorization: `login.coinbase.com/oauth2/auth`
  - Token exchange: `login.coinbase.com/oauth2/token`
  - Token refresh: supported
  - Revocation: `login.coinbase.com/oauth2/revoke`
- **Method 2**: CDP API Keys with JWT (for own account)
  - ES256 JWT signing with private key
  - Legacy API keys deprecated as of Feb 2025

**Available API Calls**:
| Endpoint | What it returns |
|----------|----------------|
| `GET /v2/accounts` | List all crypto wallets/accounts |
| `GET /v2/accounts/{id}` | Balance for specific account |
| `GET /v2/accounts/{id}/transactions` | Transaction history |
| `GET /v2/accounts/{id}/buys` | Buy orders |
| `GET /v2/accounts/{id}/sells` | Sell orders |
| Advanced Trade APIs | Full trading: orders, fills, portfolios |
| `GET /v2/exchange-rates` | Current exchange rates |

**Key Notes**:
- OAuth2 enforces portfolio-level trade access (as of May 2025)
- Advanced Trade APIs available for algorithmic trading
- Supports deposits/withdrawals, send/receive crypto
- Travel rule compliance required for EU users
- Full sandbox available

**Integration Effort**: 🟢 Low — excellent documentation, OAuth 2.0 standard, active development

---

### 3. E\*Trade (etrade.com) — Now Morgan Stanley

**API Status**: ✅ **Full public REST API available**

**Authentication**:
- **Method**: OAuth 1.0a (three-legged)
- **Flow**:
  1. Get Request Token
  2. Redirect user to E\*Trade authorization page
  3. User authorizes → receives verification code
  4. Exchange for Access Token
- **Requirement**: E\*Trade account required; apply for Individual or Vendor API key
- **Key types**: Individual key (own accounts only) or Vendor key (third-party access)

**Available API Calls**:
| Endpoint | What it returns |
|----------|----------------|
| `GET /v1/accounts/list` | List all accounts |
| `GET /v1/accounts/{accountIdKey}/balance` | Account balance, cash, margin |
| `GET /v1/accounts/{accountIdKey}/portfolio` | Positions with 70+ data fields |
| `GET /v1/accounts/{accountIdKey}/transactions` | Transaction history |
| `POST /v1/accounts/{accountIdKey}/orders/place` | Place trade orders |
| `GET /v1/market/quote/{symbols}` | Real-time market quotes |
| `GET /v1/accounts/{accountIdKey}/alerts` | Account alerts |

**Key Notes**:
- Extremely detailed position data (70+ fields: price, P&L, Greeks for options, etc.)
- Full order placement support (equities, options, mutual funds)
- Sandbox environment available for testing
- Individual key works across all your E\*Trade accounts
- Must sign API Developer Agreement

**Integration Effort**: 🟡 Medium — OAuth 1.0a is more complex than 2.0, but well-documented. Most feature-rich brokerage API.

---

### 4. Fidelity (fidelity.com)

**API Status**: ⚠️ **No direct public retail API — available only through aggregators**

**Authentication**:
- **Direct API**: Not available to individual retail developers
- **Via SnapTrade**: OAuth (user authorizes via Fidelity login within SnapTrade widget)
- **Via Plaid**: OAuth (Open Banking data access agreement with Fidelity)
- **WorkplaceXchange**: API portal for employer/institutional clients only

**Available Through Aggregators**:
| Via | What's available |
|-----|-----------------|
| **SnapTrade** | Account balances, positions (read-only). NO trading support |
| **Plaid** | Account balances, transaction history, identity verification |
| **WorkplaceXchange** | 401(k) balances, payroll integrations (employer-only) |

**Key Notes**:
- Fidelity deliberately does not offer a direct retail developer API
- SnapTrade is the primary aggregator for investment account data
- 2FA is supported through aggregator connections
- Users can disconnect at any time from Fidelity settings
- WorkplaceXchange API marketplace launching with HR/payroll + balance inquiries

**Integration Effort**: 🟡 Medium — requires SnapTrade or Plaid subscription; no direct access

---

### 5. Chase / JPMorgan (chase.com)

**API Status**: ⚠️ **No direct retail API — Plaid only (with fees)**

**Authentication**:
- **Via Plaid**: OAuth (user authorizes through Chase login flow within Plaid Link)
- **Direct API**: Not available to retail developers (institutional API via Morgan Stanley Developer Portal for institutional clients only)

**Available Through Plaid**:
| Data type | Available |
|-----------|-----------|
| Account balances | ✅ |
| Transactions | ✅ |
| Identity | ✅ |
| Income verification | ✅ |

**Key Notes**:
- JPMorgan and Plaid reached a data-sharing agreement in 2025 where Plaid pays JPMorgan for data access
- JPMorgan reported 1.89 billion API calls from aggregators in June 2025 alone — only 13% were customer-initiated
- Chase is actively pushing back on unfettered data scraping; fees now apply
- No direct developer API for individual retail customers
- This is a policy decision, not a technical limitation

**Integration Effort**: 🟡 Medium — requires Plaid subscription; works well but adds cost layer

---

### 6. Acorns (acorns.com)

**API Status**: ⚠️ **Partner API only — not publicly available**

**Authentication**:
- **Partner API**: OAuth 2.0 (restricted to approved partners)
- **Via Plaid**: Standard Plaid OAuth flow for balance/transaction data

**Available**:
| Method | What's available |
|--------|-----------------|
| **Acorns Partner API** | Account data for approved third-party apps (OAuth + Partner APIs) |
| **Via Plaid** | Balance checking, transaction monitoring, identity verification |

**Key Notes**:
- Developer docs at `developer.acorns.com` — but access requires partnership approval
- Third-party apps can see Acorns as a linkable institution through Plaid
- Not all features are available through all third-party platforms
- Users may need account/routing numbers for some integrations
- 2FA can cause issues with some third-party connections

**Integration Effort**: 🔴 High — requires partnership approval or Plaid; no self-serve API

---

### 7. Insperity (insperity.com)

**API Status**: ⚠️ **Developer portal exists — restricted to customers/employers**

**Authentication**:
- **Developer Portal**: `developer.insperity.com` — API key-based authentication
- **Via Finch**: Unified employment API (covers 200+ HRIS/payroll systems including Insperity)

**Available API Categories** (from Insperity Developer Portal):
| Category | What's available |
|----------|-----------------|
| **Payroll & Tax** | Employee compensation, general ledger post-payroll |
| **HRIS** | Employee information transfer |
| **Benefits** | Benefits enrollment data |

**Key Notes**:
- The API is primarily for employer-side integrations (not individual employees)
- Individual employees cannot directly access their 401(k) balance via Insperity API
- For personal balance tracking: use Plaid (Insperity 401(k) may be through Fidelity or Vanguard as custodian)
- Finch unified API provides a single integration point for Insperity + 200 other payroll systems
- Best approach: identify the actual 401(k) custodian (often Fidelity/Vanguard) and integrate with that

**Integration Effort**: 🔴 High — employer-only API; individual users should target the 401(k) custodian instead

---

### 8. American Express (americanexpress.com)

**API Status**: ⚠️ **Developer portal exists but US direct access is NOT available to individual developers**

**🔍 Validation Update — Two Distinct API Programs (commonly confused)**:

#### EU/PSD2 API (Europe Only)
- **Purpose**: Regulatory compliance with Payment Services Directive 2
- **Products**: Confirmation of Funds, Account Information (AIS), Payment Initiation (PIS)
- **Access**: Licensed Third-Party Providers (TPPs) registered with EU financial regulators only
- **Relevance to Zorivest**: **None** — US-based app

#### US Open Banking API (Partner-Only)
- **Purpose**: Consumer-permissioned data sharing
- **Method**: Internally developed API using encrypted connections and OAuth2
- **Access**: **Only available to approved financial service provider partners** — NOT individual developers
- **Key quote**: "American Express will only share your financial data with a financial service provider upon your request"

**Practical Access Path for Zorivest**:
```
Your App → Plaid → Amex (Assets, Balance, Transactions) ✅
Your App → MX → Amex (Account Financials API, OAuth2) ✅
Your App → Direct Amex API → ❌ NOT available to individual developers
```

**Available Through Aggregators**:
| Via | What's available |
|-----|-----------------|
| **Plaid** | Assets, balance, transactions ✅ |
| **MX** | Account Financials API via formal OAuth2 agreement with Amex ✅ |
| **Direct API** | ❌ Not available to individual developers |

**Key Notes**:
- The developer portal at `developer.americanexpress.com` exists but is for certified partners only
- Plaid and MX both have formal data-sharing agreements with American Express
- MX has a particularly strong Amex partnership via direct OAuth2 API
- For US retail customers, **aggregator is the only path**

**Integration Effort**: 🟢 Low via Plaid (already planned as primary aggregator)

---

### 9. Citizens Bank (citizensbankonline.com)

**API Status**: ✅ **Open Banking API launched March 2025 + Plaid support**

**Authentication**:
- **Citizens Open Banking API**: OAuth 2.0 (customer authorizes via Citizens login)
- **Via Plaid**: Standard Plaid OAuth flow

**Available**:
| Data type | Available |
|-----------|-----------|
| Account balances | ✅ (Open Banking API + Plaid) |
| Transactions | ✅ (Open Banking API + Plaid) |
| Identity verification | ✅ (Plaid) |
| Income verification | ✅ (Plaid) |

**Key Notes**:
- Citizens launched their own Open Banking API in March 2025
- Allows customers to view bank account balances, transactions within third-party apps
- Dual access: direct Open Banking API OR via Plaid aggregator
- Designed for budgeting apps, accounting platforms, and similar financial tools

**Integration Effort**: 🟢 Low — new Open Banking API is developer-friendly; Plaid as alternative

---

### 10. IRS (irs.gov)

**API Status**: ⚠️ **Limited APIs — primarily for tax professionals, not individual taxpayers**

**Authentication**:
- **IRS e-Services API**: Requires API Client ID application
  - Contact Help Desk at 866-255-0654 for TIN matching, Transcript Delivery System
  - Publication 5718 for IRIS (Information Returns Intake System) A2A specs
- **IRS Identity**: ID.me verification for IRS account access (consumer-facing)

**Available IRS APIs** (for tax professionals):
| Service | What's available | Access |
|---------|-----------------|--------|
| **Transcript Delivery System (TDS)** | Tax return transcripts | Tax professionals only |
| **TIN Matching** | Verify taxpayer ID numbers | Tax professionals only |
| **IRIS (A2A)** | E-file information returns (1099s, etc.) | Tax professionals/transmitters |
| **Secure Object Repository (SOR)** | Document exchange | Tax professionals only |

**Third-Party Tax Data APIs** (alternatives for retail use):
| Service | What it does | Auth |
|---------|-------------|------|
| **TaxStatus** (`developer.taxstatus.com`) | Taxpayer consent → official IRS data (income, filings, liens, levies) | OAuth consent flow |
| **Plaid Income** | Income verification from IRS data | Plaid OAuth |
| **TurboTax / H&R Block** | Tax estimation — no API for external developers | N/A |

**Key Notes for Tax Estimator**:
- IRS does NOT provide a direct API for individual taxpayers to pull their own tax data programmatically
- Tax professionals can access transcripts via TDS API
- **TaxStatus.com** is the most relevant third-party: lets taxpayers consent to share IRS data with apps
- For Zorivest's Tax Estimator: compute estimates locally from trade data rather than pulling from IRS
- Tax rates/brackets are public data that can be hardcoded with annual updates
- Wash sale detection, capital gains categorization should be computed from the app's own trade database

**Integration Effort**: 🔴 High for IRS direct; 🟡 Medium via TaxStatus; 🟢 Low for local computation

**Recommended approach**: Build the Tax Estimator as a **local calculator** using the app's own trade data + published IRS tax brackets. Don't attempt to pull data FROM the IRS.

---

### 11. TradingView (tradingview.com)

**API Status**: ⚠️ **Broker Integration API — designed for brokers, not retail developers**

**Authentication**:
- **Password Bearer**: User enters credentials on TradingView, sent to broker backend
- **OAuth 2.0 Bearer**: Server-to-server OAuth flow
- **ServerOAuth2Bearer**: For data feed authentication

**TradingView Broker API** (broker implements this, TradingView consumes it):
| Endpoint | What it does |
|----------|-------------|
| `/accounts` | List trading accounts |
| `/state` | Account balance, equity, margin |
| `/orders` | Order management (place, modify, cancel) |
| `/positions` | Open positions |
| `/executions` | Filled orders / trade history |
| `/instruments` | Available instruments |
| `/mapping` | Symbol name mapping between TradingView and broker |

**Paper Trading**:
- TradingView has a built-in Paper Trading account for simulated trading
- Paper Trading uses TradingView's own virtual broker implementation
- **No external API to access Paper Trading data** — it lives inside TradingView's frontend
- Paper trading positions/P&L are not exposed via any public REST endpoint

**🔍 Validation Update — Paper Trading Storage**:
- Paper trading data is stored **in the browser's localStorage** — not on TradingView's servers
- TradingView has explicitly stated: "We don't have an API that gives access to data as of now, but we are planning to add it in the future"
- This is a fundamental architectural limitation, not merely a missing feature

**Workarounds for Paper Trading Data** (ranked by reliability):

| Method | Reliability | Automation | Notes |
|--------|:----------:|:----------:|-------|
| **CSV export (Pro account)** | ⭐⭐⭐ | Semi-manual | Requires TradingView Pro (~$13-60/mo) |
| **Manual entry with smart defaults** | ⭐⭐⭐ | Manual | Pre-populate from market data API |
| **Webhook alerts** | ⭐⭐ | Real-time | Fires on strategy signals — can log new paper trades but not historical |
| **Browser DevTools extraction** | ⭐ | Semi-auto | Fragile — breaks on TradingView updates |

**Recommended Approach for Zorivest**:
1. **Track A**: CSV Import Pipeline — `TradingView Pro → CSV Export → Zorivest Import Module → SQLCipher`
2. **Track B**: Manual Entry — quick form with symbol pre-population from market data
3. **Track C (future)**: Webhook receiver — TradingView webhook alerts can notify Zorivest of new paper trades in real-time; design the ingestion layer to accept webhook payloads for future readiness

**For Price Data** (separate from Broker API):
- `tradingview_ta` Python library — technical analysis data (closing prices, indicators)
- This is what the existing WST Trade Logger uses for price fetching
- Screener: `america` exchange, daily interval
- No official REST API for real-time price data (WebSocket charting library requires license)

**Key Notes**:
- The Broker Integration API is designed for **brokers to implement**, not for retail developers to consume
- TradingView acts as the **frontend**; the broker provides the **backend API**
- To access Paper Trading data, you'd need to be a registered broker partner with TradingView
- **Do not wait for an API that may never come** — build CSV import now

**Integration Effort**: 🔴 High for Broker API (requires partnership); 🟢 Low for price data via `tradingview_ta`; 🟡 Medium for CSV import pipeline

---

## Aggregator Services (Cross-Cutting)

Several institutions don't offer direct APIs but work through aggregators:

### Plaid (plaid.com) — Recommended Primary Aggregator

- **Coverage**: Chase, Fidelity, Acorns, Citizens Bank, Amex, and 12,000+ US institutions
- **Auth**: OAuth 2.0 via Plaid Link (drop-in UI component)
- **Data**: Balances, transactions, identity, income, investments (varies by institution)
- **Python SDK**: `plaid-python`
- **Connected users**: 100+ million through 7,000+ apps

**🔍 Validated Pricing (2025)**:

| Tier | Cost | Best For |
|------|------|----------|
| **Free/Sandbox** | $0 (200 Production API calls + unlimited Sandbox) | Development & testing |
| **Pay-as-you-go** | No minimum, per-use billing | Personal use (5 accounts ≈ $0–15/mo) |
| **Growth** | ~$500+/month (annual commitment) | Small user base (100+ users) |
| **Enterprise** | Custom pricing | Volume discounts, SLAs |

Billing models vary by product:
- **One-time fee**: ~$0.30–$1.00 per connected account (e.g., Auth/verification)
- **Subscription**: Monthly per active connected account (e.g., Transactions)
- **Per-request**: Flat fee per successful API call

> ⚠️ Plaid does NOT publish a public price list. Exact pricing is only visible after applying for Production access. Estimates above from community reports.

### 🔍 Aggregator Comparison (Validated)

| Aggregator | Institutions | Chase | Fidelity | Amex | Citizens | Acorns | Dev Experience | Best For |
|-----------|:-----------:|:-----:|:--------:|:----:|:--------:|:------:|:--------------:|----------|
| **Plaid** | 12,000+ US | ✅ | ✅ read-only | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ | Best default — covers all 5 targets |
| **Yodlee** | 20,000+ global | ✅ | ✅ deep brokerage | ✅ | ✅ | ⚠️ varies | ⭐⭐⭐ | Deep investment data (lot-level cost basis, options) |
| **MX** | Moderate US | ✅ | ⚠️ limited | ✅ formal partnership | ⚠️ varies | ❓ | ⭐⭐⭐⭐ | Data enrichment/categorization; strong Amex partnership |
| **Finicity** | Moderate US | ✅ | ⚠️ limited | ✅ | ⚠️ varies | ❓ | ⭐⭐⭐ | Credit decisioning (Mastercard backing); complaints about dropped connections |

**Recommendation**: **Plaid as primary**. It covers all five target institutions, has the best developer experience, and Acorns itself uses Plaid internally (guaranteeing strong connectivity). Consider **Yodlee** only if deeper Fidelity brokerage data is needed (lot-level cost basis, options positions), but monitor its stability post-2025 acquisition by Symphony Technology Group.

### SnapTrade (snaptrade.com)
- **Coverage**: Fidelity, and many other brokerages
- **Auth**: OAuth (user authorizes within SnapTrade widget)
- **Focus**: Investment accounts specifically (positions, balances)
- **Limitation**: No trading support for Fidelity

### Finch (tryfinch.com)
- **Coverage**: Insperity + 200 other HRIS/payroll systems
- **Auth**: OAuth
- **Focus**: Employment data (payroll, benefits, employee info)

---

## Authentication Methods Summary

| Method | Used By | Complexity | Security |
|--------|---------|:----------:|:--------:|
| **OAuth 2.0 (Client Credentials)** | PayPal | 🟢 Low | ✅ High |
| **OAuth 2.0 (Authorization Code)** | Coinbase, Amex, Citizens, Acorns, Plaid | 🟡 Medium | ✅ High |
| **OAuth 1.0a (Three-Legged)** | E\*Trade | 🟡 Medium | ✅ High |
| **JWT (ES256)** | Coinbase (CDP keys) | 🟡 Medium | ✅ Very High |
| **API Key** | Insperity (employer) | 🟢 Low | ⚠️ Medium |
| **IRS e-Services** | IRS (tax pros) | 🔴 High | ✅ Very High |

---

## Recommended Integration Priority for Zorivest

### Phase 1 (P0) — Build First
| Service | Why | How |
|---------|-----|-----|
| **E\*Trade** | Primary broker (IBKR already done via `ibapi`) | Direct REST API, OAuth 1.0a |
| **Interactive Brokers** | Already in spec | Direct via `ibapi` library |

### Phase 2 (P1) — Build Soon
| Service | Why | How |
|---------|-----|-----|
| **PayPal** | Common payment account | Direct REST API, OAuth 2.0 |
| **Coinbase** | Crypto portfolio tracking | Direct REST API, OAuth 2.0 |

### Phase 3 (P2) — Build Next
| Service | Why | How |
|---------|-----|-----|
| **Plaid** (covers Chase, Fidelity, Citizens, Acorns, Amex) | Single integration for 5+ institutions | Plaid API + Link widget |
| **TradingView** (price data only) | Already using `tradingview_ta` | Existing library |
| **American Express** | Direct API available (PSD2) | OAuth 2.0 via developer portal |

### Phase 4 (P3) — Build Later
| Service | Why | How |
|---------|-----|-----|
| **Insperity** | 401(k) — identify actual custodian first | Via custodian API or Plaid |
| **IRS** | Tax Estimator doesn't need IRS API | Local computation from trade data |
| **TaxStatus** | Optional: verify computed estimates | TaxStatus API (if needed) |

---

## Key Architectural Decision

**Plaid as the universal fallback**: Rather than building 10+ individual integrations, use **Plaid** as the aggregator layer for all banking/credit/investment accounts that don't have a direct API. This covers Chase, Fidelity, Citizens Bank, Acorns, Amex, and thousands of others through a single integration.

**Direct integrations** should only be built for:
1. **Interactive Brokers** (already planned via `ibapi` — trade execution + live data)
2. **E\*Trade** (full REST API with trading support)
3. **Coinbase** (excellent API, crypto-specific features)
4. **PayPal** (common account, simple OAuth 2.0)

**American Express**: Do NOT attempt direct API access — route through Plaid exclusively. The Amex developer portal is for certified partners only.

**TradingView Paper Trading**: Build a CSV import pipeline now. Do not wait for an API that may never come. Design webhook receiver for future readiness.

**Tax Estimator**: Compute locally from trade data + published IRS tax brackets. Do NOT attempt to pull data from IRS directly.

**OAuth Token Security**: Use Authorization Code + PKCE for all OAuth 2.0 flows. Store tokens in SQLCipher with app-level encryption. Store the SQLCipher passphrase in the OS keychain (Windows DPAPI / macOS Keychain / Linux libsecret). Implement Refresh Token Rotation.

---

## 🔍 OAuth Token Storage in SQLCipher (Validated Best Practices)

For a local-first encrypted desktop app, the industry-standard approach is **defense in depth**:

```
┌─────────────────────────────────────────────────────────────┐
│                     ZORIVEST DESKTOP APP                     │
│                                                              │
│  ┌──────────────┐    ┌─────────────────────────────────┐    │
│  │ OAuth Client  │───→│ Token Manager                    │    │
│  │ (PKCE Flow)   │    │  • Stores encrypted tokens       │    │
│  └──────────────┘    │  • Handles rotation               │    │
│                       │  • Enforces lifetime policies     │    │
│                       └──────────┬──────────────────────┘    │
│                                  │                            │
│                       ┌──────────▼──────────────────────┐    │
│                       │ SQLCipher Database                │    │
│                       │  • AES-256 full-DB encryption    │    │
│                       │  • Token table with app-level    │    │
│                       │    column encryption (optional)   │    │
│                       └──────────┬──────────────────────┘    │
│                                  │                            │
│                       ┌──────────▼──────────────────────┐    │
│                       │ OS Keychain / Credential Store    │    │
│                       │  • Stores SQLCipher passphrase   │    │
│                       │  • Windows: DPAPI / Cred Manager │    │
│                       │  • macOS: Keychain Services      │    │
│                       │  • Linux: libsecret / GNOME      │    │
│                       └─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Checklist**:
- ✅ Use **Authorization Code Flow with PKCE** for all OAuth 2.0 providers (IETF-recommended for desktop apps)
- ✅ Use **Refresh Token Rotation (RTR)** — on every refresh, store new token and invalidate old one
- ✅ **Never hardcode** SQLCipher passphrase in source code — store in OS keychain
- ✅ Optional **app-level column encryption** for tokens (defense in depth beyond SQLCipher)
- ✅ Request **minimum scopes** — only `read` for aggregator data; trading scopes for E\*Trade only if enabled

**Token Lifetime Guidelines**:

| Token Type | Recommended Lifetime | Notes |
|-----------|---------------------|-------|
| Access Token | 15–60 minutes | Limits damage if intercepted |
| Refresh Token | 7–14 days max | Balance security vs UX |
| E\*Trade Token | Until midnight ET | Enforced by E\*Trade; cannot extend overnight |

**Token Storage Schema**:
```sql
CREATE TABLE oauth_tokens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,          -- 'etrade', 'plaid', 'coinbase', etc.
    account_id      TEXT,                   -- Provider-specific account identifier
    access_token    BLOB NOT NULL,          -- App-level encrypted
    refresh_token   BLOB,                   -- App-level encrypted (NULL for OAuth 1.0a)
    token_type      TEXT DEFAULT 'bearer',  -- 'bearer' or 'oauth1'
    expires_at      INTEGER,               -- Unix timestamp
    scope           TEXT,
    oauth1_secret   BLOB,                  -- For E*Trade OAuth 1.0a token secret
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL,
    rotation_id     TEXT UNIQUE             -- UUID for rotation tracking
);
```

---

## 🔍 Cross-Cutting Architecture (Validated)

```
┌─────────────────────────────────────────────────────────────┐
│                    ZORIVEST SERVICE LAYER                     │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │ E*Trade    │  │ Plaid      │  │ TradingView           │  │
│  │ Adapter    │  │ Adapter    │  │ Import Adapter        │  │
│  │ (OAuth1.0a)│  │ (OAuth2)   │  │ (CSV/Manual/Webhook)  │  │
│  └──────┬─────┘  └──────┬─────┘  └────────┬──────────────┘  │
│         │               │                  │                 │
│  ┌──────▼───────────────▼──────────────────▼──────────────┐  │
│  │              TOKEN MANAGER / AUTH SERVICE                │  │
│  │  • PKCE flow orchestration                              │  │
│  │  • Token rotation & lifecycle                           │  │
│  │  • OAuth 1.0a signature generation (E*Trade)            │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────────┐  │
│  │              SQLCipher DATABASE                          │  │
│  │  • Tokens, transactions, accounts, positions            │  │
│  │  • AES-256 full-DB + Argon2id key derivation            │  │
│  │  • Passphrase in OS Keychain                            │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow Summary**:

| Source | Auth Method | Data Types | Sync Frequency |
|--------|-----------|------------|:-------------:|
| **E\*Trade** | OAuth 1.0a (direct) | Positions, orders, balances, trades | Daily (token expires midnight ET) |
| **Interactive Brokers** | ibapi library | Trades, balances, executions | Real-time (connected) |
| **PayPal** | OAuth 2.0 (direct) | Balances, transactions | On-demand |
| **Coinbase** | OAuth 2.0 (direct) | Crypto balances, trades, transactions | On-demand |
| **Chase** | Plaid OAuth2 | Balances, transactions | Every 4–6 hours |
| **Fidelity** | Plaid OAuth2 | Positions, balances, transactions | Every 4–6 hours |
| **Amex** | Plaid → Amex OAuth2 | Balances, transactions, assets | Every 4–6 hours |
| **Citizens Bank** | Plaid OAuth2 | Balances, transactions | Every 4–6 hours |
| **Acorns** | Plaid OAuth2 | Positions, balances | Every 4–6 hours |
| **TradingView** | CSV import / manual | Paper trade history | On-demand (user-initiated) |

**Key Risks & Mitigations**:

| Risk | Probability | Impact | Mitigation |
|------|:----------:|:------:|-----------|
| E\*Trade migrates to OAuth 2.0 | Low | Medium | Adapter pattern isolates auth logic |
| Plaid price increases | Medium | Low–Med | Free tier sufficient for personal use |
| TradingView never ships API | High | Low | CSV import + manual entry covers the gap |
| Yodlee instability post-acquisition | Medium | Low | Plaid is primary; Yodlee only supplemental |
| SQLCipher key compromise via memory dump | Low | High | Clear sensitive memory after use; `mlock()` on Unix |
| Amex drops aggregator support | Very Low | Medium | Amex actively expanding open banking partnerships |

---

## 🤖 OpenAI GPT-5.2 Validation Results

Independent validation of 10 key claims using OpenAI research (February 9, 2026):

| # | Claim | OpenAI Verdict | Notes / Corrections |
|:-:|-------|:-:|---|
| 1 | E\*Trade: OAuth 1.0a, HMAC-SHA1, midnight ET expiry | **PARTIALLY CORRECT** | OAuth 1.0a + HMAC-SHA1 confirmed. Midnight ET token expiry is not universally documented as a stable rule — may vary by token type/flow. Our web search found E\*Trade docs referencing this, but treat with caution. |
| 2 | Fidelity: No direct retail API, aggregator only | **PARTIALLY CORRECT** | Mostly true for consumers. Fidelity participates in data-sharing/open-finance programs and has institutional/partner integrations — "aggregator only" is slightly too absolute. For Zorivest (individual developer), aggregator remains the only practical path. |
| 3 | Chase: No direct retail API, Plaid only | **INCORRECT** (nuance) | Chase supports consumer-permissioned data via multiple channels/partners — not exclusively Plaid. However, for an individual developer, Plaid remains the most accessible path. Other options include MX and Finicity. |
| 4 | Amex: US dev portal NOT for individuals | **PARTIALLY CORRECT** | Generally true for consumer account data. However, Amex has developer offerings for payments/merchant/partner programs. For balance/transaction access specifically, aggregator (Plaid/MX) is correct path. |
| 5 | Coinbase: OAuth 2.0 + JWT, legacy keys deprecated Feb 2025 | **INCORRECT** (per OpenAI) | OpenAI notes Coinbase uses API keys as primary auth for some products, not universally OAuth 2.0 + JWT. However, our web search found official Coinbase docs confirming OAuth 2.0 for third-party access and CDP JWT keys for own-account access. Legacy key deprecation was documented in Coinbase's Jan 2025 changelog. **Assessment: Our original research is more accurate than OpenAI's general knowledge here.** |
| 6 | TradingView: Paper trading in localStorage, no API | **INCORRECT** (per OpenAI) | OpenAI notes TradingView has webhooks/alerts and broker integrations, making "no external API" too absolute. **Fair correction** — we should note webhooks exist. However, for paper trading *data retrieval*, there is genuinely no API. Our workaround tracks (CSV + webhook) already account for this. |
| 7 | Plaid: 12,000+ institutions, free sandbox | **PARTIALLY CORRECT** | Institution count is a marketing figure that varies. Free sandbox and pay-as-you-go pricing confirmed. |
| 8 | PayPal: OAuth 2.0, /v1/reporting/balances | **PARTIALLY CORRECT** | OAuth 2.0 confirmed. The exact `/v1/reporting/balances` endpoint is product-specific — our web search found it in PayPal's OpenAPI specs on GitHub, so this is accurate for reporting API access. |
| 9 | Citizens Bank: Open Banking API March 2025 | **INCORRECT** (per OpenAI) | OpenAI could not confirm this specific launch. However, our web search found a Citizens Bank press release from March 27, 2025 at `investor.citizensbank.com` confirming the launch. **Assessment: Our original research is correct — OpenAI's training data may not include this event.** |
| 10 | IRS: No retail taxpayer API, tax pros only | **PARTIALLY CORRECT** | Directionally correct. Some limited IRS APIs exist for approved partners and taxpayer-facing online services, but for practical purposes, individual developers cannot access IRS data. |

### Synthesis: Where OpenAI Disagrees with Our Research

**Three claims where OpenAI GPT-5.2 marked us INCORRECT:**

1. **Chase "Plaid only"** → Fair correction. Chase works with multiple aggregators (Plaid, MX, Finicity), not exclusively Plaid. Updated recommendation: Plaid remains our primary choice but is not the only option.

2. **Coinbase auth model** → Our web search data (from official Coinbase developer docs, Jan-May 2025 changelog) is more current than OpenAI's general knowledge. We maintain our original assessment: OAuth 2.0 for third-party, CDP JWT for own-account, legacy keys deprecated.

3. **Citizens Bank Open Banking API** → Our web search found the actual press release. OpenAI's training data likely doesn't cover this March 2025 event. We maintain our original assessment.

**Key takeaway**: Web search research (Tavily) produced more current data than OpenAI's training data for 2025 events. OpenAI was valuable for identifying overly absolute claims (Chase "only Plaid", TradingView "no API at all") that needed nuance.

---

## 📚 OpenAI GPT Deep Research Validation (with Source Citations)

Third-round validation using OpenAI deep research with web search and source citations. Key findings with authoritative sources:

### Verdict Summary

| # | Claim | GPT Research Verdict | Source |
|:-:|-------|:-:|---|
| 1 | E\*Trade: OAuth 1.0a, HMAC-SHA1, midnight ET | **CONFIRMED (nuance)** | Token expires end of calendar day ET + can become "inactivated" after ~2 hours idle. Source: [apisb.etrade.com](https://apisb.etrade.com/docs/api/authorization/get_access_token.html) |
| 2 | Fidelity: No direct retail API | **PARTIALLY CORRECT** | "No public API" confirmed via Fidelity support. "Only via Plaid/SnapTrade" is vendor marketing — other partner channels may exist. Source: [reddit.com/r/fidelityinvestments](https://www.reddit.com/r/fidelityinvestments/comments/1afwcfa) |
| 3 | Chase: No direct retail API, Plaid only | **PARTIALLY CORRECT** | Renewed Plaid agreement (Sept 16, 2025) with pricing confirmed. But "Plaid only" is too strong — Chase supports multiple aggregator channels. Source: [jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement) |
| 4 | Amex: EU/PSD2 only, US must use Plaid | **INCORRECT / UNCONFIRMED** | AmEx developer gateway exists at `graph.americanexpress.com`. Sources do NOT establish PSD2-only restriction or US individual unavailability. Source: [graph.americanexpress.com](https://graph.americanexpress.com) |
| 5 | Coinbase: OAuth 2.0 + JWT, legacy deprecated | **PARTIALLY CORRECT** | Legacy keys expired Feb 2025 ✅. Auth model is API-surface dependent: CDP keys → JWT for server-to-server; OAuth2 for consumer app flows. Source: [docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/get-started/authentication/cdp-api-keys) |
| 6 | TradingView: localStorage, no external API | **INCORRECT / NOT ESTABLISHED** | No official source confirms localStorage. CSV export exists, contradicting "no external mechanism." Source: [traderinsight.pro](https://traderinsight.pro/blog/tradingview-broker-added) |
| 7 | Plaid: 12,000+ institutions, free sandbox | **CONFIRMED** | "Over 12,000 financial institutions" (multi-region, not US-only). Free sandbox + pay-as-you-go confirmed. Source: [plaid.com/pricing](https://plaid.com/pricing/) |
| 8 | PayPal: OAuth 2.0, /v1/reporting/balances | **CONFIRMED** | GET `/v1/reporting/balances` ("List all balances") documented with OAuth2 security. Source: [developer.paypal.com](https://developer.paypal.com/docs/api/transaction-search/v1/) |
| 9 | Citizens Bank: Open Banking API March 2025 | **CONFIRMED** | Official newsroom release dated 03/27/2025. Source: [investor.citizensbank.com](https://investor.citizensbank.com/about-us/newsroom/latest-news/2025/2025-03-27.aspx) |
| 10 | IRS: No retail taxpayer API | **PARTIALLY CORRECT** | No general-purpose retail API. IRS has APIs oriented around authorized professional programs. Needs precise scoping. Source: [irs.gov](https://www.irs.gov/tax-professionals/e-services-online-tools-for-tax-professionals) |

### Key Corrections Applied to Our Research

**1. E\*Trade token "inactivation" — NEW finding:**
- Beyond the midnight ET expiry, tokens can become **"inactivated" after ~2 hours of inactivity**, requiring renewal via `/oauth/renew_access_token`
- **Engineering implication**: Implement scheduled token renewal before day-end ET AND a graceful re-auth path for idle timeout
- Source: E\*Trade auth docs ([apisb.etrade.com](https://apisb.etrade.com/docs/api/authorization/get_access_token.html))

**2. American Express — developer gateway at `graph.americanexpress.com`:**
- GPT research found an AmEx developer entry point at `graph.americanexpress.com` (not the previously cited `developer.americanexpress.com`)
- The specific restrictions we claimed (EU/PSD2-only, not available to US individuals) are **not established by authoritative sources**
- **Updated recommendation**: Amex has a developer gateway; US individual availability is unclear. Use Plaid as the practical path, but acknowledge the direct portal exists and may offer access for certain use cases.

**3. TradingView localStorage claim — retracted:**
- No official source confirms paper trading data is in localStorage
- CSV export mechanism exists, which contradicts "no external mechanism"
- **Updated recommendation**: Drop the localStorage assertion. State: "No public API for paper trading data retrieval. CSV export available via TradingView Pro."

**4. Plaid scope — precision correction:**
- "12,000+ institutions" is multi-region (not US-only)
- Prefer: "connects to over 12,000 financial institutions globally"

**5. Coinbase auth — surface-dependent clarification:**
- Auth model varies by API surface:
  - **CDP API keys → JWT bearer tokens** for server-to-server (own account)
  - **OAuth 2.0** for consumer app integrations (third-party access)
- Not a single combined model — it's API-surface dependent

### Meta-Insight: "Only via X" Claims Are the Weakest

The GPT research identified a systematic pattern in our document: **exclusivity claims ("only via Plaid", "aggregator only") are the hardest to prove and most likely to be wrong.** You can confirm a channel exists, but rarely prove it's the ONLY channel.

**Recommended phrasing pattern:**
- ❌ "Only via Plaid" → ✅ "No public retail API identified; aggregator access exists (e.g., Plaid agreement confirmed)"
- ❌ "Aggregator only" → ✅ "No direct retail developer API; partner/aggregator integrations available"

### Pomera MCP Diagnostics Note

Pomera diagnostics revealed all AI provider API keys (Anthropic, OpenAI, Google, etc.) show as **"placeholder key"** — not configured. This explains why `research` actions with web search timeout (invalid API keys → no response → timeout). The earlier `generate` call that succeeded may have used a different routing. API keys need to be configured in Pomera's settings GUI for AI tools to work reliably from Cline.

---

## Questions Still to Answer

| # | Question |
|---|----------|
| 1 | Do you have accounts at all 11 services, or only some? Which are active? |
| 2 | For Fidelity — is this a brokerage account, IRA, or 401(k)? (Changes which aggregator to use) |
| 3 | Is Plaid's pricing acceptable? (~$0.30/connection/month for production) |
| 4 | For Insperity — is your 401(k) custodied at Fidelity, Vanguard, or elsewhere? |
| 5 | Do you need real-time balance updates, or is daily/on-demand sufficient? |
| 6 | For TradingView Paper Trading — is exporting CSV from TradingView an acceptable workaround? |
| 7 | Would you consider using a unified aggregator (Plaid) for ALL non-broker accounts to simplify integration? |