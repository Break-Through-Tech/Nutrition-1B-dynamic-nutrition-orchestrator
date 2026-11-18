# Task 9: Recipe-Contextual Semantic Retrieval Evaluation

## Objective

This report compares the existing ingredient-only semantic index with the new occurrence-level recipe-context index. The motivation is to retain the recipe context that can distinguish the same ingredient used in different dishes and support later matching or substitution review.

This is a qualitative retrieval inspection, not an ingredient-equivalence or accuracy evaluation. Similarity scores rank candidates and do not prove ingredient identity.

## Dataset and previous implementation

The source `data/recipes.json` contains 26 recipes, 165 ingredient occurrences, and 126 unique exact ingredient names. All 26 recipes are marked Indian. The data includes recipe names, cuisine, meal type, diet tags, ingredient quantities and units, optional ingredient notes, full instructions, and source-document names. There is no separate recipe-description field. `data/ingredients.csv` is a deduplicated 126-name list and does not retain recipe context.

The previous ChromaDB collection, `recipe_ingredients`, embeds only each unique ingredient name with `sentence-transformers/all-MiniLM-L6-v2` and cosine distance. Metadata combines recipe IDs and names for occurrences sharing the exact name. The previous qualitative comparison used six Indian ingredient queries and Phase 1 keyword candidates; it did not establish labeled retrieval accuracy.

## Updated contextual index

The new `recipe_ingredient_occurrences` collection stores one record per ingredient slot in each recipe (165 records for this dataset). Each deterministic record ID is based on the recipe ID and ingredient position. The embedded document contains source-provided ingredient name, recipe name, cuisine and meal type when present, diet tags, other ingredient names, ingredient notes, and the full recipe instructions. It does not claim that an instruction sentence applies specifically to one ingredient.

Chroma metadata stores the occurrence and recipe IDs, original and normalized ingredient name, ingredient position, quantity fields, ingredient and recipe notes, cuisine, meal type, diet tags, other ingredient names, servings, source document, and optional FDC ID already present in the source. The legacy collection remains separate. `--mode both` syncs both collections; `--rebuild-contextual` rebuilds only the contextual collection.

The embedding model remains `sentence-transformers/all-MiniLM-L6-v2`; both collections use cosine distance. The model's maximum input length is 256 tokens. Contextual documents therefore split into model-length chunks and their chunk embeddings are mean-pooled into one stored vector per occurrence. This keeps full instructions in the Chroma document while allowing text beyond the first model window to contribute to the contextual vector.

Ingredient-only contextual queries search documents beginning with the ingredient name. A context-aware query adds the supplied recipe phrase. Results retain occurrence-level recipe provenance, metadata, cosine distance, and the convenience value `1 - distance`. Neither score is an identity confidence.

## Testing and retrieval method

- Unit tests use deterministic mock embeddings and do not download model weights or call external APIs.
- `python3 scripts/build_ingredient_vector_index.py --mode both --rebuild-contextual` built both persistent collections from the unchanged recipe data.
- A repeat `--mode both` sync reported zero new embeddings, metadata-only updates, or stale removals for both collections.
- Both search modes were run against the same six ingredient queries. Context-aware searches additionally used recipe names that occur in the dataset.
- Phase 1 results below are the previously documented offline keyword-matcher observations from `task9_semantic_vs_keyword_comparison.md`; no Phase 1 matcher or USDA API was run as part of this report.

## Side-by-side observations

