# tests/unit/test_compose_step.py
"""FIC: ComposeStep (MEU-PH5) — Spec §9D.2b–c.

Acceptance Criteria:
  AC-5.1: Multiple sources merged into single dict via dict_merge     [Spec §9D.2b]
  AC-5.2: Lists from multiple sources concatenated via array_concat   [Spec §9D.2b]
  AC-5.3: Source renamed via rename field                             [Spec §9D.2c]
  AC-5.4: Non-existent step_id raises KeyError                       [Spec §9D.2c]
  AC-5.5: Composed output is deep-copy isolated from source          [Spec §9D.2c, Local Canon §9C.1b]
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(outputs: dict) -> StepContext:
    """Build a StepContext with pre-populated step outputs."""
    ctx = StepContext(
        run_id="test-run",
        policy_id="test-policy",
        outputs={},
    )
    # Use put_output to store deep copies (per §9C.1b)
    for key, value in outputs.items():
        ctx.put_output(key, value)
    return ctx


# ---------------------------------------------------------------------------
# AC-5.1: dict_merge — multiple sources merged into single dict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dict_merge() -> None:
    """AC-5.1: Multiple sources merged into single dict via dict_merge."""
    from zorivest_core.pipeline_steps.compose_step import ComposeStep

    ctx = _make_context(
        {
            "quotes": {"results": {"AAPL": 150.0, "MSFT": 300.0}},
            "watchlist": {"tickers": ["AAPL", "TSLA"]},
        }
    )

    step = ComposeStep()
    result = await step.execute(
        {
            "sources": [
                {"step_id": "quotes", "key": "results", "rename": "market_data"},
                {"step_id": "watchlist", "key": "tickers", "rename": "watchlist"},
            ],
            "output_key": "report_data",
            "merge_strategy": "dict_merge",
        },
        ctx,
    )

    assert result.output["report_data"]["market_data"] == {"AAPL": 150.0, "MSFT": 300.0}
    assert result.output["report_data"]["watchlist"] == ["AAPL", "TSLA"]


# ---------------------------------------------------------------------------
# AC-5.2: array_concat — lists from multiple sources concatenated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_array_concat() -> None:
    """AC-5.2: Lists from multiple sources concatenated via array_concat."""
    from zorivest_core.pipeline_steps.compose_step import ComposeStep

    ctx = _make_context(
        {
            "batch1": {"items": [{"ticker": "AAPL"}]},
            "batch2": {"items": [{"ticker": "MSFT"}]},
        }
    )

    step = ComposeStep()
    result = await step.execute(
        {
            "sources": [
                {"step_id": "batch1", "key": "items"},
                {"step_id": "batch2", "key": "items"},
            ],
            "output_key": "all_items",
            "merge_strategy": "array_concat",
        },
        ctx,
    )

    assert result.output["all_items"]["items"] == [
        {"ticker": "AAPL"},
        {"ticker": "MSFT"},
    ]


# ---------------------------------------------------------------------------
# AC-5.3: Source renamed via rename field
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rename() -> None:
    """AC-5.3: Source renamed via rename field."""
    from zorivest_core.pipeline_steps.compose_step import ComposeStep

    ctx = _make_context(
        {
            "metrics": {"summary": {"total_pnl": 1500.0}},
        }
    )

    step = ComposeStep()
    result = await step.execute(
        {
            "sources": [
                {"step_id": "metrics", "key": "summary", "rename": "portfolio"},
            ],
            "output_key": "composed",
            "merge_strategy": "dict_merge",
        },
        ctx,
    )

    # The key should be the rename value, not the original key
    assert "portfolio" in result.output["composed"]
    assert result.output["composed"]["portfolio"] == {"total_pnl": 1500.0}


# ---------------------------------------------------------------------------
# AC-5.4: Non-existent step_id raises KeyError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_step_raises() -> None:
    """AC-5.4: Non-existent step_id raises KeyError."""
    from zorivest_core.pipeline_steps.compose_step import ComposeStep

    ctx = _make_context({"existing": {"data": [1, 2, 3]}})

    step = ComposeStep()
    with pytest.raises(KeyError, match="nonexistent"):
        await step.execute(
            {
                "sources": [
                    {"step_id": "nonexistent", "key": "data"},
                ],
                "output_key": "composed",
            },
            ctx,
        )


# ---------------------------------------------------------------------------
# AC-5.5: Deep-copy isolation from source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deep_copy_isolation() -> None:
    """AC-5.5: Composed output is isolated from source — mutation doesn't leak."""
    from zorivest_core.pipeline_steps.compose_step import ComposeStep

    original_data = {"prices": [150.0, 300.0]}
    ctx = _make_context({"quotes": {"results": original_data}})

    step = ComposeStep()
    result = await step.execute(
        {
            "sources": [
                {"step_id": "quotes", "key": "results", "rename": "data"},
            ],
            "output_key": "composed",
        },
        ctx,
    )

    # Mutate the composed output
    result.output["composed"]["data"]["prices"].append(999.0)

    # Original context data should be unaffected
    source_data = ctx.get_output("quotes")
    assert 999.0 not in source_data["results"]["prices"]
