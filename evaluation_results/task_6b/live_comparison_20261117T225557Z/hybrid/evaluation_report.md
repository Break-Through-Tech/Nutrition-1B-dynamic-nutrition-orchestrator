# Fresh live USDA hybrid evaluation

Captured: 2026-11-17T22:58:39.913853+00:00 (UTC). Validation rows: 30 from unchanged `data/validation_set.csv`.

The matcher used live FoodData Central searches for both the SR Legacy stage and every NLP fallback search. No saved candidate snapshot was used as input.

## Exact-ID metrics

| Metric | Value |
| --- | --- |
| Accuracy | 53.33% |
| Precision | 40.91% |
| Recall | 90.00% |
| F1 | 56.25% |
| True positives | 9 |
| False positives | 13 |
| True negatives | 7 |
| False negatives | 1 |
| Assignment rate | 73.33% |
| Scored rows | 30/30 |
| API failed queries | 0 |
| Abstentions/review | 8 |

## Ingredient predictions

| Ingredient | Expected ID | Selected ID | Description | Type | Stage | Decision | SR status | NLP status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oats | 2708489 | 169705 | Oats (Includes foods for USDA's Food Distribution Program) | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| quinoa | 168874 | 168874 | Quinoa, uncooked | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| brown rice | 2710789 | 168876 | Rice, brown, parboiled, dry, UNCLE BEN'S | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| almonds | 2707485 | 170567 | Nuts, almonds | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| chia seeds | 2707590 | 170554 | Seeds, chia seeds, dried | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| olive oil | 2710186 | 167737 | Oil, corn, peanut, and olive | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| hing | None | — | — | — | — | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate |
| rajma | 2707379 | 173744 | Beans, kidney, red, mature seeds, raw | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| kasuri methi | None | — | — | — | — | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate |
| kala namak (black salt) | 2587261 | 2587261 | BLACK SALT | Branded | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| whole wheat flour (atta) | 790085 | 168944 | Wheat flour, whole-grain, soft wheat | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| ghee | 171314 | 171314 | Butter, Clarified butter (ghee) | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| degi mirch | 171329 | 171329 | Spices, paprika | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| carom seeds (ajwain) | None | — | — | — | — | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate |
| dry soya chunks | 2707451 | 2707451 | Textured vegetable protein, dry | Survey (FNDDS) | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| moong dal, soaked overnight | 174256 | 174256 | Mung beans, mature seeds, raw | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| low-fat paneer, crumbled | 2705740 | 2705740 | Cheese, paneer | Survey (FNDDS) | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| extra-firm tofu, cubed | 174290 | 174290 | Tofu, extra firm, prepared with nigari | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| kala chana, soaked overnight and boiled | 2134686 | 2054512 | KALA CHANA | Branded | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| kabuli chana, soaked and boiled | 2707414 | 2707414 | Chickpeas, NFS | Survey (FNDDS) | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| garlic, minced | 2709786 | 169230 | Garlic, raw | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| low-fat Greek yogurt | 2705423 | 170903 | Yogurt, Greek, plain, lowfat | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| unflavored whey protein | 173180 | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | Branded | nlp_fallback | accepted_nlp_fallback | no_suitable_candidate | matched |
| low-sodium soy sauce | 2707443 | 172474 | Soy sauce, reduced sodium, made from hydrolyzed vegetable protein | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| fat-free Greek yogurt | 2076798 | 170902 | Yogurt, Greek, vanilla, nonfat | SR Legacy | sr_legacy | accepted_sr_legacy | matched | not_attempted |
| whole black urad dal | 2168881 | — | — | — | — | nlp_no_suitable_candidate | no_suitable_candidate | no_suitable_candidate |
| kadhai spice mix (crushed coriander seeds / dry red chili) | None | — | — | — | — | composite_requires_review | not_attempted | not_attempted |
| onion-tomato gravy base | None | — | — | — | — | composite_requires_review | not_attempted | not_attempted |
| mint-cilantro-yogurt chutney | None | — | — | — | — | composite_requires_review | not_attempted | not_attempted |
| quinoa-rice blend | None | — | — | — | — | composite_requires_review | not_attempted | not_attempted |

## API failures

| Mode | Query | Error |
| --- | --- | --- |
| None | — | No failed live API queries |

Candidate responses are in `live_candidate_snapshot.json`; per-row trace and metrics are in `hybrid_results.json`.
