"""Tests for Layer 4 expansion normalizers — MEU-190/191.

Validates all 24 normalizer functions in normalizers.py that convert
provider-specific JSON responses into expansion DTOs.
"""

from __future__ import annotations

from decimal import Decimal


from zorivest_infra.market_data.normalizers import (
    normalize_alpaca_ohlcv,
    normalize_av_calendar,
    normalize_av_earnings,
    normalize_av_fundamentals,
    normalize_eodhd_dividends,
    normalize_eodhd_fundamentals,
    normalize_eodhd_ohlcv,
    normalize_eodhd_splits,
    normalize_finnhub_calendar,
    normalize_finnhub_earnings,
    normalize_finnhub_insider,
    normalize_finnhub_profile,
    normalize_fmp_calendar,
    normalize_fmp_dividends,
    normalize_fmp_earnings,
    normalize_fmp_fundamentals,
    normalize_fmp_insider,
    normalize_fmp_profile,
    normalize_fmp_splits,
    normalize_polygon_dividends,
    normalize_polygon_ohlcv,
    normalize_polygon_splits,
    normalize_sec_insider,
    NORMALIZERS,
)


# ── OHLCV ──────────────────────────────────────────────────────────────


class TestNormalizeAlpacaOHLCV:
    def test_full_response(self) -> None:
        data = {
            "bars": [
                {
                    "t": 1700000000,
                    "o": 150.0,
                    "h": 155.0,
                    "l": 149.0,
                    "c": 153.0,
                    "v": 1000,
                    "vw": 152.0,
                    "n": 50,
                }
            ]
        }
        result = normalize_alpaca_ohlcv(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].ticker == "AAPL"
        assert result[0].close == Decimal("153.0")
        assert result[0].provider == "Alpaca"
        assert result[0].vwap == Decimal("152.0")
        assert result[0].trade_count == 50

    def test_empty_response(self) -> None:
        assert normalize_alpaca_ohlcv({"bars": []}, ticker="X") == []
        assert normalize_alpaca_ohlcv({}, ticker="X") == []


class TestNormalizeEodhdOHLCV:
    def test_full_response(self) -> None:
        data = [
            {
                "date": "2024-01-15",
                "open": 100,
                "high": 105,
                "low": 99,
                "close": 103,
                "adjusted_close": 102,
                "volume": 500,
            }
        ]
        result = normalize_eodhd_ohlcv(data, ticker="MSFT")
        assert len(result) == 1
        assert result[0].ticker == "MSFT"
        assert result[0].close == Decimal("103")
        assert result[0].adj_close == Decimal("102")
        assert result[0].provider == "EODHD"

    def test_empty_response(self) -> None:
        assert normalize_eodhd_ohlcv([], ticker="X") == []
        assert normalize_eodhd_ohlcv({}, ticker="X") == []


class TestNormalizePolygonOHLCV:
    def test_full_response(self) -> None:
        data = {
            "ticker": "TSLA",
            "results": [
                {
                    "t": 1700000000000,
                    "o": 200,
                    "h": 210,
                    "l": 195,
                    "c": 205,
                    "v": 2000,
                    "vw": 203,
                    "n": 100,
                }
            ],
        }
        result = normalize_polygon_ohlcv(data, ticker="TSLA")
        assert len(result) == 1
        assert result[0].close == Decimal("205")
        assert result[0].provider == "Polygon.io"

    def test_empty_response(self) -> None:
        assert normalize_polygon_ohlcv({"results": []}) == []


# ── Fundamentals ───────────────────────────────────────────────────────


class TestNormalizeFmpFundamentals:
    def test_full_response(self) -> None:
        data = [
            {
                "symbol": "AAPL",
                "mktCap": 3000000000000,
                "pe": 28.5,
                "eps": 6.5,
                "beta": 1.2,
                "sector": "Technology",
                "industry": "Consumer Electronics",
            }
        ]
        result = normalize_fmp_fundamentals(data, ticker="AAPL")
        assert result.ticker == "AAPL"
        assert result.market_cap == Decimal("3000000000000")
        assert result.pe_ratio == Decimal("28.5")
        assert result.provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        result = normalize_fmp_fundamentals([], ticker="X")
        assert result.ticker == "X"
        assert result.market_cap is None


