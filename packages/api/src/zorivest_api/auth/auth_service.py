"""Auth service — envelope encryption, API key management, sessions.

Source: 04c-api-auth.md
Uses: Argon2id (argon2-cffi), Fernet (cryptography), bootstrap.json.
Integration with zorivest_infra.database.connection for PRAGMA key.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field


# ── Custom error types ──────────────────────────────────────────────────

class InvalidKeyError(Exception):
    """Raised when API key is not found or invalid (→ 401)."""


class RevokedKeyError(Exception):
    """Raised when API key has been revoked (→ 403)."""


class AlreadyUnlockedError(Exception):
    """Raised when database is already unlocked (→ 423)."""


class InvalidActionError(Exception):
    """Raised when confirmation action is not in VALID_DESTRUCTIVE_ACTIONS (→ 400)."""


# ── Constants ───────────────────────────────────────────────────────────

VALID_DESTRUCTIVE_ACTIONS = frozenset({
    "delete_account",
    "delete_trade",
    "delete_all_trades",
    "revoke_api_key",
    "factory_reset",
})


# ── Auth Service ────────────────────────────────────────────────────────

@dataclass
class AuthService:
    """Envelope-encryption auth service.

    In production, integrates with bootstrap.json and SQLCipher via
    zorivest_infra.database.connection for PRAGMA key application.

    In tests, the database layer is mocked.
    """

    # In-memory stores
    _sessions: dict[str, dict] = field(default_factory=dict)
    _confirmation_tokens: dict[str, dict] = field(default_factory=dict)
    _keys: dict[str, dict] = field(default_factory=dict)
    _unlocked: bool = False

    def unlock(self, api_key: str) -> dict:
        """Perform envelope-encryption unlock flow.

        1. Hash API key → lookup in key store
        2. Argon2id KDF → derive KEK
        3. Unwrap DEK using KEK (Fernet)
        4. Apply PRAGMA key (mocked in tests)

        Raises:
            InvalidKeyError: Key not found (401)
            RevokedKeyError: Key was revoked (403)
            AlreadyUnlockedError: DB already unlocked (423)
        """
        if self._unlocked:
            raise AlreadyUnlockedError("Database is already unlocked")

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_entry = self._keys.get(key_hash)

        if key_entry is None:
            raise InvalidKeyError("Invalid API key")

        if key_entry.get("revoked", False):
            raise RevokedKeyError("API key has been revoked")

        # In production: Argon2id → KEK → Fernet unwrap DEK → PRAGMA key
        # For now, mark as unlocked and issue session token
        self._unlocked = True
        session_token = f"tok_{secrets.token_hex(16)}"
        self._sessions[session_token] = {
            "created_at": time.time(),
            "role": key_entry.get("role", "admin"),
            "scopes": key_entry.get("scopes", ["read", "write"]),
            "expires_in": 3600,
        }

        return {
            "session_token": session_token,
            "role": key_entry.get("role", "admin"),
            "scopes": key_entry.get("scopes", ["read", "write"]),
            "expires_in": 3600,
        }

    def lock(self) -> None:
        """Lock database and invalidate all sessions."""
        self._unlocked = False
        self._sessions.clear()

    def get_status(self) -> dict:
        """Return current auth status."""
        return {"locked": not self._unlocked}

    def create_key(self, name: str, role: str = "admin") -> dict:
        """Create a new API key.

        Generates key, hashes for lookup, stores entry.
        Returns raw key exactly once.
        """
        raw_key = f"zrv_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        key_id = f"key_{secrets.token_hex(4)}"
        self._keys[key_hash] = {
            "key_id": key_id,
            "name": name,
            "role": role,
            "scopes": ["read", "write"],
            "created_at": time.time(),
            "revoked": False,
            "key_hash": key_hash,
        }

        return {
            "key_id": key_id,
            "name": name,
            "role": role,
            "raw_key": raw_key,
        }

    def list_keys(self) -> list[dict]:
        """List API keys with masked representation (never plaintext)."""
        result = []
        for _hash, entry in self._keys.items():
            if not entry.get("revoked", False):
                result.append({
                    "key_id": entry["key_id"],
                    "name": entry["name"],
                    "role": entry["role"],
                    "masked_key": f"zrv_***{_hash[-3:]}",
                    "created_at": entry["created_at"],
                })
        return result

    def revoke_key(self, key_id: str) -> None:
        """Revoke an API key by key_id."""
        for _hash, entry in self._keys.items():
            if entry["key_id"] == key_id:
                entry["revoked"] = True
                return
        raise InvalidKeyError(f"Key not found: {key_id}")

    def create_confirmation_token(self, action: str) -> dict:
        """Create a time-limited confirmation token for a destructive action.

        Raises:
            InvalidActionError: If action is not in VALID_DESTRUCTIVE_ACTIONS.
        """
        if action not in VALID_DESTRUCTIVE_ACTIONS:
            raise InvalidActionError(f"Unknown destructive action: {action}")

        token = f"ctk_{secrets.token_hex(16)}"
        expires_at = time.time() + 60  # 60s TTL
        self._confirmation_tokens[token] = {
            "action": action,
            "expires_at": expires_at,
        }

        return {
            "token": token,
            "expires_in_seconds": 60,
        }
