"""Offline behavior tests for the local semantic ingredient index."""
from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("chromadb")

from nutrition_engine.semantic_ingredient_search import (
    CONTEXTUAL_COLLECTION_NAME,
    SemanticIngredientSearch,
    _ChunkedSentenceTransformerEmbeddingFunction,
)


class StableTestEmbedding:
    """Tiny deterministic embedding so tests never download model weights."""

    def __init__(self):
        self.calls = 0
        self.inputs = []

    def __call__(self, input: list[str]) -> list[list[float]]:
        self.calls += len(input)
        self.inputs.extend(input)
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


class MockTokenizer:
    def num_special_tokens_to_add(self, pair: bool = False) -> int:
        return 2

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        return [int(token[1:]) for token in text.split() if token]

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        return " ".join(f"t{token_id}" for token_id in token_ids)


class MockEmbeddingArray:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.vectors = vectors

    def tolist(self) -> list[list[float]]:
        return self.vectors


class MockSentenceTransformer:
    def __init__(self) -> None:
        self.tokenizer = MockTokenizer()
        self.max_seq_length = 6  # Four document tokens after two special tokens.
        self.encoded_batches: list[list[str]] = []

    def encode(self, texts: list[str], *, convert_to_numpy: bool, show_progress_bar: bool):
        assert convert_to_numpy is True
        assert show_progress_bar is False
        self.encoded_batches.append(texts)
        vectors = []
        for text in texts:
            token_ids = self.tokenizer.encode(text, add_special_tokens=False)
            vectors.append([float(sum(token_ids)), float(len(token_ids))])
        return MockEmbeddingArray(vectors)


def make_search(path):
    return SemanticIngredientSearch(
        path,
        model_name="test/stable",
        embedding_function=StableTestEmbedding(),
    )


def make_contextual_search(path):
    return SemanticIngredientSearch(
        path,
        model_name="test/stable",
        embedding_function=StableTestEmbedding(),
        collection_name=CONTEXTUAL_COLLECTION_NAME,
    )


def make_chunked_embedding(monkeypatch):
    import sentence_transformers

    model = MockSentenceTransformer()
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", lambda _name: model)
    return _ChunkedSentenceTransformerEmbeddingFunction("test/mock"), model


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


