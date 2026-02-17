# Phase 8: Market Data Aggregation Layer

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 2](02-infrastructure.md), [Phase 3](03-service-layer.md), [Phase 4](04-rest-api.md) | Consumers: [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md) ([Settings](06f-gui-settings.md))
>
> **Source**: [`_inspiration/_market_tools_api-architecture.md`](../../_inspiration/_market_tools_api-architecture.md)

---

## Goal

Build a unified market data aggregation layer connecting to **9 REST API providers**, enabling agentic queries (via MCP), GUI widgets, and scheduled reporting pipelines. All providers use API key authentication with keys encrypted at rest via Fernet.

---

## Architecture Overview

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  MCP Tools       │     │  React GUI        │     │  Scheduler       │
│  (get_stock_     │     │  (Provider        │     │  (data_refresh   │
│   quote, etc.)   │     │   Settings, etc.) │     │   pipeline)      │
└────────┬─────────┘     └────────┬──────────┘     └────────┬─────────┘
         │                        │                          │
         └────────────┬───────────┘──────────────────────────┘
                      ▼
         ┌───────────────────────┐
         │  FastAPI REST API     │
         │  /api/v1/market-data  │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  MarketDataService    │──── Provider fallback chain
         │  ProviderConnection   │──── Rate limiter (per-provider)
         │  Service              │──── Response normalizer
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  HTTP Client (httpx)  │──── API key decrypt on use
         │  + Log redaction      │──── URL sanitization
         └───────────┬───────────┘
                     ▼
  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
  │Alpha │Poly- │Finn- │ FMP  │EODHD │Nasdaq│ SEC  │ API  │Benz- │
  │Vant. │gon   │hub   │      │      │Data  │ API  │Ninjas│inga  │
  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

---

## Step 8.1: Domain Layer Additions

### 8.1a: AuthMethod Enum

```python
# packages/core/src/zorivest_core/domain/enums.py  (append)

class AuthMethod(str, Enum):
    """How the API key is passed to the provider."""
    QUERY_PARAM = "query_param"         # ?apikey={key}
    BEARER_HEADER = "bearer_header"     # Authorization: Bearer {key}
    CUSTOM_HEADER = "custom_header"     # X-Api-Key: {key} or X-Finnhub-Token: {key}
    RAW_HEADER = "raw_header"           # Authorization: {key} (no Bearer prefix)
```

### 8.1b: Provider Configuration (Value Object)

```python
# packages/core/src/zorivest_core/domain/market_data.py

from dataclasses import dataclass, field
from zorivest_core.domain.enums import AuthMethod

@dataclass(frozen=True)
class ProviderConfig:
    """Immutable configuration for a market data API provider."""
    name: str
    base_url: str
    auth_method: AuthMethod
    auth_param_name: str              # "apikey", "token", "api_key", "api_token"
    headers_template: dict[str, str]  # e.g., {"X-Finnhub-Token": "{api_key}"}
    test_endpoint: str                # Lightweight endpoint for connection testing
    default_rate_limit: int           # requests per minute
    default_timeout: int = 30
    signup_url: str = ""
    response_validator_key: str = ""  # Top-level key expected in valid response
```

### 8.1c: Normalized Response DTOs

```python
# packages/core/src/zorivest_core/application/dtos.py  (append)

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MarketQuote(BaseModel):
    """Normalized stock quote across all providers."""
    ticker: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    provider: str                     # Which provider returned this data

class MarketNewsItem(BaseModel):
    """Normalized news article."""
    title: str
    source: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    tickers: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    provider: str

class TickerSearchResult(BaseModel):
    """Normalized ticker search result."""
    symbol: str
    name: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    provider: str

class SecFiling(BaseModel):
    """SEC filing reference."""
    ticker: str
    company_name: str
    cik: str
    filing_type: Optional[str] = None
    filing_date: Optional[datetime] = None
    provider: str = "SEC API"
```

### 8.1d: Port Interface

```python
# packages/core/src/zorivest_core/application/ports.py  (append)

from typing import Protocol

class MarketDataPort(Protocol):
    """Abstract interface for market data queries."""
    async def get_quote(self, ticker: str) -> MarketQuote: ...
    async def get_news(self, ticker: str | None, count: int) -> list[MarketNewsItem]: ...
    async def search_ticker(self, query: str) -> list[TickerSearchResult]: ...
    async def get_sec_filings(self, ticker: str) -> list[SecFiling]: ...
```

