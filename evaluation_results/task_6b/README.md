# Task 6B Evaluation History

This folder contains the progression of Task 6B ingredient matcher evaluations.

## Chronological Order

### 1. `live_comparison_20261117T225557Z/`
Compared the original NLP matcher against the initial SR Legacy-first hybrid matcher using the 30-example validation dataset.

This evaluation established that the initial hybrid implementation did not outperform the original NLP baseline.

### 2. `recipe_126_live_20261117T232220Z/`
Expanded the evaluation to 126 unique ingredients across 26 recipes (165 ingredient entries).

This was a broader live quality review using the USDA API. Since there were no expected FDC IDs, it does not report conventional accuracy, precision, recall, or F1.

### 3. `task6b_final_20261118T004052Z/`
Finalized the evaluation of the earlier SR Legacy-first hybrid implementation.

This was later superseded after receiving additional clarification from the advisor about considering all four FDC data types.

### 4. Earlier all-FDC implementation runs
- `hybrid_all_fdc_20261118T033233Z/`
- `hybrid_all_fdc_20261118T033630Z/`
- `hybrid_all_fdc_20261118T033809Z/`

These are intermediate evaluation runs from the updated all-FDC implementation cycle. They are retained for historical reference.

### 5. `hybrid_all_fdc_20261118T034613Z/`
**CURRENT FINAL EVALUATION**

This is the final evaluation of the updated Task 6B matcher.

The implementation:
- Searches across Survey (FNDDS), SR Legacy, Foundation, and Branded.
- Evaluates ingredient identity, preparation, and modifier compatibility.
- Uses data type as a secondary selection criterion when multiple suitable candidates exist.
- Preserves the original NLP matcher as fallback.

Results on the 30-example validation dataset:

| Metric | Original NLP | Updated Hybrid |
|---|---:|---:|
| Exact-ID F1 | 82.05% | 85.00% |
| Equivalence-aware F1 | 91.43% | 95.24% |

See `final_evaluation_report.md` for the complete results, nutrient comparisons, and manual equivalence review.

## Which Results Should Be Used?

Use the final all-FDC evaluation at `hybrid_all_fdc_20261118T034613Z/` when referencing the completed Task 6B implementation.

Earlier folders are retained for development history and comparison.