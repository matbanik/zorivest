## Executive synthesis (2025–2026, “direct retail developer API” focus)

Across your 10 claims, the pattern is consistent with the current US landscape: **very few large US consumer financial institutions offer a “public, direct-to-retail-developer” API** for account/transaction access. Instead, access tends to be (a) **broker-specific developer programs** (e.g., E\*TRADE), (b) **enterprise/partner agreements** (often via aggregators like Plaid), or (c) **special-purpose portals** (e.g., IRS tax pro programs, payments APIs like PayPal).

Your verdicts are largely aligned with the cited sources, with the biggest overstatements being **“only via X”** assertions (Fidelity, Chase) and the **AmEx EU/US availability** claim which isn’t supported by the sources provided.

---

## Verdict table (with source-grounded rationale)

| # | Claim | Verdict | What the sources *do* and *don’t* establish (2025–2026) |
|---:|---|---|---|
| 1 | **E\*TRADE uses OAuth 1.0a with HMAC‑SHA1, tokens expire at midnight ET daily** | **CONFIRMED (nuance)** | E\*TRADE documentation specifies **OAuth 1.0a** and **HMAC‑SHA1** for signing, and states the **access token expires at the end of the current calendar day (US Eastern time)**; it also notes an additional behavior where a token can become **“inactivated” after ~2 hours of inactivity**, requiring renewal. Source: E\*TRADE auth docs. ([apisb.etrade.com](https://apisb.etrade.com/docs/api/authorization/get_access_token.html?utm_source=openai)) |
| 2 | **Fidelity has NO direct retail developer API — only via Plaid/SnapTrade** | **PARTIALLY CORRECT** | The “**no public retail developer API**” portion is supported by Fidelity’s official support presence stating it does **not offer a public API**. ([reddit.com/r/fidelityinvestments](https://www.reddit.com/r/fidelityinvestments/comments/1afwcfa?utm_source=openai)) However, “**only via Plaid/SnapTrade**” is **not proven** by the provided sources; SnapTrade’s page implies **partner access exists**, but it’s **vendor marketing**, not an authoritative Fidelity policy statement. ([snaptrade.com](https://snaptrade.com/brokerage-integrations/fidelity-api?utm_source=openai)) |
| 3 | **Chase/JPMorgan has NO direct retail API — Plaid only with 2025 fee agreement** | **PARTIALLY CORRECT** | JPMorganChase confirms a **renewed data access agreement with Plaid** (Sept 16, 2025) that includes a **pricing structure**—that part is solid. ([jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai)) But “**Plaid only**” is **too strong**: the sources show Plaid is an important channel and that Chase has pursued secure API access for aggregators/apps broadly, but they do **not** prove Plaid is the *exclusive* route. ([media.chase.com](https://media.chase.com/news/plaid-signs-data-agreement-with-jpmc?utm_source=openai)) |
| 4 | **American Express developer portal is NOT available to individual US developers — EU/PSD2 only for direct, US must use Plaid/MX** | **INCORRECT / UNCONFIRMED (based on provided sources)** | The provided sources establish that an **AmEx developer entry point exists** (“Amex for Developers”). ([graph.americanexpress.com](https://graph.americanexpress.com/?utm_source=openai)) They **do not** establish the specific restrictions claimed (EU/PSD2-only, not available to US individuals, or “must use Plaid/MX” in the US). Therefore, as stated, this claim is **not validated** by the cited materials. |
| 5 | **Coinbase uses OAuth 2.0 + JWT (CDP keys), legacy API keys deprecated Feb 2025** | **PARTIALLY CORRECT** | Coinbase confirms **legacy API keys expired in February 2025**. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/coinbase-app/authentication-authorization/legacy-keys?utm_source=openai)) The auth model is **mixed in the claim**: **CDP API keys** are used to generate **JWT bearer tokens** for server-to-server calls. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/get-started/authentication/cdp-api-keys?utm_source=openai)) Separately, Coinbase consumer app flows can involve **OAuth2** (“Sign in with Coinbase”), but that is **API-surface dependent** rather than a single combined universal model. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/coinbase-app/introduction/changelog?utm_source=openai)) |
| 6 | **TradingView paper trading data stored in browser localStorage with no external API** | **INCORRECT / NOT ESTABLISHED** | No official source is provided to support the **localStorage** assertion. Additionally, the blanket “**no external API**” framing is misleading in practice because TradingView supports **exporting paper trading history to CSV**, indicating at least an export mechanism (and suggesting server-side account history exists). The provided citation here is third-party, but it contradicts “localStorage-only.” ([traderinsight.pro](https://traderinsight.pro/blog/tradingview-broker-added?utm_source=openai)) |
| 7 | **Plaid covers 12,000+ US institutions with free sandbox + pay-as-you-go pricing** | **CONFIRMED (with wording precision)** | JPMorganChase states Plaid “connects to **over 12,000 financial institutions**” (not explicitly “US-only” in that quote—rather multi-region). ([jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai)) Plaid pricing/docs confirm **Pay as You Go** and that **Sandbox usage is always free**. ([plaid.com/pricing](https://plaid.com/pricing/?utm_source=openai)) |
| 8 | **PayPal REST API uses OAuth 2.0 client credentials with /v1/reporting/balances endpoint** | **CONFIRMED** | PayPal’s Transaction Search API documents **GET `/v1/reporting/balances`** (“List all balances”) and indicates security via **OAuth2**. ([developer.paypal.com](https://developer.paypal.com/docs/api/transaction-search/v1/?utm_source=openai)) The “client credentials” detail is consistent with standard PayPal REST app patterns, and the key points (OAuth2 + endpoint) are explicitly documented. |
| 9 | **Citizens Bank launched Open Banking API in March 2025** | **CONFIRMED** | Citizens’ official newsroom release dated **03/27/2025** announces the “**Citizens Open Banking API**.” ([investor.citizensbank.com](https://investor.citizensbank.com/about-us/newsroom/latest-news/2025/2025-03-27.aspx?utm_source=openai)) |
| 10 | **IRS has no retail taxpayer API — only tax professional e‑Services** | **PARTIALLY CORRECT (needs scoping)** | IRS e-Services documentation describes **online tools for tax professionals** and an **API Client ID** process within those professional/authorized programs. ([irs.gov](https://www.irs.gov/tax-professionals/e-services-online-tools-for-tax-professionals?utm_source=openai)) From the provided sources, it’s reasonable to say there is **no general-purpose “retail taxpayer personal finance” API**. However, the claim should be scoped precisely (the IRS has APIs, but they are oriented around **authorized professional programs**, not open consumer finance aggregation). |

---

## Deep reasoning & implications for a desktop personal finance app (Windows/macOS)

### 1) “Direct retail developer APIs” are the exception, not the rule
Your dataset shows a clear divide:
- **Brokerage developer program exists and is direct**: E\*TRADE provides direct OAuth-based access with explicit token rules. ([apisb.etrade.com](https://apisb.etrade.com/docs/api/authorization/get_access_token.html?utm_source=openai))
- **Large incumbent institutions often do not provide a public API**: Fidelity’s public stance (per its support presence) is “no public API.” ([reddit.com/r/fidelityinvestments](https://www.reddit.com/r/fidelityinvestments/comments/1afwcfa?utm_source=openai))
- **Access may occur via commercial agreements**: JPMorganChase’s agreement with Plaid (including pricing) underscores that data access is frequently **contractual and metered** rather than “sign up as an individual dev.” ([jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai))

**Design implication:** A desktop PFM app typically needs an **aggregation strategy** (Plaid-like) for broad bank coverage, plus **direct connectors** only where official retail APIs exist (E\*TRADE, PayPal, Coinbase surfaces depending on your use case).

---

### 2) “Only via X” claims are usually the weakest—because exclusivity is hard to prove
Both Fidelity and Chase claims illustrate the same logic error:
- You can often confirm **a channel exists** (Plaid agreement; SnapTrade partnership marketing).
- It’s much harder (and usually incorrect) to assert **it’s the only channel**, unless the institution explicitly states exclusivity.

**How to phrase robustly (based on your sources):**
- Fidelity: “No public API; partner integrations may exist.” ([reddit.com](https://www.reddit.com/r/fidelityinvestments/comments/1afwcfa?utm_source=openai), [snaptrade.com](https://snaptrade.com/brokerage-integrations/fidelity-api?utm_source=openai))
- Chase: “Aggregator access is supported; Plaid agreement and pricing confirmed.” ([jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai))

---

### 3) Authentication and token lifecycle differences matter operationally (especially on desktop)

**E\*TRADE** is a concrete example where token behavior directly impacts UX and background refresh:
- Token expires **end of day ET**, plus potential “inactivation” after **~2 hours idle**. ([apisb.etrade.com](https://apisb.etrade.com/docs/api/authorization/get_access_token.html?utm_source=openai))
- This implies you should engineer:
  - A **scheduled renewal** before day-end ET (if you need uninterrupted connectivity),
  - A **graceful re-auth path** when the token becomes inactive after inactivity.

**PayPal** is comparatively straightforward:
- OAuth2-secured endpoint for balances exists and is documented. ([developer.paypal.com](https://developer.paypal.com/docs/api/transaction-search/v1/?utm_source=openai))

**Coinbase** requires careful API-surface selection:
- Legacy keys ended Feb 2025. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/coinbase-app/authentication-authorization/legacy-keys?utm_source=openai))
- CDP uses **JWT bearer tokens from CDP API keys** for server-to-server. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/get-started/authentication/cdp-api-keys?utm_source=openai))
- OAuth2 applies to other Coinbase consumer app integrations depending on the feature. ([docs.cdp.coinbase.com](https://docs.cdp.coinbase.com/coinbase-app/introduction/changelog?utm_source=openai))

---

### 4) Avoid unverified implementation assumptions (TradingView localStorage is a good example)
Your claim #6 illustrates a common research pitfall: inferring storage architecture without authoritative documentation. With the provided sources:
- There is **no official confirmation** of localStorage.
- There is evidence of **CSV export**, contradicting “no external mechanism” in practice. ([traderinsight.pro](https://traderinsight.pro/blog/tradingview-broker-added?utm_source=openai))

**Engineering implication:** If you want TradingView paper-trade history in a PFM, the defensible integration is an **import workflow (CSV)** unless/until TradingView publishes an official API for that dataset.

---

## Source-backed corrections to improve the original claims (more precise wording)

- **Plaid scope:** Prefer “connects to **over 12,000 financial institutions**” (multi-region), rather than “12,000+ US institutions.” ([jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai))
- **Fidelity/Chase channels:** Replace “only via Plaid/SnapTrade” / “Plaid only” with “no public retail API identified in sources; aggregator/partner access exists (e.g., Plaid agreement).” ([reddit.com](https://www.reddit.com/r/fidelityinvestments/comments/1afwcfa?utm_source=openai), [jpmorganchase.com](https://www.jpmorganchase.com/newsroom/press-releases/2025/jpmc-plaid-renewed-data-access-agreement?utm_source=openai))
- **AmEx availability:** With the provided sources, the strongest supported statement is simply: “AmEx has a developer gateway, but US individual availability / PSD2-only limitations are not established here.” ([graph.americanexpress.com](https://graph.americanexpress.com/?utm_source=openai))

---

## If you want the next step (implementation guidance)
If you share your target feature set (accounts/transactions, investments/positions, crypto balances, payments, tax docs) and whether you require **write access** (trading, transfers) vs **read-only**, I can translate the above into a **connector strategy** for a desktop app: recommended auth flow per provider, token refresh scheduling, re-auth UX, and where an aggregator is effectively required (given the lack of public APIs).