"""
Envelope Encryption Key Vault — Proof of Concept

Implements the dual-access pattern for SQLCipher:
- A random DEK (Data Encryption Key) encrypts the database
- Multiple KEKs (Key Encryption Keys) can independently unwrap the DEK
- KEK₁ derived from user passphrase (GUI access)
- KEK₂ derived from API key (MCP headless access)

Uses: cryptography.fernet (symmetric), argon2id (KDF), os.urandom (CSPRNG)
"""

import base64
import hashlib
import json
import os
import secrets
import string
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from argon2.low_level import hash_secret_raw, Type
from cryptography.fernet import Fernet, InvalidToken


# --- Configuration ---

KDF_TIME_COST = 2         # Argon2id iterations
KDF_MEMORY_COST = 19456   # 19 MiB — OWASP minimum
KDF_PARALLELISM = 1
KDF_HASH_LEN = 32         # 256-bit key
SALT_LEN = 16             # 128-bit salt
DEK_LEN = 32              # 256-bit DEK for SQLCipher
API_KEY_PREFIX = "zrv_sk_"
API_KEY_RANDOM_LEN = 40   # Random part of API key


@dataclass
class WrappedKeyEntry:
    """A single wrapped DEK entry in the key vault."""
    key_id: str
    key_type: str           # "passphrase" or "api_key"
    kdf_salt: str           # hex-encoded salt
    wrapped_dek: str        # Fernet token (base64)
    role: str = "read-write"
    scopes: list[str] = field(default_factory=lambda: ["mcp:read", "mcp:tools"])
    key_hash: str = ""      # SHA-256 of API key (for lookup, not security)
    created_at: str = ""


@dataclass
class BootstrapConfig:
    """The bootstrap.json structure with key vault support."""
    db_path: str = "zorivest_poc.db"
    kdf: dict = field(default_factory=lambda: {
        "algorithm": "argon2id",
        "time_cost": KDF_TIME_COST,
        "memory_cost": KDF_MEMORY_COST,
        "parallelism": KDF_PARALLELISM,
        "hash_len": KDF_HASH_LEN,
    })
    wrapped_keys: list[dict] = field(default_factory=list)


