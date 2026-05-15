# packages/core/src/zorivest_core/domain/tax/replacement_suggestions.py
"""Pure domain function for tax-smart replacement suggestions.

MEU-139: Implements ACs 139.1–139.7.
- ReplacementSuggestion frozen dataclass.
- REPLACEMENT_TABLE: static dict with common ETF substitution pairs.
- suggest_replacements(ticker) — lookup correlated non-identical alternatives.
- suggest_replacements_for_harvest(candidate) — convenience wrapper.

Spec: domain-model-reference.md C3 ("correlated but NOT substantially identical").

Human-approved: ETF pair families and category taxonomy approved by user
(execution-session invocation, conversation 606fc053).
"""

from __future__ import annotations

from dataclasses import dataclass

from zorivest_core.domain.tax.harvest_scanner import HarvestCandidate


@dataclass(frozen=True)
class ReplacementSuggestion:
    """A tax-smart replacement security suggestion.

    AC-139.2: Frozen dataclass with 4 fields.
    """

    ticker: str
    name: str
    category: str
    correlation_note: str


# ── AC-139.3: Static replacement table ───────────────────────────────
# Human-approved: pair families and categories
# (execution-session invocation, conversation 606fc053).


def _s(ticker: str, name: str, category: str, note: str) -> ReplacementSuggestion:
    """Shorthand factory for table construction."""
    return ReplacementSuggestion(
        ticker=ticker, name=name, category=category, correlation_note=note
    )


# Master table: maps each ticker to its correlated replacements.
# AC-139.4: Bidirectional — if VOO→IVV then IVV→VOO.
# AC-139.5: Categories from approved taxonomy.
_PAIR_FAMILIES: list[tuple[str, list[tuple[str, str]], str, str]] = [
    # (category, [(ticker, name), ...], correlation_note_template)
    # S&P 500
    (
        "S&P 500",
        [
            ("VOO", "Vanguard S&P 500 ETF"),
            ("IVV", "iShares Core S&P 500 ETF"),
            ("SPLG", "SPDR Portfolio S&P 500 ETF"),
            ("SPY", "SPDR S&P 500 ETF Trust"),
        ],
        "Tracks the S&P 500 index",
        "Same underlying index (S&P 500)",
    ),
    # US Total Market
    (
        "US Total Market",
        [
            ("VTI", "Vanguard Total Stock Market ETF"),
            ("ITOT", "iShares Core S&P Total U.S. Stock Market ETF"),
            ("SPTM", "SPDR Portfolio S&P 1500 Composite Stock Market ETF"),
            ("SCHB", "Schwab U.S. Broad Market ETF"),
        ],
        "Tracks broad US equity market",
        "Similar broad US market exposure",
    ),
    # International Developed
    (
        "International Developed",
        [
            ("VXUS", "Vanguard Total International Stock ETF"),
            ("IXUS", "iShares Core MSCI Total International Stock ETF"),
            ("VEA", "Vanguard FTSE Developed Markets ETF"),
            ("IEFA", "iShares Core MSCI EAFE ETF"),
            ("SCHF", "Schwab International Equity ETF"),
        ],
        "Tracks developed international markets",
        "Similar international developed exposure",
    ),
    # Emerging Markets
    (
        "Emerging Markets",
        [
            ("VWO", "Vanguard FTSE Emerging Markets ETF"),
            ("IEMG", "iShares Core MSCI Emerging Markets ETF"),
            ("SCHE", "Schwab Emerging Markets Equity ETF"),
            ("SPEM", "SPDR Portfolio Emerging Markets ETF"),
        ],
        "Tracks emerging market equities",
        "Similar emerging market exposure",
    ),
    # US Bonds
    (
        "US Bonds",
        [
            ("BND", "Vanguard Total Bond Market ETF"),
            ("AGG", "iShares Core U.S. Aggregate Bond ETF"),
            ("SCHZ", "Schwab U.S. Aggregate Bond ETF"),
            ("SPAB", "SPDR Portfolio Aggregate Bond ETF"),
        ],
        "Tracks US aggregate bond market",
        "Similar US bond market exposure",
    ),
    # US Small Cap
    (
        "US Small Cap",
        [
            ("VB", "Vanguard Small-Cap ETF"),
            ("IJR", "iShares Core S&P Small-Cap ETF"),
            ("SCHA", "Schwab U.S. Small-Cap ETF"),
            ("SPSM", "SPDR Portfolio S&P 600 Small Cap ETF"),
        ],
        "Tracks US small-cap equities",
        "Similar US small-cap exposure",
    ),
    # US Mid Cap
    (
        "US Mid Cap",
        [
            ("VO", "Vanguard Mid-Cap ETF"),
            ("IJH", "iShares Core S&P Mid-Cap ETF"),
            ("SCHM", "Schwab U.S. Mid-Cap ETF"),
            ("SPMD", "SPDR Portfolio S&P 400 Mid Cap ETF"),
        ],
        "Tracks US mid-cap equities",
        "Similar US mid-cap exposure",
    ),
    # US Large Cap (different from S&P 500 — total large cap)
    (
        "US Large Cap",
        [
            ("VV", "Vanguard Large-Cap ETF"),
            ("SCHX", "Schwab U.S. Large-Cap ETF"),
            ("SPLG", "SPDR Portfolio S&P 500 ETF"),
        ],
        "Tracks US large-cap equities",
        "Similar US large-cap exposure",
    ),
    # Growth
    (
        "Growth",
        [
            ("VUG", "Vanguard Growth ETF"),
            ("IWF", "iShares Russell 1000 Growth ETF"),
            ("SCHG", "Schwab U.S. Large-Cap Growth ETF"),
            ("SPYG", "SPDR Portfolio S&P 500 Growth ETF"),
        ],
        "Tracks US large-cap growth equities",
        "Similar growth exposure",
    ),
    # Value
    (
        "Value",
        [
            ("VTV", "Vanguard Value ETF"),
            ("IWD", "iShares Russell 1000 Value ETF"),
            ("SCHV", "Schwab U.S. Large-Cap Value ETF"),
            ("SPYV", "SPDR Portfolio S&P 500 Value ETF"),
        ],
        "Tracks US large-cap value equities",
        "Similar value exposure",
    ),
]


