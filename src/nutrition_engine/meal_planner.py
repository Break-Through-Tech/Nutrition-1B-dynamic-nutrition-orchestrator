"""Restriction-aware recipe planning with a deterministic fallback.

The planner treats recipe selection and nutrient arithmetic as separate concerns.
It never invents nutrient values for recipe ingredients that are absent from the
canonical nutrition catalog.
"""
from __future__ import annotations

import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Callable, Protocol, Sequence

from .macro_math import IngredientNotFoundError, InvalidQuantityError, MacroTotals, calculate_macros


RESTRICTION_TERMS: dict[str, tuple[str, ...]] = {
    # These terms are conservative rejection rules; unresolved nutrition data
    # is handled separately by the deterministic macro engine.
    "vegetarian": ("chicken", "beef", "pork", "lamb", "fish", "salmon", "meat"),
    "vegan": (
        "chicken", "beef", "pork", "lamb", "fish", "salmon", "meat", "paneer",
        "yogurt", "curd", "milk", "whey", "cheese", "ghee", "butter", "egg",
    ),
    "dairy free": (
        "paneer", "yogurt", "curd", "milk", "whey", "cheese", "ghee", "butter",
    ),
    "nut free": ("almond", "peanut", "cashew", "walnut", "nut"),
    "gluten free": (
        "wheat", "atta", "bread", "flour", "roti", "paratha", "tortilla",
    ),
}


class PlannerBackend(Protocol):
    def choose_recipe_ids(
        self, request: "MealPlanRequest", candidates: Sequence[dict]
    ) -> list[str]: ...


class InvalidPlannerResponse(ValueError):
    pass


@dataclass(frozen=True)
class MealPlanRequest:
    restrictions: tuple[str, ...] = ()
    meal_type: str | None = None
    servings: int = 1
    max_recipes: int = 3

    def __post_init__(self) -> None:
        if self.servings <= 0:
            raise ValueError("Servings must be greater than zero.")
        if self.max_recipes <= 0:
            raise ValueError("max_recipes must be greater than zero.")


@dataclass(frozen=True)
class MealPlanResult:
    recipes: tuple[dict, ...]
    rejected: tuple[dict[str, str], ...]
    source: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "recipes": list(self.recipes),
            "rejected": list(self.rejected),
            "source": self.source,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class WeeklyMealPlanRequest:
    restrictions: tuple[str, ...] = ()
    excluded_ingredients: tuple[str, ...] = ()
    meal_types: tuple[str, ...] = ("breakfast", "lunch", "dinner")
    days: int = 7
    servings: int = 1
    target_protein_g_per_day: float | None = 140.0
    max_calories_per_day: float | None = 2_000.0
    no_repeat_days: int = 2

    def __post_init__(self) -> None:
        if self.days <= 0:
            raise ValueError("days must be greater than zero.")
        if self.servings <= 0:
            raise ValueError("servings must be greater than zero.")
        if self.no_repeat_days < 0:
            raise ValueError("no_repeat_days cannot be negative.")
        if not self.meal_types or any(not meal_type.strip() for meal_type in self.meal_types):
            raise ValueError("At least one non-empty meal type is required.")
        if len({normalize_text(meal_type) for meal_type in self.meal_types}) != len(self.meal_types):
            raise ValueError("meal_types cannot contain duplicates.")
        for target in (self.target_protein_g_per_day, self.max_calories_per_day):
            if target is not None and target <= 0:
                raise ValueError("Nutrition targets must be greater than zero.")
        if any(not ingredient.strip() for ingredient in self.excluded_ingredients):
            raise ValueError("Excluded ingredients cannot be empty.")


@dataclass(frozen=True)
class WeeklyMealPlanResult:
    days: tuple[dict, ...]
    weekly_totals: dict[str, float | bool | None]
    rejected: tuple[dict[str, str], ...]
    source: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "days": list(self.days),
            "weekly_totals": self.weekly_totals,
            "rejected": list(self.rejected),
            "source": self.source,
            "warnings": list(self.warnings),
        }


