# All-data-type + NLP Hybrid Evaluation

Captured: 2026-11-18T03:32:52.249403+00:00 (UTC). Validation set: 30 rows from the unchanged `data/validation_set.csv`.

## Comparison

| Evaluation | Accuracy | Precision | Recall | F1 | Assignment rate | Examples scored |
| --- | --- | --- | --- | --- | --- | --- |
| Original live NLP baseline | 76.67% | 72.73% | 94.12% | 82.05% | 73.33% | 30/30 |
| Fully live hybrid | 80.00% | 73.91% | 100.00% | 85.00% | 76.67% | 30/30 |
| Controlled hybrid (live SR + baseline NLP) | 80.00% | 73.91% | 100.00% | 85.00% | 76.67% | 30/30 |

Metrics use the existing exact-FDC-ID TP/FP/FN/TN rules. Rows with an unresolved all-data-type candidate search or required NLP API error are excluded from that track's metric denominator and listed as unscored; they are not treated as ordinary abstentions. A failed NLP query fetched after the matcher had already accepted an earlier query is still listed in the request-error snapshot, but does not invalidate that completed decision.

### Fully live hybrid

Scored 30/30 rows; 0 rows excluded from metrics due to unresolved stage API errors.
TP=17, FP=6, TN=7, FN=0; 0 failed live API query/mode request(s).
All-data-type-stage matches: 21; NLP fallback matches: 2; abstentions/review decisions: 7.

### Controlled hybrid

Scored 30/30 rows; 0 rows excluded from metrics due to unresolved stage API errors.
TP=17, FP=6, TN=7, FN=0; 0 failed live API query/mode request(s).
All-data-type-stage matches: 21; NLP fallback matches: 2; abstentions/review decisions: 7.

## Stage contribution and comparison

Fully live hybrid NLP fallback accepted 2 ingredient(s); controlled hybrid accepted 2.
Live hybrid changes from baseline: oats, brown rice, low-fat Greek yogurt, fat-free Greek yogurt, whole black urad dal.
Corrected to a correct prediction vs baseline: oats, whole black urad dal.
Controlled changes from baseline: oats, brown rice, low-fat Greek yogurt, fat-free Greek yogurt, whole black urad dal.
Controlled corrected to a correct prediction vs baseline: oats, whole black urad dal.
A difference between fully live and controlled tracks can reflect changed USDA candidate results. The controlled track holds NLP candidate responses to the baseline snapshot; the live SR responses are shared with Track A.

## Fully live hybrid ingredient results

| Ingredient | Expected | Selected | Description | Type | Stage | Candidate search | NLP status | Decision | Correct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oats | 2708489 | 2708489 | Oats, raw | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| quinoa | 168874 | 168874 | Quinoa, uncooked | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| brown rice | 2710789 | 173155 | Snacks, brown rice chips | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | No |
| almonds | 2707485 | 2707485 | Almonds, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| chia seeds | 2707590 | 2707590 | Chia seeds | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| olive oil | 2710186 | 2710186 | Olive oil | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| hing | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| rajma | 2707379 | 2707379 | Kidney beans, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| kasuri methi | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| kala namak (black salt) | 2587261 | 2587261 | BLACK SALT | Branded | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| whole wheat flour (atta) | 790085 | 790085 | Flour, whole wheat, unenriched | Foundation | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| ghee | 171314 | 171314 | Butter, Clarified butter (ghee) | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| degi mirch | 171329 | 171329 | Spices, paprika | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| carom seeds (ajwain) | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| dry soya chunks | 2707451 | 2707451 | Textured vegetable protein, dry | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| moong dal, soaked overnight | 174256 | 174256 | Mung beans, mature seeds, raw | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| low-fat paneer, crumbled | 2705740 | 2705740 | Cheese, paneer | Survey (FNDDS) | nlp_fallback | no_suitable_candidate | matched | accepted_nlp_fallback | Yes |
| extra-firm tofu, cubed | 174290 | 2310367 | EXTRA-FIRM TOFU | Branded | all_data_types | matched | not_attempted | accepted_candidate | No |
| kala chana, soaked overnight and boiled | 2134686 | 2054512 | KALA CHANA | Branded | nlp_fallback | no_suitable_candidate | matched | accepted_nlp_fallback | No |
| kabuli chana, soaked and boiled | 2707414 | 2707414 | Chickpeas, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| garlic, minced | 2709786 | 2709786 | Garlic, raw | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| low-fat Greek yogurt | 2705423 | 170903 | Yogurt, Greek, plain, lowfat | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | No |
| unflavored whey protein | 173180 | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | Branded | all_data_types | matched | not_attempted | accepted_candidate | No |
| low-sodium soy sauce | 2707443 | 2707443 | Soy sauce, reduced sodium | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| fat-free Greek yogurt | 2076798 | 2705432 | Yogurt, Greek, nonfat milk, fruit | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | No |
| whole black urad dal | 2168881 | 2168881 | WHOLE BLACK GRAM | Branded | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| kadhai spice mix (crushed coriander seeds / dry red chili) | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| onion-tomato gravy base | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| mint-cilantro-yogurt chutney | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| quinoa-rice blend | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |

