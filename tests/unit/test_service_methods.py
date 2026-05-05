"""Tests for Layer 4 service methods — MEU-190 + MEU-191 RED phase.

FIC — Feature Intent Contract
==============================
Intent: 8 new service methods on MarketDataService with Yahoo-first fallback
    (where applicable) and API-key provider chains per spec §8a.9/§8a.10.

MEU-190 Acceptance Criteria:
- AC-190-1: get_ohlcv() tries Yahoo first, then Alpaca → EODHD → Polygon
- AC-190-2: get_fundamentals() tries Yahoo first, then FMP → EODHD → Alpha Vantage
- AC-190-3: get_earnings() uses Finnhub → FMP → Alpha Vantage (no Yahoo)
- AC-190-4: _yahoo_ohlcv() returns list[OHLCVBar] from v8/finance/chart
- AC-190-5: _yahoo_fundamentals() returns FundamentalsSnapshot from v10/quoteSummary
- AC-190-8: Fallback chain logs provider failures and continues

MEU-191 Acceptance Criteria:
- AC-191-1: get_dividends() tries Yahoo first, then Polygon → EODHD → FMP
- AC-191-2: get_splits() tries Yahoo first, then Polygon → EODHD → FMP
- AC-191-3: get_insider() uses Finnhub → FMP → SEC API (no Yahoo)
- AC-191-4: get_economic_calendar() uses Finnhub → FMP → Alpha Vantage (no Yahoo)
- AC-191-5: get_company_profile() uses FMP → Finnhub → EODHD (no Yahoo)
- AC-191-6: _yahoo_dividends() returns list[DividendRecord] from chart events
- AC-191-7: _yahoo_splits() returns list[StockSplit] from chart events

Uses asyncio.run() since pytest-asyncio is not installed.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zorivest_core.application.market_expansion_dtos import (
    DividendRecord,
    EarningsReport,
    EconomicCalendarEvent,
    FundamentalsSnapshot,
    InsiderTransaction,
    OHLCVBar,
    StockSplit,
)
from zorivest_core.services.market_data_service import (
    MarketDataError,
    MarketDataService,
)


# ── Helpers ─────────────────────────────────────────────────────────────


class FakeHttpResponse:
    """Minimal HTTP response for testing."""

    def __init__(self, status_code: int = 200, data: Any = None) -> None:
        self.status_code = status_code
        self._data = data or {}

    def json(self) -> Any:
        return self._data


def _make_setting(
    name: str,
    *,
    enabled: bool = True,
    api_key: str = "ENC:test-key",
) -> MagicMock:
    """Create a fake MarketProviderSettings."""
    setting = MagicMock()
    setting.provider_name = name
    setting.is_enabled = enabled
    setting.encrypted_api_key = api_key
    setting.encrypted_api_secret = None
    setting.rate_limit = 60
    setting.timeout = 30
    return setting


def _make_data_service(
    *,
    settings: list[Any] | None = None,
    http_responses: list[FakeHttpResponse] | None = None,
    http_side_effect: Exception | None = None,
    normalizers: dict[str, dict[str, Any]] | None = None,
) -> MarketDataService:
    """Create a MarketDataService with mocked dependencies for Layer 4 tests."""
    from zorivest_core.domain.enums import AuthMethod
    from zorivest_core.domain.market_data import ProviderConfig

    fake_settings_repo = MagicMock()
    fake_settings_repo.list_all.return_value = settings or []

    fake_uow = MagicMock()
    fake_uow.__enter__ = MagicMock(return_value=fake_uow)
    fake_uow.__exit__ = MagicMock(return_value=False)
    fake_uow.market_provider_settings = fake_settings_repo

    fake_encryption = MagicMock()
    fake_encryption.decrypt.side_effect = lambda x: x.replace("ENC:", "")

    fake_http = AsyncMock()
    if http_side_effect:
        fake_http.get.side_effect = http_side_effect
    elif http_responses:
        fake_http.get.side_effect = http_responses
    else:
        fake_http.get.return_value = FakeHttpResponse()

    fake_limiter = AsyncMock()
    fake_limiter.wait_if_needed = AsyncMock()

    # Minimal registry covering all providers referenced in fallback chains
    registry = {
        "Alpaca": ProviderConfig(
            name="Alpaca",
            base_url="https://data.alpaca.markets",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="APCA-API-KEY-ID",
            headers_template={"APCA-API-KEY-ID": "{api_key}"},
            test_endpoint="/account",
            default_rate_limit=200,
        ),
        "EODHD": ProviderConfig(
            name="EODHD",
            base_url="https://eodhd.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="api_token",
            headers_template={},
            test_endpoint="/real-time",
            default_rate_limit=20,
        ),
        "Polygon.io": ProviderConfig(
            name="Massive",
            base_url="https://api.massive.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apiKey",
            headers_template={},
            test_endpoint="/v3/reference/tickers?limit=1&apiKey={api_key}",
            default_rate_limit=5,
        ),
        "Financial Modeling Prep": ProviderConfig(
            name="Financial Modeling Prep",
            base_url="https://financialmodelingprep.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="/search",
            default_rate_limit=250,
        ),
        "Alpha Vantage": ProviderConfig(
            name="Alpha Vantage",
            base_url="https://www.alphavantage.co",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="?function=GLOBAL_QUOTE",
            default_rate_limit=5,
        ),
        "Finnhub": ProviderConfig(
            name="Finnhub",
            base_url="https://finnhub.io/api/v1",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-Finnhub-Token",
            headers_template={"X-Finnhub-Token": "{api_key}"},
            test_endpoint="/quote",
            default_rate_limit=60,
        ),
        "SEC API": ProviderConfig(
            name="SEC API",
            base_url="https://api.sec-api.io",
            auth_method=AuthMethod.RAW_HEADER,
            auth_param_name="Authorization",
            headers_template={"Authorization": "{api_key}"},
            test_endpoint="/test",
            default_rate_limit=60,
        ),
    }

    rate_limiters = {name: fake_limiter for name in registry}

    return MarketDataService(
        uow=fake_uow,
        encryption=fake_encryption,
        http_client=fake_http,
        rate_limiters=rate_limiters,
        provider_registry=registry,
        normalizers=normalizers or {},
    )


# ═══════════════════════════════════════════════════════════════════════════
# MEU-190: Core Service Methods (Tasks 3-5)
# ═══════════════════════════════════════════════════════════════════════════


# ── AC-190-1: get_ohlcv ─────────────────────────────────────────────────


class TestGetOHLCV:
    """AC-190-1/4/8: get_ohlcv tries Yahoo first, then Alpaca → EODHD → Polygon."""

    def test_yahoo_ohlcv_returns_bars(self) -> None:
        """AC-190-4: _yahoo_ohlcv returns list[OHLCVBar] from v8/chart."""
        yahoo_response = FakeHttpResponse(
            200,
            {
                "chart": {
                    "result": [
                        {
                            "meta": {"symbol": "AAPL"},
                            "timestamp": [1704067200, 1704153600],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [185.0, 186.0],
                                        "high": [187.0, 188.0],
                                        "low": [184.0, 185.0],
                                        "close": [186.5, 187.5],
                                        "volume": [1000000, 1100000],
                                    }
                                ]
                            },
                        }
                    ]
                },
            },
        )
        svc = _make_data_service(http_responses=[yahoo_response])

        result = asyncio.run(svc.get_ohlcv("AAPL"))

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(bar, OHLCVBar) for bar in result)
        assert result[0].ticker == "AAPL"
        assert result[0].close == Decimal("186.5")

    def test_yahoo_fail_falls_back_to_api_key_provider(self) -> None:
        """AC-190-1/8: Yahoo fail → API-key provider chain (Alpaca first)."""
        call_count = 0

        async def side_effect(*args: Any, **kwargs: Any) -> FakeHttpResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Yahoo down")
            return FakeHttpResponse(
                200,
                {
                    "bars": [
                        {
                            "t": "2024-01-01T00:00:00Z",
                            "o": 185,
                            "h": 187,
                            "l": 184,
                            "c": 186.5,
                            "v": 1000000,
                        },
                    ]
                },
            )

        svc = _make_data_service(
            settings=[_make_setting("Alpaca")],
            normalizers={
                "ohlcv": {
                    "Alpaca": lambda data, **kw: [
                        OHLCVBar(
                            ticker="AAPL",
                            timestamp=kw.get(
                                "_ts", __import__("datetime").datetime.now()
                            ),
                            open=Decimal("185"),
                            high=Decimal("187"),
                            low=Decimal("184"),
                            close=Decimal("186.5"),
                            adj_close=None,
                            volume=1000000,
                            vwap=None,
                            trade_count=None,
                            provider="Alpaca",
                        )
                    ],
                }
            },
        )
        svc._http.get.side_effect = side_effect  # type: ignore[union-attr]

        result = asyncio.run(svc.get_ohlcv("AAPL"))

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].provider == "Alpaca"

    def test_all_providers_fail_raises_error(self) -> None:
        """AC-190-1: MarketDataError when Yahoo + all API-key providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Alpaca")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"ohlcv": {"Alpaca": lambda data, **kw: []}},
        )

        with pytest.raises(MarketDataError, match="All providers failed|No.*provider"):
            asyncio.run(svc.get_ohlcv("AAPL"))

    def test_returns_empty_list_when_no_data(self) -> None:
        """Empty Yahoo response + no API-key providers → empty or error."""
        yahoo_response = FakeHttpResponse(200, {"chart": {"result": []}})
        svc = _make_data_service(
            settings=[],
            http_responses=[yahoo_response],
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_ohlcv("NONEXIST"))


