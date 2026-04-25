# tests/integration/test_pipeline_dataflow.py
"""MEU-PW13: Pipeline dataflow integration tests.

Tests the full Fetch→Transform→Send chain, verifying that market data
traverses the entire pipeline and produces usable output. Uses mocked HTTP
but real MarketDataProviderAdapter, real field mappings, real Pandera validation,
and real response extractors.

AC-E2E-1: Full Fetch→Transform→Send chain with mocked HTTP
AC-E2E-2: Rendered email body contains actual ticker data
AC-E2E-3: FetchStep upserts to cache after successful fetch
AC-E2E-4: TransformStep correctly unwraps Yahoo-format envelope
AC-E2E-5: Field mapping produces template-compatible output
AC-E2E-6: Zero-record scenario returns WARNING status
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

# Realistic Yahoo Finance quote API response envelope
YAHOO_QUOTE_RESPONSE: dict[str, Any] = {
    "quoteResponse": {
        "result": [
            {
                "symbol": "AAPL",
                "regularMarketPrice": 178.72,
                "regularMarketVolume": 50431000,
                "regularMarketChange": 2.15,
                "regularMarketChangePercent": 1.22,
                "regularMarketBid": 178.70,
                "regularMarketAsk": 178.75,
            },
            {
                "symbol": "MSFT",
                "regularMarketPrice": 415.20,
                "regularMarketVolume": 22189000,
                "regularMarketChange": -1.30,
                "regularMarketChangePercent": -0.31,
                "regularMarketBid": 415.18,
                "regularMarketAsk": 415.22,
            },
        ],
        "error": None,
    }
}

# Empty Yahoo response (no quotes)
YAHOO_EMPTY_RESPONSE: dict[str, Any] = {
    "quoteResponse": {
        "result": [],
        "error": None,
    }
}


def _make_adapter(response_content: bytes) -> Any:
    """Create a real MarketDataProviderAdapter with mocked HTTP client."""
    from zorivest_infra.market_data.market_data_adapter import (
        MarketDataProviderAdapter,
    )

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = response_content
    mock_response.headers = {"ETag": "test-etag"}
    mock_client.get.return_value = mock_response

    mock_rate_limiter = AsyncMock()

    async def _passthrough(provider: str, func: Any, *a: Any, **kw: Any) -> Any:
        return await func(*a, **kw)

    mock_rate_limiter.execute_with_limits = AsyncMock(side_effect=_passthrough)

    return MarketDataProviderAdapter(
        http_client=mock_client,
        rate_limiter=mock_rate_limiter,
    )


# ---------------------------------------------------------------------------
# AC-E2E-1 / AC-E2E-2: Full chain integration
# ---------------------------------------------------------------------------


class TestFullPipelineChain:
    """Integration tests for the Fetch→Transform→Send dataflow chain."""

    @pytest.mark.asyncio
    async def test_fetch_transform_send_happy_path(self) -> None:
        """Full chain: Yahoo quote fetch → transform → send produces email with ticker data.

        Verifies AC-E2E-1 (full chain) and AC-E2E-2 (real ticker data in output).
        """
        from zorivest_core.pipeline_steps.fetch_step import FetchStep
        from zorivest_core.pipeline_steps.send_step import SendStep
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        # Arrange: build pipeline context with real adapter
        adapter = _make_adapter(json.dumps(YAHOO_QUOTE_RESPONSE).encode())
        mock_db_writer = MagicMock()
        mock_db_writer.write.return_value = 2

        mock_delivery_repo = MagicMock()
        mock_delivery_repo.create.return_value = "delivery-123"
        mock_smtp = MagicMock()

        from zorivest_core.domain.approval_snapshot import ApprovalSnapshot

        context = StepContext(
            run_id="run-dataflow-1",
            policy_id="pol-dataflow-1",
            outputs={
                "provider_adapter": adapter,
                "db_writer": mock_db_writer,
                "delivery_repository": mock_delivery_repo,
                "smtp_config": mock_smtp,
            },
            approval_snapshot=ApprovalSnapshot(
                approved=True,
                approved_hash="test-hash",
                approved_at=None,
            ),
            policy_hash="test-hash",
        )

        # Step 1: Fetch
        fetch_step = FetchStep()
        fetch_result = await fetch_step.execute(
            params={
                "provider": "Yahoo Finance",
                "data_type": "quote",
                "criteria": {"symbols": ["AAPL", "MSFT"]},
                "use_cache": False,
            },
            context=context,
        )
        assert fetch_result.status == PipelineStatus.SUCCESS, (
            f"FetchStep failed: {fetch_result.error}"
        )
        # Store fetch output in context (PipelineRunner would do this)
        context.outputs["fetch_quotes"] = fetch_result.output

        # Step 2: Transform
        transform_step = TransformStep()
        transform_result = await transform_step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "validation_rules": "quote",
            },
            context=context,
        )
        assert transform_result.status == PipelineStatus.SUCCESS, (
            f"TransformStep failed: {transform_result.error}"
        )
        context.outputs["transform_quotes"] = transform_result.output

        # Verify transformed records have template-compatible fields (AC-E2E-5)
        quotes = transform_result.output["quotes"]
        assert len(quotes) >= 2, f"Expected ≥2 quotes, got {len(quotes)}"
        first_quote = quotes[0]
        # Verify key template fields are present (presentation-mapped names)
        for field in ("price", "volume"):
            assert field in first_quote, (
                f"Missing field '{field}' in quote: {first_quote}"
            )

        # Step 3: Send (email channel — full execute() path)
        send_step = SendStep()

        # Provide Jinja2 engine for Tier 2 template rendering
        from jinja2 import BaseLoader, Environment

        engine = Environment(loader=BaseLoader(), autoescape=True)
        context.outputs["template_engine"] = engine

        # smtp_config must be a dict for .get() calls inside _send_emails
        context.outputs["smtp_config"] = {
            "host": "localhost",
            "port": 587,
            "sender": "test@zorivest.local",
        }

        # delivery_repo: dedup check returns None (no prior delivery)
        mock_delivery_repo.get_by_dedup_key.return_value = None
        context.outputs["delivery_repository"] = mock_delivery_repo

        # Register a test template in EMAIL_TEMPLATES so Tier 2 kicks in
        test_template_source = (
            "<h1>Market Summary</h1>"
            "{% for q in quotes %}"
            "<p>{{ q.symbol }}: {{ q.price }} vol={{ q.volume }}</p>"
            "{% endfor %}"
        )

        # Mock send_report_email to capture the rendered html_body
        mock_send = AsyncMock(return_value=(True, "sent"))
        with (
            patch(
                "zorivest_infra.rendering.email_templates.EMAIL_TEMPLATES",
                {"test_market_report": test_template_source},
            ),
            patch(
                "zorivest_infra.email.email_sender.send_report_email",
                mock_send,
            ),
        ):
            send_result = await send_step.execute(
                params={
                    "channel": "email",
                    "recipients": ["report@example.com"],
                    "subject": "Daily Market Summary",
                    "body_template": "test_market_report",
                },
                context=context,
            )

        # AC-E2E-1: Full chain completed successfully
        assert send_result.status == PipelineStatus.SUCCESS, (
            f"SendStep failed: {send_result.error}"
        )
        assert send_result.output["sent"] == 1, (
            f"Expected 1 sent, got: {send_result.output}"
        )

        # AC-E2E-2: Rendered HTML body contains actual ticker data
        mock_send.assert_called_once()
        rendered_body = mock_send.call_args.kwargs["html_body"]
        assert "Market Summary" in rendered_body
        assert "178.72" in rendered_body, (
            f"Expected AAPL price 178.72 in rendered body, got: {rendered_body[:200]}"
        )
        assert "415.2" in rendered_body, (
            f"Expected MSFT price in rendered body, got: {rendered_body[:200]}"
        )

    @pytest.mark.asyncio
    async def test_fetch_transform_records_count(self) -> None:
        """Transform step produces correct record count from Yahoo envelope."""
        from zorivest_core.pipeline_steps.fetch_step import FetchStep
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        adapter = _make_adapter(json.dumps(YAHOO_QUOTE_RESPONSE).encode())
        mock_db_writer = MagicMock()
        mock_db_writer.write.return_value = 2

        context = StepContext(
            run_id="run-dataflow-2",
            policy_id="pol-dataflow-2",
            outputs={
                "provider_adapter": adapter,
                "db_writer": mock_db_writer,
            },
        )

        # Fetch
        fetch_step = FetchStep()
        fetch_result = await fetch_step.execute(
            params={
                "provider": "Yahoo Finance",
                "data_type": "quote",
                "criteria": {"symbols": ["AAPL", "MSFT"]},
                "use_cache": False,
            },
            context=context,
        )
        assert fetch_result.status == PipelineStatus.SUCCESS
        context.outputs["fetch_quotes"] = fetch_result.output

        # Transform — verify record extraction and validation
        transform_step = TransformStep()
        transform_result = await transform_step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "validation_rules": "quote",
            },
            context=context,
        )

        assert transform_result.status == PipelineStatus.SUCCESS, (
            f"TransformStep failed: {transform_result.error}"
        )
        assert transform_result.output["records_written"] == 2
        assert len(transform_result.output["quotes"]) == 2


# ---------------------------------------------------------------------------
# AC-E2E-3: Cache upsert verification
# ---------------------------------------------------------------------------


class TestFetchCacheIntegration:
    """Verify FetchStep cache behavior with real adapter."""

    @pytest.mark.asyncio
    async def test_cache_upsert_called_after_fetch(self) -> None:
        """FetchStep upserts to cache repo after successful fetch."""
        adapter = _make_adapter(json.dumps(YAHOO_QUOTE_RESPONSE).encode())
        mock_cache_repo = MagicMock()

        context = StepContext(
            run_id="run-cache-1",
            policy_id="pol-cache-1",
            outputs={
                "provider_adapter": adapter,
                "fetch_cache_repo": mock_cache_repo,
            },
        )

        from zorivest_core.pipeline_steps.fetch_step import FetchStep

        step = FetchStep()
        result = await step.execute(
            params={
                "provider": "Yahoo Finance",
                "data_type": "quote",
                "criteria": {"symbols": ["AAPL"]},
                "use_cache": False,
            },
            context=context,
        )

        assert result.status == PipelineStatus.SUCCESS
        mock_cache_repo.upsert.assert_called_once()

        # Verify upsert was called with correct provider/data_type
        call_kwargs = mock_cache_repo.upsert.call_args
        assert call_kwargs.kwargs["provider"] == "Yahoo Finance"
        assert call_kwargs.kwargs["data_type"] == "quote"


# ---------------------------------------------------------------------------
# AC-E2E-4: Response extractor envelope unwrapping
# ---------------------------------------------------------------------------


class TestEnvelopeUnwrapping:
    """Verify Yahoo envelope is correctly unwrapped through the chain."""

    @pytest.mark.asyncio
    async def test_yahoo_quote_envelope_extracted(self) -> None:
        """TransformStep correctly extracts records from Yahoo quoteResponse envelope."""
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        mock_db_writer = MagicMock()
        mock_db_writer.write.return_value = 2

        context = StepContext(
            run_id="run-extract-1",
            policy_id="pol-extract-1",
            outputs={
                "db_writer": mock_db_writer,
                "fetch_quotes": {
                    "content": json.dumps(YAHOO_QUOTE_RESPONSE).encode(),
                    "provider": "Yahoo Finance",
                    "data_type": "quote",
                },
            },
        )

        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "validation_rules": "quote",
            },
            context=context,
        )

        assert result.status == PipelineStatus.SUCCESS, (
            f"Extraction failed: {result.error}"
        )
        quotes = result.output["quotes"]
        assert len(quotes) == 2
        # Verify the extracted data retains meaningful values
        # Presentation mapping renames last→price
        prices = [q.get("price") for q in quotes]
        assert any(p is not None and p > 0 for p in prices), (
            f"No valid prices in extracted quotes: {quotes}"
        )


# ---------------------------------------------------------------------------
# AC-E2E-5: Field mapping produces template-compatible output
# ---------------------------------------------------------------------------


class TestFieldMappingIntegration:
    """Verify field mapping normalizes Yahoo fields to canonical names."""

    @pytest.mark.asyncio
    async def test_yahoo_fields_mapped_to_canonical(self) -> None:
        """Yahoo-specific fields (regularMarketPrice etc.) map to canonical names."""
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        mock_db_writer = MagicMock()
        mock_db_writer.write.return_value = 2

        context = StepContext(
            run_id="run-map-1",
            policy_id="pol-map-1",
            outputs={
                "db_writer": mock_db_writer,
                "fetch_quotes": {
                    "content": json.dumps(YAHOO_QUOTE_RESPONSE).encode(),
                    "provider": "Yahoo Finance",
                    "data_type": "quote",
                },
            },
        )

        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "validation_rules": "quote",
            },
            context=context,
        )

        assert result.status == PipelineStatus.SUCCESS

        # AC-E2E-5: template-compatible canonical field names
        quotes = result.output["quotes"]
        assert len(quotes) >= 1

        first = quotes[0]
        # Presentation mapping renames last→price, ticker→symbol
        template_fields = {"price", "volume"}
        present = template_fields & set(first.keys())
        assert present == template_fields, (
            f"Missing template fields: {template_fields - present}. "
            f"Keys present: {list(first.keys())}"
        )


# ---------------------------------------------------------------------------
# AC-E2E-6: Zero-record scenario returns WARNING
# ---------------------------------------------------------------------------


class TestZeroRecordWarning:
    """Verify zero-record scenario produces WARNING status."""

    @pytest.mark.asyncio
    async def test_empty_response_with_min_records_returns_warning(self) -> None:
        """Empty Yahoo response with min_records=1 → WARNING status."""
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        mock_db_writer = MagicMock()

        context = StepContext(
            run_id="run-zero-1",
            policy_id="pol-zero-1",
            outputs={
                "db_writer": mock_db_writer,
                "fetch_quotes": {
                    "content": json.dumps(YAHOO_EMPTY_RESPONSE).encode(),
                    "provider": "Yahoo Finance",
                    "data_type": "quote",
                },
            },
        )

        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "min_records": 1,
                "validation_rules": "quote",
            },
            context=context,
        )

        # AC-E2E-6: WARNING status (not FAILED, not SUCCESS)
        assert result.status == PipelineStatus.WARNING, (
            f"Expected WARNING for zero records with min_records=1, got {result.status}"
        )
        assert result.output["records_written"] == 0
        assert result.output["quotes"] == []

    @pytest.mark.asyncio
    async def test_empty_response_without_min_records_returns_success(self) -> None:
        """Empty response with min_records=0 (default) → SUCCESS status."""
        from zorivest_core.pipeline_steps.transform_step import TransformStep

        mock_db_writer = MagicMock()

        context = StepContext(
            run_id="run-zero-2",
            policy_id="pol-zero-2",
            outputs={
                "db_writer": mock_db_writer,
                "fetch_quotes": {
                    "content": json.dumps(YAHOO_EMPTY_RESPONSE).encode(),
                    "provider": "Yahoo Finance",
                    "data_type": "quote",
                },
            },
        )

        step = TransformStep()
        result = await step.execute(
            params={
                "target_table": "market_quotes",
                "source_step_id": "fetch_quotes",
                "output_key": "quotes",
                "validation_rules": "quote",
            },
            context=context,
        )

        assert result.status == PipelineStatus.SUCCESS
        assert result.output["quotes"] == []
