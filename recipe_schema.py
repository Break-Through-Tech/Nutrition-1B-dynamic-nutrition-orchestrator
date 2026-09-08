"""Schema for the local recipe seed database (Task 2).

Normalized shape recipes are stored in once pulled out of the raw Google
Docs. Ingredient FDC IDs are left optional here — Task 6 (NLP/keyword
matching) is what fills those in.

NOTE: the real recipe docs mix clean "60g Dry Soya Chunks" style amounts
with vague ones ("green chili, to taste", "Lemons & Cucumbers: Bulk
stock"). `quantity`/`unit` are for the former; `quantity_text` holds the
latter verbatim instead of forcing a fake number.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class RecipeIngredient(BaseModel):
    """One ingredient line inside a recipe."""

    name: str  # Raw ingredient name as written (e.g. "paneer, cubed") — Task 6 matches this to an FDC ID
    quantity: Optional[float] = Field(default=None, gt=0)  # Amount, when a clean number is given
    unit: Optional[str] = None  # Unit as written (g, ml, tsp, cup, piece, etc.) — not yet standardized to USDA units
    quantity_text: Optional[str] = None  # Raw amount text when there's no clean number, e.g. "to taste", "bulk stock"
    fdc_id: Optional[int] = None  # USDA FoodData Central ID, filled in later by Task 6's matcher
    notes: Optional[str] = None  # Prep notes, e.g. "diced", "soaked overnight"

    @model_validator(mode="after")
    def _quantity_or_text(self) -> "RecipeIngredient":
        # Every ingredient needs either a parsed amount or the raw text — never neither.
        if self.quantity is None and not self.quantity_text:
            raise ValueError(f"{self.name!r} needs either quantity+unit or quantity_text")
        return self


class Recipe(BaseModel):
    """A single normalized recipe record."""

    recipe_id: str  # Unique slug, e.g. "paneer-tikka-bowl"
    name: str
    cuisine: str = "Indian"
    meal_type: Optional[str] = None  # breakfast / lunch / dinner / snack
    diet_tags: list[str] = Field(default_factory=list)  # e.g. ["vegetarian", "high-protein"]
    servings: int = Field(gt=0)
    ingredients: list[RecipeIngredient]
    instructions: list[str] = Field(default_factory=list)
    source_doc: Optional[str] = None  # Which Google Doc this recipe came from, for traceability
    notes: Optional[str] = None  # e.g. "Adult path — serve with 2 rotis", target macros stated in source


__all__ = ["RecipeIngredient", "Recipe"]
