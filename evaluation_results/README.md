# Evaluation Results

This folder contains evaluation results from the Nutrition project, including the original NLP baseline, Task 6B hybrid matcher evaluations, and broader ingredient quality reviews.

## Folder Guide

### `baseline/`
Contains the original NLP ingredient matcher baseline evaluation from November 15.

This is the reference point used to compare subsequent hybrid matcher improvements.

### `task_6b/`
Contains the evaluations performed during Task 6B.

See `task_6b/README.md` for the chronological breakdown and the final evaluation to reference.

## Important Notes

- Exact-ID metrics measure whether the selected FDC ID matches the expected ID.
- Equivalence-aware metrics additionally count manually verified equivalent FDC records as successful.
- Ambiguous matches are excluded from equivalence-aware scoring.
- The 126-ingredient evaluation is a broader quality review without ground-truth FDC IDs. Its manual classifications should not be interpreted as conventional accuracy or F1 metrics.

For the latest Task 6B results, refer to:

`task_6b/hybrid_all_fdc_20261118T034613Z/final_evaluation_report.md`