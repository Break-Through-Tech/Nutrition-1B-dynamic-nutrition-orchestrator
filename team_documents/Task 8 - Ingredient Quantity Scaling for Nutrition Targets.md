# Task 8: Ingredient Quantity Scaling for Nutrition Targets

This task was to create functions that adjust ingredient quantities while recalculating their nutrition values. Scaling can be used to change a recipe’s serving size, set an ingredient to a specific gram amount, or adjust a recipe toward nutrition targets. All macro totals are recalculated from the canonical per-100-gram ingredient data.

The code follows this general process:

**Ingredient and Starting Quantity → Validate Inputs → Determine Scale Factor → Calculate New Quantity → Recalculate Macros → Check Constraints**

The scaling functions are implemented in `scaling.py`.

`scale_ingredient_by_factor()` multiplies an ingredient’s original quantity by a scale factor. For example, scaling 100 grams of chicken breast by 2.5 produces 250 grams. The function then calls the macro engine to calculate the nutrition totals for the new quantity.

`scale_ingredient_to_quantity()` changes an ingredient to a specified gram amount. It calculates the scale factor by dividing the target quantity by the original quantity, then uses the factor-scaling function to produce the result.

`scale_for_servings()` adjusts an ingredient quantity when the number of servings changes. For example, if 200 grams of an ingredient are used for two servings and the recipe is changed to five servings, the function scales the ingredient by 2.5.

`scale_recipe_to_targets()` accepts a list of ingredient names and quantities. It calculates the recipe’s starting protein and calories, then applies one uniform scale factor to the ingredients to meet a minimum protein target. By default, it targets at least 140 grams of protein while keeping calories at or below 2,000. If uniform scaling cannot satisfy both requirements, the function raises a `ConstraintTargetError` instead of returning a result that violates the calorie limit.

The functions validate ingredient quantities, scale factors, and serving counts. Invalid or unsupported inputs produce errors rather than silently returning misleading results. The scaled quantities and macro totals are returned in structured result objects that can also be converted to dictionaries.

The automated tests in `test_scaling.py` check scaling up and down, target quantities, serving adjustments, invalid inputs, serialization, and recipe target handling. A test also verifies that an impossible protein-and-calorie combination is rejected. The full test suite currently passes with **49 tests**.
