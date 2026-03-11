"""API key encryption tests — MEU-58 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
Source: docs/build-plan/08-market-data.md §8.2b.
"""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet, InvalidToken

pytestmark = pytest.mark.unit


# ── AC-2/AC-3: Encrypt/decrypt round-trip ────────────────────────────────


class TestEncryptDecryptRoundTrip:
    """AC-2/3: encrypt_api_key and decrypt_api_key are inverse operations."""

    def test_encrypt_decrypt_round_trip(self) -> None:
        from zorivest_infra.security.api_key_encryption import (
            decrypt_api_key,
            encrypt_api_key,
        )

        fernet = Fernet(Fernet.generate_key())
        original = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(original, fernet)
        decrypted = decrypt_api_key(encrypted, fernet)
        assert decrypted == original

    def test_encrypted_key_has_enc_prefix(self) -> None:
        """AC-2: encrypt returns 'ENC:' prefixed ciphertext."""
        from zorivest_infra.security.api_key_encryption import encrypt_api_key

        fernet = Fernet(Fernet.generate_key())
        encrypted = encrypt_api_key("my-api-key", fernet)
        assert encrypted.startswith("ENC:")

    def test_decrypt_strips_enc_prefix(self) -> None:
        """AC-3: decrypt strips 'ENC:' prefix."""
        from zorivest_infra.security.api_key_encryption import (
            decrypt_api_key,
            encrypt_api_key,
        )

        fernet = Fernet(Fernet.generate_key())
        encrypted = encrypt_api_key("my-api-key", fernet)
        assert encrypted.startswith("ENC:")
        decrypted = decrypt_api_key(encrypted, fernet)
        assert not decrypted.startswith("ENC:")
        assert decrypted == "my-api-key"


# ── AC-4: Idempotent encrypt ─────────────────────────────────────────────


class TestIdempotentEncrypt:
    """AC-4: Already-encrypted keys are not double-encrypted."""

    def test_already_encrypted_not_double_encrypted(self) -> None:
        from zorivest_infra.security.api_key_encryption import encrypt_api_key

        fernet = Fernet(Fernet.generate_key())
        first = encrypt_api_key("my-key", fernet)
        second = encrypt_api_key(first, fernet)
        assert first == second  # Same ciphertext, not re-encrypted


# ── AC-5: Empty/None pass-through ────────────────────────────────────────


class TestPassThrough:
    """AC-5: Empty/None input passes through both encrypt and decrypt."""

    def test_encrypt_empty_string_passes_through(self) -> None:
        from zorivest_infra.security.api_key_encryption import encrypt_api_key

        fernet = Fernet(Fernet.generate_key())
        assert encrypt_api_key("", fernet) == ""

    def test_decrypt_empty_string_passes_through(self) -> None:
        from zorivest_infra.security.api_key_encryption import decrypt_api_key

        fernet = Fernet(Fernet.generate_key())
        assert decrypt_api_key("", fernet) == ""

    def test_decrypt_non_encrypted_passes_through(self) -> None:
        """Non-encrypted key passes through decrypt_api_key unchanged."""
        from zorivest_infra.security.api_key_encryption import decrypt_api_key

        fernet = Fernet(Fernet.generate_key())
        assert decrypt_api_key("plain-key-no-enc", fernet) == "plain-key-no-enc"


# ── AC-6: derive_fernet_key ──────────────────────────────────────────────


class TestDeriveFernetKey:
    """AC-6 [Research-backed]: derive_fernet_key produces valid Fernet."""

    def test_derive_fernet_key_produces_valid_fernet(self) -> None:
        from zorivest_infra.security.api_key_encryption import derive_fernet_key

        salt = os.urandom(16)
        fernet = derive_fernet_key("my-master-password", salt)
        assert isinstance(fernet, Fernet)

    def test_derive_fernet_key_is_deterministic(self) -> None:
        from zorivest_infra.security.api_key_encryption import (
            decrypt_api_key,
            derive_fernet_key,
            encrypt_api_key,
        )

        salt = os.urandom(16)
        fernet1 = derive_fernet_key("password", salt)
        fernet2 = derive_fernet_key("password", salt)
        # Both should produce same key — encrypt with one, decrypt with other
        encrypted = encrypt_api_key("test-key", fernet1)
        decrypted = decrypt_api_key(encrypted, fernet2)
        assert decrypted == "test-key"


# ── AC-7: Wrong key raises InvalidToken ──────────────────────────────────


class TestWrongKeyRaises:
    """AC-7: Decryption with wrong Fernet key raises InvalidToken."""

    def test_wrong_key_raises_invalid_token(self) -> None:
        from zorivest_infra.security.api_key_encryption import (
            decrypt_api_key,
            encrypt_api_key,
        )

        key1 = Fernet(Fernet.generate_key())
        key2 = Fernet(Fernet.generate_key())
        encrypted = encrypt_api_key("secret-key", key1)
        with pytest.raises(InvalidToken):
            decrypt_api_key(encrypted, key2)
