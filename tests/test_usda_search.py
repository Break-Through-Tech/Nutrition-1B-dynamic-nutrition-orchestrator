"""Tests for the snapshot-backed search layer.

The snapshot is what makes the reported F1 reproducible, so its coverage
behaviour needs to be explicit: an uncaptured query and a captured-but-empty
query mean different things and must not look alike.
"""
import json

import pytest

from nutrition_engine.usda_search import (
    QueryNotCapturedError,
    cached_search_fn,
    load_macros,
)

SNAPSHOT = {
    "mung beans": [
        {
            "fdc_id": 174256,
            "description": "Mung beans, mature seeds, raw",
            "data_type": "SR Legacy",
            "calories_per_100g": 347.0,
            "protein_g_per_100g": 23.9,
            "carbs_g_per_100g": 62.6,
            "fat_g_per_100g": 1.15,
        }
    ],
    "asafoetida": [],  # captured, and USDA genuinely returned nothing
}


@pytest.fixture
def snapshot_path(tmp_path):
    path = tmp_path / "snap.json"
    path.write_text(json.dumps(SNAPSHOT), encoding="utf-8")
    return path


def test_captured_query_returns_records(snapshot_path):
    results = cached_search_fn(snapshot_path)("mung beans")
    assert [c.fdc_id for c in results] == [174256]
    assert results[0].data_type == "SR Legacy"


def test_captured_but_empty_query_returns_empty(snapshot_path):
    # USDA was asked and had nothing. That is a real answer, not a gap.
    assert cached_search_fn(snapshot_path)("asafoetida") == []


def test_uncaptured_query_raises_by_default(snapshot_path):
    # Silently returning [] would be indistinguishable from the case above,
    # turning a gap in our capture into a false "USDA has no such food".
    with pytest.raises(QueryNotCapturedError) as error:
        cached_search_fn(snapshot_path)("basmati rice")
    assert "basmati rice" in str(error.value)
    assert "snapshot_usda_candidates" in str(error.value)


def test_lenient_mode_returns_empty_instead(snapshot_path):
    assert cached_search_fn(snapshot_path, strict=False)("basmati rice") == []


def test_macros_are_keyed_by_fdc_id(snapshot_path):
    macros = load_macros(snapshot_path)
    # These are the four fields IngredientNutrition needs, sourced from USDA
    # rather than hand-entered.
    assert macros[174256]["protein_g_per_100g"] == 23.9
    assert set(macros[174256]) == {
        "calories_per_100g",
        "protein_g_per_100g",
        "carbs_g_per_100g",
        "fat_g_per_100g",
    }
