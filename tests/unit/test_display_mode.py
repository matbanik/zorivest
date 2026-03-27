# tests/unit/test_display_mode.py
"""MEU-10 Red tests: DisplayMode + format_dollar + format_percentage.

FIC source: implementation-plan.md §MEU-10 (AC-1 through AC-10).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from zorivest_core.domain.display_mode import (
    DisplayMode,
    format_dollar,
    format_percentage,
)


# ── AC-1: DisplayMode dataclass ─────────────────────────────────────────


@pytest.mark.unit
class TestDisplayModeDataclass:
    """AC-1: DisplayMode frozen dataclass with defaults."""

    def test_defaults(self) -> None:
        mode = DisplayMode()
        assert mode.hide_dollars is False
        assert mode.hide_percentages is False
        assert mode.percent_mode is False

    def test_custom_values(self) -> None:
        mode = DisplayMode(
            hide_dollars=True,
            hide_percentages=True,
            percent_mode=True,
        )
        assert mode.hide_dollars is True
        assert mode.hide_percentages is True
        assert mode.percent_mode is True

    def test_frozen(self) -> None:
        mode = DisplayMode()
        with pytest.raises(AttributeError):
            mode.hide_dollars = True  # type: ignore[misc]


# ── AC-2: format_dollar normal output ───────────────────────────────────


@pytest.mark.unit
class TestFormatDollarNormal:
    """AC-2: format_dollar returns formatted dollar string."""

    def test_basic_formatting(self) -> None:
        mode = DisplayMode()
        result = format_dollar(Decimal("437903"), mode)
        assert result == "$437,903"

    def test_zero(self) -> None:
        mode = DisplayMode()
        result = format_dollar(Decimal("0"), mode)
        assert result == "$0"

    def test_cents(self) -> None:
        mode = DisplayMode()
        result = format_dollar(Decimal("1234.56"), mode)
        assert result == "$1,234.56"


# ── AC-3: Dollar masking (truth table rows 3–5) ────────────────────────


@pytest.mark.unit
class TestFormatDollarMasked:
    """AC-3: When hide_dollars=True, returns '••••••'."""

    def test_hides_dollars(self) -> None:
        mode = DisplayMode(hide_dollars=True)
        result = format_dollar(Decimal("437903"), mode)
        assert result == "••••••"

    def test_hides_zero(self) -> None:
        mode = DisplayMode(hide_dollars=True)
        result = format_dollar(Decimal("0"), mode)
        assert result == "••••••"


# ── AC-4: Percent mode appends percentage ───────────────────────────────


@pytest.mark.unit
class TestFormatDollarPercentMode:
    """AC-4: When percent_mode=True, appends (X.XX%)."""

    def test_percent_appended(self) -> None:
        mode = DisplayMode(percent_mode=True)
        result = format_dollar(
            Decimal("437903"),
            mode,
            total_portfolio=Decimal("518000"),
        )
        assert result == "$437,903 (84.54%)"

    def test_percent_mode_without_total(self) -> None:
        """percent_mode=True but no total_portfolio → no percentage shown."""
        mode = DisplayMode(percent_mode=True)
        result = format_dollar(Decimal("437903"), mode)
        assert result == "$437,903"


# ── AC-5: hide_dollars + percent_mode ───────────────────────────────────


@pytest.mark.unit
class TestFormatDollarHiddenWithPercent:
    """AC-5: hide_dollars=True + percent_mode=True → '•••••• (X.XX%)'."""

    def test_hidden_dollars_with_percent(self) -> None:
        mode = DisplayMode(hide_dollars=True, percent_mode=True)
        result = format_dollar(
            Decimal("437903"),
            mode,
            total_portfolio=Decimal("518000"),
        )
        assert result == "•••••• (84.54%)"


# ── AC-6: Percentage masking (truth table row 4) ───────────────────────


@pytest.mark.unit
class TestFormatDollarPercentHidden:
    """AC-6: hide_percentages=True masks % part as '••%'."""

    def test_percent_hidden(self) -> None:
        mode = DisplayMode(percent_mode=True, hide_percentages=True)
        result = format_dollar(
            Decimal("437903"),
            mode,
            total_portfolio=Decimal("518000"),
        )
        assert result == "$437,903 (••%)"

    def test_all_hidden(self) -> None:
        """hide_dollars + hide_percentages + percent_mode → '•••••• (••%)'."""
        mode = DisplayMode(
            hide_dollars=True,
            hide_percentages=True,
            percent_mode=True,
        )
        result = format_dollar(
            Decimal("437903"),
            mode,
            total_portfolio=Decimal("518000"),
        )
        assert result == "•••••• (••%)"


# ── AC-7: format_percentage ─────────────────────────────────────────────


@pytest.mark.unit
class TestFormatPercentage:
    """AC-7: format_percentage returns 'X.XX%' or '••%' if hidden."""

    def test_visible_percentage(self) -> None:
        mode = DisplayMode()
        result = format_percentage(Decimal("84.52"), mode)
        assert result == "84.52%"

    def test_hidden_percentage(self) -> None:
        mode = DisplayMode(hide_percentages=True)
        result = format_percentage(Decimal("84.52"), mode)
        assert result == "••%"

    def test_zero_percentage(self) -> None:
        mode = DisplayMode()
        result = format_percentage(Decimal("0"), mode)
        assert result == "0.00%"


# ── AC-8: All 6 truth table combinations ───────────────────────────────


@pytest.mark.unit
class TestTruthTable:
    """AC-8: All 6 state combinations from the spec truth table."""

    def test_row1_all_visible_no_percent(self) -> None:
        """$ visible, % visible, % mode off → '$437,903'."""
        mode = DisplayMode()
        result = format_dollar(Decimal("437903"), mode)
        assert result == "$437,903"

    def test_row2_all_visible_percent_on(self) -> None:
        """$ visible, % visible, % mode on → '$437,903 (84.54%)'."""
        mode = DisplayMode(percent_mode=True)
        result = format_dollar(
            Decimal("437903"), mode, total_portfolio=Decimal("518000")
        )
        assert result == "$437,903 (84.54%)"

    def test_row3_dollar_hidden_percent_on(self) -> None:
        """$ hidden, % visible, % mode on → '•••••• (84.54%)'."""
        mode = DisplayMode(hide_dollars=True, percent_mode=True)
        result = format_dollar(
            Decimal("437903"), mode, total_portfolio=Decimal("518000")
        )
        assert result == "•••••• (84.54%)"

    def test_row4_all_hidden_percent_on(self) -> None:
        """$ hidden, % hidden, % mode on → '•••••• (••%)'."""
        mode = DisplayMode(hide_dollars=True, hide_percentages=True, percent_mode=True)
        result = format_dollar(
            Decimal("437903"), mode, total_portfolio=Decimal("518000")
        )
        assert result == "•••••• (••%)"

    def test_row5_dollar_hidden_percent_off(self) -> None:
        """$ hidden, % visible, % mode off → '••••••'."""
        mode = DisplayMode(hide_dollars=True)
        result = format_dollar(Decimal("437903"), mode)
        assert result == "••••••"

    def test_row6_dollar_visible_percent_hidden_on(self) -> None:
        """$ visible, % hidden, % mode on → '$437,903 (••%)'."""
        mode = DisplayMode(hide_percentages=True, percent_mode=True)
        result = format_dollar(
            Decimal("437903"), mode, total_portfolio=Decimal("518000")
        )
        assert result == "$437,903 (••%)"


# ── AC-9: Division-by-zero protection ──────────────────────────────────


@pytest.mark.unit
class TestDivisionByZero:
    """AC-9: total_portfolio=0 with percent_mode → N/A%."""

    def test_zero_total_portfolio(self) -> None:
        mode = DisplayMode(percent_mode=True)
        result = format_dollar(Decimal("437903"), mode, total_portfolio=Decimal("0"))
        assert result == "$437,903 (N/A%)"


# ── AC-10: Module imports ──────────────────────────────────────────────


@pytest.mark.unit
class TestModuleImports:
    """AC-10: Module imports only from approved packages."""

    def test_no_unexpected_imports(self) -> None:
        import zorivest_core.domain.display_mode as mod

        source = open(mod.__file__, encoding="utf-8").read()  # noqa: SIM115
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        allowed_prefixes = (
            "from __future__",
            "from dataclasses",
            "from decimal",
            "from zorivest_core.domain.enums",
            "import dataclasses",
            "import decimal",
        )
        for line in import_lines:
            assert any(line.startswith(prefix) for prefix in allowed_prefixes), (
                f"Unexpected import: {line}"
            )
        # Value: verify at least 2 import lines were checked
        assert len(import_lines) >= 2, f"Only {len(import_lines)} import lines found"
