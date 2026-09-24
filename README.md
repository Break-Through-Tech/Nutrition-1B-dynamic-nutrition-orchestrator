# AI Studio Challenge Project Title

> 💡 **Note for the team:** This is just a template. Update the above title with your AI Studio Challenge Project name. Remove all guidance notes and example text in this template and populate this README with your own content. You can work on this README throughout AI Studio, and get feedback from your AI Studio Coach and Challenge Advisor before finalizing it.  

---

### 👥 **Team Members**

| Name             | GitHub Handle | Contribution                                                             | LinkedIn Account                                 |
|------------------|---------------|--------------------------------------------------------------------------|--------------------------------------------------|
| Shirina Daniel   | @shirinadan   | (Deterministic macro calculation, recipe scaling, dietary restriction filtering, benchmark evaluation, automated testing)| www.linkedin.com/in/shirinadan/                  |
| Lakshmi Jinkala  |@lakshmijinkala|         (Error-recovery state loop, creative recipe generation)          | www.linkedin.com/in/lakshmijinkala               |
| Sadia Fathima    |@sluggysadi    | (Build the local recipe seed database,  Build the Streamlit UI)          | https://www.linkedin.com/in/sadiafathima         |

---

## 🎯 **Project Highlights**

**Example:**

- Developed a machine learning model using `[model type/technique]` to address `[challenge project task]`.
- Achieved `[key metric or result]`, demonstrating `[value or impact]` for `[host company]`.
- Generated actionable insights to inform business decisions at `[host company or stakeholders]`.
- Implemented `[specific methodology]` to address industry constraints or expectations.

---

## 👩🏽‍💻 **Setup and Installation**

**Provide step-by-step instructions so someone else can run your code and reproduce your results. Depending on your setup, include:**

* How to clone the repository
* How to install dependencies
* How to set up the environment
* How to access the dataset(s)
* How to run the notebook or scripts

---

## 🏗️ **Project Overview**

**Describe:**

- How this project is connected to the Break Through Tech AI Program
- Your AI Studio host company and the project objective and scope
- The real-world significance of the problem and the potential impact of your work

---

## 📊 **Data Exploration**

**You might consider describing the following (as applicable):**

* The dataset(s) used: origin, format, size, type of data
* Data exploration and preprocessing approaches
* Insights from your Exploratory Data Analysis (EDA)
* Challenges and assumptions when working with the dataset(s)

**Potential visualizations to include:**

* Plots, charts, heatmaps, feature visualizations, sample dataset images

---

## 🧠 **Model Development**

**You might consider describing the following (as applicable):**

* Model(s) used (e.g., CNN with transfer learning, regression models)
* Feature selection and Hyperparameter tuning strategies
* Training setup (e.g., % of data for training/validation, evaluation metric, baseline performance)


---

## 📈 **Results & Key Findings**

**You might consider describing the following (as applicable):**

* Performance metrics (e.g., Accuracy, F1 score, RMSE)
* How your model performed
* Insights from evaluating model fairness

**Potential visualizations to include:**

* Confusion matrix, precision-recall curve, feature importance plot, prediction distribution, outputs from fairness or explainability tools

---

## 🚀 **Next Steps**

**You might consider addressing the following (as applicable):**

* What are some of the limitations of your model?
* What would you do differently with more time/resources?
* What additional datasets or techniques would you explore?

---

## 📝 **License**

Specify how your project can be used by others. Choose an appropriate license and link it here (e.g., MIT, Apache 2.0). Make sure your Challenge Advisor approves of the selected license type. 

**Example:**
This project is licensed under the MIT License.

---

## 📄 **References** (Optional but encouraged)

Cite relevant papers, articles, or resources that supported your project.

---

## 🙏 **Acknowledgements** (Optional but encouraged)

Thank your Challenge Advisor, host company representatives, TA, and others who supported your project.

## Deterministic Macro Math Engine

This project includes a deterministic macro-calculation engine for calculating
ingredient nutrition totals from a canonical nutrition dataset.

### Data model

Each ingredient stores calories, protein, carbohydrates, and fat per 100 grams.

### Calculation formula

For a requested ingredient quantity:

```text
scale_factor = requested_grams / 100
total_macro = macro_per_100g * scale_factor
```

For example, chicken breast contains 31 grams of protein per 100 grams.
For 250 grams of chicken breast:

```text
protein = 31 * (250 / 100) = 77.5g
```

### Ingredient scaling

The system supports:

- Scaling an ingredient with a multiplier
- Scaling to an exact target quantity in grams
- Scaling recipe ingredients when serving counts change

Macro totals are always recalculated from the canonical per-100g nutrition
record rather than from previously rounded values.

### Evaluation benchmarks

The project uses benchmark cases to verify:

- Macro calculation accuracy
- Quantity scaling accuracy
- Recipe-serving scaling accuracy
- Deterministic repeated results
- Invalid-input handling

The expected threshold for deterministic calculation benchmarks is 100%.

### Running tests