---

## Step 8.2: Infrastructure Layer Additions

### 8.2a: Database Model

```python
# packages/infrastructure/src/zorivest_infra/database/models.py  (append)

class MarketProviderSettingModel(Base):
    __tablename__ = "market_provider_settings"

    provider_name = Column(String, primary_key=True)       # e.g., "Alpha Vantage"
    encrypted_api_key = Column(Text, nullable=True)        # Fernet-encrypted, "ENC:" prefix
    rate_limit = Column(Integer, default=5)                # requests per minute
    timeout = Column(Integer, default=30)                  # seconds
    is_enabled = Column(Boolean, default=False)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(50), nullable=True)   # "success" | "failed" | "untested"
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
```

### 8.2b: API Key Encryption Module

Generalized encryption for any API key. Uses the same Fernet + PBKDF2 pattern as SMTP credentials (see `SCHEDULER_EMAIL_SERVICE_RESEARCH.md` §8).

```python
# packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

ENC_PREFIX = "ENC:"

def encrypt_api_key(api_key: str, fernet: Fernet) -> str:
    """Encrypt an API key. Returns 'ENC:' prefixed ciphertext."""
    if not api_key or api_key.startswith(ENC_PREFIX):
        return api_key
    encrypted = fernet.encrypt(api_key.encode())
    return ENC_PREFIX + base64.urlsafe_b64encode(encrypted).decode()

def decrypt_api_key(encrypted_key: str, fernet: Fernet) -> str:
    """Decrypt an 'ENC:' prefixed key. Non-encrypted keys pass through."""
    if not encrypted_key or not encrypted_key.startswith(ENC_PREFIX):
        return encrypted_key
    encrypted_data = encrypted_key[len(ENC_PREFIX):]
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    return fernet.decrypt(encrypted_bytes).decode()
```

### 8.2c: Provider Registry (Singleton)

```python
# packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py

from zorivest_core.domain.market_data import ProviderConfig
from zorivest_core.domain.enums import AuthMethod

PROVIDER_REGISTRY: dict[str, ProviderConfig] = {
    "Alpha Vantage": ProviderConfig(
        name="Alpha Vantage",
        base_url="https://www.alphavantage.co/query",
        auth_method=AuthMethod.QUERY_PARAM,
        auth_param_name="apikey",
        headers_template={},
        test_endpoint="?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}",
        default_rate_limit=5,
        signup_url="https://www.alphavantage.co/support/#api-key",
        response_validator_key="Global Quote",
    ),
    "Polygon.io": ProviderConfig(
        name="Polygon.io",
        base_url="https://api.polygon.io/v2",
        auth_method=AuthMethod.BEARER_HEADER,
        auth_param_name="Authorization",
        headers_template={"Authorization": "Bearer {api_key}"},
        test_endpoint="/aggs/ticker/AAPL/range/1/day/2024-01-02/2024-01-02",
        default_rate_limit=5,
        signup_url="https://polygon.io/pricing",
        response_validator_key="results",
    ),
    "Finnhub": ProviderConfig(
        name="Finnhub",
        base_url="https://finnhub.io/api/v1",
        auth_method=AuthMethod.CUSTOM_HEADER,
        auth_param_name="X-Finnhub-Token",
        headers_template={"X-Finnhub-Token": "{api_key}"},
        test_endpoint="/quote?symbol=AAPL&token={api_key}",
        default_rate_limit=60,
        signup_url="https://finnhub.io/register",
        response_validator_key="c",
    ),
    "Financial Modeling Prep": ProviderConfig(
        name="Financial Modeling Prep",
        base_url="https://financialmodelingprep.com/api/v3",
        auth_method=AuthMethod.QUERY_PARAM,
        auth_param_name="apikey",
        headers_template={},
        test_endpoint="/search?query=AAPL&limit=1&apikey={api_key}",
        default_rate_limit=250,
        signup_url="https://financialmodelingprep.com/developer/docs",
    ),
    "EODHD": ProviderConfig(
        name="EODHD",
        base_url="https://eodhd.com/api",
        auth_method=AuthMethod.QUERY_PARAM,
        auth_param_name="api_token",
        headers_template={},
        test_endpoint="/real-time/AAPL.US?api_token={api_key}&fmt=json",
        default_rate_limit=20,
        signup_url="https://eodhd.com/pricing",
        response_validator_key="code",
    ),
    "Nasdaq Data Link": ProviderConfig(
        name="Nasdaq Data Link",
        base_url="https://data.nasdaq.com/api/v3",
        auth_method=AuthMethod.QUERY_PARAM,
        auth_param_name="api_key",
        headers_template={},
        test_endpoint="/datatables/ETFG/FUND.json?qopts.columns=ticker&api_key={api_key}&qopts.per_page=1",
        default_rate_limit=50,
        signup_url="https://data.nasdaq.com/sign-up",
        response_validator_key="datatable",
    ),
    "SEC API": ProviderConfig(
        name="SEC API",
        base_url="https://api.sec-api.io",
        auth_method=AuthMethod.RAW_HEADER,
        auth_param_name="Authorization",
        headers_template={"Authorization": "{api_key}"},
        test_endpoint="/mapping/ticker/AAPL",
        default_rate_limit=60,
        signup_url="https://sec-api.io/",
    ),
    "API Ninjas": ProviderConfig(
        name="API Ninjas",
        base_url="https://api.api-ninjas.com/v1",
        auth_method=AuthMethod.CUSTOM_HEADER,
        auth_param_name="X-Api-Key",
        headers_template={"X-Api-Key": "{api_key}"},
        test_endpoint="/stockprice?ticker=AAPL",
        default_rate_limit=60,
        signup_url="https://api-ninjas.com/",
        response_validator_key="price",
    ),
    "Benzinga": ProviderConfig(
        name="Benzinga",
        base_url="https://api.benzinga.com/api/v2",
        auth_method=AuthMethod.QUERY_PARAM,
        auth_param_name="token",
        headers_template={"accept": "application/json"},
        test_endpoint="/news?token={api_key}&pagesize=1",
        default_rate_limit=60,
        signup_url="https://www.benzinga.com/apis",
    ),
}
```