def _build_replacement_table() -> dict[str, list[ReplacementSuggestion]]:
    """Build the bidirectional replacement table from pair families."""
    table: dict[str, list[ReplacementSuggestion]] = {}

    for category, members, _desc, note in _PAIR_FAMILIES:
        for i, (ticker, _name) in enumerate(members):
            replacements: list[ReplacementSuggestion] = []
            for j, (other_ticker, other_name) in enumerate(members):
                if i == j:
                    continue  # Don't suggest self
                replacements.append(
                    ReplacementSuggestion(
                        ticker=other_ticker,
                        name=other_name,
                        category=category,
                        correlation_note=note,
                    )
                )
            if ticker in table:
                # Ticker appears in multiple categories — merge suggestions
                existing_tickers = {s.ticker for s in table[ticker]}
                for r in replacements:
                    if r.ticker not in existing_tickers:
                        table[ticker].append(r)
                        existing_tickers.add(r.ticker)
            else:
                table[ticker] = replacements

    return table


REPLACEMENT_TABLE: dict[str, list[ReplacementSuggestion]] = _build_replacement_table()


def suggest_replacements(ticker: str) -> list[ReplacementSuggestion]:
    """Return correlated, non-substantially-identical replacement suggestions.

    AC-139.1: Returns list of ReplacementSuggestion for known tickers.
    AC-139.4: Bidirectional — VOO→IVV and IVV→VOO.
    AC-139.7: Pure function — no API calls.

    Args:
        ticker: Ticker symbol to find replacements for.

    Returns:
        List of ReplacementSuggestion. Empty list if ticker is unknown.
    """
    return REPLACEMENT_TABLE.get(ticker, [])


def suggest_replacements_for_harvest(
    candidate: HarvestCandidate,
) -> list[ReplacementSuggestion]:
    """Convenience wrapper: suggest replacements for a harvest candidate.

    AC-139.6: Works for both blocked and unblocked candidates.

    Args:
        candidate: HarvestCandidate from scan_harvest_candidates.

    Returns:
        List of ReplacementSuggestion for the candidate's ticker.
    """
    return suggest_replacements(candidate.ticker)
