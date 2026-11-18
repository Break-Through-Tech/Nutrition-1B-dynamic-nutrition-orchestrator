# Task 6B final evaluation: original NLP vs SR Legacy-first hybrid

## Method and provenance

- No matcher was run again. The complete November 17 fresh live comparison was reused: [NLP run](../live_comparison_20261117T225557Z/nlp/evaluation_report.md), [hybrid run](../live_comparison_20261117T225557Z/hybrid/evaluation_report.md), [candidate snapshots and direct FDC detail capture](../live_comparison_20261117T225557Z/).
- Both matcher result sets contain all 30 unchanged rows from `data/validation_set.csv`; each reported zero API failures. The hybrid artifact explicitly says its candidate retrieval was live, with no snapshot fallback. The fresh November 17 NLP results reproduced the November 15 baseline predictions and metrics.
- The direct FDC detail artifact contains 31/31 unique expected/selected FDC IDs. The candidate snapshots, result rows, error records, and nutrients are preserved in the November 17 folder. No new API evaluation was necessary.
- Source inspection: `HybridIngredientMatcher.match()` performs SR Legacy search first and calls the existing `IngredientMatcher` for fallback. Candidate scoring, ranking, and acceptance remain matcher behavior. `matcher_eval.classify()` and the hybrid evaluation script classify by exact FDC ID. Equivalence-aware scoring is not part of matching or automated scoring; the November 17 `equivalence_review.json` is a separate manual post-hoc adjudication. The November 17 exact-ID report correctly reflects the current implementation and live output.
- Equivalence rubric: exact ID is exact; differing IDs use the existing November 17 manual review and require compatible ingredient identity, preparation, and relevant modifiers. Similar names/macros alone do not establish equivalence. Ambiguous assignments are excluded from selective equivalence metrics. Correct abstentions and missed matches stay TN and FN.

## Exact-ID results

| Run | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN | Assignments / rate | API failures | Abstentions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original NLP baseline, Nov 15 (exact ID) | 76.67% | 72.73% | 94.12% | 82.05% | 16 | 6 | 7 | 1 | 22/30 (73.33%) | 0 | 8 |
| Fresh original NLP, Nov 17 (exact ID) | 76.67% | 72.73% | 94.12% | 82.05% | 16 | 6 | 7 | 1 | 22/30 (73.33%) | 0 | 8 |
| Fresh Task 6B hybrid, Nov 17 (exact ID) | 53.33% | 40.91% | 90.00% | 56.25% | 9 | 13 | 7 | 1 | 22/30 (73.33%) | 0 | 8 |

The November 15 baseline is exact-ID scoring. November 17 fresh NLP matches it exactly (same 30 outcomes). The hybrid exact-ID result is the fresh November 17 live run. These exact-ID results are directly comparable because the dataset and metric definitions are the same.

## Post-hoc equivalence-aware results

| Prediction set / method | Accuracy | Precision | Recall | F1 | Exact matches | Verified equivalents | Incorrect assignments | Ambiguous (excluded) | Correct abstentions | Missed matches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original NLP predictions; post-hoc review (26 decisive rows) | 88.46% | 88.89% | 94.12% | 91.43% | 16 | 0 | 2 | 4 | 7 | 1 |
| Task 6B hybrid; post-hoc review (27 decisive rows) | 77.78% | 73.68% | 93.33% | 82.35% | 9 | 5 | 5 | 3 | 7 | 1 |

The NLP equivalence denominator is 26/30 (four ambiguous cases excluded); hybrid denominator is 27/30 (three ambiguous cases excluded). On the hybrid selective denominator, TP=14, FP=5, TN=7, FN=1; on NLP, TP=16, FP=2, TN=7, FN=1. Assignment rate remains the all-row exact matcher assignment rate (22/30 = 73.33%) and is not recalculated on the selective denominator.