## Controlled hybrid ingredient results

| Ingredient | Expected | Selected | Description | Type | Stage | Candidate search | NLP status | Decision | Correct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oats | 2708489 | 2708489 | Oats, raw | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| quinoa | 168874 | 168874 | Quinoa, uncooked | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| brown rice | 2710789 | 173155 | Snacks, brown rice chips | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | No |
| almonds | 2707485 | 2707485 | Almonds, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| chia seeds | 2707590 | 2707590 | Chia seeds | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| olive oil | 2710186 | 2710186 | Olive oil | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| hing | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| rajma | 2707379 | 2707379 | Kidney beans, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| kasuri methi | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| kala namak (black salt) | 2587261 | 2587261 | BLACK SALT | Branded | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| whole wheat flour (atta) | 790085 | 790085 | Flour, whole wheat, unenriched | Foundation | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| ghee | 171314 | 171314 | Butter, Clarified butter (ghee) | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| degi mirch | 171329 | 171329 | Spices, paprika | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| carom seeds (ajwain) | None | — | — | — | — | no_suitable_candidate | no_suitable_candidate | nlp_no_suitable_candidate | Yes |
| dry soya chunks | 2707451 | 2707451 | Textured vegetable protein, dry | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| moong dal, soaked overnight | 174256 | 174256 | Mung beans, mature seeds, raw | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| low-fat paneer, crumbled | 2705740 | 2705740 | Cheese, paneer | Survey (FNDDS) | nlp_fallback | no_suitable_candidate | matched | accepted_nlp_fallback | Yes |
| extra-firm tofu, cubed | 174290 | 2310367 | EXTRA-FIRM TOFU | Branded | all_data_types | matched | not_attempted | accepted_candidate | No |
| kala chana, soaked overnight and boiled | 2134686 | 2054512 | KALA CHANA | Branded | nlp_fallback | no_suitable_candidate | matched | accepted_nlp_fallback | No |
| kabuli chana, soaked and boiled | 2707414 | 2707414 | Chickpeas, NFS | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| garlic, minced | 2709786 | 2709786 | Garlic, raw | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| low-fat Greek yogurt | 2705423 | 170903 | Yogurt, Greek, plain, lowfat | SR Legacy | all_data_types | matched | not_attempted | accepted_candidate | No |
| unflavored whey protein | 173180 | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | Branded | all_data_types | matched | not_attempted | accepted_candidate | No |
| low-sodium soy sauce | 2707443 | 2707443 | Soy sauce, reduced sodium | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| fat-free Greek yogurt | 2076798 | 2705432 | Yogurt, Greek, nonfat milk, fruit | Survey (FNDDS) | all_data_types | matched | not_attempted | accepted_candidate | No |
| whole black urad dal | 2168881 | 2168881 | WHOLE BLACK GRAM | Branded | all_data_types | matched | not_attempted | accepted_candidate | Yes |
| kadhai spice mix (crushed coriander seeds / dry red chili) | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| onion-tomato gravy base | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| mint-cilantro-yogurt chutney | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |
| quinoa-rice blend | None | — | — | — | — | not_attempted | not_attempted | composite_requires_review | Yes |

