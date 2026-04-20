# tests/unit/test_fetch_step_cursor.py
"""TDD tests for MEU-PW11: FetchStep pipeline cursor tracking.

FIC — Feature Intent Contract:
  After a successful provider fetch (not cache hit), FetchStep must write
  the cursor state (last_cursor, last_hash) to pipeline_state_repo so that
  subsequent CriteriaResolver.resolve_incremental() calls start from the
  high-water mark instead of re-fetching everything.

AC-1: Successful fetch → upsert() called with correct args    (Local Canon)
AC-2: No pipeline_state_repo → no error, no call              (Local Canon)
AC-3: Cache hit → pipeline state NOT updated                   (Research-backed)
AC-4: last_cursor = valid ISO datetime string                  (Spec §9.4b)
AC-5: Round-trip: fetch writes → CriteriaResolver reads cursor (Spec §9.4b)

Spec: 09-scheduling.md §9.4b (lines 1461-1499)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext
from zorivest_core.pipeline_steps.fetch_step import FetchStep


# ── Fixtures ──────────────────────────────────────────────────────────────


def _make_context(
    *,
    run_id: str = "test-run-001",
    policy_id: str = "test-policy-001",
    provider_adapter: Any = None,
    fetch_cache_repo: Any = None,
    pipeline_state_repo: Any = None,
    extra_outputs: dict[str, Any] | None = None,
) -> StepContext:
    """Create a StepContext with injectable repos and adapter."""
    outputs: dict[str, Any] = {}
    if provider_adapter is not None:
        outputs["provider_adapter"] = provider_adapter
    if fetch_cache_repo is not None:
        outputs["fetch_cache_repo"] = fetch_cache_repo
    if pipeline_state_repo is not None:
        outputs["pipeline_state_repo"] = pipeline_state_repo
    if extra_outputs:
        outputs.update(extra_outputs)
    return StepContext(
        run_id=run_id,
        policy_id=policy_id,
        outputs=outputs,
    )


def _make_adapter(content: bytes = b'{"quotes": []}') -> AsyncMock:
    """Create a mock provider adapter that returns content."""
    adapter = AsyncMock()
    adapter.fetch.return_value = {
        "content": content,
        "cache_status": "miss",
        "etag": "etag-abc",
        "last_modified": "2026-04-20T12:00:00Z",
    }
    return adapter


DEFAULT_FETCH_PARAMS = {
    "provider": "yahoo",
    "data_type": "ohlcv",
    "criteria": {"tickers": ["AAPL"]},
    "use_cache": False,
}


# ── AC-1: Successful fetch → upsert() called with correct args ──────────


class TestCursorUpsertAfterFetch:
    """AC-1: After successful provider fetch, pipeline_state_repo.upsert()
    must be called with the correct policy_id, provider_id, data_type,
    entity_key, and last_hash.
    """

    @pytest.mark.asyncio
    async def test_cursor_upsert_after_successful_fetch(self) -> None:
        """FetchStep must call pipeline_state_repo.upsert() after fetch."""
        adapter = _make_adapter()
        state_repo = MagicMock()
        cache_repo = MagicMock()
        cache_repo.get_cached.return_value = None  # no cache

        ctx = _make_context(
            policy_id="policy-XYZ",
            provider_adapter=adapter,
            fetch_cache_repo=cache_repo,
            pipeline_state_repo=state_repo,
        )

        step = FetchStep()
        result = await step.execute(DEFAULT_FETCH_PARAMS, ctx)

        assert result.status == PipelineStatus.SUCCESS
        state_repo.upsert.assert_called_once()

        call_kwargs = state_repo.upsert.call_args.kwargs
        assert call_kwargs["policy_id"] == "policy-XYZ"
        assert call_kwargs["provider_id"] == "yahoo"
        assert call_kwargs["data_type"] == "ohlcv"
        assert "entity_key" in call_kwargs
        assert len(call_kwargs["entity_key"]) == 16  # SHA-256 truncated
        assert "last_hash" in call_kwargs
        assert len(call_kwargs["last_hash"]) == 64  # Full SHA-256 hex


# ── AC-2: No pipeline_state_repo → no error ─────────────────────────────


class TestNoPipelineStateRepo:
    """AC-2: When pipeline_state_repo is absent from context, FetchStep
    executes without error and does not attempt cursor updates.
    """

    @pytest.mark.asyncio
    async def test_no_state_repo_no_error(self) -> None:
        """FetchStep must not crash when pipeline_state_repo is missing."""
        adapter = _make_adapter()
        cache_repo = MagicMock()
        cache_repo.get_cached.return_value = None

        ctx = _make_context(
            provider_adapter=adapter,
            fetch_cache_repo=cache_repo,
            # pipeline_state_repo intentionally absent
        )

        step = FetchStep()
        result = await step.execute(DEFAULT_FETCH_PARAMS, ctx)

        assert result.status == PipelineStatus.SUCCESS


# ── AC-3: Cache hit → cursor NOT updated ─────────────────────────────────


class TestCacheHitSkipsCursor:
    """AC-3: When the fetch cache returns a fresh hit, pipeline state
    must NOT be updated (no upsert call).
    """

    @pytest.mark.asyncio
    async def test_cache_hit_skips_cursor_update(self) -> None:
        """Cache hit should return immediately without touching state repo."""
        adapter = _make_adapter()
        state_repo = MagicMock()

        # Simulate a fresh cache entry
        cache_entry = MagicMock()
        cache_entry.payload_json = b'{"quotes": []}'
        cache_entry.fetched_at = datetime.now(timezone.utc)
        cache_entry.ttl_seconds = 3600
        cache_entry.etag = "cached-etag"
        cache_entry.last_modified = None
        cache_entry.content_hash = "cached-hash"

        cache_repo = MagicMock()
        cache_repo.get_cached.return_value = cache_entry

        ctx = _make_context(
            provider_adapter=adapter,
            fetch_cache_repo=cache_repo,
            pipeline_state_repo=state_repo,
        )

        params = {**DEFAULT_FETCH_PARAMS, "use_cache": True}
        step = FetchStep()
        result = await step.execute(params, ctx)

        assert result.status == PipelineStatus.SUCCESS
        assert result.output["cache_status"] == "hit"
        # State repo must NOT be called on cache hit
        state_repo.upsert.assert_not_called()


# ── AC-4: last_cursor is valid ISO datetime ──────────────────────────────


class TestCursorIsIsoDatetime:
    """AC-4: The last_cursor value written by FetchStep must be a valid
    ISO datetime string parsable by datetime.fromisoformat().
    """

    @pytest.mark.asyncio
    async def test_cursor_is_valid_iso_datetime(self) -> None:
        """last_cursor must parse without error."""
        adapter = _make_adapter()
        state_repo = MagicMock()
        cache_repo = MagicMock()
        cache_repo.get_cached.return_value = None

        ctx = _make_context(
            provider_adapter=adapter,
            fetch_cache_repo=cache_repo,
            pipeline_state_repo=state_repo,
        )

        step = FetchStep()
        await step.execute(DEFAULT_FETCH_PARAMS, ctx)

        state_repo.upsert.assert_called_once()
        cursor_value = state_repo.upsert.call_args.kwargs["last_cursor"]
        # Must parse without ValueError
        parsed = datetime.fromisoformat(cursor_value)
        assert parsed.tzinfo is not None, "Cursor must be timezone-aware"


# ── AC-5: Round-trip: fetch writes → CriteriaResolver reads cursor ───────


class TestCursorRoundTrip:
    """AC-5: Cursor written by FetchStep must be readable by
    CriteriaResolver._resolve_incremental() and produce the correct
    start_date.
    """

    @pytest.mark.asyncio
    async def test_cursor_round_trip_with_resolver(self) -> None:
        """Write cursor via FetchStep, then read via CriteriaResolver."""
        from zorivest_core.services.criteria_resolver import CriteriaResolver

        # Step 1: Run fetch to capture the cursor value
        adapter = _make_adapter()
        captured_cursor: dict[str, Any] = {}

        def capture_upsert(**kwargs: Any) -> None:
            captured_cursor.update(kwargs)

        state_repo = MagicMock()
        state_repo.upsert.side_effect = capture_upsert

        cache_repo = MagicMock()
        cache_repo.get_cached.return_value = None

        ctx = _make_context(
            policy_id="policy-round-trip",
            provider_adapter=adapter,
            fetch_cache_repo=cache_repo,
            pipeline_state_repo=state_repo,
        )

        step = FetchStep()
        result = await step.execute(DEFAULT_FETCH_PARAMS, ctx)
        assert result.status == PipelineStatus.SUCCESS

        # Step 2: Use CriteriaResolver to read the cursor
        cursor_value = captured_cursor["last_cursor"]
        mock_state_model = MagicMock()
        mock_state_model.last_cursor = cursor_value

        read_repo = MagicMock()
        read_repo.get.return_value = mock_state_model

        resolver = CriteriaResolver(pipeline_state_repo=read_repo)
        resolved = resolver.resolve(
            {
                "date_range": {
                    "type": "incremental",
                    "policy_id": "policy-round-trip",
                    "provider_id": "yahoo",
                    "data_type": "ohlcv",
                }
            }
        )

        # The resolved start_date must equal the cursor we wrote
        start_date = resolved["date_range"]["start_date"]
        written_dt = datetime.fromisoformat(cursor_value)
        assert start_date == written_dt, (
            f"Round-trip failed: written={written_dt}, resolved={start_date}"
        )
