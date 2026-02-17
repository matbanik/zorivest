# Market Tools Widget — GUI Architecture Documentation

> **Purpose**: Complete UI specification for the Market Tools configuration widget.  
> **Audience**: Developers reimplementing this GUI in any language/framework.  
> **Date**: 2026-02-07  

---

## 1. High-Level Architecture

The Market Tools widget is a **two-level tabbed interface** for configuring market data API providers. It lives inside a parent application's notebook as a tab called **"Market Tools"**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Parent Application Notebook                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌─────┐                       │
│  │ Tab 1    │ │ Tab 2    │ │ Market Tools │ │ ... │                       │
│  └──────────┘ └──────────┘ └──────┬───────┘ └─────┘                       │
│                                   │                                        │
│  ┌────────────────────────────────▼────────────────────────────────────────┐│
│  │                    Market Tools Tab Content                             ││
│  │                                                                        ││
│  │  [Title]  "Market Data API Configuration"  (bold, 14pt)                ││
│  │  [Desc]   "Configure API keys and settings for market data providers"  ││
│  │                                                                        ││
│  │  ┌──────────────────────────────────────────────────────────────────┐  ││
│  │  │              MarketToolsWidget (inner notebook)                  │  ││
│  │  │  ┌───────────────┬───────────┬─────────┬─────────────┬─── ...  │  ││
│  │  │  │ Alpha Vantage │Polygon.io │ Finnhub │ Fin.Mod.Prep│         │  ││
│  │  │  └───────┬───────┴───────────┴─────────┴─────────────┘         │  ││
│  │  │          │ (provider-specific configuration panel)              │  ││
│  │  │          ▼                                                      │  ││
│  │  │  ┌──────────────────────────────────────────────────────────┐  │  ││
│  │  │  │ API Configuration | Connection Test | Provider Info     │  │  ││
│  │  │  ├──────────────────────────────────────────────────────────┤  │  ││
│  │  │  │ Rate Limiting                                           │  │  ││
│  │  │  ├──────────────────────────────────────────────────────────┤  │  ││
│  │  │  │ Connection Status                                       │  │  ││
│  │  │  └──────────────────────────────────────────────────────────┘  │  ││
│  │  └──────────────────────────────────────────────────────────────────┘  ││
│  │                                                                        ││
│  │  ┌──────────────────────────────────────────────────────────────────┐  ││
│  │  │ [Save Settings] [Reload Settings] [Test All Connections]        │  ││
│  │  └──────────────────────────────────────────────────────────────────┘  ││
│  │                                                                        ││
│  │  ┌─ Status ─────────────────────────────────────────────────────────┐  ││
│  │  │ [HH:MM:SS] Market tools configuration loaded                    │  ││
│  │  │ [HH:MM:SS] Configure API keys above and test connections        │  ││
│  │  │ (scrollable text area, 6 rows, ~80 columns)                     │  ││
│  │  └──────────────────────────────────────────────────────────────────┘  ││
│  └────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Outer Shell: MarketToolsTab

The outer shell wraps the core widget, adds global action buttons, and a status log.

### 2.1 Layout Structure