def _recipe_nutrition(
    recipe: dict,
    servings: int,
    macro_calculator: Callable[[str, float], MacroTotals],
) -> dict:
    unresolved: list[str] = []
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    ingredients = recipe.get("ingredients", [])
    try:
        recipe_servings = float(recipe.get("servings", 1))
        if recipe_servings <= 0:
            raise ValueError
        scale = servings / recipe_servings
    except (TypeError, ValueError, ZeroDivisionError):
        scale = 1.0
        unresolved.append("recipe servings")

    if not ingredients:
        unresolved.append("recipe ingredients")

    for ingredient in ingredients:
        name = ingredient.get("name", "")
        quantity = ingredient.get("quantity")
        unit = normalize_text(ingredient.get("unit") or "")
        if not isinstance(name, str) or not name.strip():
            unresolved.append("unnamed ingredient")
            continue
        if unit not in {"g", "gram", "grams"} or quantity is None:
            unresolved.append(name)
            continue
        try:
            macros = macro_calculator(name, float(quantity) * scale)
        except (IngredientNotFoundError, InvalidQuantityError, KeyError, TypeError, ValueError):
            unresolved.append(name)
            continue
        totals["calories"] += macros.calories
        totals["protein_g"] += macros.protein_g
        totals["carbs_g"] += macros.carbs_g
        totals["fat_g"] += macros.fat_g

    complete = not unresolved
    return {
        "complete": complete,
        "calories": round(totals["calories"], 2) if complete else None,
        "protein_g": round(totals["protein_g"], 2) if complete else None,
        "carbs_g": round(totals["carbs_g"], 2) if complete else None,
        "fat_g": round(totals["fat_g"], 2) if complete else None,
        "unresolved_ingredients": sorted(set(unresolved)),
    }


def _recipe_for_servings(recipe: dict, servings: int) -> dict:
    scaled = dict(recipe)
    try:
        factor = servings / float(recipe.get("servings", 1))
    except (TypeError, ValueError, ZeroDivisionError):
        factor = 1.0
    scaled_ingredients = []
    for ingredient in recipe.get("ingredients", []):
        scaled_ingredient = dict(ingredient)
        quantity = scaled_ingredient.get("quantity")
        if isinstance(quantity, (int, float)):
            scaled_ingredient["quantity"] = round(quantity * factor, 2)
        scaled_ingredients.append(scaled_ingredient)
    scaled["ingredients"] = scaled_ingredients
    scaled["servings"] = servings
    return scaled


