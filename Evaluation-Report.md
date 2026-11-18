# Evaluation Report

## 1. Project summary

This project is a Tool-Augmented Generation (TAG) system for high-protein Indian vegetarian meal planning. It combines local recipe templates with USDA nutrition data and deterministic macro calculations to reduce hallucinated arithmetic.

The implementation includes a local recipe database, deterministic calories/protein/carbohydrate/fat calculations, dietary restriction filtering, ingredient-to-USDA matching, quantity scaling, and semantic retrieval.

Sources: [Challenge-Project-Overview.md](Challenge-Project-Overview.md), [README.md](README.md).

## 2. Project objective and challenge framing

The challenge defines three success criteria:

1. Macro Optimization Precision: Mean Absolute Error (MAE) below 2% across a full 7-day generation cycle.
2. Entity Resolution Accuracy: F1-score above 90% on an unseen validation set of 30 common Indian vegetarian ingredients.
3. Scheduling Constraint Adherence: 100% compliance with zero-repeat ingredient logic across every consecutive 48-hour block.

Source: [Challenge-Project-Overview.md](Challenge-Project-Overview.md).

For a 140 g protein-per-day target, the overview gives an MAE range of 137.2 g to 142.8 g as the derived window described in the challenge.

The full 7-day macro-MAE and 48-hour scheduling-compliance outcomes are **TODO**: no repo result reproduces or reports those two outcomes.

## 3. Data and implementation

The repository includes:

- A local recipe bank: [data/recipes.json](data/recipes.json)
- An ingredient catalog: [data/ingredients.csv](data/ingredients.csv)
- A USDA candidate snapshot: [data/usda_candidates.json](data/usda_candidates.json)
- A 30-row validation set: [data/validation_set.csv](data/validation_set.csv)
- USDA raw data tables in [data/](data/)

The main implementation areas are:

- [build_recipe_db.py](build_recipe_db.py): builds normalized recipe and ingredient outputs.
- [src/nutrition_engine/macro_math.py](src/nutrition_engine/macro_math.py): calculates macros from canonical per-100 g values.
- [src/nutrition_engine/scaling.py](src/nutrition_engine/scaling.py): scales quantities and recipes.
- [src/nutrition_engine/meal_planner.py](src/nutrition_engine/meal_planner.py): applies dietary rules and meal-plan constraints.
- [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py): normalizes names, expands synonyms, and scores USDA candidates.
- [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py): computes exact-FDC-ID TP/FP/FN/TN metrics.
- [src/nutrition_engine/semantic_ingredient_search.py](src/nutrition_engine/semantic_ingredient_search.py): supports local semantic ingredient retrieval.

These data and implementation descriptions are from [README.md](README.md), [Challenge-Project-Overview.md](Challenge-Project-Overview.md), and the linked current source files.

## 4. Test status

The repository test suite was reproduced with current code:

```bash
pytest -q
```

This command passed all 175 collected tests after the dependencies declared in [requirements.txt](requirements.txt) were installed.

Sources:

- Current code output: `pytest -q`.
- Test counts are from collection across [tests/](tests/).
- The team document [team_documents/Task 4 & 5 - Deterministic Macro Engine and Evaluation Benchmarks.md](team_documents/Task%204%20&%205%20-%20Deterministic%20Macro%20Engine%20and%20Evaluation%20Benchmarks.md) says the suite currently passes 49 tests.

These counts disagree; this report identifies both numbers and does not silently replace either source. The 175-test count is the independently collected current repository count, while the 49-test statement is a saved team-document claim.

## 5. Original matcher evaluation

The original offline matcher was reproduced from the current repository code:

```bash
python scripts/evaluate_matcher.py
```

Current code output:

- Validation rows: 30
- True positives: 19
- False positives: 4
- False negatives: 0
- True negatives: 7
- Precision: 82.61%
- Recall: 100.00%
- F1: 90.48%
- Target (>90%): MET

Sources:

- Current code output: `python scripts/evaluate_matcher.py`.
- [scripts/evaluate_matcher.py](scripts/evaluate_matcher.py) and [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py).
- [data/validation_set.csv](data/validation_set.csv) and [data/usda_candidates.json](data/usda_candidates.json).

The reproduced current snapshot produced four false positives:

- Brown rice
- Extra-firm tofu, cubed
- Low-fat Greek yogurt
- Unflavored whey protein

Source: current output from `python scripts/evaluate_matcher.py`.

This exact-ID result was also reported by [team_documents/Task 6 - Ingredient matching.md](team_documents/Task%206%20-%20Ingredient%20matching.md) as F1 90.48%, precision 82.61%, and recall 100.00%. That team document is a saved report.

## 6. Latest Task 6B all-FDC evaluation

[evaluation_results/task_6b/README.md](evaluation_results/task_6b/README.md) identifies [evaluation_results/task_6b/all_fdc_ingredient_equivalence_20261118T045607Z/evaluation_report.md](evaluation_results/task_6b/all_fdc_ingredient_equivalence_20261118T045607Z/evaluation_report.md) as the current final Task 6B evaluation.

Its primary ambiguity-excluded ingredient-equivalence results are saved-report values:

| Metric | Original NLP | All-FDC |
|---|---:|---:|
| Precision | 88.89% | 90.91% |
| Recall | 94.12% | 100.00% |
| F1 | 91.43% | 95.24% |
| Accuracy | 88.46% | 93.10% |
| Assignment rate | 73.33% | 76.67% |
| Abstention rate | 26.67% | 23.33% |

