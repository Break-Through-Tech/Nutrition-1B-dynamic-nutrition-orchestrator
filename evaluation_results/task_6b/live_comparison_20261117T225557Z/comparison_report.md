# Fresh live Task 6 evaluation comparison

Evaluation folder: `evaluation_results/live_comparison_20261117T225557Z/`.

## Run provenance

- NLP run captured 2026-11-17T22:56:41.358207+00:00 UTC; 30 validation rows; direct USDA search responses saved in `nlp/candidate_snapshot.json`.
- Hybrid run captured 2026-11-17T22:58:39.913853+00:00 UTC; direct SR Legacy searches and live NLP fallback searches; no saved candidate snapshot input.
- Direct `/food/{fdcId}` record detail lookups captured 2026-11-17T23:01:45.025406+00:00 UTC: 31/31 unique expected/selected IDs retrieved, no detail failures.
- Both live search evaluations had zero API query failures and scored 30/30 rows. `hybrid/api_failures.json` records the empty failure set.
- The same unchanged `data/validation_set.csv` and exact-ID scoring definitions were used.
- Fresh candidate payloads matched the prior live captures: NLP 47/47 query responses identical; hybrid 39 SR Legacy and 22 live NLP fallback responses identical; zero response differences or errors. Fresh selected predictions also match prior predictions.

## Exact-ID metric comparison

| Run | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN | Assignment | API failures | Abstentions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Previous original NLP baseline (Nov 15) | 76.67% | 72.73% | 94.12% | 82.05% | 16 | 6 | 7 | 1 | 73.33% | 0 | 8 |
| Fresh live original NLP (Nov 17) | 76.67% | 72.73% | 94.12% | 82.05% | 16 | 6 | 7 | 1 | 73.33% | 0 | 8 |
| Previous fully live hybrid (Nov 16) | 53.33% | 40.91% | 90.00% | 56.25% | 9 | 13 | 7 | 1 | 73.33% | 0 | 8 |
| Fresh live hybrid (Nov 17) | 53.33% | 40.91% | 90.00% | 56.25% | 9 | 13 | 7 | 1 | 73.33% | 0 | 8 |

Fresh NLP and hybrid runs reproduced previous live results exactly. There is no observed evidence of candidate drift or API failures causing performance changes. The hybrid continues to reduce exact-ID performance relative to NLP because its own SR-first decisions differ; this is not an evaluation-method change. The earlier 87.50% hybrid F1 is a proposed equivalence-based calculation on adjudicated rows, not the exact-ID outcome of a live matcher run.

### Complete 30-row predictions

Every row is retained in the two per-run reports: [NLP report](nlp/evaluation_report.md), [hybrid report](hybrid/evaluation_report.md), and machine-readable results in `nlp/nlp_results.json` and `hybrid/hybrid_results.json`. The reports list all 30 ingredients, expected and selected IDs, descriptions, data types, stage, correctness, and abstention.

## Differing-ID equivalence review

Macro tuple order is kcal / protein / carbohydrate / fat / fiber per 100 g. Nutrient values are the live FDC record values on a per-100g basis. `—` means that nutrient was not reported, not zero. All reported zeros remain explicit in `fdc_record_details.json`. Percent deltas and nutrient-presence flags are in `equivalence_review.json`.

### Original NLP

