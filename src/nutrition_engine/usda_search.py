"""USDA search backends for the ingredient matcher (Task 6).

Keeps every network concern out of `ingredient_matcher`, which stays pure and
offline-testable. Task 1's `USDAClient` remains the only code that talks to
FoodData Central — this module just adapts its output into `Candidate`s.

Usage:

    from nutrition_engine.usda_search import cached_search_fn
    from nutrition_engine.ingredient_matcher import IngredientMatcher

    matcher = IngredientMatcher(cached_search_fn("data/usda_candidates.json"))
    print(matcher.match("low-fat paneer, crumbled"))
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

from .ingredient_matcher import Candidate

# `API_File.py` lives at the repository root, outside the `src/` package root
# that pytest.ini puts on the path. Adding it here keeps the import working
# without moving Gesell's file mid-sprint.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _to_candidate(food: object) -> Candidate:
    """Adapt one Task 1 `USDAFood` into a matcher `Candidate`.

    `data_type` is read defensively: `USDAFood` does not expose it today, so
    ranking simply loses the curated-record bonus until it does. Adding
    `data_type` to `USDAFood` is a one-line change on the Task 1 side that
    measurably improves ranking against Branded results.
    """
    return Candidate(
        fdc_id=getattr(food, "fdc_id"),
        description=getattr(food, "description"),
        data_type=getattr(food, "data_type", None),
    )


async def search_queries(
    queries: Sequence[str],
    page_size: int = 10,
) -> dict[str, list[dict]]:
    """Run many searches on one connection, returning raw rows per query.

    Used by `scripts/snapshot_usda_candidates.py` to capture candidates once,
    so the F1 evaluation can be replayed offline by anyone on the team without
    an API key and without network variance changing the reported number.
    """
    from API_File import USDAClient  # lazy: tests never need httpx installed

    results: dict[str, list[dict]] = {}
    failures: dict[str, str] = {}
    async with USDAClient() as client:
        for query in queries:
            try:
                foods = await client.search_foods(query, page_size=page_size)
            except Exception as error:
                # A single rejected query must not discard every result
                # captured before it. Record it and keep going.
                failures[query] = f"{type(error).__name__}: {error}"
                results[query] = []
                continue
            results[query] = [
                {
                    "fdc_id": food.fdc_id,
                    "description": food.description,
                    "data_type": getattr(food, "data_type", None),
                    # Macros are captured alongside the identity so the
                    # nutrition catalog can be generated without a second pass.
                    "calories_per_100g": float(food.nutrients_per_100g.calories),
                    "protein_g_per_100g": float(food.nutrients_per_100g.protein_g),
                    "carbs_g_per_100g": float(food.nutrients_per_100g.carbs_g),
                    "fat_g_per_100g": float(food.nutrients_per_100g.fat_g),
                }
                for food in foods
            ]

    if failures:
        print(f"{len(failures)} query/queries failed and were recorded empty:")
        for query, reason in failures.items():
            print(f"  - {query!r}: {reason.splitlines()[0]}")
    return results


class QueryNotCapturedError(KeyError):
    """A query was requested that the snapshot does not contain."""


def cached_search_fn(cache_path: str | Path, strict: bool = True):
    """Build a search function backed by a saved query -> candidates snapshot.

    A snapshot covers only the queries it was built from. Returning an empty
    list for anything else would be indistinguishable from "USDA has no such
    food", which is a very different claim -- one is a gap in our capture, the
    other is a fact about the database. `strict` (the default) raises instead,
    so a coverage gap surfaces immediately rather than silently becoming an
    unmatched ingredient.

    Pass `strict=False` only when an empty result is genuinely acceptable.
    """
    payload = json.loads(Path(cache_path).read_text(encoding="utf-8"))

    def search(query: str) -> Sequence[Candidate]:
        if query not in payload:
            if strict:
                raise QueryNotCapturedError(
                    f"{query!r} is not in {Path(cache_path).name} "
                    f"({len(payload)} queries captured). Re-run "
                    f"scripts/snapshot_usda_candidates.py to include it."
                )
            return []
        return [
            Candidate(
                fdc_id=row["fdc_id"],
                description=row["description"],
                data_type=row.get("data_type"),
            )
            for row in payload[query]
        ]

    return search


def load_macros(cache_path: str | Path) -> dict[int, dict[str, float]]:
    """Read per-100g macros out of a snapshot, keyed by FDC ID.

    This is the bridge to Task 4: once an ingredient resolves to an FDC ID,
    this supplies the four values `IngredientNutrition` needs, sourced from
    USDA rather than typed by hand.
    """
    payload = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    macros: dict[int, dict[str, float]] = {}
    for rows in payload.values():
        for row in rows:
            if "calories_per_100g" not in row:
                continue
            macros[row["fdc_id"]] = {
                "calories_per_100g": row["calories_per_100g"],
                "protein_g_per_100g": row["protein_g_per_100g"],
                "carbs_g_per_100g": row["carbs_g_per_100g"],
                "fat_g_per_100g": row["fat_g_per_100g"],
            }
    return macros


__all__ = [
    "QueryNotCapturedError",
    "cached_search_fn",
    "load_macros",
    "search_queries",
]
