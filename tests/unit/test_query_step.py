# tests/unit/test_query_step.py
"""FIC: QueryStep (MEU-PH4) — Spec §9D.1b–c.

Acceptance Criteria:
  AC-4.1: Simple SELECT returns rows as list of dicts               [Spec §9D.1b]
  AC-4.2: Row limit enforced: >row_limit rows truncated             [Spec §9D.1b]
  AC-4.3: Named :param binds resolve correctly                      [Spec §9D.1b]
  AC-4.4: {"ref": "ctx.step_id.field"} in binds resolves via RefResolver [Spec §9D.1b]
  AC-4.5: Multiple queries return merged dict keyed by query name   [Spec §9D.1c]
  AC-4.6: Output shape compatible with TransformStep auto-discovery [Spec §9D.1d]
  AC-4.7: >5 queries per step raises Pydantic validation error      [Spec §9D.1b]
  AC-4.8: All SQL routed through SqlSandbox (not raw connection)    [Spec §9D.1b]
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(
    *,
    sandbox_rows: list[dict] | None = None,
    prior_outputs: dict | None = None,
) -> StepContext:
    """Build a StepContext with a mock SqlSandbox in outputs."""
    sandbox = MagicMock()
    if sandbox_rows is not None:
        sandbox.execute.return_value = sandbox_rows

    outputs: dict = {"sql_sandbox": sandbox}
    if prior_outputs:
        outputs.update(prior_outputs)

    return StepContext(
        run_id="test-run",
        policy_id="test-policy",
        outputs=outputs,
    )


# ---------------------------------------------------------------------------
# AC-4.1: Simple SELECT returns rows as list of dicts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_simple_select() -> None:
    """AC-4.1: A simple SELECT returns rows as list of dicts."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    rows = [{"ticker": "AAPL", "price": 150.0}, {"ticker": "MSFT", "price": 300.0}]
    ctx = _make_context(sandbox_rows=rows)

    step = QueryStep()
    result = await step.execute(
        {
            "queries": [
                {
                    "name": "stocks",
                    "sql": "SELECT ticker, price FROM quotes",
                    "binds": {},
                }
            ],
            "output_key": "results",
        },
        ctx,
    )

    assert result.output["results"]["stocks"] == rows


# ---------------------------------------------------------------------------
# AC-4.2: Row limit enforced
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_row_limit_enforced() -> None:
    """AC-4.2: Rows exceeding row_limit are silently truncated."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    # Generate 10 rows, set limit to 3
    rows = [{"id": i} for i in range(10)]
    ctx = _make_context(sandbox_rows=rows)

    step = QueryStep()
    result = await step.execute(
        {
            "queries": [{"name": "big", "sql": "SELECT * FROM data", "binds": {}}],
            "row_limit": 3,
            "output_key": "results",
        },
        ctx,
    )

    assert len(result.output["results"]["big"]) == 3


# ---------------------------------------------------------------------------
# AC-4.3: Named :param binds resolve correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parameterized_binds() -> None:
    """AC-4.3: Named :param binds are passed through to sandbox.execute."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    rows = [{"ticker": "AAPL"}]
    ctx = _make_context(sandbox_rows=rows)

    step = QueryStep()
    await step.execute(
        {
            "queries": [
                {
                    "name": "filtered",
                    "sql": "SELECT ticker FROM quotes WHERE ticker = :ticker",
                    "binds": {"ticker": "AAPL"},
                }
            ],
            "output_key": "results",
        },
        ctx,
    )

    # Verify the sandbox received the correct bind values
    sandbox = ctx.outputs["sql_sandbox"]
    call_args = sandbox.execute.call_args
    assert call_args[0][1] == {"ticker": "AAPL"}  # second positional arg = binds