class OllamaBackend:
    """Optional local Ollama selector; nutrient math remains deterministic."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        endpoint: str = "http://localhost:11434/api/generate",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def choose_recipe_ids(
        self, request: MealPlanRequest, candidates: Sequence[dict]
    ) -> list[str]:
        candidate_ids = [recipe.get("recipe_id") for recipe in candidates]
        # Send IDs rather than raw recipe text so the model ranks known records
        # and cannot invent a recipe that bypasses restriction filtering.
        prompt = (
            "Choose recipes only from the candidate IDs below. Return JSON only "
            "in the form {\"recipe_ids\":[...]} with no explanation.\n"
            f"Restrictions: {list(request.restrictions)}\n"
            f"Meal type: {request.meal_type}\n"
            f"Candidate IDs: {candidate_ids}"
        )
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request_object = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request_object, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError) as error:
            raise ConnectionError("Ollama is unavailable.") from error

        # Ollama may wrap JSON in a Markdown fence despite the prompt.
        response_text = response_payload.get("response", "").strip()
        response_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text).strip()
        try:
            selected = json.loads(response_text).get("recipe_ids")
        except (AttributeError, TypeError, json.JSONDecodeError) as error:
            raise InvalidPlannerResponse("Ollama did not return valid recipe JSON.") from error
        if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
            raise InvalidPlannerResponse("Ollama recipe_ids must be a list of strings.")
        return selected


def normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def load_recipes(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as recipe_file:
        payload = json.load(recipe_file)
    if not isinstance(payload, list):
        raise ValueError("Recipe database must contain a JSON list.")
    return payload


def _restriction_conflict(recipe: dict, restriction: str) -> str | None:
    normalized_restriction = normalize_text(restriction)
    terms = RESTRICTION_TERMS.get(normalized_restriction)
    if terms is None:
        raise ValueError(f"Unsupported dietary restriction: {restriction}")

    ingredient_text = " ".join(
        normalize_text(ingredient.get("name", ""))
        for ingredient in recipe.get("ingredients", [])
    )
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", ingredient_text):
            return f"contains {term}"
    return None


def recipe_rejection_reason(recipe: dict, request: MealPlanRequest) -> str | None:
    if request.meal_type and normalize_text(recipe.get("meal_type", "")) != normalize_text(request.meal_type):
        return f"meal type is {recipe.get('meal_type', 'unspecified')}"

    for restriction in request.restrictions:
        conflict = _restriction_conflict(recipe, restriction)
        if conflict:
            return f"{restriction}: {conflict}"
    return None


def filter_recipes(recipes: Sequence[dict], request: MealPlanRequest) -> tuple[list[dict], list[dict[str, str]]]:
    accepted: list[dict] = []
    rejected: list[dict[str, str]] = []
    # Preserve rejection reasons so a UI or agent can explain why a recipe was
    # excluded instead of hiding the decision.
    for recipe in recipes:
        reason = recipe_rejection_reason(recipe, request)
        if reason is None:
            accepted.append(recipe)
        else:
            rejected.append({"recipe_id": recipe.get("recipe_id", ""), "reason": reason})
    return accepted, rejected


def deterministic_plan(recipes: Sequence[dict], request: MealPlanRequest) -> MealPlanResult:
    accepted, rejected = filter_recipes(recipes, request)
    selected = tuple(accepted[: request.max_recipes])
    warnings = () if selected else ("No recipes satisfy the requested restrictions.",)
    return MealPlanResult(selected, tuple(rejected), "deterministic", warnings)


class MealPlanningAgent:
    """Plan meals with optional recipe ranking and deterministic nutrition math."""

    def __init__(
        self,
        recipes: Sequence[dict],
        backend: PlannerBackend | None = None,
        macro_calculator: Callable[[str, float], MacroTotals] = calculate_macros,
    ) -> None:
        self.recipes = tuple(recipes)
        self.backend = backend
        self.macro_calculator = macro_calculator

    def plan(self, request: MealPlanRequest) -> MealPlanResult:
        accepted, rejected = filter_recipes(self.recipes, request)
        if self.backend is None:
            return deterministic_plan(self.recipes, request)

        try:
            # The backend sees only safe candidates; its response is validated
            # again before any recipe is returned to the caller.
            chosen_ids = self.backend.choose_recipe_ids(request, accepted)
            accepted_by_id = {recipe.get("recipe_id"): recipe for recipe in accepted}
            selected = []
            for recipe_id in chosen_ids:
                recipe = accepted_by_id.get(recipe_id)
                if recipe is None:
                    raise InvalidPlannerResponse(
                        f"Backend selected unknown or restricted recipe: {recipe_id}"
                    )
                if recipe not in selected:
                    selected.append(recipe)
            if not selected:
                raise InvalidPlannerResponse("Backend returned no recipes.")
            return MealPlanResult(
                tuple(selected[: request.max_recipes]), tuple(rejected), "llm",
            )
        except (InvalidPlannerResponse, ConnectionError, TimeoutError, ValueError) as error:
            # Local LLMs are optional. A failed model call must not make meal
            # planning unavailable or weaken the deterministic guardrails.
            fallback = deterministic_plan(self.recipes, request)
            return MealPlanResult(
                fallback.recipes,
                fallback.rejected,
                "deterministic-fallback",
                (f"LLM selection unavailable: {error}",),
            )

    def plan_week(self, request: WeeklyMealPlanRequest) -> WeeklyMealPlanResult:
        safe_recipes, rejected = filter_recipes(
            self.recipes,
            MealPlanRequest(restrictions=request.restrictions, max_recipes=max(1, len(self.recipes))),
        )
        excluded_terms = tuple(normalize_text(item) for item in request.excluded_ingredients)
        eligible_recipes = []
        for recipe in safe_recipes:
            ingredient_names = [
                normalize_text(ingredient.get("name", ""))
                for ingredient in recipe.get("ingredients", [])
            ]
            conflict = next(
                (term for term in excluded_terms if any(term in name for name in ingredient_names)),
                None,
            )
            if conflict:
                rejected.append({
                    "recipe_id": recipe.get("recipe_id", ""),
                    "reason": f"excluded ingredient: {conflict}",
                })
            else:
                eligible_recipes.append(recipe)

        nutrition_cache: dict[int, dict] = {}
        ingredient_history: list[set[str]] = []
        planned_days: list[dict] = []
        warnings: list[str] = []
        sources: set[str] = set()

        for day_number in range(1, request.days + 1):
            day_meals: list[dict] = []
            day_ingredients: set[str] = set()
            day_warnings: list[str] = []
            day_calories = 0.0
            day_protein = 0.0
            day_complete = True
            unfilled_meals: list[str] = []
            history_length = max(0, request.no_repeat_days - 1)
            recent_ingredients = set().union(*ingredient_history[-history_length:]) if history_length else set()
            meal_options: list[tuple[str, list[dict], list[tuple[tuple[float, ...], dict, dict, set[str]]]]] = []

            for meal_type in request.meal_types:
                candidates, _ = filter_recipes(
                    eligible_recipes,
                    MealPlanRequest(meal_type=meal_type, max_recipes=max(1, len(eligible_recipes))),
                )
                if not candidates:
                    meal_options.append((meal_type, candidates, []))
                    continue

                ranked = MealPlanningAgent(candidates, self.backend).plan(
                    MealPlanRequest(
                        restrictions=request.restrictions,
                        meal_type=meal_type,
                        max_recipes=len(candidates),
                    )
                )
                sources.add(ranked.source)
                day_warnings.extend(ranked.warnings)
                ranked_ids = {recipe.get("recipe_id") for recipe in ranked.recipes}
                ordered_candidates = list(ranked.recipes) + [
                    recipe for recipe in candidates if recipe.get("recipe_id") not in ranked_ids
                ]

                choices: list[tuple[tuple[float, ...], dict, dict, set[str]]] = []
                for index, recipe in enumerate(ordered_candidates):
                    recipe_ingredients = {
                        normalize_text(ingredient.get("name", ""))
                        for ingredient in recipe.get("ingredients", [])
                        if normalize_text(ingredient.get("name", ""))
                    }
                    if request.no_repeat_days and recipe_ingredients & recent_ingredients:
                        continue
                    nutrition = nutrition_cache.setdefault(
                        id(recipe),
                        _recipe_nutrition(recipe, request.servings, self.macro_calculator),
                    )
                    score = (float(nutrition["complete"]), -float(index))
                    choices.append((score, recipe, nutrition, recipe_ingredients))
                meal_options.append((meal_type, candidates, choices))

            best_combo = None
            best_score = None
            option_sets = [choices + [None] for _, _, choices in meal_options]
            for combo in product(*option_sets):
                used_ingredients = set(recent_ingredients)
                compatible = True
                for choice in combo:
                    if choice is None:
                        continue
                    recipe_ingredients = choice[3]
                    if request.no_repeat_days and recipe_ingredients & used_ingredients:
                        compatible = False
                        break
                    used_ingredients.update(recipe_ingredients)
                if not compatible:
                    continue

                selected = [choice for choice in combo if choice is not None]
                complete_choices = [choice for choice in selected if choice[2]["complete"]]
                all_slots_filled = len(selected) == len(request.meal_types)
                all_macros_complete = all_slots_filled and len(complete_choices) == len(selected)
                calories = sum(choice[2]["calories"] for choice in complete_choices)
                protein = sum(choice[2]["protein_g"] for choice in complete_choices)
                checks = []
                if request.target_protein_g_per_day is not None:
                    checks.append(protein >= request.target_protein_g_per_day)
                if request.max_calories_per_day is not None:
                    checks.append(calories <= request.max_calories_per_day)
                targets_met = all(checks) if checks and all_macros_complete else False
                calorie_excess = max(0.0, calories - request.max_calories_per_day) if request.max_calories_per_day is not None else 0.0
                rank_preference = tuple(choice[0][-1] if choice is not None else -1_000_000.0 for choice in combo)
                score = (
                    len(selected),
                    len(complete_choices),
                    float(targets_met),
                    -calorie_excess,
                    rank_preference,
                )
                if best_score is None or score > best_score:
                    best_combo = combo
                    best_score = score

            for (meal_type, candidates, choices), choice in zip(meal_options, best_combo or ()):
                if choice is None:
                    unfilled_meals.append(meal_type)
                    day_complete = False
                    if not candidates:
                        day_warnings.append(f"No recipe available for {meal_type}.")
                    else:
                        day_warnings.append(
                            f"No {meal_type} recipe fits the dietary and {request.no_repeat_days}-day ingredient-repeat constraints."
                        )
                    continue

                _, chosen_recipe, nutrition, chosen_ingredients = choice
                day_ingredients.update(chosen_ingredients)
                day_meals.append({
                    "meal_type": meal_type,
                    "recipe": _recipe_for_servings(chosen_recipe, request.servings),
                    "nutrition": nutrition,
                })
                if nutrition["complete"]:
                    day_calories += nutrition["calories"]
                    day_protein += nutrition["protein_g"]
                else:
                    day_complete = False
                    unresolved = ", ".join(nutrition["unresolved_ingredients"])
                    day_warnings.append(f"{chosen_recipe.get('name', 'Recipe')}: macros unavailable for {unresolved}.")

            totals_complete = day_complete and len(day_meals) == len(request.meal_types)
            targets_met = None
            if totals_complete:
                checks = []
                if request.target_protein_g_per_day is not None:
                    checks.append(day_protein >= request.target_protein_g_per_day)
                if request.max_calories_per_day is not None:
                    checks.append(day_calories <= request.max_calories_per_day)
                targets_met = all(checks) if checks else None
                if targets_met is False:
                    day_warnings.append("Daily nutrition targets were not met.")
            else:
                day_warnings.append("Daily macro totals and target compliance cannot be verified.")

            planned_days.append({
                "day": day_number,
                "meals": day_meals,
                "unfilled_meals": unfilled_meals,
                "nutrition": {
                    "complete": totals_complete,
                    "calories": round(day_calories, 2) if totals_complete else None,
                    "protein_g": round(day_protein, 2) if totals_complete else None,
                    "carbs_g": round(sum(meal["nutrition"]["carbs_g"] for meal in day_meals), 2) if totals_complete else None,
                    "fat_g": round(sum(meal["nutrition"]["fat_g"] for meal in day_meals), 2) if totals_complete else None,
                    "targets_met": targets_met,
                },
                "warnings": day_warnings,
            })
            warnings.extend(day_warnings)
            if request.no_repeat_days > 1:
                ingredient_history.append(day_ingredients)
                ingredient_history = ingredient_history[-(request.no_repeat_days - 1):]

        weekly_complete = all(day["nutrition"]["complete"] for day in planned_days)
        weekly_totals = {
            "complete": weekly_complete,
            "calories": round(sum(day["nutrition"]["calories"] for day in planned_days), 2) if weekly_complete else None,
            "protein_g": round(sum(day["nutrition"]["protein_g"] for day in planned_days), 2) if weekly_complete else None,
            "carbs_g": round(sum(day["nutrition"]["carbs_g"] for day in planned_days), 2) if weekly_complete else None,
            "fat_g": round(sum(day["nutrition"]["fat_g"] for day in planned_days), 2) if weekly_complete else None,
        }
        if "llm" in sources and len(sources) == 1:
            source = "llm"
        elif "deterministic-fallback" in sources:
            source = "deterministic-fallback"
        else:
            source = "deterministic"

        return WeeklyMealPlanResult(
            days=tuple(planned_days),
            weekly_totals=weekly_totals,
            rejected=tuple(rejected),
            source=source,
            warnings=tuple(dict.fromkeys(warnings)),
        )


__all__ = [
    "InvalidPlannerResponse",
    "MealPlanRequest",
    "MealPlanResult",
    "MealPlanningAgent",
    "OllamaBackend",
    "PlannerBackend",
    "WeeklyMealPlanRequest",
    "WeeklyMealPlanResult",
    "deterministic_plan",
    "filter_recipes",
    "load_recipes",
    "recipe_rejection_reason",
]
