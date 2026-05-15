# tests/unit/test_tax_audit.py
"""FIC tests for TaxService.run_audit() — MEU-153 ACs 153.1–153.7.

Feature Intent Contract:
  run_audit(account_id=None, tax_year=None) → AuditReport
  Checks: missing basis, duplicate lots, orphaned lots, negative proceeds.

Acceptance Criteria:
  AC-153.1: Accepts optional account_id and tax_year
             Source: Spec: 04f-api-tax.md lines 196-206
  AC-153.2: Returns AuditReport with findings[] and severity_summary
             Source: Spec: StubTaxService.run_audit() return shape
  AC-153.3: Missing basis check (cost_basis == 0 or None → error)
             Source: Spec: 04f-api-tax.md §Transaction audit
  AC-153.4: Duplicate lots (same account+ticker+open_date+quantity → warning)
             Source: Local Canon: lot uniqueness
  AC-153.5: Orphaned lots (closed + no linked_trade_ids → warning)
             Source: Local Canon: lot-trade linking
  AC-153.6: Negative/zero proceeds on closed lots → error
             Source: Local Canon: TaxLot.proceeds field
  AC-153.7: Each finding has: finding_type, severity, message, lot_id, details
             Source: Spec: StubTaxService contract shape

All tests use mocked UoW — no database access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


from zorivest_core.domain.entities import TaxLot
from zorivest_core.services.tax_service import TaxService, AuditFinding, AuditReport


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    account_id: str = "ACC-1",
    cost_basis: Decimal = Decimal("100.00"),
    proceeds: Decimal = Decimal("150.00"),
    quantity: float = 100.0,
    open_date: datetime | None = None,
    close_date: datetime | None = None,
    is_closed: bool = False,
    linked_trade_ids: list[str] | None = None,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=is_closed,
        linked_trade_ids=linked_trade_ids or [],
    )


def _mock_uow(lots: list[TaxLot] | None = None) -> MagicMock:
    """Create a mock UnitOfWork for audit tests."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)
    uow.tax_lots.list_all_filtered.return_value = lots or []
    return uow


# ── AC-153.1: Method signature ──────────────────────────────────────────


