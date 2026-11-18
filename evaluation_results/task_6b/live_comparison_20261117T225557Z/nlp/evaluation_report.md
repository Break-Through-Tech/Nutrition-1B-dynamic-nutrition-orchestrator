# Live USDA NLP matcher baseline

Captured: 2026-11-17T22:56:41.358207+00:00 (UTC). Validation rows: 30. Scored: 30. Unscored due to API failures: 0.

## Metrics (failed rows excluded)

| Metric | Value |
| --- | --- |
| Accuracy | 76.67% |
| Precision | 72.73% |
| Recall | 94.12% |
| F1 | 82.05% |
| True positives | 16 |
| False positives | 6 |
| True negatives | 7 |
| False negatives | 1 |
| Correct matches | 16 |
| Incorrect assignments | 6 |
| Correct abstentions | 7 |
| Missed expected matches | 1 |
| Assignment rate | 73.33% |

## Ingredient results

| Original ingredient | USDA API search query/queries | Live candidates? | Selected FDC ID | Selected description | Expected FDC ID | Correct? | Abstained? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| oats | oats | Yes | 2779253 | Oats, puffed | 2708489 | No | No |
| quinoa | quinoa | Yes | 168874 | Quinoa, uncooked | 168874 | Yes | No |
| brown rice | brown rice | Yes | 2779256 | Brown rice, puffed | 2710789 | No | No |
| almonds | almonds | Yes | 2707485 | Almonds, NFS | 2707485 | Yes | No |
| chia seeds | chia seeds | Yes | 2707590 | Chia seeds | 2707590 | Yes | No |
| olive oil | olive oil | Yes | 2710186 | Olive oil | 2710186 | Yes | No |
| hing | asafoetida; hing | Yes | — | — | None | Abstained | Yes |
| rajma | kidney beans; rajma | Yes | 2707379 | Kidney beans, NFS | 2707379 | Yes | No |
| kasuri methi | fenugreek leaves dried; kasuri methi | Yes | — | — | None | Abstained | Yes |
| kala namak (black salt) | black salt; kala namak | Yes | 2587261 | BLACK SALT | 2587261 | Yes | No |
| whole wheat flour (atta) | whole wheat flour; wheat flour | Yes | 790085 | Flour, whole wheat, unenriched | 790085 | Yes | No |
| ghee | butter oil clarified; ghee | Yes | 171314 | Butter, Clarified butter (ghee) | 171314 | Yes | No |
| degi mirch | paprika; degi mirch | Yes | 171329 | Spices, paprika | 171329 | Yes | No |
| carom seeds (ajwain) | carom seeds | Yes | — | — | None | Abstained | Yes |
| dry soya chunks | dry textured vegetable protein soy; textured vegetable protein soy; dry soya chunks | Yes | 2707451 | Textured vegetable protein, dry | 2707451 | Yes | No |
| moong dal, soaked overnight | mung beans; moong dal | Yes | 174256 | Mung beans, mature seeds, raw | 174256 | Yes | No |
| low-fat paneer, crumbled | low-fat paneer cheese; paneer cheese; low-fat paneer | Yes | 2705740 | Cheese, paneer | 2705740 | Yes | No |
| extra-firm tofu, cubed | extra-firm tofu; tofu | Yes | 2310367 | EXTRA-FIRM TOFU | 174290 | No | No |
| kala chana, soaked overnight and boiled | chickpeas black; kala chana | Yes | 2054512 | KALA CHANA | 2134686 | No | No |
| kabuli chana, soaked and boiled | chickpeas; kabuli chana | Yes | 2707414 | Chickpeas, NFS | 2707414 | Yes | No |
| garlic, minced | garlic | Yes | 2709786 | Garlic, raw | 2709786 | Yes | No |
| low-fat Greek yogurt | low-fat greek yogurt; greek yogurt | Yes | 2536668 | LOW-FAT GREEK YOGURT | 2705423 | No | No |
| unflavored whey protein | unflavored whey protein; whey protein | Yes | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 173180 | No | No |
| low-sodium soy sauce | reduced sodium soy sauce; soy sauce; low-sodium soy sauce | Yes | 2707443 | Soy sauce, reduced sodium | 2707443 | Yes | No |
| fat-free Greek yogurt | fat-free greek yogurt; greek yogurt | Yes | 2076798 | FAT-FREE GREEK YOGURT | 2076798 | Yes | No |
| whole black urad dal | black gram; black black gram; whole black urad dal | Yes | — | — | 2168881 | Abstained | Yes |
| kadhai spice mix (crushed coriander seeds / dry red chili) | (not searched: composite) | Not needed (composite) | — | — | None | Abstained | Yes |
| onion-tomato gravy base | (not searched: composite) | Not needed (composite) | — | — | None | Abstained | Yes |
| mint-cilantro-yogurt chutney | (not searched: composite) | Not needed (composite) | — | — | None | Abstained | Yes |
| quinoa-rice blend | (not searched: composite) | Not needed (composite) | — | — | None | Abstained | Yes |

## Incorrect matches and abstentions

| Outcome | Ingredient | Selected FDC ID | Description | Expected FDC ID | Matcher reason |
| --- | --- | --- | --- | --- | --- |
| FP | oats | 2779253 | Oats, puffed | 2708489 | — |
| FP | brown rice | 2779256 | Brown rice, puffed | 2710789 | — |
| TN | hing | — | — | None | below_threshold |
| TN | kasuri methi | — | — | None | below_threshold |
| TN | carom seeds (ajwain) | — | — | None | below_threshold |
| FP | extra-firm tofu, cubed | 2310367 | EXTRA-FIRM TOFU | 174290 | — |
| FP | kala chana, soaked overnight and boiled | 2054512 | KALA CHANA | 2134686 | — |
| FP | low-fat Greek yogurt | 2536668 | LOW-FAT GREEK YOGURT | 2705423 | — |
| FP | unflavored whey protein | 2510560 | WHEY PROTEIN 20 G POWDER, UNFLAVORED, UNFLAVORED | 173180 | — |
| FN | whole black urad dal | — | — | 2168881 | below_threshold |
| TN | kadhai spice mix (crushed coriander seeds / dry red chili) | — | — | None | composite |
| TN | onion-tomato gravy base | — | — | None | composite |
| TN | mint-cilantro-yogurt chutney | — | — | None | composite |
| TN | quinoa-rice blend | — | — | None | composite |

## API failures

None.

Candidate snapshot: `evaluation_results/live_comparison_20261117T225557Z/nlp/candidate_snapshot.json`
