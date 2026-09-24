"""Interactively record ground-truth FDC IDs for the validation set (Task 6).

Scoring needs a human-confirmed correct answer for each positive row. This
walks through the unlabeled rows, shows the USDA candidates the matcher found,
and writes the chosen FDC ID back into `data/validation_set.csv`.

Labeling is a judgement call and stays with a person on purpose: an F1 score
measured against machine-generated ground truth measures nothing.

    python scripts/snapshot_usda_candidates.py --validation   # capture first
    python scripts/label_validation_set.py                    # then label

Progress is saved after every answer, so quitting and resuming is safe.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.ingredient_matcher import normalize  # noqa: E402
from nutrition_engine.usda_search import cached_search_fn  # noqa: E402

VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"
CANDIDATES_JSON = REPO_ROOT / "data" / "usda_candidates.json"

FIELDNAMES = [
    "raw_name", "tier", "should_match",
    "expected_fdc_id", "expected_description", "notes",
]


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict]) -> None:
    """Write atomically so an interrupt cannot leave a truncated CSV."""
    temp = path.with_suffix(".csv.tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
    temp.replace(path)


def gather_candidates(raw_name: str, search_fn) -> list:
    """Collect de-duplicated candidates across all queries for one ingredient."""
    seen: dict[int, object] = {}
    for query in normalize(raw_name):
        for candidate in search_fn(query):
            seen.setdefault(candidate.fdc_id, candidate)
    return list(seen.values())


def prompt_for_choice(row: dict, candidates: list, index: int, total: int) -> tuple[str, str] | None:
    """Show candidates and return (fdc_id, description), or None to skip."""
    print("\n" + "=" * 70)
    print(f"[{index}/{total}]  {row['raw_name']}")
    print(f"  tier: {row['tier']}    queries: {', '.join(normalize(row['raw_name']))}")
    if row.get("notes"):
        print(f"  note: {row['notes']}")
    print("-" * 70)

    if not candidates:
        print("  No candidates captured for this ingredient.")
        print("  Likely a missing synonym. Add one to SYNONYMS, then re-snapshot.")
        return None

    for number, candidate in enumerate(candidates, start=1):
        data_type = f"  [{candidate.data_type}]" if candidate.data_type else ""
        print(f"  {number:>2}. {candidate.description}{data_type}")
        print(f"      fdc_id={candidate.fdc_id}")

    print("\n  Enter a number to accept, 'n' if none are correct,")
    print("  's' to skip for now, or 'q' to save and quit.")

    while True:
        answer = input("  > ").strip().lower()
        if answer == "q":
            raise KeyboardInterrupt
        if answer == "s":
            return None
        if answer == "n":
            # Recorded as an explicit non-answer rather than left blank, so the
            # evaluation can tell "reviewed, nothing fits" from "not yet done".
            return ("", "NO CORRECT USDA RECORD")
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            chosen = candidates[int(answer) - 1]
            return (str(chosen.fdc_id), chosen.description)
        print(f"  Enter 1-{len(candidates)}, or n / s / q.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--relabel",
        action="store_true",
        help="Revisit rows that already have an expected_fdc_id.",
    )
    args = parser.parse_args()

    if not CANDIDATES_JSON.exists():
        print(f"Missing {CANDIDATES_JSON}", file=sys.stderr)
        print("Run: python scripts/snapshot_usda_candidates.py --validation", file=sys.stderr)
        return 1

    rows = read_rows(VALIDATION_CSV)
    search_fn = cached_search_fn(CANDIDATES_JSON)

    # Composite rows are correct with no ID; they need no human review.
    todo = [
        row for row in rows
        if row["should_match"].strip().lower() == "yes"
        and (args.relabel or not row.get("expected_fdc_id", "").strip())
    ]

    if not todo:
        print("All positive rows are labeled. Run: python scripts/evaluate_matcher.py")
        return 0

    print(f"{len(todo)} row(s) to label. Progress saves after each answer.")

    try:
        for position, row in enumerate(todo, start=1):
            candidates = gather_candidates(row["raw_name"], search_fn)
            choice = prompt_for_choice(row, candidates, position, len(todo))
            if choice is None:
                continue
            row["expected_fdc_id"], row["expected_description"] = choice
            write_rows(VALIDATION_CSV, rows)
    except KeyboardInterrupt:
        print("\n\nStopped. Progress saved.")

    remaining = sum(
        1 for row in rows
        if row["should_match"].strip().lower() == "yes"
        and not row.get("expected_fdc_id", "").strip()
        and row.get("expected_description", "") != "NO CORRECT USDA RECORD"
    )
    print(f"\nSaved to {VALIDATION_CSV}")
    if remaining:
        print(f"{remaining} row(s) still unlabeled. Re-run this script to continue.")
    else:
        print("All rows labeled. Run: python scripts/evaluate_matcher.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
