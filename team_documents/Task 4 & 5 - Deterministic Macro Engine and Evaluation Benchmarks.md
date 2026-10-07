# Task 4: Build the Deterministic Macro Math Engine

This task was to create a reliable calculation tool that converts an ingredient name and quantity into calories, protein, carbohydrates, and fat. The calculations are deterministic: the same supported ingredient and quantity produce the same totals each time. The engine handles the arithmetic, while the nutrition values themselves come from the ingredient catalog.

The code follows this general process:

**Ingredient Name and Quantity → Normalize Name → Look Up Nutrition Data → Validate Quantity → Calculate Totals → Return Result.**

The `ingredients.py` file contains the nutrition records used by the engine. Each record stores calories, protein, carbohydrates, and fat per 100 grams. Keeping every ingredient on a per-100-gram basis gives the calculation code a consistent starting point.

The `calculate_macros()` function in `macro_math.py` performs the calculation. It looks up the ingredient, validates the requested quantity, and determines how much to scale the per-100-gram values:

*scale factor = requested quantity in grams / 100*

*macro total = macro value per 100 grams × scale factor*

For example, if the catalog lists 31 grams of protein per 100 grams of chicken breast, a 250-gram portion is calculated as:

*31 × (250 / 100) = 77.5 grams of protein*

Before calculating, `normalize_ingredient_name()` makes ingredient lookup more tolerant of capitalization and extra spaces. For example, `"  CHICKEN    BREAST  "` is treated the same as `"chicken breast"`. The `get_ingredient()` function then searches the canonical catalog. If the ingredient is not present, the engine raises an `IngredientNotFoundError` and lists the supported ingredients rather than estimating nutrition values.

The `validate_quantity_g()` function converts valid numeric input to a number and rejects values that cannot be converted, as well as zero or negative quantities. This prevents invalid amounts from being used to produce misleading totals. The resulting values are rounded to two decimal places and returned in a `MacroTotals` object. Its `to_dict()` method makes the result easier to pass to other tools or serialize as JSON.

The engine also includes scaling functions in `scaling.py`. These can scale an ingredient by a factor, set it to a target gram quantity, or adjust it for a different number of servings. The `scale_recipe_to_targets()` function uniformly scales a list of ingredients to meet a minimum protein target while staying below a calorie limit. Its default targets are 140 grams of protein and 2,000 calories. If uniform scaling cannot meet both constraints, it raises an error instead of returning a recipe that exceeds the calorie limit.

The engine’s nutrition catalog is currently limited to the ingredients explicitly listed in `ingredients.py`. Recipe ingredients that are not in that catalog must be matched to verified nutrition records before this engine can calculate their macros.

# Task 5: Define Evaluation Benchmarks

This task was to establish repeatable checks for the macro engine, ingredient scaling, and nutrition constraints. The benchmarks provide known inputs and expected outputs, allowing the team to detect when a calculation or scaling change produces an unexpected result.

The benchmark process follows this general flow:

**Reference Ingredient and Quantity → Run Engine → Compare Actual and Expected Values → Record Pass or Failure**

The `benchmarks.py` file defines cases for specific ingredients and quantities. Each macro benchmark includes expected calories, protein, carbohydrates, and fat. For example, a 100-gram chicken breast case checks the engine against the catalog’s baseline values, while larger quantities check whether the per-100-gram values are scaled correctly. Scaling benchmarks check both the resulting quantity and selected macro totals.

`run_macro_benchmarks()` calculates the values for each macro case and compares them with the expected results. `run_scaling_benchmarks()` and `run_extra_scaling_checks()` exercise scaling by multiplier, serving count, and target quantity. The benchmark results include a pass/fail value and the actual result for inspection.

The evaluation helpers cover additional project metrics:

- `calculate_mae_percent()` measures the average absolute difference between actual and expected values as a percentage of the expected values. A target below 2% is defined for the project. Zero expected values are excluded from percentage calculations because they cannot be used as a denominator.
- `calculate_f1_score()` calculates binary F1 from actual and expected true/false labels. It provides a utility for evaluating classification results, such as future ingredient-matching predictions. It does not by itself measure the accuracy of an NLP matcher; that requires labeled examples and predictions.
- `track_constraint_compliance()` checks each meal against a protein minimum and calorie maximum. It returns each meal’s compliance status, the number of compliant meals, the total number of meals, and the overall compliance rate.

The automated tests in `test_macro_math.py`, `test_scaling.py`, and `test_benchmarks.py` verify known calculations, input validation, scaling outcomes, benchmark pass/fail behavior, the MAE target check, F1 calculation, and constraint compliance tracking. The full test suite currently passes with **49 tests**.
