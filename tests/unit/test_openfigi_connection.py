# tests/unit/test_openfigi_connection.py
"""TDD Red-phase tests for OpenFIGI POST connection test (MEU-189).

Acceptance criteria AC-9 and AC-10 per implementation-plan.md.

AC-9: ProviderConnectionService._test_openfigi_post() dispatches POST to /v3/mapping
AC-10: OpenFIGI response validator rejects error payloads, accepts valid FIGI arrays
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# AC-9: OpenFIGI POST connection test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC9_openfigi_test_dispatches_post():
    """test_connection("OpenFIGI") uses POST to /v3/mapping, not GET."""
    from zorivest_core.services.provider_connection_service import (
        ProviderConnectionService,
    )
    from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY

    # Setup UoW mock with stored settings
    mock_uow = MagicMock()
    mock_settings = MagicMock()
    mock_settings.encrypted_api_key = "ENC:test-key"
    mock_settings.encrypted_api_secret = None
    mock_settings.timeout = 10
    mock_settings.is_enabled = True
    mock_settings.rate_limit = 10
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)
    mock_uow.market_provider_settings.get.return_value = mock_settings
    mock_uow.commit = MagicMock()
    mock_uow.market_provider_settings.save = MagicMock()

    # Setup encryption mock
    mock_enc = MagicMock()
    mock_enc.decrypt.return_value = "my-openfigi-key"

    # Setup HTTP client mock — POST should be called, not GET
    mock_http = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = [
        {"data": [{"figi": "BBG000BLNNH6", "name": "IBM"}]}
    ]
    mock_http.post.return_value = mock_post_response

    service = ProviderConnectionService(
        uow=mock_uow,
        encryption=mock_enc,
        http_client=mock_http,
        rate_limiters={},
        provider_registry=dict(PROVIDER_REGISTRY),
    )

    success, message = await service.test_connection("OpenFIGI")

    # POST must have been called, not GET
    mock_http.post.assert_called_once()
    # The URL should contain /v3/mapping
    post_call_args = mock_http.post.call_args
    url_called = post_call_args.args[0] if post_call_args.args else ""
    assert "/v3/mapping" in url_called, (
        f"Expected /v3/mapping in URL, got: {url_called}"
    )

    assert success is True
    assert "successful" in message.lower()


@pytest.mark.asyncio
async def test_AC9_openfigi_post_sends_json_body():
    """OpenFIGI POST test sends a minimal FIGI mapping body."""
    from zorivest_core.services.provider_connection_service import (
        ProviderConnectionService,
    )
    from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY

    mock_uow = MagicMock()
    mock_settings = MagicMock()
    mock_settings.encrypted_api_key = "ENC:test-key"
    mock_settings.encrypted_api_secret = None
    mock_settings.timeout = 10
    mock_settings.is_enabled = True
    mock_settings.rate_limit = 10
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)
    mock_uow.market_provider_settings.get.return_value = mock_settings
    mock_uow.commit = MagicMock()
    mock_uow.market_provider_settings.save = MagicMock()

    mock_enc = MagicMock()
    mock_enc.decrypt.return_value = "my-openfigi-key"

    mock_http = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = [{"data": [{"figi": "BBG000BLNNH6"}]}]
    mock_http.post.return_value = mock_post_response

    service = ProviderConnectionService(
        uow=mock_uow,
        encryption=mock_enc,
        http_client=mock_http,
        rate_limiters={},
        provider_registry=dict(PROVIDER_REGISTRY),
    )

    await service.test_connection("OpenFIGI")

    # Verify JSON body was sent
    post_call = mock_http.post.call_args
    json_body = post_call.kwargs.get("json") if post_call.kwargs else None
    assert json_body is not None, "POST body must be sent"
    # Minimal body: [{"idType": "TICKER", "idValue": "IBM"}]
    assert isinstance(json_body, list)
    assert len(json_body) >= 1


@pytest.mark.asyncio
async def test_AC9_openfigi_post_updates_db_status():
    """test_connection("OpenFIGI") updates last_tested_at and last_test_status in DB."""
    from zorivest_core.services.provider_connection_service import (
        ProviderConnectionService,
    )
    from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY

    mock_uow = MagicMock()
    mock_settings = MagicMock()
    mock_settings.encrypted_api_key = "ENC:test-key"
    mock_settings.encrypted_api_secret = None
    mock_settings.timeout = 10
    mock_settings.is_enabled = True
    mock_settings.rate_limit = 10
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)
    mock_uow.market_provider_settings.get.return_value = mock_settings
    mock_uow.commit = MagicMock()
    mock_uow.market_provider_settings.save = MagicMock()

    mock_enc = MagicMock()
    mock_enc.decrypt.return_value = "my-openfigi-key"

    mock_http = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = [{"data": [{"figi": "BBG000BLNNH6"}]}]
    mock_http.post.return_value = mock_post_response

    service = ProviderConnectionService(
        uow=mock_uow,
        encryption=mock_enc,
        http_client=mock_http,
        rate_limiters={},
        provider_registry=dict(PROVIDER_REGISTRY),
    )

    success, _ = await service.test_connection("OpenFIGI")
    assert success is True

    # DB should have been updated
    mock_uow.market_provider_settings.save.assert_called()
    saved_model = mock_uow.market_provider_settings.save.call_args.args[0]
    assert saved_model.last_test_status == "success"


# ---------------------------------------------------------------------------
# AC-10: OpenFIGI response validator
# ---------------------------------------------------------------------------


def test_AC10_openfigi_validator_accepts_valid_figi_response():
    """OpenFIGI validator returns True when response has [{"data": [{"figi": "..."}]}]."""
    from zorivest_core.services.provider_connection_service import (
        _PROVIDER_VALIDATORS,
    )

    validator = _PROVIDER_VALIDATORS.get("OpenFIGI")
    assert validator is not None, "OpenFIGI validator must be registered"

    # Standard successful response
    data = [{"data": [{"figi": "BBG000BLNNH6", "name": "IBM"}]}]
    assert validator(data) is True


def test_AC10_openfigi_validator_rejects_error_payload():
    """OpenFIGI validator returns False when response contains an error key."""
    from zorivest_core.services.provider_connection_service import (
        _PROVIDER_VALIDATORS,
    )

    validator = _PROVIDER_VALIDATORS.get("OpenFIGI")
    assert validator is not None

    # Error response from OpenFIGI API
    data = [{"error": "Invalid idType"}]
    assert validator(data) is False


def test_AC10_openfigi_validator_rejects_empty_list():
    """OpenFIGI validator returns False for empty list (no mapping results)."""
    from zorivest_core.services.provider_connection_service import (
        _PROVIDER_VALIDATORS,
    )

    validator = _PROVIDER_VALIDATORS.get("OpenFIGI")
    assert validator is not None

    assert validator([]) is False


def test_AC10_openfigi_validator_rejects_none():
    """OpenFIGI validator returns False for None."""
    from zorivest_core.services.provider_connection_service import (
        _PROVIDER_VALIDATORS,
    )

    validator = _PROVIDER_VALIDATORS.get("OpenFIGI")
    assert validator is not None

    assert validator(None) is False
