"""Capture USDA search results to disk so matching is reproducible (Task 6).

Why this exists: an F1 score measured against a live API is not a result anyone
can check. USDA re-indexes, results shift, and the number moves. This script
runs the searches the matcher would perform, once, and writes the candidates to
`data/usda_candidates.json`. After that the matcher, the evaluation, and the
test suite all run offline and produce the same answer every time.

Requires a USDA API key (free: https://fdc.nal.usda.gov/api-key-signup).
Put it in a local `.env` file at the repository root -- git ignores it:

    USDA_API_KEY=your_key_here

Verify setup first with: python scripts/check_api_key.py

Run from the repository root:

    python scripts/snapshot_usda_candidates.py --validation    # 30-item set
    python scripts/snapshot_usda_candidates.py                 # all ingredients
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.config import (  # noqa: E402
    MissingAPIKeyError,
    get_api_key,
    mask,
)
from nutrition_engine.ingredient_matcher import is_composite, normalize  # noqa: E402
from nutrition_engine.usda_search import search_queries  # noqa: E402

INGREDIENTS_CSV = REPO_ROOT / "data" / "ingredients.csv"
VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"
OUTPUT_JSON = REPO_ROOT / "data" / "usda_candidates.json"


def read_names(path: Path, column: str) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [row[column] for row in csv.DictReader(handle) if row.get(column)]


def collect_queries(names: list[str]) -> list[str]:
    """Expand each ingredient into the queries the matcher would actually run.

    Deduplicated: many ingredients normalize onto the same query (all four
    paneer variants collapse to "paneer cheese"), which keeps the request
    count well under the hourly rate limit.
    """
    queries: list[str] = []
    for name in names:
        # Composite entries are refused by the matcher without ever being
        # searched, so querying them wastes quota and can produce malformed
        # requests (USDA rejects "a / b" with HTTP 400).
        if is_composite(name):
            continue
        for query in normalize(name):
            if query not in queries:
                queries.append(query)
    return queries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validation",
        action="store_true",
        help="Snapshot only the 30-item validation set instead of all ingredients.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=50,
        help="USDA results per query (1-50). Defaults to the maximum: at 10, "
             "branded products crowd out curated records entirely for common "
             "terms like quinoa and paprika.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the queries that would be sent, without calling the API.",
    )
    args = parser.parse_args()

    source, column = (
        (VALIDATION_CSV, "raw_name") if args.validation
        else (INGREDIENTS_CSV, "ingredient_name")
    )
    if not source.exists():
        print(f"Missing input file: {source}", file=sys.stderr)
        return 1

    names = read_names(source, column)
    queries = collect_queries(names)
    print(f"{len(names)} ingredients -> {len(queries)} unique queries")

    if args.dry_run:
        for query in queries:
            print(f"  {query}")
        return 0

    # Resolve the key from the environment or .env before any request, so a
    # misconfigured setup fails immediately with instructions.
    try:
        key = get_api_key()
    except MissingAPIKeyError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Using API key {mask(key)}")

    try:
        results = asyncio.run(search_queries(queries, page_size=args.page_size))
    except ValueError as error:
        print(f"{error}", file=sys.stderr)
        return 1

    # Merge into any existing snapshot so a validation run does not discard an
    # earlier full-ingredient capture.
    existing: dict[str, list[dict]] = {}
    if OUTPUT_JSON.exists():
        existing = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    existing.update(results)
    OUTPUT_JSON.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    empty = [query for query, rows in results.items() if not rows]
    print(f"Wrote {len(existing)} queries to {OUTPUT_JSON}")
    if empty:
        # A query returning nothing usually means the synonym table needs a new
        # entry — these are the highest-value edits for improving F1.
        print(f"\n{len(empty)} queries returned no results (synonym candidates):")
        for query in empty:
            print(f"  - {query}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
