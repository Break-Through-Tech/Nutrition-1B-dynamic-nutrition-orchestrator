from dataclasses import dataclass

from .ingredients import INGREDIENTS, IngredientNutrition


class IngredientNotFoundError(ValueError):
    pass


class InvalidQuantityError(ValueError):
    pass


@dataclass(frozen=True)
class MacroTotals:
    ingredient: str
    quantity_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

    def to_dict(self) -> dict[str, float | str]:
        # Keep calculation results serializable for APIs, logs, and agent tools.
        return {
            "ingredient": self.ingredient,
            "quantity_g": self.quantity_g,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
        }


def normalize_ingredient_name(name: str) -> str:
    # Canonicalization lets user-entered case and repeated whitespace resolve
    # to the same trusted ingredient record.
    if not isinstance(name, str) or not name.strip():
        raise IngredientNotFoundError("Ingredient name must be a non-empty string.")

    return " ".join(name.lower().strip().split())


def get_ingredient(name: str) -> IngredientNutrition:
    normalized_name = normalize_ingredient_name(name)

    if normalized_name not in INGREDIENTS:
        supported = ", ".join(sorted(INGREDIENTS.keys()))
        raise IngredientNotFoundError(
            f"Ingredient '{name}' was not found. Supported ingredients: {supported}"
        )

    return INGREDIENTS[normalized_name]


def validate_quantity_g(quantity_g: float) -> float:
    try:
        quantity = float(quantity_g)
    except (TypeError, ValueError) as error:
        raise InvalidQuantityError("Quantity must be a numeric value in grams.") from error

    if quantity <= 0:
        # Zero and negative quantities would produce misleading nutrition data.
        raise InvalidQuantityError("Quantity must be greater than zero grams.")

    return quantity


def round_macro(value: float) -> float:
    return round(value, 2)


def calculate_macros(ingredient_name: str, quantity_g: float) -> MacroTotals:
    """
    Calculate nutrition totals from a canonical per-100g ingredient record.

    Formula:
        scale_factor = requested_grams / 100
        macro_total = macro_per_100g * scale_factor
    """
    ingredient = get_ingredient(ingredient_name)
    grams = validate_quantity_g(quantity_g)
    # All source records are expressed per 100 g, so every nutrient uses one
    # shared factor and cannot drift through separate arithmetic paths.
    scale_factor = grams / 100.0

    return MacroTotals(
        ingredient=ingredient.name,
        quantity_g=round_macro(grams),
        calories=round_macro(ingredient.calories_per_100g * scale_factor),
        protein_g=round_macro(ingredient.protein_g_per_100g * scale_factor),
        carbs_g=round_macro(ingredient.carbs_g_per_100g * scale_factor),
        fat_g=round_macro(ingredient.fat_g_per_100g * scale_factor),
    )
