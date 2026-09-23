import pytest

from nutrition_engine.scaling import (
    InvalidScaleFactorError,
    scale_ingredient_by_factor,
    scale_ingredient_to_quantity,
    scale_for_servings,
)


def test_scale_ingredient_by_factor():
    result = scale_ingredient_by_factor(
        ingredient_name="chicken breast",
        original_quantity_g=100,
        scale_factor=2.5,
    )

    assert result.ingredient == "chicken breast"
    assert result.original_quantity_g == 100.0
    assert result.scaled_quantity_g == 250.0
    assert result.scale_factor == 2.5
    assert result.macros.calories == 412.5
    assert result.macros.protein_g == 77.5
    assert result.macros.fat_g == 9.0


def test_scale_ingredient_down_by_half():
    result = scale_ingredient_by_factor(
        ingredient_name="salmon",
        original_quantity_g=200,
        scale_factor=0.5,
    )

    assert result.scaled_quantity_g == 100.0
    assert result.macros.calories == 208.0
    assert result.macros.protein_g == 20.0
    assert result.macros.fat_g == 13.0


def test_scale_to_target_quantity():
    result = scale_ingredient_to_quantity(
        ingredient_name="tofu",
        original_quantity_g=100,
        target_quantity_g=250,
    )

    assert result.scale_factor == 2.5
    assert result.original_quantity_g == 100.0
    assert result.scaled_quantity_g == 250.0
    assert result.macros.calories == 360.0
    assert result.macros.protein_g == 43.25
    assert result.macros.carbs_g == 7.0
    assert result.macros.fat_g == 21.75


def test_scale_recipe_servings():
    result = scale_for_servings(
        ingredient_name="salmon",
        original_quantity_g=200,
        original_servings=2,
        target_servings=5,
    )

    assert result.scale_factor == 2.5
    assert result.original_quantity_g == 200.0
    assert result.scaled_quantity_g == 500.0
    assert result.macros.calories == 1040.0
    assert result.macros.protein_g == 100.0
    assert result.macros.fat_g == 65.0


def test_scale_for_same_number_of_servings():
    result = scale_for_servings(
        ingredient_name="brown rice",
        original_quantity_g=150,
        original_servings=4,
        target_servings=4,
    )

    assert result.scale_factor == 1.0
    assert result.scaled_quantity_g == 150.0
    assert result.macros.calories == 184.5


@pytest.mark.parametrize(
    "invalid_scale_factor",
    [
        0,
        -1,
        -0.5,
        "invalid",
        None,
        [],
        {},
    ],
)
def test_invalid_scale_factor_raises_error(invalid_scale_factor):
    with pytest.raises(InvalidScaleFactorError):
        scale_ingredient_by_factor(
            ingredient_name="salmon",
            original_quantity_g=100,
            scale_factor=invalid_scale_factor,
        )


@pytest.mark.parametrize(
    "original_servings,target_servings",
    [
        (0, 2),
        (-1, 2),
        (2, 0),
        (2, -1),
        (1.5, 2),
        (2, 1.5),
        ("2", 4),
        (2, "4"),
    ],
)
def test_invalid_serving_counts_raise_error(
    original_servings,
    target_servings,
):
    with pytest.raises(ValueError):
        scale_for_servings(
            ingredient_name="chicken breast",
            original_quantity_g=100,
            original_servings=original_servings,
            target_servings=target_servings,
        )


def test_scaled_ingredient_can_be_serialized_to_dictionary():
    result = scale_ingredient_by_factor(
        ingredient_name="chicken breast",
        original_quantity_g=100,
        scale_factor=2,
    )

    data = result.to_dict()

    assert data["ingredient"] == "chicken breast"
    assert data["original_quantity_g"] == 100.0
    assert data["scaled_quantity_g"] == 200.0
    assert data["scale_factor"] == 2.0
    assert data["macros"]["protein_g"] == 62.0