# ---------------------------------------------------------------------------
# AC-4.4: Ref in binds resolves via RefResolver
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ref_binds() -> None:
    """AC-4.4: {\"ref\": \"ctx.step_id.field\"} in binds resolves via RefResolver."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    rows = [{"ticker": "AAPL"}]
    ctx = _make_context(
        sandbox_rows=rows,
        prior_outputs={"fetch_prices": {"output": {"watchlist_name": "Morning"}}},
    )

    step = QueryStep()
    await step.execute(
        {
            "queries": [
                {
                    "name": "watchlist",
                    "sql": "SELECT * FROM items WHERE name = :wl_name",
                    "binds": {
                        "wl_name": {"ref": "ctx.fetch_prices.output.watchlist_name"}
                    },
                }
            ],
            "output_key": "results",
        },
        ctx,
    )

    # Verify the resolved value was passed to sandbox (not the ref dict)
    sandbox = ctx.outputs["sql_sandbox"]
    call_args = sandbox.execute.call_args
    assert call_args[0][1] == {"wl_name": "Morning"}


# ---------------------------------------------------------------------------
# AC-4.5: Multiple queries return merged dict keyed by query name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_queries() -> None:
    """AC-4.5: Multiple queries return merged dict keyed by query name."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    sandbox = MagicMock()
    # First call returns stocks, second returns positions
    sandbox.execute.side_effect = [
        [{"ticker": "AAPL"}],
        [{"position": 100}],
    ]

    ctx = StepContext(
        run_id="test-run",
        policy_id="test-policy",
        outputs={"sql_sandbox": sandbox},
    )

    step = QueryStep()
    result = await step.execute(
        {
            "queries": [
                {"name": "stocks", "sql": "SELECT ticker FROM quotes", "binds": {}},
                {
                    "name": "positions",
                    "sql": "SELECT position FROM portfolio",
                    "binds": {},
                },
            ],
            "output_key": "data",
        },
        ctx,
    )

    assert "stocks" in result.output["data"]
    assert "positions" in result.output["data"]
    assert result.output["data"]["stocks"] == [{"ticker": "AAPL"}]
    assert result.output["data"]["positions"] == [{"position": 100}]


# ---------------------------------------------------------------------------
# AC-4.6: Output shape compatible with TransformStep auto-discovery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_output_shape_compatible_with_transform() -> None:
    """AC-4.6: QueryStep output dict works when consumed by TransformStep._resolve_source."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    rows = [{"ticker": "AAPL", "price": 150.0}]
    ctx = _make_context(sandbox_rows=rows)

    step = QueryStep()
    result = await step.execute(
        {
            "queries": [{"name": "quotes", "sql": "SELECT * FROM quotes", "binds": {}}],
            "output_key": "results",
        },
        ctx,
    )

    # QueryStep output is a dict keyed by output_key → dict keyed by query_name → rows
    # TransformStep._resolve_source can consume this via source_step_id
    output = result.output
    assert isinstance(output, dict)
    assert "results" in output
    assert isinstance(output["results"]["quotes"], list)
    # Rows are dicts (TransformStep expects list[dict])
    assert all(isinstance(r, dict) for r in output["results"]["quotes"])


# ---------------------------------------------------------------------------
# AC-4.7: >5 queries per step raises Pydantic validation error
# ---------------------------------------------------------------------------


def test_fan_out_cap() -> None:
    """AC-4.7: >5 queries per step raises Pydantic ValidationError."""
    from pydantic import ValidationError

    from zorivest_core.pipeline_steps.query_step import QueryStep

    six_queries = [{"name": f"q{i}", "sql": "SELECT 1", "binds": {}} for i in range(6)]

    with pytest.raises(ValidationError, match="queries"):
        QueryStep.Params(queries=six_queries, output_key="results")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# AC-4.8: All SQL routed through SqlSandbox (not raw connection)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sandbox_integration() -> None:
    """AC-4.8: SQL execution routes through SqlSandbox.execute, not raw conn."""
    from zorivest_core.pipeline_steps.query_step import QueryStep

    rows = [{"id": 1}]
    ctx = _make_context(sandbox_rows=rows)

    step = QueryStep()
    await step.execute(
        {
            "queries": [{"name": "test", "sql": "SELECT 1", "binds": {}}],
            "output_key": "results",
        },
        ctx,
    )

    # Verify sandbox.execute was called (not any raw connection)
    sandbox = ctx.outputs["sql_sandbox"]
    sandbox.execute.assert_called_once()
    # Verify the SQL was passed as first positional arg
    call_args = sandbox.execute.call_args
    assert call_args[0][0] == "SELECT 1"
