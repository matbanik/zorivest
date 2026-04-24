# Discovery Phase  
As an AI agent starting from the user’s request, the first step is to **gather context**. I’d call the following MCP tools:  

- **`list_step_types`** – to see what step types are available (e.g. fetch, transform, compose, email) and their parameter schemas. This tells me if steps like “query DB” or “compose report” exist or are missing.  
- **`list_provider_capabilities`** – to discover what data providers (e.g. Yahoo Finance, Finnhub) are registered and find their documentation URLs. This gives me endpoints and required parameters for market data and news.  
- **`list_db_tables`** – to inspect the local encrypted database schema. I need to know what tables and columns exist (e.g. watchlist, trades, accounts) so I can write SQL queries or reference that data.  
- **`list_email_templates`** – to see existing templates and required variables. The default “Morning Check-In” template may already exist, which could guide variable naming.  

From these, I collect necessary information such as the user’s watchlist tickers (likely stored in a DB table), account balance fields, trade history schema, and any existing templates.  

**Gaps:** The architecture doc warns several capabilities are missing【21†L585-L589】. For example: there is currently *no* pipeline-integrated SQL query step or compose step (see “Query internal DB tables” and “Compose/merge data” missing in the capability matrix).  If `list_step_types` shows no `QueryStep` or `ComposeStep`, I cannot directly query the DB or merge data, which is a critical gap. The tools themselves (like `list_db_tables`) give schema but without a `QueryStep`, I can’t use that schema in the policy. Also, while `list_provider_capabilities` points to docs, those are just URLs – there’s no structured endpoint metadata (like a Swagger JSON), so understanding how to call Yahoo or Finnhub APIs may require manual web searches. These are points of friction to note.

# Template Authoring  
The report needs a Jinja2 template for the email body. I’d use the **`create_email_template`** tool to make it. The template must include placeholders for:  

- **`watchlist`** – a list of tickers or dict of ticker data (e.g. symbol, current price).  
- **`account_balances`** – e.g. a list of account names and balances.  
- **`recent_trades`** – a list of recent trade records (each with ticker, action, quantity, price, date, etc.).  
- **`top_news`** – a list of news items (title, source, link, summary or timestamp).  

A sketch of the Jinja2 template might be:
```
Subject: Morning Check-In for {{ date }}

Good morning! Here's your portfolio summary for {{ date }}:

- **Watchlist:**
{% for sym, data in watchlist.items() %}
  - {{ sym }}: ${{ data.price }} ({{ data.change_pct }}%)
{% endfor %}

- **Account Balances:**
{% for acct in account_balances %}
  - {{ acct.name }}: ${{ acct.balance }}
{% endfor %}

- **Recent Trades (last 24h):**
{% for trade in recent_trades %}
  - {{ trade.date }}: {{ trade.action }} {{ trade.qty }} {{ trade.ticker }} at ${{ trade.price }}
{% endfor %}

- **Top News:**
{% for news in top_news %}
  - [{{ news.headline }}]({{ news.url }}) ({{ news.source }})
{% endfor %}
```
For `required_variables`, I’d declare: `date`, `watchlist`, `account_balances`, `recent_trades`, `top_news`. The **`sample_data_json`** should include realistic dummy data, e.g.:
```json
{
  "date": "2026-04-23",
  "watchlist": {"AAPL": {"price": 172.34, "change_pct": 1.2}, "MSFT": {"price": 298.10, "change_pct": -0.5}},
  "account_balances": [{"name": "Brokerage", "balance": 12500.75}, {"name": "Retirement", "balance": 50230.00}],
  "recent_trades": [{"date": "2026-04-22", "action": "BUY", "qty": 50, "ticker": "AAPL", "price": 170.50}],
  "top_news": [{"headline": "Tech Stocks Rally", "url": "http://...", "source": "Reuters"}]
}
```
This lets the emulator render a realistic preview of the email.  

**Template security:** We assume a *sandboxed Jinja2 environment* (as recommended by best practices) to render untrusted templates【4†L13-L21】. The Jinja sandbox restricts attribute access (for example `func.__code__` is blocked【4†L13-L21】) and prevents arbitrary code execution. However, the sandbox is not foolproof – templates can still consume excessive resources or crash if they loop infinitely【4†L39-L46】. So we rely on the sandbox to stop unsafe operations, and we ensure we pass *only necessary data objects* (simple dicts/lists) into the template【4†L51-L56】.  