### 8.2d: Log Redaction Filter

```python
# packages/infrastructure/src/zorivest_infra/security/log_redaction.py

import re

def mask_api_key(key: str) -> str:
    """Mask an API key for safe logging."""
    if len(key) > 8:
        return key[:4] + "..." + key[-4:]
    return "<keyremoved>"

def sanitize_url_for_logging(text: str, api_key: str) -> str:
    """Replace API key with masked version in any text string."""
    if api_key and len(api_key) > 4:
        return text.replace(api_key, mask_api_key(api_key))
    return text
```

### 8.2e: Rate Limiter

```python
# packages/infrastructure/src/zorivest_infra/market_data/rate_limiter.py

import time
from collections import deque

class RateLimiter:
    """Token-bucket rate limiter per provider."""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.timestamps: deque[float] = deque()

    async def wait_if_needed(self) -> None:
        """Block until a request slot is available."""
        now = time.time()
        while self.timestamps and self.timestamps[0] < now - 60:
            self.timestamps.popleft()
        if len(self.timestamps) >= self.max_per_minute:
            sleep_time = 60 - (now - self.timestamps[0])
            if sleep_time > 0:
                import asyncio
                await asyncio.sleep(sleep_time)
        self.timestamps.append(time.time())
```

---

## Step 8.3: Service Layer

### 8.3a: ProviderConnectionService

```python
# packages/core/src/zorivest_core/services/provider_connection_service.py

class ProviderConnectionService:
    """Manage market data provider credentials and connectivity."""

    def __init__(self, uow, fernet, http_client):
        self.uow = uow
        self.fernet = fernet
        self.client = http_client

    async def list_providers(self) -> list[dict]:
        """List all providers with their status (enabled, last test result)."""
        ...

    async def configure_provider(
        self, name: str, api_key: str,
        rate_limit: int | None = None, timeout: int | None = None
    ) -> None:
        """Encrypt and store an API key for a provider."""
        ...

    async def test_connection(self, provider_name: str) -> tuple[bool, str]:
        """Test a provider's API connection. Returns (success, message)."""
        ...

    async def remove_api_key(self, provider_name: str) -> None:
        """Remove a provider's API key."""
        ...
```

