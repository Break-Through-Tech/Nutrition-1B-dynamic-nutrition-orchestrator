"""Offline behavior tests for the local semantic ingredient index."""
from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("chromadb")

from nutrition_engine.semantic_ingredient_search import SemanticIngredientSearch


class StableTestEmbedding:
    """Tiny deterministic embedding so tests never download model weights."""

    def __init__(self):
        self.calls = 0

    def __call__(self, input: list[str]) -> list[list[float]]:
        self.calls += len(input)
        vectors = []
        for text in input:
            digest = hashlib.sha256(text.encode()).digest()
            vectors.append([byte / 127.5 - 1.0 for byte in digest[:16]])
        return vectors

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def is_legacy(self) -> bool:
        return False

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine"]

    @staticmethod
    def name() -> str:
        return "stable-test-embedding"

    @staticmethod
    def get_config() -> dict:
        return {}

    @staticmethod
    def build_from_config(config: dict) -> "StableTestEmbedding":
        return StableTestEmbedding()


def make_search(path):
    return SemanticIngredientSearch(
        path,
        model_name="test/stable",
        embedding_function=StableTestEmbedding(),
    )


def test_sync_is_idempotent_and_preserves_exact_names(tmp_path):
    recipes = [
        {"recipe_id": "r1", "name": "Recipe One", "ingredients": [{"name": "Atta (whole wheat flour)"}]},
        {"recipe_id": "r2", "name": "Recipe Two", "ingredients": [{"name": "Atta (whole wheat flour)"}]},
    ]
    search = make_search(tmp_path / "index")
    assert search.sync_from_recipes(recipes) == {
        "indexed": 1, "embedded": 1, "metadata_updated": 0, "removed": 0, "total": 1
    }
    embeds_after_first_build = search._embedding_function.calls
    assert search.sync_from_recipes(recipes) == {
        "indexed": 1, "embedded": 0, "metadata_updated": 0, "removed": 0, "total": 1
    }
    assert search._embedding_function.calls == embeds_after_first_build

    result = search.search("Atta", top_k=1)[0]
    assert result.original_name == "Atta (whole wheat flour)"
    assert result.normalized_name == "atta whole wheat flour"
    assert result.recipe_ids == ("r1", "r2")
    assert result.recipe_names == ("Recipe One", "Recipe Two")


def test_index_persists_across_client_instances(tmp_path):
    path = tmp_path / "persistent-index"
    make_search(path).sync_from_recipes([
        {"recipe_id": "r1", "name": "Recipe", "ingredients": [{"name": "rajma"}]}
    ])
    reopened = make_search(path)
    assert reopened.count == 1
    assert reopened.search("kidney beans", top_k=1)[0].original_name == "rajma"


def test_sync_updates_metadata_and_removes_stale_ingredients(tmp_path):
    search = make_search(tmp_path / "index")
    first = [{"recipe_id": "r1", "name": "Old", "ingredients": [{"name": "paneer"}, {"name": "rice"}]}]
    search.sync_from_recipes(first)
    second = [{"recipe_id": "r1", "name": "Updated", "ingredients": [{"name": "paneer"}, {"name": "brown rice"}]},
              {"recipe_id": "r2", "name": "Second", "ingredients": [{"name": "paneer"}]}]
    assert search.sync_from_recipes(second) == {
        "indexed": 2, "embedded": 1, "metadata_updated": 1, "removed": 1, "total": 2
    }
    result = search.search("paneer", top_k=1)[0]
    assert result.recipe_ids == ("r1", "r2")
    assert result.recipe_names == ("Second", "Updated")
    assert search.search("brown rice", top_k=1)[0].original_name == "brown rice"
    assert all(candidate.original_name != "rice" for candidate in search.search("rice", top_k=2))


@pytest.mark.parametrize("name", ["", "   ", None, 12])
def test_empty_or_invalid_query_is_rejected(tmp_path, name):
    with pytest.raises(ValueError):
        make_search(tmp_path / "index").search(name)


@pytest.mark.parametrize("top_k", [0, -1, 1.2, True, "3"])
def test_invalid_top_k_is_rejected(tmp_path, top_k):
    with pytest.raises(ValueError):
        make_search(tmp_path / "index").search("paneer", top_k=top_k)


def test_empty_index_returns_no_candidates(tmp_path):
    assert make_search(tmp_path / "index").search("paneer") == []


def test_invalid_recipe_payload_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="recipe_id"):
        make_search(tmp_path / "index").sync_from_recipes([{"name": "missing ID", "ingredients": []}])
