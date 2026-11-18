"""Offline tests for SR Legacy first matching and unchanged NLP fallback."""
import asyncio

import pytest

from nutrition_engine.ingredient_matcher import Candidate
from nutrition_engine.hybrid_ingredient_matcher import HybridIngredientMatcher


def run(coro):
    return asyncio.run(coro)


def test_suitable_sr_legacy_candidate_is_accepted_without_fallback():
    fallback_calls = []

    async def sr_search(query):
        return [Candidate(10, "Quinoa, uncooked", "SR Legacy")]

    async def nlp_search(query):
        fallback_calls.append(query)
        return []

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match("quinoa"))

    assert result.accepted
    assert result.stage == "sr_legacy"
    assert result.fdc_id == 10
    assert result.description == "Quinoa, uncooked"
    assert result.data_type == "SR Legacy"
    assert result.sr_legacy_status == "matched"
    assert result.nlp_status == "not_attempted"
    assert not fallback_calls


def test_sr_candidates_that_are_unsuitable_fall_back_to_nlp():
    async def sr_search(query):
        return [Candidate(11, "Beef liver, cooked", "SR Legacy")]

    async def nlp_search(query):
        return [Candidate(12, "Quinoa, uncooked", "Foundation")]

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match("quinoa"))

    assert result.accepted
    assert result.stage == "nlp_fallback"
    assert result.fdc_id == 12
    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.reason == "accepted_nlp_fallback"


def test_highest_scoring_suitable_sr_legacy_candidate_is_selected(monkeypatch):
    scores = {31: 0.86, 32: 0.93}
    monkeypatch.setattr(
        "nutrition_engine.hybrid_ingredient_matcher.score_candidate",
        lambda query, candidate: scores[candidate.fdc_id],
    )

    async def sr_search(query):
        return [
            Candidate(31, "Quinoa, uncooked", "SR Legacy"),
            Candidate(32, "Quinoa, raw", "SR Legacy"),
        ]

    async def nlp_search(query):
        raise AssertionError("NLP fallback should not run")

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match("quinoa"))

    assert result.stage == "sr_legacy"
    assert result.fdc_id == 32


def test_empty_sr_search_falls_back_to_existing_nlp_matcher():
    async def sr_search(query):
        return []

    async def nlp_search(query):
        return [Candidate(13, "Quinoa, uncooked", "Foundation")]

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match("quinoa"))

    assert result.stage == "nlp_fallback"
    assert result.fdc_id == 13
    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.nlp_status == "matched"


def test_multiple_normalized_queries_continue_after_successful_empty_sr_query():
    called = []

    async def sr_search(query):
        called.append(query)
        if query == "black salt":
            return []
        return [Candidate(130, "Kala namak, black salt", "SR Legacy")]

    async def nlp_search(query):
        return []

    result = run(
        HybridIngredientMatcher(sr_search, nlp_search).match(
            "kala namak (black salt)"
        )
    )

    assert called == ["black salt", "kala namak"]
    assert result.stage == "sr_legacy"
    assert result.fdc_id == 130


def test_both_stages_without_suitable_candidates_require_review():
    async def empty(query):
        return []

    result = run(HybridIngredientMatcher(empty, empty).match("quinoa"))

    assert not result.accepted
    assert result.review_required
    assert result.candidate is None
    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.nlp_status == "no_suitable_candidate"
    assert result.reason == "nlp_no_suitable_candidate"


def test_sr_api_failure_is_distinct_from_successful_empty_search():
    async def broken(query):
        raise OSError("USDA unavailable")

    async def no_nlp_results(query):
        return []

    result = run(HybridIngredientMatcher(broken, no_nlp_results).match("quinoa"))

    assert result.sr_legacy_status == "api_error"
    assert result.sr_legacy_error.startswith("OSError:")
    assert result.nlp_status == "no_suitable_candidate"
    assert result.review_required


def test_sr_api_failure_can_fall_back_to_successful_nlp_match():
    async def broken_sr(query):
        raise OSError("USDA unavailable")

    async def nlp_search(query):
        return [Candidate(33, "Quinoa, uncooked", "Foundation")]

    result = run(HybridIngredientMatcher(broken_sr, nlp_search).match("quinoa"))

    assert result.accepted
    assert result.stage == "nlp_fallback"
    assert result.sr_legacy_status == "api_error"
    assert result.nlp_status == "matched"
    assert result.sr_legacy_error.startswith("OSError:")


