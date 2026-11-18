# Task 6B: all-FDC-type hybrid evaluation

## Implementation and run provenance

- Updated matcher searches FoodData Central without a `dataType` restriction, so Survey (FNDDS), SR Legacy, Foundation, and Branded records are all eligible. It applies score threshold, ingredient identity/form, preparation, and requested-modifier compatibility before selection. If multiple suitable candidates remain, it uses the existing curated-versus-Branded tier as a secondary preference and then text score. It falls back to the original NLP matcher if the candidate stage finds no suitable record; composite and no-match cases remain review/abstention outcomes.
- The original NLP matcher module and its retrieval/scoring/threshold/decision logic were not changed. The equivalence review is post-hoc and does not affect matching.
- Fresh live run captured at 2026-11-18T03:38:30.179942+00:00 UTC from the unchanged 30-row `data/validation_set.csv`. The updated hybrid run scored 30/30 with zero API failures. Candidate responses are saved in `live_candidate_snapshot.json`; the baseline snapshot is preserved as a separate reference.
- Direct USDA record details for all 29 unique expected/selected IDs were successfully retrieved; detail failures: 0. Nutrient values for these FDC types are standardized per 100 g by USDA; Branded records are standardized from label serving values. [USDA Global Branded Food Products Database documentation](https://fdc.nal.usda.gov/GBFPD_Documentation/)
- The original NLP baseline metrics and post-hoc classifications are reused from the November 15 baseline and November 17 fresh comparison. The November 17 fresh NLP predictions reproduced the original baseline exactly.

## Exact-ID metrics

| Run | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN | Assignments / rate | API failures | Abstentions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original NLP baseline, Nov 15 | 76.67% | 72.73% | 94.12% | 82.05% | 16 | 6 | 7 | 1 | 22/30 (73.33%) | 0 | 8 |
| Updated hybrid, fresh live Nov 18 | 80.00% | 73.91% | 100.00% | 85.00% | 17 | 6 | 7 | 0 | 23/30 (76.67%) | 0 | 7 |

The Task 6B hybrid improved exact-ID accuracy by 3.33 percentage points and exact-ID F1 by 2.95 points versus the original NLP baseline.

## Equivalence-aware metrics (post-hoc)

| Prediction set | Accuracy | Precision | Recall | F1 | Exact | Verified equivalent | Incorrect | Ambiguous excluded | Correct abstentions | Missed matches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original NLP baseline, post-hoc (26/30 decisive) | 88.46% | 88.89% | 94.12% | 91.43% | 16 | 0 | 2 | 4 | 7 | 1 |
| Updated hybrid, post-hoc (29/30 decisive) | 93.10% | 90.91% | 100.00% | 95.24% | 17 | 3 | 2 | 1 | 7 | 0 |

Equivalence metrics exclude ambiguous assignments: NLP denominator 26/30, hybrid denominator 29/30. Confusion counts use exact plus verified equivalent as TP; incorrect as FP; correct abstention as TN; missed expected match as FN. These post-hoc metrics are selective manual adjudications and should not be confused with exact-ID metrics. The original NLP equivalence row is post-hoc scoring of the November 15/17 identical predictions.

## Selected FDC data types

| Selected data type | Assigned records |
| --- | --- |
| Branded | 6 |
| Foundation | 1 |
| SR Legacy | 5 |
| Survey (FNDDS) | 11 |
All four requested data types appeared among selected records. The hybrid accepted 21 records at the all-data-type candidate stage and 2 via the original NLP fallback; 7 rows were abstained/review. It assigned 23/30 (76.67%).

## All 30 ingredient outcomes

| Ingredient | Expected record | Original NLP selected record and class | Updated hybrid selected record, stage, and class |
| --- | --- | --- | --- |
| oats | 2708489: Oats, raw [Survey (FNDDS)] | 2779253: Oats, puffed [Foundation] — Incorrect | 2708489: Oats, raw [Survey (FNDDS)] — all_data_types — Exact match |
| quinoa | 168874: Quinoa, uncooked [SR Legacy] | 168874: Quinoa, uncooked [SR Legacy] — Exact match | 168874: Quinoa, uncooked [SR Legacy] — all_data_types — Exact match |
| brown rice | 2710789: Rice, brown, cooked, as ingredient [Survey (FNDDS)] | 2779256: Brown rice, puffed [Foundation] — Incorrect | 2286928: BROWN RICE [Branded] — all_data_types — Incorrect |
| almonds | 2707485: Almonds, NFS [Survey (FNDDS)] | 2707485: Almonds, NFS [Survey (FNDDS)] — Exact match | 2707485: Almonds, NFS [Survey (FNDDS)] — all_data_types — Exact match |
| chia seeds | 2707590: Chia seeds [Survey (FNDDS)] | 2707590: Chia seeds [Survey (FNDDS)] — Exact match | 2707590: Chia seeds [Survey (FNDDS)] — all_data_types — Exact match |
| olive oil | 2710186: Olive oil [Survey (FNDDS)] | 2710186: Olive oil [Survey (FNDDS)] — Exact match | 2710186: Olive oil [Survey (FNDDS)] — all_data_types — Exact match |
| hing | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| rajma | 2707379: Kidney beans, NFS [Survey (FNDDS)] | 2707379: Kidney beans, NFS [Survey (FNDDS)] — Exact match | 2707379: Kidney beans, NFS [Survey (FNDDS)] — all_data_types — Exact match |
| kasuri methi | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| kala namak (black salt) | 2587261: BLACK SALT [Branded] | 2587261: BLACK SALT [Branded] — Exact match | 2587261: BLACK SALT [Branded] — all_data_types — Exact match |
| whole wheat flour (atta) | 790085: Flour, whole wheat, unenriched [Foundation] | 790085: Flour, whole wheat, unenriched [Foundation] — Exact match | 790085: Flour, whole wheat, unenriched [Foundation] — all_data_types — Exact match |
| ghee | 171314: Butter, Clarified butter (ghee) [SR Legacy] | 171314: Butter, Clarified butter (ghee) [SR Legacy] — Exact match | 171314: Butter, Clarified butter (ghee) [SR Legacy] — all_data_types — Exact match |
| degi mirch | 171329: Spices, paprika [SR Legacy] | 171329: Spices, paprika [SR Legacy] — Exact match | 171329: Spices, paprika [SR Legacy] — all_data_types — Exact match |
| carom seeds (ajwain) | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| dry soya chunks | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] — Exact match | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] — all_data_types — Exact match |
| moong dal, soaked overnight | 174256: Mung beans, mature seeds, raw [SR Legacy] | 174256: Mung beans, mature seeds, raw [SR Legacy] — Exact match | 174256: Mung beans, mature seeds, raw [SR Legacy] — all_data_types — Exact match |
| low-fat paneer, crumbled | 2705740: Cheese, paneer [Survey (FNDDS)] | 2705740: Cheese, paneer [Survey (FNDDS)] — Exact match | 2705740: Cheese, paneer [Survey (FNDDS)] — nlp_fallback — Exact match |
| extra-firm tofu, cubed | 174290: Tofu, extra firm, prepared with nigari [SR Legacy] | 2310367: EXTRA-FIRM TOFU [Branded] — Ambiguous | 2310367: EXTRA-FIRM TOFU [Branded] — all_data_types — Verified equivalent |
| kala chana, soaked overnight and boiled | 2134686: KALA CHANA [Branded] | 2054512: KALA CHANA [Branded] — Ambiguous | 2054512: KALA CHANA [Branded] — nlp_fallback — Ambiguous |
| kabuli chana, soaked and boiled | 2707414: Chickpeas, NFS [Survey (FNDDS)] | 2707414: Chickpeas, NFS [Survey (FNDDS)] — Exact match | 2707414: Chickpeas, NFS [Survey (FNDDS)] — all_data_types — Exact match |
| garlic, minced | 2709786: Garlic, raw [Survey (FNDDS)] | 2709786: Garlic, raw [Survey (FNDDS)] — Exact match | 2709786: Garlic, raw [Survey (FNDDS)] — all_data_types — Exact match |
| low-fat Greek yogurt | 2705423: Yogurt, Greek, low fat milk, plain [Survey (FNDDS)] | 2536668: LOW-FAT GREEK YOGURT [Branded] — Ambiguous | 170903: Yogurt, Greek, plain, lowfat [SR Legacy] — all_data_types — Verified equivalent |
| unflavored whey protein | 173180: Beverages, Protein powder whey based [SR Legacy] | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — Ambiguous | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — all_data_types — Incorrect |
| low-sodium soy sauce | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] — Exact match | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] — all_data_types — Exact match |
| fat-free Greek yogurt | 2076798: FAT-FREE GREEK YOGURT [Branded] | 2076798: FAT-FREE GREEK YOGURT [Branded] — Exact match | 2705432: Yogurt, Greek, nonfat milk, fruit [Survey (FNDDS)] — all_data_types — Verified equivalent |
| whole black urad dal | 2168881: WHOLE BLACK GRAM [Branded] | —: — [—] — Missed match | 2168881: WHOLE BLACK GRAM [Branded] — all_data_types — Exact match |
| kadhai spice mix (crushed coriander seeds / dry red chili) | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| onion-tomato gravy base | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| mint-cilantro-yogurt chutney | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| quinoa-rice blend | No expected ID | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |

