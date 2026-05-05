"""ProviderConnectionService — MEU-60.

Service for managing provider credentials and testing connectivity.
Source: docs/build-plan/08-market-data.md §8.3a + §8.6.
"""

# pyright: reportArgumentType=false, reportReturnType=false, reportAttributeAccessIssue=false
# SQLAlchemy Column[T] types need suppression for Column[T] → T assignments.

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Mapping, Protocol

from zorivest_core.application.provider_status import ProviderStatus
from zorivest_core.domain.enums import AuthMethod
from zorivest_core.domain.market_data import ProviderConfig
from zorivest_core.domain.market_provider_settings import MarketProviderSettings


class HttpClient(Protocol):
    """Async HTTP client protocol for connection testing."""

    async def get(self, url: str, headers: dict[str, str], timeout: int) -> Any: ...

    async def post(
        self, url: str, headers: dict[str, str], timeout: int, json: Any = None
    ) -> Any: ...


class HttpClientWithSession(HttpClient, Protocol):
    """Extended protocol for clients that support cookie-based session requests.

    Used by Yahoo Finance crumb flow: GET fc.yahoo.com → cookie →
    GET /v1/test/getcrumb — requires session cookie persistence.
    """

    async def get_with_cookies(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
        cookies: dict[str, str],
    ) -> Any: ...


class EncryptionService(Protocol):
    """API key encryption/decryption protocol."""

    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


class RateLimiterProtocol(Protocol):
    """Rate limiter protocol."""

    async def wait_if_needed(self) -> None: ...


# ── Provider-specific response validators (§8.6) ──

_PROVIDER_VALIDATORS: dict[str, Any] = {}


def _register_validator(
    provider_name: str,
) -> Any:
    """Decorator to register a provider-specific response validator."""

    def decorator(func: Any) -> Any:
        _PROVIDER_VALIDATORS[provider_name] = func
        return func

    return decorator


@_register_validator("Alpha Vantage")
def _validate_alphavantage(data: Any) -> bool:
    """AC-7: Success when 'Global Quote' OR 'Time Series' key exists."""
    if isinstance(data, dict):
        return "Global Quote" in data or any(k.startswith("Time Series") for k in data)
    return False


@_register_validator("Polygon.io")
def _validate_polygon(data: Any) -> bool:
    """AC-8: Success when 'results' OR 'status' key exists."""
    if isinstance(data, dict):
        return "results" in data or "status" in data
    return False


@_register_validator("Finnhub")
def _validate_finnhub(data: Any) -> bool:
    """AC-9: Success when 'c' key exists AND no 'error' key."""
    if isinstance(data, dict):
        return "c" in data and "error" not in data
    return False


@_register_validator("Financial Modeling Prep")
def _validate_fmp(data: Any) -> bool:
    """AC-10: Success when response is non-empty list."""
    if isinstance(data, list):
        return len(data) > 0
    return False


@_register_validator("EODHD")
def _validate_eodhd(data: Any) -> bool:
    """AC-11: Success when 'code' OR 'close' key exists."""
    if isinstance(data, dict):
        return "code" in data or "close" in data
    return False


@_register_validator("Nasdaq Data Link")
def _validate_nasdaq(data: Any) -> bool:
    """AC-12: Success when nested datatable.data exists."""
    if isinstance(data, dict):
        datatable = data.get("datatable")
        if isinstance(datatable, dict):
            return "data" in datatable
    return False


@_register_validator("SEC API")
def _validate_sec(data: Any) -> bool:
    """AC-13: Success when response is a list; first item has 'ticker' or 'cik'."""
    if isinstance(data, list):
        if len(data) == 0:
            return True  # Empty list is valid (no results)
        first = data[0]
        if isinstance(first, dict):
            return "ticker" in first or "cik" in first
    return False


@_register_validator("API Ninjas")
def _validate_api_ninjas(data: Any) -> bool:
    """AC-14: Success when both 'price' AND 'name' keys exist."""
    if isinstance(data, dict):
        return "price" in data and "name" in data
    return False


@_register_validator("Yahoo Finance")
def _validate_yahoo_finance(data: Any) -> bool:
    """Free provider: crumb endpoint returns a plain text crumb string.

    After the cookie+crumb dance, we call the v7/finance/quote endpoint.
    Success when 'quoteResponse' key exists (v7 quote response shape).
    The generic crumb text response from /v1/test/getcrumb is also accepted.
    """
    if isinstance(data, str) and len(data) > 0:
        return True  # Crumb text = service is reachable
    if isinstance(data, dict):
        return "quoteResponse" in data or "chart" in data or "quotes" in data
    return False