| Query | Phase 1 keyword candidate (previous offline review) | Previous ingredient-only semantic top results | New contextual, ingredient-only top results | Context-aware result and observation |
|---|---|---|---|---|
| `moong dal` | Accepted raw mung-bean FDC record. | `split moong dal` (.872); `yellow moong/toor dal` (.799); `moong dal, soaked overnight` (.742). | `moong dal, soaked, ground into paste` in Cheesy Moong Dal Quesadillas (.745); `yellow moong/toor dal` (.736); `sweet corn kernels, mild` (.718). | With High-Protein Moong Dal Cheela context, the related soaked/ground moong occurrence ranks first (.823), but `oil` from the requested cheela and sweet corn from a different recipe also rank highly. Context did not put the exact requested recipe occurrence in the top three. |
| `rajma` | Accepted `Kidney beans, NFS`. | `rajma` (1.000); `rajma, soaked overnight` (.714); unrelated `kasuri methi` (.441). | `rajma, soaked overnight` (.617); `rajma` (.587); `soya chunks, processed into fine grains` (.567). | With High-Protein Dal Makhani & Paneer context, the exact `rajma` occurrence ranks first (.847); `oil` and `low-fat paneer` from that same recipe follow. Context identifies the recipe but can promote its unrelated ingredients. |
| `atta` | Accepted whole-wheat flour FDC record. | `atta, for 2 rotis` (.615); `whole wheat flour (atta)` (.429); `chaat masala` (.371). | `whole wheat flour (atta)` in Modified Paneer Paratha (.564); `carom seeds (ajwain)` (.517); `low-fat paneer, grated` (.512). | With Modified Paneer Paratha context, the matching whole-wheat flour occurrence ranks first (.823), followed by red chili powder and paneer from that recipe. |
| `ajwain` | No accepted FDC ID in the saved snapshot; considered seed records were unrelated. | `carom seeds (ajwain)` (.483); `kala namak (black salt)` (.358); `rajma` (.353). | Two `carom seeds (ajwain)` occurrences rank first (.559, .530), from different recipes; `salt` ranks third (.452). | With Modified Paneer Paratha context, that recipe's carom-seed occurrence ranks first (.806). Paneer and onion entries from another recipe still appear next. |
| `kala namak` | Accepted `BLACK SALT` FDC record. | `kala namak (black salt)` (.802); `kala chana, boiled` (.568); `kala chana, soaked overnight and boiled` (.480). | `kala namak (black salt)` (.666); `black salt` in a chana salad (.547); `tomato, chopped` (.544). | With Tofu Scramble Toast context, the exact kala namak occurrence ranks first (.860); tofu and bread from the same recipe follow. |
| `paneer` | Accepted `Cheese, paneer` FDC record. | `low-fat paneer` (.819); `low-fat paneer, crumbled` (.750); `low-fat paneer, grated` (.740). | `ginger-garlic paste` (.711); `onions` (.708); `low-fat paneer, cubed and seared` (.705), all from Saag Paneer. | With High-Protein Moong Dal Cheela context, `low-fat paneer, crumbled` ties for second (.854) with `oil`; `salt` ranks third (.852). Context locates a relevant recipe but does not reliably separate the ingredient from other recipe entries. |

## Findings

- Occurrence-level indexing preserves distinctions the old collection collapsed. For example, `carom seeds (ajwain)` now appears as separate records for Modified Paneer Paratha and Mixed Dal Chilla Wraps, each with its own recipe metadata.
- Recipe context can help rank an occurrence associated with a named dish. In these examples, the requested occurrence ranked first for rajma, atta, ajwain, and kala namak when the matching recipe name was supplied.
- Context can also dilute ingredient-specific relevance. Full instructions and neighboring ingredients make all records from one recipe similar; `oil`, `paneer`, `salt`, or other unrelated ingredients can rank near the requested ingredient. The moong dal and paneer examples show this clearly.
- Contextual ingredient-only retrieval does not uniformly improve ranking. The `moong dal` query surfaced a corn ingredient among its top three, while `paneer` ranked recipe context terms ahead of a paneer occurrence.
- Phase 1 keyword search returns USDA food records and uses curated aliases; semantic search returns local recipe ingredient occurrences. The systems answer different retrieval questions. The qualitative examples do not show that one is generally more accurate.

## Limitations and next steps

- The corpus is small and all recipes are labeled Indian, so cuisine context cannot be evaluated across cuisines.
- The six queries are representative examples, not a reviewed retrieval benchmark. No precision, recall, F1, or top-k accuracy is reported.
- Context-aware examples use the correct recipe name supplied in the query. They do not establish that the system can infer the desired recipe context automatically.
- Mean-pooling instruction chunks ensures all full-instruction text can contribute, but long instructions may still dilute ingredient-specific signals.
- A future quantitative comparison should use independently reviewed acceptable ingredient-occurrence IDs and hard negatives, with both semantic versions evaluated on the same query/context set. Ingredient equivalence and USDA ID assignment should remain separate decisions.

## Conclusion

The contextual collection adds traceable per-recipe ingredient occurrences and allows recipe phrases to influence retrieval. In this small qualitative review, context often surfaces the requested recipe occurrence near the top, but also raises unrelated ingredients from the same dish. It is a useful candidate-generation aid; these results do not establish improved accuracy or ingredient equivalence.
