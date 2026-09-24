"""Tests for Task 6 ingredient matching.

Every test runs offline against a fake search backend. The matcher must be
verifiable without an API key so the suite stays green for teammates and in CI.
"""
import pytest

from nutrition_engine.ingredient_matcher import (
    Candidate,
    IngredientMatcher,
    apply_synonyms,
    confidence_band,
    is_composite,
    normalize,
    score_candidate,
    strip_prep_terms,
)


# --- Fake backend ----------------------------------------------------------

FAKE_INDEX: dict[str, list[Candidate]] = {
    "paneer cheese": [
        Candidate(1, "Cheese, paneer", "sr_legacy_food"),
        Candidate(2, "Amul Paneer Fresh Cheese Block, 200g", "branded_food"),
    ],
    "tofu": [
        Candidate(3, "Tofu, raw, firm, prepared with calcium sulfate", "sr_legacy_food"),
    ],
    "extra-firm tofu": [
        Candidate(3, "Tofu, raw, firm, prepared with calcium sulfate", "sr_legacy_food"),
    ],
    "asafoetida": [
        Candidate(4, "Spices, asafoetida", "sr_legacy_food"),
    ],
    "mung beans": [
        Candidate(5, "Mung beans, mature seeds, raw", "sr_legacy_food"),
    ],
    "kidney beans": [
        Candidate(6, "Beans, kidney, red, mature seeds, raw", "sr_legacy_food"),
    ],
    "black salt": [
        Candidate(7, "Salt, black", "sr_legacy_food"),
    ],
}


def fake_search(query: str):
    return FAKE_INDEX.get(query, [])


def build_matcher(**kwargs) -> IngredientMatcher:
    return IngredientMatcher(fake_search, **kwargs)


# --- Normalization ---------------------------------------------------------

def test_prep_state_after_comma_is_dropped():
    # "crumbled" describes preparation, not identity; USDA indexes the food.
    assert normalize("low-fat paneer, crumbled")[0].startswith("low-fat paneer")


def test_parenthetical_is_tried_first():
    # USDA indexes "black salt", not "kala namak".
    assert normalize("kala namak (black salt)")[0] == "black salt"


def test_bare_form_is_offered_as_fallback():
    queries = normalize("low-fat paneer, crumbled")
    assert "paneer cheese" in queries


def test_synonyms_map_indian_terms_to_usda_english():
    assert apply_synonyms("hing") == "asafoetida"
    assert apply_synonyms("rajma") == "kidney beans"
    assert apply_synonyms("atta") == "whole wheat flour"


def test_longest_synonym_wins():
    # "split moong dal" must not be mangled by the shorter "moong dal" key.
    assert apply_synonyms("split moong dal") == "mung beans split"


def test_strip_prep_terms_keeps_identity_words():
    assert strip_prep_terms("kala chana soaked overnight and boiled") == "kala chana and"


def test_empty_name_is_rejected():
    with pytest.raises(ValueError):
        normalize("   ")


# --- Composite detection ---------------------------------------------------

@pytest.mark.parametrize(
    "name",
    [
        "kadhai spice mix (crushed coriander seeds / dry red chili)",
        "quinoa-rice blend",
        "onion-tomato gravy base",
        "mint-cilantro-yogurt chutney",
        "broccoli and bell peppers, mixed",
        "yellow moong/toor dal",
    ],
)
def test_composite_entries_are_detected(name):
    assert is_composite(name)


@pytest.mark.parametrize("name", ["garam masala", "chaat masala", "low-fat paneer", "rajma"])
def test_single_foods_are_not_composite(name):
    assert not is_composite(name)


def test_composite_returns_no_fdc_id_with_reason():
    result = build_matcher().match("quinoa-rice blend")
    assert result.fdc_id is None
    assert result.reason == "composite"
    assert not result.matched


# --- Scoring ---------------------------------------------------------------

def test_curated_record_outranks_branded_duplicate():
    curated = score_candidate("paneer cheese", FAKE_INDEX["paneer cheese"][0])
    branded = score_candidate("paneer cheese", FAKE_INDEX["paneer cheese"][1])
    assert curated > branded


def test_unrelated_food_scores_far_below_threshold():
    # Character similarity alone gives a small non-zero score (shared letters),
    # so the guarantee that matters is that it lands nowhere near acceptance.
    assert score_candidate("paneer", Candidate(99, "Frankfurter, beef")) < 0.2


def test_score_stays_within_bounds():
    for query, candidates in FAKE_INDEX.items():
        for candidate in candidates:
            assert 0.0 <= score_candidate(query, candidate) <= 1.0


def test_confidence_bands():
    assert confidence_band(0.9) == "high"
    assert confidence_band(0.6) == "medium"
    assert confidence_band(0.1) == "low"
    assert confidence_band(0.0) == "none"


# --- End-to-end matching ---------------------------------------------------

@pytest.mark.parametrize(
    "raw_name, expected_fdc_id",
    [
        ("low-fat paneer, crumbled", 1),
        ("extra-firm tofu, cubed", 3),
        ("hing", 4),
        ("moong dal, soaked overnight", 5),
        ("rajma, soaked overnight", 6),
        ("kala namak (black salt)", 7),
    ],
)
def test_real_recipe_strings_resolve(raw_name, expected_fdc_id):
    result = build_matcher().match(raw_name)
    assert result.fdc_id == expected_fdc_id, result.to_dict()


def test_unknown_ingredient_reports_no_candidates():
    result = build_matcher().match("dragonfruit powder")
    assert result.fdc_id is None
    assert result.reason == "no_candidates"


def test_weak_match_is_rejected_rather_than_guessed():
    # A high threshold must turn a mediocre hit into an explicit non-answer,
    # never a wrong FDC ID — a bad ID silently corrupts every macro downstream.
    # "tofu" scores ~0.81 against its USDA record: a good match in practice,
    # but below a deliberately strict threshold.
    result = IngredientMatcher(fake_search, accept_threshold=0.99).match("tofu")
    assert result.fdc_id is None
    assert result.reason == "below_threshold"
    assert result.considered  # the near-misses stay visible for review


def test_results_are_cached_so_repeats_cost_no_lookups():
    calls: list[str] = []

    def counting_search(query: str):
        calls.append(query)
        return fake_search(query)

    matcher = IngredientMatcher(counting_search)
    matcher.match("low-fat paneer, crumbled")
    before = len(calls)
    matcher.match("Low-Fat Paneer, Crumbled")  # same food, different casing
    assert len(calls) == before


def test_match_all_returns_one_result_per_input():
    names = ["hing", "rajma", "quinoa-rice blend"]
    results = build_matcher().match_all(names)
    assert [r.raw_name for r in results] == names
    assert sum(r.matched for r in results) == 2
