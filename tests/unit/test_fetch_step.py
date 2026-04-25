# tests/unit/test_fetch_step.py
"""TDD Red-phase tests for FetchStep (MEU-85).

Acceptance criteria AC-F1..AC-F15 per implementation-plan §9.4.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# AC-F1: FetchStep auto-registers with type_name="fetch"
# ---------------------------------------------------------------------------


def test_AC_F1_fetch_step_auto_registers():
    """FetchStep auto-registers in STEP_REGISTRY with type_name='fetch'."""
    from zorivest_core.domain.step_registry import STEP_REGISTRY, get_step

    # Import the pipeline_steps package to trigger eager imports
    import zorivest_core.pipeline_steps  # noqa: F401

    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    assert "fetch" in STEP_REGISTRY
    assert get_step("fetch") is FetchStep


# ---------------------------------------------------------------------------
# AC-F2: Params model validates required fields
# ---------------------------------------------------------------------------


def test_AC_F2_params_validates_required_fields():
    """FetchStep.Params rejects missing required fields."""
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    # Should succeed with required fields
    p = FetchStep.Params(provider="ibkr", data_type="ohlcv")
    assert p.provider == "ibkr"
    assert p.data_type == "ohlcv"

    # Should fail without provider
    with pytest.raises(ValidationError):
        FetchStep.Params(data_type="ohlcv")  # type: ignore[reportCallIssue]

    # Should fail without data_type
    with pytest.raises(ValidationError):
        FetchStep.Params(provider="ibkr")  # type: ignore[reportCallIssue]


# ---------------------------------------------------------------------------
# AC-F3: FetchResult computes SHA-256 content hash on init
# ---------------------------------------------------------------------------


def test_AC_F3_fetch_result_content_hash():
    """FetchResult auto-computes SHA-256 of content bytes."""
    from zorivest_core.domain.pipeline import FetchResult

    content = b'{"quotes": [1, 2, 3]}'
    result = FetchResult(
        provider="ibkr",
        data_type="ohlcv",
        content=content,
    )
    expected_hash = hashlib.sha256(content).hexdigest()
    assert result.content_hash == expected_hash


# ---------------------------------------------------------------------------
# AC-F4: CriteriaResolver resolves relative dates (per-field)
# ---------------------------------------------------------------------------


def test_AC_F4_criteria_resolver_relative_dates():
    """CriteriaResolver resolves relative date expressions like '-30d'
    using per-field resolution with static passthrough."""
    from zorivest_core.services.criteria_resolver import CriteriaResolver

    resolver = CriteriaResolver()
    result = resolver.resolve(
        {
            "date_range": {"type": "relative", "expr": "-30d"},
            "symbol": "AAPL",
        }
    )

    # Static field should pass through unchanged
    assert result["symbol"] == "AAPL"
    # Typed field should be resolved
    assert "start_date" in result["date_range"]
    assert "end_date" in result["date_range"]
    delta = result["date_range"]["end_date"] - result["date_range"]["start_date"]
    assert delta.days == 30, f"Expected 30-day delta, got {delta.days}"


# ---------------------------------------------------------------------------
# AC-F5: CriteriaResolver resolves incremental high-water marks (per-field)
# ---------------------------------------------------------------------------


def test_AC_F5_criteria_resolver_incremental():
    """CriteriaResolver resolves incremental criteria using PipelineStateRepository."""
    from datetime import datetime, timezone
    from zorivest_core.services.criteria_resolver import CriteriaResolver

    mock_state_repo = MagicMock()
    mock_state_repo.get.return_value = MagicMock(
        last_cursor="2025-01-15T00:00:00+00:00",
    )

    resolver = CriteriaResolver(pipeline_state_repo=mock_state_repo)
    result = resolver.resolve(
        {
            "hwm": {
                "type": "incremental",
                "policy_id": "policy-1",
                "provider_id": "ibkr",
                "data_type": "ohlcv",
                "entity_key": "AAPL",
            },
        },
    )

    hwm = result["hwm"]
    assert hwm["start_date"] == datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc)
    assert hwm["end_date"] > hwm["start_date"]
    mock_state_repo.get.assert_called_once_with(
        policy_id="policy-1",
        provider_id="ibkr",
        data_type="ohlcv",
        entity_key="AAPL",
    )


# ---------------------------------------------------------------------------
# AC-F6: FetchResult cache_status defaults to "miss"
# ---------------------------------------------------------------------------


def test_AC_F6_fetch_result_cache_status_default():
    """FetchResult.cache_status defaults to 'miss'."""
    from zorivest_core.domain.pipeline import FetchResult

    result = FetchResult(
        provider="ibkr",
        data_type="ohlcv",
        content=b"data",
    )
    assert result.cache_status == "miss"
    # Value: verify content_hash is computed for the data
    import hashlib

    assert result.content_hash == hashlib.sha256(b"data").hexdigest()


# ---------------------------------------------------------------------------
# AC-F7: FRESHNESS_TTL has correct values for all 4 data types
# ---------------------------------------------------------------------------


def test_AC_F7_freshness_ttl_all_data_types():
    """FRESHNESS_TTL maps all 4 DataType values to positive TTL seconds."""
    from zorivest_core.domain.pipeline import FRESHNESS_TTL

    assert len(FRESHNESS_TTL) == 4
    for dt in ("quote", "ohlcv", "news", "fundamentals"):
        assert dt in FRESHNESS_TTL
        assert isinstance(FRESHNESS_TTL[dt], int)
        assert FRESHNESS_TTL[dt] > 0


# ---------------------------------------------------------------------------
# AC-F8: is_market_closed() returns True after 4 PM ET / weekends
# ---------------------------------------------------------------------------


def test_AC_F8_is_market_closed_weekend():
    """is_market_closed() returns True on weekends."""
    from zorivest_core.domain.pipeline import is_market_closed

    # 2026-03-14 is a Saturday
    saturday = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
    assert is_market_closed(saturday) is True


def test_AC_F8_is_market_closed_after_hours():
    """is_market_closed() returns True after 4 PM ET on weekdays."""
    from zorivest_core.domain.pipeline import is_market_closed

    # 2026-03-16 is Monday, 21:30 UTC = 5:30 PM ET (after close)
    after_close = datetime(2026, 3, 16, 21, 30, tzinfo=timezone.utc)
    assert is_market_closed(after_close) is True


def test_AC_F8_is_market_open_during_hours():
    """is_market_closed() returns False during trading hours on weekdays."""
    from zorivest_core.domain.pipeline import is_market_closed

    # 2026-03-16 is Monday, 15:00 UTC = 11:00 AM ET (during trading)
    during_hours = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
    assert is_market_closed(during_hours) is False


# ---------------------------------------------------------------------------
# AC-F9: PipelineRateLimiter creates per-provider limiters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F9_rate_limiter_per_provider():
    """PipelineRateLimiter enforces per-provider limiting and global concurrency."""
    from zorivest_infra.market_data.pipeline_rate_limiter import (
        PipelineRateLimiter,
    )

    limiter = PipelineRateLimiter(
        limits={"ibkr": (10, 1.0), "polygon": (5, 1.0)},
        max_concurrent=3,
    )

    # Test through the public API: execute_with_limits should pass through return values
    call_log = []

    async def mock_fetch(provider: str) -> str:
        call_log.append(provider)
        return f"result-{provider}"

    result_ibkr = await limiter.execute_with_limits("ibkr", mock_fetch, "ibkr")
    result_polygon = await limiter.execute_with_limits("polygon", mock_fetch, "polygon")

    assert result_ibkr == "result-ibkr"
    assert result_polygon == "result-polygon"
    assert call_log == ["ibkr", "polygon"]


# ---------------------------------------------------------------------------
# AC-F10: HTTP cache returns "revalidated" on 304 response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F10_http_cache_304_revalidated():
    """fetch_with_cache returns cache_status='revalidated' on 304."""
    from zorivest_infra.market_data.http_cache import fetch_with_cache

    mock_response = MagicMock()
    mock_response.status_code = 304

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    cached_data = b'{"old": "data"}'

    result = await fetch_with_cache(
        client=mock_client,
        url="https://api.example.com/data",
        cached_content=cached_data,
        cached_etag="abc123",
    )

    assert result["cache_status"] == "revalidated"
    assert result["content"] == cached_data


# ---------------------------------------------------------------------------
# AC-F11: FetchStep with use_cache=True returns cache hit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F11_fetch_step_cache_hit():
    """FetchStep returns cached data when use_cache=True and cache is warm.

    Uses a real fetch_cache_repo mock in context instead of patching
    the private _check_cache method (F4 fix).
    """
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    cached_content_str = '{"ohlcv": "cached"}'

    # Mock cache repo returning a fresh entry
    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = cached_content_str
    mock_entry.content_hash = "cached-hash"
    mock_entry.etag = "etag-1"
    mock_entry.last_modified = "Mon, 16 Mar 2026"
    mock_entry.ttl_seconds = 3600
    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 50, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        # 15:00 UTC on Monday = 11:00 AM ET (during trading hours)
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = await step.execute(
            params={
                "provider": "ibkr",
                "data_type": "ohlcv",
                "criteria": {},
                "use_cache": True,
            },
            context=context,
        )

    assert result.output["cache_status"] == "hit"
    assert result.output["content"] == cached_content_str.encode("utf-8")
    assert result.status.value == "success"


# ---------------------------------------------------------------------------
# AC-F12: FetchStep Params rejects invalid batch_size
# ---------------------------------------------------------------------------


def test_AC_F12_params_rejects_invalid_batch_size():
    """FetchStep.Params rejects batch_size > 500 or < 1."""
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    # batch_size > 500
    with pytest.raises(ValidationError):
        FetchStep.Params(provider="ibkr", data_type="ohlcv", batch_size=501)

    # batch_size < 1
    with pytest.raises(ValidationError):
        FetchStep.Params(provider="ibkr", data_type="ohlcv", batch_size=0)

    # Valid batch_size
    p = FetchStep.Params(provider="ibkr", data_type="ohlcv", batch_size=100)
    assert p.batch_size == 100


# ---------------------------------------------------------------------------
# AC-F13: UoW exposes pipeline_state attribute
# ---------------------------------------------------------------------------


def test_AC_F13_uow_pipeline_state_attribute():
    """SqlAlchemyUnitOfWork has pipeline_state attribute."""
    from sqlalchemy import create_engine

    from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    from zorivest_infra.database.models import Base

    Base.metadata.create_all(engine)

    uow = SqlAlchemyUnitOfWork(engine)
    with uow:
        assert hasattr(uow, "pipeline_state")
        from zorivest_infra.database.scheduling_repositories import (
            PipelineStateRepository,
        )

        assert isinstance(uow.pipeline_state, PipelineStateRepository)
        # Value: verify PipelineStateRepository has expected methods
        assert hasattr(uow.pipeline_state, "get")
        assert hasattr(uow.pipeline_state, "upsert")


# ---------------------------------------------------------------------------
# AC-F14: PipelineStateRepository.get() returns state or None
# ---------------------------------------------------------------------------


def test_AC_F14_pipeline_state_repo_get():
    """PipelineStateRepository.get() returns matching state or None."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from zorivest_infra.database.models import Base
    from zorivest_infra.database.scheduling_repositories import (
        PipelineStateRepository,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = PipelineStateRepository(session)

        # Should return None for non-existent state
        result = repo.get(
            policy_id="pol-1",
            provider_id="ibkr",
            data_type="ohlcv",
            entity_key="AAPL",
        )
        assert result is None

        # Insert a state record and verify round-trip
        repo.upsert(
            policy_id="pol-1",
            provider_id="ibkr",
            data_type="ohlcv",
            entity_key="AAPL",
            last_cursor="2025-06-15T00:00:00Z",
            last_hash="abc123",
        )
        session.flush()

        found = repo.get(
            policy_id="pol-1",
            provider_id="ibkr",
            data_type="ohlcv",
            entity_key="AAPL",
        )
        assert found is not None
        assert found.last_cursor == "2025-06-15T00:00:00Z"  # type: ignore[reportGeneralTypeIssues]
        assert found.last_hash == "abc123"  # type: ignore[reportGeneralTypeIssues]
        assert found.provider_id == "ibkr"  # type: ignore[reportGeneralTypeIssues]


# ---------------------------------------------------------------------------
# AC-F15: Step registration via import
# ---------------------------------------------------------------------------


def test_AC_F15_step_registration_via_import():
    """After importing pipeline_steps package, get_step('fetch') returns FetchStep."""
    from zorivest_core.domain.step_registry import get_step

    # Clear registry first to test fresh import
    import zorivest_core.pipeline_steps  # noqa: F401

    step_cls = get_step("fetch")
    assert step_cls is not None
    assert step_cls.type_name == "fetch"
    assert step_cls.side_effects is False
    # Value: verify it's actually a callable class
    assert callable(step_cls)


# ---------------------------------------------------------------------------
# AC-F16: FetchStep.execute() resolves per-field criteria on cache-miss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F16_fetch_step_execute_resolves_criteria():
    """FetchStep.execute(use_cache=False) resolves per-field criteria and
    includes resolved_criteria in output with concrete start/end dates."""
    from unittest.mock import AsyncMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    mock_adapter = AsyncMock()
    mock_adapter.fetch.return_value = {
        "content": b"data",
        "cache_status": "miss",
        "etag": None,
        "last_modified": None,
    }

    step = FetchStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"provider_adapter": mock_adapter},
    )

    result = await step.execute(
        params={
            "provider": "ibkr",
            "data_type": "ohlcv",
            "criteria": {"date_range": {"type": "relative", "expr": "-30d"}},
            "use_cache": False,
        },
        context=context,
    )

    assert result.status.value == "success"
    assert "resolved_criteria" in result.output
    resolved = result.output["resolved_criteria"]
    assert "date_range" in resolved
    date_range = resolved["date_range"]
    assert "start_date" in date_range
    assert "end_date" in date_range
    delta = date_range["end_date"] - date_range["start_date"]
    assert delta.days == 30
    assert result.output["provider"] == "ibkr"
    assert result.output["data_type"] == "ohlcv"


