# packages/core/src/zorivest_core/pipeline_steps/fetch_step.py
"""FetchStep — retrieves market data from providers (§9.4).

Spec: 09-scheduling.md §9.4a–f
MEU: 85
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import (
    FetchResult,
    StepContext,
    StepResult,
    is_market_closed,
)
from zorivest_core.domain.step_registry import RegisteredStep

# Data types that benefit from extended TTL when markets are closed
_MARKET_SENSITIVE_TYPES = {"ohlcv", "quote"}

# Multiplier for TTL when market is closed (e.g., weekends)
_MARKET_CLOSED_TTL_MULTIPLIER = 4


def _compute_entity_key(criteria: dict[str, Any]) -> str:
    """Compute deterministic entity key from criteria.

    SHA-256 of sorted JSON criteria, truncated to 16 chars.
    """
    serialized = json.dumps(criteria, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


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
        use_cache: bool = Field(default=True, description="Check cache before fetching")

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

        # 1. Resolve criteria to concrete date ranges (before cache — F2)
        resolved_criteria: dict[str, Any] = {}
        if p.criteria:
            resolver = CriteriaResolver(
                pipeline_state_repo=context.outputs.get("pipeline_state_repo"),
                db_connection=context.outputs.get("db_connection"),
            )
            resolved_criteria = resolver.resolve(p.criteria)

        # 2. Check cache first if enabled
        stale_meta: dict[str, Any] | None = None
        if p.use_cache:
            cache_result = await self._check_cache(p, resolved_criteria, context)
            if cache_result is not None:
                if cache_result["cache_status"] == "hit":
                    return StepResult(
                        status=PipelineStatus.SUCCESS,
                        output={
                            "content": cache_result["content"],
                            "cache_status": "hit",
                            "resolved_criteria": resolved_criteria,
                        },
                    )
                # Stale entry — preserve metadata for conditional revalidation
                stale_meta = cache_result

        # 3. Fetch from provider (forward stale cache metadata — F1)
        adapter_result = await self._fetch_from_provider(
            provider=p.provider,
            data_type=p.data_type,
            resolved_criteria=resolved_criteria,
            context=context,
            cached_content=stale_meta["content"] if stale_meta else None,
            cached_etag=stale_meta.get("etag") if stale_meta else None,
            cached_last_modified=stale_meta.get("last_modified")
            if stale_meta
            else None,
        )

        content = adapter_result["content"]
        result = FetchResult(
            provider=p.provider,
            data_type=p.data_type,
            content=content,
        )

        # 4. Upsert cache after successful fetch
        cache_repo = context.outputs.get("fetch_cache_repo")
        if cache_repo is not None:
            from zorivest_core.domain.pipeline import FRESHNESS_TTL

            entity_key = _compute_entity_key(resolved_criteria)
            cache_repo.upsert(
                provider=p.provider,
                data_type=p.data_type,
                entity_key=entity_key,
                payload_json=content.decode("utf-8")
                if isinstance(content, bytes)
                else content,
                content_hash=result.content_hash,
                ttl_seconds=FRESHNESS_TTL.get(p.data_type, 3600),
                etag=adapter_result.get("etag"),
                last_modified=adapter_result.get("last_modified"),
            )

        # 5. Update pipeline cursor state for incremental tracking (MEU-PW11)
        state_repo = context.outputs.get("pipeline_state_repo")
        if state_repo is not None:
            from datetime import datetime as _dt
            from datetime import timezone as _tz

            entity_key = _compute_entity_key(resolved_criteria)
            state_repo.upsert(
                policy_id=context.policy_id,
                provider_id=p.provider,
                data_type=p.data_type,
                entity_key=entity_key,
                last_cursor=_dt.now(_tz.utc).isoformat(),
                last_hash=result.content_hash,
            )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "content": result.content,
                "content_hash": result.content_hash,
                "content_len": len(result.content),
                "cache_status": adapter_result.get("cache_status", "miss"),
                "provider": result.provider,
                "data_type": result.data_type,
                "resolved_criteria": resolved_criteria,
                "etag": adapter_result.get("etag"),
                "last_modified": adapter_result.get("last_modified"),
            },
        )

    async def _fetch_from_provider(
        self,
        *,
        provider: str,
        data_type: str,
        resolved_criteria: dict[str, Any],
        context: StepContext,
        cached_content: bytes | None = None,
        cached_etag: str | None = None,
        cached_last_modified: str | None = None,
    ) -> dict[str, Any]:
        """Fetch data from the configured provider adapter.

        Requires 'provider_adapter' in context.outputs. Raises ValueError
        if the adapter is not injected.

        When stale cache metadata is provided, the adapter can send
        conditional headers (If-None-Match / If-Modified-Since) for
        HTTP 304 revalidation.

        Returns:
            FetchAdapterResult dict with content, cache_status, etag, last_modified.
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
            cached_content=cached_content,
            cached_etag=cached_etag,
            cached_last_modified=cached_last_modified,
        )

    async def _check_cache(
        self,
        params: Params,
        resolved_criteria: dict[str, Any],
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Check fetch cache for existing data with TTL freshness.

        Returns:
            - dict with cache_status="hit" when TTL is fresh (use directly).
            - dict with cache_status="stale" when TTL expired but entry
              exists (caller should forward metadata for revalidation).
            - None when no cache entry exists at all.

        TTL extension: During market-closed hours (weekends and weekday
        after-hours), ohlcv and quote data types get 4× TTL extension
        since prices don't change.
        """
        cache_repo = context.outputs.get("fetch_cache_repo")
        if cache_repo is None:
            return None

        entity_key = _compute_entity_key(resolved_criteria)
        entry = cache_repo.get_cached(
            provider=params.provider,
            data_type=params.data_type,
            entity_key=entity_key,
        )
        if entry is None:
            return None

        # Parse payload once — used for both hit and stale paths
        content = entry.payload_json
        if isinstance(content, str):
            content = content.encode("utf-8")

        # TTL freshness check
        now = datetime.now(tz=timezone.utc)
        # SQLite returns naive datetimes; normalize to UTC-aware for subtraction
        fetched_at = entry.fetched_at
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        elapsed = (now - fetched_at).total_seconds()
        effective_ttl = entry.ttl_seconds

        # Apply market-closed extension for market-sensitive data types
        # Uses canonical is_market_closed() with weekday after-hours (F3)
        if params.data_type in _MARKET_SENSITIVE_TYPES and is_market_closed(now):
            effective_ttl = entry.ttl_seconds * _MARKET_CLOSED_TTL_MULTIPLIER

        if elapsed > effective_ttl:
            # Stale — return metadata for conditional revalidation (F1)
            return {
                "content": content,
                "cache_status": "stale",
                "etag": entry.etag,
                "last_modified": entry.last_modified,
                "content_hash": entry.content_hash,
            }

        # Cache hit — fresh data
        return {
            "content": content,
            "cache_status": "hit",
            "etag": entry.etag,
            "last_modified": entry.last_modified,
            "content_hash": entry.content_hash,
        }
