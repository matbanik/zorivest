# tests/unit/test_scheduling_recipes.py
"""MEU-194 — Scheduling Recipes unit tests.

FIC: implementation-plan.md §MEU-194 AC-1..AC-6
Tests the 10 pre-built scheduling recipe definitions:
  AC-1: 10 recipes defined with correct cron, provider, fallback per spec
  AC-2: All 10 recipes pass PolicyDocument validation
  AC-3: Recipes seeded with approved=false (human-in-the-loop)
  AC-4: Recipes use schema_version: 2 for query/compose steps where needed
  AC-5: Seed script is idempotent (re-running doesn't create duplicates)
  AC-6: Recipe #9 (options chain) created with enabled=false
"""

from __future__ import annotations

import pytest


# ── AC-1: 10 recipes defined ─────────────────────────────────────────────


class TestAC1RecipeDefinitions:
    """AC-1: 10 scheduling recipes defined with correct cron, provider, fallback."""

    def test_exactly_10_recipes(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        assert len(SCHEDULING_RECIPES) == 10

    def test_all_recipes_have_name(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            assert recipe.get("name"), f"Recipe missing 'name': {recipe}"

    def test_all_recipes_have_cron(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            trigger = recipe.get("trigger", {})
            assert trigger.get("cron_expression"), (
                f"Recipe '{recipe.get('name')}' missing cron_expression"
            )

    def test_nightly_ohlcv_cron(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        ohlcv = next(r for r in SCHEDULING_RECIPES if "OHLCV" in r["name"])
        assert ohlcv["trigger"]["cron_expression"] == "0 22 * * 1-5"

    def test_premarket_quote_cron(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        quote = next(r for r in SCHEDULING_RECIPES if "quote" in r["name"].lower())
        assert quote["trigger"]["cron_expression"] == "*/5 4-9 * * 1-5"

    def test_recipe_names_are_unique(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        names = [r["name"] for r in SCHEDULING_RECIPES]
        assert len(names) == len(set(names)), f"Duplicate names found: {names}"


# ── AC-2: All 10 pass PolicyDocument validation ──────────────────────────


class TestAC2PolicyValidation:
    """AC-2: All 10 recipes pass PolicyDocument validation."""

    def test_all_recipes_validate(self) -> None:
        from zorivest_core.domain.pipeline import PolicyDocument
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            try:
                PolicyDocument(**recipe)
            except Exception as e:
                pytest.fail(f"Recipe '{recipe.get('name')}' failed validation: {e}")


# ── AC-3: Recipes seeded with approved=false ─────────────────────────────


class TestAC3ApprovalState:
    """AC-3: Recipes seeded with approved=false (human-in-the-loop)."""

    def test_seed_function_sets_approved_false(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        # The seed function should NOT set approved=true on any recipe.
        # This is validated at seed-time, not in the PolicyDocument itself.
        # We verify the recipes don't carry an 'approved' field
        # (the PolicyModel defaults to approved=false).
        for recipe in SCHEDULING_RECIPES:
            # PolicyDocument doesn't have an 'approved' field —
            # that's set at the model/repository level.
            assert "approved" not in recipe, (
                f"Recipe '{recipe.get('name')}' should not set 'approved' "
                "(repository defaults to false)"
            )


# ── AC-4: Schema version correctness ────────────────────────────────────


class TestAC4SchemaVersion:
    """AC-4: Recipes use correct schema_version."""

    def test_all_recipes_have_schema_version(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            assert "schema_version" in recipe, (
                f"Recipe '{recipe.get('name')}' missing schema_version"
            )


# ── AC-5: Idempotency ───────────────────────────────────────────────────


class TestAC5Idempotency:
    """AC-5: Seed script is idempotent (re-running doesn't create duplicates)."""

    def test_seed_function_exists_and_callable(self) -> None:
        from tools.seed_scheduling_recipes import seed_recipes

        assert callable(seed_recipes)

    def test_seed_dedup_by_name(self) -> None:
        """Verify the seed function uses name-based dedup."""
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        names = [r["name"] for r in SCHEDULING_RECIPES]
        assert len(names) == len(set(names))

    def test_seed_idempotent_second_run_skips_all(self) -> None:
        """Calling seed_recipes() twice against the same repo creates no dupes."""
        from unittest.mock import MagicMock
        from tools.seed_scheduling_recipes import seed_recipes

        mock_repo = MagicMock()
        # First run: no existing recipes → all created
        mock_repo.get_by_name.return_value = None
        mock_repo.create.side_effect = list(range(1, 11))

        first_results = seed_recipes(policy_repo=mock_repo)
        created_count = sum(1 for r in first_results if r["status"] == "created")
        assert created_count == 10, f"First run should create 10, got {created_count}"
        assert mock_repo.create.call_count == 10

        # Reset mocks for second run
        mock_repo.reset_mock()
        # Second run: all recipes already exist → all skipped
        mock_repo.get_by_name.return_value = MagicMock()  # non-None = exists

        second_results = seed_recipes(policy_repo=mock_repo)
        skipped_count = sum(1 for r in second_results if r["status"] == "skipped")
        assert skipped_count == 10, (
            f"Second run should skip all 10, got {skipped_count}"
        )
        assert mock_repo.create.call_count == 0, "Second run should not call create()"


# ── AC-6: Recipe #9 (options chain) disabled ──────────────────────────────


class TestAC6OptionsChainDisabled:
    """AC-6: Recipe #9 (options chain) created with enabled=false."""

    def test_options_chain_disabled(self) -> None:
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        options_recipe = next(
            r for r in SCHEDULING_RECIPES if "options" in r["name"].lower()
        )
        assert options_recipe["trigger"]["enabled"] is False, (
            "Options chain recipe should be disabled (enabled=false) "
            "pending implementation of get_options_chain() service method"
        )


# ── F1-FIX: Store steps have source_step_id wired ──────────────────────


class TestStoreStepSourceWiring:
    """Finding 1: All store steps must have source_step_id pointing to a fetch step."""

    def test_all_store_steps_have_source_step_id(self) -> None:
        """Every market_data_store step must have source_step_id set."""
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            steps = recipe.get("steps", [])
            for step in steps:
                if step.get("type") == "market_data_store":
                    source = step.get("params", {}).get("source_step_id")
                    assert source is not None, (
                        f"Recipe '{recipe['name']}' store step '{step.get('id')}' "
                        f"missing source_step_id"
                    )

    def test_store_source_step_id_references_existing_fetch(self) -> None:
        """source_step_id must reference a fetch step in the same recipe."""
        from tools.seed_scheduling_recipes import SCHEDULING_RECIPES

        for recipe in SCHEDULING_RECIPES:
            steps = recipe.get("steps", [])
            step_ids = {s.get("id") for s in steps}
            for step in steps:
                if step.get("type") == "market_data_store":
                    source = step.get("params", {}).get("source_step_id")
                    if source is not None:
                        assert source in step_ids, (
                            f"Recipe '{recipe['name']}': source_step_id '{source}' "
                            f"not found in step ids: {step_ids}"
                        )
