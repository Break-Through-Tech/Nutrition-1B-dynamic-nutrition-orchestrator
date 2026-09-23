from dataclasses import dataclass

from .macro_math import MacroTotals, calculate_macros, validate_quantity_g


class InvalidScaleFactorError(ValueError):
    pass


@dataclass(frozen=True)
class ScaledIngredient:
    ingredient: str
    original_quantity_g: float
    scaled_quantity_g: float
    scale_factor: float
    macros: MacroTotals


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
