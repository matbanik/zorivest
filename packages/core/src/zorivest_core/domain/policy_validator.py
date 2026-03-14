# packages/core/src/zorivest_core/domain/policy_validator.py
"""Policy validation module for the pipeline engine (Phase 9).

Implements:
- validate_policy(): structural + referential validation (8 rules)
- compute_content_hash(): SHA-256 for change detection
- SQL_BLOCKLIST: defense-in-depth keyword filter

Spec reference: 09-scheduling.md §9.1g
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from zorivest_core.domain.pipeline import PolicyDocument
from zorivest_core.domain.step_registry import has_step


@dataclass
class ValidationError:
    """A validation issue found in a policy document."""

    field: str
    message: str
    severity: str = "error"  # "error" | "warning"


# SQL keywords that must never appear in report queries
SQL_BLOCKLIST = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "ATTACH", "PRAGMA", "CREATE"
}


# ---------------------------------------------------------------------------
# Cron validation — use APScheduler's own parser for correctness
# ---------------------------------------------------------------------------


def _validate_cron(expression: str) -> str | None:
    """Validate a cron expression using APScheduler's parser.

    Returns None if valid, or an error message if invalid.
    """
    try:
        from apscheduler.triggers.cron import CronTrigger

        CronTrigger.from_crontab(expression)
        return None
    except (ValueError, KeyError) as exc:
        return str(exc)


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------


def validate_policy(doc: PolicyDocument) -> list[ValidationError]:
    """Full structural and referential validation of a policy document.

    Returns an empty list if the policy is valid.
    """
    errors: list[ValidationError] = []

    # 1. Schema version
    if doc.schema_version != 1:
        errors.append(
            ValidationError(
                "schema_version", f"Unsupported version: {doc.schema_version}"
            )
        )

    # 2. Step count (defense-in-depth; Pydantic also validates this)
    if len(doc.steps) > 10:
        errors.append(
            ValidationError("steps", f"Max 10 steps allowed, got {len(doc.steps)}")
        )

    # 3. Step types exist in registry
    for step in doc.steps:
        if not has_step(step.type):
            errors.append(
                ValidationError(
                    f"steps[{step.id}].type",
                    f"Unknown step type: '{step.type}'",
                )
            )

    # 4. Referential integrity — refs must point to prior steps
    seen_ids: set[str] = set()
    for step in doc.steps:
        _check_refs(step.params, step.id, seen_ids, errors)
        seen_ids.add(step.id)

    # 5. Cron expression validity
    cron_error = _validate_cron(doc.trigger.cron_expression)
    if cron_error:
        errors.append(
            ValidationError(
                "trigger.cron_expression",
                f"Invalid cron expression: {cron_error}",
            )
        )

    # 6. SQL blocklist check in params
    _check_sql_blocklist(doc, errors)

    return errors


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------


def compute_content_hash(doc: PolicyDocument) -> str:
    """SHA-256 of canonical JSON representation (for change detection)."""
    canonical = json.dumps(
        doc.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_refs(
    params: dict,
    step_id: str,
    seen_ids: set[str],
    errors: list[ValidationError],
) -> None:
    """Recursively walk params dict and validate all { "ref": ... } values."""
    for key, value in params.items():
        if isinstance(value, dict):
            if "ref" in value and len(value) == 1:
                ref_path = value["ref"]
                if not isinstance(ref_path, str):
                    errors.append(
                        ValidationError(
                            f"steps[{step_id}].params.{key}",
                            f"ref value must be a string, got {type(ref_path).__name__}",
                        )
                    )
                elif not ref_path.startswith("ctx."):
                    errors.append(
                        ValidationError(
                            f"steps[{step_id}].params.{key}",
                            f"Invalid ref format: '{ref_path}' (must start with 'ctx.')",
                        )
                    )
                else:
                    ref_step = ref_path.split(".")[1]
                    if ref_step not in seen_ids:
                        errors.append(
                            ValidationError(
                                f"steps[{step_id}].params.{key}",
                                f"Ref '{ref_path}' points to step '{ref_step}' "
                                f"which hasn't executed yet (or doesn't exist)",
                            )
                        )
            else:
                _check_refs(value, step_id, seen_ids, errors)
        elif isinstance(value, list):
            _check_refs_list(value, step_id, seen_ids, errors, f"steps[{step_id}].params.{key}")


def _check_refs_list(
    items: list,
    step_id: str,
    seen_ids: set[str],
    errors: list[ValidationError],
    path: str,
) -> None:
    """Recursively walk a list for ref markers (handles list-of-list nesting)."""
    for _i, item in enumerate(items):
        if isinstance(item, dict):
            # Check if this dict IS a ref marker (e.g. {"ref": "ctx.step.output"})
            if "ref" in item and len(item) == 1:
                ref_path = item["ref"]
                if not isinstance(ref_path, str):
                    errors.append(
                        ValidationError(
                            f"{path}[{_i}]",
                            f"ref value must be a string, got {type(ref_path).__name__}",
                        )
                    )
                elif not ref_path.startswith("ctx."):
                    errors.append(
                        ValidationError(
                            f"{path}[{_i}]",
                            f"Invalid ref format: '{ref_path}' (must start with 'ctx.')",
                        )
                    )
                else:
                    ref_step = ref_path.split(".")[1]
                    if ref_step not in seen_ids:
                        errors.append(
                            ValidationError(
                                f"{path}[{_i}]",
                                f"Ref '{ref_path}' points to step '{ref_step}' "
                                f"which hasn't executed yet (or doesn't exist)",
                            )
                        )
            else:
                _check_refs(item, step_id, seen_ids, errors)
        elif isinstance(item, list):
            _check_refs_list(item, step_id, seen_ids, errors, f"{path}[{_i}]")


def _check_sql_blocklist(
    doc: PolicyDocument, errors: list[ValidationError]
) -> None:
    """Recursively scan all string values in step params for SQL injection patterns.

    Note: This is defense-in-depth. The primary protection is SQLite's
    set_authorizer + PRAGMA query_only (see Step 9.6c).
    """
    for step in doc.steps:
        _scan_value_for_sql(step.params, f"steps[{step.id}].params", errors)


def _scan_value_for_sql(
    value: Any, path: str, errors: list[ValidationError]
) -> None:
    """Recursively scan a value tree for blocked SQL keywords."""
    if isinstance(value, str):
        tokens = set(re.split(r"[^A-Za-z]+", value.upper()))
        blocked = SQL_BLOCKLIST.intersection(tokens)
        if blocked:
            errors.append(
                ValidationError(
                    path,
                    f"Blocked SQL keywords found: {blocked}",
                    severity="error",
                )
            )
    elif isinstance(value, dict):
        for k, v in value.items():
            _scan_value_for_sql(v, f"{path}.{k}", errors)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan_value_for_sql(item, f"{path}[{i}]", errors)
