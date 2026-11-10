"""Local semantic search over recipe ingredient names.

Search results are ingredient-name candidates only. This module has no USDA
integration and never assigns FoodData Central IDs.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_INDEX_PATH = Path(__file__).resolve().parents[2] / "data" / "ingredient_vector_index"
COLLECTION_NAME = "recipe_ingredients"


def normalize_ingredient_name(name: str) -> str:
    """Return a separate search normalization; never alter the source name."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Ingredient name must be a non-empty string.")
    return " ".join(re.sub(r"[^\w\-/ ]+", " ", name.casefold()).split())


def _ingredient_id(original_name: str) -> str:
    # Hash exact UTF-8 source text so distinct original spellings remain distinct.
    return hashlib.sha256(original_name.encode("utf-8")).hexdigest()


def _load_model_embedding_function(model_name: str) -> Any:
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError as exc:  # pragma: no cover - depends on installed extras
        raise RuntimeError(
            "Semantic search dependencies are missing. Install requirements.txt."
        ) from exc
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


@dataclass(frozen=True)
class IngredientCandidate:
    ingredient_id: str
    original_name: str
    normalized_name: str
    recipe_ids: tuple[str, ...]
    recipe_names: tuple[str, ...]
    distance: float
    similarity: float


class SemanticIngredientSearch:
    """Query the persistent Chroma index of recipe ingredient names."""

    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_INDEX_PATH,
        model_name: str = DEFAULT_MODEL,
        *,
        embedding_function: Any | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:  # pragma: no cover - depends on installed extras
            raise RuntimeError(
                "Semantic search dependencies are missing. Install requirements.txt."
            ) from exc
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string.")
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._embedding_function = embedding_function or _load_model_embedding_function(model_name)
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": model_name},
        )
        stored_model = (self._collection.metadata or {}).get("embedding_model")
        if stored_model and stored_model != model_name:
            raise ValueError(
                f"Index uses embedding model {stored_model!r}, but {model_name!r} was requested. "
                "Build a separate index or clear/rebuild this index before switching models."
            )

    @property
    def count(self) -> int:
        return self._collection.count()

    def sync_from_recipes(self, recipes: list[dict[str, Any]]) -> dict[str, int]:
        """Upsert current unique ingredients and remove records no longer present."""
        if not isinstance(recipes, list):
            raise ValueError("recipes must be a list of recipe objects.")
        records: dict[str, dict[str, Any]] = {}
        for recipe in recipes:
            if not isinstance(recipe, dict):
                raise ValueError("Each recipe must be an object.")
            recipe_id = recipe.get("recipe_id")
            recipe_name = recipe.get("name")
            ingredients = recipe.get("ingredients")
            if not isinstance(recipe_id, str) or not recipe_id.strip():
                raise ValueError("Each recipe must have a non-empty recipe_id.")
            if not isinstance(recipe_name, str) or not recipe_name.strip():
                raise ValueError(f"Recipe {recipe_id!r} must have a non-empty name.")
            if not isinstance(ingredients, list):
                raise ValueError(f"Recipe {recipe_id!r} must have an ingredients list.")
            for ingredient in ingredients:
                if not isinstance(ingredient, dict):
                    raise ValueError(f"Recipe {recipe_id!r} contains an invalid ingredient.")
                original = ingredient.get("name")
                normalized = normalize_ingredient_name(original)
                identifier = _ingredient_id(original)
                record = records.setdefault(identifier, {
                    "id": identifier,
                    "original_name": original,
                    "normalized_name": normalized,
                    "recipe_ids": set(),
                    "recipe_names": set(),
                })
                record["recipe_ids"].add(recipe_id)
                record["recipe_names"].add(recipe_name)

        current = self._collection.get(include=["documents", "metadatas"])
        old_ids = set(current.get("ids", []))
        old_documents = dict(zip(current.get("ids", []), current.get("documents", [])))
        old_metadatas = dict(zip(current.get("ids", []), current.get("metadatas", [])))
        new_ids = set(records)
        removed = old_ids - new_ids
        if removed:
            self._collection.delete(ids=sorted(removed))
        additions: list[tuple[str, str, dict[str, Any]]] = []
        metadata_updates: list[tuple[str, dict[str, Any]]] = []
        if records:
            for identifier, record in sorted(records.items()):
                metadata = {
                    "original_name": record["original_name"],
                    "normalized_name": record["normalized_name"],
                    "recipe_ids": json.dumps(sorted(record["recipe_ids"]), ensure_ascii=False),
                    "recipe_names": json.dumps(sorted(record["recipe_names"]), ensure_ascii=False),
                }
                document = record["original_name"]
                if identifier not in old_ids or old_documents.get(identifier) != document:
                    additions.append((identifier, document, metadata))
                elif old_metadatas.get(identifier) != metadata:
                    metadata_updates.append((identifier, metadata))
        # Only new/changed documents get embeddings. Metadata-only changes use
        # update(), and unchanged records are untouched on repeat builds.
        if additions:
            self._collection.upsert(
                ids=[item[0] for item in additions],
                documents=[item[1] for item in additions],
                metadatas=[item[2] for item in additions],
            )
        if metadata_updates:
            self._collection.update(
                ids=[item[0] for item in metadata_updates],
                metadatas=[item[1] for item in metadata_updates],
            )
        return {
            "indexed": len(records),
            "embedded": len(additions),
            "metadata_updated": len(metadata_updates),
            "removed": len(removed),
            "total": self.count,
        }

    def search(self, ingredient_name: str, top_k: int = 5) -> list[IngredientCandidate]:
        """Return the nearest ingredient-name candidates with cosine distance."""
        query = normalize_ingredient_name(ingredient_name)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        if self.count == 0:
            return []
        result = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self.count),
            include=["metadatas", "distances"],
        )
        candidates: list[IngredientCandidate] = []
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for identifier, metadata, distance in zip(ids, metadatas, distances):
            # Chroma cosine distance is 0..2; expose both raw distance and a
            # bounded convenience similarity. Neither is a confirmation score.
            value = float(distance)
            candidates.append(IngredientCandidate(
                ingredient_id=identifier,
                original_name=metadata["original_name"],
                normalized_name=metadata["normalized_name"],
                recipe_ids=tuple(json.loads(metadata["recipe_ids"])),
                recipe_names=tuple(json.loads(metadata["recipe_names"])),
                distance=value,
                similarity=max(0.0, min(1.0, 1.0 - value)),
            ))
        return candidates


__all__ = [
    "DEFAULT_INDEX_PATH",
    "DEFAULT_MODEL",
    "IngredientCandidate",
    "SemanticIngredientSearch",
    "normalize_ingredient_name",
]
