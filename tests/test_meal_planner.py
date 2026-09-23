import json
from pathlib import Path

import pytest

from nutrition_engine.meal_planner import (
    MealPlanRequest,
    MealPlanningAgent,
    deterministic_plan,
    filter_recipes,
    load_recipes,
)


RECIPE_DATA = Path(__file__).parents[1] / "data" / "recipes.json"


def recipe(recipe_id, name, ingredients, meal_type="lunch"):
    return {
        "recipe_id": recipe_id,
        "name": name,
        "meal_type": meal_type,
        "ingredients": [{"name": ingredient} for ingredient in ingredients],
    }


def test_restriction_filter_rejects_dairy_and_keeps_tofu():
    # Filtering must reject conflicting ingredients without removing safe ones.
    recipes = [
        recipe("paneer-bowl", "Paneer Bowl", ["low-fat paneer"]),
        recipe("tofu-bowl", "Tofu Bowl", ["firm tofu", "broccoli"]),
    ]

    accepted, rejected = filter_recipes(
        recipes,
        MealPlanRequest(restrictions=("dairy-free",)),
    )

    assert [item["recipe_id"] for item in accepted] == ["tofu-bowl"]
    assert rejected == [{"recipe_id": "paneer-bowl", "reason": "dairy-free: contains paneer"}]


def test_real_seed_database_can_be_loaded_and_filtered():
    # Verify the planner works with the actual repository recipe seed bank.
    recipes = load_recipes(RECIPE_DATA)
    result = deterministic_plan(
        recipes,
        MealPlanRequest(restrictions=("vegetarian",), meal_type="breakfast"),
    )

    assert len(recipes) == 26
    assert result.recipes
    assert all(item["meal_type"] == "breakfast" for item in result.recipes)


class SelectingBackend:
    def choose_recipe_ids(self, request, candidates):
        return [candidates[-1]["recipe_id"]]


def test_backend_can_select_only_from_guardrailed_candidates():
    # A backend can rank candidates, but cannot bypass deterministic filters.
    recipes = [
        recipe("dairy", "Dairy", ["paneer"]),
        recipe("safe", "Safe", ["tofu"]),
    ]
    result = MealPlanningAgent(recipes, SelectingBackend()).plan(
        MealPlanRequest(restrictions=("dairy-free",))
    )

    assert result.source == "llm"
    assert [item["recipe_id"] for item in result.recipes] == ["safe"]


class InvalidBackend:
    def choose_recipe_ids(self, request, candidates):
        return ["not-in-candidates"]


def test_invalid_backend_response_falls_back_to_deterministic_plan():
    # Model failures must degrade to a usable deterministic result.
    recipes = [recipe("safe", "Safe", ["tofu"])]
    result = MealPlanningAgent(recipes, InvalidBackend()).plan(MealPlanRequest())

    assert result.source == "deterministic-fallback"
    assert result.recipes[0]["recipe_id"] == "safe"
    assert result.warnings


def test_unknown_restriction_is_rejected():
    with pytest.raises(ValueError, match="Unsupported dietary restriction"):
        filter_recipes([recipe("x", "X", ["tofu"])], MealPlanRequest(restrictions=("keto",)))