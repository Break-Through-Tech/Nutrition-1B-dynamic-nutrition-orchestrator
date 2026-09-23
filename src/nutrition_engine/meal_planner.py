"""Restriction-aware recipe planning with a deterministic fallback.

The planner treats recipe selection and nutrient arithmetic as separate concerns.
It never invents nutrient values for recipe ingredients that are absent from the
canonical nutrition catalog.
"""
from __future__ import annotations

import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


RESTRICTION_TERMS: dict[str, tuple[str, ...]] = {
    # These terms are conservative rejection rules; unresolved nutrition data
    # is handled separately by the deterministic macro engine.
    "vegetarian": ("chicken", "beef", "pork", "lamb", "fish", "salmon", "meat"),
    "vegan": (
        "chicken", "beef", "pork", "lamb", "fish", "salmon", "meat", "paneer",
        "yogurt", "curd", "milk", "whey", "cheese", "ghee", "butter", "egg",
    ),
    "dairy free": (
        "paneer", "yogurt", "curd", "milk", "whey", "cheese", "ghee", "butter",
    ),
    "nut free": ("almond", "peanut", "cashew", "walnut", "nut"),
    "gluten free": (
        "wheat", "atta", "bread", "flour", "roti", "paratha", "tortilla",
    ),
}


class PlannerBackend(Protocol):
    def choose_recipe_ids(
        self, request: "MealPlanRequest", candidates: Sequence[dict]
    ) -> list[str]: ...


class InvalidPlannerResponse(ValueError):
    pass


@dataclass(frozen=True)
class MealPlanRequest:
    restrictions: tuple[str, ...] = ()
    meal_type: str | None = None
    servings: int = 1
    max_recipes: int = 3

    def __post_init__(self) -> None:
        if self.servings <= 0:
            raise ValueError("Servings must be greater than zero.")
        if self.max_recipes <= 0:
            raise ValueError("max_recipes must be greater than zero.")


@dataclass(frozen=True)
class MealPlanResult:
    recipes: tuple[dict, ...]
    rejected: tuple[dict[str, str], ...]
    source: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "recipes": list(self.recipes),
            "rejected": list(self.rejected),
            "source": self.source,
            "warnings": list(self.warnings),
        }