class KeyVault:
    """Envelope encryption: DEK wrapped by multiple KEKs.

    The DEK (Data Encryption Key) is a random 32-byte key used as the
    SQLCipher PRAGMA key. It is never stored in plaintext.

    Each credential (passphrase or API key) derives a KEK via Argon2id,
    which wraps (Fernet-encrypts) the DEK. The wrapped copy is stored
    in bootstrap.json. Any valid credential can unwrap the DEK.
    """

    def __init__(self, bootstrap_path: Path):
        self.bootstrap_path = bootstrap_path
        self.config = self._load_or_create()

    def _load_or_create(self) -> BootstrapConfig:
        """Load existing bootstrap.json or create a new one."""
        if self.bootstrap_path.exists():
            data = json.loads(self.bootstrap_path.read_text())
            return BootstrapConfig(
                db_path=data.get("db_path", "zorivest_poc.db"),
                kdf=data.get("kdf", BootstrapConfig().kdf),
                wrapped_keys=data.get("wrapped_keys", []),
            )
        config = BootstrapConfig()
        self._save(config)
        return config

    def _save(self, config: Optional[BootstrapConfig] = None) -> None:
        """Persist bootstrap config to disk."""
        config = config or self.config
        self.bootstrap_path.write_text(
            json.dumps(asdict(config), indent=2)
        )

    # --- Core cryptographic operations ---

    @staticmethod
    def _derive_kek(credential: str, salt: bytes) -> bytes:
        """Derive a KEK from a credential (passphrase or API key) via Argon2id."""
        raw = hash_secret_raw(
            secret=credential.encode("utf-8"),
            salt=salt,
            time_cost=KDF_TIME_COST,
            memory_cost=KDF_MEMORY_COST,
            parallelism=KDF_PARALLELISM,
            hash_len=KDF_HASH_LEN,
            type=Type.ID,
        )
        # Fernet requires a 32-byte key, URL-safe base64 encoded
        return base64.urlsafe_b64encode(raw)

    @staticmethod
    def generate_dek() -> bytes:
        """Generate a random DEK (Data Encryption Key)."""
        return os.urandom(DEK_LEN)

    @staticmethod
    def wrap_dek(dek: bytes, kek: bytes) -> str:
        """Encrypt DEK with KEK using Fernet. Returns Fernet token string."""
        f = Fernet(kek)
        return f.encrypt(dek).decode("utf-8")

    @staticmethod
    def unwrap_dek(wrapped: str, kek: bytes) -> bytes:
        """Decrypt DEK from Fernet token using KEK. Raises on bad credential."""
        f = Fernet(kek)
        return f.decrypt(wrapped.encode("utf-8"))

    # --- High-level operations ---

    def initialize_with_passphrase(self, passphrase: str) -> bytes:
        """First-run: generate DEK, wrap with passphrase, save to bootstrap.

        Returns the DEK for immediate use.
        """
        dek = self.generate_dek()
        salt = os.urandom(SALT_LEN)
        kek = self._derive_kek(passphrase, salt)
        wrapped = self.wrap_dek(dek, kek)

        entry = WrappedKeyEntry(
            key_id="gui-passphrase",
            key_type="passphrase",
            kdf_salt=salt.hex(),
            wrapped_dek=wrapped,
            role="admin",
            scopes=["mcp:read", "mcp:tools", "mcp:admin"],
            created_at="2026-02-16T23:00:00Z",
        )
        self.config.wrapped_keys.append(asdict(entry))
        self._save()
        return dek

    def generate_api_key(self, dek: bytes, role: str = "read-write",
                         scopes: Optional[list[str]] = None) -> str:
        """Generate a new API key and wrap the DEK with it.

        Returns the raw API key (shown once to user).
        The DEK must already be available (from a prior passphrase unlock).
        """
        # Generate random API key
        random_part = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(API_KEY_RANDOM_LEN)
        )
        api_key = f"{API_KEY_PREFIX}{random_part}"

        # Wrap DEK with this API key
        salt = os.urandom(SALT_LEN)
        kek = self._derive_kek(api_key, salt)
        wrapped = self.wrap_dek(dek, kek)

        # Hash for lookup (not for security — just to identify which entry)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        entry = WrappedKeyEntry(
            key_id=f"api-key-{key_hash[:8]}",
            key_type="api_key",
            kdf_salt=salt.hex(),
            wrapped_dek=wrapped,
            role=role,
            scopes=scopes or ["mcp:read", "mcp:tools"],
            key_hash=key_hash,
            created_at="2026-02-16T23:00:00Z",
        )
        self.config.wrapped_keys.append(asdict(entry))
        self._save()
        return api_key

    def unlock_with_passphrase(self, passphrase: str) -> bytes:
        """Unwrap DEK using the user's passphrase. Returns DEK bytes."""
        for entry in self.config.wrapped_keys:
            if entry["key_type"] == "passphrase":
                salt = bytes.fromhex(entry["kdf_salt"])
                kek = self._derive_kek(passphrase, salt)
                try:
                    return self.unwrap_dek(entry["wrapped_dek"], kek)
                except InvalidToken:
                    raise ValueError("Invalid passphrase")
        raise ValueError("No passphrase entry found in key vault")

    def unlock_with_api_key(self, api_key: str) -> bytes:
        """Unwrap DEK using an API key. Returns DEK bytes."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        for entry in self.config.wrapped_keys:
            if entry["key_type"] == "api_key" and entry["key_hash"] == key_hash:
                salt = bytes.fromhex(entry["kdf_salt"])
                kek = self._derive_kek(api_key, salt)
                try:
                    return self.unwrap_dek(entry["wrapped_dek"], kek)
                except InvalidToken:
                    raise ValueError("Invalid API key")
        raise ValueError(f"No matching API key entry found in key vault")

    def revoke_api_key(self, key_id: str) -> bool:
        """Remove a wrapped key entry by key_id."""
        before = len(self.config.wrapped_keys)
        self.config.wrapped_keys = [
            e for e in self.config.wrapped_keys if e["key_id"] != key_id
        ]
        removed = len(self.config.wrapped_keys) < before
        if removed:
            self._save()
        return removed
