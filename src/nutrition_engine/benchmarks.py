from dataclasses import dataclass

from .macro_math import calculate_macros
from .scaling import (
    scale_ingredient_by_factor,
    scale_for_servings,
    scale_ingredient_to_quantity,
)


# These constants mirror the September success criteria for the deterministic
# baseline and give future agent evaluations a stable comparison point.
MAE_TARGET_PERCENT = 2.0
F1_BASELINE = 1.0


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
    # Expected values are hand-checkable per-100 g reference calculations.
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
    BenchmarkCase(
        id="macro-tofu-100g",
        description="Tofu baseline quantity",
        ingredient="tofu",
        quantity_g=100,
        expected_calories=144.0,
        expected_protein_g=17.3,
        expected_carbs_g=2.8,
        expected_fat_g=8.7,
    ),
]


SCALING_BENCHMARKS = [
    "scale-factor-chicken-100g-to-250g",
    "scale-servings-salmon-2-to-5",
    "scale-tofu-100g-to-250g",
]


def run_macro_benchmarks() -> list[dict]:
    results = []

    for case in MACRO_BENCHMARKS:
        actual = calculate_macros(case.ingredient, case.quantity_g)

        # Exact equality is appropriate here because both expected and actual
        # values are rounded by the deterministic engine to two decimals.
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

    tofu_result = scale_ingredient_by_factor(
        ingredient_name="tofu",
        original_quantity_g=100,
        scale_factor=2.5,
    )
    results.append(
        {
            "id": "scale-tofu-100g-to-250g",
            "passed": (
                tofu_result.scaled_quantity_g == 250.0
                and tofu_result.macros.calories == 360.0
                and tofu_result.macros.protein_g == 43.25
            ),
            "actual": tofu_result,
        }
    )

    return results


def run_extra_scaling_checks() -> list[dict]:
    target_quantity = scale_ingredient_to_quantity(
        ingredient_name="tofu",
        original_quantity_g=100,
        target_quantity_g=250,
    )
    same_servings = scale_for_servings(
        ingredient_name="brown rice",
        original_quantity_g=150,
        original_servings=4,
        target_servings=4,
    )

    return [
        {
            "id": "scale-to-target-quantity-tofu",
            "passed": target_quantity.scaled_quantity_g == 250.0,
            "actual": target_quantity,
        },
        {
            "id": "scale-same-servings-rice",
            "passed": (
                same_servings.scaled_quantity_g == 150.0
                and same_servings.macros.calories == 184.5
            ),
            "actual": same_servings,
        },
    ]


def calculate_mae_percent(actual: list[float], expected: list[float]) -> float:
    """Return mean absolute error as a percentage of expected magnitudes."""
    if len(actual) != len(expected) or not expected:
        raise ValueError("Actual and expected values must have equal non-zero length.")

    # Zero-valued targets have no meaningful relative error denominator, so
    # they are excluded from percentage MAE rather than silently divided by 0.
    non_zero_pairs = [
        (observed, target)
        for observed, target in zip(actual, expected)
        if target != 0
    ]
    if not non_zero_pairs:
        return 0.0

    return round(
        sum(abs(observed - target) / abs(target) * 100 for observed, target in non_zero_pairs)
        / len(non_zero_pairs),
        4,
    )


def calculate_f1_score(actual: list[bool], expected: list[bool]) -> float:
    """Calculate binary F1 without adding a machine-learning dependency."""
    if len(actual) != len(expected) or not expected:
        raise ValueError("Actual and expected labels must have equal non-zero length.")

    # This small implementation avoids pulling an ML dependency into the math
    # baseline while preserving the standard binary classification definition.
    true_positive = sum(observed and target for observed, target in zip(actual, expected))
    false_positive = sum(observed and not target for observed, target in zip(actual, expected))
    false_negative = sum(not observed and target for observed, target in zip(actual, expected))
    if true_positive == 0:
        return 0.0

    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    return round(2 * precision * recall / (precision + recall), 4)


def track_constraint_compliance(
    meals: list[dict[str, float]],
    target_protein_g: float = 140.0,
    max_calories: float = 2_000.0,
) -> dict[str, float | int | list[bool]]:
    """Track whether each meal satisfies the protein minimum and calorie cap."""
    # Each meal is independently checked against both hard constraints so the
    # caller can inspect failures instead of receiving only one aggregate rate.
    statuses = [
        meal["protein_g"] >= target_protein_g and meal["calories"] <= max_calories
        for meal in meals
    ]
    compliant_count = sum(statuses)
    return {
        "statuses": statuses,
        "total_meals": len(meals),
        "compliant_meals": compliant_count,
        "compliance_rate": round(compliant_count / len(meals), 4) if meals else 0.0,
    }