| Ingredient | Expected (ID; type; description) | Selected (ID; type; description) | Expected macros | Selected macros | Class | Evidence-based reason |
|---|---|---|---|---|---|
| oats | 2708489; Survey (FNDDS); Oats, raw | 2779253; Foundation; Oats, puffed | 379 / 13.2 / 67.7 / 6.52 / 10.1 | — / 14.5625 / 70.5525 / 6.85 / 8.79 | Incorrect | Puffed oats are explicitly a different preparation/form from the expected raw oats. |
| brown rice | 2710789; Survey (FNDDS); Rice, brown, cooked, as ingredient | 2779256; Foundation; Brown rice, puffed | 124 / 2.45 / 25.9 / 1.12 / 1.0 | — / 7.8125 / 80.2625 / 2.76 / 2.7 | Incorrect | Expected record is cooked brown rice; selected record is puffed brown rice. |
| extra-firm tofu, cubed | 174290; SR Legacy; Tofu, extra firm, prepared with nigari | 2310367; Branded; EXTRA-FIRM TOFU | 83.0 / 9.98 / 1.18 / 5.26 / 1.0 | — / 10.71 / 3.57 / 5.36 / 1.2 | Ambiguous | Both are extra-firm tofu, but selected branded detail has unavailable energy and does not establish ingredient formulation equivalence. |
| kala chana, soaked overnight and boiled | 2134686; Branded; KALA CHANA | 2054512; Branded; KALA CHANA | 363.0 / 20.0 / 60.0 / 5.71 / 17.1 | 368.0 / 16.84 / 66.32 / 0.0 / 34.7 | Ambiguous | Both descriptions say kala chana, but they are distinct branded records with sizable fiber/macronutrient differences and unclear preparation. |
| low-fat Greek yogurt | 2705423; Survey (FNDDS); Yogurt, Greek, low fat milk, plain | 2536668; Branded; LOW-FAT GREEK YOGURT | 67.0 / 10.2 / 3.6 / 1.36 / 0.0 | 125.0 / 6.25 / 17.19 / 3.12 / 0.8 | Ambiguous | Selected branded description omits plainness; its carbohydrate and calorie values differ substantially from the expected plain FNDDS yogurt. |
| unflavored whey protein | 173180; SR Legacy; Beverages, Protein powder whey based | 2510560; Branded; WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 352.0 / 78.13 / 6.25 / 1.56 / 3.1 | 360.0 / 80.0 / 4.0 / 4.0 / 0.0 | Ambiguous | Selected record is an unflavored branded powder, but formulation and fiber/nutrient values differ; broad product identity is insufficient. |

### Hybrid