def test_contextual_document_contains_source_recipe_context(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    recipe = {
        "recipe_id": "moong-cheela", "name": "Moong Dal Cheela", "cuisine": "Indian",
        "meal_type": "breakfast", "diet_tags": ["vegetarian"],
        "ingredients": [
            {"name": "moong dal, soaked overnight", "quantity": 60, "unit": "g", "notes": "drained"},
            {"name": "low-fat paneer", "quantity": 75, "unit": "g"},
        ],
        "instructions": ["Drain and blend the soaked moong dal.", "Cook the cheela on a tawa."],
    }
    search.sync_contextual_from_recipes([recipe])
    row = search._collection.get(include=["documents", "metadatas"])
    doc = row["documents"][0]
    metadata = row["metadatas"][0]
    assert "Ingredient: moong dal, soaked overnight" in doc
    assert "Recipe: Moong Dal Cheela" in doc
    assert "Cuisine: Indian" in doc and "Meal type: breakfast" in doc
    assert "Other ingredients: low-fat paneer" in doc
    assert "Ingredient notes: drained" in doc
    assert "Drain and blend the soaked moong dal." in doc
    assert metadata["recipe_id"] == "moong-cheela"
    assert metadata["recipe_name"] == "Moong Dal Cheela"
    assert metadata["ingredient_name"] == "moong dal, soaked overnight"
    assert metadata["quantity"] == 60 and metadata["unit"] == "g"
    assert metadata["occurrence_id"] == "moong-cheela:0"


def test_same_ingredient_in_different_recipes_has_distinct_occurrences(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    recipes = [
        {"recipe_id": "r1", "name": "Rajma Bowl", "ingredients": [{"name": "onion"}]},
        {"recipe_id": "r2", "name": "Paneer Curry", "ingredients": [{"name": "onion"}]},
    ]
    result = search.sync_contextual_from_recipes(recipes)
    assert result == {"indexed": 2, "embedded": 2, "metadata_updated": 0, "removed": 0, "total": 2}
    stored = search._collection.get(include=["documents", "metadatas"])
    assert len(set(stored["ids"])) == 2
    assert {m["recipe_id"] for m in stored["metadatas"]} == {"r1", "r2"}
    assert all("Ingredient: onion" in d for d in stored["documents"])


def test_contextual_ids_are_deterministic_and_sync_is_idempotent(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    recipes = [{"recipe_id": "r1", "name": "One", "ingredients": [{"name": "rice"}, {"name": "rice"}]}]
    first = search.sync_contextual_from_recipes(recipes)
    first_ids = sorted(search._collection.get()["ids"])
    assert first["total"] == 2
    second = search.sync_contextual_from_recipes(recipes)
    second_ids = sorted(search._collection.get()["ids"])
    assert first_ids == second_ids
    assert second == {"indexed": 2, "embedded": 0, "metadata_updated": 0, "removed": 0, "total": 2}


def test_contextual_sync_updates_documents_metadata_and_removes_stale_rows(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    first = [{
        "recipe_id": "r1", "name": "Paneer Bowl", "ingredients": [
            {"name": "paneer", "quantity": 50, "unit": "g"}, {"name": "rice"}
        ], "instructions": ["Cook rice."],
    }]
    search.sync_contextual_from_recipes(first)
    changed_metadata = [{
        "recipe_id": "r1", "name": "Paneer Bowl", "ingredients": [
            {"name": "paneer", "quantity": 100, "unit": "g"}, {"name": "rice"}
        ], "instructions": ["Cook rice."],
    }]
    assert search.sync_contextual_from_recipes(changed_metadata) == {
        "indexed": 2, "embedded": 0, "metadata_updated": 1, "removed": 0, "total": 2
    }
    changed_document = [{
        "recipe_id": "r1", "name": "Paneer Bowl", "ingredients": [
            {"name": "paneer", "quantity": 100, "unit": "g"}, {"name": "rice"}
        ], "instructions": ["Simmer paneer and rice."],
    }]
    assert search.sync_contextual_from_recipes(changed_document) == {
        "indexed": 2, "embedded": 2, "metadata_updated": 0, "removed": 0, "total": 2
    }
    stored = search._collection.get(include=["documents", "metadatas"])
    assert all("Simmer paneer and rice." in doc for doc in stored["documents"])
    paneer_meta = next(m for m in stored["metadatas"] if m["ingredient_name"] == "paneer")
    assert paneer_meta["quantity"] == 100
    assert search.sync_contextual_from_recipes([
        {"recipe_id": "r1", "name": "Paneer Bowl", "ingredients": [{"name": "paneer"}]}
    ]) == {"indexed": 1, "embedded": 1, "metadata_updated": 0, "removed": 1, "total": 1}


def test_contextual_search_returns_occurrence_provenance_and_accepts_context(tmp_path):
    embedding = StableTestEmbedding()
    search = SemanticIngredientSearch(
        tmp_path / "index", model_name="test/stable", embedding_function=embedding,
        collection_name=CONTEXTUAL_COLLECTION_NAME,
    )
    search.sync_contextual_from_recipes([
        {"recipe_id": "r1", "name": "Rajma Masala", "cuisine": "Indian", "ingredients": [{"name": "rajma"}]},
        {"recipe_id": "r2", "name": "Rajma Salad", "cuisine": "Indian", "ingredients": [{"name": "rajma"}]},
    ])
    ingredient_only = search.search_contextual("rajma", top_k=2)
    assert len(ingredient_only) == 2
    assert {candidate.original_name for candidate in ingredient_only} == {"rajma"}
    assert {candidate.recipe_name for candidate in ingredient_only} == {"Rajma Masala", "Rajma Salad"}
    assert all(candidate.recipe_id in {"r1", "r2"} for candidate in ingredient_only)
    contextual = search.search_contextual("rajma", top_k=1, recipe_context="Rajma Masala")
    assert contextual[0].similarity == 1.0 - contextual[0].distance
    assert embedding.inputs[-1] == "Ingredient: rajma\nRecipe context: Rajma Masala"


def test_contextual_search_empty_and_invalid_inputs(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    assert search.search_contextual("paneer") == []
    with pytest.raises(ValueError):
        search.search_contextual(" ")
    with pytest.raises(ValueError):
        search.search_contextual("paneer", top_k=0)
    with pytest.raises(ValueError):
        search.search_contextual("paneer", recipe_context=12)


def test_contextual_sync_handles_missing_optional_recipe_metadata(tmp_path):
    search = make_contextual_search(tmp_path / "index")
    search.sync_contextual_from_recipes([
        {"recipe_id": "r1", "name": "Plain Recipe", "ingredients": [{"name": "rice"}]}
    ])
    candidate = search.search_contextual("rice", top_k=1)[0]
    assert candidate.cuisine is None
    assert candidate.meal_type is None
    assert candidate.quantity is None
    assert candidate.other_ingredients == ()


def test_contextual_collection_does_not_replace_ingredient_only_baseline(tmp_path):
    path = tmp_path / "shared-index"
    legacy = make_search(path)
    contextual = make_contextual_search(path)
    recipe = [{"recipe_id": "r1", "name": "Rajma Bowl", "ingredients": [{"name": "rajma"}]}]
    legacy.sync_from_recipes(recipe)
    contextual.sync_contextual_from_recipes(recipe)
    assert legacy.count == 1
    assert contextual.count == 1
    assert legacy.search("rajma", top_k=1)[0].recipe_names == ("Rajma Bowl",)
    assert contextual.search_contextual("rajma", top_k=1)[0].recipe_name == "Rajma Bowl"


def test_chunked_embedding_splits_and_embeds_every_chunk(monkeypatch):
    embedding, model = make_chunked_embedding(monkeypatch)

    result = embedding(["t1 t2 t3 t4 t5"])

    assert model.encoded_batches == [["t1 t2 t3 t4", "t5"]]
    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0] == [7.5, 2.5]


def test_chunked_embedding_handles_empty_and_short_documents(monkeypatch):
    embedding, model = make_chunked_embedding(monkeypatch)

    result = embedding(["", "t7 t8"])

    assert model.encoded_batches == [[""], ["t7 t8"]]
    assert result == [[0.0, 0.0], [15.0, 2.0]]
