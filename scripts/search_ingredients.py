"""Search the local Task 9 ingredient vector index.

Build the indexes first with scripts/build_ingredient_vector_index.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.semantic_ingredient_search import (  # noqa: E402
    COLLECTION_NAME,
    CONTEXTUAL_COLLECTION_NAME,
    DEFAULT_INDEX_PATH,
    DEFAULT_MODEL,
    SemanticIngredientSearch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ingredient", help="Ingredient phrase to search for.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--contextual", action="store_true",
        help="Search occurrence-level recipe-context records instead of the ingredient-only baseline.",
    )
    parser.add_argument(
        "--recipe-context", help="Optional recipe name, cuisine, or other query context; implies --contextual."
    )
    args = parser.parse_args()
    try:
        contextual = args.contextual or args.recipe_context is not None
        search = SemanticIngredientSearch(
            args.index,
            model_name=args.model,
            collection_name=CONTEXTUAL_COLLECTION_NAME if contextual else COLLECTION_NAME,
        )
        if contextual:
            results = search.search_contextual(
                args.ingredient, top_k=args.top_k, recipe_context=args.recipe_context
            )
        else:
            results = search.search(args.ingredient, top_k=args.top_k)
    except (ValueError, RuntimeError) as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("No indexed ingredients. Build the index first.")
        return 0
    for rank, result in enumerate(results, 1):
        print(f"{rank}. {result.original_name}  similarity={result.similarity:.4f} distance={result.distance:.4f}")
        print(f"   normalized: {result.normalized_name}")
        if contextual:
            print(f"   occurrence: {result.occurrence_id}  recipe: {result.recipe_name} ({result.recipe_id})")
            print(f"   cuisine/meal: {result.cuisine or '—'} / {result.meal_type or '—'}")
            print(f"   diet tags: {', '.join(result.diet_tags) or '—'}")
            print(f"   other ingredients: {', '.join(result.other_ingredients) or '—'}")
            print(f"   quantity: {result.quantity if result.quantity is not None else result.quantity_text or '—'} {result.unit or ''}".rstrip())
            print(f"   ingredient notes: {result.notes or '—'}")
            print(f"   source document: {result.source_doc or '—'}")
        else:
            print(f"   recipes: {', '.join(result.recipe_names)}")
    print("Candidates only; similarity does not confirm ingredient identity or assign a USDA ID.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
