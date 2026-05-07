"""Tests for ProviderConnectionService — MEU-60.

FIC-60 acceptance criteria with provider-specific validation tests.
All tests use mocked HTTP client and in-memory persistence.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from zorivest_core.application.provider_status import ProviderStatus
from zorivest_core.domain.enums import AuthMethod
from zorivest_core.domain.market_data import ProviderConfig
from zorivest_core.services.provider_connection_service import (
    ProviderConnectionService,
)
from zorivest_core.domain.market_provider_settings import MarketProviderSettings


# ── Test Fixtures ────────────────────────────────────────────────────────


def _make_registry() -> dict[str, ProviderConfig]:
    """Minimal registry for testing (subset of providers)."""
    return {
        "Alpha Vantage": ProviderConfig(
            name="Alpha Vantage",
            base_url="https://alphavantage.co",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="?function=GLOBAL_QUOTE&apikey={api_key}",
            default_rate_limit=5,
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
        "Finnhub": ProviderConfig(
            name="Finnhub",
            base_url="https://finnhub.io",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-Finnhub-Token",
            headers_template={"X-Finnhub-Token": "{api_key}"},
            test_endpoint="/quote?symbol=AAPL",
            default_rate_limit=60,
        ),
        "Financial Modeling Prep": ProviderConfig(
            name="Financial Modeling Prep",
            base_url="https://fmp.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="apikey",
            headers_template={},
            test_endpoint="/search?apikey={api_key}",
            default_rate_limit=250,
        ),
        "EODHD": ProviderConfig(
            name="EODHD",
            base_url="https://eodhd.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="api_token",
            headers_template={},
            test_endpoint="/real-time?api_token={api_key}",
            default_rate_limit=20,
        ),
        "Nasdaq Data Link": ProviderConfig(
            name="Nasdaq Data Link",
            base_url="https://data.nasdaq.com",
            auth_method=AuthMethod.QUERY_PARAM,
            auth_param_name="api_key",
            headers_template={},
            test_endpoint="/test?api_key={api_key}",
            default_rate_limit=50,
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
        "API Ninjas": ProviderConfig(
            name="API Ninjas",
            base_url="https://api-ninjas.com",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-Api-Key",
            headers_template={"X-Api-Key": "{api_key}"},
            test_endpoint="/test",
            default_rate_limit=60,
        ),
        "OpenFIGI": ProviderConfig(
            name="OpenFIGI",
            base_url="https://api.openfigi.com",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="X-OPENFIGI-APIKEY",
            headers_template={"X-OPENFIGI-APIKEY": "{api_key}"},
            test_endpoint="/mapping",
            default_rate_limit=10,
        ),
        "Alpaca": ProviderConfig(
            name="Alpaca",
            base_url="https://api.alpaca.markets",
            auth_method=AuthMethod.CUSTOM_HEADER,
            auth_param_name="APCA-API-KEY-ID",
            headers_template={
                "APCA-API-KEY-ID": "{api_key}",
                "APCA-API-SECRET-KEY": "{api_secret}",
            },
            test_endpoint="/account",
            default_rate_limit=200,
        ),
        "Tradier": ProviderConfig(
            name="Tradier",
            base_url="https://api.tradier.com",
            auth_method=AuthMethod.BEARER_HEADER,
            auth_param_name="Authorization",
            headers_template={"Authorization": "Bearer {api_key}"},
            test_endpoint="/user/profile",
            default_rate_limit=120,
        ),
    }


@dataclass
class MockResponse:
    """Mock HTTP response."""

    status_code: int
    _json: Any = None
    text: str = ""

    def json(self) -> Any:
        if self._json is None:
            raise ValueError("No JSON")
        return self._json


class MockHttpClient:
    """Mock async HTTP client."""

    def __init__(self, response: MockResponse | Exception | None = None) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], int]] = []

    async def get(
        self, url: str, headers: dict[str, str], timeout: int
    ) -> MockResponse:
        self.calls.append((url, headers, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        assert self.response is not None
        return self.response

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
        json: Any = None,
    ) -> MockResponse:
        self.calls.append((url, headers, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        assert self.response is not None
        return self.response


class MockEncryption:
    """Mock encryption that prefixes/strips 'ENC:'."""

    def encrypt(self, plaintext: str) -> str:
        return f"ENC:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext.removeprefix("ENC:")


class InMemoryRepo:
    """In-memory market provider settings repository."""

    def __init__(self) -> None:
        self._store: dict[str, MarketProviderSettings] = {}

    def get(self, name: str) -> MarketProviderSettings | None:
        return self._store.get(name)

    def save(self, model: MarketProviderSettings) -> None:
        self._store[model.provider_name] = model

    def list_all(self) -> list[MarketProviderSettings]:
        return list(self._store.values())

    def delete(self, name: str) -> None:
        self._store.pop(name, None)


class MockUoW:
    """Mock UnitOfWork with in-memory repo."""

    def __init__(self) -> None:
        self.market_provider_settings = InMemoryRepo()
        self._committed = False

    def __enter__(self) -> MockUoW:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        pass


class MockRateLimiter:
    """Mock rate limiter that tracks calls."""

    def __init__(self) -> None:
        self.call_count = 0

    async def wait_if_needed(self) -> None:
        self.call_count += 1


def _make_service(
    *,
    uow: MockUoW | None = None,
    http: MockHttpClient | None = None,
    rate_limiters: dict[str, MockRateLimiter] | None = None,
) -> tuple[ProviderConnectionService, MockUoW, MockHttpClient]:
    """Create a service with test doubles."""
    _uow = uow or MockUoW()
    _http = http or MockHttpClient()
    _enc = MockEncryption()
    _rl = rate_limiters or {}
    registry = _make_registry()
    svc = ProviderConnectionService(_uow, _enc, _http, _rl, registry)
    return svc, _uow, _http


def _configure_provider_in_uow(
    uow: MockUoW,
    name: str,
    api_key: str = "testkey123",
    api_secret: str | None = None,
    is_enabled: bool = True,
) -> None:
    """Pre-configure a provider in the mock UoW."""
    model = MarketProviderSettings(
        provider_name=name,
        encrypted_api_key=f"ENC:{api_key}",
        encrypted_api_secret=f"ENC:{api_secret}" if api_secret else None,
        rate_limit=5,
        timeout=30,
        is_enabled=is_enabled,
        created_at=datetime.now(),
    )
    uow.market_provider_settings.save(model)


# ── AC-1/AC-2: ProviderStatus + list_providers ──


class TestListProviders:
    """AC-1/AC-2: list_providers returns typed ProviderStatus for all 11."""

    def test_returns_list_of_provider_status(self) -> None:
        async def _run() -> None:
            svc, _, _ = _make_service()
            result = await svc.list_providers()
            assert len(result) == 11
            for item in result:
                assert isinstance(item, ProviderStatus)

        asyncio.run(_run())

    def test_default_status_no_settings(self) -> None:
        async def _run() -> None:
            svc, _, _ = _make_service()
            result = await svc.list_providers()
            av = next(p for p in result if p.provider_name == "Alpha Vantage")
            assert av.is_enabled is False
            assert av.has_api_key is False
            assert av.rate_limit == 5  # default from registry

        asyncio.run(_run())

    def test_status_with_configured_provider(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            svc, _, _ = _make_service(uow=uow)
            result = await svc.list_providers()
            fh = next(p for p in result if p.provider_name == "Finnhub")
            assert fh.is_enabled is True
            assert fh.has_api_key is True

        asyncio.run(_run())


# ── AC-3/AC-4/AC-5/AC-6: configure_provider ──


class TestConfigureProvider:
    """configure_provider PATCH semantics."""

    def test_encrypts_and_stores_api_key(self) -> None:
        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider("Alpha Vantage", api_key="mykey")
            model = uow.market_provider_settings.get("Alpha Vantage")
            assert model is not None
            assert model.encrypted_api_key == "ENC:mykey"

        asyncio.run(_run())

    def test_already_encrypted_key_passthrough(self) -> None:
        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider(
                "Alpha Vantage", api_key="ENC:already_encrypted"
            )
            model = uow.market_provider_settings.get("Alpha Vantage")
            assert model is not None
            assert model.encrypted_api_key == "ENC:already_encrypted"

        asyncio.run(_run())

    def test_dual_key_alpaca(self) -> None:
        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider("Alpaca", api_key="key", api_secret="secret")
            model = uow.market_provider_settings.get("Alpaca")
            assert model is not None
            assert model.encrypted_api_key == "ENC:key"
            assert model.encrypted_api_secret == "ENC:secret"

        asyncio.run(_run())

    def test_is_enabled_updates(self) -> None:
        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider("Finnhub", api_key="k", is_enabled=True)
            model = uow.market_provider_settings.get("Finnhub")
            assert model is not None
            assert model.is_enabled is True

            await svc.configure_provider("Finnhub", is_enabled=False)
            model = uow.market_provider_settings.get("Finnhub")
            assert model is not None
            assert model.is_enabled is False

        asyncio.run(_run())

    def test_patch_only_rate_limit(self) -> None:
        """Only provided fields are updated."""

        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider("Finnhub", api_key="k", is_enabled=True)
            await svc.configure_provider("Finnhub", rate_limit=100)
            model = uow.market_provider_settings.get("Finnhub")
            assert model is not None
            assert model.rate_limit == 100
            assert model.is_enabled is True  # Unchanged
            assert model.encrypted_api_key == "ENC:k"  # Unchanged

        asyncio.run(_run())

    def test_unknown_provider_raises(self) -> None:
        async def _run() -> None:
            import pytest as _pt

            svc, _, _ = _make_service()
            with _pt.raises(KeyError, match="Unknown"):
                await svc.configure_provider("Unknown", api_key="k")

        asyncio.run(_run())


# ── AC-7 through AC-15: Provider-specific validation ──


class TestAlphaVantageValidation:
    """AC-7: Global Quote OR Time Series."""

    def test_global_quote_key(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(200, _json={"Global Quote": {}}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is True
            assert msg == "Connection successful"

        asyncio.run(_run())

    def test_time_series_key(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(200, _json={"Time Series (Daily)": {}}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Alpha Vantage")
            assert success is True

        asyncio.run(_run())


class TestPolygonValidation:
    """AC-8: results OR status key."""

    def test_results_key(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Polygon.io")
            http = MockHttpClient(MockResponse(200, _json={"results": []}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Polygon.io")
            assert success is True

        asyncio.run(_run())

    def test_status_key(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Polygon.io")
            http = MockHttpClient(MockResponse(200, _json={"status": "OK"}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Polygon.io")
            assert success is True

        asyncio.run(_run())


class TestFinnhubValidation:
    """AC-9: 'c' key exists AND no 'error' key."""

    def test_valid_response(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            http = MockHttpClient(MockResponse(200, _json={"c": 150.0}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Finnhub")
            assert success is True

        asyncio.run(_run())

    def test_error_key_fails(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            http = MockHttpClient(
                MockResponse(200, _json={"c": 0, "error": "API rate limit"})
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Finnhub")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())


class TestFMPValidation:
    """AC-10: Non-empty list OR 403 with Legacy Endpoint."""

    def test_non_empty_list(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Financial Modeling Prep")
            http = MockHttpClient(MockResponse(200, _json=[{"symbol": "AAPL"}]))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Financial Modeling Prep")
            assert success is True

        asyncio.run(_run())

    def test_legacy_endpoint_403(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Financial Modeling Prep")
            http = MockHttpClient(
                MockResponse(403, text="Legacy Endpoint is deprecated")
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Financial Modeling Prep")
            assert success is True
            assert "deprecated" in msg.lower()

        asyncio.run(_run())


class TestEODHDValidation:
    """AC-11: 'code' OR 'close' key exists."""

    def test_code_key(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "EODHD")
            http = MockHttpClient(MockResponse(200, _json={"code": "AAPL.US"}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("EODHD")
            assert success is True

        asyncio.run(_run())


class TestNasdaqValidation:
    """AC-12: Nested datatable.data exists."""

    def test_nested_datatable(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Nasdaq Data Link")
            http = MockHttpClient(MockResponse(200, _json={"datatable": {"data": []}}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Nasdaq Data Link")
            assert success is True

        asyncio.run(_run())


class TestSECValidation:
    """AC-13: List; first item has 'ticker' or 'cik'."""

    def test_list_with_cik(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "SEC API")
            http = MockHttpClient(MockResponse(200, _json=[{"cik": "0001234"}]))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("SEC API")
            assert success is True

        asyncio.run(_run())

    def test_empty_list_succeeds(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "SEC API")
            http = MockHttpClient(MockResponse(200, _json=[]))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("SEC API")
            assert success is True

        asyncio.run(_run())


class TestAPINinjasValidation:
    """AC-14: Both 'price' AND 'name' exist."""

    def test_both_keys_present(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "API Ninjas")
            http = MockHttpClient(
                MockResponse(200, _json={"price": 150.0, "name": "AAPL"})
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("API Ninjas")
            assert success is True

        asyncio.run(_run())


# ── AC-16 through AC-20: HTTP status interpretation ──


class TestHTTPStatusInterpretation:
    """AC-16/17/18/19/20: HTTP status codes."""

    def test_200_unexpected_json(self) -> None:
        """AC-16: 200 + unexpected JSON."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(200, _json={"weird": "data"}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())

    def test_401_invalid_api_key(self) -> None:
        """AC-17: 401."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(401))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is False
            assert "Invalid API key" in msg

        asyncio.run(_run())

    def test_429_rate_limit(self) -> None:
        """AC-18: 429."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(429))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is False
            assert "Rate limit" in msg

        asyncio.run(_run())

    def test_timeout(self) -> None:
        """AC-19: Timeout."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(TimeoutError("timed out"))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is False
            assert "timeout" in msg.lower()

        asyncio.run(_run())

    def test_connection_error(self) -> None:
        """AC-20: ConnectionError."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(ConnectionError("DNS failure"))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpha Vantage")
            assert success is False
            assert "failed" in msg.lower()

        asyncio.run(_run())


