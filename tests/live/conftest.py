# tests/live/conftest.py
"""Shared fixtures and configuration for live data tests.

Provides the --run-live CLI flag and shared HTTP client fixtures.
"""

from __future__ import annotations

import pytest
import pytest_asyncio


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --run-live CLI option for live data tests."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live data integration tests (makes real HTTP calls)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the 'live' marker."""
    config.addinivalue_line(
        "markers",
        "live: mark test as live data test (requires --run-live to run)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip live-marked tests unless --run-live is provided."""
    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(reason="need --run-live option to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest_asyncio.fixture()
async def http_client():
    """Function-scoped httpx.AsyncClient for live tests.

    Uses a realistic User-Agent and sensible timeouts.
    Function-scoped to avoid event-loop-closed errors on Windows
    with pytest-asyncio's strict mode.
    """
    import httpx

    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
        },
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
    ) as client:
        yield client