This NLP equivalence result is post-hoc: the November 15 exact-ID prediction set is identical to the November 17 fresh NLP set, and the manual adjudication was made from November 17 FDC detail evidence. It must not be presented as the metric originally reported on November 15. The earlier 87.50% hybrid F1 proposal used a different manual adjudication and a 25-row decisive denominator; the current November 17 review classifies the HVP-based sauce and vanilla yogurt as incompatible, leaving three ambiguous hybrid assignments and a 27-row denominator. The 87.50% value is superseded by the present review, not by a matcher change.

## All 30 validation predictions

Macro nutrient order for the separate differing-ID evidence table is kcal / protein / carbohydrate / fat / fiber per 100 g. In the table below, expected and selected FDC IDs and descriptions are paired with the manual class. A “review” stage means the hybrid abstained and requested review.

| Ingredient | Expected record | Original NLP selected record and class | Task 6B hybrid selected record, stage, and class |
| --- | --- | --- | --- |
| oats | 2708489: Oats, raw [Survey (FNDDS)] | 2779253: Oats, puffed [Foundation] — Incorrect | 169705: Oats (Includes foods for USDA's Food Distribution Program) [SR Legacy] — sr_legacy — Verified equivalent |
| quinoa | 168874: — [—] | 168874: Quinoa, uncooked [—] — Exact match | 168874: Quinoa, uncooked [SR Legacy] — sr_legacy — Exact match |
| brown rice | 2710789: Rice, brown, cooked, as ingredient [Survey (FNDDS)] | 2779256: Brown rice, puffed [Foundation] — Incorrect | 168876: Rice, brown, parboiled, dry, UNCLE BEN'S [SR Legacy] — sr_legacy — Incorrect |
| almonds | 2707485: Almonds, NFS [Survey (FNDDS)] | 2707485: Almonds, NFS [Survey (FNDDS)] — Exact match | 170567: Nuts, almonds [SR Legacy] — sr_legacy — Verified equivalent |
| chia seeds | 2707590: Chia seeds [Survey (FNDDS)] | 2707590: Chia seeds [Survey (FNDDS)] — Exact match | 170554: Seeds, chia seeds, dried [SR Legacy] — sr_legacy — Verified equivalent |
| olive oil | 2710186: Olive oil [Survey (FNDDS)] | 2710186: Olive oil [Survey (FNDDS)] — Exact match | 167737: Oil, corn, peanut, and olive [SR Legacy] — sr_legacy — Incorrect |
| hing | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| rajma | 2707379: Kidney beans, NFS [Survey (FNDDS)] | 2707379: Kidney beans, NFS [Survey (FNDDS)] — Exact match | 173744: Beans, kidney, red, mature seeds, raw [SR Legacy] — sr_legacy — Incorrect |
| kasuri methi | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| kala namak (black salt) | 2587261: — [—] | 2587261: BLACK SALT [—] — Exact match | 2587261: BLACK SALT [Branded] — nlp_fallback — Exact match |
| whole wheat flour (atta) | 790085: Flour, whole wheat, unenriched [Foundation] | 790085: Flour, whole wheat, unenriched [Foundation] — Exact match | 168944: Wheat flour, whole-grain, soft wheat [SR Legacy] — sr_legacy — Ambiguous |
| ghee | 171314: — [—] | 171314: Butter, Clarified butter (ghee) [—] — Exact match | 171314: Butter, Clarified butter (ghee) [SR Legacy] — sr_legacy — Exact match |
| degi mirch | 171329: — [—] | 171329: Spices, paprika [—] — Exact match | 171329: Spices, paprika [SR Legacy] — sr_legacy — Exact match |
| carom seeds (ajwain) | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| dry soya chunks | 2707451: — [—] | 2707451: Textured vegetable protein, dry [—] — Exact match | 2707451: Textured vegetable protein, dry [Survey (FNDDS)] — nlp_fallback — Exact match |
| moong dal, soaked overnight | 174256: — [—] | 174256: Mung beans, mature seeds, raw [—] — Exact match | 174256: Mung beans, mature seeds, raw [SR Legacy] — sr_legacy — Exact match |
| low-fat paneer, crumbled | 2705740: — [—] | 2705740: Cheese, paneer [—] — Exact match | 2705740: Cheese, paneer [Survey (FNDDS)] — nlp_fallback — Exact match |
| extra-firm tofu, cubed | 174290: Tofu, extra firm, prepared with nigari [SR Legacy] | 2310367: EXTRA-FIRM TOFU [Branded] — Ambiguous | 174290: Tofu, extra firm, prepared with nigari [SR Legacy] — sr_legacy — Exact match |
| kala chana, soaked overnight and boiled | 2134686: KALA CHANA [Branded] | 2054512: KALA CHANA [Branded] — Ambiguous | 2054512: KALA CHANA [Branded] — nlp_fallback — Ambiguous |
| kabuli chana, soaked and boiled | 2707414: — [—] | 2707414: Chickpeas, NFS [—] — Exact match | 2707414: Chickpeas, NFS [Survey (FNDDS)] — nlp_fallback — Exact match |
| garlic, minced | 2709786: Garlic, raw [Survey (FNDDS)] | 2709786: Garlic, raw [Survey (FNDDS)] — Exact match | 169230: Garlic, raw [SR Legacy] — sr_legacy — Verified equivalent |
| low-fat Greek yogurt | 2705423: Yogurt, Greek, low fat milk, plain [Survey (FNDDS)] | 2536668: LOW-FAT GREEK YOGURT [Branded] — Ambiguous | 170903: Yogurt, Greek, plain, lowfat [SR Legacy] — sr_legacy — Verified equivalent |
| unflavored whey protein | 173180: Beverages, Protein powder whey based [SR Legacy] | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — Ambiguous | 2510560: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED [Branded] — nlp_fallback — Ambiguous |
| low-sodium soy sauce | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] | 2707443: Soy sauce, reduced sodium [Survey (FNDDS)] — Exact match | 172474: Soy sauce, reduced sodium, made from hydrolyzed vegetable protein [SR Legacy] — sr_legacy — Incorrect |
| fat-free Greek yogurt | 2076798: FAT-FREE GREEK YOGURT [Branded] | 2076798: FAT-FREE GREEK YOGURT [Branded] — Exact match | 170902: Yogurt, Greek, vanilla, nonfat [SR Legacy] — sr_legacy — Incorrect |
| whole black urad dal | 2168881: — [—] | —: — [—] — Missed match | —: — [—] — review — Missed match |
| kadhai spice mix (crushed coriander seeds / dry red chili) | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| onion-tomato gravy base | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| mint-cilantro-yogurt chutney | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |
| quinoa-rice blend | — | —: — [—] — Correct abstention | —: — [—] — review — Correct abstention |