# ── AC-21: remove_api_key ──


class TestRemoveApiKey:
    """AC-21: remove_api_key clears key and disables."""

    def test_removes_and_disables(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            svc, _, _ = _make_service(uow=uow)
            await svc.remove_api_key("Finnhub")
            model = uow.market_provider_settings.get("Finnhub")
            assert model is not None
            assert model.encrypted_api_key is None
            assert model.encrypted_api_secret is None
            assert model.is_enabled is False

        asyncio.run(_run())


# ── AC-22/23: test_all_providers ──


class TestTestAllProviders:
    """AC-22/23: Semaphore + only configured providers."""

    def test_only_tests_providers_with_keys(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            # Only configure 2 out of 12
            _configure_provider_in_uow(uow, "Finnhub")
            _configure_provider_in_uow(uow, "Tradier")
            http = MockHttpClient(MockResponse(200, _json={"c": 150.0}))
            svc, _, _ = _make_service(uow=uow, http=http)
            results = await svc.test_all_providers()
            assert len(results) == 2
            names = {r[0] for r in results}
            assert names == {"Finnhub", "Tradier"}

        asyncio.run(_run())

    def test_respects_semaphore(self) -> None:
        """Test that semaphore limits concurrency to 2."""

        async def _run() -> None:
            uow = MockUoW()
            for name in ["Finnhub", "Tradier", "EODHD"]:
                _configure_provider_in_uow(uow, name)
            http = MockHttpClient(MockResponse(200, _json={"c": 150.0}))
            svc, _, _ = _make_service(uow=uow, http=http)
            # Verify the semaphore value is 2
            assert svc._test_semaphore._value == 2
            results = await svc.test_all_providers()
            assert len(results) == 3

        asyncio.run(_run())


# ── AC-24: Connection test updates DB ──


class TestConnectionUpdatesDB:
    """AC-24: test updates last_tested_at and last_test_status."""

    def test_updates_test_status(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            http = MockHttpClient(MockResponse(200, _json={"c": 150.0}))
            svc, _, _ = _make_service(uow=uow, http=http)
            await svc.test_connection("Finnhub")
            model = uow.market_provider_settings.get("Finnhub")
            assert model is not None
            assert model.last_tested_at is not None
            assert model.last_test_status == "success"

        asyncio.run(_run())


# ── AC-25: Rate limiter integration ──


class TestRateLimiterIntegration:
    """AC-25: HTTP calls use rate limiter."""

    def test_rate_limiter_called(self) -> None:
        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Finnhub")
            http = MockHttpClient(MockResponse(200, _json={"c": 150.0}))
            rl = MockRateLimiter()
            svc, _, _ = _make_service(uow=uow, http=http, rate_limiters={"Finnhub": rl})
            await svc.test_connection("Finnhub")
            assert rl.call_count == 1

        asyncio.run(_run())


# ── AC-26: Dual-key (Alpaca) storage ──


class TestDualKeyStorage:
    """AC-26: Alpaca stores both api_key and api_secret."""

    def test_stores_both_keys(self) -> None:
        async def _run() -> None:
            svc, uow, _ = _make_service()
            await svc.configure_provider(
                "Alpaca", api_key="alpaca_key", api_secret="alpaca_secret"
            )
            model = uow.market_provider_settings.get("Alpaca")
            assert model is not None
            assert model.encrypted_api_key == "ENC:alpaca_key"
            assert model.encrypted_api_secret == "ENC:alpaca_secret"

        asyncio.run(_run())


# ── AC-27: OpenFIGI provider-specific validation ──


class TestOpenFIGIValidation:
    """OpenFIGI uses POST with provider-specific validator."""

    def test_openfigi_valid_data_list(self) -> None:
        """OpenFIGI success: list with 'data' key in first element."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "OpenFIGI")
            http = MockHttpClient(
                MockResponse(200, _json=[{"data": [{"figi": "BBG"}]}])
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("OpenFIGI")
            assert success is True
            assert msg == "Connection successful"

        asyncio.run(_run())


# ── Tradier provider-specific validation ──


class TestTradierValidation:
    """Tradier /user/profile returns {"profile": {"account": {...}}}.

    Validator accepts: {"profile": {}} — key presence confirms valid auth.
    Validator rejects: {"fault": {"faultstring": "..."}}, unexpected shapes.
    """

    def test_valid_profile_response(self) -> None:
        """Tradier success: response contains 'profile' key."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Tradier")
            http = MockHttpClient(
                MockResponse(
                    200, _json={"profile": {"account": {"account_number": "123"}}}
                )
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Tradier")
            assert success is True
            assert msg == "Connection successful"

        asyncio.run(_run())

    def test_minimal_profile_response(self) -> None:
        """Tradier success: empty profile dict still valid."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Tradier")
            http = MockHttpClient(MockResponse(200, _json={"profile": {}}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, _ = await svc.test_connection("Tradier")
            assert success is True

        asyncio.run(_run())

    def test_fault_response_rejected(self) -> None:
        """Tradier failure: 'fault' key indicates invalid API key or auth error."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Tradier")
            http = MockHttpClient(
                MockResponse(
                    200,
                    _json={"fault": {"faultstring": "Invalid ApiKey"}},
                )
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Tradier")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())

    def test_unexpected_json_shape_rejected(self) -> None:
        """Tradier failure: response without 'profile' key."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Tradier")
            http = MockHttpClient(MockResponse(200, _json={"error": "unauthorized"}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Tradier")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())

    def test_xml_response_fails_gracefully(self) -> None:
        """Tradier failure: XML response (json parse throws) → unexpected response.

        This is the root cause of the original bug: Tradier returns XML
        when Accept header is missing. response.json() throws → data=None.
        """

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Tradier")
            # MockResponse with _json=None causes json() to raise ValueError
            http = MockHttpClient(
                MockResponse(200, _json=None, text="<xml>profile</xml>")
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Tradier")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())


# ── Alpaca provider-specific validation ──


class TestAlpacaValidation:
    """Alpaca /v2/stocks/AAPL/snapshot returns market data snapshot.

    Validator accepts: {"latestTrade": ..., "latestQuote": ...} — market data keys.
    Validator rejects: {"code": 40110000, "message": "..."}, unexpected shapes.
    """

    def test_valid_snapshot_response(self) -> None:
        """Alpaca success: response contains 'latestTrade' key."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpaca")
            http = MockHttpClient(
                MockResponse(
                    200,
                    _json={
                        "latestTrade": {"p": 150.0, "s": 100},
                        "latestQuote": {"bp": 149.9, "ap": 150.1},
                    },
                )
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpaca")
            assert success is True
            assert msg == "Connection successful"

        asyncio.run(_run())

    def test_quote_only_response(self) -> None:
        """Alpaca success: response with only 'latestQuote' also valid."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpaca")
            http = MockHttpClient(
                MockResponse(200, _json={"latestQuote": {"bp": 149.9}})
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpaca")
            assert success is True

        asyncio.run(_run())

    def test_error_code_response_rejected(self) -> None:
        """Alpaca failure: 'code' key indicates API error."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpaca")
            http = MockHttpClient(
                MockResponse(
                    200,
                    _json={"code": 40110000, "message": "request is not authorized"},
                )
            )
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpaca")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())

    def test_unexpected_json_shape_rejected(self) -> None:
        """Alpaca failure: response without snapshot keys."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpaca")
            http = MockHttpClient(MockResponse(200, _json={"error": "unauthorized"}))
            svc, _, _ = _make_service(uow=uow, http=http)
            success, msg = await svc.test_connection("Alpaca")
            assert success is False
            assert "unexpected" in msg.lower()

        asyncio.run(_run())


# ═══════════════════════════════════════════════════════════════════════════
# Corrections: Finding 4 — display_name Regression Coverage
# ═══════════════════════════════════════════════════════════════════════════


class TestDisplayNameRegression:
    """F4: display_name must distinguish rebranded providers from non-rebranded."""

    def test_polygon_produces_display_name_massive(self) -> None:
        """Polygon.io key → config.name='Massive' → display_name='Massive'."""

        async def _run() -> None:
            uow = MockUoW()
            # Enable Polygon.io so it appears in list
            _configure_provider_in_uow(uow, "Polygon.io")
            http = MockHttpClient(MockResponse(200, _json={}))
            svc, _, _ = _make_service(uow=uow, http=http)
            providers = await svc.list_providers()
            polygon = next(p for p in providers if p.provider_name == "Polygon.io")
            assert polygon.display_name == "Massive", (
                f"Expected display_name='Massive', got '{polygon.display_name}'"
            )

        asyncio.run(_run())

    def test_non_rebranded_provider_has_no_display_name(self) -> None:
        """Alpha Vantage key == config.name → display_name=None."""

        async def _run() -> None:
            uow = MockUoW()
            _configure_provider_in_uow(uow, "Alpha Vantage")
            http = MockHttpClient(MockResponse(200, _json={}))
            svc, _, _ = _make_service(uow=uow, http=http)
            providers = await svc.list_providers()
            av = next(p for p in providers if p.provider_name == "Alpha Vantage")
            assert av.display_name is None, (
                f"Expected display_name=None for non-rebranded provider, got '{av.display_name}'"
            )

        asyncio.run(_run())
