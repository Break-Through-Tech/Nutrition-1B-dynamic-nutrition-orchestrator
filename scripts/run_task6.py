"""One-command pipeline for Task 6: key -> capture -> label -> score.

Runs each stage in order and stops with a clear instruction whenever a stage
needs something from you. Safe to re-run: completed stages are skipped, so
re-running after labeling picks up where it left off.

    python scripts/run_task6.py              # run the pipeline
    python scripts/run_task6.py --refresh    # re-capture from USDA first
    python scripts/run_task6.py --full       # capture all 126, not just the 30
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.config import (  # noqa: E402
    MissingAPIKeyError,
    get_api_key,
    mask,
)

VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"
CANDIDATES_JSON = REPO_ROOT / "data" / "usda_candidates.json"


def run(script: str, *script_args: str) -> int:
    """Run a sibling script in a child process, inheriting stdin/stdout."""
    return subprocess.call([sys.executable, str(SCRIPTS / script), *script_args])


def unlabeled_count() -> int:
    with VALIDATION_CSV.open(encoding="utf-8", newline="") as handle:
        return sum(
            1
            for row in csv.DictReader(handle)
            if row["should_match"].strip().lower() == "yes"
            and not row.get("expected_fdc_id", "").strip()
            and row.get("expected_description", "") != "NO CORRECT USDA RECORD"
        )


def step(number: int, title: str) -> None:
    print(f"\n{'=' * 60}\nStep {number}: {title}\n{'=' * 60}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-capture from USDA.")
    parser.add_argument("--full", action="store_true", help="Capture all 126 ingredients.")
    parser.add_argument("--skip-label", action="store_true", help="Do not open the labeler.")
    args = parser.parse_args()

    # --- 1. Key -----------------------------------------------------------
    step(1, "USDA API key")
    try:
        key = get_api_key()
    except MissingAPIKeyError as error:
        print(error)
        return 1
    if key == "your_key_here":
        print("`.env` still holds the placeholder. Put your real key in it.")
        return 1
    print(f"Key found ({mask(key)}).")

    # --- 2. Capture -------------------------------------------------------
    step(2, "Capture USDA candidates")
    if CANDIDATES_JSON.exists() and not args.refresh:
        print(f"Snapshot already present: {CANDIDATES_JSON}")
        print("Use --refresh to re-capture.")
    else:
        snapshot_args = [] if args.full else ["--validation"]
        if run("snapshot_usda_candidates.py", *snapshot_args) != 0:
            print("\nCapture failed. Try: python scripts/check_api_key.py")
            return 1

    # --- 3. Label ---------------------------------------------------------
    step(3, "Ground-truth labels")
    remaining = unlabeled_count()
    if remaining == 0:
        print("All positive rows are labeled.")
    elif args.skip_label:
        print(f"{remaining} row(s) unlabeled; skipping as requested.")
        print("Scores below will be incomplete.")
    else:
        print(f"{remaining} row(s) need a human-confirmed FDC ID.")
        print("Labeling is interactive and saves after every answer.\n")
        run("label_validation_set.py")

    # --- 4. Score ---------------------------------------------------------
    step(4, "Evaluate")
    exit_code = run("evaluate_matcher.py")

    print(f"\n{'=' * 60}")
    if exit_code == 0:
        print("F1 target met. Task 6 acceptance criterion satisfied.")
        print("Record the score in README.md and close the issue.")
    else:
        print("F1 target not met yet. Next steps:")
        print("  - Read the failure list above; note which tier is failing.")
        print("  - Add missing terms to SYNONYMS in ingredient_matcher.py.")
        print("  - Re-run with --refresh to re-capture the new queries.")
        print("  - Try: python scripts/evaluate_matcher.py --sweep")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