## Differing-ID decisions and nutrient evidence

| Matcher | Ingredient | Expected FDC record | Selected FDC record | Expected macros / 100g | Selected macros / 100g | Class | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NLP | oats | 2708489 Survey (FNDDS): Oats, raw | 2779253 Foundation: Oats, puffed | 379 / 13.2 / 67.7 / 6.52 / 10.1 | — / 14.5625 / 70.5525 / 6.85 / 8.79 | Incorrect | Puffed oats are explicitly a different preparation/form from the expected raw oats. |
| Hybrid | oats | 2708489 Survey (FNDDS): Oats, raw | 169705 SR Legacy: Oats (Includes foods for USDA's Food Distribution Program) | 379 / 13.2 / 67.7 / 6.52 / 10.1 | 389.0 / 16.89 / 66.27 / 6.9 / 10.6 | Verified equivalent | Generic SR Legacy oats record has no contradictory preparation label; its per-100g profile is close to expected raw oats. |
| NLP | brown rice | 2710789 Survey (FNDDS): Rice, brown, cooked, as ingredient | 2779256 Foundation: Brown rice, puffed | 124 / 2.45 / 25.9 / 1.12 / 1.0 | — / 7.8125 / 80.2625 / 2.76 / 2.7 | Incorrect | Expected record is cooked brown rice; selected record is puffed brown rice. |
| Hybrid | brown rice | 2710789 Survey (FNDDS): Rice, brown, cooked, as ingredient | 168876 SR Legacy: Rice, brown, parboiled, dry, UNCLE BEN'S | 124 / 2.45 / 25.9 / 1.12 / 1.0 | 370.0 / 7.6 / 78.68 / 2.75 / 3.5 | Incorrect | Expected record is cooked brown rice; selected record is dry, parboiled, branded brown rice. |
| Hybrid | almonds | 2707485 Survey (FNDDS): Almonds, NFS | 170567 SR Legacy: Nuts, almonds | 598 / 21.0 / 21.0 / 52.5 / 10.9 | 579.0 / 21.15 / 21.55 / 49.93 / 12.5 | Verified equivalent | Both are generic almonds; no conflicting preparation or modifier; profiles are close. |
| Hybrid | chia seeds | 2707590 Survey (FNDDS): Chia seeds | 170554 SR Legacy: Seeds, chia seeds, dried | 486 / 16.5 / 42.1 / 30.7 / 34.4 | 486.0 / 16.54 / 42.12 / 30.74 / 34.4 | Verified equivalent | Both are chia seeds; SR Legacy explicitly dried and the FNDDS seed profile agrees closely. |
| Hybrid | olive oil | 2710186 Survey (FNDDS): Olive oil | 167737 SR Legacy: Oil, corn, peanut, and olive | 900 / 0.0 / 0.0 / 100 / 0.0 | 884.0 / 0.0 / 0.0 / 100.0 / 0.0 | Incorrect | Selected SR Legacy record is a corn/peanut/olive oil blend, not pure olive oil. |
| Hybrid | rajma | 2707379 Survey (FNDDS): Kidney beans, NFS | 173744 SR Legacy: Beans, kidney, red, mature seeds, raw | 177 / 8.06 / 21.2 / 6.97 / 6.9 | 337.0 / 22.53 / 61.29 / 1.06 / 15.2 | Incorrect | Selected record explicitly describes raw mature kidney beans; expected FNDDS NFS record has a prepared-food nutrient profile. Preparation is incompatible. |
| Hybrid | whole wheat flour (atta) | 790085 Foundation: Flour, whole wheat, unenriched | 168944 SR Legacy: Wheat flour, whole-grain, soft wheat | 370.0 / 15.1 / 71.2 / 2.73 / 10.6 | 332.0 / 9.61 / 74.48 / 1.95 / 13.1 | Ambiguous | Both are whole-wheat flour, but selected record specifies soft wheat and profile differs materially; atta subtype is not established. |
| NLP | extra-firm tofu, cubed | 174290 SR Legacy: Tofu, extra firm, prepared with nigari | 2310367 Branded: EXTRA-FIRM TOFU | 83.0 / 9.98 / 1.18 / 5.26 / 1.0 | — / 10.71 / 3.57 / 5.36 / 1.2 | Ambiguous | Both are extra-firm tofu, but selected branded detail has unavailable energy and does not establish ingredient formulation equivalence. |
| NLP | kala chana, soaked overnight and boiled | 2134686 Branded: KALA CHANA | 2054512 Branded: KALA CHANA | 363.0 / 20.0 / 60.0 / 5.71 / 17.1 | 368.0 / 16.84 / 66.32 / 0.0 / 34.7 | Ambiguous | Both descriptions say kala chana, but they are distinct branded records with sizable fiber/macronutrient differences and unclear preparation. |
| Hybrid | kala chana, soaked overnight and boiled | 2134686 Branded: KALA CHANA | 2054512 Branded: KALA CHANA | 363.0 / 20.0 / 60.0 / 5.71 / 17.1 | 368.0 / 16.84 / 66.32 / 0.0 / 34.7 | Ambiguous | Same branded name, but distinct records have large fiber and macro differences; detail does not resolve whether products/formulation or prep differ. |
| Hybrid | garlic, minced | 2709786 Survey (FNDDS): Garlic, raw | 169230 SR Legacy: Garlic, raw | 143 / 6.62 / 28.2 / 0.38 / 2.7 | 149.0 / 6.36 / 33.06 / 0.5 / 2.1 | Verified equivalent | Expected is raw garlic; selected is raw garlic. Minced form is compatible; per-100g values are close. |
| NLP | low-fat Greek yogurt | 2705423 Survey (FNDDS): Yogurt, Greek, low fat milk, plain | 2536668 Branded: LOW-FAT GREEK YOGURT | 67.0 / 10.2 / 3.6 / 1.36 / 0.0 | 125.0 / 6.25 / 17.19 / 3.12 / 0.8 | Ambiguous | Selected branded description omits plainness; its carbohydrate and calorie values differ substantially from the expected plain FNDDS yogurt. |
| Hybrid | low-fat Greek yogurt | 2705423 Survey (FNDDS): Yogurt, Greek, low fat milk, plain | 170903 SR Legacy: Yogurt, Greek, plain, lowfat | 67.0 / 10.2 / 3.6 / 1.36 / 0.0 | 73.0 / 9.95 / 3.94 / 1.92 / 0.0 | Verified equivalent | Both descriptions specify plain low-fat Greek yogurt; per-100g values are close. |
| NLP | unflavored whey protein | 173180 SR Legacy: Beverages, Protein powder whey based | 2510560 Branded: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 352.0 / 78.13 / 6.25 / 1.56 / 3.1 | 360.0 / 80.0 / 4.0 / 4.0 / 0.0 | Ambiguous | Selected record is an unflavored branded powder, but formulation and fiber/nutrient values differ; broad product identity is insufficient. |
| Hybrid | unflavored whey protein | 173180 SR Legacy: Beverages, Protein powder whey based | 2510560 Branded: WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 352.0 / 78.13 / 6.25 / 1.56 / 3.1 | 360.0 / 80.0 / 4.0 / 4.0 / 0.0 | Ambiguous | Branded unflavored whey powder is plausible, but a specific 20 g powder formulation and differing nutrients prevent confident equivalence. |
| Hybrid | low-sodium soy sauce | 2707443 Survey (FNDDS): Soy sauce, reduced sodium | 172474 SR Legacy: Soy sauce, reduced sodium, made from hydrolyzed vegetable protein | 57.0 / 9.05 / 5.59 / 0.3 / 0.7 | 90.0 / 8.19 / 14.44 / 0.31 / 0.3 | Incorrect | Selected is reduced-sodium sauce made from hydrolyzed vegetable protein, a different formulation from soy sauce. |
| Hybrid | fat-free Greek yogurt | 2076798 Branded: FAT-FREE GREEK YOGURT | 170902 SR Legacy: Yogurt, Greek, vanilla, nonfat | 93.0 / 7.33 / 12.67 / 1.33 / 0.7 | 78.0 / 8.64 / 10.37 / 0.18 / 0.5 | Incorrect | Expected is fat-free Greek yogurt; selected SR Legacy record is vanilla nonfat yogurt, a meaningful flavor/formulation modifier. |

The November 17 detailed equivalence artifact gives per-nutrient absolute/percentage differences and identifies missing versus reported-zero nutrients for all differing-ID pairs. `—` in macro profiles means unavailable, not zero.

## Interpretation and limitations

- Exact-ID scoring shows the hybrid at 56.25% F1 versus the NLP baseline’s 82.05%. Under the current post-hoc equivalence adjudication, the hybrid is 82.35% F1 on 27 decisive cases; NLP is 91.43% on 26 decisive cases. These equivalence metrics have different denominators due to separately excluded ambiguous cases and are selective manual metrics, not the original exact-ID scores.
- Hybrid was SR Legacy-first and made 16 SR Legacy assignments plus 6 NLP fallback assignments on the labeled set; it assigned 22 total and sent 8 to review. It corrected some identity matches but generated more exact-ID false positives than the NLP baseline.
- The equivalence outcomes are human judgments, not code-enforced truth labels. Branded records, unspecified preparation, and formulation differences remain a source of ambiguity. A different FDC ID is not automatically wrong, and similar macros do not establish identity.
- No validation rows, prior artifacts, matchers, or API configuration were changed. No source changes were made.

## Files created in this folder

- `final_evaluation_report.md` — this report with both exact-ID and post-hoc equivalence results and all 30 predictions.
- `comparison_results.csv` — the same 30 predictions and classifications in tabular form.
