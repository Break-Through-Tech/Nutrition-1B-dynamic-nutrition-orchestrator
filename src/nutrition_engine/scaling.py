from dataclasses import dataclass

from .macro_math import MacroTotals, calculate_macros, validate_quantity_g


class InvalidScaleFactorError(ValueError):
    pass


class ConstraintTargetError(ValueError):
    pass


@dataclass(frozen=True)
class ScaledIngredient:
    ingredient: str
    original_quantity_g: float
    scaled_quantity_g: float
    scale_factor: float
    macros: MacroTotals

    def to_dict(self) -> dict[str, float | str | dict[str, float | str]]:
        # Nested macro output keeps the original quantity and derived quantity
        # together when this object crosses an API or agent boundary.
        return {
            "ingredient": self.ingredient,
            "original_quantity_g": self.original_quantity_g,
            "scaled_quantity_g": self.scaled_quantity_g,
            "scale_factor": self.scale_factor,
            "macros": self.macros.to_dict(),
        }


@dataclass(frozen=True)
class ScaledRecipe:
    ingredients: tuple[ScaledIngredient, ...]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

    def to_dict(self) -> dict[str, list[dict] | float]:
        return {
            "ingredients": [ingredient.to_dict() for ingredient in self.ingredients],
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
        }


def validate_scale_factor(scale_factor: float) -> float:
    try:
        factor = float(scale_factor)
    except (TypeError, ValueError) as error:
        raise InvalidScaleFactorError(
            "Scale factor must be a numeric value."
        ) from error

    if factor <= 0:
        raise InvalidScaleFactorError(
            "Scale factor must be greater than zero."
        )

    return factor


def scale_ingredient_by_factor(
    ingredient_name: str,
    original_quantity_g: float,
    scale_factor: float,
) -> ScaledIngredient:
    """
    Example:
    100g chicken breast scaled by 1.5 becomes 150g chicken breast.
    """
    original_grams = validate_quantity_g(original_quantity_g)
    factor = validate_scale_factor(scale_factor)
    # Recalculate from the canonical ingredient record instead of scaling an
    # already rounded MacroTotals instance.
    scaled_grams = original_grams * factor
    macros = calculate_macros(ingredient_name, scaled_grams)

    return ScaledIngredient(
        ingredient=macros.ingredient,
        original_quantity_g=round(original_grams, 2),
        scaled_quantity_g=round(scaled_grams, 2),
        scale_factor=round(factor, 4),
        macros=macros,
    )


def scale_ingredient_to_quantity(
    ingredient_name: str,
    original_quantity_g: float,
    target_quantity_g: float,
) -> ScaledIngredient:
    """
    Example:
    Change chicken breast from 120g to 300g.
    """
    original_grams = validate_quantity_g(original_quantity_g)
    target_grams = validate_quantity_g(target_quantity_g)
    factor = target_grams / original_grams

    return scale_ingredient_by_factor(
        ingredient_name=ingredient_name,
        original_quantity_g=original_grams,
        scale_factor=factor,
    )


def scale_for_servings(
    ingredient_name: str,
    original_quantity_g: float,
    original_servings: int,
    target_servings: int,
) -> ScaledIngredient:
    """
    Example:
    200g of salmon for 2 servings -> 500g for 5 servings.
    """
    if not isinstance(original_servings, int) or original_servings <= 0:
        raise ValueError("Original servings must be a positive integer.")

    if not isinstance(target_servings, int) or target_servings <= 0:
        raise ValueError("Target servings must be a positive integer.")

    serving_scale_factor = target_servings / original_servings

    return scale_ingredient_by_factor(
        ingredient_name=ingredient_name,
        original_quantity_g=original_quantity_g,
        scale_factor=serving_scale_factor,
    )


def scale_recipe_to_targets(
    ingredients: list[tuple[str, float]],
    target_protein_g: float = 140.0,
    max_calories: float = 2_000.0,
) -> ScaledRecipe:
    """Uniformly scale a recipe to a protein minimum under a calorie cap."""
    if not ingredients:
        raise ConstraintTargetError("Recipe must contain at least one ingredient.")

    try:
        protein_target = float(target_protein_g)
        calorie_limit = float(max_calories)
    except (TypeError, ValueError) as error:
        raise ConstraintTargetError("Targets must be numeric values.") from error

    if protein_target <= 0 or calorie_limit <= 0:
        raise ConstraintTargetError("Targets must be greater than zero.")

    # Establish the unscaled recipe totals before selecting one uniform factor.
    base_ingredients = [
        calculate_macros(ingredient_name, quantity_g)
        for ingredient_name, quantity_g in ingredients
    ]
    base_protein = sum(item.protein_g for item in base_ingredients)
    base_calories = sum(item.calories for item in base_ingredients)

    if base_protein <= 0:
        raise ConstraintTargetError("Recipe must contain protein.")

    # Scaling only upward preserves an already-sufficient recipe while meeting
    # the protein minimum with the smallest possible calorie increase.
    factor = max(1.0, protein_target / base_protein)
    if base_calories * factor > calorie_limit:
        # A uniform factor cannot satisfy both constraints when this check fails.
        raise ConstraintTargetError(
            "Protein target cannot be met without exceeding the calorie limit."
        )

    scaled = tuple(
        scale_ingredient_by_factor(item.ingredient, item.quantity_g, factor)
        for item in base_ingredients
    )
    return ScaledRecipe(
        ingredients=scaled,
        calories=round(sum(item.macros.calories for item in scaled), 2),
        protein_g=round(sum(item.macros.protein_g for item in scaled), 2),
        carbs_g=round(sum(item.macros.carbs_g for item in scaled), 2),
        fat_g=round(sum(item.macros.fat_g for item in scaled), 2),
    )