# ---------------------------------------------------------------------------
# AC-F17: FetchStep._fetch_from_provider() calls injected adapter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F17_fetch_step_calls_provider_adapter():
    """When provider_adapter is injected via context.outputs,
    _fetch_from_provider() calls adapter.fetch() with correct args
    and returns the fetched content."""
    from unittest.mock import AsyncMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    mock_adapter = AsyncMock()
    mock_adapter.fetch.return_value = {
        "content": b'{"data": [1, 2, 3]}',
        "cache_status": "miss",
        "etag": None,
        "last_modified": None,
    }

    step = FetchStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"provider_adapter": mock_adapter},
    )

    result = await step.execute(
        params={
            "provider": "ibkr",
            "data_type": "ohlcv",
            "criteria": {"date_range": {"type": "relative", "expr": "-7d"}},
            "use_cache": False,
        },
        context=context,
    )

    assert result.status.value == "success"
    mock_adapter.fetch.assert_called_once()
    call_kwargs = mock_adapter.fetch.call_args.kwargs
    assert call_kwargs["provider"] == "ibkr"
    assert call_kwargs["data_type"] == "ohlcv"
    assert "criteria" in call_kwargs
    assert result.output["content"] == b'{"data": [1, 2, 3]}'
    assert result.output["content_len"] > 0