class TestNormalizeEodhdFundamentals:
    def test_full_response(self) -> None:
        data = {
            "General": {"Code": "MSFT", "Sector": "Tech", "Industry": "Software"},
            "Highlights": {
                "MarketCapitalization": 2800000000000,
                "PERatio": 35,
                "EarningsShare": 11.0,
            },
        }
        result = normalize_eodhd_fundamentals(data, ticker="MSFT")
        assert result.ticker == "MSFT"
        assert result.pe_ratio == Decimal("35")
        assert result.provider == "EODHD"

    def test_empty_response(self) -> None:
        result = normalize_eodhd_fundamentals({}, ticker="X")
        assert result.ticker == "X"


class TestNormalizeAvFundamentals:
    def test_full_response(self) -> None:
        data = {
            "Symbol": "GOOG",
            "MarketCapitalization": "2000000000000",
            "PERatio": "25",
            "EPS": "5.5",
            "Beta": "1.1",
            "Sector": "Communication",
            "Industry": "Internet",
            "FullTimeEmployees": "180000",
        }
        result = normalize_av_fundamentals(data, ticker="GOOG")
        assert result.ticker == "GOOG"
        assert result.eps == Decimal("5.5")
        assert result.employees == 180000
        assert result.provider == "Alpha Vantage"

    def test_none_string_fields(self) -> None:
        """Alpha Vantage returns 'None' strings for missing fields."""
        data = {"Symbol": "X", "PERatio": "None", "EPS": "None"}
        result = normalize_av_fundamentals(data, ticker="X")
        assert result.pe_ratio is None
        assert result.eps is None


# ── Earnings ───────────────────────────────────────────────────────────


class TestNormalizeFinnhubEarnings:
    def test_full_response(self) -> None:
        data = [
            {
                "symbol": "AAPL",
                "quarter": 1,
                "year": 2024,
                "period": "2024-03-31",
                "actual": 1.53,
                "estimate": 1.50,
                "surprise": 0.03,
            }
        ]
        result = normalize_finnhub_earnings(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].fiscal_period == "Q1"
        assert result[0].eps_actual == Decimal("1.53")
        assert result[0].provider == "Finnhub"

    def test_empty_response(self) -> None:
        assert normalize_finnhub_earnings([], ticker="X") == []


class TestNormalizeFmpEarnings:
    def test_full_response(self) -> None:
        data = [
            {
                "symbol": "MSFT",
                "date": "2024-01-25",
                "fiscalPeriod": "Q2",
                "fiscalDateEnding": "2024-12-31",
                "actualEarningResult": 2.93,
                "estimatedEarning": 2.78,
            }
        ]
        result = normalize_fmp_earnings(data, ticker="MSFT")
        assert len(result) == 1
        assert result[0].eps_actual == Decimal("2.93")
        assert result[0].provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        assert normalize_fmp_earnings([], ticker="X") == []


class TestNormalizeAvEarnings:
    def test_full_response(self) -> None:
        data = {
            "quarterlyEarnings": [
                {
                    "fiscalDateEnding": "2024-03-31",
                    "reportedDate": "2024-04-25",
                    "reportedEPS": "1.53",
                    "estimatedEPS": "1.50",
                }
            ]
        }
        result = normalize_av_earnings(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].eps_actual == Decimal("1.53")
        assert result[0].provider == "Alpha Vantage"

    def test_empty_response(self) -> None:
        assert normalize_av_earnings({}, ticker="X") == []


# ── Dividends ──────────────────────────────────────────────────────────


class TestNormalizePolygonDividends:
    def test_full_response(self) -> None:
        data = {
            "results": [
                {
                    "ticker": "AAPL",
                    "cash_amount": 0.24,
                    "currency": "USD",
                    "ex_dividend_date": "2024-02-09",
                    "record_date": "2024-02-12",
                    "pay_date": "2024-02-15",
                    "frequency": 4,
                }
            ]
        }
        result = normalize_polygon_dividends(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].dividend_amount == Decimal("0.24")
        assert result[0].provider == "Polygon.io"

    def test_empty_response(self) -> None:
        assert normalize_polygon_dividends({"results": []}) == []


