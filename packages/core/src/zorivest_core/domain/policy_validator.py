# packages/core/src/zorivest_core/domain/policy_validator.py
"""Policy validation module for the pipeline engine (Phase 9).

Implements:
- validate_policy(): structural + referential validation (8 rules)
- compute_content_hash(): SHA-256 for change detection
- scan_for_secrets(): regex guard on policy text (§9C.5)
- policy_content_id(): content-addressable SHA-256 (§9C.6)
- AST-based SQL validation via SqlSandbox (§9C.2b)

Spec reference: 09-scheduling.md §9.1g, 09c §9C.5, §9C.6
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from zorivest_core.domain.pipeline import PolicyDocument
from zorivest_core.domain.step_registry import STEP_REGISTRY, has_step


@dataclass
class ValidationError:
    """A validation issue found in a policy document."""

    field: str
    message: str
    severity: str = "error"  # "error" | "warning"


# ---------------------------------------------------------------------------
# §9C.5: Secrets Scanning — regex guard on policy text
# ---------------------------------------------------------------------------

_SECRETS_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|ghp_[a-zA-Z0-9]{36}"
    r"|Bearer\s+[a-zA-Z0-9\-._~+/]+=*"
    r"|-----BEGIN.*PRIVATE KEY-----"
    r")"
)


def scan_for_secrets(policy_json: str) -> list[str]:
    """Scan policy JSON text for possible embedded credentials.

    Returns a list of truncated match descriptions. Empty = clean.
    """
    matches = _SECRETS_PATTERN.findall(policy_json)
    if matches:
        return [f"Possible credential detected: {m[:10]}..." for m in matches]
    return []


# ---------------------------------------------------------------------------
# §9C.6: Content-Addressable Policy IDs
# ---------------------------------------------------------------------------


def policy_content_id(policy: dict) -> str:
    """SHA-256 of canonical JSON for audit trail and TOCTOU prevention."""
    canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


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
    if doc.schema_version not in (1, 2):
        errors.append(
            ValidationError(
                "schema_version", f"Unsupported version: {doc.schema_version}"
            )
        )

    # 2. Step count (defense-in-depth; Pydantic also validates this)
    if len(doc.steps) > 20:
        errors.append(
            ValidationError("steps", f"Max 20 steps allowed, got {len(doc.steps)}")
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

    # 6. SQL AST validation in params (replaces old SQL_BLOCKLIST)
    _check_sql_ast(doc, errors)

    # 7. Step params validation against Params model (AC-9)
    # For each step with a known type in STEP_REGISTRY, validate step.params
    # against the step class's Params model. Invalid values → 422 at boundary.
    _check_step_params(doc, errors)

    # 8. v2 feature gating (defense-in-depth, mirrors model_validator)
    _check_v2_features(doc, errors)

    # 9. Unused variable warning (v2 only)
    _check_unused_variables(doc, errors)

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
            _check_refs_list(
                value, step_id, seen_ids, errors, f"steps[{step_id}].params.{key}"
            )


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


def _check_sql_ast(doc: PolicyDocument, errors: list[ValidationError]) -> None:
    """Validate SQL strings in step params using sqlglot AST analysis.

    Replaces the old SQL_BLOCKLIST string-match approach (§9C.2b).
    Uses SqlSandbox.validate_sql() for C-level equivalent validation.
    """
    from zorivest_core.services.sql_sandbox import SqlSandbox

    sandbox = SqlSandbox.__new__(SqlSandbox)  # no connection needed for validate_sql
    for step in doc.steps:
        _scan_value_for_sql_ast(
            step.params, f"steps[{step.id}].params", errors, sandbox
        )


def _scan_value_for_sql_ast(
    value: Any, path: str, errors: list[ValidationError], sandbox: Any
) -> None:
    """Recursively scan a value tree for blocked SQL using AST validation."""
    if isinstance(value, str):
        # Only validate strings that look like SQL (contain SELECT/INSERT/etc.)
        sql_keywords = {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "ATTACH",
        }
        tokens = set(re.split(r"[^A-Za-z]+", value.upper()))
        if sql_keywords.intersection(tokens):
            ast_errors = sandbox.validate_sql(value)
            if ast_errors:
                errors.append(
                    ValidationError(
                        path,
                        f"SQL validation failed: {ast_errors}",
                        severity="error",
                    )
                )
    elif isinstance(value, dict):
        for k, v in value.items():
            _scan_value_for_sql_ast(v, f"{path}.{k}", errors, sandbox)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan_value_for_sql_ast(item, f"{path}[{i}]", errors, sandbox)


def _check_step_params(doc: PolicyDocument, errors: list[ValidationError]) -> None:
    """Rule 7: validate step.params against the step class's Params model (AC-9).

    For each step with a known type in STEP_REGISTRY that has a Params class,
    attempt to instantiate the Params model with step.params. If validation
    fails, append the Pydantic errors as policy ValidationErrors.

    Steps without a Params class skip validation (their params are opaque).
    """
    from pydantic import ValidationError as PydanticValidationError

    for step in doc.steps:
        step_cls = STEP_REGISTRY.get(step.type)
        if step_cls is None:
            continue  # Unknown step types already caught by rule 3

        params_cls = getattr(step_cls, "Params", None)
        if params_cls is None:
            continue  # Step has no Params model — skip

        try:
            params_cls(**step.params)
        except PydanticValidationError as exc:
            for pydantic_error in exc.errors():
                loc = ".".join(str(loc_part) for loc_part in pydantic_error["loc"])
                input_repr = repr(pydantic_error.get("input", ""))
                errors.append(
                    ValidationError(
                        f"steps[{step.id}].params.{loc}",
                        f"{loc}: {pydantic_error['msg']} (input={input_repr})",
                        severity="error",
                    )
                )


def _check_v2_features(doc: PolicyDocument, errors: list[ValidationError]) -> None:
    """Rule 8: reject v2 features when schema_version=1 (defense-in-depth).

    This mirrors the model_validator on PolicyDocument, but provides
    defense-in-depth validation at the policy_validator layer. This catches
    cases where the model_validator is bypassed (e.g., direct attribute set).
    """
    if doc.schema_version >= 2:
        return  # v2 features are allowed on v2 schemas

    # Check for v2 step types
    v2_step_types = {"query", "compose"}
    for step in doc.steps:
        if step.type in v2_step_types:
            errors.append(
                ValidationError(
                    f"steps[{step.id}].type",
                    f"Step type '{step.type}' requires schema_version >= 2 (v2 feature)",
                )
            )

    # Check for assertion kind
    for step in doc.steps:
        if step.params.get("kind") == "assertion":
            errors.append(
                ValidationError(
                    f"steps[{step.id}].params.kind",
                    "Assertion kind requires schema_version >= 2 (v2 feature)",
                )
            )

    # Check for {var: ...} refs in params
    var_refs = _scan_for_var_refs(doc)
    for step_id, path in var_refs:
        errors.append(
            ValidationError(
                f"steps[{step_id}].params.{path}",
                'Variable refs {{"var": ...}} require schema_version >= 2 (v2 feature)',
            )
        )


def _scan_for_var_refs(doc: PolicyDocument) -> list[tuple[str, str]]:
    """Find all {var: ...} references in step params."""
    found: list[tuple[str, str]] = []
    for step in doc.steps:
        _find_var_refs(step.params, step.id, "", found)
    return found


def _find_var_refs(
    obj: Any,
    step_id: str,
    path: str,
    found: list[tuple[str, str]],
) -> None:
    """Recursively scan for {var: ...} dicts."""
    if isinstance(obj, dict):
        if "var" in obj and len(obj) == 1:
            found.append((step_id, path or "root"))
        else:
            for k, v in obj.items():
                _find_var_refs(v, step_id, f"{path}.{k}" if path else k, found)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _find_var_refs(item, step_id, f"{path}[{i}]", found)


def _check_unused_variables(doc: PolicyDocument, errors: list[ValidationError]) -> None:
    """Rule 9: warn about unused variables in v2 policies."""
    if doc.schema_version < 2 or not doc.variables:
        return

    # Collect referenced variable names from step params
    referenced_vars: set[str] = set()
    for step in doc.steps:
        _collect_referenced_var_names(step.params, referenced_vars)

    unused = set(doc.variables.keys()) - referenced_vars
    for var_name in sorted(unused):
        errors.append(
            ValidationError(
                f"variables.{var_name}",
                f"Unused variable '{var_name}' defined but never referenced",
                severity="warning",
            )
        )


def _collect_referenced_var_names(obj: Any, names: set[str]) -> None:
    """Recursively collect all variable names from {var: ...} refs."""
    if isinstance(obj, dict):
        if "var" in obj and len(obj) == 1:
            names.add(obj["var"])
        else:
            for v in obj.values():
                _collect_referenced_var_names(v, names)
    elif isinstance(obj, list):
        for item in obj:
            _collect_referenced_var_names(item, names)
