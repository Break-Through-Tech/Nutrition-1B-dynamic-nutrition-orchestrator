from dataclasses import dataclass

from .macro_math import calculate_macros
from .scaling import scale_ingredient_by_factor, scale_for_servings


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    description: str
    ingredient: str
    quantity_g: float
    expected_calories: float
    expected_protein_g: float
    expected_carbs_g: float
    expected_fat_g: float


MACRO_BENCHMARKS: list[BenchmarkCase] = [
    BenchmarkCase(
        id="macro-chicken-100g",
        description="Chicken breast baseline quantity",
        ingredient="chicken breast",
        quantity_g=100,
        expected_calories=165.0,
        expected_protein_g=31.0,
        expected_carbs_g=0.0,
        expected_fat_g=3.6,
    ),
    BenchmarkCase(
        id="macro-chicken-250g",
        description="Chicken breast larger quantity",
        ingredient="chicken breast",
        quantity_g=250,
        expected_calories=412.5,
        expected_protein_g=77.5,
        expected_carbs_g=0.0,
        expected_fat_g=9.0,
    ),
    BenchmarkCase(
        id="macro-salmon-150g",
        description="Salmon scaled quantity",
        ingredient="salmon",
        quantity_g=150,
        expected_calories=312.0,
        expected_protein_g=30.0,
        expected_carbs_g=0.0,
        expected_fat_g=19.5,
    ),
    BenchmarkCase(
        id="macro-black-beans-200g",
        description="Black beans doubled from baseline",
        ingredient="black beans",
        quantity_g=200,
        expected_calories=264.0,
        expected_protein_g=17.8,
        expected_carbs_g=47.4,
        expected_fat_g=1.0,
    ),
]


def run_macro_benchmarks() -> list[dict]:
    results = []

    for case in MACRO_BENCHMARKS:
        actual = calculate_macros(case.ingredient, case.quantity_g)

        passed = (
            actual.calories == case.expected_calories
            and actual.protein_g == case.expected_protein_g
            and actual.carbs_g == case.expected_carbs_g
            and actual.fat_g == case.expected_fat_g
        )

        results.append(
            {
                "id": case.id,
                "description": case.description,
                "passed": passed,
                "actual": actual,
            }
        )

    return results


def run_scaling_benchmarks() -> list[dict]:
    results = []

    factor_result = scale_ingredient_by_factor(
        ingredient_name="chicken breast",
        original_quantity_g=100,
        scale_factor=2.5,
    )

    results.append(
        {
            "id": "scale-factor-chicken-100g-to-250g",
            "passed": (
                factor_result.scaled_quantity_g == 250.0
                and factor_result.macros.calories == 412.5
                and factor_result.macros.protein_g == 77.5
            ),
            "actual": factor_result,
        }
    )

    serving_result = scale_for_servings(
        ingredient_name="salmon",
        original_quantity_g=200,
        original_servings=2,
        target_servings=5,
    )

    results.append(
        {
            "id": "scale-servings-salmon-2-to-5",
            "passed": (
                serving_result.scaled_quantity_g == 500.0
                and serving_result.macros.calories == 1040.0
                and serving_result.macros.protein_g == 100.0
            ),
            "actual": serving_result,
        }
    )

    return results
