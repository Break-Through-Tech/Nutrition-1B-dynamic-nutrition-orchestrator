# Dynamic Nutrition Orchestrator

### 👥 **Team Members**

| Name             | GitHub Handle | Contribution                                                             | LinkedIn Account                                 |
|------------------|---------------|--------------------------------------------------------------------------|--------------------------------------------------|
| Shirina Daniel   | @shirinadan   | Deterministic macro calculation, recipe scaling, dietary restriction filtering, benchmark evaluation, automated testing | www.linkedin.com/in/shirinadan/                  |
| Lakshmi Jinkala  | @lakshmijinkala | Error-recovery state loop, creative recipe generation | www.linkedin.com/in/lakshmijinkala               |
| Sadia Fathima    | @sluggysadi | Build the local recipe seed database, build the Streamlit UI | https://www.linkedin.com/in/sadiafathima         |
| Gesell Gonzalez  | @ggesell17 | Build the USDA FoodData Central API and incorporate Pydantic schemas | www.linkedin.com/in/gesell-gonzalez              |

---

## 🎯 **Project Highlights**

- Builds a local recipe database from source recipe documents and stores the normalized output in JSON and CSV files.
- Uses a deterministic macro engine to calculate calories, protein, carbohydrates, and fat from canonical per-100g nutrition values.
- Restricts meal selection by dietary rules such as vegetarian, vegan, dairy-free, nut-free, and gluten-free.
- Resolves raw ingredient strings to USDA FoodData Central records using a local search snapshot and validation set.
- Keeps evaluation reproducible by saving USDA candidates to disk and scoring against a labeled validation CSV instead of relying on a live API.

Relevant source files: [build_recipe_db.py](build_recipe_db.py), [src/nutrition_engine/meal_planner.py](src/nutrition_engine/meal_planner.py), [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py), [scripts/snapshot_usda_candidates.py](scripts/snapshot_usda_candidates.py).

---

## 👩🏽‍💻 **Setup and Installation**

The project expects a local `.env` file with a USDA API key in the environment variable `USDA_API_KEY`. The configuration logic is in [src/nutrition_engine/config.py](src/nutrition_engine/config.py). The project is designed to read the key from the environment or from a repository-root `.env` file.

Manual verification required in a fresh environment:

```bash
pip install -r requirements.txt
```

To capture USDA candidates once and keep evaluation reproducible:

```bash
python scripts/snapshot_usda_candidates.py --validation
```

To run the matcher against the offline validation set:

```bash
python scripts/evaluate_matcher.py
```

To run the repository test suite:

```bash
pytest -q
```

The current repository state was checked with `pytest -q`, and it passed. The matcher evaluation was also reproduced with `python scripts/evaluate_matcher.py` and is reported in the Results section below.

---

## 🏗️ **Project Overview**

This project is a nutrition-planning and constraint-optimization system for high-protein Indian vegetarian meal planning. The repository description in [Challenge-Project-Overview.md](Challenge-Project-Overview.md) states that it is a Tool-Augmented Generation (TAG) system that combines local recipe templates with USDA nutrient density data and a deterministic arithmetic layer to prevent hallucinated macro calculations.

The repo implements that concept in three connected parts:

1. A local recipe seed database built from recipe source documents and stored in JSON and CSV files.
2. A deterministic macro engine that calculates nutritional totals from canonical per-100g values and scales ingredients to servings or nutrition targets.
3. A matcher that resolves raw ingredient names to USDA FDC records so the macro engine can operate on verified nutrition data rather than guessed values.

The most relevant implementation files are [build_recipe_db.py](build_recipe_db.py), [src/nutrition_engine/macro_math.py](src/nutrition_engine/macro_math.py), [src/nutrition_engine/scaling.py](src/nutrition_engine/scaling.py), [src/nutrition_engine/meal_planner.py](src/nutrition_engine/meal_planner.py), and [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py).

The project overview also lists three success criteria:

- Mean absolute error below 2% across a full 7-day generation cycle.
- F1-score above 90% on a validation set of 30 common Indian vegetarian ingredients.
- 100% compliance with zero-repeat ingredient logic across consecutive 48-hour blocks.

Source: [Challenge-Project-Overview.md](Challenge-Project-Overview.md).

Important note: these are project targets and requirements, not all of them are independently reproduced in the current code output. The only metric verified directly from the repo state was the F1 evaluation result in the Results section below.

---

## 📊 **Data Exploration**

The repository contains a real data pipeline rather than a single static dataset.

Data sources and outputs in the repo:

- Local recipe bank: [data/recipes.json](data/recipes.json)
- Ingredient catalog: [data/ingredients.csv](data/ingredients.csv)
- USDA candidate snapshot: [data/usda_candidates.json](data/usda_candidates.json)
- Validation set for matcher evaluation: [data/validation_set.csv](data/validation_set.csv)
- USDA raw tables: [data/](data/)

The recipe database is built by [build_recipe_db.py](build_recipe_db.py). It normalizes recipe records and writes both the full list of recipe objects and a deduplicated flat list of ingredients. The code also records each ingredient’s example unit and numeric quantity flag.

