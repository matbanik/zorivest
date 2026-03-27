# tests/unit/test_account_review.py
"""MEU-11 Red tests: Account Review workflow domain logic.

FIC source: implementation-plan.md §MEU-11 (AC-1 through AC-10).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import Account, BalanceSnapshot
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.account_review import (
    AccountReviewItem,
    AccountReviewResult,
    AccountReviewSummary,
    apply_balance_update,
    prepare_review_checklist,
    skip_account,
    summarize_review,
)


# ── Helpers ─────────────────────────────────────────────────────────────


def _snapshot(account_id: str, balance: Decimal, dt: datetime) -> BalanceSnapshot:
    """Create a BalanceSnapshot for testing."""
    return BalanceSnapshot(id=0, account_id=account_id, datetime=dt, balance=balance)


def _account(
    account_id: str,
    account_type: AccountType = AccountType.BROKER,
    snapshots: list[BalanceSnapshot] | None = None,
) -> Account:
    """Create an Account for testing."""
    acct = Account(
        account_id=account_id,
        name=f"Test {account_id}",
        account_type=account_type,
        institution="Test Bank",
    )
    if snapshots:
        acct.balance_snapshots.extend(snapshots)
    return acct


# ── AC-1: AccountReviewItem dataclass ───────────────────────────────────


@pytest.mark.unit
class TestAccountReviewItemDataclass:
    """AC-1: AccountReviewItem frozen dataclass with all fields."""

    def test_fields_exist(self) -> None:
        item = AccountReviewItem(
            account_id="a1",
            name="Brokerage",
            account_type=AccountType.BROKER,
            institution="IBKR",
            last_balance=Decimal("50000"),
            last_balance_datetime=datetime(2026, 1, 1),
            supports_api_fetch=True,
        )
        assert item.account_id == "a1"
        assert item.name == "Brokerage"
        assert item.account_type == AccountType.BROKER
        assert item.institution == "IBKR"
        assert item.last_balance == Decimal("50000")
        assert item.last_balance_datetime == datetime(2026, 1, 1)
        assert item.supports_api_fetch is True

    def test_frozen(self) -> None:
        item = AccountReviewItem(
            account_id="a1",
            name="Test",
            account_type=AccountType.BANK,
            institution="",
            last_balance=None,
            last_balance_datetime=None,
            supports_api_fetch=False,
        )
        with pytest.raises(AttributeError):
            item.account_id = "x"  # type: ignore[misc]


# ── AC-2: AccountReviewResult dataclass ─────────────────────────────────


@pytest.mark.unit
class TestAccountReviewResultDataclass:
    """AC-2: AccountReviewResult frozen dataclass."""

    def test_updated_result(self) -> None:
        result = AccountReviewResult(
            account_id="a1",
            action="updated",
            old_balance=Decimal("1000"),
            new_balance=Decimal("2000"),
        )
        assert result.action == "updated"
        assert result.old_balance == Decimal("1000")
        assert result.new_balance == Decimal("2000")

    def test_skipped_result(self) -> None:
        result = AccountReviewResult(
            account_id="a1",
            action="skipped",
            old_balance=Decimal("1000"),
            new_balance=None,
        )
        assert result.action == "skipped"


# ── AC-3: AccountReviewSummary dataclass ────────────────────────────────


@pytest.mark.unit
class TestAccountReviewSummaryDataclass:
    """AC-3: AccountReviewSummary frozen dataclass."""

    def test_fields_exist(self) -> None:
        summary = AccountReviewSummary(
            total_accounts=3,
            updated_count=2,
            skipped_count=1,
            old_total=Decimal("10000"),
            new_total=Decimal("12000"),
            results=[],
        )
        assert summary.total_accounts == 3
        assert summary.updated_count == 2
        assert summary.skipped_count == 1
        assert summary.old_total == Decimal("10000")
        assert summary.new_total == Decimal("12000")


# ── AC-4: prepare_review_checklist (BROKER = api fetch) ─────────────────


@pytest.mark.unit
class TestPrepareReviewChecklist:
    """AC-4: BROKER type sets supports_api_fetch=True."""

    def test_broker_gets_api_fetch(self) -> None:
        acct = _account(
            "a1",
            AccountType.BROKER,
            [_snapshot("a1", Decimal("50000"), datetime(2026, 1, 1))],
        )
        items = prepare_review_checklist([acct])
        assert len(items) == 1
        assert items[0].supports_api_fetch is True

    def test_bank_no_api_fetch(self) -> None:
        acct = _account(
            "a1",
            AccountType.BANK,
            [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))],
        )
        items = prepare_review_checklist([acct])
        assert items[0].supports_api_fetch is False

    def test_revolving_no_api_fetch(self) -> None:
        acct = _account("a1", AccountType.REVOLVING)
        items = prepare_review_checklist([acct])
        assert items[0].supports_api_fetch is False

    def test_multiple_accounts_ordering(self) -> None:
        acct1 = _account("a1", AccountType.BROKER)
        acct2 = _account("a2", AccountType.BANK)
        items = prepare_review_checklist([acct1, acct2])
        assert len(items) == 2
        assert items[0].account_id == "a1"
        assert items[1].account_id == "a2"


# ── AC-5: Latest balance from max(datetime) ────────────────────────────


@pytest.mark.unit
class TestPrepareChecklistLatestBalance:
    """AC-5: Extracts last_balance from max(datetime) snapshot."""

    def test_latest_by_datetime(self) -> None:
        old = _snapshot("a1", Decimal("1000"), datetime(2026, 1, 1))
        new = _snapshot("a1", Decimal("9999"), datetime(2026, 6, 15))
        mid = _snapshot("a1", Decimal("5000"), datetime(2026, 3, 1))
        acct = _account("a1", AccountType.BROKER, [old, new, mid])
        items = prepare_review_checklist([acct])
        assert items[0].last_balance == Decimal("9999")
        assert items[0].last_balance_datetime == datetime(2026, 6, 15)

    def test_no_snapshots_returns_none(self) -> None:
        acct = _account("a1", AccountType.BANK)
        items = prepare_review_checklist([acct])
        assert items[0].last_balance is None
        assert items[0].last_balance_datetime is None


# ── AC-6: apply_balance_update creates snapshot ─────────────────────────


@pytest.mark.unit
class TestApplyBalanceUpdate:
    """AC-6: Creates a new BalanceSnapshot and returns 'updated' result."""

    def test_creates_snapshot_and_returns_updated(self) -> None:
        acct = _account(
            "a1",
            AccountType.BROKER,
            [_snapshot("a1", Decimal("1000"), datetime(2026, 1, 1))],
        )
        original_count = len(acct.balance_snapshots)
        result = apply_balance_update(acct, Decimal("2000"), datetime(2026, 3, 1))
        assert result.action == "updated"
        assert result.account_id == "a1"
        assert result.old_balance == Decimal("1000")
        assert result.new_balance == Decimal("2000")
        assert len(acct.balance_snapshots) == original_count + 1

    def test_update_from_no_snapshots(self) -> None:
        acct = _account("a1", AccountType.BANK)
        result = apply_balance_update(acct, Decimal("5000"), datetime(2026, 1, 1))
        assert result.action == "updated"
        assert result.old_balance is None
        assert result.new_balance == Decimal("5000")
        assert len(acct.balance_snapshots) == 1


# ── AC-7: Dedup rule ───────────────────────────────────────────────────


@pytest.mark.unit
class TestApplyBalanceUpdateDedup:
    """AC-7: 'skipped' if new_balance equals latest existing balance."""

    def test_same_balance_skips(self) -> None:
        acct = _account(
            "a1",
            AccountType.BROKER,
            [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))],
        )
        original_count = len(acct.balance_snapshots)
        result = apply_balance_update(acct, Decimal("5000"), datetime(2026, 3, 1))
        assert result.action == "skipped"
        assert len(acct.balance_snapshots) == original_count  # no new snapshot

    def test_different_balance_updates(self) -> None:
        acct = _account(
            "a1",
            AccountType.BROKER,
            [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))],
        )
        result = apply_balance_update(acct, Decimal("5001"), datetime(2026, 3, 1))
        assert result.action == "updated"


# ── AC-8: skip_account ─────────────────────────────────────────────────


@pytest.mark.unit
class TestSkipAccount:
    """AC-8: Returns 'skipped', no side effects."""

    def test_skip_returns_skipped(self) -> None:
        acct = _account(
            "a1",
            AccountType.BROKER,
            [_snapshot("a1", Decimal("5000"), datetime(2026, 1, 1))],
        )
        original_count = len(acct.balance_snapshots)
        result = skip_account(acct)
        assert result.action == "skipped"
        assert result.account_id == "a1"
        assert result.old_balance == Decimal("5000")
        assert result.new_balance is None
        assert len(acct.balance_snapshots) == original_count

    def test_skip_no_snapshots(self) -> None:
        acct = _account("a1", AccountType.BANK)
        result = skip_account(acct)
        assert result.action == "skipped"
        assert result.old_balance is None


# ── AC-9: summarize_review ──────────────────────────────────────────────


@pytest.mark.unit
class TestSummarizeReview:
    """AC-9: Aggregates counts and computes old/new totals."""

    def test_mixed_results(self) -> None:
        acct1 = _account(
            "a1",
            AccountType.BROKER,
            [
                _snapshot("a1", Decimal("1000"), datetime(2026, 1, 1)),
                _snapshot("a1", Decimal("2000"), datetime(2026, 3, 1)),
            ],
        )
        acct2 = _account(
            "a2",
            AccountType.BANK,
            [_snapshot("a2", Decimal("3000"), datetime(2026, 1, 1))],
        )
        results = [
            AccountReviewResult("a1", "updated", Decimal("1000"), Decimal("2000")),
            AccountReviewResult("a2", "skipped", Decimal("3000"), None),
        ]
        summary = summarize_review(results, [acct1, acct2])
        assert summary.total_accounts == 2
        assert summary.updated_count == 1
        assert summary.skipped_count == 1
        assert summary.results == results

    def test_empty(self) -> None:
        summary = summarize_review([], [])
        assert summary.total_accounts == 0
        assert summary.updated_count == 0
        assert summary.skipped_count == 0
        assert summary.old_total == Decimal("0")
        assert summary.new_total == Decimal("0")


# ── AC-10: Module imports ──────────────────────────────────────────────


@pytest.mark.unit
class TestModuleImports:
    """AC-10: Module imports only from approved packages."""

    def test_no_unexpected_imports(self) -> None:
        import zorivest_core.domain.account_review as mod

        source = open(mod.__file__, encoding="utf-8").read()  # noqa: SIM115
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
            "from zorivest_core.domain.enums",
            "import dataclasses",
            "import datetime",
            "import decimal",
        )
        for line in import_lines:
            assert any(line.startswith(prefix) for prefix in allowed_prefixes), (
                f"Unexpected import: {line}"
            )
        # Value: verify import count is bounded (module shouldn't grow unchecked)
        assert len(import_lines) <= 10, f"Too many imports: {len(import_lines)}"
