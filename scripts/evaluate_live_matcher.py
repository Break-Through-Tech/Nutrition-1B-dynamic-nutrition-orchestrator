"""Evaluate the existing ingredient matcher against fresh USDA search results.

Writes a reproducible candidate snapshot and a Markdown report beneath
``evaluation_results/``. API failures are recorded and never replaced with
saved candidates. Rows that depend on a failed query are excluded from metrics.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.config import MissingAPIKeyError, get_api_key  # noqa: E402
from nutrition_engine.ingredient_matcher import ACCEPT_THRESHOLD, Candidate, IngredientMatcher, is_composite, normalize  # noqa: E402
from nutrition_engine.matcher_eval import classify, load_validation_set  # noqa: E402

VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"


async def fetch_live(queries: list[str], page_size: int) -> tuple[dict, dict]:
    from API_File import USDAClient

    results: dict[str, list[dict]] = {}
    errors: dict[str, str] = {}
    async with USDAClient() as client:
        for query in queries:
            try:
                foods = await client.search_foods(query, page_size=page_size)
            except Exception as exc:
                errors[query] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
                continue
            results[query] = [
                {"fdc_id": food.fdc_id, "description": food.description,
                 "data_type": food.data_type}
                for food in foods
            ]
    return results, errors


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(clean(value) for value in row) + " |" for row in rows],
    ])


def run(args: argparse.Namespace) -> int:
    try:
        get_api_key()
    except MissingAPIKeyError as exc:
        print(f"Live evaluation cannot start: {exc}", file=sys.stderr)
        return 1

    validation = load_validation_set(VALIDATION_CSV)
    raw_queries = list(dict.fromkeys(
        query for row in validation if not is_composite(row.raw_name)
        for query in normalize(row.raw_name)
    ))
    candidates_by_query, errors = asyncio.run(fetch_live(raw_queries, args.page_size))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "evaluation_results" / f"live_nlp_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "source": "live USDA FoodData Central /foods/search",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "page_size": args.page_size,
        "queries": candidates_by_query,
        "errors": errors,
    }
    (out_dir / "candidate_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    def search(query: str) -> list[Candidate]:
        return [Candidate(r["fdc_id"], r["description"], r.get("data_type")) for r in candidates_by_query[query]]

    matcher = IngredientMatcher(search, accept_threshold=ACCEPT_THRESHOLD)
    rows = []
    for row in validation:
        queries = normalize(row.raw_name)
        failed = [query for query in queries if query in errors]
        # Composite rows are deliberately rejected by the unchanged matcher and do not require API data.
        if failed and not is_composite(row.raw_name):
            rows.append((row, None, failed))
        else:
            rows.append((row, matcher.match(row.raw_name), []))

    scored = [(row, result) for row, result, failed in rows if result is not None]
    counts = {label: 0 for label in ("TP", "FP", "TN", "FN")}
    for row, result in scored:
        counts[classify(row, result)] += 1
    tp, fp, tn, fn = (counts[k] for k in ("TP", "FP", "TN", "FN"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    correct_matches = tp
    incorrect = fp
    correct_abstentions = tn
    missed = fn
    assignments = sum(result.matched for _, result in scored)
    assignment_rate = assignments / len(scored) if scored else 0.0

    detail_rows: list[list[object]] = []
    for row, result, failed in rows:
        if failed:
            detail_rows.append([row.raw_name, ", ".join(failed), "No; API failure", "—", "—", row.expected_fdc_id, "Unscored", "No"])
        else:
            assert result is not None
            detail_rows.append([
                row.raw_name, "; ".join(result.queries) or "(not searched: composite)",
                "Yes" if result.queries else "Not needed (composite)",
                result.fdc_id if result.fdc_id is not None else "—",
                result.description or "—", row.expected_fdc_id if row.expected_fdc_id is not None else "None",
                "Yes" if result.matched and row.should_match and result.fdc_id == row.expected_fdc_id else ("No" if result.matched else "Abstained"),
                "Yes" if not result.matched else "No",
            ])
    errors_text = "\n".join(f"- `{query}`: {error}" for query, error in errors.items()) or "None."
    report = [
        "# Live USDA NLP matcher baseline", "",
        f"Captured: {snapshot['captured_at_utc']} (UTC). Validation rows: {len(validation)}. Scored: {len(scored)}. Unscored due to API failures: {len(validation)-len(scored)}.",
        "", "## Metrics (failed rows excluded)", "",
        markdown_table(["Metric", "Value"], [
            ["Accuracy", f"{(tp+tn)/len(scored):.2%}" if scored else "N/A"],
            ["Precision", f"{precision:.2%}"], ["Recall", f"{recall:.2%}"], ["F1", f"{f1:.2%}"],
            ["True positives", tp], ["False positives", fp], ["True negatives", tn], ["False negatives", fn],
            ["Correct matches", correct_matches], ["Incorrect assignments", incorrect],
            ["Correct abstentions", correct_abstentions], ["Missed expected matches", missed],
            ["Assignment rate", f"{assignment_rate:.2%}"],
        ]), "", "## Ingredient results", "",
        markdown_table(["Original ingredient", "USDA API search query/queries", "Live candidates?", "Selected FDC ID", "Selected description", "Expected FDC ID", "Correct?", "Abstained?"], detail_rows),
        "", "## Incorrect matches and abstentions", "",
    ]
    issue_rows = []
    for row, result, failed in rows:
        if failed:
            continue
        assert result is not None
        label = classify(row, result)
        if label in {"FP", "FN", "TN"}:
            issue_rows.append([label, row.raw_name, result.fdc_id or "—", result.description or "—", row.expected_fdc_id if row.expected_fdc_id is not None else "None", result.reason or "—"])
    report.append(markdown_table(["Outcome", "Ingredient", "Selected FDC ID", "Description", "Expected FDC ID", "Matcher reason"], issue_rows) if issue_rows else "None.")
    report.extend(["", "## API failures", "", errors_text, "", f"Candidate snapshot: `{out_dir / 'candidate_snapshot.json'}`", ""])
    (out_dir / "evaluation_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {out_dir / 'evaluation_report.md'}")
    print(f"Wrote {out_dir / 'candidate_snapshot.json'}")
    print(f"Scored {len(scored)}/{len(validation)} rows; {len(errors)} API queries failed.")
    return 0 if not errors else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--output-dir", help="New output directory; must not already exist.")
    args = parser.parse_args()
    if not 1 <= args.page_size <= 50:
        parser.error("--page-size must be between 1 and 50")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
