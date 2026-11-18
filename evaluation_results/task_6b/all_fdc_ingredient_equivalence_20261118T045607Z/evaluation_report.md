# All-FDC Ingredient-Equivalence Evaluation

Created 2026-11-18T04:56:07.324064+00:00 (UTC).

## Answer

Yes, on this saved 30-example run, the experimental all-FDC matcher improves ingredient-equivalence precision, recall, and F1 over the original NLP matcher under the primary ambiguity-excluded scoring: precision 90.91% vs 88.89%, recall 100.00% vs 94.12%, and F1 95.24% vs 91.43%. The result is based on the archived live candidate snapshot and post-hoc record review, not a new live run.

## Source and implementation audit

Recovered the final all-FDC run and implementation patch from Git commit `dc584a0` and `/tmp/task6b_all_fdc_experiment.patch`. The archived matcher omits the USDA data-type filter; the saved candidate snapshot contains Survey (FNDDS), SR Legacy, Foundation, and Branded records (plus one record labeled Experimental in the bounded response window). It applies text score, ingredient identity, preparation, and modifier checks before choosing among suitable records by data-type tier and then score. The current tier function favors curated types over Branded. The archived evaluation reports 0 all-type query errors, 0 record-detail errors, 30/30 scored rows, 21 all-type-stage assignments, 2 NLP fallback assignments, and 7 abstentions/review cases.

**Nutritional comparison limitation:** The matcher source does not compare calories, protein, carbohydrates, fat, or fiber during candidate selection. Nutrient values are present in the saved post-hoc record review and are used here as supporting evidence for manual equivalence adjudication. The algorithm therefore does not fully implement the objective’s stated nutritional-comparison step.

## Primary metric comparison

| Metric | Original NLP | New all-FDC matcher |
|---|---:|---:|
| Precision | 88.89% | 90.91% |
| Recall | 94.12% | 100.00% |
| Ingredient-equivalence F1 | 91.43% | 95.24% |
| Accuracy | 88.46% | 93.10% |
| Assignment rate | 73.33% | 76.67% |
| Abstention rate | 26.67% | 23.33% |
| Incorrect matches | 2 | 2 |
| Ambiguous matches | 4 | 1 |

Primary denominator: NLP 26/30 (4 ambiguous excluded); all-FDC 29/30 (1 ambiguous excluded).

### Confusion counts, classifications, and conservative sensitivity

| Matcher / scoring | TP | FP | TN | FN | Denominator | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original NLP | 16 | 2 | 7 | 1 | 26/30 | 88.89% | 94.12% | 91.43% | 88.46% |
| New all-FDC | 20 | 2 | 7 | 0 | 29/30 | 90.91% | 100.00% | 95.24% | 93.10% |
| Original NLP, conservative | 16 | 6 | 7 | 1 | 30/30 | 72.73% | 94.12% | 82.05% | 76.67% |
| New all-FDC, conservative | 20 | 3 | 7 | 0 | 30/30 | 86.96% | 100.00% | 93.02% | 90.00% |

Conservative scoring treats every ambiguous assigned candidate as FP and includes all 30 rows. All-FDC remains ahead: F1 93.02% vs 82.05%.

### Classification totals

| Matcher | Exact ingredient | Verified equivalent | Incorrect | Ambiguous | Correct abstentions | Missed matches | Abstentions |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original NLP | 16 | 0 | 2 | 4 | 7 | 1 | 8 |
| New all-FDC | 17 | 3 | 2 | 1 | 7 | 0 | 7 |

## All 30 examples

Abbreviations: FNDDS = Survey. Nutrients are kcal and grams per 100 g where available; `—` means unavailable/missing, not zero. Full field-level macro values for every row are in the CSV and JSON.

