# TASK 6: Keyword/NLP ingredient matching (USDA entity resolution)

Resolves raw recipe ingredient strings to USDA FoodData Central records,
connecting the recipe seed bank (Task 2) to the deterministic macro engine
(Task 4), which until now had no verified nutrient source for any of the
126 ingredients in data/ingredients.csv.

Result: F1 90.48% (precision 82.61%, recall 100%) on the 30-item validation
set, against the >90% target in success criterion 2.

### Pipeline:
- ingredient_matcher.py  normalize -> search -> score, no network dependency
- usda_search.py         adapts Task 1's USDAClient; offline snapshot replay
- matcher_eval.py        TP/FP/FN/TN scoring with per-tier breakdown
- config.py              .env loading so each person supplies their own key

### Scoring rules, each added to fix an observed failure class:
- Base-form preference: "quinoa" means the grain, not "Quinoa, cooked".
  Moved F1 from 70.0% to 81.8%; mung beans are 23.9g protein raw against
  6.5g cooked, so this was also the most damaging error class.
- Derivative rejection: "Flour, rice, brown" is milled rice, not rice.
- Dish rejection: a conjunction in the leading segment marks a prepared dish.
- Record quality: curated Foundation/SR Legacy preferred over Branded,
  modestly, since kala namak, kala chana and urad dal exist only as branded.
- Retrieval depth raised to 50; at 10, branded products crowded out every
  curated record for common terms like quinoa and paprika.

Reproducibility: data/usda_candidates.json snapshots the USDA responses, so
the reported F1 can be re-derived offline by anyone without an API key.

### Also:
- API_File.py: carry USDA's dataType through USDAFood (additive, optional).
  Without it, curated records cannot be preferred over branded ones.
- requirements.txt: add httpx and pydantic, which the code already needed.
- .gitignore: exclude .env; add .env.example as a committed template.
- README.md: restore Sadia Fathima's team-table row, dropped by becb424.

Known limitations are documented in README.md under "Honest limitations":
the margin over target is 0.48 points, the accept threshold was tuned on
this same validation set rather than a held-out one, and USDA has no record
at all for hing, kasuri methi or ajwain.
