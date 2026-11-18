"""Evaluate the SR Legacy first hybrid matcher on the 30-row validation set.

Track A uses live SR Legacy and live unfiltered NLP searches. Track B reuses
the same live SR Legacy responses and reads every NLP fallback candidate only
from the original live NLP baseline snapshot.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.config import MissingAPIKeyError, get_api_key  # noqa: E402
from nutrition_engine.hybrid_ingredient_matcher import (  # noqa: E402
    HybridIngredientMatcher,
    HybridMatchResult,
)
from nutrition_engine.ingredient_matcher import (  # noqa: E402
    Candidate,
    IngredientMatcher,
    MatchResult,
    is_composite,
    normalize,
)
from nutrition_engine.matcher_eval import (  # noqa: E402
    classify,
    evaluate,
    load_validation_set,
)

VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"
BASELINE_DIR = REPO_ROOT / "evaluation_results" / "live_nlp_20261115T213543Z"
BASELINE_SNAPSHOT = BASELINE_DIR / "candidate_snapshot.json"
BASELINE_REPORT = BASELINE_DIR / "evaluation_report.md"


def _label(row: Any, result: HybridMatchResult) -> str:
    """Apply the existing exact-ID TP/FP/FN/TN classifier to a hybrid result."""
    match_result = MatchResult(
        raw_name=row.raw_name,
        queries=result.queries,
        fdc_id=result.fdc_id,
        description=result.description,
        score=0.0,
        confidence="none",
        reason=result.reason if result.fdc_id is None else None,
    )
    return classify(row, match_result)


def _redact(text: str, secret: str) -> str:
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return re.sub(r"([?&]api_key=)[^&\s]+", r"\1[REDACTED]", text)


def _safe_json(payload: Any, secret: str) -> str:
    return _redact(json.dumps(payload, indent=2), secret)


def _candidate_rows(foods: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "fdc_id": food.fdc_id,
            "description": food.description,
            "data_type": getattr(food, "data_type", None),
        }
        for food in foods
    ]


def _to_candidates(rows: Sequence[dict[str, Any]]) -> list[Candidate]:
    return [
        Candidate(row["fdc_id"], row["description"], row.get("data_type"))
        for row in rows
    ]


class RecordingUSDAClient:
    """Deduplicate identical live requests and retain their candidate payloads."""

    def __init__(self, client: Any, secret: str, page_size: int = 50) -> None:
        self.client = client
        self.secret = secret
        self.page_size = page_size
        self.cache: dict[tuple[str, str], list[Any] | Exception] = {}
        self.responses: dict[str, dict[str, list[dict[str, Any]]]] = {
            "sr_legacy": {}, "nlp_live": {},
        }
        self.errors: dict[str, dict[str, str]] = {"sr_legacy": {}, "nlp_live": {}}

    def _safe_error(self, error: BaseException) -> str:
        value = f"{type(error).__name__}: {str(error).splitlines()[0]}"
        if self.secret:
            value = value.replace(self.secret, "[REDACTED]")
        value = re.sub(r"([?&]api_key=)[^&\s]+", r"\1[REDACTED]", value)
        return value

    async def search_foods(
        self,
        query: str,
        page_size: int = 50,
        data_types: Sequence[str] | None = None,
    ) -> list[Any]:
        mode = "sr_legacy" if data_types is not None else "nlp_live"
        normalized_query = " ".join(query.split())
        cache_key = (mode, normalized_query)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if isinstance(cached, Exception):
                raise cached
            return cached

        try:
            foods = await self.client.search_foods(
                normalized_query,
                page_size=page_size or self.page_size,
                data_types=data_types,
            )
        except Exception as error:
            self.errors[mode][normalized_query] = self._safe_error(error)
            self.cache[cache_key] = error
            raise

        self.responses[mode][normalized_query] = _candidate_rows(foods)
        self.cache[cache_key] = foods
        return foods

    def snapshot(self, captured_at: str) -> dict[str, Any]:
        return {
            "source": "live USDA FoodData Central /foods/search",
            "captured_at_utc": captured_at,
            "page_size": self.page_size,
            "tracks": {
                "sr_legacy": {
                    "data_types": ["SR Legacy"],
                    "queries": self.responses["sr_legacy"],
                    "errors": self.errors["sr_legacy"],
                },
                "nlp_live": {
                    "data_types": None,
                    "queries": self.responses["nlp_live"],
                    "errors": self.errors["nlp_live"],
                },
            },
        }


class MissingSnapshotQueryError(KeyError):
    pass


def _metrics(rows: list[Any], results: list[HybridMatchResult]) -> dict[str, Any]:
    eligible: list[tuple[Any, HybridMatchResult]] = []
    failed_rows: list[str] = []
    for row, result in zip(rows, results):
        if result.sr_legacy_status == "api_error" or result.nlp_status == "api_error":
            failed_rows.append(row.raw_name)
        else:
            eligible.append((row, result))

    counts = {label: 0 for label in ("TP", "FP", "TN", "FN")}
    for row, result in eligible:
        counts[_label(row, result)] += 1
    tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    assigned = sum(result.accepted for _, result in eligible)
    return {
        "total_rows": len(rows),
        "evaluated_rows": len(eligible),
        "unscored_api_failure_rows": failed_rows,
        "counts": counts,
        "accuracy": (tp + tn) / len(eligible) if eligible else None,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "assignment_rate": assigned / len(eligible) if eligible else None,
        "sr_legacy_matches": sum(result.stage == "sr_legacy" for result in results),
        "nlp_fallback_matches": sum(result.stage == "nlp_fallback" for result in results),
        "abstentions": sum(
            result.review_required
            and result.sr_legacy_status != "api_error"
            and result.nlp_status != "api_error"
            for result in results
        ),
    }


def _error_rows(result: HybridMatchResult) -> list[str]:
    errors = []
    if result.sr_legacy_error:
        errors.append(f"SR Legacy: {result.sr_legacy_error}")
    if result.nlp_error:
        errors.append(f"NLP fallback: {result.nlp_error}")
    errors.extend(f"NLP query {query}: {error}" for query, error in result.nlp_query_errors)
    return errors


def _serialize_rows(rows: list[Any], results: list[HybridMatchResult]) -> list[dict[str, Any]]:
    serialized = []
    for row, result in zip(rows, results):
        api_failed = result.sr_legacy_status == "api_error" or result.nlp_status == "api_error"
        label = None if api_failed else _label(row, result)
        serialized.append({
            "original_ingredient": row.raw_name,
            "expected_fdc_id": row.expected_fdc_id,
            "selected_fdc_id": result.fdc_id,
            "selected_description": result.description,
            "selected_data_type": result.data_type,
            "matching_stage": result.stage,
            "accepted": result.accepted,
            "review_required": result.review_required,
            "reason": result.reason,
            "sr_legacy_status": result.sr_legacy_status,
            "nlp_fallback_status": result.nlp_status,
            "sr_legacy_error": result.sr_legacy_error,
            "nlp_error": result.nlp_error,
            "nlp_query_errors": [
                {"query": query, "error": error}
                for query, error in result.nlp_query_errors
            ],
            "correct": (label in {"TP", "TN"}) if label is not None else None,
            "evaluation_label": label or "UNSCORED_API_FAILURE",
            "queries": list(result.queries),
        })
    return serialized


def _baseline_rows(rows: list[Any], payload: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    query_rows = payload["queries"]

    def search(query: str) -> list[Candidate]:
        if query not in query_rows:
            raise MissingSnapshotQueryError(query)
        return _to_candidates(query_rows[query])

    baseline = evaluate(IngredientMatcher(search), rows)
    return baseline, [outcome.result for outcome in baseline["outcomes"]]


def _baseline_metrics(report: dict[str, Any]) -> dict[str, Any]:
    counts = report["counts"]
    tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))
    assigned = tp + fp
    return {
        "total_rows": report["total"],
        "evaluated_rows": report["total"],
        "unscored_api_failure_rows": [],
        "counts": counts,
        "accuracy": (tp + tn) / report["total"] if report["total"] else None,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f1": report["f1"],
        "assignment_rate": assigned / report["total"] if report["total"] else None,
        "sr_legacy_matches": 0,
        "nlp_fallback_matches": assigned,
        "abstentions": tn + fn,
    }


def _result_diff(baseline_results: list[Any], hybrid_rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    changed: list[str] = []
    improved: list[str] = []
    for baseline, hybrid in zip(baseline_results, hybrid_rows):
        base_id = baseline.fdc_id
        hybrid_id = hybrid["selected_fdc_id"]
        base_assigned = base_id is not None
        hybrid_assigned = hybrid["accepted"]
        if base_id != hybrid_id or base_assigned != hybrid_assigned:
            changed.append(hybrid["original_ingredient"])
        baseline_correct = (
            base_id is not None and hybrid["expected_fdc_id"] == base_id
            if hybrid["expected_fdc_id"] is not None else base_id is None
        )
        if hybrid["correct"] is True and baseline_correct is False:
            improved.append(hybrid["original_ingredient"])
    return {"changed_from_baseline": changed, "corrected_to_correct": improved}


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(clean(value) for value in row) + " |" for row in rows],
    ])


def _render_report(
    captured_at: str,
    rows: list[Any],
    baseline_rows: list[Any],
    baseline_metrics: dict[str, Any],
    live_results: list[HybridMatchResult],
    controlled_results: list[HybridMatchResult],
    live_metrics: dict[str, Any],
    controlled_metrics: dict[str, Any],
    live_artifact: dict[str, Any],
    controlled_artifact: dict[str, Any],
    baseline_snapshot_hash: str,
    baseline_report_hash: str,
) -> str:
    live_serialized = _serialize_rows(rows, live_results)
    controlled_serialized = _serialize_rows(rows, controlled_results)
    live_diff = _result_diff(baseline_rows, live_serialized)
    control_diff = _result_diff(baseline_rows, controlled_serialized)
    compare_rows = []
    for name, metrics in (
        ("Original live NLP baseline", baseline_metrics),
        ("Fully live hybrid", live_metrics),
        ("Controlled hybrid (live SR + baseline NLP)", controlled_metrics),
    ):
        compare_rows.append([
            name,
            "N/A" if metrics["accuracy"] is None else f"{metrics['accuracy']:.2%}",
            f"{metrics['precision']:.2%}", f"{metrics['recall']:.2%}", f"{metrics['f1']:.2%}",
            "N/A" if metrics["assignment_rate"] is None else f"{metrics['assignment_rate']:.2%}",
            f"{metrics['evaluated_rows']}/{metrics['total_rows']}",
        ])

    def metric_lines(name: str, metrics: dict[str, Any], api_errors: dict[str, dict[str, str]]) -> list[str]:
        query_error_count = sum(len(errors) for errors in api_errors.values())
        counts = metrics["counts"]
        return [
            f"### {name}", "",
            f"Scored {metrics['evaluated_rows']}/{metrics['total_rows']} rows; {len(metrics['unscored_api_failure_rows'])} rows excluded from metrics due to unresolved stage API errors.",
            f"TP={counts['TP']}, FP={counts['FP']}, TN={counts['TN']}, FN={counts['FN']}; {query_error_count} failed live API query/mode request(s).",
            f"SR Legacy matches: {metrics['sr_legacy_matches']}; NLP fallback matches: {metrics['nlp_fallback_matches']}; abstentions/review decisions: {metrics['abstentions']}.", "",
        ]

    sections = [
        "# SR Legacy + NLP Hybrid Evaluation", "",
        f"Captured: {captured_at} (UTC). Validation set: {len(rows)} rows from the unchanged `data/validation_set.csv`.",
        "",
        "## Comparison", "",
        _table(["Evaluation", "Accuracy", "Precision", "Recall", "F1", "Assignment rate", "Examples scored"], compare_rows),
        "",
        "Metrics use the existing exact-FDC-ID TP/FP/FN/TN rules. Rows with an unresolved SR Legacy or required NLP API error are excluded from that track's metric denominator and listed as unscored; they are not treated as ordinary abstentions. A failed NLP query fetched after the matcher had already accepted an earlier query is still listed in the request-error snapshot, but does not invalidate that completed decision.",
        "",
        *metric_lines("Fully live hybrid", live_metrics, live_artifact["tracks_errors"]),
        *metric_lines("Controlled hybrid", controlled_metrics, controlled_artifact["tracks_errors"]),
        "## Stage contribution and comparison", "",
        f"Fully live hybrid NLP fallback accepted {live_metrics['nlp_fallback_matches']} ingredient(s); controlled hybrid accepted {controlled_metrics['nlp_fallback_matches']}.",
        f"Live hybrid changes from baseline: {', '.join(live_diff['changed_from_baseline']) or 'none'}.",
        f"Corrected to a correct prediction vs baseline: {', '.join(live_diff['corrected_to_correct']) or 'none'}.",
        f"Controlled changes from baseline: {', '.join(control_diff['changed_from_baseline']) or 'none'}.",
        f"Controlled corrected to a correct prediction vs baseline: {', '.join(control_diff['corrected_to_correct']) or 'none'}.",
        "A difference between fully live and controlled tracks can reflect changed USDA candidate results. The controlled track holds NLP candidate responses to the baseline snapshot; the live SR responses are shared with Track A.",
        "",
        "## Fully live hybrid ingredient results", "",
        _table(
            ["Ingredient", "Expected", "Selected", "Description", "Type", "Stage", "SR status", "NLP status", "Decision", "Correct"],
            [[r["original_ingredient"], r["expected_fdc_id"], r["selected_fdc_id"] or "—",
              r["selected_description"] or "—", r["selected_data_type"] or "—", r["matching_stage"] or "—",
              r["sr_legacy_status"], r["nlp_fallback_status"], r["reason"],
              "Unscored" if r["correct"] is None else ("Yes" if r["correct"] else "No")]
             for r in live_serialized],
        ),
        "",
        "## Controlled hybrid ingredient results", "",
        _table(
            ["Ingredient", "Expected", "Selected", "Description", "Type", "Stage", "SR status", "NLP status", "Decision", "Correct"],
            [[r["original_ingredient"], r["expected_fdc_id"], r["selected_fdc_id"] or "—",
              r["selected_description"] or "—", r["selected_data_type"] or "—", r["matching_stage"] or "—",
              r["sr_legacy_status"], r["nlp_fallback_status"], r["reason"],
              "Unscored" if r["correct"] is None else ("Yes" if r["correct"] else "No")]
             for r in controlled_serialized],
        ),
        "",
        "## Incorrect assignments", "",
    ]
    incorrect_rows = []
    for track_name, serialized in (("Live", live_serialized), ("Controlled", controlled_serialized)):
        for row in serialized:
            if row["evaluation_label"] == "FP":
                incorrect_rows.append([track_name, row["original_ingredient"], row["expected_fdc_id"], row["selected_fdc_id"], row["selected_description"], row["matching_stage"]])
    sections.append(_table(["Track", "Ingredient", "Expected FDC ID", "Selected FDC ID", "Description", "Stage"], incorrect_rows) if incorrect_rows else "None.")
    sections.extend(["", "## Manual review and API failures", ""])
    review_rows = []
    for track_name, results in (("Live", live_results), ("Controlled", controlled_results)):
        for result in results:
            if result.review_required or _error_rows(result):
                review_rows.append([track_name, result.raw_name, result.reason, result.sr_legacy_status, result.nlp_status, "; ".join(_error_rows(result)) or "—"])
    sections.append(_table(["Track", "Ingredient", "Reason", "SR status", "NLP status", "Errors"], review_rows) if review_rows else "None.")
    sections.extend([
        "",
        f"Baseline snapshot SHA-256: `{baseline_snapshot_hash}`. Baseline report SHA-256: `{baseline_report_hash}`.",
        "The original baseline folder was read only. Candidate responses used by Track A are saved in `live_candidate_snapshot.json`; Track B uses the exact baseline snapshot copied to `baseline_nlp_candidate_snapshot_reference.json` and reuses Track A's captured SR Legacy responses.",
        "",
    ])
    return "\n".join(sections)


async def _run_tracks(rows: list[Any], secret: str, page_size: int, baseline_queries: dict[str, Any]):
    from API_File import USDAClient

    async def snapshot_search(query: str) -> list[Candidate]:
        if query not in baseline_queries:
            raise MissingSnapshotQueryError(
                f"Required normalized query {query!r} is missing from the baseline snapshot."
            )
        return _to_candidates(baseline_queries[query])

    async with USDAClient() as client:
        recording_client = RecordingUSDAClient(client, secret, page_size)
        live_matcher = HybridIngredientMatcher.from_usda_client(
            recording_client, page_size=page_size
        )
        live_results = [await live_matcher.match(row.raw_name) for row in rows]

        # Reuse the exact live SR responses from Track A, but use only snapshot
        # NLP candidates in this matcher. No missing query is filled live.
        controlled_matcher = HybridIngredientMatcher(
            live_matcher.sr_legacy_search,
            snapshot_search,
        )
        controlled_results = [await controlled_matcher.match(row.raw_name) for row in rows]
    return live_results, controlled_results, recording_client


def run(args: argparse.Namespace) -> int:
    try:
        secret = get_api_key()
    except MissingAPIKeyError as exc:
        print(f"Live hybrid evaluation cannot start: {exc}", file=sys.stderr)
        return 1

    if not BASELINE_SNAPSHOT.is_file() or not BASELINE_REPORT.is_file():
        print("Required original baseline snapshot/report is missing.", file=sys.stderr)
        return 1

    baseline_bytes = BASELINE_SNAPSHOT.read_bytes()
    baseline_report_bytes = BASELINE_REPORT.read_bytes()
    baseline_payload = json.loads(baseline_bytes)
    if not isinstance(baseline_payload.get("queries"), dict) or not isinstance(baseline_payload.get("errors"), dict):
        print("Baseline snapshot does not have the inspected queries/errors schema.", file=sys.stderr)
        return 1
    rows = load_validation_set(VALIDATION_CSV)
    if len(rows) != 30:
        print(f"Expected exactly 30 validation rows; found {len(rows)}.", file=sys.stderr)
        return 1

    required_queries = {
        query for row in rows if not is_composite(row.raw_name)
        for query in normalize(row.raw_name)
    }
    snapshot_queries = baseline_payload["queries"]
    snapshot_errors = baseline_payload["errors"]
    missing = sorted(query for query in required_queries if query not in snapshot_queries)
    captured_as_error = sorted(query for query in required_queries if query in snapshot_errors)
    if args.preflight_only:
        print(f"API key loaded: yes (value hidden)")
        print(f"Validation rows: {len(rows)}")
        print(f"Baseline NLP query coverage: {len(required_queries) - len(missing) - len(captured_as_error)}/{len(required_queries)}")
        print(f"Missing baseline queries: {len(missing)}; baseline query errors: {len(captured_as_error)}")
        return 0 if not missing and not captured_as_error else 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "evaluation_results" / f"hybrid_{stamp}"
    if out_dir.exists():
        print(f"Output directory already exists: {out_dir}", file=sys.stderr)
        return 1

    baseline_report, baseline_results = _baseline_rows(rows, baseline_payload)
    baseline_metrics = _baseline_metrics(baseline_report)
    # Fail closed before making requests if any normalized NLP candidate query
    # is absent or was an error in the saved baseline.
    if missing or captured_as_error:
        print("Controlled comparison is not reliable: required baseline NLP queries are unavailable.", file=sys.stderr)
        print(f"Missing queries: {missing}", file=sys.stderr)
        print(f"Captured query errors: {captured_as_error}", file=sys.stderr)
        return 2

    try:
        live_results, controlled_results, recorder = asyncio.run(
            _run_tracks(rows, secret, args.page_size, baseline_payload["queries"])
        )
    except Exception as exc:
        # Keep arbitrary client errors (which can contain request URLs) out of
        # stdout/stderr. Per-query errors are captured by RecordingUSDAClient.
        print(f"Evaluation aborted before artifacts were written ({type(exc).__name__}).", file=sys.stderr)
        return 1

    captured_at = datetime.now(timezone.utc).isoformat()
    live_metrics = _metrics(rows, live_results)
    controlled_metrics = _metrics(rows, controlled_results)
    tracks_errors = {
        "sr_legacy": recorder.errors["sr_legacy"],
        "nlp_live": recorder.errors["nlp_live"],
    }
    live_artifact = {"tracks_errors": tracks_errors}
    controlled_artifact = {"tracks_errors": {"sr_legacy": recorder.errors["sr_legacy"], "nlp_live": {}}}
    live_snapshot = recorder.snapshot(captured_at)
    controlled_rows = _serialize_rows(rows, controlled_results)
    live_rows = _serialize_rows(rows, live_results)
    baseline_snapshot_hash = hashlib.sha256(baseline_bytes).hexdigest()
    baseline_report_hash = hashlib.sha256(baseline_report_bytes).hexdigest()

    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "live_candidate_snapshot.json").write_text(
        json.dumps(live_snapshot, indent=2), encoding="utf-8"
    )
    (out_dir / "baseline_nlp_candidate_snapshot_reference.json").write_bytes(baseline_bytes)
    results_payload = {
        "captured_at_utc": captured_at,
        "validation_csv": str(VALIDATION_CSV.relative_to(REPO_ROOT)),
        "baseline_snapshot": {
            "path": str(BASELINE_SNAPSHOT.relative_to(REPO_ROOT)),
            "sha256": baseline_snapshot_hash,
            "query_coverage": {"required": len(required_queries), "available": len(required_queries) - len(missing) - len(captured_as_error), "missing": missing, "errors": captured_as_error},
        },
        "original_live_nlp_baseline": {"metrics": baseline_metrics},
        "fully_live_hybrid": {
            "metrics": live_metrics,
            "rows": live_rows,
            "api_query_errors": tracks_errors,
        },
        "controlled_hybrid": {
            "metrics": controlled_metrics,
            "rows": controlled_rows,
            "nlp_candidate_source": "original baseline snapshot only",
            "api_query_errors": controlled_artifact["tracks_errors"],
        },
    }
    (out_dir / "hybrid_results.json").write_text(
        _safe_json(results_payload, secret), encoding="utf-8"
    )
    controlled_payload = {
        "metrics": controlled_metrics,
        "rows": controlled_rows,
        "nlp_candidate_source": str(BASELINE_SNAPSHOT.relative_to(REPO_ROOT)),
        "baseline_snapshot_sha256": baseline_snapshot_hash,
        "live_sr_responses_reused_from": "fully_live_hybrid",
        "api_query_errors": controlled_artifact["tracks_errors"],
    }
    (out_dir / "controlled_comparison.json").write_text(
        _safe_json(controlled_payload, secret), encoding="utf-8"
    )
    report = _render_report(
        captured_at, rows, baseline_results, baseline_metrics,
        live_results, controlled_results, live_metrics, controlled_metrics,
        live_artifact, controlled_artifact,
        baseline_snapshot_hash, baseline_report_hash,
    )
    (out_dir / "evaluation_report.md").write_text(_redact(report, secret), encoding="utf-8")
    print(f"Evaluation artifacts: {out_dir}")
    print(f"Live hybrid scored {live_metrics['evaluated_rows']}/30; controlled hybrid scored {controlled_metrics['evaluated_rows']}/30.")
    print(f"Live API query failures: {sum(len(v) for v in tracks_errors.values())}; baseline missing/error queries: 0/0.")
    return 0 if not any(tracks_errors.values()) else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--output-dir", help="New output directory; must not already exist.")
    parser.add_argument("--preflight-only", action="store_true", help="Check key loading and saved-input coverage without making API calls.")
    args = parser.parse_args()
    if not 1 <= args.page_size <= 50:
        parser.error("--page-size must be between 1 and 50")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