| Ingredient | Expected FDC record | Original NLP selected / class | New all-FDC selected / stage / class |
|---|---|---|---|
| oats | 2708489: Oats, raw [Survey (FNDDS)] | 2779253: Oats, puffed [Foundation] — incorrect | 2708489: Oats, raw [Survey (FNDDS)] — all_data_types — exact_ingredient |
| quinoa | 168874: Quinoa, uncooked [SR Legacy] | 168874: Quinoa, uncooked [SR Legacy] — exact_ingredient | 168874: Quinoa, uncooked [SR Legacy] — all_data_types — exact_ingredient |
| brown rice | 2710789: Rice, brown, cooked, as ingredient [Survey (FNDDS)] | 2779256: Brown rice, puffed [Foundation] — incorrect | 2286928: BROWN RICE [Branded] — all_data_types — incorrect |
| almonds | 2707485: Almonds, NFS [Survey (FNDDS)] | 2707485: Almonds, NFS [Survey (FNDDS)] — exact_ingredient | 2707485: Almonds, NFS [Survey (FNDDS)] — all_data_types — exact_ingredient |
| chia seeds | 2707590: Chia seeds [Survey (FNDDS)] | 2707590: Chia seeds [Survey (FNDDS)] — exact_ingredient | 2707590: Chia seeds [Survey (FNDDS)] — all_data_types — exact_ingredient |
| olive oil | 2710186: Olive oil [Survey (FNDDS)] | 2710186: Olive oil [Survey (FNDDS)] — exact_ingredient | 2710186: Olive oil [Survey (FNDDS)] — all_data_types — exact_ingredient |
| hing | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| rajma | 2707379: Kidney beans, NFS [Survey (FNDDS)] | 2707379: Kidney beans, NFS [Survey (FNDDS)] — exact_ingredient | 2707379: Kidney beans, NFS [Survey (FNDDS)] — all_data_types — exact_ingredient |
| kasuri methi | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| kala namak (black salt) | 2587261: BLACK SALT [Branded] | 2587261: BLACK SALT [Branded] — exact_ingredient | 2587261: BLACK SALT [Branded] — all_data_types — exact_ingredient |
| whole wheat flour (atta) | 790085: Flour, whole wheat, unenriched [Foundation] | 790085: Flour, whole wheat, unenriched [Foundation] — exact_ingredient | 790085: Flour, whole wheat, unenriched [Foundation] — all_data_types — exact_ingredient |
| ghee | 171314: Butter, Clarified butter (ghee) [SR Legacy] | 171314: Butter, Clarified butter (ghee) [SR Legacy] — exact_ingredient | 171314: Butter, Clarified butter (ghee) [SR Legacy] — all_data_types — exact_ingredient |
| degi mirch | 171329: Spices, paprika [SR Legacy] | 171329: Spices, paprika [SR Legacy] — exact_ingredient | 171329: Spices, paprika [SR Legacy] — all_data_types — exact_ingredient |
| carom seeds (ajwain) | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| dry soya chunks | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] — exact_ingredient | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] — all_data_types — exact_ingredient |
| moong dal, soaked overnight | 174256: Mung beans, mature seeds, raw [SR Legacy] | 174256: Mung beans, mature seeds, raw [SR Legacy] — exact_ingredient | 174256: Mung beans, mature seeds, raw [SR Legacy] — all_data_types — exact_ingredient |
| low-fat paneer, crumbled | 2705740: Cheese, paneer [Survey (FNDDS)] | 2705740: Cheese, paneer [Survey (FNDDS)] — exact_ingredient | 2705740: Cheese, paneer [Survey (FNDDS)] — nlp_fallback — exact_ingredient |
| extra-firm tofu, cubed | 174290: Tofu, extra firm, prepared with nigari [SR Legacy] | 2310367: EXTRA-FIRM TOFU [Branded] — ambiguous | 2310367: EXTRA-FIRM TOFU [Branded] — all_data_types — verified_equivalent |
| kala chana, soaked overnight and boiled | 2134686: KALA CHANA [Branded] | 2054512: KALA CHANA [Branded] — ambiguous | 2054512: KALA CHANA [Branded] — nlp_fallback — ambiguous |
| kabuli chana, soaked and boiled | 2707414: Chickpeas, NFS [Survey (FNDDS)] | 2707414: Chickpeas, NFS [Survey (FNDDS)] — exact_ingredient | 2707414: Chickpeas, NFS [Survey (FNDDS)] — all_data_types — exact_ingredient |
| garlic, minced | 2709786: Garlic, raw [Survey (FNDDS)] | 2709786: Garlic, raw [Survey (FNDDS)] — exact_ingredient | 2709786: Garlic, raw [Survey (FNDDS)] — all_data_types — exact_ingredient |
| low-fat Greek yogurt | 2705423: Yogurt, Greek, low fat milk, plain [Survey (FNDDS)] | 2536668: LOW-FAT GREEK YOGURT [Branded] — ambiguous | 170903: Yogurt, Greek, plain, lowfat [SR Legacy] — all_data_types — verified_equivalent |
| unflavored whey protein | 173180: Beverages, Protein powder whey based [SR Legacy] | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — ambiguous | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — all_data_types — incorrect |
| low-sodium soy sauce | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] — exact_ingredient | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] — all_data_types — exact_ingredient |
| fat-free Greek yogurt | 2076798: FAT-FREE GREEK YOGURT [Branded] | 2076798: FAT-FREE GREEK YOGURT [Branded] — exact_ingredient | 2705432: Yogurt, Greek, nonfat milk, fruit [Survey (FNDDS)] — all_data_types — verified_equivalent |
| whole black urad dal | 2168881: WHOLE BLACK GRAM [Branded] | —: — [—] — abstained | 2168881: WHOLE BLACK GRAM [Branded] — all_data_types — exact_ingredient |
| kadhai spice mix (crushed coriander seeds / dry red chili) | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| onion-tomato gravy base | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| mint-cilantro-yogurt chutney | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |
| quinoa-rice blend | —: — [—] | —: — [—] — abstained | —: — [—] — — — abstained |

## Where the all-FDC matcher succeeds and fails

- It corrects the original oats error. Brown rice remains incorrect because the chosen branded record is dry while the expected record is cooked.
- It selects verified equivalent branded extra-firm tofu and cross-type equivalent plain low-fat Greek yogurt, and a fruit nonfat Greek yogurt record for the expected fruit yogurt.
- It incorrectly selects the whey product containing micellar casein; the similar protein and calorie values do not establish the same formulation.
- Kala chana remains ambiguous because the branded record’s pulse identity and fiber profile conflict with the expected record.
- Relative to NLP, all-FDC has 3 verified equivalents and 1 ambiguous assigned case, versus 0 verified equivalents and 4 ambiguous cases for NLP. It also turns one missed expected match into a successful match, and increases assignment rate by 3.33 points.

The saved review shows preference for generic/curated records when suitable candidates were available; branded records were used when selected by the saved run. This sample supports a gain, but does not isolate the causal impact of data-type preference from the added identity/preparation/modifier rules or the changed candidate set.

## Reproducibility and limitations

- All 30 original validation rows were used. No new USDA requests or matcher execution occurred during this recalculation.
- Candidate search responses and direct record details were read from commit `dc584a0`; the original NLP baseline candidate snapshot was referenced from the same commit. Candidate search was bounded to page size 50; absence from a saved response does not prove absence from FDC.
- Post-hoc equivalence labels were reused from the saved manual evidence review, including per-100 g macro profiles. Missing nutrient values remain null/unavailable; zero values remain numeric zero.
- Exact FDC ID equality was not used as the success rule.
