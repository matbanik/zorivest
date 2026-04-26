# tests/unit/test_variable_injection.py
"""FIC Red-phase tests for variable injection (PH7, AC-7.1–AC-7.3).

Spec: 09d-pipeline-step-extensions.md §9D.3c
"""

from __future__ import annotations

import pytest

from zorivest_core.domain.pipeline import StepContext
from zorivest_core.services.ref_resolver import RefResolver


# ---------------------------------------------------------------------------
# AC-7.1: {"var": "threshold"} resolves to variables["threshold"]
# ---------------------------------------------------------------------------


def test_var_ref_resolves() -> None:
    """AC-7.1: {var: name} resolves to the policy-level variable value."""
    resolver = RefResolver()
    ctx = StepContext(run_id="r1", policy_id="p1")
    variables = {"threshold": 0.05}
    params = {"limit": {"var": "threshold"}}
    resolved = resolver.resolve(params, ctx, variables=variables)
    assert resolved["limit"] == 0.05


# ---------------------------------------------------------------------------
# AC-7.2: Undefined variable raises ValueError
# ---------------------------------------------------------------------------


def test_undefined_var_raises() -> None:
    """AC-7.2: Referencing an undefined variable raises ValueError."""
    resolver = RefResolver()
    ctx = StepContext(run_id="r1", policy_id="p1")
    variables = {"threshold": 0.05}
    params = {"limit": {"var": "missing_var"}}
    with pytest.raises(ValueError, match="Undefined variable"):
        resolver.resolve(params, ctx, variables=variables)


# ---------------------------------------------------------------------------
# AC-7.3: Variable reference in QueryStep binds resolves correctly
# ---------------------------------------------------------------------------


def test_var_in_nested_binds() -> None:
    """AC-7.3: Variable refs in nested query binds resolve correctly."""
    resolver = RefResolver()
    ctx = StepContext(run_id="r1", policy_id="p1")
    variables = {"watchlist_name": "Morning Watch", "limit": 50}
    params = {
        "queries": [
            {
                "name": "tickers",
                "sql": "SELECT ticker FROM watchlist_items WHERE name = :wl",
                "binds": {
                    "wl": {"var": "watchlist_name"},
                    "max_rows": {"var": "limit"},
                },
            }
        ]
    }
    resolved = resolver.resolve(params, ctx, variables=variables)
    assert resolved["queries"][0]["binds"]["wl"] == "Morning Watch"
    assert resolved["queries"][0]["binds"]["max_rows"] == 50


# ---------------------------------------------------------------------------
# AC-7.3b: Variables flow through StepContext (Codex finding #2)
# ---------------------------------------------------------------------------


def test_step_context_carries_variables() -> None:
    """AC-7.3b: StepContext.variables field is populated by PipelineRunner."""
    ctx = StepContext(
        run_id="r1",
        policy_id="p1",
        variables={"threshold": 0.05, "limit": 100},
    )
    assert ctx.variables == {"threshold": 0.05, "limit": 100}


def test_step_context_variables_defaults_empty() -> None:
    """AC-7.3c: StepContext.variables defaults to empty dict if not provided."""
    ctx = StepContext(run_id="r1", policy_id="p1")
    assert ctx.variables == {}


@pytest.mark.asyncio
async def test_query_step_resolves_var_from_context_variables() -> None:
    """AC-7.3d: QueryStep uses context.variables for {var} bind resolution.

    Regression: Codex finding #2 — QueryStep's internal RefResolver.resolve()
    was called without variables, causing ValueError on {var} references.
    """
    from zorivest_core.pipeline_steps.query_step import QueryStep

    step = QueryStep()

    # Create a context with variables AND a mock sql_sandbox
    class _MockSandbox:
        def execute(self, sql: str, binds: dict) -> list[dict]:
            # Verify the bind was resolved to the actual variable value
            assert binds["row_limit"] == 100, f"Expected 100, got {binds['row_limit']}"
            return [{"id": 1}]

    ctx = StepContext(
        run_id="r1",
        policy_id="p1",
        variables={"limit": 100},
    )
    ctx.outputs["sql_sandbox"] = _MockSandbox()

    params = {
        "queries": [
            {
                "name": "test_q",
                "sql": "SELECT * FROM trades LIMIT :row_limit",
                "binds": {"row_limit": {"var": "limit"}},
            }
        ],
        "output_key": "results",
    }

    result = await step.execute(params, ctx)
    assert result.status.value == "success"
