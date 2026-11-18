# Task 9 Structured Retrieval Artifact Summary

Generated 2026-11-18T06:02:23.061001+00:00 UTC.

## Methodology

The existing report contains the six-query comparison in prose/table form but no saved row-level CSV or JSON output. The Phase 1 keyword rows below are recovered only from `docs/task9_semantic_vs_keyword_comparison.md`; the Phase 1 matcher was not executed. The saved report does not provide exact FDC IDs or descriptions for every considered Phase 1 candidate, so those fields remain blank or are explicitly described as the limited detail that was saved. Their displayed rank reflects report listing order only.

The legacy and contextual semantic result sets were reproduced using the existing persistent Chroma collections `recipe_ingredients` (126 records) and `recipe_ingredient_occurrences` (165 records). The model and embedding strategy are recorded on those collections. No index build was run. Searches were executed with Hugging Face and Transformers offline flags, using cached model weights; no USDA/API or external network request was made.

Context-aware searches used the exact recipe phrases in the existing report: `moong dal` → `High-Protein Moong Dal Cheela`, `rajma` → `High-Protein Dal Makhani & Paneer`, `atta` → `Modified Paneer Paratha`, `ajwain` → `Modified Paneer Paratha`, `kala namak` → `Tofu Scramble Toast`, `paneer` → `High-Protein Moong Dal Cheela`.

## Coverage

- Queries: 6.
- Retrieval categories: four (saved Phase 1 keyword results, previous ingredient-only semantic, contextual ingredient-only, contextual with recipe context).
- Semantic result rows: 54 (18 in each of the three semantic categories).
- Recovered Phase 1 candidate rows: 12; these are only the candidates explicitly named in the prior report.
- Total CSV rows: 66.

## Match to the existing report

All 18 semantic top-three lists matched the report’s candidate names and similarity values when rounded to three decimals. Their complete scores and occurrence-level metadata are stored in `retrieval_comparison.csv`. The previous Phase 1 candidates match only to the extent they were explicitly documented; no missing candidate details or ranks were inferred. For `paneer`, the saved contextual result describes the paneer occurrence tied for second with `oil` at .854; Chroma’s returned ordering in the reproduced run placed `oil` first among the tied results, which is recorded as returned.

## Findings and limitations

Context can move the requested occurrence up the ranking for several queries (including rajma, atta, ajwain, and kala namak), but it also brings other ingredients from the same recipe into the top results. Moong dal did not return the exact Moong Dal Cheela occurrence in the contextual top three; paneer was tied with oil and followed by salt in the context-aware results. These are qualitative observations only.

The Phase 1 and semantic systems return different candidate types (USDA FDC records versus local recipe ingredients), so this comparison is not a like-for-like accuracy evaluation. No relevance labels were created and no accuracy, precision, recall, or F1 was calculated. Similarity values are ranking signals, not confidence or equivalence evidence. Saved Phase 1 prose omits some candidate IDs, descriptions, and ranking scores; those omissions remain visible in the CSV rather than being filled from a matcher rerun.

## Artifacts

- `retrieval_comparison.csv`: structured rows for all saved/reproduced candidates.
- `retrieval_comparison.md`: ranked human-readable comparison by query and retrieval mode.
- `evaluation_summary.md`: methodology, coverage, report-match check, findings, and limitations.