class TestNormalizeEodhdDividends:
    def test_full_response(self) -> None:
        data = [{"date": "2024-02-09", "value": 0.24, "currency": "USD"}]
        result = normalize_eodhd_dividends(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].dividend_amount == Decimal("0.24")
        assert result[0].provider == "EODHD"

    def test_empty_response(self) -> None:
        assert normalize_eodhd_dividends([], ticker="X") == []


class TestNormalizeFmpDividends:
    def test_full_response(self) -> None:
        data = {"historical": [{"date": "2024-02-09", "dividend": 0.24}]}
        result = normalize_fmp_dividends(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].dividend_amount == Decimal("0.24")
        assert result[0].provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        assert normalize_fmp_dividends({"historical": []}) == []


# ── Splits ─────────────────────────────────────────────────────────────


class TestNormalizePolygonSplits:
    def test_full_response(self) -> None:
        data = {
            "results": [
                {
                    "ticker": "AAPL",
                    "execution_date": "2020-08-31",
                    "split_from": 1,
                    "split_to": 4,
                }
            ]
        }
        result = normalize_polygon_splits(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].ratio_from == 1
        assert result[0].ratio_to == 4
        assert result[0].provider == "Polygon.io"

    def test_empty_response(self) -> None:
        assert normalize_polygon_splits({"results": []}) == []


class TestNormalizeEodhdSplits:
    def test_full_response(self) -> None:
        data = [{"date": "2020-08-31", "split": "4/1"}]
        result = normalize_eodhd_splits(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].ratio_to == 4
        assert result[0].ratio_from == 1
        assert result[0].provider == "EODHD"

    def test_empty_response(self) -> None:
        assert normalize_eodhd_splits([], ticker="X") == []


class TestNormalizeFmpSplits:
    def test_full_response(self) -> None:
        data = {
            "historical": [{"date": "2020-08-31", "numerator": 4, "denominator": 1}]
        }
        result = normalize_fmp_splits(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].ratio_to == 4
        assert result[0].ratio_from == 1
        assert result[0].provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        assert normalize_fmp_splits({"historical": []}) == []


# ── Insider ────────────────────────────────────────────────────────────


class TestNormalizeFinnhubInsider:
    def test_full_response(self) -> None:
        data = {
            "data": [
                {
                    "symbol": "AAPL",
                    "name": "Tim Cook",
                    "transactionDate": "2024-01-15",
                    "transactionCode": "S",
                    "share": 50000,
                    "transactionPrice": 185.0,
                }
            ]
        }
        result = normalize_finnhub_insider(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].name == "Tim Cook"
        assert result[0].shares == 50000
        assert result[0].provider == "Finnhub"

    def test_empty_response(self) -> None:
        assert normalize_finnhub_insider({"data": []}) == []


class TestNormalizeFmpInsider:
    def test_full_response(self) -> None:
        data = [
            {
                "symbol": "AAPL",
                "reportingName": "Tim Cook",
                "transactionDate": "2024-01-15",
                "transactionType": "S-Sale",
                "securitiesTransacted": 50000,
                "price": 185.0,
            }
        ]
        result = normalize_fmp_insider(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].name == "Tim Cook"
        assert result[0].provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        assert normalize_fmp_insider([], ticker="X") == []


class TestNormalizeSecInsider:
    def test_full_response(self) -> None:
        data = [
            {
                "reportingOwner": {"name": "Tim Cook"},
                "transactionDate": "2024-01-15",
                "transactionCode": "S",
                "transactionShares": 50000,
                "transactionPricePerShare": 185.0,
            }
        ]
        result = normalize_sec_insider(data, ticker="AAPL")
        assert len(result) == 1
        assert result[0].name == "Tim Cook"
        assert result[0].provider == "SEC API"

    def test_empty_response(self) -> None:
        assert normalize_sec_insider([], ticker="X") == []


# ── Economic Calendar ──────────────────────────────────────────────────