```
┌─ tab_frame (fills parent notebook) ──────────────────────────────────┐
│  padding: 10px all sides                                             │
│                                                                      │
│  ┌─ Title Label ──────────────────────────────────────────────────┐  │
│  │  "Market Data API Configuration"                               │  │
│  │  Font: Arial 14pt Bold                                         │  │
│  │  Bottom margin: 5px                                            │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ Description Label ────────────────────────────────────────────┐  │
│  │  "Configure API keys and settings for market data providers"   │  │
│  │  Font: Arial 9pt                                               │  │
│  │  Bottom margin: 15px                                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ MarketToolsWidget ───────────────────────────────────────────┐  │
│  │  (fills remaining width and height — see Section 3)            │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ Button Frame ─────────────────────────────────────────────────┐  │
│  │  Top margin: 10px                                              │  │
│  │  [Save Settings] [Reload Settings] [Test All Connections]      │  │
│  │  ◄── buttons packed LEFT with 5px horizontal gap ──►           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ Status (LabelFrame, title="Status") ──────────────────────────┐ │
│  │  Top margin: 10px, padding: 5px                                │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ ScrolledText (height=6 rows, width=80 chars)             │  │ │
│  │  │                                                          │  │ │
│  │  │ [08:30:15] Market tools configuration loaded     (black) │  │ │
│  │  │ [08:30:15] Configure API keys above and test...  (black) │  │ │
│  │  │ [08:31:02] Saving settings...                    (black) │  │ │
│  │  │ [08:31:02] Settings saved successfully           (green) │  │ │
│  │  │ [08:32:10] Testing Alpha Vantage...              (black) │  │ │
│  │  │ [08:32:12] ❌ No API key configured              (red)   │  │ │
│  │  │                                         ▼ scrollbar      │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Global Action Buttons

| Button | Label | Behavior |
|--------|-------|----------|
| **Save Settings** | `Save Settings` | Persists all provider settings (API keys, rate limits, timeouts) to encrypted storage. Logs "Saving settings..." followed by success/error message to status area. |
| **Reload Settings** | `Reload Settings` | Reloads all provider settings from the configuration file back into every provider tab's fields. Updates API key, rate limit, timeout, and resets connection status to "Settings reloaded". Logs success/error to status area. |
| **Test All Connections** | `Test All Connections` | Iterates through all 9 providers. For each provider that has a non-empty, non-placeholder API key, it launches a connection test (same as clicking "Test Connection" on that provider's tab). Providers without configured keys are skipped with a warning. Reports count of tested providers. |

### 2.3 Status Log Area

- **Widget type**: Scrollable multiline text area (read-only appearance but technically writable by the application)
- **Dimensions**: 6 rows tall × 80 characters wide
- **Entry format**: `[HH:MM:SS] message text`
- **Color-coded messages** (text color by severity):

| Level | Color | Example |
|-------|-------|---------|
| INFO | Black | `[08:30:15] Market tools configuration loaded` |
| WARNING | Orange | `[08:31:02] Skipping Polygon.io - no API key configured` |
| ERROR | Red | `[08:32:10] Failed to save settings: ...` |
| SUCCESS | Green | `[08:31:03] Settings saved successfully` |

- Auto-scrolls to the newest entry when a new message is appended.

---

## 3. Inner Widget: MarketToolsWidget (Provider Notebook)

The core widget is a **tabbed notebook** where each tab represents one market data API provider. All 9 tabs share the same layout template.

### 3.1 Provider Tabs

The inner notebook contains exactly **9 tabs**, presented in this order left-to-right:

```
┌───────────────┬────────────┬─────────┬────────────────────────┬───────┐
│ Alpha Vantage │ Polygon.io │ Finnhub │ Financial Modeling Prep │ EODHD │ ...
└───────────────┴────────────┴─────────┴────────────────────────┴───────┘
                                    ┌─────────────────┬─────────┬────────────┬──────────┐
                                ... │ Nasdaq Data Link │ SEC API │ API Ninjas │ Benzinga │
                                    └─────────────────┴─────────┴────────────┴──────────┘
```

Tab labels (exact text): `Alpha Vantage`, `Polygon.io`, `Finnhub`, `Financial Modeling Prep`, `EODHD`, `Nasdaq Data Link`, `SEC API`, `API Ninjas`, `Benzinga`

When a tab is clicked, the system internally tracks which provider is currently selected. This fires a tab-change event that updates internal state.

---

### 3.2 Per-Provider Tab Layout (Identical Template)

Every provider tab uses the **same layout** populated with provider-specific data. Below is the complete layout for a single provider tab:

```
┌─ Provider Tab Content ────────────────────────────────────────────────────────┐
│  padding: 5px, anchored to top                                                │
│                                                                               │
│  ┌─ Top Row (3 sections side-by-side) ─────────────────────────────────────┐  │
│  │                                                                         │  │
│  │  ┌─ API Configuration 🔒 ──────┐ ┌─ Connection Test ─┐ ┌─ Provider ──┐│  │
│  │  │                              │ │                    │ │ Information ││  │
│  │  │ API Key: [********] [Get ►]  │ │ [Test Connection]  │ │             ││  │
│  │  │                              │ │                    │ │ Free Tier:  ││  │
│  │  └──────────────────────────────┘ └────────────────────┘ │ 25 req/day  ││  │
│  │                                                          │             ││  │
│  │                                                          │ Description:││  │
│  │                                                          │ Real-time...││  │
│  │                                                          └─────────────┘│  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─ Rate Limiting ────────────────────────────────────────────────────────┐   │
│  │                                                                        │   │
│  │  Requests per minute: [  60  ]     Timeout (seconds): [  30  ]         │   │
│  │                                                                        │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌─ Connection Status ────────────────────────────────────────────────────┐   │
│  │                                                                        │   │
│  │                          Not tested                                    │   │
│  │                                                                        │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Section-by-Section Breakdown