## Different-ID assignments and nutrient evidence

Macro tuple order: kcal / protein / carbohydrate / fat / fiber per 100 g. Delta is selected minus expected; `—` means the nutrient is unavailable in the API record, not zero. Explicit zeros (for example fiber 0.00 g) remain numeric. Energy reported only in kJ was converted to kcal using 1 kcal = 4.184 kJ. The six updated-hybrid differing-ID assignments are reviewed alongside the original NLP differing-ID cases.

| Matcher | Ingredient | Expected record | Selected record | Expected macros | Selected macros | Delta | Class | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original NLP | oats | 2708489 Survey (FNDDS): Oats, raw | 2779253 Foundation: Oats, puffed | 379.00 / 13.20 / 67.70 / 6.52 / 10.10 | 402.11 / 14.56 / 70.55 / 6.85 / 8.79 | +23.11 / +1.36 / +2.85 / +0.33 / -1.31 | Incorrect | Puffed oats are explicitly a different preparation/form from the expected raw oats. |
| Original NLP | brown rice | 2710789 Survey (FNDDS): Rice, brown, cooked, as ingredient | 2779256 Foundation: Brown rice, puffed | 124.00 / 2.45 / 25.90 / 1.12 / 1.00 | 377.14 / 7.81 / 80.26 / 2.76 / 2.70 | +253.14 / +5.36 / +54.36 / +1.64 / +1.70 | Incorrect | Expected record is cooked brown rice; selected record is puffed brown rice. |
| Original NLP | extra-firm tofu, cubed | 174290 SR Legacy: Tofu, extra firm, prepared with nigari | 2310367 Branded: EXTRA-FIRM TOFU | 83.41 / 9.98 / 1.18 / 5.26 / 1.00 | — / 10.71 / 3.57 / 5.36 / 1.20 | — / +0.73 / +2.39 / +0.10 / +0.20 | Ambiguous | Both are extra-firm tofu, but selected branded detail has unavailable energy and does not establish ingredient formulation equivalence. |
| Original NLP | kala chana, soaked overnight and boiled | 2134686 Branded: KALA CHANA | 2054512 Branded: KALA CHANA | 363.00 / 20.00 / 60.00 / 5.71 / 17.10 | 368.00 / 16.84 / 66.32 / 4.21 / 34.70 | +5.00 / -3.16 / +6.32 / -1.50 / +17.60 | Ambiguous | Both descriptions say kala chana, but they are distinct branded records with sizable fiber/macronutrient differences and unclear preparation. |
| Original NLP | low-fat Greek yogurt | 2705423 Survey (FNDDS): Yogurt, Greek, low fat milk, plain | 2536668 Branded: LOW-FAT GREEK YOGURT | 67.00 / 10.20 / 3.60 / 1.36 / 0.00 | 125.00 / 6.25 / 17.19 / 3.12 / 0.80 | +58.00 / -3.95 / +13.59 / +1.76 / +0.80 | Ambiguous | Selected branded description omits plainness; its carbohydrate and calorie values differ substantially from the expected plain FNDDS yogurt. |
| Original NLP | unflavored whey protein | 173180 SR Legacy: Beverages, Protein powder whey based | 2510560 Branded: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 351.82 / 78.13 / 6.25 / 1.56 / 3.10 | 360.00 / 80.00 / 4.00 / 4.00 / 0.00 | +8.18 / +1.87 / -2.25 / +2.44 / -3.10 | Ambiguous | Selected record is an unflavored branded powder, but formulation and fiber/nutrient values differ; broad product identity is insufficient. |
| Updated hybrid | brown rice | 2710789 Survey (FNDDS): Rice, brown, cooked, as ingredient | 2286928 Branded: BROWN RICE | 124.00 / 2.45 / 25.90 / 1.12 / 1.00 | 378.00 / 8.89 / 75.56 / 3.33 / 6.70 | +254.00 / +6.44 / +49.66 / +2.21 / +5.70 | Incorrect | Expected FNDDS record is cooked brown rice; selected branded record is long-grain brown rice with a dry ingredient list. The per-100g energy/carbohydrate values are 124 kcal/25.9 g versus 378 kcal/75.56 g, consistent with different preparation states. |
| Updated hybrid | extra-firm tofu, cubed | 174290 SR Legacy: Tofu, extra firm, prepared with nigari | 2310367 Branded: EXTRA-FIRM TOFU | 83.41 / 9.98 / 1.18 / 5.26 / 1.00 | — / 10.71 / 3.57 / 5.36 / 1.20 | — / +0.73 / +2.39 / +0.10 / +0.20 | Verified equivalent | Both records identify extra-firm tofu. The selected Branded ingredient list is water, organic soybeans, calcium sulfate, and magnesium chloride (nigari is magnesium chloride); preparation and identity are compatible. Protein/fat/fiber are close per 100 g; selected energy is not reported and carbohydrate is 3.57 g vs 1.18 g. |
| Updated hybrid | kala chana, soaked overnight and boiled | 2134686 Branded: KALA CHANA | 2054512 Branded: KALA CHANA | 363.00 / 20.00 / 60.00 / 5.71 / 17.10 | 368.00 / 16.84 / 66.32 / 4.21 / 34.70 | +5.00 / -3.16 / +6.32 / -1.50 / +17.60 | Ambiguous | Both descriptions say KALA CHANA, but selected record lists black chickpeas while expected lists whole black gram. Fiber is 34.7 g vs 17.1 g/100 g and the label ingredient wording conflicts. Available evidence cannot confidently resolve whether these are equivalent pulses or different products. |
| Updated hybrid | low-fat Greek yogurt | 2705423 Survey (FNDDS): Yogurt, Greek, low fat milk, plain | 170903 SR Legacy: Yogurt, Greek, plain, lowfat | 67.00 / 10.20 / 3.60 / 1.36 / 0.00 | 72.90 / 9.95 / 3.94 / 1.92 / 0.00 | +5.90 / -0.25 / +0.34 / +0.56 / +0.00 | Verified equivalent | Both records describe plain, low-fat Greek yogurt. Per 100 g: 67 vs 72.9 kcal, protein 10.2 vs 9.95 g, carbohydrates 3.6 vs 3.94 g, fat 1.36 vs 1.92 g, fiber 0 vs 0 g. |
| Updated hybrid | unflavored whey protein | 173180 SR Legacy: Beverages, Protein powder whey based | 2510560 Branded: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 351.82 / 78.13 / 6.25 / 1.56 / 3.10 | 360.00 / 80.00 / 4.00 / 4.00 / 0.00 | +8.18 / +1.87 / -2.25 / +2.44 / -3.10 | Incorrect | Selected Branded ingredients contain whey concentrate, whey isolate, and micellar casein. The added casein makes this a whey/casein blend rather than the expected whey-based protein. Similar protein/calories do not establish identity; selected fiber is reported zero vs 3.1 g/100 g expected. |
| Updated hybrid | fat-free Greek yogurt | 2076798 Branded: FAT-FREE GREEK YOGURT | 2705432 Survey (FNDDS): Yogurt, Greek, nonfat milk, fruit | 93.00 / 7.33 / 12.67 / 1.33 / 0.70 | 83.00 / 9.21 / 10.80 / 0.34 / 0.10 | -10.00 / +1.88 / -1.87 / -0.99 / -0.60 | Verified equivalent | Expected Branded ingredients describe nonfat Greek yogurt with a mango/pineapple fruit preparation; selected Survey record is Greek nonfat yogurt with fruit. Identity, nonfat modifier, and fruit form are compatible. Values differ moderately per 100 g (93 vs 83 kcal; protein 7.33 vs 9.21 g; carbs 12.67 vs 10.8 g; fat 1.33 vs 0.34 g; fiber 0.7 vs 0.1 g), so retain the evidence in the CSV. |