@_register_validator("TradingView")
def _validate_tradingview(data: Any) -> bool:
    """Scanner endpoint returns JSON with 'totalCount' and 'data' fields.

    Any non-negative totalCount means the scanner responded successfully.
    This is the same endpoint used by tradingview-screener and tvscreener.
    """
    if isinstance(data, dict):
        return "totalCount" in data
    return False


@_register_validator("OpenFIGI")
def _validate_openfigi(data: Any) -> bool:
    """OpenFIGI /v3/mapping returns list of dicts with 'data' key on success.

    Accepts: [{"data": [{"figi": "BBG...", ...}]}]
    Rejects: [{"error": "Invalid idType"}], [], None
    """
    if not isinstance(data, list) or len(data) == 0:
        return False
    first = data[0]
    if isinstance(first, dict):
        return "data" in first and "error" not in first
    return False


@_register_validator("Tradier")
def _validate_tradier(data: Any) -> bool:
    """Tradier /user/profile returns {"profile": {"account": {...}}}.

    Accepts: {"profile": {}} — key presence confirms valid auth.
    Rejects: {"fault": {"faultstring": "..."}}, None
    """
    if isinstance(data, dict):
        return "profile" in data and "fault" not in data
    return False


@_register_validator("Alpaca")
def _validate_alpaca(data: Any) -> bool:
    """Alpaca /v2/account returns {"id": "...", "status": "..."}.

    Accepts: {"id": "..."} — key presence confirms valid auth.
    Rejects: {"code": 40110000, "message": "..."}, None
    """
    if isinstance(data, dict):
        return "id" in data and "code" not in data
    return False


def _validate_generic(data: Any) -> bool:
    """AC-27: Generic check for providers not in the validation table."""
    return data is not None