#### 3.3.1 Top Row — Three Grouped Panels (Horizontal Layout)

The top row contains three **labeled group boxes** arranged horizontally, left-to-right:

##### Panel A: "API Configuration" (with encryption indicator)

```
┌─ API Configuration 🔒 ─────────────────────────────────┐
│                                                          │
│  API Key:  [*************************]  [ Get API Key ]  │
│            ▲ password entry (25 chars)   ▲ button        │
│            │ shows asterisks             │ opens browser  │
│            │ editable                    │                │
└──────────────────────────────────────────────────────────┘
```

| Element | Type | Details |
|---------|------|---------|
| **Group title** | LabelFrame title | Text: `"API Configuration 🔒"` when encryption is available, `"API Configuration ⚠️"` when encryption is unavailable |
| **"API Key:" label** | Static text | Positioned to the left of the entry field |
| **API key entry** | Password text field | Width: 25 characters. Displays `*` characters to mask the key. Pre-populated with decrypted key from settings, or placeholder `"enter_your_api_key"` if no key is stored |
| **"Get API Key" button** | Push button | Opens the provider's API key signup page in the system's default web browser |

**API Key Entry behaviors:**
- Every keystroke triggers an auto-save: the current value of all fields (API key, rate limit, timeout) is encrypted and persisted immediately.
- When displaying, the stored encrypted key is decrypted and shown masked.
- Empty or placeholder values (`"enter_your_api_key"`) are stored as plaintext; real keys are encrypted before storage.
- API keys are registered with a global security filter that prevents them from appearing in log output.

##### Panel B: "Connection Test"

```
┌─ Connection Test ────────┐
│                           │
│   [ Test Connection ]     │
│     ▲ button              │
│                           │
└───────────────────────────┘
```

| Element | Type | Details |
|---------|------|---------|
| **Group title** | LabelFrame title | Text: `"Connection Test"` |
| **"Test Connection" button** | Push button | Launches an API connection test for this specific provider (runs in a background thread to avoid freezing the GUI) |

**Test Connection behavior:**
1. Sets the Connection Status display to `"Testing..."`.
2. Only one test can run at a time across all providers — if a test is already running, the button click is silently ignored.
3. Reads the current API key from the entry field (decrypts from storage).
4. If the key is empty or placeholder, immediately shows `"❌ No API key provided"`.
5. Constructs a test HTTP GET request using the provider's base URL + test endpoint.
6. Uses the timeout value from the Rate Limiting section.
7. Sends the request with appropriate authentication headers.
8. Interprets the response and updates the Connection Status display.

##### Panel C: "Provider Information"

```
┌─ Provider Information ─────────────────────────────┐
│                                                     │
│  Free Tier: 25 requests/day                         │
│  Description: Real-time and historical stock data,  │
│  technical indicators                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

| Element | Type | Details |
|---------|------|---------|
| **Group title** | LabelFrame title | Text: `"Provider Information"` |
| **Info text** | Static multiline label | Word-wrapped at 300px. Displays free tier quota and a description. Read-only, populated from provider configuration data. |

This panel expands to fill remaining horizontal space after the API Configuration and Connection Test panels.

---

#### 3.3.2 Rate Limiting Section

```
┌─ Rate Limiting ──────────────────────────────────────────────────┐
│                                                                   │
│  Requests per minute: [   60   ]     Timeout (seconds): [  30  ] │
│                        ▲ entry (10w)                     ▲ entry  │
│                        │ numeric                         │ (10w)  │
│                        │ editable                        │ numeric│
└───────────────────────────────────────────────────────────────────┘
```

| Element | Type | Default | Details |
|---------|------|---------|---------|
| **Group title** | LabelFrame title | — | Text: `"Rate Limiting"` |
| **"Requests per minute:" label** | Static text | — | Left-aligned |
| **Rate limit entry** | Text input | `60` | Width: 10 characters. Numeric value. Each change triggers auto-save. |
| **"Timeout (seconds):" label** | Static text | — | Positioned to the right of the rate limit entry with 20px gap |
| **Timeout entry** | Text input | `30` | Width: 10 characters. Numeric value (seconds). Used as the HTTP request timeout when testing connections. Each change triggers auto-save. |

Both fields are arranged in a single horizontal row within the group box.

---

#### 3.3.3 Connection Status Section

```
┌─ Connection Status ──────────────────────────────────────────────┐
│                                                                   │
│                          Not tested                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

