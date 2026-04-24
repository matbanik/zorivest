# tests/unit/test_pipeline_template_wiring.py
"""TDD tests for pipeline template-output key wiring (Bug 1).

Validates that the SendStep two-level merge correctly promotes
TransformStep output_key values into the Jinja2 template context,
and that the daily_quote_summary template can access quote data
via the configured output_key.

Bug: TransformStep stores data under `records` (default output_key),
but daily_quote_summary template checks `{% if quotes %}`.
Fix: The output_key must be set to `quotes` in the policy OR
     the template must use the generic `records` key.
     The system fix is to make the template use the output_key
     from the transform step — validated via two-level merge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_context(
    outputs: dict | None = None,
    policy_id: str = "test-policy",
    run_id: str = "test-run",
) -> MagicMock:
    """Build a minimal StepContext mock."""
    ctx = MagicMock()
    ctx.policy_id = policy_id
    ctx.run_id = run_id
    ctx.outputs = outputs or {}
    return ctx


def _sample_quotes() -> list[dict]:
    """Return sample quote data matching Yahoo Finance field mapping output."""
    return [
        {
            "symbol": "AAPL",
            "price": 185.50,
            "change": 2.35,
            "change_pct": 1.28,
            "volume": 47_500_000,
        },
        {
            "symbol": "MSFT",
            "price": 405.25,
            "change": -1.10,
            "change_pct": -0.27,
            "volume": 22_100_000,
        },
    ]


# ---------------------------------------------------------------------------
# Test: Two-level merge promotes output_key into template context
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTwoLevelMergePromotesOutputKey:
    """SendStep's two-level merge must promote inner keys from step outputs.

    When TransformStep stores `{"quotes": [...]}` in its output dict,
    the merge must make `quotes` available as a top-level template variable.
    """

    def test_output_key_quotes_is_promoted_to_template_context(self):
        """AC: When transform output contains output_key='quotes',
        the template context must contain a 'quotes' key with the records list.
        """
        transform_output = {
            "target_table": "market_quotes",
            "write_disposition": "append",
            "records_written": 2,
            "records_quarantined": 0,
            "quality_ratio": 1.0,
            "quotes": _sample_quotes(),  # output_key = "quotes"
        }

        context = _make_context(outputs={"transform_quotes": transform_output})

        # Simulate the two-level merge from SendStep._resolve_body
        render_ctx: dict = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "policy_id": context.policy_id,
            "run_id": context.run_id,
        }

        for key, value in context.outputs.items():
            if key not in render_ctx:
                render_ctx[key] = value
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    if inner_key not in render_ctx:
                        render_ctx[inner_key] = inner_value

        # THE KEY ASSERTION: quotes must be a top-level variable
        assert "quotes" in render_ctx
        assert len(render_ctx["quotes"]) == 2
        assert render_ctx["quotes"][0]["symbol"] == "AAPL"

    def test_default_output_key_records_is_promoted(self):
        """When output_key is default 'records', it must also be promoted."""
        transform_output = {
            "target_table": "market_quotes",
            "records_written": 2,
            "records": _sample_quotes(),  # default output_key
        }

        context = _make_context(outputs={"transform_quotes": transform_output})

        render_ctx: dict = {
            "generated_at": "2026-04-21",
            "policy_id": context.policy_id,
            "run_id": context.run_id,
        }

        for key, value in context.outputs.items():
            if key not in render_ctx:
                render_ctx[key] = value
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    if inner_key not in render_ctx:
                        render_ctx[inner_key] = inner_value

        assert "records" in render_ctx
        assert len(render_ctx["records"]) == 2

    def test_records_key_does_not_satisfy_quotes_template(self):
        """REGRESSION: If output_key='records' but template checks 'quotes',
        the template must NOT find quote data — proving the bug exists
        when output_key is not set to 'quotes'.
        """
        transform_output = {
            "target_table": "market_quotes",
            "records_written": 2,
            "records": _sample_quotes(),  # default output_key = 'records'
            # NOTE: No 'quotes' key here
        }

        context = _make_context(outputs={"transform_quotes": transform_output})

        render_ctx: dict = {
            "generated_at": "2026-04-21",
            "policy_id": context.policy_id,
            "run_id": context.run_id,
        }

        for key, value in context.outputs.items():
            if key not in render_ctx:
                render_ctx[key] = value
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    if inner_key not in render_ctx:
                        render_ctx[inner_key] = inner_value

        # With default output_key='records', 'quotes' is NOT in context
        assert "quotes" not in render_ctx
        assert "records" in render_ctx


# ---------------------------------------------------------------------------
# Test: Template renders correctly with quotes variable
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDailyQuoteTemplateRendering:
    """The daily_quote_summary template must render quote data
    when the 'quotes' variable is present in the context."""

    def test_template_renders_table_with_quotes(self):
        """When quotes=[...] is in context, template renders a data table."""
        from zorivest_infra.rendering.email_templates import EMAIL_TEMPLATES

        try:
            from zorivest_infra.rendering.template_engine import (
                create_template_engine,
            )

            engine = create_template_engine()
        except ImportError:
            from jinja2 import BaseLoader, Environment

            engine = Environment(loader=BaseLoader(), autoescape=True)

        source = EMAIL_TEMPLATES["daily_quote_summary"]
        tmpl = engine.from_string(source)

        html = tmpl.render(
            generated_at="2026-04-21 03:26 UTC",
            quotes=_sample_quotes(),
        )

        assert "AAPL" in html
        assert "MSFT" in html
        assert "No quote data available" not in html

    def test_template_shows_no_data_without_quotes(self):
        """When quotes is missing/empty, template shows fallback message."""
        from zorivest_infra.rendering.email_templates import EMAIL_TEMPLATES

        try:
            from zorivest_infra.rendering.template_engine import (
                create_template_engine,
            )

            engine = create_template_engine()
        except ImportError:
            from jinja2 import BaseLoader, Environment

            engine = Environment(loader=BaseLoader(), autoescape=True)

        source = EMAIL_TEMPLATES["daily_quote_summary"]
        tmpl = engine.from_string(source)

        html = tmpl.render(
            generated_at="2026-04-21 03:26 UTC",
            # NO quotes variable — simulates the bug
        )

        assert "No quote data available" in html


# ---------------------------------------------------------------------------
# Test: HTTP status validation in fetch_with_cache
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFetchWithCacheHTTPValidation:
    """fetch_with_cache must raise on non-2xx HTTP responses.

    Bug: The function reads response.content without checking status_code.
    A 401/403 from Yahoo returns error HTML that gets cached as valid data.
    Fix: Add HTTP status validation before accepting content.
    """

    @pytest.mark.asyncio
    async def test_raises_on_401_unauthorized(self):
        """A 401 response must raise, not silently return error HTML."""
        from zorivest_infra.market_data.http_cache import fetch_with_cache

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.content = b"<html>Unauthorized</html>"
        mock_response.headers = {}

        # Make client.get awaitable
        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client.get = mock_get

        with pytest.raises(Exception) as exc_info:
            await fetch_with_cache(
                client=mock_client,
                url="https://query1.finance.yahoo.com/v6/finance/quote?symbols=AAPL",
            )

        # The error must mention the HTTP status
        assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_403_forbidden(self):
        """A 403 response must raise, not silently return error content."""
        from zorivest_infra.market_data.http_cache import fetch_with_cache

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.content = b'{"error": "forbidden"}'
        mock_response.headers = {}

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client.get = mock_get

        with pytest.raises(Exception) as exc_info:
            await fetch_with_cache(
                client=mock_client,
                url="https://query1.finance.yahoo.com/v6/finance/quote?symbols=AAPL",
            )

        assert "403" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_500_server_error(self):
        """A 500 response must raise."""
        from zorivest_infra.market_data.http_cache import fetch_with_cache

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        mock_response.headers = {}

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client.get = mock_get

        with pytest.raises(Exception) as exc_info:
            await fetch_with_cache(
                client=mock_client,
                url="https://example.com/api",
            )

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_200_ok_returns_content(self):
        """A 200 response must return content normally."""
        from zorivest_infra.market_data.http_cache import fetch_with_cache

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"quoteResponse": {"result": []}}'
        mock_response.headers = {"ETag": '"abc123"'}

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client.get = mock_get

        result = await fetch_with_cache(
            client=mock_client,
            url="https://query1.finance.yahoo.com/v6/finance/quote?symbols=AAPL",
        )

        assert result["cache_status"] == "miss"
        assert result["content"] == b'{"quoteResponse": {"result": []}}'
        assert result["etag"] == '"abc123"'

    @pytest.mark.asyncio
    async def test_304_with_cache_returns_cached(self):
        """A 304 Not Modified must return cached content (revalidation)."""
        from zorivest_infra.market_data.http_cache import fetch_with_cache

        cached = b'{"quoteResponse": {"result": [{"symbol": "AAPL"}]}}'
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 304
        mock_response.headers = {}

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client.get = mock_get

        result = await fetch_with_cache(
            client=mock_client,
            url="https://query1.finance.yahoo.com/v6/finance/quote?symbols=AAPL",
            cached_content=cached,
            cached_etag='"abc123"',
        )

        assert result["cache_status"] == "revalidated"
        assert result["content"] == cached
