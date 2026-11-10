"""Build/update the persistent local Task 9 ingredient index.

Usage: python scripts/build_ingredient_vector_index.py [--recipes PATH]
"""
from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--recipes", type=Path, default=REPO_ROOT / "data" / "recipes.json")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    try:
        recipes = json.loads(args.recipes.read_text(encoding="utf-8"))
        search = SemanticIngredientSearch(args.index, model_name=args.model)
        report = search.sync_from_recipes(recipes)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Embedding model: {args.model}")
    print(f"Index directory: {args.index}")
    print(f"Unique ingredients indexed: {report['indexed']}")
    print(f"New/changed embeddings generated: {report['embedded']}")
    print(f"Metadata records updated: {report['metadata_updated']}")
    print(f"Stale records removed: {report['removed']}")
    print(f"Index total: {report['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
