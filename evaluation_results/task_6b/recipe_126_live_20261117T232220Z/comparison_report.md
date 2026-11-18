# Live 126-ingredient Task 6B matcher comparison

Run folder: `evaluation_results/recipe_126_live_20261117T232220Z/`.

## Method

- Source was `data/recipes.json`: 26 recipes and 165 ingredient entries. Deduplication used Unicode NFKC normalization, casefolding, and trimming/collapsing whitespace; the first-seen original spelling is preserved. The resulting count is 126 unique ingredients.
- The original synchronous NLP matcher used only fresh USDA `/foods/search` responses fetched for this run (137 distinct normalized query strings). Captured responses were replayed within this run to the unchanged synchronous matcher; no prior snapshots or predictions were read.
- The hybrid matcher used the unchanged live `HybridIngredientMatcher.from_usda_client` workflow. Each ingredient was searched directly against USDA, SR Legacy first, then live NLP fallback according to the implementation. It made no use of saved candidates. The request log preserves every call and data type filter.
- Candidate search page size was 50. Selected FDC records were then fetched directly using a separate live USDA client. The initial detail-fetch loop referenced the already closed search client and made no requests; that local setup issue was corrected, and all 98 selected IDs were successfully fetched directly. This was not a USDA API failure.
- `recipes.json` does not provide expected FDC IDs for these names. No accuracy, precision, recall, or F1 is calculated. Manual quality classifications compare the selected record with the ingredient wording and are not ground-truth labeled metrics.

## Summary

| Measure | Original NLP | Task 6B hybrid |
|---|---:|---:|
| Ingredients processed | 126 | 126 |
| Accepted matches | 97 | 98 |
| Abstentions / review | 29 | 28 |
| Ingredient rows with at least one search API error | 0 | 0 |
| Successful API search requests | 137 distinct queries | 243 requests |
| Failed API search requests | 0 | 0 |
| Hybrid SR Legacy selections | — | 68 |
| Hybrid NLP fallback selections | — | 30 |
| Hybrid review cases | — | 28 |
| Both selected the same non-null FDC ID | — | 53 |
| Both abstained | — | 28 |
| Different outcomes (different ID or assignment vs abstention) | — | 45 |

The hybrid assigned one more ingredient than NLP (98 vs 97) and had one fewer abstention (28 vs 29). Among 126 ingredient names, both selected the same non-null FDC record for 53; both abstained for 28; their outcomes differed for 45. These counts say nothing by themselves about accuracy.

## Quality review

The review file contains 126 rows, one per ingredient, comparing both selected outputs. Each classification is a manual judgment against the text of the ingredient; no expected IDs exist, so `Exact` is not applicable. Nutrients from SR Legacy, Foundation, and Survey records are reported per 100 g. For Branded records, serving-based values were normalized to 100 g only when USDA supplied a positive serving size in grams; values could not be normalized for records with missing serving mass or an mL-only serving. Those cells are blank, and the raw API detail is retained. A nutrient reported as zero remains `0.00`; a blank cell means unavailable or not normalizable. Counts by matcher:

| Manual classification | NLP | Hybrid |
|---|---:|---:|
| Verified equivalent | 57 | 49 |
| Incorrect | 13 | 23 |
| Ambiguous | 56 | 54 |

“Verified equivalent” here means the retrieved description appears compatible with the named ingredient and does not show a contradictory requested form/modifier; it does not mean the FDC ID is ground-truth validated. Abstentions and uncertain interpretations remain ambiguous. Nutrient profiles per 100 g for selected records are in `quality_review.csv`; the detailed USDA responses, including nutrient identifiers/units and omitted nutrients, are in `selected_food_details.json`.

### Illustrative disagreements

- **Ginger:** NLP selected “Tea, ginger” for minced/julienned ginger; hybrid selected “Ginger root, raw”. This is a clear hybrid improvement in ingredient identity.
- **Low-fat curd:** NLP abstained while hybrid selected “Yogurt, plain, low fat”, a plausible alias-compatible assignment.
- **Onion:** NLP selected onion dip and hybrid selected onion powder for diced/finely chopped onion. Both are meaningful mismatches; SR Legacy did not solve this case.
- **Olive oil:** NLP selected olive oil; hybrid selected a corn/peanut/olive blend. Similar oil identity does not make the blend equivalent to pure olive oil.
- **Low-fat paneer:** both selected generic paneer records that do not establish the requested low-fat modifier. The hybrid’s selection for “regular paneer” was instead cheese crackers, an obvious mismatch.
- **Preparation and form remain important:** brown rice hybrid selection is dry, parboiled branded rice; several soaked/boiled bean or soy ingredient names received raw/dry records; tomato powder was selected for chopped tomato; split moong dal fell back to whole raw mung beans.
- **Modifiers/formulations matter:** hybrid selected chocolate low-fat milk for low-fat milk, vanilla nonfat yogurt for fat-free Greek yogurt, and an HVP-based reduced-sodium sauce for low-sodium soy sauce. These are not justified by text similarity alone.

The SR Legacy-first stage made 68 accepted SR Legacy selections; the existing NLP fallback made 30 accepted selections, including records outside SR Legacy. Across inspected disagreements it corrected some identity errors (ginger, low-fat curd) and introduced or retained others (onion powder, oil blend, chocolate milk, pasta with spinach, etc.). There is no ground-truth basis for claiming either matcher is more accurate overall.

## API status and limitations

- Original NLP: 137 unique live queries succeeded; 0 failed.
- Hybrid: 243 live search calls succeeded; 0 failed.
- FDC record details: 98 of 98 selected IDs retrieved; 0 failed.
- API failures and genuine successful empty results remain distinct in the candidate snapshots and `api_failures.json`.
- FDC search results are limited to 50 records per query and can change in future. The snapshots preserve this run’s candidate inputs.
- FDC nutrient fields absent from detail responses are not interpreted as zero. USDA branded products can have incomplete or formulation-specific descriptions.
- Manual review is necessarily limited by the recipe data: an ingredient name often omits brand, preparation, cultivar, or state. Ambiguous cases should remain subject to human review.

## Artifacts

- `comparison_report.md` — this report.
- `ingredient_results.csv` — exactly one row per unique ingredient with both matcher outputs, scores, stage, API error flag, and same-record indicator.
- `quality_review.csv` — 126 rows, selected descriptions/types, per-100g macros where reported, manual classifications and rationales.
- `nlp_candidate_snapshot.json`, `hybrid_candidate_snapshot.json` — candidate responses captured from live API calls.
- `nlp_raw_predictions.json`, `hybrid_raw_predictions.json` — full matcher outcomes.
- `selected_food_details.json` — direct FDC details for selected IDs.
- `api_failures.json`, `run_metadata.json`.
