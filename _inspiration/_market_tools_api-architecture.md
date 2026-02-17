# Market Tools — API Connectivity Architecture

> **Purpose**: Complete technical reference for connecting to all 9 market data API providers.  
> **Audience**: Developers integrating these APIs in any language.  
> **Date**: 2026-02-07  

---

## Table of Contents

1. [Overview](#1-overview)
2. [API Key Encryption & Storage](#2-api-key-encryption--storage)
3. [Settings Persistence](#3-settings-persistence)
4. [API Key Security (Log Redaction)](#4-api-key-security-log-redaction)
5. [Provider-by-Provider Connection Guide](#5-provider-by-provider-connection-guide)
6. [Connection Testing Framework](#6-connection-testing-framework)
7. [Response Validation Per Provider](#7-response-validation-per-provider)
8. [Error Handling Patterns](#8-error-handling-patterns)
9. [Rate Limiting](#9-rate-limiting)
10. [Complete Working Example](#10-complete-working-example)

---

## 1. Overview

The Market Tools system connects to **9 financial data API providers**, each with its own authentication method, base URL, and endpoint structure. All providers use **REST APIs** accessed via HTTP GET requests. API keys are **encrypted at rest** using Fernet symmetric encryption (PBKDF2 key derivation) and **redacted from logs** via a global security filter.

### Architecture Diagram

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  Application │────▶│  Settings Manager │────▶│  market_settings.json │
│  (GUI/CLI)   │     │  (load/save/backup)│     │  (encrypted keys)    │
└──────┬───────┘     └──────────────────┘     └──────────────────────┘
       │
       │  decrypt key
       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  Encryption  │────▶│  HTTP Client     │────▶│  Provider API Server  │
│  Module      │     │  (requests lib)  │     │  (Alpha Vantage, etc) │
│  (Fernet)    │     │  + rate limiting │     │                       │
└──────────────┘     └──────┬───────────┘     └──────────┬───────────┘
                            │                            │
                            │◀───── JSON response ───────┘
                            ▼
                     ┌──────────────────┐
                     │  Response        │
                     │  Validator       │
                     │  (per-provider)  │
                     └──────────────────┘
```

---

## 2. API Key Encryption & Storage

### 2.1 Encryption Mechanism

API keys are encrypted using the `cryptography` Python library. The encryption is machine-specific — a key encrypted on one computer cannot be decrypted on another.

**Dependencies:**
```bash
pip install cryptography
```

**Encryption functions:**

```python
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Flag indicating if encryption is available
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False


def get_system_encryption_key():
    """Generate a machine-specific encryption key using PBKDF2 + Fernet."""
    if not ENCRYPTION_AVAILABLE:
        return None

    try:
        # Build machine-specific salt from environment variables
        machine_id = os.environ.get('COMPUTERNAME', '') + os.environ.get('USERNAME', '')
        if not machine_id:
            # Linux/Mac fallback
            machine_id = os.environ.get('HOSTNAME', '') + os.environ.get('USER', '')

        # Pad or truncate to exactly 16 bytes
        salt = machine_id.encode()[:16].ljust(16, b'0')

        # Derive key using PBKDF2 with SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"pomera_ai_tool_encryption"))
        return Fernet(key)
    except Exception:
        return None


def encrypt_api_key(api_key):
    """
    Encrypt an API key for storage.
    
    Returns the key prefixed with 'ENC:' to mark it as encrypted.
    If encryption is unavailable or the key is a placeholder, returns as-is.
    """
    if not api_key or api_key == "enter_your_api_key" or not ENCRYPTION_AVAILABLE:
        return api_key

    # Already encrypted — don't double-encrypt
    if api_key.startswith("ENC:"):
        return api_key

    try:
        fernet = get_system_encryption_key()
        if not fernet:
            return api_key

        encrypted = fernet.encrypt(api_key.encode())
        return "ENC:" + base64.urlsafe_b64encode(encrypted).decode()
    except Exception:
        return api_key  # Fallback to plaintext


def decrypt_api_key(encrypted_key):
    """
    Decrypt an API key for use.
    
    Only decrypts keys prefixed with 'ENC:'. Non-encrypted keys pass through.
    """
    if not encrypted_key or encrypted_key == "enter_your_api_key" or not ENCRYPTION_AVAILABLE:
        return encrypted_key

    # Not encrypted — return as-is
    if not encrypted_key.startswith("ENC:"):
        return encrypted_key

    try:
        fernet = get_system_encryption_key()
        if not fernet:
            return encrypted_key

        # Remove "ENC:" prefix, then decode and decrypt
        encrypted_data = encrypted_key[4:]
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception:
        return encrypted_key  # Return encrypted value if decryption fails
```

### 2.2 Storage Format

Encrypted keys are stored with the `ENC:` prefix followed by base64-encoded ciphertext:

```
"API_KEY": "ENC:Z0FBQUFBQm8tcVhyeXBhRHE3bHB2RnFnems..."
```

Plaintext or placeholder keys are stored as-is:

```
"API_KEY": "enter_your_api_key"
```

---

## 3. Settings Persistence

### 3.1 File: `market_settings.json`

All provider settings are persisted in a single JSON file at the project root.

**Structure:**

```json
{
  "market_tool_settings": {
    "Alpha Vantage": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "5",
      "TIMEOUT": "30"
    },
    "Polygon.io": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "5",
      "TIMEOUT": "30"
    },
    "Finnhub": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "60",
      "TIMEOUT": "30"
    },
    "Financial Modeling Prep": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "250",
      "TIMEOUT": "30"
    },
    "EODHD": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "20",
      "TIMEOUT": "30"
    },
    "Nasdaq Data Link": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "50",
      "TIMEOUT": "30"
    },
    "SEC API": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "60",
      "TIMEOUT": "30"
    },
    "API Ninjas": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "60",
      "TIMEOUT": "30"
    },
    "Benzinga": {
      "API_KEY": "ENC:Z0FBQUFBQm8t...",
      "RATE_LIMIT": "60",
      "TIMEOUT": "30"
    }
  },
  "data_collection": {
    "enabled": true,
    "collection_time": "06:00",
    "max_retries": 3,
    "retry_delay": 5
  },
  "database": {
    "path": "market_data.db",
    "backup_enabled": true,
    "retention_days": 90
  }
}
```

### 3.2 Per-Provider Settings Schema

Each provider stores exactly **3 fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `API_KEY` | string | `"enter_your_api_key"` | Encrypted API key (prefixed `ENC:`) or plaintext placeholder |
| `RATE_LIMIT` | string | varies | Max requests per minute (stored as string) |
| `TIMEOUT` | string | `"30"` | HTTP request timeout in seconds (stored as string) |

### 3.3 Backup Strategy

On every save:
1. If the settings file exists, create a timestamped backup: `market_settings.backup_YYYYMMDD_HHMMSS.json`
2. Save new settings as `market_settings.json`
3. Clean up old backups, keeping only the 5 most recent

```python
import json
import shutil
from pathlib import Path
from datetime import datetime

class MarketSettingsManager:
    def __init__(self, config_file="market_settings.json"):
        self.config_file = Path(config_file)

    def load_settings(self):
        """Load settings from JSON. Returns (settings_dict, errors_dict)."""
        if not self.config_file.exists():
            return self._get_default_settings(), {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # Deep merge with defaults so new providers get default values
            merged = self._deep_merge(self._get_default_settings(), loaded)
            return merged, {}
        except json.JSONDecodeError as e:
            return self._get_default_settings(), {'json_error': str(e)}

    def save_settings(self, settings):
        """Save settings with backup. Returns dict of errors (empty = success)."""
        try:
            if self.config_file.exists():
                self._create_backup()
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return {}
        except Exception as e:
            return {'save_error': str(e)}

    def _create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_file.with_suffix(f'.backup_{timestamp}.json')
        shutil.copy2(self.config_file, backup_path)
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        pattern = f"{self.config_file.stem}.backup_*.json"
        backups = sorted(
            self.config_file.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old in backups[5:]:
            old.unlink()

    def _deep_merge(self, default, loaded):
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

---

## 4. API Key Security (Log Redaction)

All API keys are automatically redacted from log output to prevent accidental exposure.

### 4.1 How It Works

1. When an API key is decrypted for use, it is **registered** with a global singleton filter.
2. The filter wraps all logging handlers so that any log message containing a registered key gets the key replaced with a masked version.
3. Additionally, regex patterns catch common URL-embedded keys (`?apikey=`, `&token=`, etc.).

### 4.2 Masking Format

| Key Length | Masked Output |
|------------|---------------|
| > 8 chars | First 4 chars + `...` + last 4 chars (e.g., `sk-x...9abc`) |
| ≤ 8 chars | `<keyremoved>` |

### 4.3 URL Sanitization (Per-Request)

Before logging any URL or response text, a per-request sanitizer replaces the API key:

```python
def sanitize_url_for_logging(text, api_key):
    """Replace API key with masked version in any text string."""
    if api_key and len(api_key) > 4:
        masked = api_key[:4] + "*" * (len(api_key) - 4)
        return text.replace(api_key, masked)
    return text
```

---

## 5. Provider-by-Provider Connection Guide

### 5.1 Alpha Vantage

| Property | Value |
|----------|-------|
| **Base URL** | `https://www.alphavantage.co/query` |
| **Auth method** | API key as query parameter |
| **Auth header** | None |
| **Free tier** | 25 requests/day |
| **API key signup** | https://www.alphavantage.co/support/#api-key |

**Authentication**: The API key is passed as a URL query parameter named `apikey`.

```python
import requests

API_KEY = "your_alpha_vantage_key"
BASE_URL = "https://www.alphavantage.co/query"

# Example: Get a stock quote
params = {
    "function": "GLOBAL_QUOTE",
    "symbol": "IBM",
    "apikey": API_KEY
}
response = requests.get(BASE_URL, params=params, timeout=30)
data = response.json()

# Successful response contains "Global Quote" key
if "Global Quote" in data:
    print(f"Price: {data['Global Quote']['05. price']}")
```

**Test endpoint for connection verification:**

```
GET https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}
```

**Successful response structure:**
```json
{
  "Global Quote": {
    "01. symbol": "IBM",
    "02. open": "236.1000",
    "05. price": "237.5600",
    ...
  }
}
```

---

### 5.2 Polygon.io

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.polygon.io/v2` |
| **Auth method** | Bearer token in `Authorization` header |
| **Auth header** | `Authorization: Bearer {api_key}` |
| **Free tier** | 5 calls/minute |
| **API key signup** | https://polygon.io/pricing |

**Authentication**: The API key is passed as a Bearer token in the `Authorization` header.

```python
import requests

API_KEY = "your_polygon_key"
BASE_URL = "https://api.polygon.io/v2"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Example: Get daily aggregates for AAPL
endpoint = "/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02"
response = requests.get(BASE_URL + endpoint, headers=headers, timeout=30)
data = response.json()

# Successful response contains "results" or "status"
if "results" in data:
    for bar in data["results"]:
        print(f"Close: {bar['c']}, Volume: {bar['v']}")
```

**Test endpoint:**

```
GET https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02
Headers: Authorization: Bearer {api_key}
```

**Successful response structure:**
```json
{
  "ticker": "AAPL",
  "status": "OK",
  "results": [
    {"c": 185.64, "h": 186.10, "l": 183.79, "o": 185.68, "v": 42628803, ...}
  ]
}
```

---

### 5.3 Finnhub

| Property | Value |
|----------|-------|
| **Base URL** | `https://finnhub.io/api/v1` |
| **Auth method** | Custom header OR query parameter |
| **Auth header** | `X-Finnhub-Token: {api_key}` |
| **Free tier** | 60 calls/minute |
| **API key signup** | https://finnhub.io/register |

**Authentication**: The API key can be passed via the `X-Finnhub-Token` header or as a `token` query parameter.

```python
import requests

API_KEY = "your_finnhub_key"
BASE_URL = "https://finnhub.io/api/v1"

headers = {
    "X-Finnhub-Token": API_KEY
}

# Example: Get stock quote
# Method 1: Using header
response = requests.get(f"{BASE_URL}/quote?symbol=AAPL", headers=headers, timeout=30)

# Method 2: Using query parameter (also valid)
# response = requests.get(f"{BASE_URL}/quote?symbol=AAPL&token={API_KEY}", timeout=30)

data = response.json()

# Successful response contains "c" (current price)
if "c" in data:
    print(f"Current price: {data['c']}")
    print(f"High: {data['h']}, Low: {data['l']}")
```

> **Note**: The test endpoint uses the query parameter method: `?symbol=AAPL&token={api_key}`. This is because the system appends the token to the URL when constructing the test URL. In production use, the header method is preferred.

**Test endpoint:**

```
GET https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}
```

**Successful response structure:**
```json
{
  "c": 189.84,
  "d": 0.35,
  "dp": 0.1845,
  "h": 190.65,
  "l": 188.28,
  "o": 189.33,
  "pc": 189.49,
  "t": 1706302801
}
```

Field meanings: `c`=current, `d`=change, `dp`=percent change, `h`=high, `l`=low, `o`=open, `pc`=previous close, `t`=timestamp.

---

### 5.4 Financial Modeling Prep

| Property | Value |
|----------|-------|
| **Base URL** | `https://financialmodelingprep.com/api/v3` |
| **Auth method** | API key as query parameter |
| **Auth header** | None |
| **Free tier** | 250 calls/day |
| **API key signup** | https://financialmodelingprep.com/developer/docs |

**Authentication**: The API key is passed as a URL query parameter named `apikey`.

```python
import requests

API_KEY = "your_fmp_key"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Example: Search for a stock
params = {
    "query": "AAPL",
    "limit": 1,
    "apikey": API_KEY
}
response = requests.get(f"{BASE_URL}/search", params=params, timeout=30)
data = response.json()

# Successful response is a list of results
if isinstance(data, list) and len(data) > 0:
    print(f"Found: {data[0]['name']} ({data[0]['symbol']})")
```

> **Special case**: FMP may return a "Legacy Endpoint" error for some endpoints if using a newer API version. This error still means the API key is **valid** — only the endpoint has been deprecated.

**Test endpoint:**

```
GET https://financialmodelingprep.com/api/v3/search?query=AAPL&limit=1&apikey={api_key}
```

**Successful response structure:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "currency": "USD",
    "stockExchange": "NASDAQ",
    "exchangeShortName": "NASDAQ"
  }
]
```

**Legacy endpoint response (still indicates valid key):**
```json
{
  "Error Message": "Legacy Endpoint: This endpoint has been deprecated..."
}
```

---

### 5.5 EODHD

| Property | Value |
|----------|-------|
| **Base URL** | `https://eodhd.com/api` |
| **Auth method** | API key as query parameter |
| **Auth header** | None |
| **Free tier** | 20 calls/day |
| **API key signup** | https://eodhd.com/pricing |

**Authentication**: The API key is passed as a URL query parameter named `api_token`. The response format is specified via `fmt=json`.

```python
import requests

API_KEY = "your_eodhd_key"
BASE_URL = "https://eodhd.com/api"

# Example: Get real-time price for AAPL (US exchange)
params = {
    "api_token": API_KEY,
    "fmt": "json"
}
response = requests.get(f"{BASE_URL}/real-time/AAPL.US", params=params, timeout=30)
data = response.json()

# Successful response contains "code" or "close"
if "code" in data or "close" in data:
    print(f"Ticker: {data.get('code')}, Close: {data.get('close')}")
```

> **Important**: EODHD tickers include the exchange suffix (e.g., `AAPL.US` for US stocks).

**Test endpoint:**

```
GET https://eodhd.com/api/real-time/AAPL.US?api_token={api_key}&fmt=json
```

**Successful response structure:**
```json
{
  "code": "AAPL.US",
  "timestamp": 1706302801,
  "gmtoffset": 0,
  "open": 189.33,
  "high": 190.65,
  "low": 188.28,
  "close": 189.84,
  "volume": 42628803,
  ...
}
```

---

### 5.6 Nasdaq Data Link

| Property | Value |
|----------|-------|
| **Base URL** | `https://data.nasdaq.com/api/v3` |
| **Auth method** | API key as query parameter |
| **Auth header** | None |
| **Free tier** | 50 calls/day |
| **API key signup** | https://data.nasdaq.com/sign-up |

**Authentication**: The API key is passed as a URL query parameter named `api_key`.

```python
import requests

API_KEY = "your_nasdaq_key"
BASE_URL = "https://data.nasdaq.com/api/v3"

# Example: Query ETFG fund data
params = {
    "qopts.columns": "ticker",
    "api_key": API_KEY,
    "qopts.per_page": 1
}
response = requests.get(
    f"{BASE_URL}/datatables/ETFG/FUND.json",
    params=params,
    timeout=30
)
data = response.json()

# Successful response contains "datatable" with "data" array
if "datatable" in data and "data" in data["datatable"]:
    print(f"Records found: {len(data['datatable']['data'])}")
```

**Test endpoint:**

```
GET https://data.nasdaq.com/api/v3/datatables/ETFG/FUND.json?qopts.columns=ticker&api_key={api_key}&qopts.per_page=1
```

**Successful response structure:**
```json
{
  "datatable": {
    "data": [["SPY"]],
    "columns": [{"name": "ticker", "type": "text"}]
  },
  "meta": {
    "next_cursor_id": null
  }
}
```

---

### 5.7 SEC API

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.sec-api.io` |
| **Auth method** | Bearer-style token in `Authorization` header |
| **Auth header** | `Authorization: {api_key}` (no "Bearer" prefix) |
| **Free tier** | 100 requests/day |
| **API key signup** | https://sec-api.io/ |

**Authentication**: The API key is passed directly in the `Authorization` header **without** the `Bearer` prefix.

```python
import requests

API_KEY = "your_sec_api_key"
BASE_URL = "https://api.sec-api.io"

headers = {
    "Authorization": API_KEY  # Note: NO "Bearer" prefix
}

# Example: Get company mapping by ticker
response = requests.get(
    f"{BASE_URL}/mapping/ticker/AAPL",
    headers=headers,
    timeout=30
)
data = response.json()

# Successful response is a list of company mappings
if isinstance(data, list) and len(data) > 0:
    company = data[0]
    print(f"Company: {company.get('name')}, CIK: {company.get('cik')}")
```

> **Important**: Unlike most providers, SEC API does NOT use the `Bearer` prefix in the Authorization header. The raw API key is the entire header value.

**Test endpoint:**

```
GET https://api.sec-api.io/mapping/ticker/AAPL
Headers: Authorization: {api_key}
```

**Successful response structure:**
```json
[
  {
    "ticker": "AAPL",
    "cik": "0000320193",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    ...
  }
]
```

---

### 5.8 API Ninjas

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.api-ninjas.com/v1` |
| **Auth method** | Custom header |
| **Auth header** | `X-Api-Key: {api_key}` |
| **Free tier** | 50,000 requests/month |
| **API key signup** | https://api-ninjas.com/ |

**Authentication**: The API key is passed in the `X-Api-Key` custom header.

```python
import requests

API_KEY = "your_api_ninjas_key"
BASE_URL = "https://api.api-ninjas.com/v1"

headers = {
    "X-Api-Key": API_KEY
}

# Example: Get stock price
response = requests.get(
    f"{BASE_URL}/stockprice",
    params={"ticker": "AAPL"},
    headers=headers,
    timeout=30
)
data = response.json()

# Successful response contains "price" and "name"
if "price" in data and "name" in data:
    print(f"{data['name']}: ${data['price']}")
```

**Test endpoint:**

```
GET https://api.api-ninjas.com/v1/stockprice?ticker=AAPL
Headers: X-Api-Key: {api_key}
```

**Successful response structure:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "price": 189.84,
  "exchange": "NASDAQ",
  "updated": 1706302801
}
```

---

### 5.9 Benzinga

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.benzinga.com/api/v2` |
| **Auth method** | API key as query parameter |
| **Auth header** | `accept: application/json` (standard, not auth) |
| **Free tier** | Contact for pricing |
| **API key signup** | https://www.benzinga.com/apis |

**Authentication**: The API key is passed as a URL query parameter named `token`.

```python
import requests

API_KEY = "your_benzinga_key"
BASE_URL = "https://api.benzinga.com/api/v2"

headers = {
    "accept": "application/json"
}

# Example: Get latest financial news
params = {
    "token": API_KEY,
    "pagesize": 5
}
response = requests.get(
    f"{BASE_URL}/news",
    params=params,
    headers=headers,
    timeout=30
)
data = response.json()

# Successful response is a list of news articles
if isinstance(data, list):
    for article in data[:3]:
        print(f"- {article.get('title')}")
```

**Test endpoint:**

```
GET https://api.benzinga.com/api/v2/news?token={api_key}&pagesize=1
Headers: accept: application/json
```

**Successful response structure:**
```json
[
  {
    "id": 12345,
    "title": "Apple Reports Record Revenue",
    "author": "Benzinga Staff",
    "created": "2024-01-26T14:30:00Z",
    "updated": "2024-01-26T14:35:00Z",
    "teaser": "Apple Inc reported...",
    "body": "Full article text...",
    "channels": [{"name": "News"}],
    "stocks": [{"name": "AAPL"}],
    ...
  }
]
```

---

## 6. Connection Testing Framework

The connection testing system verifies that an API key is valid by making a lightweight test request. Here is the complete framework:

```python
import requests
import json
import threading

class MarketConnectionTester:
    """Test API connections for all market data providers."""

    # Complete provider configuration
    PROVIDERS = {
        "Alpha Vantage": {
            "url": "https://www.alphavantage.co/query",
            "headers_template": {},
            "test_endpoint": "?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}"
        },
        "Polygon.io": {
            "url": "https://api.polygon.io/v2",
            "headers_template": {"Authorization": "Bearer {api_key}"},
            "test_endpoint": "/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02"
        },
        "Finnhub": {
            "url": "https://finnhub.io/api/v1",
            "headers_template": {"X-Finnhub-Token": "{api_key}"},
            "test_endpoint": "/quote?symbol=AAPL&token={api_key}"
        },
        "Financial Modeling Prep": {
            "url": "https://financialmodelingprep.com/api/v3",
            "headers_template": {},
            "test_endpoint": "/search?query=AAPL&limit=1&apikey={api_key}"
        },
        "EODHD": {
            "url": "https://eodhd.com/api",
            "headers_template": {},
            "test_endpoint": "/real-time/AAPL.US?api_token={api_key}&fmt=json"
        },
        "Nasdaq Data Link": {
            "url": "https://data.nasdaq.com/api/v3",
            "headers_template": {},
            "test_endpoint": "/datatables/ETFG/FUND.json?qopts.columns=ticker&api_key={api_key}&qopts.per_page=1"
        },
        "SEC API": {
            "url": "https://api.sec-api.io",
            "headers_template": {"Authorization": "{api_key}"},
            "test_endpoint": "/mapping/ticker/AAPL"
        },
        "API Ninjas": {
            "url": "https://api.api-ninjas.com/v1",
            "headers_template": {"X-Api-Key": "{api_key}"},
            "test_endpoint": "/stockprice?ticker=AAPL"
        },
        "Benzinga": {
            "url": "https://api.benzinga.com/api/v2",
            "headers_template": {"accept": "application/json"},
            "test_endpoint": "/news?token={api_key}&pagesize=1"
        }
    }

    def __init__(self):
        self._test_lock = threading.Lock()

    def test_connection(self, provider_name, api_key, timeout=30):
        """
        Test API connection for a single provider.
        
        Args:
            provider_name: Provider name (must match PROVIDERS keys)
            api_key: Decrypted API key
            timeout: Request timeout in seconds
        
        Returns:
            (success: bool, status_message: str)
        """
        if not api_key or api_key == "enter_your_api_key":
            return False, "❌ No API key provided"

        config = self.PROVIDERS.get(provider_name)
        if not config:
            return False, f"❌ Unknown provider: {provider_name}"

        try:
            # Build URL
            base_url = config["url"]
            test_endpoint = config["test_endpoint"].format(api_key=api_key)
            test_url = base_url + test_endpoint

            # Build headers (substitute {api_key} in header values)
            headers = {}
            for key, value in config["headers_template"].items():
                headers[key] = value.format(api_key=api_key)

            # Make request
            response = requests.get(test_url, headers=headers, timeout=timeout)

            # Interpret response
            if response.status_code == 200:
                try:
                    data = response.json()
                    if self._validate_response(provider_name, data):
                        return True, "✅ Connection successful"
                    else:
                        return True, "⚠️ Connected but unexpected response"
                except json.JSONDecodeError:
                    return True, "⚠️ Connected but invalid JSON response"

            elif response.status_code == 401:
                return False, "❌ Invalid API key"

            elif response.status_code == 429:
                return False, "⚠️ Rate limit exceeded"

            elif response.status_code == 403:
                # Special check for FMP "Legacy Endpoint" (key is valid)
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("Error Message", "")
                        if "Legacy Endpoint" in error_msg:
                            return True, "✅ API key valid (endpoint deprecated)"
                except json.JSONDecodeError:
                    pass
                return False, f"❌ HTTP {response.status_code}"

            else:
                return False, f"❌ HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "❌ Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "❌ Connection failed"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:30]}"

    def test_connection_async(self, provider_name, api_key, callback, timeout=30):
        """Test connection in a background thread. Calls callback(success, message)."""
        thread = threading.Thread(
            target=lambda: callback(*self.test_connection(provider_name, api_key, timeout)),
            daemon=True
        )
        thread.start()
        return thread

    def _validate_response(self, provider_name, data):
        """Validate that the response contains expected data for each provider."""
        # See Section 7 for full validation logic
        validators = {
            "Alpha Vantage":           lambda d: "Global Quote" in d or "Time Series" in d,
            "Polygon.io":              lambda d: "results" in d or "status" in d,
            "Finnhub":                 lambda d: "c" in d or "error" not in d,
            "Financial Modeling Prep":  lambda d: (isinstance(d, list) and len(d) > 0) or
                                                  (isinstance(d, dict) and "Legacy Endpoint" in d.get("Error Message", "")),
            "EODHD":                   lambda d: "code" in d or "close" in d,
            "Nasdaq Data Link":        lambda d: "datatable" in d and "data" in d["datatable"],
            "SEC API":                 lambda d: isinstance(d, list) and (
                                                  len(d) == 0 or
                                                  (isinstance(d[0], dict) and ("ticker" in d[0] or "cik" in d[0]))),
            "API Ninjas":              lambda d: "price" in d and "name" in d,
            "Benzinga":                lambda d: isinstance(d, list) or
                                                  (isinstance(d, dict) and "data" in d and isinstance(d["data"], list)),
        }
        validator = validators.get(provider_name, lambda d: True)
        try:
            return validator(data)
        except Exception:
            return False
```

---

## 7. Response Validation Per Provider

Each provider has specific expected fields in a successful test response:

| Provider | Expected Key(s) in JSON | Validation Rule |
|----------|------------------------|-----------------|
| **Alpha Vantage** | `"Global Quote"` or `"Time Series"` | Top-level key exists |
| **Polygon.io** | `"results"` or `"status"` | Top-level key exists |
| **Finnhub** | `"c"` | Key `"c"` (current price) exists AND no `"error"` key |
| **Financial Modeling Prep** | Array with items | Response is a non-empty list, OR dict with `"Legacy Endpoint"` in error message |
| **EODHD** | `"code"` or `"close"` | Top-level key exists |
| **Nasdaq Data Link** | `"datatable"` → `"data"` | Nested `datatable.data` exists |
| **SEC API** | Array of dicts | Response is a list; if non-empty, first item has `"ticker"` or `"cik"` |
| **API Ninjas** | `"price"` and `"name"` | Both keys exist |
| **Benzinga** | Array or dict with `"data"` | Response is a list, OR dict with `"data"` array; error keys absent |

---

## 8. Error Handling Patterns

### 8.1 HTTP Status Code Interpretation

| Status | Meaning | User-Facing Message |
|--------|---------|---------------------|
| 200 | Success (validate response body) | ✅ Connection successful |
| 200 + invalid JSON | Server returned non-JSON | ⚠️ Connected but invalid JSON response |
| 200 + unexpected structure | Valid JSON but wrong shape | ⚠️ Connected but unexpected response |
| 401 | Invalid or expired API key | ❌ Invalid API key |
| 403 | Forbidden (check for legacy endpoint) | ❌ HTTP 403 (or ✅ if legacy endpoint) |
| 429 | Rate limit exceeded | ⚠️ Rate limit exceeded |
| Other | Server-side or client error | ❌ HTTP {code} |
| Timeout | Connection or read timeout | ❌ Connection timeout |
| ConnectionError | DNS/network failure | ❌ Connection failed |
| Exception | Any other error | ❌ Error: {truncated message} |

### 8.2 Threading Model

- Connection tests run in **daemon threads** so they don't block the main application.
- A **global lock** prevents multiple concurrent tests — only one test at a time.
- If a test is already running, new test requests are silently ignored.

```python
# Thread-safe connection test
if self._test_thread and self._test_thread.is_alive():
    return  # Another test is already running

self._test_thread = threading.Thread(
    target=self.test_connection,
    args=(provider_name,),
    daemon=True
)
self._test_thread.start()
```

---

## 9. Rate Limiting

Rate limits are stored per-provider but are **not enforced client-side** by the current implementation. They are configuration values that downstream consumers should respect.

| Provider | Default Rate Limit | Unit |
|----------|--------------------|------|
| Alpha Vantage | 5 | req/min |
| Polygon.io | 5 | req/min |
| Finnhub | 60 | req/min |
| Financial Modeling Prep | 250 | req/day (stored as req/min) |
| EODHD | 20 | req/day (stored as req/min) |
| Nasdaq Data Link | 50 | req/day (stored as req/min) |
| SEC API | 60 | req/min |
| API Ninjas | 60 | req/min |
| Benzinga | 60 | req/min |

### Implementing Rate Limiting (Recommended Pattern)

```python
import time
from collections import deque

class RateLimiter:
    """Token-bucket rate limiter."""
    
    def __init__(self, max_per_minute):
        self.max_per_minute = max_per_minute
        self.timestamps = deque()

    def wait_if_needed(self):
        """Block until a request slot is available."""
        now = time.time()
        # Remove timestamps older than 60 seconds
        while self.timestamps and self.timestamps[0] < now - 60:
            self.timestamps.popleft()
        
        if len(self.timestamps) >= self.max_per_minute:
            sleep_time = 60 - (now - self.timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.timestamps.append(time.time())
```

---

## 10. Complete Working Example

A self-contained example that loads settings, decrypts an API key, tests a connection, and makes a data request:

```python
"""
Complete example: Connect to Alpha Vantage and fetch a stock quote.
"""
import json
import requests
from pathlib import Path

# --- Step 1: Load settings ---
config_file = Path("market_settings.json")
with open(config_file, 'r', encoding='utf-8') as f:
    settings = json.load(f)

provider_settings = settings["market_tool_settings"]["Alpha Vantage"]
encrypted_key = provider_settings["API_KEY"]
timeout = int(provider_settings.get("TIMEOUT", "30"))

# --- Step 2: Decrypt the API key ---
# (uses the encryption functions from Section 2)
api_key = decrypt_api_key(encrypted_key)

if not api_key or api_key == "enter_your_api_key":
    print("No API key configured for Alpha Vantage")
    exit(1)

# --- Step 3: Test the connection ---
test_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}"
response = requests.get(test_url, timeout=timeout)

if response.status_code != 200:
    print(f"Connection failed: HTTP {response.status_code}")
    exit(1)

data = response.json()
if "Global Quote" not in data:
    print(f"Unexpected response: {json.dumps(data)[:200]}")
    exit(1)

print("✅ Connection verified!")

# --- Step 4: Fetch actual data ---
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "AAPL",
    "outputsize": "compact",
    "apikey": api_key
}
response = requests.get("https://www.alphavantage.co/query", params=params, timeout=timeout)
data = response.json()

if "Time Series (Daily)" in data:
    daily = data["Time Series (Daily)"]
    for date, values in list(daily.items())[:5]:
        print(f"  {date}: Open={values['1. open']}, Close={values['4. close']}, "
              f"Volume={values['5. volume']}")
else:
    print(f"Error: {data}")
```

---

## 11. Authentication Method Quick Reference

| Provider | Auth Location | Header / Param Name | Format |
|----------|--------------|---------------------|--------|
| **Alpha Vantage** | Query param | `apikey` | `?apikey={key}` |
| **Polygon.io** | Header | `Authorization` | `Bearer {key}` |
| **Finnhub** | Header + Query | `X-Finnhub-Token` / `token` | Header or `?token={key}` |
| **Financial Modeling Prep** | Query param | `apikey` | `?apikey={key}` |
| **EODHD** | Query param | `api_token` | `?api_token={key}` |
| **Nasdaq Data Link** | Query param | `api_key` | `?api_key={key}` |
| **SEC API** | Header | `Authorization` | `{key}` (no Bearer prefix!) |
| **API Ninjas** | Header | `X-Api-Key` | Custom header |
| **Benzinga** | Query param | `token` | `?token={key}` |

> **⚠️ Critical difference**: SEC API uses `Authorization: {key}` (raw key), while Polygon.io uses `Authorization: Bearer {key}` (with prefix). Mixing these up will cause authentication failures.