def test_nlp_api_failure_is_distinct_from_nlp_no_match():
    async def no_sr_results(query):
        return []

    async def broken(query):
        raise OSError("USDA unavailable")

    result = run(HybridIngredientMatcher(no_sr_results, broken).match("quinoa"))

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.nlp_status == "api_error"
    assert result.nlp_error.startswith("OSError:")
    assert result.nlp_query_errors == (("quinoa", "OSError: USDA unavailable"),)
    assert result.review_required


def test_nlp_earlier_query_failure_is_not_hidden_by_later_success():
    async def no_sr_results(query):
        return []

    async def nlp_search(query):
        if query == "black salt":
            raise OSError("USDA unavailable")
        return [Candidate(17, "Salt, black", "SR Legacy")]

    result = run(
        HybridIngredientMatcher(no_sr_results, nlp_search).match(
            "kala namak (black salt)"
        )
    )

    assert result.nlp_status == "api_error"
    assert result.review_required
    assert result.nlp_query_errors == (("black salt", "OSError: USDA unavailable"),)


def test_nlp_later_query_failure_is_reported_when_earlier_query_matches():
    async def no_sr_results(query):
        return []

    async def nlp_search(query):
        if query == "black salt":
            return [Candidate(18, "Salt, black", "SR Legacy")]
        raise OSError("USDA unavailable")

    result = run(
        HybridIngredientMatcher(no_sr_results, nlp_search).match(
            "kala namak (black salt)"
        )
    )

    assert result.accepted
    assert result.nlp_status == "matched"
    assert result.nlp_query_errors == (("kala namak", "OSError: USDA unavailable"),)


def test_nlp_trace_uses_the_selected_description_for_duplicate_fdc_ids(monkeypatch):
    monkeypatch.setattr(
        "nutrition_engine.ingredient_matcher.score_candidate",
        lambda query, candidate: 0.70 if candidate.description == "Salt, black" else 0.90,
    )

    async def no_sr_results(query):
        return []

    async def nlp_search(query):
        if query == "black salt":
            return [Candidate(19, "Salt, black", "Branded")]
        return [Candidate(19, "Kala namak, black salt", "Foundation")]

    result = run(
        HybridIngredientMatcher(no_sr_results, nlp_search).match(
            "kala namak (black salt)"
        )
    )

    assert result.accepted
    assert result.fdc_id == 19
    assert result.description == "Kala namak, black salt"
    assert result.data_type == "Foundation"


def test_explicit_raw_cooked_mismatch_is_not_accepted(monkeypatch):
    monkeypatch.setattr(
        "nutrition_engine.hybrid_ingredient_matcher.score_candidate",
        lambda query, candidate: 1.0,
    )

    async def sr_search(query):
        return [Candidate(14, "Quinoa, cooked", "SR Legacy")]

    async def no_nlp_results(query):
        return []

    result = run(
        HybridIngredientMatcher(sr_search, no_nlp_results).match("quinoa, raw")
    )

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.nlp_status == "no_suitable_candidate"
    assert result.review_required


@pytest.mark.parametrize(
    "ingredient,description",
    [
        ("quinoa, raw", "Quinoa"),
        ("quinoa, raw", "Quinoa, uncooked"),
        ("quinoa, boiled", "Quinoa, boiled"),
        ("rice, cooked", "Rice"),
    ],
)
def test_missing_or_compatible_preparation_state_is_not_a_mismatch(
    ingredient, description, monkeypatch
):
    monkeypatch.setattr(
        "nutrition_engine.hybrid_ingredient_matcher.score_candidate",
        lambda query, candidate: 1.0,
    )

    async def sr_search(query):
        return [Candidate(15, description, "SR Legacy")]

    async def nlp_search(query):
        return []

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match(ingredient))

    assert result.accepted
    assert result.stage == "sr_legacy"


