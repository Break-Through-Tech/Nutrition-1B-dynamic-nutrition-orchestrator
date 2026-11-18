"""Local semantic search over recipe ingredient names and occurrences.

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
CONTEXTUAL_COLLECTION_NAME = "recipe_ingredient_occurrences"


def normalize_ingredient_name(name: str) -> str:
    """Return a separate search normalization; never alter the source name."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Ingredient name must be a non-empty string.")
    return " ".join(re.sub(r"[^\w\-/ ]+", " ", name.casefold()).split())


def _ingredient_id(original_name: str) -> str:
    # Hash exact UTF-8 source text so distinct original spellings remain distinct.
    return hashlib.sha256(original_name.encode("utf-8")).hexdigest()


def _occurrence_id(recipe_id: str, ingredient_index: int) -> str:
    """Return a stable ID for one ingredient slot in a source recipe."""
    key = f"{recipe_id}\0{ingredient_index}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def _contextual_document(
    recipe: dict[str, Any], ingredient: dict[str, Any], other_names: list[str]
) -> str:
    """Render only source-provided recipe and ingredient context."""
    sections = [f"Ingredient: {ingredient['name']}", f"Recipe: {recipe['name']}"]
    for key, label in (("cuisine", "Cuisine"), ("meal_type", "Meal type")):
        value = recipe.get(key)
        if isinstance(value, str) and value.strip():
            sections.append(f"{label}: {value.strip()}")
    tags = recipe.get("diet_tags")
    if isinstance(tags, list):
        tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        if tags:
            sections.append(f"Diet tags: {', '.join(tags)}")
    if other_names:
        sections.append(f"Other ingredients: {', '.join(other_names)}")
    notes = ingredient.get("notes")
    if isinstance(notes, str) and notes.strip():
        sections.append(f"Ingredient notes: {notes.strip()}")
    instructions = recipe.get("instructions")
    if isinstance(instructions, list) and instructions:
        sections.append("Recipe instructions: " + " ".join(instructions))
    return "\n".join(sections)


def _chroma_metadata_value(value: Any) -> str | int | float | bool:
    """Convert structured optional values to Chroma-compatible metadata."""
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_model_embedding_function(model_name: str) -> Any:
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError as exc:  # pragma: no cover - depends on installed extras
        raise RuntimeError(
            "Semantic search dependencies are missing. Install requirements.txt."
        ) from exc
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


class _ChunkedSentenceTransformerEmbeddingFunction:
    """Embed all document text by mean-pooling model-length chunks.

    The contextual documents contain full recipe instructions. The existing
    MiniLM model accepts at most 256 tokens per pass, so this wrapper keeps a
    single Chroma vector per occurrence while allowing every text chunk to
    contribute to that vector.
    """

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - dependency is supplied with Chroma extras
            raise RuntimeError("Sentence Transformers is required for semantic search.") from exc
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.tokenizer = self.model.tokenizer
        special_tokens = self.tokenizer.num_special_tokens_to_add(pair=False)
        self.chunk_size = int(self.model.max_seq_length) - int(special_tokens)
        if self.chunk_size < 1:
            raise ValueError("Embedding model has no room for document tokens after special tokens.")

    def _chunks(self, text: str) -> list[str]:
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        if not token_ids:
            return [text]
        return [
            self.tokenizer.decode(token_ids[i:i + self.chunk_size], skip_special_tokens=True)
            for i in range(0, len(token_ids), self.chunk_size)
        ]

    def __call__(self, input: list[str]) -> list[list[float]]:
        output = []
        for document in input:
            chunks = self._chunks(document)
            embeddings = self.model.encode(
                chunks, convert_to_numpy=True, show_progress_bar=False
            )
            vectors = embeddings.tolist()
            output.append([
                sum(float(vector[i]) for vector in vectors) / len(vectors)
                for i in range(len(vectors[0]))
            ])
        return output

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def name(self) -> str:
        return "sentence-transformer-mean-pooled-chunks"

    def get_config(self) -> dict[str, str]:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: dict[str, str]) -> "_ChunkedSentenceTransformerEmbeddingFunction":
        return _ChunkedSentenceTransformerEmbeddingFunction(config["model_name"])