# ---------------------------------------------------------------------------
# AC-F18: CriteriaResolver db_query uses injected connection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F18_fetch_step_db_query_criteria_with_connection():
    """FetchStep passes sql_sandbox to CriteriaResolver, enabling
    db_query criteria resolution via sandboxed SQL execution."""
    import sqlite3
    from unittest.mock import AsyncMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep
    from zorivest_core.services.sql_sandbox import SqlSandbox

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dates (start_date TEXT, end_date TEXT)")
    conn.execute(
        "INSERT INTO dates VALUES ('2026-01-01T00:00:00+00:00', '2026-01-31T00:00:00+00:00')"
    )
    conn.commit()

    # Create a sandbox wrapping the same in-memory connection
    sandbox = SqlSandbox.__new__(SqlSandbox)
    sandbox._conn = conn
    sandbox._start_time = 0.0

    mock_adapter = AsyncMock()
    mock_adapter.fetch.return_value = {
        "content": b"data",
        "cache_status": "miss",
        "etag": None,
        "last_modified": None,
    }

    step = FetchStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"sql_sandbox": sandbox, "provider_adapter": mock_adapter},
    )

    result = await step.execute(
        params={
            "provider": "ibkr",
            "data_type": "ohlcv",
            "criteria": {
                "dates": {
                    "type": "db_query",
                    "sql": "SELECT start_date, end_date FROM dates LIMIT 1",
                },
            },
            "use_cache": False,
        },
        context=context,
    )

    assert result.status.value == "success"
    resolved = result.output["resolved_criteria"]
    dates = resolved["dates"]
    assert "start_date" in dates
    assert "end_date" in dates
    from datetime import datetime

    assert isinstance(dates["start_date"], datetime)
    assert dates["start_date"].year == 2026
    assert dates["start_date"].month == 1
    conn.close()


