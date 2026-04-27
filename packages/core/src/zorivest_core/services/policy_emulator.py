# packages/core/src/zorivest_core/services/policy_emulator.py
"""4-phase policy emulator for AI policy authoring (§9F.1).

Phases:
    PARSE    → Validate policy JSON against PolicyDocument Pydantic model
    VALIDATE → Run 8+ validation rules, pre-parse SQL, check ref integrity,
               verify template existence
    SIMULATE → Execute step graph with mock/anonymized data
    RENDER   → Compile templates with simulated data, return SHA-256 hash

Security properties:
    - RENDER returns SHA-256 hash, never raw rendered content
    - SIMULATE uses synthetic/anonymized data
    - Output containment: agent gets validity signal without seeing data

Spec reference: 09f §9F.1, §9F.2, §9F.4
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from zorivest_core.domain.emulator_models import EmulatorError, EmulatorResult
from zorivest_core.domain.pipeline import PolicyDocument
from zorivest_core.domain.policy_validator import validate_policy
from zorivest_core.ports.email_template_port import EmailTemplatePort
from zorivest_core.services.secure_jinja import HardenedSandbox
from zorivest_core.services.sql_sandbox import SqlSandbox

# Default phases if none specified
_ALL_PHASES = ("PARSE", "VALIDATE", "SIMULATE", "RENDER")

# Source type mapping per §9F.4
_SOURCE_TYPES: dict[str, str] = {
    "fetch": "provider",
    "query": "db",
    "transform": "computed",
    "compose": "computed",
    "render": "computed",
    "send": "computed",
}


def _anonymize(value: Any) -> Any:
    """Anonymize step output values for emulator safety.

    Replaces actual data with type-preserving placeholders so the agent
    sees structure but never real data.
    """
    if isinstance(value, dict):
        return {k: _anonymize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_anonymize(v) for v in value]
    if isinstance(value, str):
        return "***"
    if isinstance(value, (int, float)):
        return 0
    if isinstance(value, bool):
        return False
    return None


def _get_mock_output(step_type: str) -> dict[str, Any]:
    """Generate mock output data for a step type.

    Returns synthetic data appropriate to the step type for SIMULATE phase.
    """
    source_type = _SOURCE_TYPES.get(step_type, "computed")

    base: dict[str, Any] = {
        "_source_type": source_type,
    }

    if step_type == "fetch":
        base["output"] = {"quotes": [{"ticker": "MOCK", "price": 0.0}]}
    elif step_type == "query":
        base["output"] = {"rows": [{"col1": "***", "col2": 0}], "count": 1}
    elif step_type == "transform":
        base["output"] = {"transformed": True}
    elif step_type == "compose":
        base["output"] = {"sections": []}
    elif step_type == "send":
        base["output"] = {"sent": False, "dry_run": True}
    else:
        base["output"] = {}

    return base


class PolicyEmulator:
    """4-phase dry-run engine for AI policy authoring."""

    def __init__(
        self,
        sandbox: SqlSandbox,
        template_engine: HardenedSandbox,
        template_port: EmailTemplatePort,
        email_config_checker: Callable[[], bool] | None = None,
    ) -> None:
        """Initialize emulator with security services.

        Args:
            sandbox: SQL sandbox for query validation (validate_sql only).
            template_engine: Hardened Jinja2 sandbox for template rendering.
            template_port: Core port for template lookup (NOT infra repo).
            email_config_checker: Callable returning True if SMTP is configured.
                                  If None, SMTP check is skipped (backward compat).
        """
        self._sandbox = sandbox
        self._engine = template_engine
        self._template_port = template_port
        self._email_config_checker = email_config_checker

    async def emulate(
        self,
        policy_json: dict,
        phases: list[str] | None = None,
    ) -> EmulatorResult:
        """Run the emulator on a policy JSON dict.

        Args:
            policy_json: Raw policy dict (will be validated by Pydantic).
            phases: Optional subset of phases to run. Default: all 4.

        Returns:
            EmulatorResult with structured errors/warnings and mock outputs.
        """
        active_phases = phases or list(_ALL_PHASES)
        result = EmulatorResult()
        policy: PolicyDocument | None = None

        # PHASE 1: PARSE
        if "PARSE" in active_phases:
            try:
                policy = PolicyDocument(**policy_json)
                result.phase = "PARSE"
            except (ValidationError, TypeError) as e:
                result.valid = False
                result.errors.append(
                    EmulatorError(
                        phase="PARSE",
                        error_type="SCHEMA_INVALID",
                        message=str(e),
                    )
                )
                result.phase = "PARSE"
                return result

        # If PARSE wasn't requested but later phases need the doc, try to parse
        if policy is None and any(
            p in active_phases for p in ("VALIDATE", "SIMULATE", "RENDER")
        ):
            try:
                policy = PolicyDocument(**policy_json)
            except (ValidationError, TypeError) as e:
                result.valid = False
                result.errors.append(
                    EmulatorError(
                        phase="PARSE",
                        error_type="SCHEMA_INVALID",
                        message=str(e),
                    )
                )
                result.phase = "PARSE"
                return result

        # PHASE 2: VALIDATE
        if "VALIDATE" in active_phases and policy is not None:
            self._run_validate(policy, result)
            result.phase = "VALIDATE"

        # PHASE 3: SIMULATE
        if "SIMULATE" in active_phases and policy is not None and result.valid:
            self._run_simulate(policy, result)
            result.phase = "SIMULATE"

        # PHASE 4: RENDER
        if "RENDER" in active_phases and policy is not None and result.valid:
            self._run_render(policy, result)
            result.phase = "RENDER"

        return result

    def _run_validate(self, policy: PolicyDocument, result: EmulatorResult) -> None:
        """PHASE 2: Structural + semantic validation."""
        # Run standard policy validator
        val_errors = validate_policy(policy)
        for ve in val_errors:
            error_type = self._classify_validation_error(ve)
            result.errors.append(
                EmulatorError(
                    phase="VALIDATE",
                    error_type=error_type,
                    field=ve.field,
                    message=ve.message,
                )
            )
            if ve.severity == "warning":
                # Move warnings from errors to warnings list
                result.warnings.append(result.errors.pop())

        # SQL validation for query steps
        for step in policy.steps:
            if step.type == "query":
                for query in step.params.get("queries", []):
                    sql = query.get("sql", "")
                    sql_errors = self._sandbox.validate_sql(sql)
                    for sql_err in sql_errors:
                        result.errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="SQL_BLOCKED",
                                step_id=step.id,
                                message=sql_err,
                            )
                        )

        # Template existence check for send steps
        for step in policy.steps:
            if step.type == "send":
                tmpl_name = step.params.get("body_template")
                if tmpl_name:
                    tmpl = self._template_port.get_by_name(tmpl_name)
                    if not tmpl:
                        result.errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="TEMPLATE_MISSING",
                                step_id=step.id,
                                field=f"steps[{step.id}].params.body_template",
                                message=f"Template '{tmpl_name}' not found",
                            )
                        )

        # Ref integrity check
        ref_errors = self._check_ref_integrity(policy)
        for ref_err in ref_errors:
            result.errors.append(ref_err)

        # PH13: EXPLAIN SQL schema check (AC-26/AC-27)
        for step in policy.steps:
            if step.type == "query":
                for query in step.params.get("queries", []):
                    sql = query.get("sql", "")
                    try:
                        self._sandbox.execute(f"EXPLAIN {sql}", {})
                    except Exception as e:
                        result.errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="SQL_SCHEMA_ERROR",
                                step_id=step.id,
                                message=str(e),
                            )
                        )

        # PH13: SMTP readiness check (AC-28/AC-29)
        # Only email-channel send steps require SMTP — local_file steps do not.
        has_email_send_steps = any(
            s.type == "send" and s.params.get("channel") == "email"
            for s in policy.steps
        )
        if has_email_send_steps and self._email_config_checker is not None:
            if not self._email_config_checker():
                result.errors.append(
                    EmulatorError(
                        phase="VALIDATE",
                        error_type="SMTP_NOT_CONFIGURED",
                        message="Policy has send steps but SMTP email is not configured. "
                        "Configure email settings before running this policy.",
                    )
                )

        # PH13: Step wiring validation (AC-30..AC-33)
        step_map = {s.id: s for s in policy.steps}
        for step in policy.steps:
            if step.type == "send":
                body_from = step.params.get("body_from_step")
                if body_from:
                    target = step_map.get(body_from)
                    if target is None:
                        result.errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="STEP_WIRING_ERROR",
                                step_id=step.id,
                                field=f"steps[{step.id}].params.body_from_step",
                                message=f"body_from_step references nonexistent step '{body_from}'",
                            )
                        )
                    elif target.type not in ("render", "compose"):
                        result.errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="STEP_WIRING_ERROR",
                                step_id=step.id,
                                field=f"steps[{step.id}].params.body_from_step",
                                message=f"body_from_step references step '{body_from}' of type "
                                f"'{target.type}', expected 'render' or 'compose'",
                            )
                        )

        if result.errors:
            result.valid = False

    def _run_simulate(self, policy: PolicyDocument, result: EmulatorResult) -> None:
        """PHASE 3: Mock execution with anonymized data."""
        mock_outputs: dict[str, Any] = {}
        for step_def in policy.steps:
            mock_output = _get_mock_output(step_def.type)
            mock_outputs[step_def.id] = _anonymize(mock_output)
        result.mock_outputs = mock_outputs

    def _run_render(self, policy: PolicyDocument, result: EmulatorResult) -> None:
        """PHASE 4: Template compilation with SHA-256 output."""
        mock_context = result.mock_outputs or {}
        for step_def in policy.steps:
            if step_def.type == "send":
                template_source: str | None = None

                # Check named template (body_template field)
                tmpl_name = step_def.params.get("body_template")
                if tmpl_name:
                    tmpl_dto = self._template_port.get_by_name(tmpl_name)
                    if tmpl_dto:
                        template_source = tmpl_dto.body_html

                # Check inline template (body_template_inline field)
                inline = step_def.params.get("body_template_inline")
                if inline:
                    template_source = inline

                if template_source:
                    try:
                        rendered = self._engine.render_safe(
                            template_source, mock_context
                        )
                        result.template_preview_hash = hashlib.sha256(
                            rendered.encode()
                        ).hexdigest()
                    except Exception as e:
                        result.errors.append(
                            EmulatorError(
                                phase="RENDER",
                                error_type="RENDER_ERROR",
                                step_id=step_def.id,
                                message=str(e),
                            )
                        )
                        result.valid = False

    def _check_ref_integrity(self, policy: PolicyDocument) -> list[EmulatorError]:
        """Check that all step refs point to preceding steps."""
        errors: list[EmulatorError] = []
        step_ids = {s.id for s in policy.steps}
        seen_ids: set[str] = set()

        for step in policy.steps:
            self._walk_refs(step.params, step.id, seen_ids, step_ids, errors)
            seen_ids.add(step.id)

        return errors

    def _walk_refs(
        self,
        obj: Any,
        step_id: str,
        seen_ids: set[str],
        all_ids: set[str],
        errors: list[EmulatorError],
    ) -> None:
        """Recursively walk params for ref markers and validate them."""
        if isinstance(obj, dict):
            if "ref" in obj and len(obj) == 1:
                ref_path = obj["ref"]
                if isinstance(ref_path, str) and ref_path.startswith("ctx."):
                    ref_step = ref_path.split(".")[1]
                    if ref_step not in seen_ids:
                        errors.append(
                            EmulatorError(
                                phase="VALIDATE",
                                error_type="REF_UNRESOLVED",
                                step_id=step_id,
                                message=(
                                    f"Ref '{ref_path}' points to step '{ref_step}' "
                                    f"which hasn't executed yet (or doesn't exist)"
                                ),
                            )
                        )
            else:
                for v in obj.values():
                    self._walk_refs(v, step_id, seen_ids, all_ids, errors)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self._walk_refs(item, step_id, seen_ids, all_ids, errors)

    @staticmethod
    def _classify_validation_error(ve: Any) -> str:
        """Map a policy_validator.ValidationError to an emulator error_type."""
        msg = ve.message.lower()
        if "ref" in msg and ("hasn't executed" in msg or "doesn't exist" in msg):
            return "REF_UNRESOLVED"
        if "sql" in msg:
            return "SQL_BLOCKED"
        if "step type" in msg or "unknown" in msg:
            return "VALIDATION_FAILED"
        if "cron" in msg:
            return "VALIDATION_FAILED"
        if "variable" in msg and "unused" in msg:
            return "VARIABLE_UNUSED"
        return "VALIDATION_FAILED"