class TestAuditSignature:
    """AC-153.1: run_audit accepts optional account_id and tax_year."""

    def test_no_args(self) -> None:
        """AC-153.1: Works with no arguments."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit()
        assert result is not None

    def test_with_account_id(self) -> None:
        """AC-153.1: Accepts account_id."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit(account_id="ACC-1")
        assert result is not None

    def test_with_tax_year(self) -> None:
        """AC-153.1: Accepts tax_year."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit(tax_year=2026)
        assert result is not None


# ── AC-153.2: Return type structure ─────────────────────────────────────


class TestAuditReturnType:
    """AC-153.2: Returns AuditReport with findings[] and severity_summary."""

    def test_returns_audit_report(self) -> None:
        """AC-153.2: Return type is AuditReport."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit()
        assert isinstance(result, AuditReport)

    def test_has_findings_list(self) -> None:
        """AC-153.2: findings is a list."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit()
        assert isinstance(result.findings, list)

    def test_has_severity_summary(self) -> None:
        """AC-153.2: severity_summary has error/warning/info counts."""
        uow = _mock_uow()
        svc = TaxService(uow)
        result = svc.run_audit()
        assert "error" in result.severity_summary
        assert "warning" in result.severity_summary
        assert "info" in result.severity_summary


# ── AC-153.3: Missing basis check ──────────────────────────────────────


class TestAuditMissingBasis:
    """AC-153.3: Lots with cost_basis == 0 → error."""

    def test_zero_basis_flagged(self) -> None:
        """AC-153.3: Zero cost_basis → error finding."""
        lot = _lot(lot_id="L-ZERO", cost_basis=Decimal("0"))
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        errors = [f for f in result.findings if f.finding_type == "missing_basis"]
        assert len(errors) == 1
        assert errors[0].severity == "error"
        assert errors[0].lot_id == "L-ZERO"

    def test_normal_basis_not_flagged(self) -> None:
        """AC-153.3: Normal cost_basis → no error."""
        lot = _lot(lot_id="L-OK", cost_basis=Decimal("100.00"))
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        errors = [f for f in result.findings if f.finding_type == "missing_basis"]
        assert len(errors) == 0


# ── AC-153.4: Duplicate lots ───────────────────────────────────────────


class TestAuditDuplicateLots:
    """AC-153.4: Duplicate lots → warning."""

    def test_duplicate_detected(self) -> None:
        """AC-153.4: Same account+ticker+open_date+quantity → warning."""
        open_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        lot1 = _lot(
            lot_id="L1",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=open_dt,
            quantity=100.0,
        )
        lot2 = _lot(
            lot_id="L2",
            account_id="ACC-1",
            ticker="AAPL",
            open_date=open_dt,
            quantity=100.0,
        )
        uow = _mock_uow(lots=[lot1, lot2])
        svc = TaxService(uow)
        result = svc.run_audit()

        dupes = [f for f in result.findings if f.finding_type == "duplicate_lot"]
        assert len(dupes) >= 1
        assert dupes[0].severity == "warning"

    def test_different_lots_not_flagged(self) -> None:
        """AC-153.4: Different quantities → not duplicates."""
        open_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        lot1 = _lot(lot_id="L1", open_date=open_dt, quantity=100.0)
        lot2 = _lot(lot_id="L2", open_date=open_dt, quantity=200.0)
        uow = _mock_uow(lots=[lot1, lot2])
        svc = TaxService(uow)
        result = svc.run_audit()

        dupes = [f for f in result.findings if f.finding_type == "duplicate_lot"]
        assert len(dupes) == 0


# ── AC-153.5: Orphaned lots ───────────────────────────────────────────


class TestAuditOrphanedLots:
    """AC-153.5: Closed lots with no linked_trade_ids → warning."""

    def test_orphaned_closed_lot(self) -> None:
        """AC-153.5: Closed lot with no linked trades → warning."""
        lot = _lot(
            lot_id="L-ORPHAN",
            is_closed=True,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            linked_trade_ids=[],
        )
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        orphans = [f for f in result.findings if f.finding_type == "orphaned_lot"]
        assert len(orphans) == 1
        assert orphans[0].severity == "warning"

    def test_linked_lot_not_orphaned(self) -> None:
        """AC-153.5: Closed lot with linked trades → not orphaned."""
        lot = _lot(
            lot_id="L-LINKED",
            is_closed=True,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            linked_trade_ids=["T1"],
        )
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        orphans = [f for f in result.findings if f.finding_type == "orphaned_lot"]
        assert len(orphans) == 0


# ── AC-153.6: Negative/zero proceeds ───────────────────────────────────


class TestAuditNegativeProceeds:
    """AC-153.6: Negative or zero proceeds on closed lots → error."""

    def test_zero_proceeds_flagged(self) -> None:
        """AC-153.6: Zero proceeds on closed lot → error."""
        lot = _lot(
            lot_id="L-ZERO-PROC",
            is_closed=True,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            proceeds=Decimal("0"),
        )
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        errors = [f for f in result.findings if f.finding_type == "invalid_proceeds"]
        assert len(errors) == 1
        assert errors[0].severity == "error"

    def test_negative_proceeds_flagged(self) -> None:
        """AC-153.6: Negative proceeds on closed lot → error."""
        lot = _lot(
            lot_id="L-NEG-PROC",
            is_closed=True,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            proceeds=Decimal("-50.00"),
        )
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        errors = [f for f in result.findings if f.finding_type == "invalid_proceeds"]
        assert len(errors) == 1

    def test_positive_proceeds_not_flagged(self) -> None:
        """AC-153.6: Positive proceeds → no error."""
        lot = _lot(
            lot_id="L-OK",
            is_closed=True,
            close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            proceeds=Decimal("150.00"),
        )
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        errors = [f for f in result.findings if f.finding_type == "invalid_proceeds"]
        assert len(errors) == 0


# ── AC-153.7: Finding structure ────────────────────────────────────────


class TestAuditFindingStructure:
    """AC-153.7: Each finding has required fields."""

    def test_finding_fields(self) -> None:
        """AC-153.7: AuditFinding has all required attributes."""
        lot = _lot(lot_id="L-ZERO", cost_basis=Decimal("0"))
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert isinstance(finding, AuditFinding)
        assert hasattr(finding, "finding_type")
        assert hasattr(finding, "severity")
        assert hasattr(finding, "message")
        assert hasattr(finding, "lot_id")
        assert hasattr(finding, "details")

    def test_severity_summary_counts(self) -> None:
        """AC-153.7: severity_summary counts match findings."""
        lot = _lot(lot_id="L-ZERO", cost_basis=Decimal("0"))
        uow = _mock_uow(lots=[lot])
        svc = TaxService(uow)
        result = svc.run_audit()

        total_findings = len(result.findings)
        total_summary = sum(result.severity_summary.values())
        assert total_findings == total_summary
