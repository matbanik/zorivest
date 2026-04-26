# packages/core/src/zorivest_core/pipeline_steps/query_step.py
"""QueryStep — executes read-only SQL queries via SqlSandbox (§9D.1b).

Spec: 09d-pipeline-step-extensions.md §9D.1a–d
MEU: PH4

Executes parameterized SQL queries against the internal Zorivest DB through
the SqlSandbox (6-layer security stack). Supports:
  - Named :param binds
  - {ref} resolution via RefResolver
  - Multiple queries per step (fan-out cap: 5)
  - Row limit enforcement (default 1000, max 5000)
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field, field_validator

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep
from zorivest_core.services.ref_resolver import RefResolver

logger = structlog.get_logger(__name__)

_ref_resolver = RefResolver()


class QueryDef(BaseModel):
    """Definition of a single SQL query within a QueryStep."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, max_length=64)
    sql: str = Field(..., min_length=1)
    binds: dict[str, Any] = Field(default_factory=dict)


class QueryStep(RegisteredStep):
    """Execute read-only SQL queries against the internal Zorivest DB.

    Auto-registers as ``type_name="query"`` in the step registry.
    """

    type_name = "query"
    side_effects = False  # read-only
    source_type = "db"  # output metadata for taint tracking (R5*)

    class Params(BaseModel):
        """QueryStep parameter schema."""

        model_config = {"extra": "forbid"}

        queries: list[QueryDef] = Field(..., min_length=1, max_length=5)
        output_key: str = Field(default="results", min_length=1)
        row_limit: int = Field(default=1000, ge=1, le=5000)

        @field_validator("queries")
        @classmethod
        def unique_query_names(cls, v: list[QueryDef]) -> list[QueryDef]:
            """Ensure all query names are unique within a step."""
            names = [q.name for q in v]
            if len(names) != len(set(names)):
                dupes = [x for x in names if names.count(x) > 1]
                raise ValueError(f"Duplicate query names: {set(dupes)}")
            return v

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute all queries and return results keyed by query name."""
        p = self.Params(**params)
        sandbox = context.outputs["sql_sandbox"]  # PH2 provides this

        results: dict[str, list[dict]] = {}
        for q in p.queries:
            # Resolve any {ref} and {var} markers in binds
            resolved_binds = _ref_resolver.resolve(
                q.binds, context, variables=context.variables
            )

            # Execute through SqlSandbox (6-layer security stack)
            rows = sandbox.execute(q.sql, resolved_binds)

            # Enforce row limit (silently truncate)
            if len(rows) > p.row_limit:
                logger.info(
                    "query_row_limit_applied",
                    query_name=q.name,
                    total_rows=len(rows),
                    row_limit=p.row_limit,
                )
                rows = rows[: p.row_limit]

            results[q.name] = rows

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={p.output_key: results},
        )