class ProviderConnectionService:
    """Manage provider credentials and test connectivity.

    Args:
        uow: Unit of Work for persistence.
        encryption: Encryption service for API keys.
        http_client: Async HTTP client.
        rate_limiters: Per-provider rate limiters.
        provider_registry: Static provider configuration registry.
    """

    _ENC_PREFIX = "ENC:"

    def __init__(
        self,
        uow: Any,  # UnitOfWork
        encryption: EncryptionService,
        http_client: HttpClient,
        rate_limiters: Mapping[str, RateLimiterProtocol],
        provider_registry: dict[str, ProviderConfig],
    ) -> None:
        self._uow = uow
        self._encryption = encryption
        self._http = http_client
        self._rate_limiters = rate_limiters
        self._registry = provider_registry
        self._test_semaphore = asyncio.Semaphore(2)

    async def list_providers(self) -> list[ProviderStatus]:
        """List all providers with status information.

        Returns:
            List of ProviderStatus for all 13 registered providers.
        """
        result: list[ProviderStatus] = []
        with self._uow as uow:
            settings = {
                m.provider_name: m for m in uow.market_provider_settings.list_all()
            }

        for name in sorted(self._registry):
            setting = settings.get(name)
            config = self._registry[name]
            result.append(
                ProviderStatus(
                    provider_name=name,
                    display_name=config.name if config.name != name else None,
                    is_enabled=bool(setting.is_enabled) if setting else False,
                    has_api_key=bool(setting and setting.encrypted_api_key),
                    rate_limit=(
                        setting.rate_limit
                        if setting and setting.rate_limit
                        else config.default_rate_limit
                    ),
                    timeout=setting.timeout if setting and setting.timeout else 30,
                    last_test_status=(setting.last_test_status if setting else None),
                    signup_url=config.signup_url or None,
                )
            )
        return result

    async def configure_provider(
        self,
        name: str,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        rate_limit: int | None = None,
        timeout: int | None = None,
        is_enabled: bool | None = None,
    ) -> None:
        """Configure a provider with PATCH semantics.

        Only provided fields are updated; omitted fields are left unchanged.
        """
        if name not in self._registry:
            raise KeyError(f"Unknown provider: '{name}'")

        with self._uow as uow:
            model = uow.market_provider_settings.get(name)
            if model is None:
                model = MarketProviderSettings(
                    provider_name=name,
                    rate_limit=self._registry[name].default_rate_limit,
                    timeout=30,
                    is_enabled=False,
                    created_at=datetime.now(),
                )

            if api_key is not None:
                if api_key.startswith(self._ENC_PREFIX):
                    model.encrypted_api_key = api_key
                else:
                    model.encrypted_api_key = self._encryption.encrypt(api_key)

            if api_secret is not None:
                if api_secret.startswith(self._ENC_PREFIX):
                    model.encrypted_api_secret = api_secret
                else:
                    model.encrypted_api_secret = self._encryption.encrypt(api_secret)

            if rate_limit is not None:
                model.rate_limit = rate_limit

            if timeout is not None:
                model.timeout = timeout

            if is_enabled is not None:
                model.is_enabled = is_enabled

            model.updated_at = datetime.now()
            uow.market_provider_settings.save(model)
            uow.commit()

    async def test_connection(self, name: str) -> tuple[bool, str]:
        """Test connectivity to a provider.

        Returns:
            Tuple of (success, message).
        """
        if name not in self._registry:
            raise KeyError(f"Unknown provider: '{name}'")

        config = self._registry[name]

        # Always fetch stored settings (for timeout, test-status update, etc.)
        with self._uow as uow:
            setting = uow.market_provider_settings.get(name)

        # Free providers (AuthMethod.NONE) can be tested without an API key
        if config.auth_method == AuthMethod.NONE:
            api_key = ""
            api_secret = ""
        else:
            if not setting or not setting.encrypted_api_key:
                return False, "No API key configured"

            api_key = self._encryption.decrypt(setting.encrypted_api_key)
            api_secret = ""
            if setting.encrypted_api_secret:
                api_secret = self._encryption.decrypt(setting.encrypted_api_secret)

        # Build request
        url = config.base_url + config.test_endpoint.format(
            api_key=api_key, api_secret=api_secret
        )
        headers = {
            k: v.format(api_key=api_key, api_secret=api_secret)
            for k, v in config.headers_template.items()
        }
        timeout = setting.timeout if (setting and setting.timeout) else 30

        # Rate limit
        limiter = self._rate_limiters.get(name)
        if limiter:
            await limiter.wait_if_needed()

        # Yahoo Finance requires a 2-step cookie+crumb session.
        # Standard single-GET endpoints return 401/429 without session context.
        if name == "Yahoo Finance":
            return await self._test_yahoo_finance_crumb(timeout, headers)

        # TradingView scanner API requires a POST request (not GET).
        # Used by all major Python TradingView libraries (tradingview-screener etc.)
        if name == "TradingView":
            return await self._test_tradingview_scanner(url, headers, timeout)

        # OpenFIGI API requires POST with JSON body to /v3/mapping.
        # GET to /v3/mapping returns 405 Method Not Allowed.
        if name == "OpenFIGI":
            return await self._test_openfigi_post(headers, timeout)

        try:
            response = await self._http.get(url, headers, timeout)
        except TimeoutError:
            success, message = False, "Connection timeout"
        except ConnectionError:
            success, message = False, "Connection failed"
        else:
            success, message = self._interpret_response(name, response, config)

        # Update test status in DB
        with self._uow as uow:
            model = uow.market_provider_settings.get(name)
            if model:
                model.last_tested_at = datetime.now()
                model.last_test_status = "success" if success else "failed"
                model.updated_at = datetime.now()
                uow.market_provider_settings.save(model)
                uow.commit()

        return success, message

    async def _test_yahoo_finance_crumb(
        self, timeout: int, headers: dict[str, str]
    ) -> tuple[bool, str]:
        """Test Yahoo Finance via the official cookie+crumb dance.

        Yahoo Finance requires a session-aware 2-step flow since mid-2023:
          Step 1: GET https://fc.yahoo.com — 404 expected; the httpx AsyncClient
                  stores the returned 'A3' session cookie automatically.
          Step 2: GET /v1/test/getcrumb — the stored cookie is sent automatically
                  by httpx; a non-empty crumb text proves the service is reachable.

        Both calls go through the same HttpClient instance, which holds a single
        AsyncClient internally — this ensures cookie persistence between calls.
        """
        cookie_url = "https://fc.yahoo.com"
        crumb_url = "https://query1.finance.yahoo.com/v1/test/getcrumb"

        success: bool
        message: str
        try:
            # Step 1: Hit fc.yahoo.com to obtain the session cookie (404 is expected)
            await self._http.get(cookie_url, headers, timeout)

            # Step 2: getcrumb uses the cookie stored in the shared AsyncClient session
            crumb_resp = await self._http.get(crumb_url, headers, timeout)

            if crumb_resp.status_code == 200:
                crumb_text = getattr(crumb_resp, "text", "")
                if crumb_text and len(crumb_text.strip()) > 0:
                    success, message = True, "Connection successful"
                else:
                    success, message = False, "Connected but crumb was empty"
            elif crumb_resp.status_code == 401:
                success, message = False, "Yahoo session rejected (cookie invalid)"
            else:
                success, message = (
                    False,
                    f"Unexpected status code: {crumb_resp.status_code}",
                )
        except TimeoutError:
            success, message = False, "Connection timeout"
        except ConnectionError:
            success, message = False, "Connection failed"

        # Update DB status
        with self._uow as uow:
            model = uow.market_provider_settings.get("Yahoo Finance")
            if model:
                model.last_tested_at = datetime.now()
                model.last_test_status = "success" if success else "failed"
                model.updated_at = datetime.now()
                uow.market_provider_settings.save(model)
                uow.commit()

        return success, message

    async def _test_tradingview_scanner(
        self, url: str, headers: dict[str, str], timeout: int
    ) -> tuple[bool, str]:
        """Test TradingView via its scanner API (POST request).

        scanner.tradingview.com/america/scan accepts a minimal JSON payload
        and returns {'totalCount': N, 'data': [...]}. Used by all major
        Python TradingView libraries (tradingview-screener, tvscreener, etc.).
        """
        # Minimal payload — just enough to trigger a valid response
        payload = {"columns": ["name"], "range": [0, 1]}

        success: bool
        message: str
        try:
            response = await self._http.post(url, headers, timeout, json=payload)
            success, message = self._interpret_response("TradingView", response, None)  # type: ignore[arg-type]
        except TimeoutError:
            success, message = False, "Connection timeout"
        except ConnectionError:
            success, message = False, "Connection failed"

        # Update DB status
        with self._uow as uow:
            model = uow.market_provider_settings.get("TradingView")
            if model:
                model.last_tested_at = datetime.now()
                model.last_test_status = "success" if success else "failed"
                model.updated_at = datetime.now()
                uow.market_provider_settings.save(model)
                uow.commit()

        return success, message

    async def _test_openfigi_post(
        self, headers: dict[str, str], timeout: int
    ) -> tuple[bool, str]:
        """Test OpenFIGI via its POST-only /v3/mapping endpoint.

        OpenFIGI requires POST with a JSON body: [{"idType": "TICKER", "idValue": "IBM"}].
        GET to /v3/mapping returns 405 Method Not Allowed.

        Uses the same pattern as _test_tradingview_scanner: POST → validate → update DB.
        """
        url = "https://api.openfigi.com/v3/mapping"
        payload = [{"idType": "TICKER", "idValue": "IBM"}]

        success: bool
        message: str
        try:
            response = await self._http.post(url, headers, timeout, json=payload)
            success, message = self._interpret_response("OpenFIGI", response, None)  # type: ignore[arg-type]
        except TimeoutError:
            success, message = False, "Connection timeout"
        except ConnectionError:
            success, message = False, "Connection failed"

        # Update DB status
        with self._uow as uow:
            model = uow.market_provider_settings.get("OpenFIGI")
            if model:
                model.last_tested_at = datetime.now()
                model.last_test_status = "success" if success else "failed"
                model.updated_at = datetime.now()
                uow.market_provider_settings.save(model)
                uow.commit()

        return success, message

    def _interpret_response(
        self, name: str, response: Any, config: ProviderConfig
    ) -> tuple[bool, str]:
        """Interpret HTTP response per §8.6 rules."""
        status_code = response.status_code

        if status_code == 401:
            return False, "Invalid API key"

        if status_code == 403:
            # FMP-specific: "Legacy Endpoint" treated as success
            if name == "Financial Modeling Prep":
                body_text = getattr(response, "text", "")
                if "Legacy Endpoint" in body_text:
                    return True, "API key valid (endpoint deprecated)"
            return False, "Access forbidden"

        if status_code == 429:
            return False, "Rate limit exceeded"

        if status_code == 200:
            # TradingView's pingpong endpoint returns empty body — treat as success
            # for any provider that has a registered validator (they handle None).
            validator = _PROVIDER_VALIDATORS.get(name)
            try:
                data = response.json()
            except Exception:
                data = None

            if data is None:
                # Empty body: success only if there's a provider-specific validator
                if validator and validator(data):
                    return True, "Connection successful"
                return False, "Connected but unexpected response"

            # Use provider-specific validator or generic fallback
            if validator is None:
                validator = _validate_generic
            if validator(data):
                return True, "Connection successful"
            else:
                return False, "Connected but unexpected response"

        return False, f"Unexpected status code: {status_code}"

    async def remove_api_key(self, name: str) -> None:
        """Remove API key and disable provider."""
        if name not in self._registry:
            raise KeyError(f"Unknown provider: '{name}'")

        with self._uow as uow:
            model = uow.market_provider_settings.get(name)
            if model:
                model.encrypted_api_key = None
                model.encrypted_api_secret = None
                model.is_enabled = False
                model.updated_at = datetime.now()
                uow.market_provider_settings.save(model)
                uow.commit()

    async def test_all_providers(self) -> list[tuple[str, bool, str]]:
        """Test all providers that have API keys configured.

        Uses asyncio.Semaphore(2) to limit concurrent tests.
        """
        providers = await self.list_providers()
        enabled = [p for p in providers if p.has_api_key]

        async def _guarded_test(provider: ProviderStatus) -> tuple[str, bool, str]:
            async with self._test_semaphore:
                success, message = await self.test_connection(provider.provider_name)
                return (provider.provider_name, success, message)

        return list(await asyncio.gather(*[_guarded_test(p) for p in enabled]))
