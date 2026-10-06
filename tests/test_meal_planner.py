import json
from pathlib import Path

import pytest

from nutrition_engine.meal_planner import (
    MealPlanRequest,
    MealPlanningAgent,
    WeeklyMealPlanRequest,
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


def measured_recipe(recipe_id, name, meal_type, ingredient_name, quantity=100):
    return {
        "recipe_id": recipe_id,
        "name": name,
        "meal_type": meal_type,
        "servings": 1,
        "ingredients": [{"name": ingredient_name, "quantity": quantity, "unit": "g"}],
    }


def test_weekly_agent_scales_servings_calculates_macros_and_avoids_recent_ingredients():
    recipes = [
        measured_recipe("breakfast-yogurt", "Yogurt", "breakfast", "greek yogurt"),
        measured_recipe("breakfast-egg", "Egg", "breakfast", "egg"),
        measured_recipe("lunch-tofu", "Tofu", "lunch", "tofu"),
        measured_recipe("lunch-beans", "Beans", "lunch", "black beans"),
        measured_recipe("dinner-salmon", "Salmon", "dinner", "salmon"),
        measured_recipe("dinner-rice", "Rice", "dinner", "brown rice"),
    ]

    result = MealPlanningAgent(recipes).plan_week(
        WeeklyMealPlanRequest(days=2, servings=2, target_protein_g_per_day=40)
    )

    assert result.weekly_totals["complete"] is True
    assert all(day["nutrition"]["targets_met"] is True for day in result.days)
    assert result.days[0]["meals"][0]["recipe"]["servings"] == 2
    assert result.days[0]["meals"][0]["recipe"]["ingredients"][0]["quantity"] == 200
    first_day_ingredients = {
        item["name"] for meal in result.days[0]["meals"] for item in meal["recipe"]["ingredients"]
    }
    second_day_ingredients = {
        item["name"] for meal in result.days[1]["meals"] for item in meal["recipe"]["ingredients"]
    }
    assert first_day_ingredients.isdisjoint(second_day_ingredients)


def test_weekly_agent_marks_unresolved_macro_totals_unknown():
    recipes = [measured_recipe("oats", "Oats", "breakfast", "oats")]

    result = MealPlanningAgent(recipes).plan_week(
        WeeklyMealPlanRequest(days=1, meal_types=("breakfast",))
    )

    assert result.days[0]["nutrition"]["complete"] is False
    assert result.days[0]["nutrition"]["protein_g"] is None
    assert result.days[0]["nutrition"]["targets_met"] is None
    assert "oats" in result.days[0]["meals"][0]["nutrition"]["unresolved_ingredients"]


def test_weekly_agent_leaves_slot_empty_when_repeat_window_blocks_only_recipe():
    recipes = [measured_recipe("tofu", "Tofu", "lunch", "tofu")]

    result = MealPlanningAgent(recipes).plan_week(
        WeeklyMealPlanRequest(days=2, meal_types=("lunch",), no_repeat_days=2)
    )

    assert len(result.days[0]["meals"]) == 1
    assert result.days[1]["meals"] == []
    assert result.days[1]["unfilled_meals"] == ["lunch"]
    assert any("ingredient-repeat constraints" in warning for warning in result.warnings)


def test_weekly_agent_finds_compatible_meal_combination_before_leaving_slot_empty():
    recipes = [
        recipe("breakfast-oil", "Breakfast with oil", ["oil"], "breakfast"),
        recipe("breakfast-egg", "Breakfast with egg", ["egg"], "breakfast"),
        recipe("lunch-oil", "Lunch with oil", ["oil"], "lunch"),
    ]

    result = MealPlanningAgent(recipes).plan_week(
        WeeklyMealPlanRequest(
            days=1,
            meal_types=("breakfast", "lunch"),
            target_protein_g_per_day=None,
            max_calories_per_day=None,
        )
    )

    assert result.days[0]["unfilled_meals"] == []
    assert [meal["recipe"]["recipe_id"] for meal in result.days[0]["meals"]] == [
        "breakfast-egg",
        "lunch-oil",
    ]