# Re-export the stable tool surface used by scripts, tests, and agent callers.
from .macro_math import (
    IngredientNotFoundError,
    InvalidQuantityError,
    MacroTotals,
    calculate_macros,
    get_ingredient,
)
from .scaling import (
    ConstraintTargetError,
    InvalidScaleFactorError,
    ScaledIngredient,
    ScaledRecipe,
    scale_ingredient_by_factor,
    scale_ingredient_to_quantity,
    scale_for_servings,
    scale_recipe_to_targets,
)
from .meal_planner import (
    InvalidPlannerResponse,
    MealPlanRequest,
    MealPlanResult,
    MealPlanningAgent,
    OllamaBackend,
    deterministic_plan,
    filter_recipes,
    load_recipes,
    recipe_rejection_reason,
)

__all__ = [
    "IngredientNotFoundError",
    "InvalidQuantityError",
    "ConstraintTargetError",
    "InvalidScaleFactorError",
    "MacroTotals",
    "ScaledIngredient",
    "ScaledRecipe",
    "calculate_macros",
    "get_ingredient",
    "scale_ingredient_by_factor",
    "scale_ingredient_to_quantity",
    "scale_for_servings",
    "scale_recipe_to_targets",
    "InvalidPlannerResponse",
    "MealPlanRequest",
    "MealPlanResult",
    "MealPlanningAgent",
    "OllamaBackend",
    "deterministic_plan",
    "filter_recipes",
    "load_recipes",
    "recipe_rejection_reason",
]
