"""Build/update the legacy and/or contextual local Task 9 indexes.

Usage: python scripts/build_ingredient_vector_index.py [--mode both|legacy|contextual]
"""
from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--recipes", type=Path, default=REPO_ROOT / "data" / "recipes.json")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--mode", choices=("both", "legacy", "contextual"), default="both",
        help="Collections to sync; both preserves the ingredient-only baseline while building contextual records.",
    )
    parser.add_argument(
        "--rebuild-contextual", action="store_true",
        help="Delete and recreate only the contextual collection before syncing it.",
    )
    args = parser.parse_args()
    try:
        recipes = json.loads(args.recipes.read_text(encoding="utf-8"))
        reports = {}
        if args.mode in ("both", "legacy"):
            legacy = SemanticIngredientSearch(
                args.index, model_name=args.model, collection_name=COLLECTION_NAME
            )
            reports["ingredient-only"] = legacy.sync_from_recipes(recipes)
        if args.mode in ("both", "contextual"):
            if args.rebuild_contextual:
                import chromadb
                from chromadb.config import Settings
                client = chromadb.PersistentClient(
                    path=str(args.index), settings=Settings(anonymized_telemetry=False)
                )
                collection_names = {
                    item if isinstance(item, str) else item.name
                    for item in client.list_collections()
                }
                if CONTEXTUAL_COLLECTION_NAME in collection_names:
                    client.delete_collection(name=CONTEXTUAL_COLLECTION_NAME)
            contextual = SemanticIngredientSearch(
                args.index, model_name=args.model, collection_name=CONTEXTUAL_COLLECTION_NAME
            )
            reports["contextual"] = contextual.sync_contextual_from_recipes(recipes)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Embedding model: {args.model}")
    print(f"Index directory: {args.index}")
    for collection, report in reports.items():
        print(f"{collection} collection: {report['total']} records")
        print(f"  records in source: {report['indexed']}")
        print(f"  new/changed embeddings: {report['embedded']}")
        print(f"  metadata-only updates: {report['metadata_updated']}")
        print(f"  stale records removed: {report['removed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