# Policy Composition  
Next I author the policy JSON. I outline step by step, justifying each choice:  

1. **Fetch Watchlist** (type=`QueryStep` or equivalent): Query the local DB for the user’s watchlist tickers. *Why:* We need the tickers to know what market data to fetch. Parameters: table=`watchlist`, columns=`symbol`. If `QueryStep` is not yet implemented (gap C), this is a major friction. We may have to simulate by using an existing step (e.g. fetch CSV or skip this and hardcode symbols?).  

2. **Fetch Market Data** (type=`fetch` or similar, perhaps one step per provider or a combined fetch): Call Yahoo Finance API for quotes. *Why:* To get current prices for the watchlist tickers. Params: `provider: "YahooFinance"`, `endpoint: "quote"` (or `'chart'`), query params `symbols: [tickers], fields: [price, change_pct]`. We may call Yahoo’s unofficial JSON endpoints (e.g. `query1.finance.yahoo.com/v7/finance/quote`)【21†L483-L489】. We must specify the watchlist symbols here.  

3. **Fetch Account Balances** (type=`query` or `fetch`): Query the local DB for account balances. *Why:* To include in report. Params: table=`accounts`, columns=`name, balance`.  

4. **Fetch Recent Trades** (type=`query`): Query the local DB for trades in the last day. Params: table=`trades`, filter=`date >= today-1 day`, columns=`date, action, qty, ticker, price`.  

5. **Fetch Market News** (type=`fetch`): Call Finnhub’s news endpoint. *Why:* To get top market news. We can use the general market news endpoint (`news/news`, category like `"general"` or `"top"`). Params: `provider: "Finnhub"`, `endpoint: "news"`, e.g. query `category=general`. Alternatively, use `company-news` for specific tickers (but “top news” suggests general category). Must include API key (Finnhub requires a token)【15†L65-L69】.  

6. **Transform Steps**: We might need to normalize data formats. For example, convert raw JSON outputs into a consistent structure for templating. If available, use a `transform` step for each output to select/rename fields (e.g. pick only price and percent change).  

7. **Compose Data** (type=`ComposeStep`): Merge all fetched data into one context object. *Why:* The email template expects all variables in one namespace. E.g. `{ date: ..., watchlist: {...}, account_balances: [...], recent_trades: [...], top_news: [...] }`. This step might be a literal “compose” step that assembles these into a single JSON. If `ComposeStep` (Gap D) isn’t implemented, I might hack it by using a `transform` with constant JSON.  

8. **Send Email** (type=`SendEmailStep`): Reference the created template by name, use context variables to populate it, and schedule send at 7am EST daily. Params: `template_name: "Morning Check-In"`, `to: user@example.com`, `from: noreply@zorivest.com`, `send_time: "07:00"`.  

Each step’s `id` should be meaningful (e.g. `fetch_yahoo`, `fetch_news`, etc.) to help debug errors. I must also define any **policy-level variables** (Gap F) – for example, `schedule: "0 7 * * *"` if using cron syntax, or an `email_time` parameter. The schema might let me put `variables: { schedule: "cron daily 7am" }`.  

**Friction points:** The schema may be limiting. For example, if the policy JSON has no native support for list slicing or iteration, the agent must ensure fetched arrays can be looped over in Jinja (so `watchlist` should be a dict or list, not a single string). The policy format for multi-field queries or for “filter by date” might be limited. Also, referencing outputs between steps requires the correct `{ "ref": "ctx.step_id.field" }` syntax, which can be error-prone. Gap G (assertion gates) isn’t implemented, so we lack a way to assert e.g. “ensure account balance > 0”.  

# Validation Loop  
I would then call the **`emulate_policy(policy_json)`** tool. I expect a structured JSON response like:
```
{
  valid: false,
  phase: "VALIDATE",
  errors: [...],
  warnings: [...],
  mock_outputs: { ... },
  template_preview: "<Rendered HTML preview>"
}
```
If everything is correct, `valid` will be `true` after the RENDER phase.

Common errors might be:
- **Missing variable**: e.g. template expects `recent_trades` but no step produced it. The error should indicate the template name, missing variable name, and perhaps the phase (VALIDATE). For self-correction, an ideal error object would be structured like:
  ```json
  {
    "phase": "VALIDATE",
    "step_id": null,
    "error_type": "MissingVariable",
    "variable": "recent_trades",
    "message": "Template 'Morning Check-In' requires variable 'recent_trades' not found in context outputs."
  }
  ```
  This tells me exactly what to add.  
