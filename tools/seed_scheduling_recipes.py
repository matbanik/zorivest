# tools/seed_scheduling_recipes.py
"""Seed 10 pre-built scheduling recipes for market data pipelines (§8a.13).

Defines 10 PolicyDocument-compliant recipe dicts and provides
a seed_recipes() function for idempotent insertion into the database.

Spec: 08a-market-data-expansion.md §8a.13
MEU: 194
"""

from __future__ import annotations

import json
from typing import Any


# ── 10 Scheduling Recipes (§8a.13) ────────────────────────────────────────

SCHEDULING_RECIPES: list[dict[str, Any]] = [
    # 1. Nightly OHLCV refresh
    {
        "schema_version": 1,
        "name": "Nightly OHLCV Refresh",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Fetch daily OHLCV bars after market close for all watched tickers.",
        },
        "trigger": {
            "cron_expression": "0 22 * * 1-5",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_ohlcv",
                "type": "fetch",
                "params": {
                    "provider": "alpaca",
                    "data_type": "ohlcv",
                    "fallback_provider": "eodhd",
                },
            },
            {
                "id": "store_ohlcv",
                "type": "market_data_store",
                "params": {
                    "data_type": "ohlcv",
                    "write_mode": "upsert",
                    "source_step_id": "fetch_ohlcv",
                },
            },
        ],
    },
    # 2. Pre-market quote sweep
    {
        "schema_version": 1,
        "name": "Pre-market Quote Sweep",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Sweep pre-market quotes every 5 minutes before market open.",
        },
        "trigger": {
            "cron_expression": "*/5 4-9 * * 1-5",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_quotes",
                "type": "fetch",
                "params": {
                    "provider": "finnhub",
                    "data_type": "quote",
                    "fallback_provider": "alpaca",
                },
            },
        ],
    },
    # 3. Weekly fundamentals
    {
        "schema_version": 1,
        "name": "Weekly Fundamentals",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Refresh fundamentals data every Saturday morning.",
        },
        "trigger": {
            "cron_expression": "0 6 * * 6",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_fundamentals",
                "type": "fetch",
                "params": {
                    "provider": "fmp",
                    "data_type": "fundamentals",
                    "fallback_provider": "alpha_vantage",
                },
            },
            {
                "id": "store_fundamentals",
                "type": "market_data_store",
                "params": {
                    "data_type": "fundamentals",
                    "write_mode": "upsert",
                    "source_step_id": "fetch_fundamentals",
                },
            },
        ],
    },
    # 4. Daily earnings calendar
    {
        "schema_version": 1,
        "name": "Daily Earnings Calendar",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Fetch upcoming earnings reports daily before market open.",
        },
        "trigger": {
            "cron_expression": "0 5 * * *",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_earnings",
                "type": "fetch",
                "params": {
                    "provider": "finnhub",
                    "data_type": "earnings",
                    "fallback_provider": "fmp",
                },
            },
            {
                "id": "store_earnings",
                "type": "market_data_store",
                "params": {
                    "data_type": "earnings",
                    "write_mode": "upsert",
                    "source_step_id": "fetch_earnings",
                },
            },
        ],
    },
    # 5. Weekly dividend tracker
    {
        "schema_version": 1,
        "name": "Weekly Dividend Tracker",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Track dividend announcements every Monday morning.",
        },
        "trigger": {
            "cron_expression": "0 7 * * 1",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_dividends",
                "type": "fetch",
                "params": {
                    "provider": "polygon",
                    "data_type": "dividends",
                    "fallback_provider": "eodhd",
                },
            },
            {
                "id": "store_dividends",
                "type": "market_data_store",
                "params": {
                    "data_type": "dividends",
                    "write_mode": "upsert",
                    "source_step_id": "fetch_dividends",
                },
            },
        ],
    },
    # 6. Near-real-time news
    {
        "schema_version": 1,
        "name": "Near-real-time News Feed",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Stream market news every 2 minutes during trading hours.",
        },
        "trigger": {
            "cron_expression": "*/2 6-20 * * 1-5",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_news",
                "type": "fetch",
                "params": {
                    "provider": "finnhub",
                    "data_type": "news",
                    "fallback_provider": "polygon",
                },
            },
        ],
    },
    # 7. Daily insider transactions
    {
        "schema_version": 1,
        "name": "Daily Insider Transactions",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Fetch insider buy/sell filings after market close.",
        },
        "trigger": {
            "cron_expression": "30 23 * * 1-5",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_insider",
                "type": "fetch",
                "params": {
                    "provider": "finnhub",
                    "data_type": "insider",
                    "fallback_provider": "fmp",
                },
            },
            {
                "id": "store_insider",
                "type": "market_data_store",
                "params": {
                    "data_type": "insider",
                    "write_mode": "upsert",
                    "source_step_id": "fetch_insider",
                },
            },
        ],
    },
    # 8. Weekly economic calendar
    {
        "schema_version": 1,
        "name": "Weekly Economic Calendar",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Refresh economic calendar events every Sunday morning.",
        },
        "trigger": {
            "cron_expression": "0 6 * * 0",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_economic",
                "type": "fetch",
                "params": {
                    "provider": "finnhub",
                    "data_type": "economic_calendar",
                    "fallback_provider": "fmp",
                },
            },
        ],
    },
    # 9. Daily options chain (DISABLED — pending get_options_chain())
    {
        "schema_version": 1,
        "name": "Daily Options Chain",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Fetch options chain data before market close. "
            "Disabled pending implementation of get_options_chain() service method.",
        },
        "trigger": {
            "cron_expression": "30 15 * * 1-5",
            "timezone": "America/New_York",
            "enabled": False,  # AC-6: disabled pending service implementation
        },
        "steps": [
            {
                "id": "fetch_options",
                "type": "fetch",
                "params": {
                    "provider": "tradier",
                    "data_type": "options_chain",
                    "fallback_provider": "polygon",
                },
            },
        ],
    },
    # 10. Monthly ETF holdings
    {
        "schema_version": 1,
        "name": "Monthly ETF Holdings",
        "metadata": {
            "author": "seed_scheduling_recipes",
            "description": "Refresh ETF holdings data on the first of each month.",
        },
        "trigger": {
            "cron_expression": "0 8 1 * *",
            "timezone": "America/New_York",
            "enabled": True,
        },
        "steps": [
            {
                "id": "fetch_etf_holdings",
                "type": "fetch",
                "params": {
                    "provider": "fmp",
                    "data_type": "etf_holdings",
                    "fallback_provider": "eodhd",
                },
            },
        ],
    },
]


