from dataclasses import dataclass


@dataclass(frozen=True)
class IngredientNutrition:
    name: str
    calories_per_100g: float
    protein_g_per_100g: float
    carbs_g_per_100g: float = 0.0
    fat_g_per_100g: float = 0.0


INGREDIENTS: dict[str, IngredientNutrition] = {
    "chicken breast": IngredientNutrition(
        name="chicken breast",
        calories_per_100g=165.0,
        protein_g_per_100g=31.0,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=3.6,
    ),
    "salmon": IngredientNutrition(
        name="salmon",
        calories_per_100g=208.0,
        protein_g_per_100g=20.0,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=13.0,
    ),
    "greek yogurt": IngredientNutrition(
        name="greek yogurt",
        calories_per_100g=59.0,
        protein_g_per_100g=10.0,
        carbs_g_per_100g=3.6,
        fat_g_per_100g=0.4,
    ),
    "egg": IngredientNutrition(
        name="egg",
        calories_per_100g=143.0,
        protein_g_per_100g=12.6,
        carbs_g_per_100g=0.7,
        fat_g_per_100g=9.5,
    ),
    "tofu": IngredientNutrition(
        name="tofu",
        calories_per_100g=144.0,
        protein_g_per_100g=17.3,
        carbs_g_per_100g=2.8,
        fat_g_per_100g=8.7,
    ),
    "black beans": IngredientNutrition(
        name="black beans",
        calories_per_100g=132.0,
        protein_g_per_100g=8.9,
        carbs_g_per_100g=23.7,
        fat_g_per_100g=0.5,
    ),
    "brown rice": IngredientNutrition(
        name="brown rice",
        calories_per_100g=123.0,
        protein_g_per_100g=2.7,
        carbs_g_per_100g=25.6,
        fat_g_per_100g=1.0,
    ),
}
