"""Entity-resolution scoring for the ingredient matcher (Task 6).

Success criterion 2 asks for F1 > 90% on a 30-ingredient validation set. That
requires a definition of what counts as a hit, because "matched something" and
"matched the right thing" are different questions:

    TP  asserted a match, and the FDC ID is the expected one
    FP  asserted a match that is wrong, OR asserted one where none was correct
        (a composite like "quinoa-rice blend" has no single correct record)
    FN  asserted no match where a correct record exists
    TN  correctly declined to match a composite

Matching a real ingredient to the *wrong* FDC ID counts as a false positive,
not a miss. That is the failure mode that actually damages this project: a
wrong ID silently feeds wrong macros into the deterministic engine, and the
arithmetic will be flawlessly correct about a number that was never right.

`benchmarks.calculate_f1_score` (Task 5) is used as a cross-check on the
simpler "did it match at all" framing, so both tasks report the same way.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .benchmarks import calculate_f1_score
from .ingredient_matcher import IngredientMatcher, MatchResult


@dataclass(frozen=True)
class ValidationRow:
    raw_name: str
    tier: str
    should_match: bool
    expected_fdc_id: int | None
    notes: str = ""

    @property
    def is_labeled(self) -> bool:
        """A positive row is only scorable once a ground-truth ID is recorded."""
        return (not self.should_match) or (self.expected_fdc_id is not None)


@dataclass(frozen=True)
class Outcome:
    row: ValidationRow
    result: MatchResult
    label: str  # "TP" | "FP" | "FN" | "TN"


def load_validation_set(path: str | Path) -> list[ValidationRow]:
    rows: list[ValidationRow] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            raw_id = (record.get("expected_fdc_id") or "").strip()
            rows.append(
                ValidationRow(
                    raw_name=record["raw_name"],
                    tier=record.get("tier", ""),
                    should_match=record["should_match"].strip().lower() == "yes",
                    expected_fdc_id=int(raw_id) if raw_id else None,
                    notes=record.get("notes", ""),
                )
            )
    return rows


def classify(row: ValidationRow, result: MatchResult) -> str:
    if result.matched:
        if row.should_match and result.fdc_id == row.expected_fdc_id:
            return "TP"
        # Either the wrong record, or a match on something unmatchable.
        return "FP"
    return "FN" if row.should_match else "TN"


def evaluate(matcher: IngredientMatcher, rows: list[ValidationRow]) -> dict:
    """Score the matcher and return a report suitable for the eval write-up."""
    unlabeled = [row.raw_name for row in rows if not row.is_labeled]

    outcomes = [
        Outcome(row, result, classify(row, result))
        for row, result in ((row, matcher.match(row.raw_name)) for row in rows)
    ]

    # All four labels are always present so the report shape stays stable
    # for anything consuming it (docs, CI, the Streamlit UI later).
    counts: dict[str, int] = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for outcome in outcomes:
        counts[outcome.label] += 1

    true_positive = counts["TP"]
    false_positive = counts["FP"]
    false_negative = counts["FN"]

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    # Cross-check against Task 5's helper on the coarser "did it match at all"
    # framing, so the two tasks agree on how a score is computed.
    coarse_f1 = calculate_f1_score(
        [outcome.result.matched for outcome in outcomes],
        [outcome.row.should_match for outcome in outcomes],
    )

    per_tier: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for outcome in outcomes:
        per_tier[outcome.row.tier][outcome.label] += 1
        per_tier[outcome.row.tier]["total"] += 1

    return {
        "total": len(rows),
        "unlabeled": unlabeled,
        "counts": counts,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "f1_match_only": coarse_f1,
        "meets_target": f1 > 0.90,
        "per_tier": {tier: dict(stats) for tier, stats in per_tier.items()},
        "outcomes": outcomes,
    }


def format_report(report: dict) -> str:
    """Render the report as plain text for a terminal or a docs paste."""
    lines: list[str] = []

    if report["unlabeled"]:
        lines.append(
            f"WARNING: {len(report['unlabeled'])} positive rows have no "
            f"expected_fdc_id yet. Scores below are not final."
        )
        for name in report["unlabeled"]:
            lines.append(f"  unlabeled: {name}")
        lines.append("")

    counts = report["counts"]
    lines.append(f"Validation rows : {report['total']}")
    lines.append(
        "TP {TP}  FP {FP}  FN {FN}  TN {TN}".format(
            TP=counts.get("TP", 0),
            FP=counts.get("FP", 0),
            FN=counts.get("FN", 0),
            TN=counts.get("TN", 0),
        )
    )
    lines.append(f"Precision       : {report['precision']:.2%}")
    lines.append(f"Recall          : {report['recall']:.2%}")
    lines.append(f"F1              : {report['f1']:.2%}")
    lines.append(f"Target (>90%)   : {'MET' if report['meets_target'] else 'NOT MET'}")
    lines.append("")
    lines.append("By tier:")
    for tier, stats in sorted(report["per_tier"].items()):
        detail = " ".join(
            f"{label}={stats.get(label, 0)}" for label in ("TP", "FP", "FN", "TN")
        )
        lines.append(f"  {tier:<11} n={stats['total']:<3} {detail}")

    misses = [o for o in report["outcomes"] if o.label in ("FP", "FN")]
    if misses:
        lines.append("")
        lines.append("Failures to review:")
        for outcome in misses:
            got = outcome.result.description or "(no match)"
            lines.append(
                f"  [{outcome.label}] {outcome.row.raw_name}"
                f"\n        expected fdc_id={outcome.row.expected_fdc_id}"
                f"\n        got      fdc_id={outcome.result.fdc_id} {got!r}"
                f" score={outcome.result.score}"
            )

    return "\n".join(lines)


__all__ = [
    "Outcome",
    "ValidationRow",
    "classify",
    "evaluate",
    "format_report",
    "load_validation_set",
]