The USDA search snapshot is created by [scripts/snapshot_usda_candidates.py](scripts/snapshot_usda_candidates.py). That script explains why the project stores a snapshot: USDA content can change over time, so the evaluation should be reproducible from a saved candidate set instead of a live API result.

The validation set is managed by [scripts/label_validation_set.py](scripts/label_validation_set.py) and is the ground truth used by [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py). It labels raw ingredient names with an expected USDA FDC ID where appropriate.

---

## 🧠 **Model Development**

This project is not a traditional supervised-learning model with a training set and a learned classifier. The code describes a deterministic, rule-based macro and planning pipeline: it normalizes ingredient names, expands synonyms, filters composite ingredients, scores USDA candidates, and computes nutrition deterministically.

The relevant implementation files are:

- [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py): normalization, synonym mapping, composite detection, candidate scoring, and accept-threshold decision.
- [src/nutrition_engine/usda_search.py](src/nutrition_engine/usda_search.py): adaptation layer between the search API and matcher Candidate objects.
- [src/nutrition_engine/macro_math.py](src/nutrition_engine/macro_math.py): caloric and macronutrient totals from per-100g values.
- [src/nutrition_engine/meal_planner.py](src/nutrition_engine/meal_planner.py): diet-aware recipe selection and weekly planning logic.
- [src/nutrition_engine/benchmarks.py](src/nutrition_engine/benchmarks.py): benchmark cases and evaluation helper functions.

The project’s acceptance metric is an F1 score computed on a validation set of 30 items, with a target greater than 90%. The code enforces this in [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py), where `meets_target` is defined as `f1 > 0.90`.

---

## 📈 **Results & Key Findings**

### Verified current code output

The following numbers were reproduced directly from the current repository by running the project scripts in this environment.

- `pytest -q` passed successfully in the current repo.
- `python scripts/evaluate_matcher.py` produced:
  - Validation rows: 30
  - TP: 19
  - FP: 4
  - FN: 0
  - TN: 7
  - Precision: 82.61%
  - Recall: 100.00%
  - F1: 90.48%
  - Target (>90%): MET

This result is generated by the evaluation logic in [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py), using the validation set in [data/validation_set.csv](data/validation_set.csv) and the snapshot in [data/usda_candidates.json](data/usda_candidates.json).

### Saved-report and target values in the repo

The repository also contains benchmark targets and constants that are important for the project definition, but they are not all current observed outputs:

- `MAE_TARGET_PERCENT = 2.0` in [src/nutrition_engine/benchmarks.py](src/nutrition_engine/benchmarks.py)
- `F1_BASELINE = 1.0` in [src/nutrition_engine/benchmarks.py](src/nutrition_engine/benchmarks.py)
- `ACCEPT_THRESHOLD = 0.80` in [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py)
- “F1 > 90% on a 30-ingredient validation set” in [src/nutrition_engine/matcher_eval.py](src/nutrition_engine/matcher_eval.py)
- “The expected threshold for deterministic calculation benchmarks is 100%.” in [README.md](README.md)

---

### Honest limitations

- **The result clears the target narrowly.** The measured F1 is 90.48%, just 0.48 percentage points above the 90% threshold.
- **Some errors concern record choice, not ingredient identification.** For extra-firm tofu, low-fat Greek yogurt, and whey protein, the matcher found the intended food but selected a branded record instead of an available lab-analyzed record. Protein values for extra-firm tofu vary from 5.88 to 9.98 g across records, so the evaluation treats the curated record as the correct match.
- **The labels include judgment calls.** When multiple USDA records are defensible, one was selected for the validation set, with the rationale documented in the `notes` column of [data/validation_set.csv](data/validation_set.csv).
- **USDA records are unavailable for hing, kasuri methi, and ajwain.** The validation set marks these ingredients as having no correct record, and the matcher declines them. Recipes that use them need a documented fallback because USDA cannot supply their nutrition values.
- **Further keyword tuning has not improved the total error count.** Later rounds traded one error for another, motivating the semantic-retrieval approach planned for Task 9.

---

## 🚀 **Next Steps**

TODO: Finalize stakeholder-ready narrative metrics and add a polished summary section once a full end-to-end planner run is validated.

TODO: Add a license file if repository licensing is required by the Challenge Advisor or hosting organization.

TODO: If a UI is added, document the exact run steps and screenshots in this README.

The immediate repository facts support the following next step: improve the matcher by reviewing the remaining false positives shown in the evaluation output and by expanding the label set or synonym rules as needed.

---

## 📝 **License**

TODO: Add the project license file and link it here. No license file was found in the repository root during review.

---

## 📄 **References** (Optional but encouraged)

The repo includes the following source material for background and project framing:

- [Challenge-Project-Overview.md](Challenge-Project-Overview.md)
- [README.md](README.md)
- [src/nutrition_engine/ingredient_matcher.py](src/nutrition_engine/ingredient_matcher.py)
- The challenge overview links to additional external readings and resources, including USDA API documentation and research papers.

---

## 🙏 **Acknowledgements**

We want to thank our Challenge Advisor, Sakshi, for the opportunity to work on thie projects, and we want to thank our AI Studio Coach, Sai, for not just helping us in this endeavor, but for also being understanding and checking in on us

- Challenge Advisor: FNU Sakshi, sakshi.lindner@gmail.com
- AI Studio Coach: Sai Duddu