@pytest.mark.parametrize(
    "ingredient,description",
    [
        ("quinoa, raw", "Quinoa, cooked"),
        ("rice, cooked", "Rice, raw"),
    ],
)
def test_explicitly_contradictory_preparation_states_are_rejected(
    ingredient, description, monkeypatch
):
    monkeypatch.setattr(
        "nutrition_engine.hybrid_ingredient_matcher.score_candidate",
        lambda query, candidate: 1.0,
    )

    async def sr_search(query):
        return [Candidate(16, description, "SR Legacy")]

    async def nlp_search(query):
        return []

    result = run(HybridIngredientMatcher(sr_search, nlp_search).match(ingredient))

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.review_required


def test_unrequested_cooked_candidate_is_rejected():
    async def sr_search(query):
        return [Candidate(160, "Quinoa, cooked", "SR Legacy")]

    async def no_nlp_results(query):
        return []

    result = run(HybridIngredientMatcher(sr_search, no_nlp_results).match("quinoa"))

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.review_required


def test_requested_modifier_must_be_supported_by_sr_description():
    async def sr_search(query):
        return [Candidate(161, "Cheese, paneer", "SR Legacy")]

    async def no_nlp_results(query):
        return []

    result = run(
        HybridIngredientMatcher(sr_search, no_nlp_results).match("low-fat paneer")
    )

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.review_required


def test_supported_low_fat_modifier_can_be_accepted():
    async def sr_search(query):
        return [Candidate(162, "Cheese, paneer, low-fat", "SR Legacy")]

    async def no_nlp_results(query):
        return []

    result = run(
        HybridIngredientMatcher(sr_search, no_nlp_results).match("low-fat paneer")
    )

    assert result.accepted
    assert result.stage == "sr_legacy"


def test_composite_is_sent_to_review_without_searching():
    calls = []

    async def unexpected_search(query):
        calls.append(query)
        return []

    result = run(
        HybridIngredientMatcher(unexpected_search, unexpected_search).match(
            "quinoa-rice blend"
        )
    )

    assert result.review_required
    assert result.reason == "composite_requires_review"
    assert result.sr_legacy_status == "not_attempted"
    assert result.nlp_status == "not_attempted"
    assert not calls


def test_data_type_filter_is_passed_to_usda_search_client():
    from API_File import USDAClient

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"foods": [{"fdcId": 20, "description": "Quinoa", "dataType": "SR Legacy"}]}

    class FakeHTTPClient:
        def __init__(self):
            self.kwargs = None

        async def post(self, *args, **kwargs):
            self.kwargs = kwargs
            return Response()

    async def call():
        client = USDAClient(api_key="test-only")
        fake_http = FakeHTTPClient()
        client._client = fake_http
        foods = await client.search_foods(" quinoa ", data_types=["SR Legacy"])
        return fake_http.kwargs, foods

    kwargs, foods = run(call())

    assert kwargs["json"] == {
        "query": "quinoa", "pageSize": 10, "dataType": ["SR Legacy"]
    }
    assert foods[0].data_type == "SR Legacy"


def test_branded_candidate_cannot_be_accepted_in_sr_legacy_stage(monkeypatch):
    monkeypatch.setattr(
        "nutrition_engine.hybrid_ingredient_matcher.score_candidate",
        lambda query, candidate: 1.0,
    )

    async def sr_search(query):
        return [Candidate(21, "QUINOA", "Branded")]

    async def no_nlp_results(query):
        return []

    result = run(HybridIngredientMatcher(sr_search, no_nlp_results).match("quinoa"))

    assert result.sr_legacy_status == "no_suitable_candidate"
    assert result.review_required


def test_existing_nlp_fallback_can_still_accept_branded_candidates():
    async def no_sr_results(query):
        return []

    async def branded_fallback(query):
        return [Candidate(22, "QUINOA", "Branded")]

    result = run(
        HybridIngredientMatcher(no_sr_results, branded_fallback).match("quinoa")
    )

    assert result.accepted
    assert result.stage == "nlp_fallback"
    assert result.data_type == "Branded"


def test_empty_data_type_filter_is_rejected():
    from API_File import USDAClient

    async def call():
        client = USDAClient(api_key="test-only")
        await client.search_foods("quinoa", data_types=[])

    with pytest.raises(ValueError, match="data_types"):
        run(call())