def seed_recipes(
    *,
    policy_repo: Any = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Seed the 10 scheduling recipes into the policy repository.

    Idempotent: skips recipes whose name already exists (AC-5).
    All recipes are created with approved=false (AC-3).

    Args:
        policy_repo: Repository with create() and get_by_name() methods.
                     If None, returns validated recipes without persisting.
        dry_run: If True, validate only — do not persist.

    Returns:
        List of created recipe metadata dicts.
    """
    from zorivest_core.domain.pipeline import PolicyDocument

    results: list[dict[str, Any]] = []

    for recipe_dict in SCHEDULING_RECIPES:
        # Validate against PolicyDocument schema (AC-2)
        doc = PolicyDocument(**recipe_dict)

        if dry_run or policy_repo is None:
            results.append(
                {
                    "name": doc.name,
                    "status": "validated",
                    "schema_version": doc.schema_version,
                }
            )
            continue

        # Idempotent check (AC-5)
        existing = policy_repo.get_by_name(doc.name)
        if existing is not None:
            results.append(
                {
                    "name": doc.name,
                    "status": "skipped",
                    "reason": "already exists",
                }
            )
            continue

        # Persist (AC-3: approved=false is the repository default)
        policy_id = policy_repo.create(
            name=doc.name,
            policy_json=json.dumps(recipe_dict),
            content_hash="seed",
            enabled=recipe_dict["trigger"].get("enabled", True),
        )

        results.append(
            {
                "name": doc.name,
                "status": "created",
                "policy_id": policy_id,
            }
        )

    return results


if __name__ == "__main__":
    # CLI: validate all recipes without persisting
    print("Validating 10 scheduling recipes...")
    results = seed_recipes(dry_run=True)
    for r in results:
        print(f"  {r['status']:>10} | {r['name']}")
    print(f"\n{len(results)} recipes validated.")