## Case notes

- Brown rice: the selected Branded record contains long-grain brown rice, but the expected record is cooked brown rice; per-100 g energy and carbohydrate levels are far higher in the selected record, consistent with dry vs cooked preparation. Incorrect.
- Extra-firm tofu: Branded product ingredient details identify soybeans and nigari-related magnesium chloride. It is extra-firm tofu; macro values are close, though energy is absent. Verified equivalent with this nutrient limitation disclosed.
- Kala chana: two Branded records share the title, but one lists whole black gram and the other black chickpeas; fiber differs by 17.6 g/100 g. Ambiguous, not credited.
- Plain low-fat Greek yogurt: description and all reported macro values are compatible; verified equivalent.
- Unflavored whey: selected branded ingredient list includes micellar casein in addition to whey concentrate/isolate. Incorrect despite similar calories/protein.
- Fat-free Greek yogurt: expected Branded ingredient list includes a mango/pineapple fruit preparation and selected FNDDS is nonfat Greek yogurt with fruit. Both identify fruit yogurt; nutrient differences are shown above and considered modest in absolute grams, so verified equivalent.

## API failures and limitations

- All-data-type live search had 0 failed queries; direct record lookups had 0 failures. No saved candidate responses were used as live inputs. The original baseline candidate snapshot was used only as the controlled baseline/fallback reference documented by the evaluator.
- The search API returns a bounded candidate window (page size 50); lack of a record in that window does not prove FDC has no such record.
- The Branded whey record illustrates that API candidate descriptions may omit formulation ingredients; the ingredient list was available only after direct detail retrieval, so the matcher accepted a record the manual review classifies as incompatible.
- The NLP fallback intentionally retains original NLP behavior and can accept candidates that fail the stricter primary suitability checks. It is preserved by requirement; fallback stage is visible in the result trace.
- Equivalence is a manual adjudication supported by direct USDA descriptions, ingredients, preparation, and nutrients. Ambiguous kala chana and energy-missing tofu evidence are retained transparently; ambiguous does not count as correct.
- Two earlier live runs in this implementation cycle are retained unchanged in sibling timestamped folders. This report uses only the final-code run `hybrid_all_fdc_20261118T033809Z`.

## Artifacts

- `evaluation_report.md` — exact-ID live evaluation generated by the evaluator.
- `final_evaluation_report.md` — this comparison and post-hoc equivalence report.
- `hybrid_results.json` — raw predictions, exact metrics, stages, and failures.
- `live_candidate_snapshot.json` and `baseline_nlp_candidate_snapshot_reference.json`.
- `fdc_record_details.json` — direct live details.
- `equivalence_review.json` — per-row post-hoc classifications and macro profiles.
- `comparison_results.csv` — all 30 rows with both matcher outcomes and classes.