class TestNormalizeFinnhubCalendar:
    def test_full_response(self) -> None:
        data = {
            "economicCalendar": [
                {
                    "event": "GDP",
                    "country": "US",
                    "date": "2024-01-25",
                    "impact": "high",
                    "actual": 3.2,
                    "estimate": 3.0,
                    "prev": 2.9,
                }
            ]
        }
        result = normalize_finnhub_calendar(data)
        assert len(result) == 1
        assert result[0].event == "GDP"
        assert result[0].country == "US"
        assert result[0].actual == "3.2"
        assert result[0].provider == "Finnhub"

    def test_empty_response(self) -> None:
        assert normalize_finnhub_calendar({}) == []


class TestNormalizeFmpCalendar:
    def test_full_response(self) -> None:
        data = [
            {
                "event": "CPI",
                "country": "US",
                "date": "2024-02-13",
                "impact": "high",
                "actual": 3.1,
                "estimate": 3.0,
                "previous": 3.4,
            }
        ]
        result = normalize_fmp_calendar(data)
        assert len(result) == 1
        assert result[0].event == "CPI"
        assert result[0].previous == "3.4"
        assert result[0].provider == "Financial Modeling Prep"

    def test_empty_response(self) -> None:
        assert normalize_fmp_calendar([]) == []


class TestNormalizeAvCalendar:
    def test_full_response(self) -> None:
        data = {
            "data": [
                {
                    "name": "Unemployment Rate",
                    "country": "US",
                    "date": "2024-02-02",
                    "value": "3.7",
                }
            ]
        }
        result = normalize_av_calendar(data)
        assert len(result) == 1
        assert result[0].event == "Unemployment Rate"
        assert result[0].actual == "3.7"
        assert result[0].provider == "Alpha Vantage"

    def test_empty_response(self) -> None:
        assert normalize_av_calendar({}) == []


# ── Company Profile ────────────────────────────────────────────────────


class TestNormalizeFmpProfile:
    def test_delegates_to_fundamentals(self) -> None:
        data = [{"symbol": "AAPL", "mktCap": 3000000000000, "sector": "Technology"}]
        result = normalize_fmp_profile(data, ticker="AAPL")
        assert result.ticker == "AAPL"
        assert result.provider == "Financial Modeling Prep"


class TestNormalizeFinnhubProfile:
    def test_full_response(self) -> None:
        data = {
            "ticker": "AAPL",
            "marketCapitalization": 3000000,
            "finnhubIndustry": "Technology",
        }
        result = normalize_finnhub_profile(data, ticker="AAPL")
        assert result.ticker == "AAPL"
        assert result.sector == "Technology"
        assert result.provider == "Finnhub"

    def test_empty_response(self) -> None:
        result = normalize_finnhub_profile({}, ticker="X")
        assert result.ticker == "X"


class TestNormalizeEodhdProfile:
    def test_delegates_to_fundamentals(self) -> None:
        data = {"General": {"Code": "MSFT", "Sector": "Tech"}, "Highlights": {}}
        from zorivest_infra.market_data.normalizers import normalize_eodhd_profile

        actual = normalize_eodhd_profile(data, ticker="MSFT")
        assert actual.ticker == "MSFT"
        assert actual.provider == "EODHD"


# ── Registry ───────────────────────────────────────────────────────────


class TestNormalizersRegistry:
    def test_all_data_types_present(self) -> None:
        expected = {
            "ohlcv",
            "fundamentals",
            "earnings",
            "dividends",
            "splits",
            "insider",
            "economic_calendar",
            "company_profile",
        }
        assert set(NORMALIZERS.keys()) == expected

    def test_each_type_has_three_providers(self) -> None:
        for data_type, providers in NORMALIZERS.items():
            assert len(providers) >= 3, (
                f"{data_type} has {len(providers)} providers, expected ≥3"
            )

    def test_all_values_are_callable(self) -> None:
        for data_type, providers in NORMALIZERS.items():
            for name, func in providers.items():
                assert callable(func), (
                    f"NORMALIZERS['{data_type}']['{name}'] is not callable"
                )
