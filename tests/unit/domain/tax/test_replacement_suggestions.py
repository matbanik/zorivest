# tests/unit/domain/tax/test_replacement_suggestions.py
"""FIC tests for replacement_suggestions — MEU-139 ACs 139.1–139.7.

Feature Intent Contract:
  ReplacementSuggestion frozen dataclass.
  REPLACEMENT_TABLE: static dict with ≥15 common ETF pairs.
  suggest_replacements(ticker) — returns correlated non-identical alternatives.
  suggest_replacements_for_harvest(candidate) — convenience wrapper.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from zorivest_core.domain.tax.replacement_suggestions import (
    REPLACEMENT_TABLE,
    ReplacementSuggestion,
    suggest_replacements,
    suggest_replacements_for_harvest,
)
from zorivest_core.domain.tax.harvest_scanner import HarvestCandidate
from zorivest_core.domain.tax.lot_matcher import LotDetail


# ── AC-139.2: ReplacementSuggestion frozen ───────────────────────────


class TestReplacementSuggestionFrozen:
    """AC-139.2: ReplacementSuggestion must be a frozen dataclass."""

    def test_frozen(self) -> None:
        s = ReplacementSuggestion(
            ticker="IVV",
            name="iShares Core S&P 500 ETF",
            category="S&P 500",
            correlation_note="Same underlying index (S&P 500)",
        )
        with pytest.raises(FrozenInstanceError):
            s.ticker = "VOO"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        s = ReplacementSuggestion(
            ticker="ITOT",
            name="iShares Core S&P Total U.S. Stock Market ETF",
            category="US Total Market",
            correlation_note="Tracks similar broad US market index",
        )
        assert s.ticker == "ITOT"
        assert s.name != ""
        assert s.category == "US Total Market"
        assert s.correlation_note != ""


# ── AC-139.3: REPLACEMENT_TABLE ──────────────────────────────────────


class TestReplacementTable:
    """AC-139.3: Static table with ≥15 common ETF pairs."""

    def test_table_has_minimum_entries(self) -> None:
        assert len(REPLACEMENT_TABLE) >= 15

    def test_table_values_are_lists(self) -> None:
        for ticker, suggestions in REPLACEMENT_TABLE.items():
            assert isinstance(suggestions, list), f"{ticker} value is not a list"
            assert len(suggestions) > 0, f"{ticker} has no suggestions"
            for s in suggestions:
                assert isinstance(s, ReplacementSuggestion), (
                    f"{ticker} contains non-ReplacementSuggestion: {type(s)}"
                )


# ── AC-139.1: suggest_replacements ───────────────────────────────────


class TestSuggestReplacements:
    """AC-139.1: suggest_replacements returns correlated alternatives."""

    def test_known_ticker_returns_suggestions(self) -> None:
        """VOO → at least one suggestion (e.g., IVV)."""
        results = suggest_replacements("VOO")
        assert len(results) > 0
        tickers = [r.ticker for r in results]
        assert "IVV" in tickers or "SPLG" in tickers

    def test_unknown_ticker_empty(self) -> None:
        """AC-139.1 negative: unknown ticker → empty list."""
        results = suggest_replacements("ZZZZZ")
        assert results == []

    def test_results_are_non_identical(self) -> None:
        """Suggestions should not include the input ticker itself."""
        results = suggest_replacements("VOO")
        tickers = [r.ticker for r in results]
        assert "VOO" not in tickers


# ── AC-139.4: Bidirectional lookup ───────────────────────────────────


class TestBidirectionalLookup:
    """AC-139.4: VOO → IVV AND IVV → VOO."""

    def test_voo_to_ivv(self) -> None:
        results = suggest_replacements("VOO")
        tickers = [r.ticker for r in results]
        assert "IVV" in tickers

    def test_ivv_to_voo(self) -> None:
        results = suggest_replacements("IVV")
        tickers = [r.ticker for r in results]
        assert "VOO" in tickers


# ── AC-139.5: Category taxonomy ──────────────────────────────────────


class TestCategoryTaxonomy:
    """AC-139.5: Recognized categories in the table."""

    EXPECTED_CATEGORIES = {
        "US Total Market",
        "US Large Cap",
        "International Developed",
        "Emerging Markets",
        "US Bonds",
        "US Small Cap",
        "US Mid Cap",
        "S&P 500",
        "Growth",
        "Value",
    }

    def test_categories_present(self) -> None:
        """All expected categories appear in the table."""
        found: set[str] = set()
        for suggestions in REPLACEMENT_TABLE.values():
            for s in suggestions:
                found.add(s.category)
        for cat in self.EXPECTED_CATEGORIES:
            assert cat in found, f"Category '{cat}' not found in table"


# ── AC-139.6: suggest_replacements_for_harvest ───────────────────────


class TestSuggestReplacementsForHarvest:
    """AC-139.6: Convenience wrapper for HarvestCandidate input."""

    def test_returns_suggestions(self) -> None:
        candidate = HarvestCandidate(
            ticker="VOO",
            lots=[
                LotDetail(
                    lot_id="L1",
                    ticker="VOO",
                    quantity=100.0,
                    cost_basis=Decimal("100.00"),
                    unrealized_gain=Decimal("-500"),
                    unrealized_gain_pct=Decimal("-5.00"),
                    holding_period_days=300,
                    days_to_long_term=66,
                    is_long_term=False,
                ),
            ],
            total_harvestable_loss=Decimal("500"),
            wash_sale_blocked=False,
            wash_sale_reason="",
            days_to_clear=0,
        )
        results = suggest_replacements_for_harvest(candidate)
        assert len(results) > 0

    def test_blocked_candidate_still_returns(self) -> None:
        """AC-139.6: Blocked candidate → still returns suggestions."""
        candidate = HarvestCandidate(
            ticker="VTI",
            lots=[],
            total_harvestable_loss=Decimal("1000"),
            wash_sale_blocked=True,
            wash_sale_reason="Recent purchase",
            days_to_clear=15,
        )
        results = suggest_replacements_for_harvest(candidate)
        assert len(results) > 0


# ── AC-139.7: Pure function ─────────────────────────────────────────


class TestPureFunction:
    """AC-139.7: No API calls, no market data lookups. Hardcoded table."""

    def test_deterministic(self) -> None:
        """Same input → same output."""
        r1 = suggest_replacements("VOO")
        r2 = suggest_replacements("VOO")
        assert r1 == r2
