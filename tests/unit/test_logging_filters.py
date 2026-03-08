"""Tests for FeatureFilter and CatchallFilter — MEU-2A (AC-1 through AC-4)."""

from __future__ import annotations

import logging




from zorivest_infra.logging.filters import CatchallFilter, FeatureFilter


# ---------------------------------------------------------------------------
# FeatureFilter
# ---------------------------------------------------------------------------


class TestFeatureFilter:
    """AC-1, AC-2: FeatureFilter routes by logger name prefix."""

    def test_accepts_matching_prefix(self) -> None:
        """AC-1: FeatureFilter('zorivest.trades') accepts 'zorivest.trades.service'."""
        f = FeatureFilter("zorivest.trades")
        record = logging.LogRecord(
            name="zorivest.trades.service",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True

    def test_accepts_exact_prefix(self) -> None:
        """FeatureFilter accepts record whose name exactly equals the prefix."""
        f = FeatureFilter("zorivest.trades")
        record = logging.LogRecord(
            name="zorivest.trades",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True

    def test_rejects_non_matching_prefix(self) -> None:
        """AC-2: FeatureFilter('zorivest.trades') rejects 'zorivest.marketdata'."""
        f = FeatureFilter("zorivest.trades")
        record = logging.LogRecord(
            name="zorivest.marketdata",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is False

    def test_rejects_unrelated_logger(self) -> None:
        """FeatureFilter rejects completely unrelated logger names."""
        f = FeatureFilter("zorivest.trades")
        record = logging.LogRecord(
            name="some.other.module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is False


# ---------------------------------------------------------------------------
# CatchallFilter
# ---------------------------------------------------------------------------


class TestCatchallFilter:
    """AC-3, AC-4: CatchallFilter accepts non-feature, rejects known-feature."""

    KNOWN_PREFIXES = ["zorivest.trades", "zorivest.marketdata", "zorivest.accounts"]

    def test_accepts_non_feature_record(self) -> None:
        """AC-3: CatchallFilter accepts record whose name matches no known prefix."""
        f = CatchallFilter(self.KNOWN_PREFIXES)
        record = logging.LogRecord(
            name="some.random.module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True

    def test_rejects_known_feature_record(self) -> None:
        """AC-4: CatchallFilter rejects record whose name matches a known prefix."""
        f = CatchallFilter(self.KNOWN_PREFIXES)
        record = logging.LogRecord(
            name="zorivest.trades.service",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is False

    def test_rejects_exact_prefix_match(self) -> None:
        """CatchallFilter rejects exact prefix match (not just children)."""
        f = CatchallFilter(self.KNOWN_PREFIXES)
        record = logging.LogRecord(
            name="zorivest.accounts",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is False

    def test_accepts_with_empty_known_prefixes(self) -> None:
        """CatchallFilter with no known prefixes accepts all records."""
        f = CatchallFilter([])
        record = logging.LogRecord(
            name="zorivest.trades",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True