Install dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
pytest
```

The evaluation helpers are available from `nutrition_engine.benchmarks`:

- `calculate_mae_percent`: percentage mean absolute error with a 2% target
- `calculate_f1_score`: dependency-free binary F1 calculation
- `track_constraint_compliance`: per-meal and aggregate protein/calorie compliance

Recipe quantities can be scaled with `scale_recipe_to_targets`. It scales all
ingredients uniformly to meet a minimum protein target and raises an error when
the calorie cap cannot be satisfied. The default targets are 140 g protein and
2,000 kcal.

## Restriction-aware planning

`nutrition_engine.meal_planner` provides a deterministic recipe selector for the
local `data/recipes.json` seed bank. It supports vegetarian, vegan, dairy-free,
nut-free, and gluten-free restrictions. An optional backend can rank the already
filtered candidates, but the planner validates every returned recipe ID and
falls back to deterministic selection when the backend is unavailable or unsafe.

For local LLM selection, pass `OllamaBackend()` to `MealPlanningAgent`. Ollama
is optional; if its local endpoint is unavailable, the same deterministic
restriction-filtered plan is returned.

The planner does not invent macros for recipe ingredients missing from the
canonical nutrition catalog. Those ingredients must be resolved through the
USDA pipeline before macro totals are reported.

## Ingredient Matching (USDA Entity Resolution)

*Task 6 — Maddux.*

`nutrition_engine.ingredient_matcher` resolves a raw recipe ingredient string
to a USDA FoodData Central record. This is the link between the recipe seed
bank and the deterministic macro engine: until an ingredient has an FDC ID,
no verified macro value exists for it.

### Pipeline

Matching runs in three stages, each testable on its own.

1. **Normalization** turns a raw string into ordered search queries.
   Preparation state after a comma is discarded, parentheticals are tried
   first, and Indian ingredient names are mapped to the English terms USDA
   indexes.

   ```text
   "low-fat paneer, crumbled"   -> low-fat paneer cheese, paneer cheese
   "kala namak (black salt)"    -> black salt, kala namak
   "moong dal, soaked overnight" -> mung beans, moong dal
   "hing"                       -> asafoetida
   ```

2. **Search** is injected rather than hardcoded. `usda_search` adapts the
   Task 1 `USDAClient`, so the matcher itself performs no network calls and
   the test suite runs offline.

3. **Scoring** rates each candidate from 0.0 to 1.0, led by how many query
   terms appear in the USDA description, then adjusted for record quality and
   for forms the recipe did not ask for (cooked, flavoured, flour, prepared
   dishes). The individual rules and the failure each one fixes are listed
   under Results.

### Refusing to guess

Two cases deliberately return no FDC ID:

- **Composite entries** such as `kadhai spice mix`, `onion-tomato gravy base`,
  or `quinoa-rice blend`. No single USDA record is correct for a prepared
  mixture, so the matcher reports `reason="composite"`.
- **Low-confidence matches** below the accept threshold (default 0.80, chosen
  by sweep -- see Results), which report `reason="below_threshold"` along with
  the candidates considered.

An unmatched ingredient is visible and fixable. A confidently wrong FDC ID is
neither: it feeds a plausible but incorrect macro into the deterministic
engine, which will then be exactly correct about a number that was never
right. Declining to answer is the safer failure.

### Reproducible evaluation

An F1 score measured against a live API cannot be checked by anyone else.
`scripts/snapshot_usda_candidates.py` captures USDA results once to
`data/usda_candidates.json`; every later run replays that snapshot offline and
produces the same number, with no API key required.

```bash
# One time, requires a key in .env
python scripts/snapshot_usda_candidates.py --validation

# Anytime, offline and reproducible
python scripts/evaluate_matcher.py
python scripts/evaluate_matcher.py --sweep    # F1 across accept thresholds
```

### Setup: supplying an API key

The USDA key is personal and must never be committed. Each person supplies
their own through a local `.env` file that git ignores.

```bash
pip install -r requirements.txt

cp .env.example .env            # PowerShell: Copy-Item .env.example .env
# edit .env and replace your_key_here with a real key

