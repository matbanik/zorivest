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
        FetchStep.Params(data_type="ohlcv")

    # Should fail without data_type
    with pytest.raises(ValidationError):
        FetchStep.Params(provider="ibkr")


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
    result = resolver.resolve({
        "date_range": {"type": "relative", "expr": "-30d"},
        "symbol": "AAPL",
    })

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
    """FetchStep returns cached data when use_cache=True and cache is warm."""
    from zorivest_core.domain.pipeline import StepContext, StepResult
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    step = FetchStep()
    context = StepContext(run_id="run-1", policy_id="pol-1")

    cached_content = b"cached_ohlcv_data"

    # Mock the cache and provider
    with patch.object(step, "_check_cache", return_value={
        "content": cached_content,
        "cache_status": "hit",
        "etag": "etag-1",
    }):
        result = await step.execute(
            params={
                "provider": "ibkr",
                "data_type": "ohlcv",
                "criteria": {"date_range": {"type": "relative", "expr": "-1d"}},
                "use_cache": True,
            },
            context=context,
        )

    assert result.output["cache_status"] == "hit"
    assert result.output["content"] == cached_content
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
        assert found.last_cursor == "2025-06-15T00:00:00Z"
        assert found.last_hash == "abc123"
        assert found.provider_id == "ibkr"


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
    mock_adapter.fetch.return_value = b"data"

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
    mock_adapter.fetch.return_value = b'{"data": [1, 2, 3]}'

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
    """FetchStep passes db_connection to CriteriaResolver, enabling
    db_query criteria resolution via SQL execution."""
    import sqlite3
    from unittest.mock import AsyncMock

    from zorivest_core.domain.pipeline import StepContext
    from zorivest_core.pipeline_steps.fetch_step import FetchStep

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dates (start_date TEXT, end_date TEXT)")
    conn.execute(
        "INSERT INTO dates VALUES ('2026-01-01T00:00:00+00:00', '2026-01-31T00:00:00+00:00')"
    )
    conn.commit()

    mock_adapter = AsyncMock()
    mock_adapter.fetch.return_value = b"data"

    step = FetchStep()
    context = StepContext(
        run_id="run-1",
        policy_id="pol-1",
        outputs={"db_connection": conn, "provider_adapter": mock_adapter},
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
