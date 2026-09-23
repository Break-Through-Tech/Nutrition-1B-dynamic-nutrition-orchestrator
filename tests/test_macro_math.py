import pytest

from nutrition_engine.macro_math import (
    IngredientNotFoundError,
    InvalidQuantityError,
    calculate_macros,
)


def test_chicken_breast_baseline_100g():
    result = calculate_macros("chicken breast", 100)

    assert result.ingredient == "chicken breast"
    assert result.quantity_g == 100.0
    assert result.calories == 165.0
    assert result.protein_g == 31.0
    assert result.carbs_g == 0.0
    assert result.fat_g == 3.6


def test_chicken_breast_250g():
    result = calculate_macros("chicken breast", 250)

    assert result.calories == 412.5
    assert result.protein_g == 77.5
    assert result.carbs_g == 0.0
    assert result.fat_g == 9.0


def test_salmon_150g():
    result = calculate_macros("salmon", 150)

    assert result.calories == 312.0
    assert result.protein_g == 30.0
    assert result.carbs_g == 0.0
    assert result.fat_g == 19.5


def test_input_normalization_handles_case_and_whitespace():
    clean_input = calculate_macros("chicken breast", 100)
    messy_input = calculate_macros("  CHICKEN    BREAST  ", 100)

    assert clean_input == messy_input


def test_to_dict_returns_json_friendly_result():
    result = calculate_macros("tofu", 100)

    assert result.to_dict() == {
        "ingredient": "tofu",
        "quantity_g": 100.0,
        "calories": 144.0,
        "protein_g": 17.3,
        "carbs_g": 2.8,
        "fat_g": 8.7,
    }


def test_unknown_ingredient_raises_clear_error():
    with pytest.raises(IngredientNotFoundError):
        calculate_macros("pizza", 100)


@pytest.mark.parametrize(
    "invalid_quantity",
    [
        0,
        -1,
        -100,
        "not-a-number",
        None,
        [],
        {},
    ],
)
def test_invalid_quantities_raise_error(invalid_quantity):
    with pytest.raises(InvalidQuantityError):
        calculate_macros("salmon", invalid_quantity)


def test_same_input_produces_same_output_every_time():
    first_result = calculate_macros("tofu", 175)
    second_result = calculate_macros("tofu", 175)

    assert first_result == second_result
