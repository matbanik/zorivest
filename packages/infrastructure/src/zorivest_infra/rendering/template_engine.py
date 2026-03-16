# packages/infrastructure/src/zorivest_infra/rendering/template_engine.py
"""Jinja2 template engine with financial filters (§9.7a).

Provides create_template_engine() with currency and percent filters.

Spec: 09-scheduling.md §9.7a
MEU: 87
"""

from __future__ import annotations

from jinja2 import Environment, BaseLoader


def _currency_filter(value: float, symbol: str = "$", decimals: int = 2) -> str:
    """Format a number as currency."""
    return f"{symbol}{value:,.{decimals}f}"


def _percent_filter(value: float, decimals: int = 2) -> str:
    """Format a decimal fraction as percentage."""
    return f"{value * 100:.{decimals}f}%"


def create_template_engine() -> Environment:
    """Create a Jinja2 environment with financial filters.

    Registers:
    - ``currency``: Format numbers as $1,234.56
    - ``percent``: Format 0.1234 as 12.34%
    """
    env = Environment(
        loader=BaseLoader(),
        autoescape=True,
    )

    env.filters["currency"] = _currency_filter
    env.filters["percent"] = _percent_filter

    return env
