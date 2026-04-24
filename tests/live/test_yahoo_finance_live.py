# tests/live/test_yahoo_finance_live.py
"""Live data validation for Yahoo Finance provider.

Run with: pytest tests/live/test_yahoo_finance_live.py --run-live -v

These tests make REAL HTTP calls to Yahoo Finance endpoints.
They validate:
  1. Endpoint reachability and valid JSON response
  2. Response envelope structure matches extractor expectations
  3. Field mapping produces canonical schema fields
  4. Full pipeline fetch→transform→render chain produces displayable data

This is the canonical pattern for adding live tests for other providers.
Copy this file and adapt the endpoint/extractor/mapping details.
"""

from __future__ import annotations

import json

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YAHOO_BASE_URL = "https://query1.finance.yahoo.com"
YAHOO_QUOTE_SYMBOLS = ["AAPL", "MSFT", "GOOGL"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fetch_v6_quote(
    http_client,
    symbols: list[str],
) -> tuple[int, bytes]:
    """Make a real HTTP call to Yahoo Finance v6 quote endpoint (deprecated).

    Returns (status_code, content_bytes).
    """
    symbols_str = ",".join(symbols)
    url = f"{YAHOO_BASE_URL}/v6/finance/quote?symbols={symbols_str}"

    response = await http_client.get(
        url,
        headers={
            "Referer": "https://finance.yahoo.com/",
        },
    )
    return response.status_code, response.content


async def _fetch_v8_chart(
    http_client,
    symbol: str,
) -> tuple[int, bytes]:
    """Make a real HTTP call to Yahoo Finance v8/chart endpoint.

    This is the current working endpoint for quote data.
    Returns (status_code, content_bytes).
    """
    url = f"{YAHOO_BASE_URL}/v8/finance/chart/{symbol}?range=1d&interval=1d"

    response = await http_client.get(
        url,
        headers={
            "Referer": "https://finance.yahoo.com/",
        },
    )
    return response.status_code, response.content


# ---------------------------------------------------------------------------
# Tests — v6 Deprecation Canary
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
class TestYahooFinanceV6DeprecationCanary:
    """Canary test documenting that v6/finance/quote is dead (404).

    If Yahoo ever restores v6, this test will fail, which is a useful signal.
    """

    async def test_v6_endpoint_returns_404(self, http_client):
        """Yahoo v6/finance/quote should return 404 (deprecated)."""
        status, content = await _fetch_v6_quote(http_client, ["AAPL"])

        print(f"\n  Yahoo /v6/finance/quote status: {status}")
        print(f"  Response length: {len(content)} bytes")
        if content:
            preview = content[:200].decode("utf-8", errors="replace")
            print(f"  Response preview: {preview}")

        # Document the current state — v6 returns 404
        assert status == 404, (
            f"v6/finance/quote returned {status} instead of expected 404. "
            "If this test fails, v6 may have been restored — investigate."
        )


# ---------------------------------------------------------------------------
# Tests — v8/chart Endpoint (Current Working Endpoint)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
class TestYahooFinanceV8QuoteEndpoint:
    """Validate Yahoo Finance v8/chart endpoint for quote data.

    This is the endpoint Zorivest now uses after v6 deprecation.
    """

    async def test_endpoint_returns_200(self, http_client):
        """v8/finance/chart must return 200 for a valid symbol."""
        status, content = await _fetch_v8_chart(http_client, "AAPL")

        print(f"\n  Yahoo /v8/finance/chart status: {status}")
        print(f"  Response length: {len(content)} bytes")

        assert status == 200, (
            f"v8/finance/chart returned {status}. "
            f"Preview: {content[:200].decode('utf-8', errors='replace')}"
        )

    async def test_response_is_valid_json(self, http_client):
        """The response must be parseable JSON."""
        status, content = await _fetch_v8_chart(http_client, "AAPL")

        if status != 200:
            pytest.skip(f"Yahoo v8/chart returned {status}")

        data = json.loads(content)
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

    async def test_response_has_chart_envelope(self, http_client):
        """v8/chart response must contain chart.result[0].meta envelope."""
        status, content = await _fetch_v8_chart(http_client, "AAPL")

        if status != 200:
            pytest.skip(f"Yahoo v8/chart returned {status}")

        data = json.loads(content)

        assert "chart" in data, f"Missing 'chart' key. Available: {list(data.keys())}"
        chart = data["chart"]
        assert isinstance(chart, dict)

        result = chart.get("result", [])
        assert isinstance(result, list) and len(result) >= 1, (
            f"Expected non-empty chart.result list, got {result}"
        )

        meta = result[0].get("meta", {})
        assert isinstance(meta, dict) and meta, (
            f"Expected non-empty meta dict, got {meta}"
        )

        # Log key fields
        print(f"\n  Symbol: {meta.get('symbol')}")
        print(f"  Price: {meta.get('regularMarketPrice')}")
        print(f"  Currency: {meta.get('currency')}")

    async def test_extractor_returns_records(self, http_client):
        """Zorivest's response extractor must extract records from v8/chart."""
        status, content = await _fetch_v8_chart(http_client, "AAPL")

        if status != 200:
            pytest.skip(f"Yahoo v8/chart returned {status}")

        from zorivest_infra.market_data.response_extractors import (
            extract_records,
        )

        records = extract_records(content, "Yahoo Finance", "quote")

        assert isinstance(records, list), f"Expected list, got {type(records)}"
        print(f"\n  Extracted {len(records)} records from v8/chart response")

        if records:
            print(f"  Fields: {list(records[0].keys())}")
            for r in records:
                sym = r.get("symbol", "?")
                price = r.get("regularMarketPrice", "?")
                print(f"    {sym}: ${price}")

        assert len(records) >= 1, (
            "Expected at least 1 record from v8/chart. "
            "The response extractor may not handle the v8 envelope."
        )

    async def test_field_mapping_produces_canonical_fields(self, http_client):
        """Field mapping must transform v8/chart meta fields to canonical schema."""
        status, content = await _fetch_v8_chart(http_client, "AAPL")

        if status != 200:
            pytest.skip(f"Yahoo v8/chart returned {status}")

        from zorivest_infra.market_data.field_mappings import (
            apply_field_mapping,
        )
        from zorivest_infra.market_data.response_extractors import (
            extract_records,
        )

        records = extract_records(content, "Yahoo Finance", "quote")
        if not records:
            pytest.skip("No records extracted — cannot test mapping")

        mapped = apply_field_mapping(
            record=records[0],
            provider="Yahoo Finance",
            data_type="quote",
        )

        print(f"\n  Mapped fields: {list(mapped.keys())}")

        # Check canonical field presence
        # v8/chart meta has regularMarketPrice=last, symbol=ticker
        # but may lack bid/ask (not in chart meta)
        assert "ticker" in mapped, (
            f"Missing 'ticker' canonical field. Mapped: {list(mapped.keys())}"
        )
        assert "last" in mapped, (
            f"Missing 'last' canonical field. Mapped: {list(mapped.keys())}"
        )

    async def test_full_pipeline_chain(self, http_client):
        """Full fetch → extract → map → template chain must produce HTML with data.

        This is the end-to-end validation that the daily quote pipeline
        would produce a meaningful email rather than 'No quote data available'.
        """
        # Fetch for all symbols, accumulating results
        all_records = []
        for sym in YAHOO_QUOTE_SYMBOLS:
            status, content = await _fetch_v8_chart(http_client, sym)
            if status != 200:
                continue

            from zorivest_infra.market_data.response_extractors import (
                extract_records,
            )

            records = extract_records(content, "Yahoo Finance", "quote")
            all_records.extend(records)

        assert len(all_records) >= 1, (
            f"No records extracted for any of {YAHOO_QUOTE_SYMBOLS}"
        )

        from zorivest_infra.market_data.field_mappings import (
            apply_field_mapping,
        )

        # Map to canonical fields
        mapped_records = [
            apply_field_mapping(record=r, provider="Yahoo Finance", data_type="quote")
            for r in all_records
        ]

        # Build presentation-ready dicts
        quotes = []
        for r in mapped_records:
            quotes.append(
                {
                    "symbol": r.get("ticker", "?"),
                    "price": r.get("last", 0),
                    "change": r.get("change", 0),
                    "change_pct": r.get("change_pct", 0),
                    "volume": r.get("volume", 0) or 0,
                }
            )

        # Render template
        from zorivest_infra.rendering.email_templates import EMAIL_TEMPLATES

        try:
            from zorivest_infra.rendering.template_engine import (
                create_template_engine,
            )

            engine = create_template_engine()
        except ImportError:
            from jinja2 import BaseLoader, Environment

            engine = Environment(loader=BaseLoader(), autoescape=True)

        tmpl = engine.from_string(EMAIL_TEMPLATES["daily_quote_summary"])
        html = tmpl.render(
            generated_at="2026-04-21 (LIVE TEST)",
            quotes=quotes,
        )

        print(f"\n  Rendered HTML length: {len(html)} chars")
        assert "No quote data available" not in html, (
            "Template rendered 'No quote data available' despite having data"
        )

        # Verify at least one symbol appears in the rendered HTML
        found_symbols = [s for s in YAHOO_QUOTE_SYMBOLS if s in html]
        assert len(found_symbols) >= 1, (
            f"None of {YAHOO_QUOTE_SYMBOLS} found in rendered HTML"
        )
        print(f"  Symbols in rendered HTML: {found_symbols}")
        print(f"  Quotes data: {quotes[:3]}")


# ---------------------------------------------------------------------------
# Tests — Search Endpoint (Stable Alternative)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
class TestYahooFinanceSearchEndpoint:
    """Validate Yahoo Finance search endpoint (stable, used for health checks)."""

    async def test_search_endpoint_reachable(self, http_client):
        """The v1/finance/search endpoint should be alive (used in provider_registry test_endpoint)."""
        url = f"{YAHOO_BASE_URL}/v1/finance/search?q=AAPL&quotesCount=1&newsCount=0"

        response = await http_client.get(
            url,
            headers={"Referer": "https://finance.yahoo.com/"},
        )

        print(f"\n  Yahoo /v1/finance/search status: {response.status_code}")
        print(f"  Response length: {len(response.content)} bytes")

        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"  Response keys: {list(data.keys())}")
            quotes = data.get("quotes", [])
            print(f"  Matching quotes: {len(quotes)}")
            if quotes:
                print(f"  First match: {quotes[0].get('symbol', '?')}")

        assert response.status_code == 200
