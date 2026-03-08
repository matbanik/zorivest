# tests/unit/test_portfolio_balance.py
"""MEU-9 Red tests: TotalPortfolioBalance + calculate_total_portfolio_balance.

FIC source: implementation-plan.md §MEU-9 (AC-1 through AC-7).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.portfolio_balance import (
    TotalPortfolioBalance,
    calculate_total_portfolio_balance,
)


# ── Helpers ─────────────────────────────────────────────────────────────


def _snapshot(account_id: str, balance: Decimal, dt: datetime) -> BalanceSnapshot:
    """Create a BalanceSnapshot for testing."""
    return BalanceSnapshot(
        id=0,
        account_id=account_id,
        datetime=dt,
        balance=balance,
    )


def _account(
    account_id: str,
    snapshots: list[BalanceSnapshot] | None = None,
    account_type: AccountType = AccountType.BROKER,
) -> Account:
    """Create an Account for testing."""
    acct = Account(
        account_id=account_id,
        name=f"Test {account_id}",
        account_type=account_type,
    )
    if snapshots:
        acct.balance_snapshots.extend(snapshots)
    return acct


# ── AC-1: TotalPortfolioBalance dataclass ───────────────────────────────


@pytest.mark.unit
class TestTotalPortfolioBalanceDataclass:
    """AC-1: TotalPortfolioBalance frozen dataclass."""

    def test_fields_exist(self) -> None:
        result = TotalPortfolioBalance(
            total=Decimal("1000"),
            per_account={"acct1": Decimal("1000")},
            computed_at=datetime(2026, 1, 1),
        )
        assert result.total == Decimal("1000")
        assert result.per_account == {"acct1": Decimal("1000")}
        assert result.computed_at == datetime(2026, 1, 1)

    def test_frozen(self) -> None:
        result = TotalPortfolioBalance(
            total=Decimal("0"),
            per_account={},
            computed_at=datetime(2026, 1, 1),
        )
        with pytest.raises(AttributeError):
            result.total = Decimal("999")  # type: ignore[misc]


# ── AC-2: Basic calculation ─────────────────────────────────────────────


@pytest.mark.unit
class TestCalculateBasic:
    """AC-2: Sums latest BalanceSnapshot.balance per account."""

    def test_single_account_single_snapshot(self) -> None:
        acct = _account("a1", [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))])
        result = calculate_total_portfolio_balance([acct])
        assert result.total == Decimal("5000")
        assert result.per_account == {"a1": Decimal("5000")}

    def test_multiple_accounts(self) -> None:
        acct1 = _account("a1", [_snapshot("a1", Decimal("3000"), datetime(2026, 1, 1))])
        acct2 = _account("a2", [_snapshot("a2", Decimal("7000"), datetime(2026, 1, 1))])
        result = calculate_total_portfolio_balance([acct1, acct2])
        assert result.total == Decimal("10000")
        assert result.per_account == {
            "a1": Decimal("3000"),
            "a2": Decimal("7000"),
        }


# ── AC-3: Empty snapshots → zero contribution ──────────────────────────


@pytest.mark.unit
class TestEmptySnapshots:
    """AC-3: Accounts with no snapshots contribute Decimal('0')."""

    def test_account_with_no_snapshots(self) -> None:
        acct = _account("a1")
        result = calculate_total_portfolio_balance([acct])
        assert result.total == Decimal("0")
        assert result.per_account == {"a1": Decimal("0")}

    def test_mixed_with_and_without_snapshots(self) -> None:
        acct1 = _account("a1", [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))])
        acct2 = _account("a2")  # no snapshots
        result = calculate_total_portfolio_balance([acct1, acct2])
        assert result.total == Decimal("5000")
        assert result.per_account["a1"] == Decimal("5000")
        assert result.per_account["a2"] == Decimal("0")


# ── AC-4: Negative balances included ────────────────────────────────────


@pytest.mark.unit
class TestNegativeBalances:
    """AC-4: Credit cards/loans with negative balances are summed."""

    def test_negative_balance_reduces_total(self) -> None:
        acct1 = _account(
            "broker",
            [_snapshot("broker", Decimal("100000"), datetime(2026, 1, 1))],
            AccountType.BROKER,
        )
        acct2 = _account(
            "credit",
            [_snapshot("credit", Decimal("-5000"), datetime(2026, 1, 1))],
            AccountType.REVOLVING,
        )
        result = calculate_total_portfolio_balance([acct1, acct2])
        assert result.total == Decimal("95000")
        assert result.per_account["credit"] == Decimal("-5000")

    def test_all_negative(self) -> None:
        acct = _account(
            "loan",
            [_snapshot("loan", Decimal("-25000"), datetime(2026, 1, 1))],
            AccountType.INSTALLMENT,
        )
        result = calculate_total_portfolio_balance([acct])
        assert result.total == Decimal("-25000")


# ── AC-5: Latest by max(datetime) ──────────────────────────────────────


@pytest.mark.unit
class TestLatestByDatetime:
    """AC-5: 'Latest' = max(snapshot.datetime), not list position."""

    def test_uses_max_datetime_not_last_position(self) -> None:
        # Snapshots in non-chronological order
        old = _snapshot("a1", Decimal("1000"), datetime(2026, 1, 1))
        new = _snapshot("a1", Decimal("9999"), datetime(2026, 6, 15))
        mid = _snapshot("a1", Decimal("5000"), datetime(2026, 3, 1))
        acct = _account("a1", [old, new, mid])  # new is in the middle of the list
        result = calculate_total_portfolio_balance([acct])
        assert result.total == Decimal("9999")
        assert result.per_account["a1"] == Decimal("9999")


# ── AC-6: Empty accounts list ──────────────────────────────────────────


@pytest.mark.unit
class TestEmptyAccountsList:
    """AC-6: Empty list returns zero total and empty per_account."""

    def test_empty_list(self) -> None:
        result = calculate_total_portfolio_balance([])
        assert result.total == Decimal("0")
        assert result.per_account == {}


# ── AC-7: Module import surface ─────────────────────────────────────────


@pytest.mark.unit
class TestModuleImports:
    """AC-7: Module imports only from approved packages."""

    def test_no_unexpected_imports(self) -> None:
        import zorivest_core.domain.portfolio_balance as mod

        source = open(mod.__file__, encoding="utf-8").read()  # noqa: SIM115
        # Allowed imports: __future__, dataclasses, datetime, decimal,
        # zorivest_core.domain.entities
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        allowed_prefixes = (
            "from __future__",
            "from dataclasses",
            "from datetime",
            "from decimal",
            "from zorivest_core.domain.entities",
            "import dataclasses",
            "import datetime",
            "import decimal",
        )
        for line in import_lines:
            assert any(
                line.startswith(prefix) for prefix in allowed_prefixes
            ), f"Unexpected import: {line}"
