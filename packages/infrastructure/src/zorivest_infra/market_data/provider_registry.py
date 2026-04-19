"""Market data provider registry — MEU-59 + MEU-65.

Static registry of 14 market data API provider configurations:
- 12 API-key providers (MEU-59 spec, docs/build-plan/08-market-data.md §8.2c)
- 2 free providers added by MEU-65: Yahoo Finance, TradingView
"""

from __future__ import annotations

from zorivest_core.domain.enums import AuthMethod
from zorivest_core.domain.market_data import ProviderConfig

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
        test_endpoint=(
            "/datatables/ETFG/FUND.json"
            "?qopts.columns=ticker&api_key={api_key}&qopts.per_page=1"
        ),
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
    "OpenFIGI": ProviderConfig(
        name="OpenFIGI",
        base_url="https://api.openfigi.com/v3",
        auth_method=AuthMethod.CUSTOM_HEADER,
        auth_param_name="X-OPENFIGI-APIKEY",
        headers_template={"X-OPENFIGI-APIKEY": "{api_key}"},
        test_endpoint="/mapping",
        default_rate_limit=10,
        signup_url="https://www.openfigi.com/api",
        response_validator_key="data",
    ),
    "Alpaca": ProviderConfig(
        name="Alpaca",
        base_url="https://api.alpaca.markets/v2",
        auth_method=AuthMethod.CUSTOM_HEADER,
        auth_param_name="APCA-API-KEY-ID",
        headers_template={
            "APCA-API-KEY-ID": "{api_key}",
            "APCA-API-SECRET-KEY": "{api_secret}",
        },
        test_endpoint="/account",
        default_rate_limit=200,
        signup_url="https://app.alpaca.markets/signup",
        response_validator_key="id",
    ),
    "Tradier": ProviderConfig(
        name="Tradier",
        base_url="https://api.tradier.com/v1",
        auth_method=AuthMethod.BEARER_HEADER,
        auth_param_name="Authorization",
        headers_template={"Authorization": "Bearer {api_key}"},
        test_endpoint="/user/profile",
        default_rate_limit=120,
        signup_url="https://developer.tradier.com/",
        response_validator_key="profile",
    ),
    # ── Free providers — no API key required ──────────────────────────────
    "Yahoo Finance": ProviderConfig(
        name="Yahoo Finance",
        # Yahoo API paths span multiple version prefixes (/v1, /v6, /v8),
        # so base_url must be the bare domain — builders construct full paths.
        base_url="https://query1.finance.yahoo.com",
        auth_method=AuthMethod.NONE,
        auth_param_name="",
        headers_template={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Referer": "https://finance.yahoo.com/",
        },
        test_endpoint="/v1/finance/search?q=AAPL&quotesCount=1&newsCount=0",
        default_rate_limit=100,  # ~2000 req/hr; conservative limit
        signup_url="https://pypi.org/project/yfinance/",
        response_validator_key="quotes",
    ),
    "TradingView": ProviderConfig(
        name="TradingView",
        # scanner.tradingview.com is the endpoint used by all major Python
        # TradingView libraries (tradingview-screener, tvscreener, tv-scraper).
        # POST to /america/scan with an empty-ish payload returns 200 + JSON
        # with 'totalCount' and 'data' fields. No auth required.
        # symbol-search.tradingview.com is Cloudflare-blocked (403) for scripts.
        # data.tradingview.com/pingpong/ returns 301 redirect.
        base_url="https://scanner.tradingview.com",
        auth_method=AuthMethod.NONE,
        auth_param_name="",
        headers_template={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        test_endpoint="/america/scan",
        default_rate_limit=60,
        signup_url="https://www.tradingview.com/",
        response_validator_key="totalCount",
    ),
}


def get_provider_config(name: str) -> ProviderConfig:
    """Look up a provider configuration by name.

    Args:
        name: Provider name (e.g. "Alpha Vantage").

    Returns:
        The ProviderConfig for the given name.

    Raises:
        KeyError: If no provider with that name exists.
    """
    try:
        return PROVIDER_REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Unknown market data provider: '{name}'. "
            f"Available: {', '.join(sorted(PROVIDER_REGISTRY))}"
        ) from None


def list_provider_names() -> list[str]:
    """Return a sorted list of all registered provider names."""
    return sorted(PROVIDER_REGISTRY)
