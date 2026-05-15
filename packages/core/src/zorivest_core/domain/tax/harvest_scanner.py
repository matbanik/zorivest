# packages/core/src/zorivest_core/domain/tax/harvest_scanner.py
"""Pure domain function for tax-loss harvesting scan.

MEU-138: Implements ACs 138.1–138.9.
- HarvestCandidate / HarvestScanResult frozen dataclasses.
- scan_harvest_candidates() — scans open lots for harvestable losses,
  filters wash-sale-blocked, ranks by loss magnitude.

Spec: domain-model-reference.md C2 ("tax-loss harvesting scanner").
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.tax.lot_matcher import LotDetail, get_lot_details
from zorivest_core.domain.tax.wash_sale_detector import _is_substantially_identical


@dataclass(frozen=True)
class HarvestCandidate:
    """A position eligible for tax-loss harvesting.

    AC-138.2: ticker, lots, total_harvestable_loss, wash_sale_blocked,
    wash_sale_reason, days_to_clear.
    """

    ticker: str
    lots: list[LotDetail]
    total_harvestable_loss: Decimal
    wash_sale_blocked: bool
    wash_sale_reason: str
    days_to_clear: int


@dataclass(frozen=True)
class HarvestScanResult:
    """Result of a tax-loss harvesting scan.

    AC-138.3: candidates, total_harvestable, total_blocked, skipped_tickers.
    """

    candidates: list[HarvestCandidate]
    total_harvestable: Decimal
    total_blocked: Decimal
    skipped_tickers: list[str]


def scan_harvest_candidates(
    open_lots: list[TaxLot],
    current_prices: dict[str, Decimal],
    tax_profile: TaxProfile,
    all_lots: list[TaxLot],
) -> HarvestScanResult:
    """Scan open lots for tax-loss harvesting opportunities.

    AC-138.1: Main scan function.
    AC-138.4: Only lots with unrealized loss are included.
    AC-138.5: Wash-sale-blocked positions are flagged.
    AC-138.6: Results ranked by total_harvestable_loss descending.
    AC-138.7: days_to_clear = days until 30-day window expires.
    AC-138.8: Respects tax_profile.wash_sale_method.
    AC-138.9: Missing prices → excluded, appended to skipped_tickers.

    Args:
        open_lots: All open tax lots.
        current_prices: Dict of ticker → current market price.
        tax_profile: User's tax configuration.
        all_lots: All lots (open + closed) for wash sale checking.

    Returns:
        HarvestScanResult with ranked candidates.
    """
    # AC-138.9: Separate lots by price availability
    skipped_tickers: list[str] = []
    priced_lots: dict[str, list[TaxLot]] = defaultdict(list)

    seen_tickers: set[str] = set()
    for lot in open_lots:
        seen_tickers.add(lot.ticker)
        if lot.ticker in current_prices:
            priced_lots[lot.ticker].append(lot)

    for ticker in seen_tickers:
        if ticker not in current_prices and ticker not in skipped_tickers:
            skipped_tickers.append(ticker)

    candidates: list[HarvestCandidate] = []
    total_harvestable = Decimal("0")
    total_blocked = Decimal("0")

    for ticker, lots in priced_lots.items():
        price = current_prices[ticker]

        # AC-138.4: Only include lots with unrealized loss
        loss_lots: list[TaxLot] = []
        for lot in lots:
            adjusted_basis = lot.cost_basis + lot.wash_sale_adjustment
            if price < adjusted_basis:
                loss_lots.append(lot)

        if not loss_lots:
            continue

        # Enrich with LotDetail
        lot_details = get_lot_details(loss_lots, price)

        # Total harvestable loss (absolute value of unrealized losses)
        harvestable = sum(
            (abs(d.unrealized_gain) for d in lot_details),
            Decimal("0"),
        )

        # AC-138.5 / AC-138.8: Check for wash sale conflicts
        # Look for recent purchases of substantially identical securities
        # using the shared detector's matching logic (respects wash_sale_method).
        now = datetime.now(tz=timezone.utc)
        wash_blocked = False
        wash_reason = ""
        days_to_clear = 0

        # Check all lots for substantially identical recent purchases
        recent_purchases: list[TaxLot] = []

        for candidate_lot in all_lots:
            # Skip the loss lots themselves — we're looking for replacement purchases
            if candidate_lot.lot_id in {ll.lot_id for ll in loss_lots}:
                continue
            # AC-138.8: Use shared substantially-identical matching
            if not _is_substantially_identical(
                ticker,
                candidate_lot.ticker,
                tax_profile.wash_sale_method,
            ):
                continue
            # Check if purchased within the last 30 days
            days_since_purchase = (now - candidate_lot.open_date).days
            if days_since_purchase <= 30:
                recent_purchases.append(candidate_lot)

        if recent_purchases:
            wash_blocked = True
            # Find the most recent purchase to compute days_to_clear
            most_recent = max(recent_purchases, key=lambda lot: lot.open_date)
            days_since = (now - most_recent.open_date).days
            days_to_clear = max(0, 31 - days_since)  # 30 days + sale day
            wash_reason = (
                f"Recent purchase of substantially identical security for {ticker} "
                f"within 30 days ({len(recent_purchases)} lot(s)). "
                f"Wait {days_to_clear} day(s) to avoid wash sale."
            )

        if wash_blocked:
            total_blocked += harvestable
        else:
            total_harvestable += harvestable

        candidates.append(
            HarvestCandidate(
                ticker=ticker,
                lots=lot_details,
                total_harvestable_loss=harvestable,
                wash_sale_blocked=wash_blocked,
                wash_sale_reason=wash_reason,
                days_to_clear=days_to_clear,
            )
        )

    # AC-138.6: Sort by total_harvestable_loss descending
    candidates.sort(key=lambda c: c.total_harvestable_loss, reverse=True)

    return HarvestScanResult(
        candidates=candidates,
        total_harvestable=total_harvestable,
        total_blocked=total_blocked,
        skipped_tickers=skipped_tickers,
    )
