"""Search the local Task 9 ingredient vector index.

Build the index first with scripts/build_ingredient_vector_index.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.semantic_ingredient_search import (  # noqa: E402
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
    args = parser.parse_args()
    try:
        search = SemanticIngredientSearch(args.index, model_name=args.model)
        results = search.search(args.ingredient, top_k=args.top_k)
    except (ValueError, RuntimeError) as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("No indexed ingredients. Build the index first.")
        return 0
    for rank, result in enumerate(results, 1):
        print(
            f"{rank}. {result.original_name}  "
            f"similarity={result.similarity:.4f} distance={result.distance:.4f}"
        )
        print(f"   normalized: {result.normalized_name}")
        print(f"   recipes: {', '.join(result.recipe_names)}")
    print("Candidates only; similarity does not confirm ingredient identity or assign a USDA ID.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