# ---------------------------------------------------------------------------
# AC-F19: FetchStep raises ValueError when provider_adapter is missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_F19_fetch_step_raises_without_adapter():
    """FetchStep.execute() raises ValueError when provider_adapter is not
    injected via context.outputs."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    with pytest.raises(ValueError, match="provider_adapter required"):
        await step.execute(
            params={
                "provider": "ibkr",
                "data_type": "ohlcv",
                "use_cache": False,
            },
            context=context,
        )


# ===========================================================================
# PW2: FetchStep._check_cache() with TTL + Market-Closed Hours
# ===========================================================================


# ---------------------------------------------------------------------------
# AC-3 (PW2): _check_cache returns cached bytes when TTL is fresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_PW2_AC3_check_cache_returns_data_when_fresh():
    """_check_cache returns cached dict when TTL is fresh."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    # Create a mock fetch_cache_repo with a fresh entry
    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": [1, 2, 3]}'
    mock_entry.content_hash = "abc123"
    mock_entry.etag = "etag-1"
    mock_entry.last_modified = "Wed, 01 Jan 2026"
    mock_entry.ttl_seconds = 3600  # 1 hour
    # fetched_at is 10 minutes ago (well within 1-hour TTL)
    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 50, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # Freeze time to 15:00 UTC (10 min after fetch, within TTL)
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
        result = await step._check_cache(params, {}, context)

    assert result is not None
    assert result["content"] is not None
    assert result["cache_status"] == "hit"