## Incorrect assignments

| Track | Ingredient | Expected FDC ID | Selected FDC ID | Description | Stage |
| --- | --- | --- | --- | --- | --- |
| Live | brown rice | 2710789 | 173155 | Snacks, brown rice chips | all_data_types |
| Live | extra-firm tofu, cubed | 174290 | 2310367 | EXTRA-FIRM TOFU | all_data_types |
| Live | kala chana, soaked overnight and boiled | 2134686 | 2054512 | KALA CHANA | nlp_fallback |
| Live | low-fat Greek yogurt | 2705423 | 170903 | Yogurt, Greek, plain, lowfat | all_data_types |
| Live | unflavored whey protein | 173180 | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | all_data_types |
| Live | fat-free Greek yogurt | 2076798 | 2705432 | Yogurt, Greek, nonfat milk, fruit | all_data_types |
| Controlled | brown rice | 2710789 | 173155 | Snacks, brown rice chips | all_data_types |
| Controlled | extra-firm tofu, cubed | 174290 | 2310367 | EXTRA-FIRM TOFU | all_data_types |
| Controlled | kala chana, soaked overnight and boiled | 2134686 | 2054512 | KALA CHANA | nlp_fallback |
| Controlled | low-fat Greek yogurt | 2705423 | 170903 | Yogurt, Greek, plain, lowfat | all_data_types |
| Controlled | unflavored whey protein | 173180 | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | all_data_types |
| Controlled | fat-free Greek yogurt | 2076798 | 2705432 | Yogurt, Greek, nonfat milk, fruit | all_data_types |

## Manual review and API failures

| Track | Ingredient | Reason | SR status | NLP status | Errors |
| --- | --- | --- | --- | --- | --- |
| Live | hing | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Live | kasuri methi | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Live | carom seeds (ajwain) | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Live | kadhai spice mix (crushed coriander seeds / dry red chili) | composite_requires_review | not_attempted | not_attempted | — |
| Live | onion-tomato gravy base | composite_requires_review | not_attempted | not_attempted | — |
| Live | mint-cilantro-yogurt chutney | composite_requires_review | not_attempted | not_attempted | — |
| Live | quinoa-rice blend | composite_requires_review | not_attempted | not_attempted | — |
| Controlled | hing | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Controlled | kasuri methi | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Controlled | carom seeds (ajwain) | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate | — |
| Controlled | kadhai spice mix (crushed coriander seeds / dry red chili) | composite_requires_review | not_attempted | not_attempted | — |
| Controlled | onion-tomato gravy base | composite_requires_review | not_attempted | not_attempted | — |
| Controlled | mint-cilantro-yogurt chutney | composite_requires_review | not_attempted | not_attempted | — |
| Controlled | quinoa-rice blend | composite_requires_review | not_attempted | not_attempted | — |

Baseline snapshot SHA-256: `932b4eeff51ffe15e95beb7f8918baebb1f37eddae416720f60d479e72de14ca`. Baseline report SHA-256: `35ea4e4e10a8efab29b645651372ab0b319c81744739801118cc951eb3f76390`.
The original baseline folder was read only. Candidate responses used by Track A are saved in `live_candidate_snapshot.json`; Track B uses the exact baseline snapshot copied to `baseline_nlp_candidate_snapshot_reference.json` and reuses Track A's captured all-data-type responses.
