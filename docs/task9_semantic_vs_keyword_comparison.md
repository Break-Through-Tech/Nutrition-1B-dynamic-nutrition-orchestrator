# Task 9: Semantic and Keyword Ingredient Retrieval Comparison

## Purpose

This report compares the existing Phase 1 keyword matcher with Task 9 semantic ingredient retrieval on the same recipe ingredient queries. It describes observed candidates; it does not claim either system has higher measured accuracy.

## Testing methodology

- Used six ingredient queries from names or name variants in `data/recipes.json`: `moong dal`, `rajma`, `atta`, `ajwain`, `kala namak`, and `paneer`.
- Also queried `spacecraft battery` and `dragonfruit powder` as unrelated examples.
- Ran Phase 1 using its existing normalization/synonym rules and the checked-in offline `data/usda_candidates.json` snapshot (47 captured query strings). No live USDA request was made.
- Ran semantic retrieval against the persistent 126-name Chroma index using `sentence-transformers/all-MiniLM-L6-v2`, top 3. Reported similarity is derived from Chroma cosine distance; it is a ranking signal, not an identity confidence.
- Relevance in the table is a qualitative inspection of the displayed names/descriptions. It is not an independently reviewed labeled evaluation set.

Phase 1 returns USDA FoodData Central records and may accept one FDC ID or decline a match while retaining considered records. Task 9 returns recipe ingredient-name strings. Those candidate types differ, so side-by-side relevance is informative but not a direct like-for-like accuracy comparison.

## Side-by-side results

| Query | Phase 1 keyword candidates (final / considered) | Task 9 semantic candidates (top 3; similarity) | Qualitative relevance and differences |
|---|---|---|---|
| `moong dal` | Accepted `Mung beans, mature seeds, raw` (FDC 174256, score 1.00). Other considered: sprouted mung beans; branded `MUNG BEANS`. | `split moong dal` (.872); `yellow moong/toor dal` (.799); `moong dal, soaked overnight` (.742). | Both surface mung/moong-related items. Phase 1 normalizes the alias to the English USDA name and selects a raw mung record. Semantic retrieval returns source recipe strings, including a mixed dal candidate that needs review. |
| `rajma` | Accepted `Kidney beans, NFS` (FDC 2707379, score 1.00). Other considered include raw kidney beans and a prepared kidney-bean record. | `rajma` (1.000); `rajma, soaked overnight` (.714); `kasuri methi` (.441). | Both retrieve a relevant exact or close recipe name. Phase 1 offers USDA records; semantic ranks exact raw-name identity first. The third semantic result is unrelated noise. |
| `atta` | Accepted `Flour, whole wheat, unenriched` (FDC 790085, score 1.00). | `atta, for 2 rotis` (.616); `whole wheat flour (atta)` (.429); `chaat masala` (.371). | Phase 1 maps `atta` through its synonym table to a clear USDA whole-wheat-flour result. Semantic retrieval finds local recipe variants, but the parenthetical whole-wheat-flour variant ranks below the rotis entry and has a modest score. |
| `ajwain` | No accepted FDC ID. Considered `Chia seeds` (.779), `Flax seeds` (.750), and `Mixed seeds` (.741); these are not relevant carom-seed matches. | `carom seeds (ajwain)` (.483); `kala namak (black salt)` (.358); `rajma` (.353). | Semantic places the relevant local parenthetical name first, but with a low score and irrelevant alternatives. Phase 1 has a curated `ajwain` → `carom seeds` synonym, but this snapshot's returned records are unrelated and remain below its acceptance threshold. |
| `kala namak` | Accepted `BLACK SALT` (FDC 2587261, score .94). Other considered results include unrelated records. | `kala namak (black salt)` (.802); `kala chana, boiled` (.568); `kala chana, soaked overnight and boiled` (.480). | Both top candidates are relevant. Phase 1 retrieves an FDC black-salt record; semantic returns the local recipe spelling. Its lower-ranked kala chana entries share words but are different ingredients. |
| `paneer` | Accepted `Cheese, paneer` (FDC 2705740, score 1.00). Other considered results are paneer records. | `low-fat paneer` (.819); `low-fat paneer, crumbled` (.750); `low-fat paneer, grated` (.740). | Both return relevant candidates. Phase 1 selects a USDA record; semantic exposes local fat/preparation variants, which matter for later human review but do not establish a USDA identity. |
| `spacecraft battery` | **Unavailable:** snapshot does not contain normalized query `spacecraft battery`; strict offline lookup reports a coverage gap. | `lemon juice` (.158); `atta, for 2 rotis` (.154); `mint leaves` (.150). | Semantic scores are low and candidates appear unrelated. Phase 1 cannot be characterized as returning no match: its checked-in snapshot has no data for this query. |
| `dragonfruit powder` | **Unavailable:** snapshot does not contain normalized query `dragonfruit powder`; strict offline lookup reports a coverage gap. | `cumin powder` (.614); `red chili powder` (.599); `roasted cumin powder` (.547). | Semantic returns powder-name matches that appear unrelated to dragonfruit. This is a useful example of token/semantic proximity producing plausible-looking but incorrect candidates. Phase 1 is not testable from the current snapshot. |

