from nutrition_engine import (
    calculate_macros,
    scale_ingredient_by_factor,
    scale_for_servings,
)


def main():
    chicken = calculate_macros("chicken breast", 250)
    print("Chicken breast, 250g:")
    print(chicken.to_dict())

    tofu = scale_ingredient_by_factor(
        ingredient_name="tofu",
        original_quantity_g=120,
        scale_factor=1.5,
    )
    print("\nTofu scaled from 120g by 1.5:")
    print(tofu.to_dict())

    salmon = scale_for_servings(
        ingredient_name="salmon",
        original_quantity_g=200,
        original_servings=2,
        target_servings=5,
    )
    print("\nSalmon recipe scaled from 2 servings to 5:")
    print(salmon.to_dict())


if __name__ == "__main__":
    main()