- **Invalid SQL**: If a query step had bad SQL, the error might be:
  ```json
  {
    "phase": "SIMULATE",
    "step_id": "fetch_trades",
    "error_type": "SQLParseError",
    "sql": "SELECT ...",
    "message": "Syntax error at 'WHEE': did you mean 'WHERE'?"
  }
  ```
  With such detail, I can fix typos or unsupported syntax.

I’d iterate: adjust the policy or template, then run `emulate_policy` again. The mock outputs allow me to see sample data structure. The **`template_preview`** field (if returned) would show me the rendered email HTML/Markdown for the sample data, letting me spot formatting issues. The structured errors need to include the step ID, variable name, or JSON path; without structure it’s hard for the agent to know where to fix things. (This addresses the question on error schema – ideally errors are an array of objects with fields like `phase`, `step_id`, `field`, `message`.)

# Provider Discovery  
For Yahoo Finance and Finnhub, I’d examine their docs:

- **Yahoo Finance:** There is *no official* public Yahoo Finance API key or documentation【21†L585-L589】. The user must rely on unverified endpoints or scraping. For quotes, blogs show an unofficial endpoint like `query2.finance.yahoo.com/v8/finance/chart/{ticker}?period1=...&period2=...`【21†L483-L489】 or `query1.finance.yahoo.com/v7/finance/quote?symbols=`. However, these aren’t documented by Yahoo. The scrapfly guide confirms “no formal API or API key” and says data access is typically via scraping or unofficial libraries【21†L585-L589】【21†L591-L594】. In practice, I can try to use the chart API for historical OHLC (as in 【21†L483-L489】) or rely on a JSON news API (if any). For example, Yahoo pages have news under `https://finance.yahoo.com/quote/XYZ/news`. The incomplete/missing info is a worry: I may need to test endpoints interactively.

- **Finnhub:** The Finnhub docs (v1) are clear. The base URL is `https://finnhub.io/api/v1` and *all* requests require an API key as a `token` parameter or `X-Finnhub-Token` header【15†L65-L69】. Endpoints include `/stock/profile2`, `/quote`, `/company-news`, and `/news/news`. In particular, “company-news” returns company-specific news with `symbol`, `from`, `to` params, and “news/news” returns market news by category【15†L87-L90】. For example, GET `/api/v1/stock/symbol?exchange=US` lists symbols, `/api/v1/company-news?symbol=AAPL&from=2026-04-22&to=2026-04-23` would give Apple news. I have enough info to call `/company-news` (with symbols from the watchlist) or `/news/news?category=general` for broad news. The missing pieces are practical examples and authentication. The agent will need the user’s Finnhub API key (probably stored in the MCP’s secret store). Overall, Finnhub’s structured docs mean composing a `fetch` step is straightforward once the key is handled【15†L65-L69】【15†L87-L90】.  

In summary, the Finnhub docs provide endpoint schemas (so we can build a correct HTTP request), whereas Yahoo’s data must rely on discovered endpoints and perhaps scraping. Without structured metadata, the agent has to guess or trial-and-error the Yahoo calls.

# Edge Cases  
- **Empty Watchlist:** If the user’s watchlist is empty, the `fetch` step for quotes would have no symbols. The policy should handle this gracefully: maybe skip the Yahoo fetch (skip condition?), and the template loop `{% for %}` would just render nothing. Ideally, we’d assert or default that case (e.g. “No watchlist tickers”). Right now, lacking assertion gates (Gap G), the agent may need to include logic: e.g. a `skip` step or an `if` in the template (`{% if watchlist %}…{% else %}No tickers{% endif %}`) to avoid errors.  

- **Provider API Down:** If Yahoo or Finnhub is unreachable at 7am, the emulator can’t fully simulate that, but the real pipeline should handle it. We might catch failures by checking HTTP status in a `transform` or have a retry mechanism. The agent should at least note this risk. Without an emulator phase for runtime errors, we assume the pipeline platform retries or logs errors.  

- **Missing Template Variable:** If the template references a var that no step produces, `emulate_policy` will flag it (likely in the VALIDATE phase). The agent would then need to add a step that produces that variable or remove the reference. A robust emulator error (as above) would make this easy.  