### 8.3b: MarketDataService

```python
# packages/core/src/zorivest_core/services/market_data_service.py

class MarketDataService:
    """Unified market data queries with provider fallback."""

    def __init__(self, uow, fernet, http_client, rate_limiters: dict[str, RateLimiter]):
        self.uow = uow
        self.fernet = fernet
        self.client = http_client
        self.rate_limiters = rate_limiters

    async def get_stock_quote(self, ticker: str, providers: list[str] | None = None) -> MarketQuote:
        """Get a stock quote, trying providers in order until success."""
        ...

    async def get_market_news(self, ticker: str | None = None, count: int = 5) -> list[MarketNewsItem]:
        """Get market news from news-capable providers (Finnhub, Benzinga)."""
        ...

    async def search_ticker(self, query: str) -> list[TickerSearchResult]:
        """Search for tickers across providers (FMP, Alpha Vantage)."""
        ...

    async def get_sec_filings(self, ticker: str) -> list[SecFiling]:
        """Get SEC filings for a company (SEC API only)."""
        ...
```

### 8.3c: Response Normalizers

```python
# packages/infrastructure/src/zorivest_infra/market_data/normalizers.py

def normalize_alpha_vantage_quote(data: dict) -> MarketQuote:
    """Convert Alpha Vantage 'Global Quote' → MarketQuote."""
    gq = data.get("Global Quote", {})
    return MarketQuote(
        ticker=gq.get("01. symbol", ""),
        price=float(gq.get("05. price", 0)),
        open=float(gq.get("02. open", 0)),
        high=float(gq.get("03. high", 0)),
        low=float(gq.get("04. low", 0)),
        previous_close=float(gq.get("08. previous close", 0)),
        change=float(gq.get("09. change", 0)),
        change_pct=float(gq.get("10. change percent", "0").rstrip("%")),
        volume=int(gq.get("06. volume", 0)),
        provider="Alpha Vantage",
    )

# Similar normalizers for each provider:
# normalize_polygon_quote, normalize_finnhub_quote, normalize_eodhd_quote,
# normalize_api_ninjas_quote, normalize_fmp_search, normalize_sec_filing,
# normalize_benzinga_news, normalize_finnhub_news
```

---

## Step 8.4: REST API Endpoints

```python
# packages/api/src/zorivest_api/routes/market_data.py

from fastapi import APIRouter, Depends, HTTPException, Query

market_data_router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])

@market_data_router.get("/quote")
async def get_quote(ticker: str = Query(...), service = Depends(get_market_data_service)):
    return await service.get_stock_quote(ticker)

@market_data_router.get("/news")
async def get_news(ticker: str | None = None, count: int = 5, service = Depends(get_market_data_service)):
    return await service.get_market_news(ticker, count)

@market_data_router.get("/search")
async def search_tickers(query: str = Query(...), service = Depends(get_market_data_service)):
    return await service.search_ticker(query)

@market_data_router.get("/sec-filings")
async def get_sec_filings(ticker: str = Query(...), service = Depends(get_market_data_service)):
    return await service.get_sec_filings(ticker)

@market_data_router.get("/providers")
async def list_providers(service = Depends(get_provider_service)):
    return await service.list_providers()

@market_data_router.put("/providers/{name}")
async def configure_provider(name: str, body: ProviderConfigRequest, service = Depends(get_provider_service)):
    """Update provider settings. Omitted fields are left unchanged (PATCH semantics)."""
    await service.configure_provider(
        name,
        api_key=body.api_key,
        rate_limit=body.rate_limit,
        timeout=body.timeout,
        is_enabled=body.is_enabled,
    )
    return {"status": "configured"}

@market_data_router.post("/providers/{name}/test")
async def test_provider(name: str, service = Depends(get_provider_service)):
    success, message = await service.test_connection(name)
    return {"success": success, "message": message}

@market_data_router.delete("/providers/{name}/key")
async def remove_provider_key(name: str, service = Depends(get_provider_service)):
    """Remove API key and disable provider."""
    await service.remove_api_key(name)
    return {"status": "removed"}


class ProviderConfigRequest(BaseModel):
    """All fields optional — omitted fields are left unchanged (PATCH semantics)."""
    api_key: str | None = None
    rate_limit: int | None = None
    timeout: int | None = None
    is_enabled: bool | None = None
```