## Observations

- Phase 1's curated synonym table helps bridge Indian names to the vocabulary used by USDA. In these runs, `moong dal`, `rajma`, `atta`, `kala namak`, and `paneer` resolved to relevant USDA records. For `ajwain`, the alias was transformed to `carom seeds`, but the available snapshot candidates were not relevant, so the matcher declined to assign an FDC ID.
- Keyword normalization depends on its explicit synonym and preparation vocabularies. It can miss an unlisted transliteration or spelling variation; token and character similarity may help rank a near-spelling among retrieved records, but cannot reliably supply a missing semantic alias.
- Semantic retrieval is useful for finding the exact local spelling and ingredient variants. It returns recipe strings with recipe provenance, but has no USDA catalog or concept-level identity mapping.
- Similarity ranking can place a useful candidate first (`carom seeds (ajwain)`), while still returning misleading alternatives. Conversely, the unrelated `dragonfruit powder` query received a .614 similarity for `cumin powder`.
- Keyword matching has its own failure modes: synonym coverage must be curated, and an offline snapshot only supports query strings it captured. A missing snapshot entry is a coverage gap, not evidence that USDA has no relevant food.
- These outputs do not establish that semantic retrieval is generally better or worse. They show different strengths and error modes on a small set of examples.

## Limitations and evaluation metrics

No precision, recall, F1, top-k accuracy, or overall accuracy is calculated. The existing validation labels judge whether a proposed USDA FDC ID is the right final food record; they do not label acceptable local ingredient-name candidates. Reusing them for semantic retrieval would conflate candidate retrieval with final food identification.

The unrelated Phase 1 queries were not captured in the local USDA snapshot. Testing them against live USDA would require a network search and would introduce a different, time-varying retrieval source, so this comparison reports the coverage gap instead of inventing a no-match result.

For quantitative comparison, create an independently reviewed retrieval dataset with each query linked to one or more acceptable canonical ingredient IDs from the recipe corpus, plus reviewed hard negatives (for example, `toor dal` versus `moong dal`). Reviewers should judge ambiguous variants and prepared/composite forms. Run both systems against the same fixed query set and compare candidate recall at k, precision at k, MRR or top-k accuracy where appropriate, and manual-review rate. Keep USDA FDC identity evaluation separate.

## Recommendations

1. Keep semantic results as suggestions that require verification; do not turn similarity directly into an FDC ID.
2. Do not select a global similarity cutoff from these examples. A cutoff low enough to retain `carom seeds (ajwain)` may also retain misleading matches; a higher cutoff may discard useful variants such as the `atta` parenthetical candidate. Calibrate an abstention threshold and/or score margin only against reviewed retrieval labels.
3. Consider a separately maintained, ingredient-specific alias/normalization layer for known Indian-English equivalents and preparation modifiers. Preserve the source name and keep this layer separate from the Phase 1 matcher unless a future, reviewed integration demonstrates value.
4. Expand the fixed offline USDA snapshot before interpreting Phase 1 results for new queries; report uncaptured terms explicitly.
5. Review semantically close but distinct ingredients and composites, especially mixed dals, spice blends, and prepared ingredients.

## Conclusion

Both approaches produced relevant candidates for several shared queries, but each also showed limitations. Phase 1 produced useful USDA records where its synonym mapping and snapshot coverage aligned. Task 9 surfaced local variants and exact recipe spellings, while also returning misleading neighbors for unrelated or ambiguous queries. The evidence supports keeping semantic retrieval as a separate candidate-generation aid and collecting reviewed retrieval labels before claiming a performance advantage or reporting quantitative metrics.
