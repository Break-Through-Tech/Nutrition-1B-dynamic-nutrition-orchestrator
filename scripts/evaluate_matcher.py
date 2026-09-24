"""Score the ingredient matcher against the validation set (Task 6).

Runs fully offline against the snapshot written by
`scripts/snapshot_usda_candidates.py`, so the reported F1 is reproducible by
anyone on the team without an API key.

    python scripts/snapshot_usda_candidates.py --validation   # once, needs key
    python scripts/evaluate_matcher.py                        # anytime, offline

`--threshold` sweeps the accept threshold, which is the main tuning knob:
lower accepts more matches (higher recall, more wrong IDs), higher rejects more
(higher precision, more unmatched ingredients).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.ingredient_matcher import ACCEPT_THRESHOLD, IngredientMatcher  # noqa: E402
from nutrition_engine.matcher_eval import evaluate, format_report, load_validation_set  # noqa: E402
from nutrition_engine.usda_search import cached_search_fn  # noqa: E402

VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"
CANDIDATES_JSON = REPO_ROOT / "data" / "usda_candidates.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold",
        type=float,
        default=ACCEPT_THRESHOLD,
        help=f"Accept threshold (default {ACCEPT_THRESHOLD}).",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Report F1 across a range of thresholds instead of one value.",
    )
    args = parser.parse_args()

    if not CANDIDATES_JSON.exists():
        print(f"Missing {CANDIDATES_JSON}", file=sys.stderr)
        print(
            "Run: python scripts/snapshot_usda_candidates.py --validation",
            file=sys.stderr,
        )
        return 1

    rows = load_validation_set(VALIDATION_CSV)
    search_fn = cached_search_fn(CANDIDATES_JSON)

    if args.sweep:
        print(f"{'threshold':>10}  {'precision':>9}  {'recall':>7}  {'F1':>7}")
        for step in range(30, 91, 5):
            threshold = step / 100
            report = evaluate(IngredientMatcher(search_fn, accept_threshold=threshold), rows)
            print(
                f"{threshold:>10.2f}  {report['precision']:>9.2%}"
                f"  {report['recall']:>7.2%}  {report['f1']:>7.2%}"
            )
        return 0

    report = evaluate(IngredientMatcher(search_fn, accept_threshold=args.threshold), rows)
    print(format_report(report))
    return 0 if report["meets_target"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
