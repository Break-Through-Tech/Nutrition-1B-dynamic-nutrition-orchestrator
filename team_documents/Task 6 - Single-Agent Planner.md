# Single-Agent Meal Planner

> **Task naming:** The challenge brief describes the single-agent planner as part of its first phase.

## Goal

The planner accepts dietary and scheduling requirements, chooses only from the local recipe bank, scales numeric ingredient quantities to the requested servings, and calculates nutrition using the existing deterministic macro tool. Optional Ollama ranking can influence recipe preference, but it cannot bypass restriction filters or provide macro values.

## Requesting a Plan

The public types are exported from `nutrition_engine`:

```python
from pathlib import Path

from nutrition_engine import (
    MealPlanningAgent,
    WeeklyMealPlanRequest,
    load_recipes,
)

recipes = load_recipes(Path("data/recipes.json"))
agent = MealPlanningAgent(recipes)
request = WeeklyMealPlanRequest(
    restrictions=("vegetarian",),
    excluded_ingredients=("peanut",),
    meal_types=("breakfast", "lunch", "dinner"),
    days=7,
    servings=1,
    target_protein_g_per_day=140,
    max_calories_per_day=2000,
    no_repeat_days=2,
)
plan = agent.plan_week(request).to_dict()
```

`days=1` produces a single-day plan. `no_repeat_days=2` prohibits an ingredient from appearing in two adjacent planned days and also prevents duplicate ingredients between meals on the same day. Set it to `0` to disable ingredient-repeat checks. Protein is treated as a minimum; calories are treated as a maximum. Either target can be set to `None` to disable that check.

## Planning Flow

1. `load_recipes` reads the local JSON recipe list.
2. Existing restriction checks remove recipes conflicting with requested dietary restrictions. Unsupported restrictions are rejected instead of silently ignored.
3. Excluded-ingredient terms remove recipes containing a matching normalized ingredient name.
4. The planner gathers candidates for each requested meal type. The optional backend ranks safe recipe IDs; responses are validated, and deterministic ordering is used if the backend is unavailable or returns an invalid selection.
5. The planner considers compatible recipe combinations for that day. It prefers filling all requested meal slots, then favors recipes with complete macro data, plans meeting configured targets, lower calorie excess, and backend preference order. It does not relax ingredient-repeat rules to fill a slot.
6. Selected recipes are scaled to the requested servings. Numeric ingredient quantities are multiplied by `requested servings / recipe servings`.
7. The injected macro calculator (by default `calculate_macros`) calculates calories, protein, carbohydrates, and fat from canonical ingredient data. Nutrition is returned only when all recipe ingredients have gram quantities and can be resolved by the calculator.
8. Daily and weekly totals are emitted. If any selected meal has unresolved nutrition data or a requested slot is unfilled, the affected totals and target-compliance status are marked incomplete/unknown and a warning explains why.

## Output Shape

`WeeklyMealPlanResult.to_dict()` returns:

- `days`: ordered day records. Each contains selected meals, unfilled meal types, daily nutrition totals, target status, and warnings.
- `weekly_totals`: aggregate nutrition totals, or `None` values when a complete weekly total cannot be verified.
- `rejected`: recipe IDs excluded by dietary restrictions or excluded ingredients, with reasons.
- `source`: `deterministic`, `llm`, or `deterministic-fallback`.
- `warnings`: deduplicated warnings gathered across the plan.

Each meal includes its meal type, a serving-scaled recipe copy, and nutrition details. Per-recipe nutrition includes a `complete` flag and the list of unresolved ingredients. No recipe in the source seed data is mutated.

## Code Map

- `src/nutrition_engine/meal_planner.py`: request/result models, recipe loading and safety filters, optional Ollama selector, nutrition aggregation, serving scaling, and daily/weekly scheduling.
- `src/nutrition_engine/macro_math.py`: deterministic per-ingredient nutrition calculations used by the planner. It and `scaling.py` defer annotation evaluation so Python 3.9 can import their union type annotations.
- `src/nutrition_engine/scaling.py`: existing ingredient and recipe scaling utilities. The planner scales a recipe's stored ingredient quantities directly for the requested serving count; target-based recipe scaling remains a separate tool.
- `src/nutrition_engine/__init__.py`: public exports for planner request/result types and helpers.
- `tests/test_meal_planner.py`: tests for restriction filtering, optional backend guardrails, serving scaling, macro totals, incomplete nutrition, no-repeat scheduling, and selecting compatible meal combinations.
- `README.md`: short user-facing planner description and nutrition-data caveat.
- `src/nutrition_engine/benchmarks.py`: postponed annotation evaluation for Python 3.9 compatibility.

## Current Data Limitation

The planner does not resolve recipe ingredients to USDA records itself. Its default macro calculator uses the small canonical catalog in `nutrition_engine.ingredients`; many seed recipes have ingredients absent from that catalog or use units such as teaspoons and pieces. For those recipes, the plan can still select and schedule a recipe, but it reports nutrition totals and target compliance as unknown. To verify macros for the full seed bank, connect Task 6 ingredient matching and USDA nutrient records through a macro-calculator/catalog adapter and normalize recipe quantities to grams. Unknown values must not be replaced with guessed values.

Ingredient repeat and exclusion checks currently compare normalized ingredient-name text, not semantic ingredient identities. Synonyms and variant names may therefore need canonicalization from the ingredient-matching pipeline before they can be treated as the same ingredient.

The strict repeat window can leave requested meal slots empty when the recipe bank has no compatible combination. This occurs in the current vegetarian seed bank: all lunch candidates share oil with most breakfast candidates, so some adjacent days cannot fill both slots without violating the rule. The planner reports these unfilled slots rather than weakening the constraint; expanding or normalizing the recipe bank is needed for complete schedules.

## Validation

From the repository root, run:

```bash
.venv/bin/python -m pytest tests/test_meal_planner.py
.venv/bin/python -m pytest
```
