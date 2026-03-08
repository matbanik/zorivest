# packages/core/src/zorivest_core/domain/settings_validator.py
"""Three-stage settings validation pipeline: type → format → security.

Source: 02a-backup-restore.md §2A.2b

Runs before any write to SettingModel. Pure domain logic — no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from zorivest_core.domain.settings import SettingSpec
from zorivest_core.domain.settings_resolver import SettingsResolver


@dataclass
class ValidationResult:
    """Outcome of validating a single setting value."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    key: str = ""
    raw_value: Any = None


class SettingsValidationError(Exception):
    """Raised when one or more settings fail validation.

    Contains per-key error details for the REST layer to surface as 422.
    """

    def __init__(self, per_key_errors: dict[str, list[str]]) -> None:
        self.per_key_errors = per_key_errors
        super().__init__(f"Validation failed for {len(per_key_errors)} key(s)")


# Security patterns — compiled once at module level
_PATH_TRAVERSAL = re.compile(r"\.\.[/\\]")
_SQL_INJECTION = re.compile(
    r"('\s*;\s*(DROP|ALTER|DELETE|UPDATE|INSERT))"
    r"|(\bOR\b\s+\d+\s*=\s*\d+)"
    r"|(\bUNION\b\s+\bSELECT\b)",
    re.IGNORECASE,
)
_SCRIPT_INJECTION = re.compile(
    r"<\s*script"
    r"|javascript\s*:"
    r"|on(load|error|click|mouseover)\s*=",
    re.IGNORECASE,
)


class SettingsValidator:
    """Three-stage validation pipeline: type → format → security.

    Runs on every PUT /settings write. Pure domain — no I/O.
    Stages run in order; pipeline stops at the first stage that produces errors.
    """

    def __init__(self, registry: dict[str, SettingSpec]) -> None:
        self._registry = registry

    def validate(self, key: str, raw_value: Any) -> ValidationResult:
        """Run all three stages. Returns on first failing stage."""
        spec = self._resolve_spec(key)
        if spec is None:
            return ValidationResult(
                valid=False,
                errors=[f"Unknown setting: {key}"],
                key=key,
                raw_value=raw_value,
            )

        # Stage 1: Type validation
        type_errors = self._validate_type(raw_value, spec)
        if type_errors:
            return ValidationResult(
                valid=False, errors=type_errors, key=key, raw_value=raw_value
            )

        # Stage 2: Format validation (ranges, enums, custom)
        format_errors = self._validate_format(raw_value, spec)
        if format_errors:
            return ValidationResult(
                valid=False, errors=format_errors, key=key, raw_value=raw_value
            )

        # Stage 3: Security validation
        security_errors = self._validate_security(raw_value, spec)
        return ValidationResult(
            valid=len(security_errors) == 0,
            errors=security_errors,
            key=key,
            raw_value=raw_value,
        )

    def _resolve_spec(self, key: str) -> Optional[SettingSpec]:
        """Look up spec by exact key, then fall back to glob patterns."""
        spec = self._registry.get(key)
        if spec is not None:
            return spec
        # Glob fallback: replace middle segments with * and try matching
        parts = key.split(".")
        for i in range(len(parts)):
            pattern_parts = parts[:i] + ["*"] + parts[i + 1 :]
            pattern_key = ".".join(pattern_parts)
            spec = self._registry.get(pattern_key)
            if spec is not None:
                return spec
        return None

    def validate_bulk(self, settings: dict[str, Any]) -> dict[str, list[str]]:
        """Validate multiple settings. Returns dict of key → errors (empty if all valid)."""
        errors: dict[str, list[str]] = {}
        for key, value in settings.items():
            result = self.validate(key, value)
            if not result.valid:
                errors[key] = result.errors
        return errors

    # ── Stage 1: Type ───────────────────────────────────────────

    @staticmethod
    def _validate_type(raw_value: Any, spec: SettingSpec) -> list[str]:
        """Verify raw_value can be parsed to spec.value_type."""
        try:
            SettingsResolver._parse(str(raw_value), spec.value_type)
            return []
        except (ValueError, TypeError) as e:
            return [f"Cannot parse '{raw_value}' as {spec.value_type}: {e}"]

    # ── Stage 2: Format ─────────────────────────────────────────

    @staticmethod
    def _validate_format(raw_value: Any, spec: SettingSpec) -> list[str]:
        """Check allowed_values, numeric ranges, string length, custom validator."""
        errors: list[str] = []
        str_val = str(raw_value)

        # Enum constraint
        if spec.allowed_values is not None and str_val not in spec.allowed_values:
            errors.append(
                f"'{str_val}' not in allowed values: {spec.allowed_values}"
            )

        # Numeric range
        if spec.value_type in ("int", "float"):
            try:
                num = float(str_val)
                if spec.min_value is not None and num < spec.min_value:
                    errors.append(f"Value {num} below minimum {spec.min_value}")
                if spec.max_value is not None and num > spec.max_value:
                    errors.append(f"Value {num} above maximum {spec.max_value}")
            except ValueError:
                pass  # Already caught by Stage 1

        # String length cap
        if len(str_val) > spec.max_length:
            errors.append(
                f"Value length {len(str_val)} exceeds max {spec.max_length}"
            )

        # Custom per-key validator
        if spec.validator is not None and not spec.validator(raw_value):
            errors.append(f"Custom validation failed for '{spec.key}'")

        return errors

    # ── Stage 3: Security ───────────────────────────────────────

    @staticmethod
    def _validate_security(raw_value: Any, spec: SettingSpec) -> list[str]:
        """Reject path traversal, SQL injection, and script injection."""
        errors: list[str] = []
        str_val = str(raw_value)

        if _PATH_TRAVERSAL.search(str_val):
            errors.append("Value contains path traversal pattern")
        if _SQL_INJECTION.search(str_val):
            errors.append("Value contains SQL injection pattern")
        if _SCRIPT_INJECTION.search(str_val):
            errors.append("Value contains script injection pattern")

        return errors