Source: [evaluation_results/task_6b/all_fdc_ingredient_equivalence_20261118T045607Z/evaluation_report.md](evaluation_results/task_6b/all_fdc_ingredient_equivalence_20261118T045607Z/evaluation_report.md), saved report.

The all-FDC result excluded 1 ambiguous row from its denominator of 29 rows; the original NLP result excluded 4 ambiguous rows from its denominator of 26 rows. The reported totals are:

- Original NLP: TP 16, FP 2, TN 7, FN 1.
- All-FDC: TP 20, FP 2, TN 7, FN 0.

Under conservative all-30-row scoring in the same saved report:

- Original NLP F1: 82.05%.
- All-FDC F1: 93.02%.

Source: the same saved all-FDC evaluation report.

The saved report explicitly says that no matcher was rerun and no live USDA calls were made during this recalculation. It reused archived candidates and direct record details. Therefore, these equivalence-aware numbers are **saved-report results**, not independent current-code output.

## 7. Earlier Task 6B results and disagreements

The repository contains older and differently defined Task 6B results:

- [evaluation_results/task_6b/task6b_final_20261118T004052Z/final_evaluation_report.md](evaluation_results/task_6b/task6b_final_20261118T004052Z/final_evaluation_report.md) reports the earlier SR Legacy-first hybrid exact-ID run:
  - Original NLP F1: 82.05%.
  - Hybrid F1: 56.25%.
- [evaluation_results/baseline/live_nlp_20261115T213543Z/evaluation_report.md](evaluation_results/baseline/live_nlp_20261115T213543Z/evaluation_report.md) reports an exact-ID live NLP baseline F1 of 82.05%.
- [evaluation_results/task_6b/README.md](evaluation_results/task_6b/README.md) says the earlier SR Legacy-first approach was superseded and directs readers to the all-FDC equivalence evaluation.

These files use exact-ID or post-hoc ingredient-equivalence definitions that are not interchangeable with the 90.48% offline exact-ID result. The report will not combine or silently choose among these values:

- 82.05% is an exact-ID saved NLP baseline in the live and Task 6B comparison reports.
- 56.25% is an exact-ID saved SR Legacy-first hybrid result.
- 91.43% is a post-hoc equivalence-aware saved NLP result in the Task 6B reports.
- 95.24% is the latest saved post-hoc all-FDC equivalence-aware result.
- 90.48% is the current independently reproduced offline exact-ID result.

## 8. Macro benchmarks and targets

The benchmark constants and helper implementation are in [src/nutrition_engine/benchmarks.py](src/nutrition_engine/benchmarks.py):

- `MAE_TARGET_PERCENT = 2.0`
- `F1_BASELINE = 1.0`
- Default target protein: 140 g
- Maximum calories: 2,000

The deterministic calculation formula is in [src/nutrition_engine/macro_math.py](src/nutrition_engine/macro_math.py): macro total = per-100 g value × requested grams / 100.

Source: current code.

The repository has benchmark cases for chicken, salmon, black beans, and tofu, plus scaling checks. The tests for these benchmarks pass in the current suite, but no full 7-day observed MAE result is present.

Saved README text says the expected threshold for deterministic calculation benchmarks is 100%. This is a project benchmark expectation, not an observed full 7-day MAE.

Sources: [README.md](README.md) and [src/nutrition_engine/benchmarks.py](src/nutrition_engine/benchmarks.py).

## 9. Task 9 semantic retrieval

Task 9 used six queries and qualitatively compared saved Phase 1 keyword candidates with semantic retrieval results.

Current or reproduced evidence:

- The saved report says 18 semantic top-three lists matched the previous report’s candidate names and similarity values, rounded to three decimals.
- The contextual reproduction used the existing persistent Chroma collections and no USDA/API calls.
- Context can move relevant occurrences up for rajma, atta, ajwain, and kala namak, but also introduces other ingredients from the same recipe.
- The report found no clear exact Moong Dal Cheela occurrence in the contextual top three.
- Paneer was tied with oil in the context-aware paneer query at 0.854 in the saved report, with oil returned first because of Chroma ordering.

Sources:

- [evaluation_results/task_9/contextual_semantic_retrieval/evaluation_summary.md](evaluation_results/task_9/contextual_semantic_retrieval/evaluation_summary.md): saved reproduction report.
- [evaluation_results/task_9/contextual_semantic_retrieval/retrieval_comparison.md](evaluation_results/task_9/contextual_semantic_retrieval/retrieval_comparison.md): saved report.
- [team_documents/Task 9 - Semantic Ingredient Retrieval.md](team_documents/Task%209%20-%20Semantic%20Ingredient%20Retrieval.md): saved qualitative reflection.

The report explicitly did not calculate accuracy, precision, recall, or F1 because the validation set is for USDA exact-record matching rather than semantic local-recipe retrieval. Similarity values are ranking signals, not confidence or equivalence evidence.

## 10. Honest limitations and TODOs

- The latest all-FDC metrics are saved-post-hoc results for 30 examples; they do not establish generalization.
- The exact-ID, post-hoc equivalence, and conservative metric definitions must not be combined.
- Hing, kasuri methi, and ajwain have no saved correct USDA record in the validation set.
- The task-9 systems compare different candidate types and are not a like-for-like accuracy evaluation.

## 12. Commands

Tested commands:

```bash
pytest -q
python scripts/evaluate_matcher.py
python -m pip install -r requirements.txt
```

The following command is from [README.md](README.md) and [scripts/evaluate_matcher.py](scripts/evaluate_matcher.py) but requires a USDA API key and live API access. It is marked for manual verification:

```bash
python scripts/snapshot_usda_candidates.py --validation
```
