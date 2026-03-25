"""Service factory helpers for market data wiring — MEU-65.

Adapters for ProviderConnectionService dependencies:
- FernetEncryptionAdapter: wraps api_key_encryption functions as EncryptionService Protocol
- HttpxClient: wraps httpx.AsyncClient as HttpClient Protocol

Source: docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md
        §Remaining Work → Step 1
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from cryptography.fernet import Fernet

from zorivest_infra.security.api_key_encryption import (
    decrypt_api_key,
    derive_fernet_key,
    encrypt_api_key,
)

# Salt is stable per deployment — derive from env or use a fixed default.
# For production, set ZORIVEST_ENC_SALT env var to a hex-encoded 32-byte value.
_DEFAULT_SALT = b"zorivest-market-data-salt-v1-201"  # 32 bytes


def _get_fernet() -> Fernet:
    """Derive a Fernet key from ZORIVEST_ENC_PASSWORD (or a safe default)."""
    password = os.environ.get("ZORIVEST_ENC_PASSWORD", "zorivest-default-dev-password")
    salt_hex = os.environ.get("ZORIVEST_ENC_SALT", "")
    salt = bytes.fromhex(salt_hex) if salt_hex else _DEFAULT_SALT
    return derive_fernet_key(password, salt)


class FernetEncryptionAdapter:
    """Adapt function-based encryption to EncryptionService Protocol.

    Satisfies ProviderConnectionService.EncryptionService:
        def encrypt(self, plaintext: str) -> str: ...
        def decrypt(self, ciphertext: str) -> str: ...
    """

    def __init__(self, fernet: Fernet | None = None) -> None:
        self._fernet = fernet or _get_fernet()

    def encrypt(self, plaintext: str) -> str:
        return encrypt_api_key(plaintext, self._fernet)

    def decrypt(self, ciphertext: str) -> str:
        return decrypt_api_key(ciphertext, self._fernet)


class HttpxClient:
    """Adapt httpx.AsyncClient to HttpClient Protocol.

    Satisfies ProviderConnectionService.HttpClient:
        async def get(self, url: str, headers: dict[str, str], timeout: int) -> Any: ...
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        # follow_redirects=True: TradingView pingpong redirects 301 to final URL.
        # Without this, httpx returns 301 and the interpreter reports failure.
        self._client = client or httpx.AsyncClient(follow_redirects=True)

    async def get(self, url: str, headers: dict[str, str], timeout: int) -> Any:
        return await self._client.get(url, headers=headers, timeout=timeout)

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
        json: Any = None,
    ) -> Any:
        """POST with optional JSON body — used for TradingView scanner API."""
        return await self._client.post(url, headers=headers, timeout=timeout, json=json)

    async def get_with_cookies(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
        cookies: dict[str, str],
    ) -> Any:
        """GET with explicit cookies — used for session-aware providers (Yahoo Finance)."""
        return await self._client.get(
            url, headers=headers, timeout=timeout, cookies=cookies
        )

    async def aclose(self) -> None:
        await self._client.aclose()