| Ingredient | Expected (ID; type; description) | Selected (ID; type; description) | Expected macros | Selected macros | Class | Evidence-based reason |
|---|---|---|---|---|---|
| oats | 2708489; Survey (FNDDS); Oats, raw | 169705; SR Legacy; Oats (Includes foods for USDA's Food Distribution Program) | 379 / 13.2 / 67.7 / 6.52 / 10.1 | 389.0 / 16.89 / 66.27 / 6.9 / 10.6 | Verified equivalent | Generic SR Legacy oats record has no contradictory preparation label; its per-100g profile is close to expected raw oats. |
| brown rice | 2710789; Survey (FNDDS); Rice, brown, cooked, as ingredient | 168876; SR Legacy; Rice, brown, parboiled, dry, UNCLE BEN'S | 124 / 2.45 / 25.9 / 1.12 / 1.0 | 370.0 / 7.6 / 78.68 / 2.75 / 3.5 | Incorrect | Expected record is cooked brown rice; selected record is dry, parboiled, branded brown rice. |
| almonds | 2707485; Survey (FNDDS); Almonds, NFS | 170567; SR Legacy; Nuts, almonds | 598 / 21.0 / 21.0 / 52.5 / 10.9 | 579.0 / 21.15 / 21.55 / 49.93 / 12.5 | Verified equivalent | Both are generic almonds; no conflicting preparation or modifier; profiles are close. |
| chia seeds | 2707590; Survey (FNDDS); Chia seeds | 170554; SR Legacy; Seeds, chia seeds, dried | 486 / 16.5 / 42.1 / 30.7 / 34.4 | 486.0 / 16.54 / 42.12 / 30.74 / 34.4 | Verified equivalent | Both are chia seeds; SR Legacy explicitly dried and the FNDDS seed profile agrees closely. |
| olive oil | 2710186; Survey (FNDDS); Olive oil | 167737; SR Legacy; Oil, corn, peanut, and olive | 900 / 0.0 / 0.0 / 100 / 0.0 | 884.0 / 0.0 / 0.0 / 100.0 / 0.0 | Incorrect | Selected SR Legacy record is a corn/peanut/olive oil blend, not pure olive oil. |
| rajma | 2707379; Survey (FNDDS); Kidney beans, NFS | 173744; SR Legacy; Beans, kidney, red, mature seeds, raw | 177 / 8.06 / 21.2 / 6.97 / 6.9 | 337.0 / 22.53 / 61.29 / 1.06 / 15.2 | Incorrect | Selected record explicitly describes raw mature kidney beans; expected FNDDS NFS record has a prepared-food nutrient profile. Preparation is incompatible. |
| whole wheat flour (atta) | 790085; Foundation; Flour, whole wheat, unenriched | 168944; SR Legacy; Wheat flour, whole-grain, soft wheat | 370.0 / 15.1 / 71.2 / 2.73 / 10.6 | 332.0 / 9.61 / 74.48 / 1.95 / 13.1 | Ambiguous | Both are whole-wheat flour, but selected record specifies soft wheat and profile differs materially; atta subtype is not established. |
| kala chana, soaked overnight and boiled | 2134686; Branded; KALA CHANA | 2054512; Branded; KALA CHANA | 363.0 / 20.0 / 60.0 / 5.71 / 17.1 | 368.0 / 16.84 / 66.32 / 0.0 / 34.7 | Ambiguous | Same branded name, but distinct records have large fiber and macro differences; detail does not resolve whether products/formulation or prep differ. |
| garlic, minced | 2709786; Survey (FNDDS); Garlic, raw | 169230; SR Legacy; Garlic, raw | 143 / 6.62 / 28.2 / 0.38 / 2.7 | 149.0 / 6.36 / 33.06 / 0.5 / 2.1 | Verified equivalent | Expected is raw garlic; selected is raw garlic. Minced form is compatible; per-100g values are close. |
| low-fat Greek yogurt | 2705423; Survey (FNDDS); Yogurt, Greek, low fat milk, plain | 170903; SR Legacy; Yogurt, Greek, plain, lowfat | 67.0 / 10.2 / 3.6 / 1.36 / 0.0 | 73.0 / 9.95 / 3.94 / 1.92 / 0.0 | Verified equivalent | Both descriptions specify plain low-fat Greek yogurt; per-100g values are close. |
| unflavored whey protein | 173180; SR Legacy; Beverages, Protein powder whey based | 2510560; Branded; WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 352.0 / 78.13 / 6.25 / 1.56 / 3.1 | 360.0 / 80.0 / 4.0 / 4.0 / 0.0 | Ambiguous | Branded unflavored whey powder is plausible, but a specific 20 g powder formulation and differing nutrients prevent confident equivalence. |
| low-sodium soy sauce | 2707443; Survey (FNDDS); Soy sauce, reduced sodium | 172474; SR Legacy; Soy sauce, reduced sodium, made from hydrolyzed vegetable protein | 57.0 / 9.05 / 5.59 / 0.3 / 0.7 | 90.0 / 8.19 / 14.44 / 0.31 / 0.3 | Incorrect | Selected is reduced-sodium sauce made from hydrolyzed vegetable protein, a different formulation from soy sauce. |
| fat-free Greek yogurt | 2076798; Branded; FAT-FREE GREEK YOGURT | 170902; SR Legacy; Yogurt, Greek, vanilla, nonfat | 93.0 / 7.33 / 12.67 / 1.33 / 0.7 | 78.0 / 8.64 / 10.37 / 0.18 / 0.5 | Incorrect | Expected is fat-free Greek yogurt; selected SR Legacy record is vanilla nonfat yogurt, a meaningful flavor/formulation modifier. |

### Equivalence-based metric method

Exact matches and verified equivalents count as positive matches. Incorrect selected assignments count as FP. Ambiguous selected assignments are excluded from the metric denominator (reported separately), not credited. Correct abstentions remain TN; missed expected matches remain FN. Thus these are adjudicated, selective metrics over decisive rows, not conventional all-30-row accuracy.

| Run | Exact IDs | Verified equivalents | Incorrect | Ambiguous (excluded) | Decisive denominator | TP | FP | TN | FN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fresh live NLP | 16 | 0 | 2 | 4 | 26 | 16 | 2 | 7 | 1 | 88.46% | 88.89% | 94.12% | 91.43% |
| Fresh live hybrid | 9 | 5 | 5 | 3 | 27 | 14 | 5 | 7 | 1 | 77.78% | 73.68% | 93.33% | 82.35% |

The fresh live NLP equivalence F1 is 91.43% (26 decisive rows); fresh hybrid is 82.35% (27 decisive rows). These rely on the manual classifications above. They are not the exact-ID F1 values and are not fully automated/ground-truth equivalence metrics. Under this review, the hybrid has 14 correct assignments after adding five verified equivalents, five incorrect assignments, three ambiguous assignments, seven correct abstentions, and one missed match. The earlier proposed 87.50% hybrid F1 used a different manual adjudication that left two now-incompatible modifier/formulation cases ambiguous; it should not be conflated with the stricter current assessment. NLP has 16 exact correct assignments, no verified different-ID equivalents, two incorrect assignments, four ambiguous assignments, seven correct abstentions, and one missed match.

## Nutritional evidence and interpretation

- Closest cross-record same-ingredient examples: FNDDS chia (486 kcal, 16.5/42.1/30.7/34.4 g) vs dried SR Legacy chia (486 kcal, 16.54/42.12/30.74/34.4 g); FNDDS almonds vs SR almonds (598 vs 579 kcal; similar macros); raw FNDDS garlic vs SR raw garlic (143 vs 149 kcal); and plain low-fat Greek yogurt (67 vs 73 kcal). These support equivalence because identity and form are compatible, not simply because values align.
- Strong preparation mismatch: cooked brown rice expected is 124 kcal and 25.9 g carbs per 100 g, while selected dry parboiled rice is 370 kcal and 78.68 g carbs. Rajma expected NFS is 177 kcal and 21.2 g carbs, while explicitly raw kidney beans are 337 kcal and 61.29 g carbs. These are not comparable forms.
- Formulation/identity mismatches: pure olive oil expected is 900 kcal and 100 g fat; selected oil blend is 884 kcal and 100 g fat but includes corn and peanut oils. Reduced-sodium soy sauce differs from an HVP-based sauce. Vanilla nonfat yogurt differs from the expected fat-free Greek yogurt description.
- Other uncertain pairs: oat record is generic USDA food-distribution oats and near the raw oat profile but does not state raw; atta record specifies soft wheat while expected whole-wheat flour does not; branded kala chana records have near calories but fiber 17.1 vs 34.7 g and require product/preparation review; branded whey record has calories/protein broadly close but is a specific 20 g powder product, and the expected generic record reports fiber while selected reports zero. Zero is reported data, not missing.
- Tofu selected branded record has no energy value, so calories are unavailable; protein/fat are close to expected, but that alone does not establish equivalence.

## API failures, completeness, and limits

- Both candidate searches and 31 distinct FDC record lookups completed with zero recorded errors. No snapshots were substituted for live searches.
- Candidate discovery returns only the API search result window used by each matcher; identical responses establish repeatability for these captures, not that USDA’s database will never change or that the selected candidate was globally optimal.
- Equivalence decisions are human adjudications of the retrieved descriptions and nutrients. Nutrient resemblance cannot prove formulation identity, especially for branded records. Ambiguous cases remain excluded from proposed metrics.
- We did not rerun either matcher using detail lookups or manually alter predictions. FDC detail calls are solely for post-prediction equivalence review.

## Artifacts

- `nlp/evaluation_report.md`, `nlp/nlp_results.json`, `nlp/candidate_snapshot.json`
- `hybrid/evaluation_report.md`, `hybrid/hybrid_results.json`, `hybrid/live_candidate_snapshot.json`, `hybrid/api_failures.json`
- `fdc_record_details.json`
- `equivalence_review.json`