# ── AC-190-2: get_fundamentals ──────────────────────────────────────────


class TestGetFundamentals:
    """AC-190-2/5: get_fundamentals tries Yahoo first, then FMP → EODHD → AV."""

    def test_yahoo_fundamentals_returns_snapshot(self) -> None:
        """AC-190-5: _yahoo_fundamentals returns FundamentalsSnapshot from v10."""
        yahoo_response = FakeHttpResponse(
            200,
            {
                "quoteSummary": {
                    "result": [
                        {
                            "financialData": {
                                "currentPrice": {"raw": 186.5},
                                "targetMeanPrice": {"raw": 200.0},
                            },
                            "defaultKeyStatistics": {
                                "trailingPE": {"raw": 30.5},
                                "priceToBook": {"raw": 45.0},
                                "beta": {"raw": 1.2},
                                "trailingEps": {"raw": 6.12},
                                "marketCap": {"raw": 2900000000000},
                            },
                            "summaryProfile": {
                                "sector": "Technology",
                                "industry": "Consumer Electronics",
                                "fullTimeEmployees": 164000,
                            },
                        }
                    ]
                },
            },
        )
        svc = _make_data_service(http_responses=[yahoo_response])

        result = asyncio.run(svc.get_fundamentals("AAPL"))

        assert isinstance(result, FundamentalsSnapshot)
        assert result.ticker == "AAPL"
        assert result.pe_ratio == Decimal("30.5")

    def test_yahoo_fail_falls_back_to_fmp(self) -> None:
        """AC-190-2: Yahoo fail → FMP (primary API-key provider)."""
        call_count = 0

        async def side_effect(*args: Any, **kwargs: Any) -> FakeHttpResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Yahoo down")
            return FakeHttpResponse(200, [{"symbol": "AAPL", "mktCap": 2.9e12}])

        from datetime import datetime, timezone

        svc = _make_data_service(
            settings=[_make_setting("Financial Modeling Prep")],
            normalizers={
                "fundamentals": {
                    "Financial Modeling Prep": lambda data, **kw: FundamentalsSnapshot(
                        ticker="AAPL",
                        market_cap=Decimal("2900000000000"),
                        pe_ratio=None,
                        pb_ratio=None,
                        ps_ratio=None,
                        eps=None,
                        dividend_yield=None,
                        beta=None,
                        sector=None,
                        industry=None,
                        employees=None,
                        provider="Financial Modeling Prep",
                        timestamp=datetime.now(timezone.utc),
                    ),
                }
            },
        )
        svc._http.get.side_effect = side_effect  # type: ignore[union-attr]

        result = asyncio.run(svc.get_fundamentals("AAPL"))

        assert isinstance(result, FundamentalsSnapshot)
        assert result.provider == "Financial Modeling Prep"

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all sources fail."""
        svc = _make_data_service(
            settings=[_make_setting("Financial Modeling Prep")],
            http_side_effect=ConnectionError("All down"),
            normalizers={
                "fundamentals": {
                    "Financial Modeling Prep": lambda data, **kw: None,
                }
            },
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_fundamentals("AAPL"))


# ── AC-190-3: get_earnings ──────────────────────────────────────────────


class TestGetEarnings:
    """AC-190-3: get_earnings uses Finnhub → FMP → AV (no Yahoo)."""

    @patch.object(
        MarketDataService,
        "_yahoo_quote",
        side_effect=Exception("Yahoo should not be called"),
    )
    def test_no_yahoo_fallback(self, _mock: MagicMock) -> None:
        """Earnings does NOT try Yahoo first."""
        from datetime import date

        response = FakeHttpResponse(
            200,
            [
                {"date": "2024-01-25", "epsActual": 2.18, "epsEstimate": 2.10},
            ],
        )
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_responses=[response],
            normalizers={
                "earnings": {
                    "Finnhub": lambda data, **kw: [
                        EarningsReport(
                            ticker="AAPL",
                            fiscal_period="Q1",
                            fiscal_year=2024,
                            report_date=date(2024, 1, 25),
                            eps_actual=Decimal("2.18"),
                            eps_estimate=Decimal("2.10"),
                            eps_surprise=Decimal("0.08"),
                            revenue_actual=None,
                            revenue_estimate=None,
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )

        result = asyncio.run(svc.get_earnings("AAPL"))

        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(e, EarningsReport) for e in result)
        assert result[0].eps_actual == Decimal("2.18")

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all earnings providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"earnings": {"Finnhub": lambda data, **kw: []}},
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_earnings("AAPL"))


# ═══════════════════════════════════════════════════════════════════════════
# MEU-191: Extended Service Methods (Task 10)
# ═══════════════════════════════════════════════════════════════════════════


# ── AC-191-1: get_dividends ─────────────────────────────────────────────


class TestGetDividends:
    """AC-191-1/6: get_dividends tries Yahoo first, then Polygon → EODHD → FMP."""

    def test_yahoo_dividends_returns_records(self) -> None:
        """AC-191-6: _yahoo_dividends returns list[DividendRecord] from chart events."""

        yahoo_response = FakeHttpResponse(
            200,
            {
                "chart": {
                    "result": [
                        {
                            "meta": {"symbol": "AAPL"},
                            "events": {
                                "dividends": {
                                    "1700000000": {"amount": 0.24, "date": 1700000000},
                                    "1710000000": {"amount": 0.25, "date": 1710000000},
                                }
                            },
                        }
                    ]
                },
            },
        )
        svc = _make_data_service(http_responses=[yahoo_response])

        result = asyncio.run(svc.get_dividends("AAPL"))

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(d, DividendRecord) for d in result)

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all dividend providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Polygon.io")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"dividends": {"Polygon.io": lambda data, **kw: []}},
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_dividends("AAPL"))


# ── AC-191-2: get_splits ───────────────────────────────────────────────


class TestGetSplits:
    """AC-191-2/7: get_splits tries Yahoo first, then Polygon → EODHD → FMP."""

    def test_yahoo_splits_returns_records(self) -> None:
        """AC-191-7: _yahoo_splits returns list[StockSplit] from chart events."""

        yahoo_response = FakeHttpResponse(
            200,
            {
                "chart": {
                    "result": [
                        {
                            "meta": {"symbol": "AAPL"},
                            "events": {
                                "splits": {
                                    "1598832000": {
                                        "date": 1598832000,
                                        "numerator": 4,
                                        "denominator": 1,
                                    },
                                }
                            },
                        }
                    ]
                },
            },
        )
        svc = _make_data_service(http_responses=[yahoo_response])

        result = asyncio.run(svc.get_splits("AAPL"))

        assert isinstance(result, list)
        assert len(result) == 1
        assert all(isinstance(s, StockSplit) for s in result)
        assert result[0].ratio_to == 4
        assert result[0].ratio_from == 1

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all split providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Polygon.io")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"splits": {"Polygon.io": lambda data, **kw: []}},
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_splits("AAPL"))


# ── AC-191-3: get_insider ──────────────────────────────────────────────


class TestGetInsider:
    """AC-191-3: get_insider uses Finnhub → FMP → SEC API (no Yahoo)."""

    def test_returns_insider_transactions(self) -> None:
        """Returns list[InsiderTransaction] from first enabled provider."""
        from datetime import date

        response = FakeHttpResponse(
            200,
            [
                {"name": "Tim Cook", "share": 100000, "transactionDate": "2024-01-15"},
            ],
        )
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_responses=[response],
            normalizers={
                "insider": {
                    "Finnhub": lambda data, **kw: [
                        InsiderTransaction(
                            ticker="AAPL",
                            name="Tim Cook",
                            title="CEO",
                            transaction_date=date(2024, 1, 15),
                            transaction_code="S",
                            shares=100000,
                            price=Decimal("186.50"),
                            value=Decimal("18650000"),
                            shares_owned_after=None,
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )

        result = asyncio.run(svc.get_insider("AAPL"))

        assert isinstance(result, list)
        assert all(isinstance(t, InsiderTransaction) for t in result)

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all insider providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"insider": {"Finnhub": lambda data, **kw: []}},
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_insider("AAPL"))


# ── AC-191-4: get_economic_calendar ─────────────────────────────────────


class TestGetEconomicCalendar:
    """AC-191-4: get_economic_calendar uses Finnhub → FMP → AV (no Yahoo)."""

    def test_returns_events(self) -> None:
        """Returns list[EconomicCalendarEvent]."""
        from datetime import date

        response = FakeHttpResponse(
            200,
            [
                {"event": "CPI", "country": "US", "date": "2024-01-11"},
            ],
        )
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_responses=[response],
            normalizers={
                "economic_calendar": {
                    "Finnhub": lambda data, **kw: [
                        EconomicCalendarEvent(
                            event="CPI",
                            country="US",
                            date=date(2024, 1, 11),
                            time=None,
                            impact="high",
                            actual="3.4%",
                            forecast="3.2%",
                            previous="3.1%",
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )

        result = asyncio.run(svc.get_economic_calendar())

        assert isinstance(result, list)
        assert all(isinstance(e, EconomicCalendarEvent) for e in result)

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all calendar providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            http_side_effect=ConnectionError("All down"),
            normalizers={"economic_calendar": {"Finnhub": lambda d, **kw: []}},
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_economic_calendar())


# ── AC-191-5: get_company_profile ───────────────────────────────────────


class TestGetCompanyProfile:
    """AC-191-5: get_company_profile uses FMP → Finnhub → EODHD (no Yahoo)."""

    def test_returns_fundamentals_snapshot(self) -> None:
        """Returns FundamentalsSnapshot (same DTO as fundamentals)."""
        from datetime import datetime, timezone

        response = FakeHttpResponse(200, [{"symbol": "AAPL", "companyName": "Apple"}])
        svc = _make_data_service(
            settings=[_make_setting("Financial Modeling Prep")],
            http_responses=[response],
            normalizers={
                "company_profile": {
                    "Financial Modeling Prep": lambda data, **kw: FundamentalsSnapshot(
                        ticker="AAPL",
                        market_cap=Decimal("2900000000000"),
                        pe_ratio=None,
                        pb_ratio=None,
                        ps_ratio=None,
                        eps=None,
                        dividend_yield=None,
                        beta=None,
                        sector="Technology",
                        industry="Consumer Electronics",
                        employees=164000,
                        provider="Financial Modeling Prep",
                        timestamp=datetime.now(timezone.utc),
                    ),
                }
            },
        )

        result = asyncio.run(svc.get_company_profile("AAPL"))

        assert isinstance(result, FundamentalsSnapshot)
        assert result.sector == "Technology"

    def test_all_fail_raises_error(self) -> None:
        """MarketDataError when all profile providers fail."""
        svc = _make_data_service(
            settings=[_make_setting("Financial Modeling Prep")],
            http_side_effect=ConnectionError("All down"),
            normalizers={
                "company_profile": {
                    "Financial Modeling Prep": lambda d, **kw: None,
                }
            },
        )

        with pytest.raises(MarketDataError):
            asyncio.run(svc.get_company_profile("AAPL"))


# ═══════════════════════════════════════════════════════════════════════════
# Corrections: Finding 2 — Fallback Order (explicit, not alphabetical)
# ═══════════════════════════════════════════════════════════════════════════


class TestFallbackOrder:
    """F2: Provider fallback order must match spec, not alphabetical sort."""

    def test_fundamentals_order_fmp_eodhd_av(self) -> None:
        """AC-190-2: fundamentals chain is FMP → EODHD → AV, not AV → EODHD → FMP."""
        call_order: list[str] = []

        async def side_effect(*args: Any, **kwargs: Any) -> FakeHttpResponse:
            raise ConnectionError("Intentional fail")

        from datetime import datetime, timezone

        svc = _make_data_service(
            settings=[
                _make_setting("Financial Modeling Prep"),
                _make_setting("EODHD"),
                _make_setting("Alpha Vantage"),
            ],
            normalizers={
                "fundamentals": {
                    # Dict order = spec order: FMP → EODHD → AV
                    "Financial Modeling Prep": lambda data, **kw: (
                        call_order.append("FMP")
                        or FundamentalsSnapshot(
                            ticker="AAPL",
                            market_cap=None,
                            pe_ratio=None,
                            pb_ratio=None,
                            ps_ratio=None,
                            eps=None,
                            dividend_yield=None,
                            beta=None,
                            sector=None,
                            industry=None,
                            employees=None,
                            provider="FMP",
                            timestamp=datetime.now(timezone.utc),
                        )
                    ),
                    "EODHD": lambda data, **kw: (
                        call_order.append("EODHD")
                        or FundamentalsSnapshot(
                            ticker="AAPL",
                            market_cap=None,
                            pe_ratio=None,
                            pb_ratio=None,
                            ps_ratio=None,
                            eps=None,
                            dividend_yield=None,
                            beta=None,
                            sector=None,
                            industry=None,
                            employees=None,
                            provider="EODHD",
                            timestamp=datetime.now(timezone.utc),
                        )
                    ),
                    "Alpha Vantage": lambda data, **kw: (
                        call_order.append("AV")
                        or FundamentalsSnapshot(
                            ticker="AAPL",
                            market_cap=None,
                            pe_ratio=None,
                            pb_ratio=None,
                            ps_ratio=None,
                            eps=None,
                            dividend_yield=None,
                            beta=None,
                            sector=None,
                            industry=None,
                            employees=None,
                            provider="AV",
                            timestamp=datetime.now(timezone.utc),
                        )
                    ),
                }
            },
        )
        # Make Yahoo fail so we go to API-key chain
        svc._http.get.side_effect = [  # type: ignore[union-attr]
            ConnectionError("Yahoo down"),
            FakeHttpResponse(200, [{"symbol": "AAPL"}]),
        ]

        result = asyncio.run(svc.get_fundamentals("AAPL"))

        # First successful provider should be FMP (not AV which is alphabetically first)
        assert result.provider == "FMP"
        assert call_order[0] == "FMP"

    def test_dividends_order_polygon_eodhd_fmp(self) -> None:
        """AC-191-1: dividends chain is Polygon → EODHD → FMP."""
        from datetime import date

        svc = _make_data_service(
            settings=[
                _make_setting("Polygon.io"),
                _make_setting("EODHD"),
                _make_setting("Financial Modeling Prep"),
            ],
            normalizers={
                "dividends": {
                    # Spec order: Polygon → EODHD → FMP
                    "Polygon.io": lambda data, **kw: [
                        DividendRecord(
                            ticker="AAPL",
                            ex_date=date(2024, 1, 1),
                            pay_date=None,
                            record_date=None,
                            declaration_date=None,
                            dividend_amount=Decimal("0.24"),
                            currency="USD",
                            frequency=None,
                            provider="Polygon.io",
                        )
                    ],
                    "EODHD": lambda data, **kw: [
                        DividendRecord(
                            ticker="AAPL",
                            ex_date=date(2024, 1, 1),
                            pay_date=None,
                            record_date=None,
                            declaration_date=None,
                            dividend_amount=Decimal("0.24"),
                            currency="USD",
                            frequency=None,
                            provider="EODHD",
                        )
                    ],
                    "Financial Modeling Prep": lambda data, **kw: [
                        DividendRecord(
                            ticker="AAPL",
                            ex_date=date(2024, 1, 1),
                            pay_date=None,
                            record_date=None,
                            declaration_date=None,
                            dividend_amount=Decimal("0.24"),
                            currency="USD",
                            frequency=None,
                            provider="FMP",
                        )
                    ],
                }
            },
        )
        # Yahoo fail, then first API provider succeeds
        svc._http.get.side_effect = [  # type: ignore[union-attr]
            ConnectionError("Yahoo down"),
            FakeHttpResponse(200, {"results": []}),
        ]

        result = asyncio.run(svc.get_dividends("AAPL"))

        # Should be Polygon (first in spec), not EODHD (first alphabetically)
        assert result[0].provider == "Polygon.io"


# ═══════════════════════════════════════════════════════════════════════════
# Corrections: Finding 1 — Provider-Specific URL Construction
# ═══════════════════════════════════════════════════════════════════════════


class TestProviderSpecificURLs:
    """F1: _generic_api_fetch must use URL builders, not base_url?ticker=."""

    def test_eodhd_ohlcv_url_uses_builder(self) -> None:
        """EODHD OHLCV URL should contain /api/eod/AAPL.US, not ?ticker=AAPL."""
        captured_urls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            captured_urls.append(url)
            if "yahoo" in url.lower():
                raise ConnectionError("Yahoo down")
            return FakeHttpResponse(200, [{"date": "2024-01-01", "open": 185}])

        svc = _make_data_service(
            settings=[_make_setting("EODHD")],
            normalizers={
                "ohlcv": {
                    "EODHD": lambda data, **kw: [
                        OHLCVBar(
                            ticker="AAPL",
                            timestamp=__import__("datetime").datetime.now(
                                __import__("datetime").timezone.utc
                            ),
                            open=Decimal("185"),
                            high=Decimal("187"),
                            low=Decimal("184"),
                            close=Decimal("186.5"),
                            adj_close=None,
                            volume=1000000,
                            vwap=None,
                            trade_count=None,
                            provider="EODHD",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_ohlcv("AAPL"))

        # Find the EODHD call (not the Yahoo call)
        eodhd_urls = [u for u in captured_urls if "eodhd" in u.lower()]
        assert len(eodhd_urls) >= 1, f"No EODHD URL found in: {captured_urls}"
        assert "/api/eod/AAPL.US" in eodhd_urls[0], (
            f"Expected /api/eod/AAPL.US in URL, got: {eodhd_urls[0]}"
        )
        assert "?ticker=" not in eodhd_urls[0], (
            f"Generic ?ticker= pattern found: {eodhd_urls[0]}"
        )

    def test_query_param_auth_in_url_not_headers(self) -> None:
        """QUERY_PARAM providers (EODHD, FMP) should have api key in URL, not headers."""
        captured_headers: list[dict[str, str]] = []

        async def capture_get(
            url: str,
            headers: dict[str, str],
            *args: Any,
            **kwargs: Any,
        ) -> FakeHttpResponse:
            if "eodhd" in url.lower():
                captured_headers.append(headers)
            if "yahoo" in url.lower():
                raise ConnectionError("Yahoo down")
            return FakeHttpResponse(200, [])

        svc = _make_data_service(
            settings=[_make_setting("EODHD")],
            normalizers={
                "ohlcv": {
                    "EODHD": lambda data, **kw: [
                        OHLCVBar(
                            ticker="AAPL",
                            timestamp=__import__("datetime").datetime.now(
                                __import__("datetime").timezone.utc
                            ),
                            open=Decimal("185"),
                            high=Decimal("187"),
                            low=Decimal("184"),
                            close=Decimal("186.5"),
                            adj_close=None,
                            volume=1000000,
                            vwap=None,
                            trade_count=None,
                            provider="EODHD",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_ohlcv("AAPL"))

        # EODHD uses QUERY_PARAM auth — headers should be empty (no auth header)
        assert len(captured_headers) >= 1, "No EODHD request captured"
        assert captured_headers[0] == {}, (
            f"Expected empty headers for QUERY_PARAM provider, got: {captured_headers[0]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Corrections Pass 2: R2 — Finnhub Endpoint Selection
# ═══════════════════════════════════════════════════════════════════════════


class TestFinnhubEndpoints:
    """R2: FinnhubUrlBuilder must route each data type to its correct endpoint."""

    def test_finnhub_company_profile_url(self) -> None:
        """company_profile should hit /stock/profile2, not /quote."""
        captured_urls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            captured_urls.append(url)
            return FakeHttpResponse(
                200,
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc",
                    "finnhubIndustry": "Technology",
                    "marketCapitalization": 3000000,
                },
            )

        from datetime import datetime, timezone

        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            normalizers={
                "company_profile": {
                    "Finnhub": lambda data, **kw: FundamentalsSnapshot(
                        ticker="AAPL",
                        market_cap=None,
                        pe_ratio=None,
                        pb_ratio=None,
                        ps_ratio=None,
                        eps=None,
                        dividend_yield=None,
                        beta=None,
                        sector=None,
                        industry=None,
                        employees=None,
                        provider="Finnhub",
                        timestamp=datetime.now(timezone.utc),
                    ),
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_company_profile("AAPL"))

        finnhub_urls = [u for u in captured_urls if "finnhub" in u.lower()]
        assert len(finnhub_urls) >= 1, f"No Finnhub URL found in: {captured_urls}"
        assert "/stock/profile2" in finnhub_urls[0], (
            f"Expected /stock/profile2 in URL, got: {finnhub_urls[0]}"
        )
        assert "/quote?" not in finnhub_urls[0], (
            f"Fell back to /quote instead of /stock/profile2: {finnhub_urls[0]}"
        )

    def test_finnhub_insider_url(self) -> None:
        """insider should hit /stock/insider-transactions, not /quote."""
        captured_urls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            captured_urls.append(url)
            return FakeHttpResponse(200, {"data": []})

        from datetime import date

        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            normalizers={
                "insider": {
                    "Finnhub": lambda data, **kw: [
                        InsiderTransaction(
                            ticker="AAPL",
                            transaction_date=date(2024, 1, 10),
                            name="Tim Cook",
                            title="CEO",
                            transaction_code="S",
                            shares=50000,
                            price=None,
                            value=None,
                            shares_owned_after=None,
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_insider("AAPL"))

        finnhub_urls = [u for u in captured_urls if "finnhub" in u.lower()]
        assert len(finnhub_urls) >= 1, f"No Finnhub URL found in: {captured_urls}"
        assert "/stock/insider-transactions" in finnhub_urls[0], (
            f"Expected /stock/insider-transactions in URL, got: {finnhub_urls[0]}"
        )

    def test_finnhub_earnings_url(self) -> None:
        """earnings should hit /stock/earnings, not /quote."""
        captured_urls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            captured_urls.append(url)
            return FakeHttpResponse(200, [])

        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            normalizers={
                "earnings": {
                    "Finnhub": lambda data, **kw: [
                        EarningsReport(
                            ticker="AAPL",
                            fiscal_period="Q1",
                            report_date=__import__("datetime").date(2024, 1, 25),
                            fiscal_year=2024,
                            eps_actual=Decimal("2.18"),
                            eps_estimate=Decimal("2.10"),
                            eps_surprise=Decimal("0.08"),
                            revenue_actual=None,
                            revenue_estimate=None,
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_earnings("AAPL"))

        finnhub_urls = [u for u in captured_urls if "finnhub" in u.lower()]
        assert len(finnhub_urls) >= 1, f"No Finnhub URL found in: {captured_urls}"
        assert "/stock/earnings" in finnhub_urls[0], (
            f"Expected /stock/earnings in URL, got: {finnhub_urls[0]}"
        )

    def test_finnhub_economic_calendar_url(self) -> None:
        """economic_calendar should hit /calendar/economic, not /quote."""
        captured_urls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            captured_urls.append(url)
            return FakeHttpResponse(200, {"economicCalendar": []})

        svc = _make_data_service(
            settings=[_make_setting("Finnhub")],
            normalizers={
                "economic_calendar": {
                    "Finnhub": lambda data, **kw: [
                        EconomicCalendarEvent(
                            event="CPI",
                            country="US",
                            date=__import__("datetime").date(2024, 2, 13),
                            time=None,
                            actual=None,
                            forecast=None,
                            previous=None,
                            impact="high",
                            provider="Finnhub",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)

        asyncio.run(svc.get_economic_calendar())

        finnhub_urls = [u for u in captured_urls if "finnhub" in u.lower()]
        assert len(finnhub_urls) >= 1, f"No Finnhub URL found in: {captured_urls}"
        assert "/calendar/economic" in finnhub_urls[0], (
            f"Expected /calendar/economic in URL, got: {finnhub_urls[0]}"
        )
        assert "/quote?" not in finnhub_urls[0], (
            f"Fell back to /quote instead of /calendar/economic: {finnhub_urls[0]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Corrections Pass 2: R1 — POST Dispatch for POST-body Providers
# ═══════════════════════════════════════════════════════════════════════════


class TestPOSTDispatch:
    """R1: POST-body providers (SEC API) must use HTTP POST, not GET."""

    def test_sec_api_insider_uses_post(self) -> None:
        """SEC API insider fallback should call _http.post with JSON body."""
        post_calls: list[dict[str, Any]] = []
        get_calls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            get_calls.append(url)
            # Finnhub and FMP fail, SEC API should be reached via POST
            if "finnhub" in url.lower() or "financialmodelingprep" in url.lower():
                raise ConnectionError("Intentional provider failure")
            return FakeHttpResponse(200, {"hits": []})

        async def capture_post(
            url: str,
            headers: dict[str, str],
            timeout: int,
            json: Any = None,
        ) -> FakeHttpResponse:
            post_calls.append({"url": url, "json": json})
            return FakeHttpResponse(200, {"hits": {"hits": []}})

        from datetime import date

        svc = _make_data_service(
            settings=[
                _make_setting("Finnhub"),
                _make_setting("Financial Modeling Prep"),
                _make_setting("SEC API"),
            ],
            normalizers={
                "insider": {
                    "Finnhub": lambda data, **kw: (_ for _ in ()).throw(
                        Exception("Finnhub normalizer fail")
                    ),
                    "Financial Modeling Prep": lambda data, **kw: (_ for _ in ()).throw(
                        Exception("FMP normalizer fail")
                    ),
                    "SEC API": lambda data, **kw: [
                        InsiderTransaction(
                            ticker="AAPL",
                            transaction_date=date(2024, 1, 10),
                            name="Tim Cook",
                            title="CEO",
                            transaction_code="S",
                            shares=50000,
                            price=None,
                            value=None,
                            shares_owned_after=None,
                            provider="SEC API",
                        )
                    ],
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)
        svc._http.post = AsyncMock(side_effect=capture_post)

        asyncio.run(svc.get_insider("AAPL"))

        # SEC API should have been called via POST
        assert len(post_calls) >= 1, (
            f"SEC API should use POST, but no post calls were made. "
            f"GET calls: {get_calls}"
        )
        assert "search-index" in post_calls[0]["url"], (
            f"Expected SEC API search-index URL, got: {post_calls[0]['url']}"
        )

    def test_fmp_fundamentals_uses_get(self) -> None:
        """FMP fundamentals should still use HTTP GET (no regression)."""
        get_calls: list[str] = []

        async def capture_get(url: str, *args: Any, **kwargs: Any) -> FakeHttpResponse:
            get_calls.append(url)
            if "yahoo" in url.lower():
                raise ConnectionError("Yahoo down")
            return FakeHttpResponse(200, [{"symbol": "AAPL", "mktCap": 3000000}])

        from datetime import datetime, timezone

        svc = _make_data_service(
            settings=[_make_setting("Financial Modeling Prep")],
            normalizers={
                "fundamentals": {
                    "Financial Modeling Prep": lambda data, **kw: FundamentalsSnapshot(
                        ticker="AAPL",
                        market_cap=None,
                        pe_ratio=None,
                        pb_ratio=None,
                        ps_ratio=None,
                        eps=None,
                        dividend_yield=None,
                        beta=None,
                        sector=None,
                        industry=None,
                        employees=None,
                        provider="FMP",
                        timestamp=datetime.now(timezone.utc),
                    ),
                }
            },
        )
        svc._http.get = AsyncMock(side_effect=capture_get)
        svc._http.post = AsyncMock()

        asyncio.run(svc.get_fundamentals("AAPL"))

        # FMP uses GET — post should NOT have been called
        fmp_gets = [u for u in get_calls if "financialmodelingprep" in u.lower()]
        assert len(fmp_gets) >= 1, f"FMP GET not found. GET calls: {get_calls}"
        svc._http.post.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# R1/R2 Integration: Production Registry + URL Builder Composition (Pass 3)
# ═══════════════════════════════════════════════════════════════════════════


class TestProductionRegistryURLIntegration:
    """Verify that every provider's registry base_url composes correctly
    with its URL builder — no double-prefix segments in the resulting URL.

    This test imports the REAL PROVIDER_REGISTRY and REAL builders to catch
    mismatches that unit tests with synthetic base_urls would miss.
    """

    # Known path segments each builder prepends — if these appear in
    # the registry base_url AND the built URL, we have a double-prefix.
    _BUILDER_PATH_PREFIXES: dict[str, list[str]] = {
        "Financial Modeling Prep": ["/api/v3/"],
        "EODHD": ["/api/"],
        "Alpaca": ["/v2/"],
        "API Ninjas": ["/v1/"],
        "Tradier": ["/v1/"],
        "Alpha Vantage": ["/query"],
        "Nasdaq Data Link": ["/datatables/"],
    }

    def _build_url_for_provider(self, name: str) -> str:
        """Build a quote URL using the real registry + real builder."""
        from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY
        from zorivest_infra.market_data.url_builders import get_url_builder

        config = PROVIDER_REGISTRY[name]
        builder = get_url_builder(name)

        # Use build_request for POST providers, build_url for GET
        build_request_fn = getattr(builder, "build_request", None)
        if build_request_fn is not None:
            spec = build_request_fn(config.base_url, "quote", ["AAPL"], {})
            return spec.url
        return builder.build_url(config.base_url, "quote", ["AAPL"], {})

    def test_fmp_no_double_prefix(self) -> None:
        """FMP URL must not contain /api/v3/api/v3/."""
        url = self._build_url_for_provider("Financial Modeling Prep")
        assert "/api/v3/api/v3/" not in url, f"Double-prefix in FMP URL: {url}"
        assert "/api/v3/" in url, f"Missing expected path in FMP URL: {url}"

    def test_eodhd_no_double_prefix(self) -> None:
        """EODHD URL must not contain /api/api/."""
        url = self._build_url_for_provider("EODHD")
        assert "/api/api/" not in url, f"Double-prefix in EODHD URL: {url}"

    def test_alpaca_correct_host_and_path(self) -> None:
        """Alpaca URL must use data.alpaca.markets and not double /v2/v2/."""
        url = self._build_url_for_provider("Alpaca")
        assert "data.alpaca.markets" in url, f"Wrong host in Alpaca URL: {url}"
        assert "/v2/v2/" not in url, f"Double-prefix in Alpaca URL: {url}"

    def test_api_ninjas_no_double_prefix(self) -> None:
        """API Ninjas URL must not contain /v1/v1/."""
        url = self._build_url_for_provider("API Ninjas")
        assert "/v1/v1/" not in url, f"Double-prefix in API Ninjas URL: {url}"
        assert "/v1/" in url, f"Missing expected path in API Ninjas URL: {url}"

    def test_tradier_no_double_prefix(self) -> None:
        """Tradier URL must not contain /v1/v1/."""
        url = self._build_url_for_provider("Tradier")
        assert "/v1/v1/" not in url, f"Double-prefix in Tradier URL: {url}"
        assert "/v1/" in url, f"Missing expected path in Tradier URL: {url}"

    def test_alpha_vantage_no_double_prefix(self) -> None:
        """Alpha Vantage URL must not contain /query/query."""
        url = self._build_url_for_provider("Alpha Vantage")
        assert "/query/query" not in url, f"Double-prefix in AV URL: {url}"
        assert "/query" in url, f"Missing expected path in AV URL: {url}"

    def test_nasdaq_dl_no_double_prefix(self) -> None:
        """Nasdaq DL URL must not contain /api/v3/datatables/."""
        url = self._build_url_for_provider("Nasdaq Data Link")
        # The builder appends /datatables/ directly; if base_url has /api/v3
        # the result is /api/v3/datatables/ which is wrong
        assert "/api/v3/datatables/" not in url, (
            f"Double-prefix in Nasdaq DL URL: {url}"
        )
        assert "/datatables/" in url, f"Missing expected path in Nasdaq DL URL: {url}"

    def test_all_providers_produce_valid_urls(self) -> None:
        """Every registered provider must produce a URL starting with https://."""
        from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY

        failures = []
        for name in PROVIDER_REGISTRY:
            try:
                url = self._build_url_for_provider(name)
                if not url.startswith("https://"):
                    failures.append(f"{name}: URL does not start with https:// → {url}")
            except Exception as exc:
                failures.append(f"{name}: {exc}")
        assert not failures, "Provider URL failures:\n" + "\n".join(failures)