| Element | Type | Details |
|---------|------|---------|
| **Group title** | LabelFrame title | Text: `"Connection Status"` |
| **Status text** | Dynamic label | Displays current connection test result. Centered within the frame. Updated programmatically — not user-editable. |

**Possible status values:**

| Status Text | Meaning |
|-------------|---------|
| `Not tested` | Initial state, no test has been run |
| `Testing...` | Connection test is currently running |
| `✅ Connection successful` | Test request returned HTTP 200 with valid data |
| `✅ API key valid (endpoint deprecated)` | API key is accepted but the test endpoint is deprecated (HTTP 403 with "Legacy Endpoint" message) |
| `⚠️ Connected but unexpected response` | HTTP 200 but response data structure didn't match expectations |
| `⚠️ Connected but invalid JSON response` | HTTP 200 but response body was not valid JSON |
| `⚠️ Rate limit exceeded` | HTTP 429 response |
| `❌ No API key provided` | API key field is empty or contains the placeholder |
| `❌ Invalid API key` | HTTP 401 response |
| `❌ HTTP {code}` | Any other non-200 HTTP status code |
| `❌ Connection timeout` | Request exceeded the configured timeout |
| `❌ Connection failed` | Network/DNS error, server unreachable |
| `❌ Error: {message}` | Any other unexpected error (message truncated to 30 chars) |
| `Settings reloaded` | Shown after the "Reload Settings" action |

---

## 4. Provider Configuration Reference

Each of the 9 provider tabs shows the same layout but is populated with provider-specific data:

| # | Tab Label | API Key Signup URL | Free Tier | Description |
|---|-----------|-------------------|-----------|-------------|
| 1 | **Alpha Vantage** | alphavantage.co/support/#api-key | 25 requests/day | Real-time and historical stock data, technical indicators |
| 2 | **Polygon.io** | polygon.io/pricing | 5 calls/minute | Real-time and historical market data, news, financials |
| 3 | **Finnhub** | finnhub.io/register | 60 calls/minute | Real-time stock prices, company fundamentals, news |
| 4 | **Financial Modeling Prep** | financialmodelingprep.com/developer/docs | 250 calls/day | Financial statements, ratios, stock prices |
| 5 | **EODHD** | eodhd.com/pricing | 20 calls/day | End-of-day historical data, fundamentals |
| 6 | **Nasdaq Data Link** | data.nasdaq.com/sign-up | 50 calls/day | Economic data, alternative datasets |
| 7 | **SEC API** | sec-api.io/ | 100 requests/day | SEC EDGAR filings, insider trading, institutional holdings |
| 8 | **API Ninjas** | api-ninjas.com/ | 50,000 requests/month | Stock prices, company info, economic indicators, news |
| 9 | **Benzinga** | benzinga.com/apis | Contact for pricing | Financial news, earnings, analyst ratings, market data |

---

## 5. Error State: Widget Creation Failure

If the inner MarketToolsWidget fails to initialize (e.g., missing dependency), the tab shows a fallback error screen:

```
┌─ tab_frame ──────────────────────────────────────────────────────┐
│                                                                   │
│           Error Loading Market Tools  (red, bold, 14pt)           │
│                                                                   │
│    Failed to create market tools interface: {error message}       │
│    (wrapped at 600px)                                             │
│                                                                   │
│                         [ Retry ]                                 │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

| Element | Type | Details |
|---------|------|---------|
| **Error title** | Label | Text: `"Error Loading Market Tools"`, font: Arial 14pt Bold, color: red |
| **Error detail** | Label | Dynamic error message text, word-wrapped at 600px |
| **Retry button** | Push button | Clears all child widgets and re-attempts creating the entire tab content from scratch |

---

## 6. Behavioral Specifications

### 6.1 Settings Auto-Save

Every provider tab has **three editable fields**: API Key, Requests per minute, and Timeout. **Each field has a change listener** that fires on every keystroke. When the listener fires:

1. Collects current values from all three fields for that provider.
2. If the API key is a real key (not empty, not placeholder), encrypts it before storage.
3. Saves all values to the application's settings store.
4. The save is written to a persistent settings file on disk.

### 6.2 Encryption

- API keys are encrypted at rest using the `cryptography` library (Fernet symmetric encryption with PBKDF2 key derivation).
- The encryption indicator in the "API Configuration" group title shows:
  - `🔒` (lock icon) — encryption is available, keys are encrypted at rest.
  - `⚠️` (warning icon) — encryption is NOT available (library not installed), keys stored as plaintext.
- When displaying a stored key, it is decrypted in memory and shown masked (asterisks).
- Placeholder value `"enter_your_api_key"` is never encrypted.

### 6.3 Connection Testing

- Tests run in a **background thread** to keep the UI responsive.
- Only **one test can run at a time** globally — concurrent test requests are silently blocked.
- Each provider has a unique test endpoint and expected response structure.
- Responses are validated per-provider to confirm not just HTTP 200, but that the returned data contains the expected fields.
- API keys in URLs and log messages are **sanitized** — only the first 4 characters are shown, the rest replaced with `*`.

### 6.4 Settings Reload

When "Reload Settings" is clicked:
1. All settings are re-read from the persistent settings file.
2. For each of the 9 providers, the API key, rate limit, and timeout fields are repopulated.
3. The Connection Status for each provider is reset to `"Settings reloaded"`.

### 6.5 Test All Connections

When "Test All Connections" is clicked:
1. Iterates through all 9 providers in order.
2. For each provider, checks if a valid API key is stored (not empty, not placeholder).
3. Providers with valid keys: launches an asynchronous connection test.
4. Providers without keys: logs a warning to the status area and skips.
5. Reports total number of providers tested.

---

## 7. Widget Hierarchy Tree

```
MarketToolsTab
├── tab_frame                        (Frame, added to parent notebook as "Market Tools")
│   └── main_container               (Frame, padding=10)
│       ├── title_label              (Label: "Market Data API Configuration", bold 14pt)
│       ├── desc_label               (Label: description text, 9pt)
│       ├── MarketToolsWidget        (Frame, fills BOTH directions)
│       │   └── notebook             (Notebook, inner tabbed interface)
│       │       ├── tab[0]           (Frame: "Alpha Vantage")
│       │       │   └── [Provider Layout — see Section 3.2]
│       │       ├── tab[1]           (Frame: "Polygon.io")
│       │       │   └── [Provider Layout]
│       │       ├── tab[2]           (Frame: "Finnhub")
│       │       │   └── [Provider Layout]
│       │       ├── tab[3]           (Frame: "Financial Modeling Prep")
│       │       │   └── [Provider Layout]
│       │       ├── tab[4]           (Frame: "EODHD")
│       │       │   └── [Provider Layout]
│       │       ├── tab[5]           (Frame: "Nasdaq Data Link")
│       │       │   └── [Provider Layout]
│       │       ├── tab[6]           (Frame: "SEC API")
│       │       │   └── [Provider Layout]
│       │       ├── tab[7]           (Frame: "API Ninjas")
│       │       │   └── [Provider Layout]
│       │       └── tab[8]           (Frame: "Benzinga")
│       │           └── [Provider Layout]
│       ├── button_frame             (Frame, horizontal layout)
│       │   ├── save_btn             (Button: "Save Settings")
│       │   ├── reload_btn           (Button: "Reload Settings")
│       │   └── test_all_btn         (Button: "Test All Connections")
│       └── status_frame             (LabelFrame: "Status")
│           └── status_text          (ScrolledText, 6×80)
```

### Provider Layout Tree (repeated per tab)

```
tab[N]
└── main_frame                       (Frame, fill=X, padding=5, anchor=top)
    ├── top_frame                    (Frame, horizontal layout)
    │   ├── api_frame                (LabelFrame: "API Configuration 🔒")
    │   │   ├── api_key_label        (Label: "API Key:")
    │   │   ├── api_key_entry        (Entry, password masked, width=25)
    │   │   └── get_key_btn          (Button: "Get API Key")
    │   ├── test_frame               (LabelFrame: "Connection Test")
    │   │   └── test_btn             (Button: "Test Connection")
    │   └── info_frame               (LabelFrame: "Provider Information")
    │       └── info_label           (Label: free tier + description, wrap=300)
    ├── rate_frame                   (LabelFrame: "Rate Limiting")
    │   └── rate_row                 (Frame, horizontal layout)
    │       ├── rate_label           (Label: "Requests per minute:")
    │       ├── rate_entry           (Entry, width=10)
    │       ├── timeout_label        (Label: "Timeout (seconds):")
    │       └── timeout_entry        (Entry, width=10)
    └── status_frame                 (LabelFrame: "Connection Status")
        └── status_label             (Label, dynamic text)
