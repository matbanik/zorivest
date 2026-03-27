"""Resolves parameter references in pipeline step params (§9.3b).

Recursively walks a params dict, replacing single-key ``{"ref": "ctx.<step_id>.<path>"}``
objects with actual values from the pipeline context.
"""

from __future__ import annotations

from typing import Any

from zorivest_core.domain.pipeline import StepContext


class RefResolver:
    """Resolves ``{"ref": "ctx.<step_id>.output.<path>"}`` references in step params."""

    def resolve(self, params: dict, context: StepContext) -> dict:
        """Return a new dict with all refs resolved."""
        return self._walk(params, context)

    def _walk(self, obj: Any, context: StepContext) -> Any:
        if isinstance(obj, dict):
            # Single-key dict with "ref" → resolve
            if "ref" in obj and len(obj) == 1:
                return self._resolve_ref(obj["ref"], context)
            return {k: self._walk(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._walk(item, context) for item in obj]
        return obj

    def _resolve_ref(self, ref_path: str, context: StepContext) -> Any:
        """Resolve ``ctx.step_id.output.nested.path`` to an actual value."""
        parts = ref_path.split(".")
        if parts[0] != "ctx" or len(parts) < 2:
            raise ValueError(f"Invalid ref format: {ref_path}")

        step_id = parts[1]
        value = context.get_output(step_id)  # Raises KeyError if missing

        # Navigate nested path
        for part in parts[2:]:
            if isinstance(value, dict):
                if part not in value:
                    raise KeyError(
                        f"Ref path '{ref_path}': key '{part}' not found "
                        f"in {list(value.keys())}"
                    )
                value = value[part]
            elif isinstance(value, list):
                try:
                    value = value[int(part)]
                except (ValueError, IndexError):
                    raise KeyError(f"Ref path '{ref_path}': invalid index '{part}'")
            else:
                raise KeyError(
                    f"Ref path '{ref_path}': cannot traverse "
                    f"into {type(value).__name__}"
                )

        return value
