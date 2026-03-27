"""Value object tests — MEU-4 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
FIC defined in implementation-plan.md §MEU-4.
All value objects from 01-domain-layer.md §1.2 line 29:
  Money, PositionSize, Ticker, Conviction, ImageData
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

pytestmark = pytest.mark.unit


# ── AC-1 / AC-2 / AC-3: Money ───────────────────────────────────────────


class TestMoney:
    """Money frozen dataclass with amount (Decimal) and currency (str)."""

    def test_money_construction(self) -> None:
        from zorivest_core.domain.value_objects import Money

        m = Money(amount=Decimal("100.50"), currency="USD")
        assert m.amount == Decimal("100.50")
        assert m.currency == "USD"

    def test_money_default_currency_is_usd(self) -> None:
        from zorivest_core.domain.value_objects import Money

        m = Money(amount=Decimal("0"))
        assert m.currency == "USD"

    def test_money_zero_amount_allowed(self) -> None:
        from zorivest_core.domain.value_objects import Money

        m = Money(amount=Decimal("0"))
        assert m.amount == Decimal("0")

    def test_money_rejects_negative_amount(self) -> None:
        """AC-2: Negative amount raises ValueError."""
        from zorivest_core.domain.value_objects import Money

        with pytest.raises(ValueError, match="negative"):
            Money(amount=Decimal("-1.00"))

    def test_money_rejects_empty_currency(self) -> None:
        """AC-3: Empty currency raises ValueError."""
        from zorivest_core.domain.value_objects import Money

        with pytest.raises(ValueError, match="currency"):
            Money(amount=Decimal("100"), currency="")


# ── AC-4 / AC-5: PositionSize ───────────────────────────────────────────


class TestPositionSize:
    """PositionSize frozen dataclass wrapping share_size, position_size, risk_per_share."""

    def test_position_size_construction(self) -> None:
        from zorivest_core.domain.value_objects import PositionSize

        ps = PositionSize(
            share_size=100,
            position_size=Decimal("61961.00"),
            risk_per_share=Decimal("1.00"),
        )
        assert ps.share_size == 100
        assert ps.position_size == Decimal("61961.00")
        assert ps.risk_per_share == Decimal("1.00")

    def test_position_size_rejects_negative_share_size(self) -> None:
        """AC-5: Negative share_size raises ValueError."""
        from zorivest_core.domain.value_objects import PositionSize

        with pytest.raises(ValueError, match="share_size"):
            PositionSize(
                share_size=-1,
                position_size=Decimal("0"),
                risk_per_share=Decimal("1.00"),
            )


# ── AC-6 / AC-7: Ticker ─────────────────────────────────────────────────


class TestTicker:
    """Ticker frozen dataclass with symbol normalization."""

    def test_ticker_normalizes_to_uppercase(self) -> None:
        """AC-6: Ticker normalizes to uppercase at construction."""
        from zorivest_core.domain.value_objects import Ticker

        t = Ticker(symbol="spy")
        assert t.symbol == "SPY"

    def test_ticker_already_uppercase_unchanged(self) -> None:
        from zorivest_core.domain.value_objects import Ticker

        t = Ticker(symbol="AAPL")
        assert t.symbol == "AAPL"

    def test_ticker_rejects_empty_symbol(self) -> None:
        """AC-7: Empty symbol raises ValueError."""
        from zorivest_core.domain.value_objects import Ticker

        with pytest.raises(ValueError, match="symbol"):
            Ticker(symbol="")

    def test_ticker_rejects_whitespace_only_symbol(self) -> None:
        """AC-7: Whitespace-only symbol raises ValueError."""
        from zorivest_core.domain.value_objects import Ticker

        with pytest.raises(ValueError, match="symbol"):
            Ticker(symbol="   ")


# ── AC-8: Conviction ────────────────────────────────────────────────────


class TestConviction:
    """Conviction frozen dataclass with ConvictionLevel enum."""

    def test_conviction_construction(self) -> None:
        from zorivest_core.domain.enums import ConvictionLevel
        from zorivest_core.domain.value_objects import Conviction

        c = Conviction(level=ConvictionLevel.HIGH)
        assert c.level == ConvictionLevel.HIGH


# ── AC-9 / AC-10 / AC-11: ImageData ─────────────────────────────────────


class TestImageData:
    """ImageData frozen dataclass with data, mime_type, width, height."""

    def test_image_data_construction(self) -> None:
        from zorivest_core.domain.value_objects import ImageData

        img = ImageData(
            data=b"\x00\x01\x02",
            mime_type="image/webp",
            width=1920,
            height=1080,
        )
        assert img.data == b"\x00\x01\x02"
        assert img.mime_type == "image/webp"
        assert img.width == 1920
        assert img.height == 1080

    def test_image_data_rejects_non_positive_width(self) -> None:
        """AC-10: Non-positive width raises ValueError."""
        from zorivest_core.domain.value_objects import ImageData

        with pytest.raises(ValueError, match="width"):
            ImageData(data=b"\x00", mime_type="image/webp", width=0, height=100)

    def test_image_data_rejects_non_positive_height(self) -> None:
        """AC-10: Non-positive height raises ValueError."""
        from zorivest_core.domain.value_objects import ImageData

        with pytest.raises(ValueError, match="height"):
            ImageData(data=b"\x00", mime_type="image/webp", width=100, height=-1)

    def test_image_data_rejects_empty_data(self) -> None:
        """AC-11: Empty data raises ValueError."""
        from zorivest_core.domain.value_objects import ImageData

        with pytest.raises(ValueError, match="data"):
            ImageData(data=b"", mime_type="image/webp", width=100, height=100)


# ── AC-12: All value objects are frozen ──────────────────────────────────


class TestFrozenEnforcement:
    """AC-12: All value objects are frozen. Assignment raises FrozenInstanceError."""

    def test_money_is_frozen(self) -> None:
        from zorivest_core.domain.value_objects import Money

        m = Money(amount=Decimal("10"))
        with pytest.raises(FrozenInstanceError):
            m.amount = Decimal("20")  # type: ignore[misc]

    def test_position_size_is_frozen(self) -> None:
        from zorivest_core.domain.value_objects import PositionSize

        ps = PositionSize(
            share_size=10,
            position_size=Decimal("1000"),
            risk_per_share=Decimal("1"),
        )
        with pytest.raises(FrozenInstanceError):
            ps.share_size = 20  # type: ignore[misc]

    def test_ticker_is_frozen(self) -> None:
        from zorivest_core.domain.value_objects import Ticker

        t = Ticker(symbol="SPY")
        with pytest.raises(FrozenInstanceError):
            t.symbol = "AAPL"  # type: ignore[misc]

    def test_conviction_is_frozen(self) -> None:
        from zorivest_core.domain.enums import ConvictionLevel
        from zorivest_core.domain.value_objects import Conviction

        c = Conviction(level=ConvictionLevel.HIGH)
        with pytest.raises(FrozenInstanceError):
            c.level = ConvictionLevel.LOW  # type: ignore[misc]

    def test_image_data_is_frozen(self) -> None:
        from zorivest_core.domain.value_objects import ImageData

        img = ImageData(data=b"\x00", mime_type="image/webp", width=10, height=10)
        with pytest.raises(FrozenInstanceError):
            img.width = 20  # type: ignore[misc]


# ── AC-13: Import surface ───────────────────────────────────────────────


class TestImportSurface:
    """AC-13: Module imports only from allowed modules."""

    def test_import_surface_value_objects(self) -> None:
        import zorivest_core.domain.value_objects as mod

        source_file = mod.__file__
        assert source_file is not None

        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        allowed_modules = {
            "__future__",
            "dataclasses",
            "decimal",
            "zorivest_core",
        }
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in allowed_modules, f"Forbidden import: {alias.name}"
                    import_count += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )
                    import_count += 1
        # Value: verify at least 2 imports were checked
        assert import_count >= 2, f"Only {import_count} imports found"


# ── Module integrity ────────────────────────────────────────────────────


class TestModuleIntegrity:
    """Verify the module exports exactly the 5 expected value object classes."""

    def test_module_has_expected_classes(self) -> None:
        import zorivest_core.domain.value_objects as mod

        class_names = [
            name
            for name, obj in inspect.getmembers(mod, inspect.isclass)
            if obj.__module__ == mod.__name__
        ]
        expected = {"Money", "PositionSize", "Ticker", "Conviction", "ImageData"}
        assert set(class_names) == expected, (
            f"Expected {expected}, got {set(class_names)}"
        )
