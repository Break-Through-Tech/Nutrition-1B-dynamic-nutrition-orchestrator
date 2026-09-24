"""Tests for Task 6 evaluation scoring.

The F1 number is only trustworthy if the thing computing it is itself tested,
so these cover the TP/FP/FN/TN rules directly rather than only end to end.
"""
from pathlib import Path

import pytest

from nutrition_engine.ingredient_matcher import Candidate, IngredientMatcher
from nutrition_engine.matcher_eval import (
    ValidationRow,
    classify,
    evaluate,
    format_report,
    load_validation_set,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_CSV = REPO_ROOT / "data" / "validation_set.csv"


FAKE_INDEX = {
    "asafoetida": [Candidate(4, "Spices, asafoetida", "sr_legacy_food")],
    "kidney beans": [Candidate(6, "Beans, kidney, red, mature seeds, raw", "sr_legacy_food")],
    "mung beans": [Candidate(5, "Mung beans, mature seeds, raw", "sr_legacy_food")],
}


def fake_search(query):
    return FAKE_INDEX.get(query, [])


def row(name, should_match=True, expected_id=None, tier="synonym"):
    return ValidationRow(
        raw_name=name, tier=tier, should_match=should_match, expected_fdc_id=expected_id
    )


# --- Classification rules --------------------------------------------------

def test_correct_id_is_a_true_positive():
    matcher = IngredientMatcher(fake_search)
    assert classify(row("hing", expected_id=4), matcher.match("hing")) == "TP"


def test_wrong_id_is_a_false_positive_not_a_miss():
    # The core rule: a confidently wrong FDC ID is worse than no answer,
    # because it feeds a plausible-but-wrong macro into the engine.
    matcher = IngredientMatcher(fake_search)
    assert classify(row("hing", expected_id=999), matcher.match("hing")) == "FP"


def test_matching_a_composite_is_a_false_positive():
    matcher = IngredientMatcher(fake_search, allow_composite=True)
    result = matcher.match("rajma")  # stands in for an unmatchable entry
    assert classify(row("rajma", should_match=False), result) == "FP"


def test_declining_a_composite_is_a_true_negative():
    matcher = IngredientMatcher(fake_search)
    result = matcher.match("quinoa-rice blend")
    assert classify(row("quinoa-rice blend", should_match=False), result) == "TN"


def test_missing_a_real_ingredient_is_a_false_negative():
    matcher = IngredientMatcher(fake_search)
    assert classify(row("dragonfruit", expected_id=1), matcher.match("dragonfruit")) == "FN"


# --- Aggregate scoring -----------------------------------------------------

def test_perfect_run_scores_one():
    rows = [
        row("hing", expected_id=4),
        row("rajma", expected_id=6),
        row("quinoa-rice blend", should_match=False, tier="composite"),
    ]
    report = evaluate(IngredientMatcher(fake_search), rows)
    assert report["f1"] == 1.0
    assert report["meets_target"]
    assert report["counts"] == {"TP": 2, "FP": 0, "FN": 0, "TN": 1}


def test_wrong_label_drags_precision_down():
    rows = [row("hing", expected_id=999), row("rajma", expected_id=6)]
    report = evaluate(IngredientMatcher(fake_search), rows)
    assert report["precision"] == 0.5
    assert not report["meets_target"]


def test_per_tier_breakdown_is_reported():
    rows = [
        row("hing", expected_id=4, tier="synonym"),
        row("quinoa-rice blend", should_match=False, tier="composite"),
    ]
    report = evaluate(IngredientMatcher(fake_search), rows)
    assert report["per_tier"]["synonym"]["TP"] == 1
    assert report["per_tier"]["composite"]["TN"] == 1


def test_unlabeled_positive_rows_are_flagged_loudly():
    rows = [row("hing", expected_id=None)]
    report = evaluate(IngredientMatcher(fake_search), rows)
    assert report["unlabeled"] == ["hing"]
    assert "not final" in format_report(report)


def test_negative_rows_need_no_label():
    assert row("quinoa-rice blend", should_match=False).is_labeled


# --- The real validation file ----------------------------------------------

def test_validation_set_has_thirty_rows():
    assert len(load_validation_set(VALIDATION_CSV)) == 30


def test_validation_set_contains_both_classes():
    rows = load_validation_set(VALIDATION_CSV)
    # F1 is only meaningful with true negatives present; without them the
    # metric collapses into plain accuracy.
    assert any(r.should_match for r in rows)
    assert any(not r.should_match for r in rows)


@pytest.mark.parametrize("tier", ["direct", "synonym", "prep_note", "modifier", "composite"])
def test_every_difficulty_tier_is_represented(tier):
    rows = load_validation_set(VALIDATION_CSV)
    assert any(r.tier == tier for r in rows), f"no rows for tier {tier}"