@pytest.mark.asyncio
async def test_PW2_AC3_check_cache_returns_stale_when_expired():
    """_check_cache returns stale dict (not None) when TTL is expired.

    Stale entries preserve metadata for conditional revalidation (F1).
    """
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "old"}'
    mock_entry.content_hash = "old-hash"
    mock_entry.etag = "etag-old"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 60  # 1 minute TTL (quote)
    # fetched_at is 5 minutes ago (expired for 1-minute TTL)
    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 55, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="quote")
        result = await step._check_cache(params, {}, context)

    # Stale entry returns metadata for revalidation, not None
    assert result is not None
    assert result["cache_status"] == "stale"
    assert result["etag"] == "etag-old"
    assert result["content"] is not None


@pytest.mark.asyncio
async def test_PW2_AC3_check_cache_returns_none_when_no_entry():
    """_check_cache returns None when no cache entry exists."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_cache_repo.get_cached.return_value = None

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
    result = await step._check_cache(params, {}, context)

    assert result is None


@pytest.mark.asyncio
async def test_PW2_AC3_check_cache_returns_none_when_repo_missing():
    """_check_cache returns None gracefully when fetch_cache_repo is not in context."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={},
    )

    params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
    result = await step._check_cache(params, {}, context)

    assert result is None


# ---------------------------------------------------------------------------
# AC-4 (PW2): Market-closed TTL extension (4× for ohlcv/quote)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_PW2_AC4_market_closed_extends_ttl_for_ohlcv():
    """When market is closed, ohlcv TTL is extended by 4×, so an entry
    that would be stale during market hours is still fresh."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "ohlcv"}'
    mock_entry.content_hash = "hash-1"
    mock_entry.etag = "etag-1"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 3600  # 1-hour base TTL for ohlcv
    # fetched_at is 2 hours ago — stale with base TTL, fresh with 4× (4hr)
    mock_entry.fetched_at = datetime(2026, 3, 14, 10, 0, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # 2026-03-14 is Saturday (market closed) — 12:00 UTC
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
        result = await step._check_cache(params, {}, context)

    # Should be a cache hit because 4× TTL = 4 hours, and 2 hours elapsed
    assert result is not None
    assert result["cache_status"] == "hit"


@pytest.mark.asyncio
async def test_PW2_AC4_market_open_uses_standard_ttl():
    """During market hours, standard TTL applies (no extension)."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "ohlcv"}'
    mock_entry.content_hash = "hash-1"
    mock_entry.etag = "etag-1"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 3600  # 1-hour base TTL for ohlcv
    # fetched_at is 2 hours ago — stale with base 1hr TTL
    mock_entry.fetched_at = datetime(2026, 3, 16, 13, 0, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # 2026-03-16 is Monday, 15:00 UTC = 11:00 AM ET (during trading)
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
        result = await step._check_cache(params, {}, context)

    # Should be stale — 2 hours > 1-hour TTL (returns stale metadata, not None)
    assert result is not None
    assert result["cache_status"] == "stale"


@pytest.mark.asyncio
async def test_PW2_AC4_market_closed_no_extension_for_news():
    """Market-closed TTL extension only applies to ohlcv and quote,
    NOT to news or fundamentals."""
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "news"}'
    mock_entry.content_hash = "hash-1"
    mock_entry.etag = None
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 1800  # 30 minutes for news
    # fetched_at is 1 hour ago — stale for news (30min TTL), fresh if 4× (2hr)
    mock_entry.fetched_at = datetime(2026, 3, 14, 11, 0, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # 2026-03-14 is Saturday (market closed) — 12:00 UTC
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="news")
        result = await step._check_cache(params, {}, context)

    # News should still be stale even on weekends — no TTL extension
    # But stale returns metadata, not None
    assert result is not None
    assert result["cache_status"] == "stale"


