"""Dual-layer redaction filter for sensitive data in log records.

Layer 1: Regex patterns scan all string content for known secret formats.
Layer 2: Key denylist scans dict args/extra for sensitive field names.
"""

from __future__ import annotations

import logging
import re
from typing import Any


class RedactionFilter(logging.Filter):
    """Dual-layer redaction: regex patterns + sensitive key denylist.

    Layer 1: Regex patterns scan all string content for known secret formats.
    Layer 2: Key denylist scans dict args/extra for sensitive field names.
    """

    # --- Layer 1: Regex patterns (order matters — specific before general) ---
    PATTERNS: list[tuple[re.Pattern[str], str]] = [
        # 1. URL query params (covers Alpha Vantage, FMP, EODHD, Benzinga, etc.)
        (re.compile(
            r'(apikey|api_key|api_token|token|password|secret)=([^&\s]+)', re.I),
         r'\1=[REDACTED]'),
        # 2. Bearer tokens (Polygon.io, OAuth)
        (re.compile(r'Bearer\s+\S+', re.I),
         'Bearer [REDACTED]'),
        # 3. Fernet-encrypted values (ENC: prefix)
        (re.compile(r'ENC:[A-Za-z0-9+/=]+'),
         '[ENCRYPTED_VALUE]'),
        # 4. JWT tokens (three base64url segments)
        (re.compile(r'eyJ[\w-]+\.eyJ[\w-]+\.[\w-]+'),
         '[JWT_REDACTED]'),
        # 5. AWS access key IDs
        (re.compile(r'AKIA[0-9A-Z]{16}'),
         '[AWS_KEY_REDACTED]'),
        # 6. AWS secret keys
        (re.compile(
            r'(aws_secret_access_key|secret_key)[\s:=]+[A-Za-z0-9/+=]{40}', re.I),
         r'\1=[REDACTED]'),
        # 7. Connection strings (user:pass in URIs)
        (re.compile(r'://[^:]+:[^@]+@'),
         '://[REDACTED]:[REDACTED]@'),
        # 8. Credit card numbers (PAN, with optional separators)
        (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
         '[CC_REDACTED]'),
        # 9. US Social Security Numbers
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
         '[SSN_REDACTED]'),
        # 10. Custom auth headers (X-Api-Key, X-Finnhub-Token, etc.)
        (re.compile(
            r'(X-[\w-]*(?:Key|Token|Auth)[\w-]*)\s*[:=]\s*\S+', re.I),
         r'\1: [REDACTED]'),
        # 11. Raw Authorization header (non-Bearer, e.g. SEC API)
        (re.compile(r'Authorization\s*[:=]\s*(?!Bearer\b)\S+', re.I),
         'Authorization: [REDACTED]'),
        # 12. Passphrase/password params in logs
        (re.compile(r'(passphrase|passwd|db_password)\s*[=:]\s*\S+', re.I),
         r'\1=[REDACTED]'),
        # 13. Zorivest API keys (zrv_sk_ prefix)
        (re.compile(r'zrv_sk_[A-Za-z0-9_-]{32,}'),
         '[ZRV_KEY_REDACTED]'),
    ]

    # --- Layer 2: Sensitive key denylist (for dict/extra data) ---
    SENSITIVE_KEYS: frozenset[str] = frozenset({
        'password', 'passwd', 'passphrase', 'secret', 'token',
        'apikey', 'api_key', 'api_token', 'authorization',
        'cookie', 'set-cookie', 'x-api-key', 'x-finnhub-token',
        'encrypted_api_key', 'credential', 'private_key',
        'dek', 'wrapped_dek', 'kek', 'master_key',
    })

    # Reserved LogRecord attrs — never scan these as "extras"
    _RESERVED: frozenset[str] = frozenset({
        'name', 'msg', 'args', 'created', 'relativeCreated', 'exc_info',
        'exc_text', 'stack_info', 'lineno', 'funcName', 'pathname',
        'filename', 'module', 'thread', 'threadName', 'process',
        'processName', 'levelname', 'levelno', 'msecs', 'taskName',
    })

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if record.args:
            record.args = self._redact_args(record.args)
        # Layer 2: Redact non-reserved extras (emitted verbatim by formatter)
        for attr_key in list(record.__dict__):
            if attr_key not in self._RESERVED and not attr_key.startswith('_'):
                val = record.__dict__[attr_key]
                if isinstance(val, str):
                    record.__dict__[attr_key] = self._redact(val)
                elif isinstance(val, dict):
                    record.__dict__[attr_key] = self._redact_dict(val)
        return True

    def _redact(self, text: str) -> str:
        """Apply all regex patterns to a string."""
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _redact_args(self, args: Any) -> Any:
        """Redact log record args (tuple, dict, or single value)."""
        if isinstance(args, dict):
            return self._redact_dict(args)
        if isinstance(args, tuple):
            return tuple(
                self._redact_dict(a) if isinstance(a, dict)
                else self._redact(str(a)) if isinstance(a, str)
                else a
                for a in args
            )
        return args

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact dict values whose keys match the denylist."""
        return {
            k: '[REDACTED]' if k.lower() in self.SENSITIVE_KEYS
            else self._redact(str(v)) if isinstance(v, str)
            else self._redact_dict(v) if isinstance(v, dict)
            else v
            for k, v in data.items()
        }
