# packages/core/src/zorivest_core/pipeline_steps/compose_step.py
"""ComposeStep — merges outputs from multiple steps (§9D.2b).

Spec: 09d-pipeline-step-extensions.md §9D.2a–d
MEU: PH5

Merges outputs from multiple preceding steps into a single dict for
template rendering. Supports:
  - dict_merge: each source maps to a key in the merged dict
  - array_concat: items from all sources concatenated into a single list
  - rename: override the key under which a source is stored
"""

from __future__ import annotations

from typing import Literal

import structlog
from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep

logger = structlog.get_logger(__name__)


class SourceDef(BaseModel):
    """Definition of a single source for ComposeStep."""

    model_config = {"extra": "forbid"}

    step_id: str = Field(..., min_length=1, max_length=64)
    key: str | None = Field(
        default=None,
        description="Key within the step's output dict to extract. None = entire output.",
    )
    rename: str | None = Field(
        default=None,
        description="Override key name in the merged output.",
    )


class ComposeStep(RegisteredStep):
    """Merge outputs from multiple preceding steps.

    Auto-registers as ``type_name="compose"`` in the step registry.
    """

    type_name = "compose"
    side_effects = False
    source_type = "computed"  # output metadata for taint tracking

    class Params(BaseModel):
        """ComposeStep parameter schema."""

        model_config = {"extra": "forbid"}

        sources: list[SourceDef] = Field(..., min_length=1)
        output_key: str = Field(default="composed", min_length=1)
        merge_strategy: Literal["dict_merge", "array_concat"] = "dict_merge"

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the compose step: merge upstream outputs."""
        p = self.Params(**params)
        merged: dict = {}

        for src in p.sources:
            # get_output returns a deep copy (§9C.1b isolation).
            # When an optional upstream step failed (on_error="log_and_continue"),
            # its output won't exist — skip gracefully instead of crashing.
            try:
                upstream = context.get_output(src.step_id)
            except KeyError:
                target_key = src.rename or src.key or src.step_id
                logger.warning(
                    "compose_step.source_missing",
                    step_id=src.step_id,
                    target_key=target_key,
                    msg=f"Upstream step '{src.step_id}' has no output — skipping",
                )
                continue

            # Extract specific key if provided, otherwise use entire output
            data = upstream.get(src.key, upstream) if src.key else upstream

            # Determine the target key in merged output
            target_key = src.rename or src.key or src.step_id

            if p.merge_strategy == "dict_merge":
                merged[target_key] = data
            elif p.merge_strategy == "array_concat":
                merged.setdefault("items", []).extend(
                    data if isinstance(data, list) else [data]
                )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={p.output_key: merged},
        )
