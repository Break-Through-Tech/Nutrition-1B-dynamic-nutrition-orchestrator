# Task 6B Evaluation History

This folder documents the progression of Task 6B ingredient matcher evaluations, from the original NLP baseline to the updated all-FDC approach.

## Chronological Order

### 1. `live_comparison_20261117T225557Z/`

Compared the original NLP matcher against the initial SR Legacy-first hybrid matcher using the 30-example validation dataset.

This evaluation showed that the initial hybrid implementation did not outperform the original NLP baseline.

### 2. `recipe_126_live_20261117T232220Z/`

Expanded the evaluation to 126 unique ingredients across 26 recipes (165 ingredient entries).

This was a broader live quality review using the USDA API. Since the recipe dataset did not contain expected FDC IDs, conventional accuracy, precision, recall, and F1 metrics were not calculated.

### 3. `task6b_final_20261118T004052Z/`

Finalized the evaluation of the earlier SR Legacy-first hybrid implementation.

This approach was later superseded following clarification from the advisor about considering all four USDA FoodData Central data types.

### 4. Earlier all-FDC implementation runs

The following runs were part of the updated all-FDC implementation cycle:

- `hybrid_all_fdc_20261118T033233Z/`
- `hybrid_all_fdc_20261118T033630Z/`
- `hybrid_all_fdc_20261118T033809Z/`
- `hybrid_all_fdc_20261118T034613Z/`

These runs document intermediate development and evaluation work. They are retained in Git history for reference.

### 5. `all_fdc_ingredient_equivalence_20261118T045607Z/`

**CURRENT FINAL EVALUATION**

This evaluation compares the original NLP matcher against the experimental all-FDC matcher using ingredient-equivalence review on the same 30-example validation dataset.

The all-FDC implementation:

- Searches across Survey (FNDDS), SR Legacy, Foundation, and Branded records.
- Evaluates ingredient identity, preparation, and meaningful modifier compatibility.
- Prioritizes suitable curated records over Branded records.
- Uses the original NLP matcher as a fallback when the all-FDC search does not produce a suitable assignment.
- Uses conservative review and abstention when a suitable match cannot be established.

**Results:**

| Metric | Original NLP | All-FDC |
|---|---:|---:|
| Precision | 88.89% | 90.91% |
| Recall | 94.12% | 100.00% |
| Ingredient-equivalence F1 | 91.43% | 95.24% |
| Accuracy | 88.46% | 93.10% |
| Assignment Rate | 73.33% | 76.67% |
| Abstention Rate | 26.67% | 23.33% |

The all-FDC matcher improved ingredient-equivalence F1 by **3.81 percentage points** and achieved 100% recall on this validation set.

See `evaluation_report.md` for the complete results, confusion counts, ambiguity analysis, and conservative scoring comparison.

**Evaluation notes:**
- Results are based on 30 validation examples and manual ingredient-equivalence adjudication.
- The evaluation reused saved USDA candidate snapshots and record details. No new live API calls were made.
- Nutritional values were considered during manual equivalence review, but they are not currently part of the matcher's candidate-selection logic.
- These results are specific to this validation set and do not establish generalization to a larger dataset.

## Which Results Should Be Used?

Use `all_fdc_ingredient_equivalence_20261118T045607Z/` when referencing the latest Task 6B evaluation.

The earlier evaluations document the development process and comparisons that led to the updated all-FDC approach.