- **Feature Request (“add earnings calendar”):** Suppose later the user wants to include earnings events. The agent would need to fetch from an earnings API and include in the template. It might involve adding one new fetch step (`provider: Finnhub`, `endpoint: "calendar/earnings"`, etc) and adding `earnings` to the template context and required_variables. The rest of the policy (the existing steps) could remain mostly intact. Possibly only the Compose step needs to include the new data. So it’s a localized change, not a full rewrite: add one step and modify the compose/template. This shows the benefit of separating the template – we can update it and the policy step without rewriting everything.

# Specific Questions  

1. **MCP Tool Completeness:** The 10 proposed tools cover many bases (step discovery, DB introspection, template CRUD, policy emulation). For writing a new policy, they’re mostly sufficient. However, a few additions would smooth the workflow:
   - **`get_db_row_samples`**: Instead of just listing table schemas, a tool to fetch example rows (for building sample_data_json or debugging queries) would help.
   - **`execute_fetch_simulated`**: A tool to test a provider API call outside the full policy would let the agent quickly see response shape.
   - **`get_environment_vars`**: To inspect things like time zones or user profile (e.g. confirm user’s email or watchlist ID).
   - **`list_policies`** (or `get_policy`): To inspect existing policies for examples or reuse.
   - **`explain_error`**: Given an emulator error, a tool that summarizes it in plain terms or suggests fixes (though ideally the error schema is enough).
   These would significantly aid iterative development.  

2. **Error Message Quality:** For an agent to self-correct quickly, each error should include: which *phase* failed, the *step or template name*, the *field or variable* involved, and a concise message. For example, errors might be objects like:  
   ```
   { "phase": "VALIDATE",
     "step": "render_email",
     "error": "MissingVariable",
     "details": { "template": "Morning Check-In", "variable": "top_news" },
     "message": "Variable 'top_news' is required by the template but was not produced by any step."
   }
   ```
   Ideally, use a JSON structure (not just text) so the agent can parse it. Also include stack-like paths (e.g. `policy.steps[3].sql`) or schema paths. A warning might have similar fields. This structured schema is crucial: with it the agent can pinpoint and fix issues in 1–2 iterations. (For instance, QWED’s SQL analysis example flags the offending SQL snippet【7†L80-L89】 – a similar approach should be used here.)

3. **Template DB vs Inline:** From an agent’s viewpoint, storing templates in the DB means **one extra step** (create and reference by name) rather than embedding the template in the policy JSON. This is some overhead. However, it allows reusing templates across policies and editing them independently. In practice, having a **library of templates** is valuable (the agent or user can pick or update a template without editing JSON). The trade-off is small friction when authoring: the agent must call `create_email_template`, then use the returned `template_id` or `name` in the policy. Given that policies can get long, separating template source helps manage complexity. Overall, the reuse and clarity justifies the extra CRUD step, especially since we can `preview_email_template` to test it. In short, it adds a bit of boilerplate for the agent but improves maintainability.

4. **Provider `docs_url` vs Structured Metadata:** Agents would *prefer* structured metadata. Relying on a URL forces the agent to browse and parse free-form docs (which we just did), which is brittle. If the registry instead provided a JSON schema for each endpoint (e.g. expected path, query params, request/response schema), the agent could automatically fill the `fetch` step params. The **minimum needed** would be: endpoint path, HTTP method, list of parameters (names, types, required/optional), and a sample response schema or example. Even a Swagger/OpenAPI JSON would suffice. Without that, the agent is forced to search the web or experiment, which is error-prone. So yes, we should push for structured API metadata (or at least JSON examples in the docs) to avoid manual searches.

5. **Default Template Strategy:** A pre-loaded “Morning Check-In” template helps jumpstart the agent. It should be a **semi-complete template** that covers all sections (watchlist, balances, trades, news) with placeholder syntax. A complete, ready-to-use template means the agent mostly needs to supply data; it could customize language. A too-minimal skeleton would require the agent to write more from scratch (which is more work). For ease of development, providing a **full template with all sections and placeholder variables** is best. The agent can then adjust phrasing or add/remove fields, but it doesn’t have to invent the whole structure. This reduces mistakes (we know such a template works once) and saves time.

# Open Questions / Limitations  
- The architecture currently lacks an actual `QueryStep`, so this policy is partly theoretical until Gap C is resolved.  
- Real error outputs from the emulator were not tested (since we couldn’t run the emulator), so our error schema design is hypothetical.  
- We assumed certain endpoints for Yahoo Finance (charts API) based on blogs; in reality, the agent might discover different URLs or use an unofficial library like `yfinance`.  