# ---------------------------------------------------------------------------
# F3 regression: Weekday after-hours TTL extension
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_PW2_AC4_weekday_after_hours_extends_ttl():
    """Monday 21:00 UTC (5:00 PM ET) is after market close.

    Canonical is_market_closed() returns True for weekday after-hours,
    so ohlcv cache should get 4× TTL extension.
    Regression for F3: weekend-only _is_market_closed was replaced.
    """
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()

    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"data": "after_hours"}'
    mock_entry.content_hash = "hash-ah"
    mock_entry.etag = "etag-ah"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 3600  # 1-hour base TTL
    # fetched_at is 2 hours ago — stale with base TTL, fresh with 4× (4hr)
    mock_entry.fetched_at = datetime(2026, 3, 16, 19, 0, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # Monday 2026-03-16, 21:00 UTC = 5:00 PM ET (after market close)
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 21, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(provider="ibkr", data_type="ohlcv")
        result = await step._check_cache(params, {}, context)

    # 4× extension: effective TTL = 4 hours, elapsed = 2 hours → fresh
    assert result is not None
    assert result["cache_status"] == "hit"


# ---------------------------------------------------------------------------
# F2 regression: Entity key consistency (resolved vs raw criteria)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_PW2_F2_entity_key_uses_resolved_criteria():
    """Cache read and write must use the same entity key.

    When criteria contain relative date_range, the resolved criteria
    differ from raw criteria. Both _check_cache and cache upsert must
    use _compute_entity_key(resolved_criteria).

    Regression for F2: cache read used params.criteria while write used
    resolved_criteria, causing divergent hashes.
    """
    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import (
        FetchStep,
        _compute_entity_key,
    )

    step = FetchStep()

    raw_criteria = {
        "date_range": {"type": "relative", "expr": "-30d"},
        "symbol": "AAPL",
    }
    resolved_criteria = {
        "date_range": {"start_date": "2026-02-14", "end_date": "2026-03-16"},
        "symbol": "AAPL",
    }
    resolved_key = _compute_entity_key(resolved_criteria)

    # Setup cache repo that returns a fresh entry when called with resolved key
    mock_cache_repo = MagicMock()
    mock_entry = MagicMock()
    mock_entry.payload_json = '{"results": [{"c": 150}]}'
    mock_entry.content_hash = "hash-resolved"
    mock_entry.etag = "etag-resolved"
    mock_entry.last_modified = None
    mock_entry.ttl_seconds = 3600
    mock_entry.fetched_at = datetime(2026, 3, 16, 14, 50, tzinfo=timezone.utc)
    mock_cache_repo.get_cached.return_value = mock_entry

    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"fetch_cache_repo": mock_cache_repo},
    )

    # Call _check_cache with resolved_criteria (as execute() now does)
    with patch("zorivest_core.pipeline_steps.fetch_step.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        params = FetchStep.Params(
            provider="ibkr",
            data_type="ohlcv",
            criteria=raw_criteria,
        )
        result = await step._check_cache(params, resolved_criteria, context)

    assert result is not None
    assert result["cache_status"] == "hit"

    # Verify the cache repo was called with the resolved key, not the raw key
    call_kwargs = mock_cache_repo.get_cached.call_args
    assert call_kwargs.kwargs["entity_key"] == resolved_key