python scripts/check_api_key.py # confirms the key is found and works
```

Get a free key instantly at <https://fdc.nal.usda.gov/api-key-signup>. A
personal key allows 1,000 requests/hour; the shared `DEMO_KEY` allows only 30,
which is not enough for a full capture.

`nutrition_engine.config` loads `.env` into the process environment, so the
Task 1 `USDAClient` — which reads `os.getenv("USDA_API_KEY")` — picks the key
up with no change to `API_File.py`. An already-exported environment variable
takes precedence over the file, so CI secrets are never overridden by a stale
local copy.

### Running the whole pipeline

```bash
python scripts/run_task6.py
```

This runs every stage in order and stops with an instruction whenever a stage
needs input: it verifies the key, captures USDA candidates, opens the
interactive labeler for any rows still missing a ground-truth FDC ID, then
scores the matcher. Re-running skips completed stages, so it is safe to stop
and resume.

| Script | Purpose |
| :--- | :--- |
| `check_api_key.py` | Confirm the key is found and accepted by USDA |
| `snapshot_usda_candidates.py` | Capture USDA results to `data/usda_candidates.json` |
| `label_validation_set.py` | Record human-confirmed FDC IDs for the 30-item set |
| `evaluate_matcher.py` | Score precision, recall, and F1 offline |
| `run_task6.py` | Run all of the above in order |

Ground-truth labels are recorded by a person, not generated. An F1 score
measured against machine-produced ground truth measures only that the matcher
agrees with itself.

### Validation set

`data/validation_set.csv` holds 30 ingredients sampled from the 126 in
`data/ingredients.csv`, every row traceable verbatim to that file. The sample
is stratified by difficulty so a failure points at a cause rather than a
single opaque score:

| Tier | Rows | What it exercises |
| :--- | :--- | :--- |
| `direct` | 6 | Plain English terms USDA indexes as written |
| `synonym` | 9 | Indian names with no direct USDA entry (hing, rajma, degi mirch) |
| `prep_note` | 6 | Preparation state that must be stripped before searching |
| `modifier` | 5 | Modifiers that change macros (fat-free vs low-fat) |
| `composite` | 4 | Entries that must return no match at all |

The four composite rows are true negatives. Without them F1 collapses into
plain accuracy, and a matcher that assigns some record to everything would
appear to score well.

### Scoring rules

`nutrition_engine.matcher_eval` classifies each row as TP, FP, FN, or TN.
Matching an ingredient to the **wrong** FDC ID counts as a false positive
rather than a miss, because a wrong identifier is the failure that corrupts
downstream macros. `calculate_f1_score` from `nutrition_engine.benchmarks`
(Task 5) is reported alongside as a cross-check on the coarser
"matched or not" framing.

### Supplying macros to the math engine

`usda_search.load_macros()` reads per-100g calories, protein, carbohydrates,
and fat out of the snapshot, keyed by FDC ID. These are the four values
`IngredientNutrition` requires, sourced from USDA rather than entered by hand.

### Results

Measured against the 30-item validation set, captured from USDA FoodData
Central on 2026-09-23 (`data/usda_candidates.json`, 47 queries at 50 results
each). Reproduce offline with `python scripts/evaluate_matcher.py`.

| Metric | Value |
| :--- | :--- |
| Precision | 82.61% |
| Recall | 100.00% |
| **F1** | **90.48%** |
| Target | > 90% — met |

TP 19, FP 4, FN 0, TN 7.

| Tier | n | TP | FP | FN | TN |
| :--- | --: | --: | --: | --: | --: |
| direct | 6 | 5 | 1 | 0 | 0 |
| synonym | 9 | 6 | 0 | 0 | 3 |
| prep_note | 6 | 5 | 1 | 0 | 0 |
| modifier | 5 | 3 | 2 | 0 | 0 |
| composite | 4 | 0 | 0 | 0 | 4 |

Scoring rules that produced this, each added to fix an observed failure class:

- **Base-form preference.** A recipe naming "quinoa" means the grain, not
  "Quinoa, cooked". Records carrying an unrequested transformation are
  penalised. This alone moved F1 from 70.0% to 81.8% — mung beans are 23.9g
  protein raw against 6.5g cooked, so the error class was also the most
  damaging one.
- **Derivative rejection.** "Flour, rice, brown" is milled rice, not rice.
- **Dish rejection.** A conjunction in the leading segment ("Kidney beans with
  meat") marks a prepared dish rather than an ingredient.
- **Record-quality preference.** Curated Foundation/SR Legacy records are
  favoured over Branded ones, modestly: several ingredients (kala namak, kala
  chana, urad dal) exist in USDA *only* as branded records, so a hard rule
  lost them entirely.
- **Retrieval depth.** At 10 results per query, branded products crowded out
  every curated record for common terms like quinoa and paprika. The capture
  now requests the maximum 50.

### Honest limitations

- **The margin is 0.48 points.** This clears the target but is not comfortable.
- **The threshold was tuned on this same set.** Success criterion 2 specifies
  an *unseen* validation set; 0.80 was selected by sweeping against these 30
  ingredients, so the true out-of-sample figure is likely lower. A genuinely
  held-out set should be scored before this number is presented as final.
- **Three of the four remaining errors are record-quality calls**, not
  identification failures. For extra-firm tofu, low-fat Greek yogurt, and whey
  protein the matcher found the right *food* but chose a branded record where
  a lab-analyzed one exists. Branded entries carry label values that disagree
  (extra-firm tofu ranges 5.88-9.98g protein across records), which is why the
  curated record is treated as the correct answer.
- **Ground truth reflects one person's judgement.** Where several USDA records
  are defensible, the curated record was chosen and the reasoning recorded in
  the `notes` column of `data/validation_set.csv`.
- **USDA has no record for hing, kasuri methi, or ajwain.** These are labeled
  as having no correct record, and the matcher correctly declines all three.
  Recipes using them need a documented fallback, since their macros cannot be
  sourced from USDA at all.
- **Keyword matching is at its ceiling here.** Later tuning rounds traded one
  error for another rather than reducing the total, which is the expected
  motivation for Task 9's semantic retrieval.