```

---

## 8. Data Flow Summary

```
┌──────────────┐     auto-save on      ┌──────────────────┐     read/write     ┌─────────────┐
│  User types  │ ──── keystroke ──────► │  Settings        │ ◄───────────────► │  Settings   │
│  in any      │                        │  Manager         │                    │  File       │
│  field       │                        │  (in memory)     │                    │  (on disk)  │
└──────────────┘                        └──────────────────┘                    └─────────────┘
                                               │
                                               │ encrypt/decrypt
                                               ▼
                                        ┌──────────────────┐
                                        │  Encryption      │
                                        │  Module          │
                                        │  (Fernet/PBKDF2) │
                                        └──────────────────┘

┌──────────────┐     click              ┌──────────────────┐     HTTP GET       ┌─────────────┐
│  Test        │ ──── button ─────────► │  Background      │ ──────────────── ► │  Provider   │
│  Connection  │                        │  Thread          │                    │  API        │
│  button      │                        │  (test_connection)│ ◄──────────────── │  Server     │
└──────────────┘                        └──────┬───────────┘    JSON response   └─────────────┘
                                               │
                                               │ update status text
                                               ▼
                                        ┌──────────────────┐
                                        │  Connection      │
                                        │  Status Label    │
                                        └──────────────────┘
```

---

## 9. Implementation Notes for Cross-Language Ports

### 9.1 Essential Requirements

1. **Tabbed interface (nested)**: The outer application uses tabs; Market Tools is one tab. Inside Market Tools, there is a second level of tabs (one per provider).
2. **Password-masked entry**: The API key field must display asterisks instead of the actual characters.
3. **Change listeners**: API key, rate limit, and timeout fields must have change listeners that trigger auto-save on every modification.
4. **Background threading**: Connection tests must run asynchronously to prevent UI freezing. Only one test may run at a time.
5. **Encrypted storage**: API keys should be encrypted at rest. If encryption is unavailable, fall back to plaintext with a visual warning.
6. **External browser launch**: "Get API Key" buttons must open URLs in the system's default web browser.
7. **Scrollable status log**: The status text area must be scrollable, support color-coded text, and auto-scroll to the bottom.

### 9.2 UI Layout Strategy

- **Outer shell** uses vertical stacking (top-to-bottom): title → description → widget → buttons → status.
- **Inner provider panels** use vertical stacking with a horizontal top row.
- **Top row** uses horizontal arrangement: API Config (left) → Connection Test (center-left) → Provider Info (fills remaining).
- **Rate limiting row** uses horizontal arrangement within a group box.
- **Connection status** is a simple centered label within a group box.
- Group boxes (LabelFrames) provide visual separation and labeling for each section.

### 9.3 Per-Provider Data Model

Each provider stores exactly 3 user-editable settings plus 1 display-only field:

| Field | Storage Key | Type | Editable | Persisted |
|-------|-------------|------|----------|-----------|
| API Key | `API_KEY` | String (encrypted) | Yes | Yes |
| Rate Limit | `RATE_LIMIT` | String (numeric) | Yes | Yes |
| Timeout | `TIMEOUT` | String (numeric) | Yes | Yes |
| Connection Status | `STATUS` | String | No (program-set) | No |

### 9.4 Font Customization

The widget supports applying a custom font to all text widgets within it. This is used when the parent application has a font size/family preference. Only `Text` type widgets (not labels or entries) are affected by the font override.
