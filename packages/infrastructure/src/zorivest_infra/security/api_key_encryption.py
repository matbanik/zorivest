"""API key encryption module — MEU-58.

Fernet-based encrypt/decrypt for market data provider API keys.
Source: docs/build-plan/08-market-data.md §8.2b.
"""

from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ENC_PREFIX = "ENC:"


def encrypt_api_key(api_key: str, fernet: Fernet) -> str:
    """Encrypt an API key. Returns 'ENC:' prefixed ciphertext.

    Already-encrypted keys (ENC: prefix) pass through unchanged.
    Empty strings pass through unchanged.
    """
    if not api_key or api_key.startswith(ENC_PREFIX):
        return api_key
    encrypted = fernet.encrypt(api_key.encode())
    return ENC_PREFIX + base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str, fernet: Fernet) -> str:
    """Decrypt an 'ENC:' prefixed key. Non-encrypted keys pass through.

    Empty strings pass through unchanged.
    """
    if not encrypted_key or not encrypted_key.startswith(ENC_PREFIX):
        return encrypted_key
    encrypted_data = encrypted_key[len(ENC_PREFIX) :]
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    return fernet.decrypt(encrypted_bytes).decode()


def derive_fernet_key(password: str, salt: bytes) -> Fernet:
    """Derive a Fernet key from a password and salt using PBKDF2.

    Uses PBKDF2HMAC with SHA256 and 480,000 iterations per OWASP
    PBKDF2 recommendation. [Research-backed] — not specified in
    08-market-data.md §8.2b.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)