class OllamaBackend:
    """Optional local Ollama selector; nutrient math remains deterministic."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        endpoint: str = "http://localhost:11434/api/generate",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def choose_recipe_ids(
        self, request: MealPlanRequest, candidates: Sequence[dict]
    ) -> list[str]:
        candidate_ids = [recipe.get("recipe_id") for recipe in candidates]
        # Send IDs rather than raw recipe text so the model ranks known records
        # and cannot invent a recipe that bypasses restriction filtering.
        prompt = (
            "Choose recipes only from the candidate IDs below. Return JSON only "
            "in the form {\"recipe_ids\":[...]} with no explanation.\n"
            f"Restrictions: {list(request.restrictions)}\n"
            f"Meal type: {request.meal_type}\n"
            f"Candidate IDs: {candidate_ids}"
        )
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request_object = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request_object, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError) as error:
            raise ConnectionError("Ollama is unavailable.") from error

        # Ollama may wrap JSON in a Markdown fence despite the prompt.
        response_text = response_payload.get("response", "").strip()
        response_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text).strip()
        try:
            selected = json.loads(response_text).get("recipe_ids")
        except (AttributeError, TypeError, json.JSONDecodeError) as error:
            raise InvalidPlannerResponse("Ollama did not return valid recipe JSON.") from error
        if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
            raise InvalidPlannerResponse("Ollama recipe_ids must be a list of strings.")
        return selected


def normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def load_recipes(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as recipe_file:
        payload = json.load(recipe_file)
    if not isinstance(payload, list):
        raise ValueError("Recipe database must contain a JSON list.")
    return payload


def _restriction_conflict(recipe: dict, restriction: str) -> str | None:
    normalized_restriction = normalize_text(restriction)
    terms = RESTRICTION_TERMS.get(normalized_restriction)
    if terms is None:
        raise ValueError(f"Unsupported dietary restriction: {restriction}")

    ingredient_text = " ".join(
        normalize_text(ingredient.get("name", ""))
        for ingredient in recipe.get("ingredients", [])
    )
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", ingredient_text):
            return f"contains {term}"
    return None


def recipe_rejection_reason(recipe: dict, request: MealPlanRequest) -> str | None:
    if request.meal_type and normalize_text(recipe.get("meal_type", "")) != normalize_text(request.meal_type):
        return f"meal type is {recipe.get('meal_type', 'unspecified')}"

    for restriction in request.restrictions:
        conflict = _restriction_conflict(recipe, restriction)
        if conflict:
            return f"{restriction}: {conflict}"
    return None


def filter_recipes(recipes: Sequence[dict], request: MealPlanRequest) -> tuple[list[dict], list[dict[str, str]]]:
    accepted: list[dict] = []
    rejected: list[dict[str, str]] = []
    # Preserve rejection reasons so a UI or agent can explain why a recipe was
    # excluded instead of hiding the decision.
    for recipe in recipes:
        reason = recipe_rejection_reason(recipe, request)
        if reason is None:
            accepted.append(recipe)
        else:
            rejected.append({"recipe_id": recipe.get("recipe_id", ""), "reason": reason})
    return accepted, rejected


def deterministic_plan(recipes: Sequence[dict], request: MealPlanRequest) -> MealPlanResult:
    accepted, rejected = filter_recipes(recipes, request)
    selected = tuple(accepted[: request.max_recipes])
    warnings = () if selected else ("No recipes satisfy the requested restrictions.",)
    return MealPlanResult(selected, tuple(rejected), "deterministic", warnings)


class MealPlanningAgent:
    """Use an optional LLM selector while enforcing deterministic guardrails."""

    def __init__(self, recipes: Sequence[dict], backend: PlannerBackend | None = None) -> None:
        self.recipes = tuple(recipes)
        self.backend = backend

    def plan(self, request: MealPlanRequest) -> MealPlanResult:
        accepted, rejected = filter_recipes(self.recipes, request)
        if self.backend is None:
            return deterministic_plan(self.recipes, request)

        try:
            # The backend sees only safe candidates; its response is validated
            # again before any recipe is returned to the caller.
            chosen_ids = self.backend.choose_recipe_ids(request, accepted)
            accepted_by_id = {recipe.get("recipe_id"): recipe for recipe in accepted}
            selected = []
            for recipe_id in chosen_ids:
                recipe = accepted_by_id.get(recipe_id)
                if recipe is None:
                    raise InvalidPlannerResponse(
                        f"Backend selected unknown or restricted recipe: {recipe_id}"
                    )
                if recipe not in selected:
                    selected.append(recipe)
            if not selected:
                raise InvalidPlannerResponse("Backend returned no recipes.")
            return MealPlanResult(
                tuple(selected[: request.max_recipes]), tuple(rejected), "llm",
            )
        except (InvalidPlannerResponse, ConnectionError, TimeoutError, ValueError) as error:
            # Local LLMs are optional. A failed model call must not make meal
            # planning unavailable or weaken the deterministic guardrails.
            fallback = deterministic_plan(self.recipes, request)
            return MealPlanResult(
                fallback.recipes,
                fallback.rejected,
                "deterministic-fallback",
                (f"LLM selection unavailable: {error}",),
            )


__all__ = [
    "InvalidPlannerResponse",
    "MealPlanRequest",
    "MealPlanResult",
    "MealPlanningAgent",
    "OllamaBackend",
    "PlannerBackend",
    "deterministic_plan",
    "filter_recipes",
    "load_recipes",
    "recipe_rejection_reason",
]
