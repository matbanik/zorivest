# packages/core/src/zorivest_core/pipeline_steps/fetch_step.py
"""FetchStep — retrieves market data from providers (§9.4).

Spec: 09-scheduling.md §9.4a–f
MEU: 85
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import FetchResult, StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class FetchStep(RegisteredStep):
    """Fetch market data from a configured provider.

    Auto-registers as ``type_name="fetch"`` in the step registry.
    """

    type_name = "fetch"
    side_effects = False

    class Params(BaseModel):
        """FetchStep parameter schema — validated before execute()."""

        provider: str = Field(..., description="Data provider key, e.g. 'ibkr'")
        data_type: str = Field(..., description="Market data type, e.g. 'ohlcv'")
        criteria: dict[str, Any] = Field(
            default_factory=dict,
            description="Criteria for data selection (relative, incremental, or db_query)",
        )
        batch_size: int = Field(
            default=100, ge=1, le=500, description="Max records per fetch batch"
        )
        use_cache: bool = Field(
            default=True, description="Check cache before fetching"
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the fetch step.

        1. Validate params via Pydantic model
        2. Resolve criteria (relative dates, incremental HWM, db_query)
        3. Check cache if use_cache=True
        4. Fetch from provider via _fetch_from_provider() hook
        5. Return FetchResult envelope with SHA-256 hash
        """
        from zorivest_core.services.criteria_resolver import CriteriaResolver

        p = self.Params(**params)

        # 1. Resolve criteria to concrete date ranges
        resolved_criteria: dict[str, Any] = {}
        if p.criteria:
            resolver = CriteriaResolver(
                pipeline_state_repo=context.outputs.get("pipeline_state_repo"),
                db_connection=context.outputs.get("db_connection"),
            )
            resolved_criteria = resolver.resolve(p.criteria)

        # 2. Check cache first if enabled
        if p.use_cache:
            cache_hit = await self._check_cache(p, context)
            if cache_hit:
                return StepResult(
                    status=PipelineStatus.SUCCESS,
                    output={
                        "content": cache_hit["content"],
                        "cache_status": cache_hit["cache_status"],
                        "resolved_criteria": resolved_criteria,
                    },
                )

        # 3. Fetch from provider via hook method
        content = await self._fetch_from_provider(
            provider=p.provider,
            data_type=p.data_type,
            resolved_criteria=resolved_criteria,
            context=context,
        )

        result = FetchResult(
            provider=p.provider,
            data_type=p.data_type,
            content=content,
        )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "content": result.content,
                "content_hash": result.content_hash,
                "content_len": len(result.content),
                "cache_status": result.cache_status,
                "provider": result.provider,
                "data_type": result.data_type,
                "resolved_criteria": resolved_criteria,
            },
        )

    async def _fetch_from_provider(
        self,
        *,
        provider: str,
        data_type: str,
        resolved_criteria: dict[str, Any],
        context: StepContext,
    ) -> bytes:
        """Fetch data from the configured provider adapter.

        Requires 'provider_adapter' in context.outputs. Raises ValueError
        if the adapter is not injected.
        """
        adapter = context.outputs.get("provider_adapter")
        if adapter is None:
            raise ValueError(
                "provider_adapter required in context.outputs for FetchStep"
            )
        return await adapter.fetch(
            provider=provider,
            data_type=data_type,
            criteria=resolved_criteria,
        )

    async def _check_cache(
        self, params: Params, context: StepContext
    ) -> dict[str, Any] | None:
        """Check fetch cache for existing data. Returns None on miss."""
        return None