@dataclass(frozen=True)
class IngredientCandidate:
    ingredient_id: str
    original_name: str
    normalized_name: str
    recipe_ids: tuple[str, ...]
    recipe_names: tuple[str, ...]
    distance: float
    similarity: float


@dataclass(frozen=True)
class ContextualIngredientCandidate:
    """One retrieved ingredient occurrence with its recipe provenance."""

    occurrence_id: str
    recipe_id: str
    recipe_name: str
    original_name: str
    normalized_name: str
    cuisine: str | None
    meal_type: str | None
    quantity: int | float | None
    unit: str | None
    quantity_text: str | None
    notes: str | None
    recipe_notes: str | None
    source_doc: str | None
    servings: int | None
    fdc_id: str | None
    other_ingredients: tuple[str, ...]
    diet_tags: tuple[str, ...]
    distance: float
    similarity: float


class SemanticIngredientSearch:
    """Query legacy ingredient names or per-recipe ingredient occurrences."""

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
        self._embedding_function = embedding_function or (
            _ChunkedSentenceTransformerEmbeddingFunction(model_name)
            if collection_name == CONTEXTUAL_COLLECTION_NAME
            else _load_model_embedding_function(model_name)
        )
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": model_name,
                "embedding_strategy": (
                    "mean_pool_chunks_v1" if collection_name == CONTEXTUAL_COLLECTION_NAME
                    else "sentence_transformer_default"
                ),
            },
        )
        stored_model = (self._collection.metadata or {}).get("embedding_model")
        if stored_model and stored_model != model_name:
            raise ValueError(
                f"Index uses embedding model {stored_model!r}, but {model_name!r} was requested. "
                "Build a separate index or clear/rebuild this index before switching models."
            )
        expected_strategy = (
            "mean_pool_chunks_v1" if collection_name == CONTEXTUAL_COLLECTION_NAME
            else "sentence_transformer_default"
        )
        stored_strategy = (self._collection.metadata or {}).get("embedding_strategy")
        if collection_name == CONTEXTUAL_COLLECTION_NAME and stored_strategy != expected_strategy:
            raise ValueError(
                f"Index uses embedding strategy {stored_strategy!r}, but {expected_strategy!r} was requested. "
                "Build a separate index or clear/rebuild this collection before changing strategies."
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

    def sync_contextual_from_recipes(self, recipes: list[dict[str, Any]]) -> dict[str, int]:
        """Upsert one contextual vector per recipe ingredient occurrence.

        Occurrence IDs are stable for a recipe's ingredient position, so
        repeated syncs update records in place and remove stale recipe slots.
        This method is intended for a separate contextual Chroma collection.
        """
        if not isinstance(recipes, list):
            raise ValueError("recipes must be a list of recipe objects.")
        records: dict[str, tuple[str, dict[str, Any]]] = {}
        seen_recipe_ids: set[str] = set()
        for recipe in recipes:
            if not isinstance(recipe, dict):
                raise ValueError("Each recipe must be an object.")
            recipe_id = recipe.get("recipe_id")
            recipe_name = recipe.get("name")
            ingredients = recipe.get("ingredients")
            if not isinstance(recipe_id, str) or not recipe_id.strip():
                raise ValueError("Each recipe must have a non-empty recipe_id.")
            if recipe_id in seen_recipe_ids:
                raise ValueError(f"Duplicate recipe_id {recipe_id!r} would collide in the contextual index.")
            seen_recipe_ids.add(recipe_id)
            if not isinstance(recipe_name, str) or not recipe_name.strip():
                raise ValueError(f"Recipe {recipe_id!r} must have a non-empty name.")
            if not isinstance(ingredients, list):
                raise ValueError(f"Recipe {recipe_id!r} must have an ingredients list.")
            normalized_names = []
            for ingredient in ingredients:
                if not isinstance(ingredient, dict):
                    raise ValueError(f"Recipe {recipe_id!r} contains an invalid ingredient.")
                normalized_names.append(normalize_ingredient_name(ingredient.get("name")))
            instructions = recipe.get("instructions", [])
            if not isinstance(instructions, list) or any(not isinstance(x, str) for x in instructions):
                raise ValueError(f"Recipe {recipe_id!r} instructions must be a list of strings.")
            diet_tags = recipe.get("diet_tags", [])
            if not isinstance(diet_tags, list):
                raise ValueError(f"Recipe {recipe_id!r} diet_tags must be a list.")

            for index, ingredient in enumerate(ingredients):
                original = ingredient["name"]
                identifier = _occurrence_id(recipe_id, index)
                other_names = [item["name"] for i, item in enumerate(ingredients) if i != index]
                document = _contextual_document(recipe, ingredient, other_names)
                metadata: dict[str, Any] = {
                    "occurrence_id": f"{recipe_id}:{index}",
                    "recipe_id": recipe_id,
                    "recipe_name": recipe_name,
                    "ingredient_index": index,
                    "ingredient_name": original,
                    "normalized_name": normalized_names[index],
                    "other_ingredients": json.dumps(other_names, ensure_ascii=False),
                    "diet_tags": json.dumps(diet_tags, ensure_ascii=False),
                }
                for key in ("cuisine", "meal_type", "source_doc"):
                    value = recipe.get(key)
                    if value is not None:
                        metadata[key] = _chroma_metadata_value(value)
                for key in ("unit", "quantity_text", "notes"):
                    value = ingredient.get(key)
                    if value is not None:
                        metadata[key] = _chroma_metadata_value(value)
                recipe_notes = recipe.get("notes")
                if recipe_notes is not None:
                    metadata["recipe_notes"] = _chroma_metadata_value(recipe_notes)
                quantity = ingredient.get("quantity")
                if isinstance(quantity, (int, float)) and not isinstance(quantity, bool):
                    metadata["quantity"] = quantity
                fdc_id = ingredient.get("fdc_id")
                if isinstance(fdc_id, (int, str)) and str(fdc_id).strip():
                    metadata["fdc_id"] = str(fdc_id)
                servings = recipe.get("servings")
                if isinstance(servings, int) and not isinstance(servings, bool):
                    metadata["servings"] = servings
                records[identifier] = (document, metadata)

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
        for identifier, (document, metadata) in sorted(records.items()):
            if identifier not in old_ids or old_documents.get(identifier) != document:
                additions.append((identifier, document, metadata))
            elif old_metadatas.get(identifier) != metadata:
                metadata_updates.append((identifier, metadata))
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

    def search_contextual(
        self,
        ingredient_name: str,
        top_k: int = 5,
        *,
        recipe_context: str | None = None,
    ) -> list[ContextualIngredientCandidate]:
        """Search occurrence records with an optional recipe-context phrase."""
        query = normalize_ingredient_name(ingredient_name)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        if recipe_context is not None and not isinstance(recipe_context, str):
            raise ValueError("recipe_context must be a string when provided.")
        query_text = f"Ingredient: {query}"
        if recipe_context and recipe_context.strip():
            query_text += f"\nRecipe context: {recipe_context.strip()}"
        if self.count == 0:
            return []
        result = self._collection.query(
            query_texts=[query_text],
            n_results=min(top_k, self.count),
            include=["metadatas", "distances"],
        )
        candidates = []
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for identifier, metadata, distance in zip(ids, metadatas, distances):
            value = float(distance)
            candidates.append(ContextualIngredientCandidate(
                occurrence_id=metadata["occurrence_id"],
                recipe_id=metadata["recipe_id"],
                recipe_name=metadata["recipe_name"],
                original_name=metadata["ingredient_name"],
                normalized_name=metadata["normalized_name"],
                cuisine=metadata.get("cuisine"),
                meal_type=metadata.get("meal_type"),
                quantity=metadata.get("quantity"),
                unit=metadata.get("unit"),
                quantity_text=metadata.get("quantity_text"),
                notes=metadata.get("notes"),
                recipe_notes=metadata.get("recipe_notes"),
                source_doc=metadata.get("source_doc"),
                servings=metadata.get("servings"),
                fdc_id=metadata.get("fdc_id"),
                other_ingredients=tuple(json.loads(metadata.get("other_ingredients", "[]"))),
                diet_tags=tuple(json.loads(metadata.get("diet_tags", "[]"))),
                distance=value,
                similarity=max(0.0, min(1.0, 1.0 - value)),
            ))
        return candidates


__all__ = [
    "COLLECTION_NAME",
    "CONTEXTUAL_COLLECTION_NAME",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_MODEL",
    "ContextualIngredientCandidate",
    "IngredientCandidate",
    "SemanticIngredientSearch",
    "normalize_ingredient_name",
]