---

## Step 8.5: MCP Tools (TypeScript)

```typescript
// mcp-server/src/tools/market-data-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerMarketDataTools(server: McpServer) {

  server.tool(
    'get_stock_quote',
    'Get real-time stock price data for a ticker symbol.',
    { ticker: z.string().describe('Stock ticker symbol, e.g. "AAPL"') },
    async ({ ticker }) => {
      const res = await fetch(`${API_BASE}/market-data/quote?ticker=${encodeURIComponent(ticker)}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  server.tool(
    'get_market_news',
    'Get recent financial news, optionally filtered by ticker.',
    {
      ticker: z.string().optional().describe('Stock ticker to filter news'),
      count: z.number().default(5).describe('Number of articles'),
    },
    async ({ ticker, count }) => {
      const params = new URLSearchParams({ count: String(count) });
      if (ticker) params.set('ticker', ticker);
      const res = await fetch(`${API_BASE}/market-data/news?${params}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  server.tool(
    'search_ticker',
    'Search for stock tickers by company name or symbol.',
    { query: z.string().describe('Company name or partial ticker') },
    async ({ query }) => {
      const res = await fetch(`${API_BASE}/market-data/search?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  server.tool(
    'get_sec_filings',
    'Get SEC filings for a company by ticker symbol.',
    { ticker: z.string().describe('Stock ticker symbol') },
    async ({ ticker }) => {
      const res = await fetch(`${API_BASE}/market-data/sec-filings?ticker=${encodeURIComponent(ticker)}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  server.tool(
    'list_market_providers',
    'Show the status of all configured market data API providers.',
    {},
    async () => {
      const res = await fetch(`${API_BASE}/market-data/providers`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );

  server.tool(
    'test_market_provider',
    'Test the API connection for a specific market data provider.',
    { provider_name: z.string().describe('Provider name, e.g. "Alpha Vantage"') },
    async ({ provider_name }) => {
      const res = await fetch(`${API_BASE}/market-data/providers/${encodeURIComponent(provider_name)}/test`, {
        method: 'POST',
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );

  server.tool(
    'disconnect_market_provider',
    'Remove API key and disable a market data provider.',
    { provider_name: z.string().describe('Provider name, e.g. "Alpha Vantage"') },
    async ({ provider_name }) => {
      const res = await fetch(`${API_BASE}/market-data/providers/${encodeURIComponent(provider_name)}/key`, {
        method: 'DELETE',
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
}
```

---

## Step 8.6: Connection Testing Framework

Response validation rules per provider (used by `ProviderConnectionService.test_connection`):

| Provider | Expected Key(s) in JSON | Validation Rule |
|----------|------------------------|--------------------|
| Alpha Vantage | `"Global Quote"` or `"Time Series"` | Top-level key exists |
| Polygon.io | `"results"` or `"status"` | Top-level key exists |
| Finnhub | `"c"` | Key `"c"` (current price) exists AND no `"error"` key |
| Financial Modeling Prep | Array with items | Non-empty list, OR dict with `"Legacy Endpoint"` in error (still valid) |
| EODHD | `"code"` or `"close"` | Top-level key exists |
| Nasdaq Data Link | `"datatable"` → `"data"` | Nested `datatable.data` exists |
| SEC API | Array of dicts | List; if non-empty, first item has `"ticker"` or `"cik"` |
| API Ninjas | `"price"` and `"name"` | Both keys exist |
| Benzinga | Array or dict with `"data"` | List, OR dict with `"data"` array |

### HTTP Status Interpretation

| Status | Meaning | User Message |
|--------|---------|-------------|
| 200 + valid JSON | Success | ✅ Connection successful |
| 200 + unexpected JSON | Key is valid but wrong data shape | ⚠️ Connected but unexpected response |
| 401 | Invalid API key | ❌ Invalid API key |
| 403 + "Legacy Endpoint" | FMP-specific: key is valid | ✅ API key valid (endpoint deprecated) |
| 429 | Rate limit exceeded | ⚠️ Rate limit exceeded |
| Timeout | Connection or read timeout | ❌ Connection timeout |
| ConnectionError | DNS/network failure | ❌ Connection failed |

### Concurrency Guard

When testing multiple providers (e.g., "Test All Connections"), use an `asyncio.Semaphore` to limit concurrency and prevent rate-limiting from providers that detect rapid sequential requests:

```python
# Limit to 2 concurrent connection tests
_test_semaphore = asyncio.Semaphore(2)

async def test_all_providers(self) -> list[tuple[str, bool, str]]:
    async def _guarded_test(provider: ProviderStatus):
        async with self._test_semaphore:
            return (provider.provider_name, *await self.test_connection(provider.provider_name))
    
    providers: list[ProviderStatus] = await self.list_providers()
    enabled = [p for p in providers if p.has_api_key]
    return await asyncio.gather(*[_guarded_test(p) for p in enabled])
```

> This is the async equivalent of the thread lock pattern from the inspiration doc. A semaphore (rather than a mutex) allows 2 concurrent tests for reasonable throughput while still preventing rate-limit storms. `ProviderStatus` is a Pydantic model returned by `list_providers()` — see [06f-gui-settings.md](06f-gui-settings.md) for the TypeScript equivalent.

---

## Step 8.7: Authentication Quick Reference

| Provider | Auth Location | Header / Param | Format |
|----------|--------------|----------------|--------|
| Alpha Vantage | Query param | `apikey` | `?apikey={key}` |
| Polygon.io | Header | `Authorization` | `Bearer {key}` |
| Finnhub | Header + Query | `X-Finnhub-Token` / `token` | Header or `?token={key}` |
| FMP | Query param | `apikey` | `?apikey={key}` |
| EODHD | Query param | `api_token` | `?api_token={key}` |
| Nasdaq Data Link | Query param | `api_key` | `?api_key={key}` |
| SEC API | Header | `Authorization` | `{key}` (no Bearer!) |
| API Ninjas | Header | `X-Api-Key` | Custom header |
| Benzinga | Query param | `token` | `?token={key}` |

> **⚠️ Critical**: SEC API uses `Authorization: {key}` (raw), while Polygon.io uses `Authorization: Bearer {key}`. Mixing these causes auth failures.

---

## Test Plan

| Test File | What It Tests |
|-----------|---------------|
| `tests/unit/test_market_data_entities.py` | `ProviderConfig`, `AuthMethod`, normalized DTOs |
| `tests/unit/test_api_key_encryption.py` | Encrypt/decrypt round-trip, `ENC:` prefix handling |
| `tests/unit/test_rate_limiter.py` | Token-bucket timing, burst handling |
| `tests/unit/test_response_normalizers.py` | Per-provider JSON → DTO conversion (fixture data) |
| `tests/unit/test_log_redaction.py` | API key masking, URL sanitization |
| `tests/unit/test_provider_connection_service.py` | Connection test logic with mocked HTTP (success, 401, 429, timeout) |
| `tests/unit/test_market_data_service.py` | Quote/news/search with mocked providers, fallback chain |
| `tests/e2e/test_market_data_api.py` | REST endpoints via `TestClient` |
| `tests/typescript/mcp/market-data-tools.test.ts` | MCP tools with mocked `fetch()` |

---

## Exit Criteria

1. All 9 providers registered in provider registry with correct auth config
2. Encrypt/decrypt round-trip tests pass for API keys
3. Connection testing returns correct status for each HTTP scenario (200, 401, 429, timeout)
4. Response normalizers convert fixture data correctly for all supported providers
5. Rate limiter correctly throttles burst requests
6. REST API endpoints return normalized data via `TestClient`
7. MCP tools correctly call REST endpoints (Vitest with mocked fetch)
8. Log redaction masks API keys in all output

---

## Outputs

- `AuthMethod` enum + 9 `ProviderConfig` entries
- `MarketProviderSettingModel` SQLAlchemy table
- API key encryption module (generalized Fernet)
- `ProviderConnectionService` with test/configure/list operations
- `MarketDataService` with quote/news/search/SEC query operations
- Rate limiter (async token-bucket)
- Response normalizers for all 9 providers
- Log redaction filter
- 8 FastAPI REST endpoints under `/api/v1/market-data/`
- 7 TypeScript MCP tools
- Full test suite (unit + e2e + TypeScript)
