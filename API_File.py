# This file connects our project to the USDA FoodData Central API.

from __future__ import annotations

# os lets us read the USDA_API_KEY from the computer's environment.
# Decimal stores nutrient numbers accurately. 
# InvalidOperation helps us catch a USDA value that cannot be converted into a number.
# Any describes the general dictionary format returned by the USDA API.
# httpx sends HTTP requests to the USDA website (The async version allows the
# program to wait for the response without blocking other work)
# Pydantic turns API dictionaries into checked Python objects. Field adds rules
# such as "this number cannot be negative."
import os
from decimal import Decimal, InvalidOperation
from typing import Any
import httpx
from pydantic import BaseModel, Field

# This is the base address shared by USDA FoodData Central API requests.
FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"


class NutrientsPer100g(BaseModel):
    """Nutrients for a food, reported by USDA per 100 grams."""

    # These four fields are the values the rest of the project needs.
    # Decimal is used instead of float to reduce rounding surprises.
    calories: Decimal = Field(ge=0)
    protein_g: Decimal = Field(ge=0)
    carbs_g: Decimal = Field(ge=0)
    fat_g: Decimal = Field(ge=0)


class USDAFood(BaseModel):
    """A simplified food record that our project can use."""

    fdc_id: int # fdc_id is USDA's unique ID for this food.
    description: str # description is the food name returned by USDA.
    # USDA's dataType: "Foundation" and "SR Legacy" are lab-analyzed generic
    # foods, "Branded" are commercial products. Ingredient matching needs this
    # to prefer curated records over branded ones. Optional so older callers
    # are unaffected.
    data_type: str | None = None
    nutrients_per_100g: NutrientsPer100g # Nutrient values are kept together in their own validated model.


class USDAClient:
    """Small client responsible for searching USDA foods."""

    def __init__(self, api_key: str | None = None) -> None:
        # Prefer a key passed directly, otherwise read it from the environment.
        # Keeping the key outside the source code prevents accidentally sharing it.
        self.api_key = api_key or os.getenv("USDA_API_KEY")
        if not self.api_key: # Stop early with a clear message if no key was provided.
            raise ValueError("Provide an API key or set USDA_API_KEY") 
        self._client: httpx.AsyncClient | None = None # The HTTP client is created when the async context starts.

    async def __aenter__(self) -> "USDAClient":
        # This makes `async with USDAClient()` open one reusable connection.
        self._client = httpx.AsyncClient(base_url=FDC_BASE_URL, timeout=15.0)
        return self

    async def __aexit__(self, *args) -> None:
        if self._client: # Closing the client releases the network connection when finished.
            await self._client.aclose()
            self._client = None

    async def search_foods(self, query: str, page_size: int = 10) -> list[USDAFood]:
        """Search USDA and return a list of validated food records."""

        # Remove extra spaces so a user's search is sent in a clean form.
        cleaned_query = " ".join(query.split())
        if not cleaned_query: # An empty search would not be useful to the USDA API.
            raise ValueError("query must not be empty")
        if not 1 <= page_size <= 50: # Limit the response size so requests stay reasonable.
            raise ValueError("page_size must be between 1 and 50")

        if self._client is None:
            # The caller must use the client inside `async with` so it is closed safely.
            raise RuntimeError(
                "Use USDAClient as an async context manager: "
                "`async with USDAClient() as client:`"
            )

        # Send the search request. The API key is sent as a query parameter.
        response = await self._client.post(
            "/foods/search",
            params={"api_key": self.api_key},
            # USDA accepts the search text and requested number of results as JSON.
            json={"query": cleaned_query, "pageSize": page_size},
        )
        response.raise_for_status() # Turn HTTP errors, such as an invalid key, into Python exceptions.
        payload = response.json() # Convert the response body from JSON text into Python dictionaries.

        return [ # Build USDAFood objects so Pydantic validates every returned record.
            USDAFood(
                fdc_id=food["fdcId"],
                description=food["description"],
                data_type=food.get("dataType"),
                nutrients_per_100g=_nutrient_amounts(food),
            )
            for food in payload.get("foods", [])
        ]


def _nutrient_amounts(food: dict[str, Any]) -> NutrientsPer100g:
    """Pick the four nutrient values we need from one USDA food dictionary."""

    # Start missing nutrients at zero. USDA can omit a nutrient for some foods.
    values: dict[str, Decimal] = {
        "calories": Decimal("0"),
        "protein_g": Decimal("0"),
        "carbs_g": Decimal("0"),
        "fat_g": Decimal("0"),
    }
    # These are USDA's IDs for energy, protein, carbohydrates, and fat.
    nutrient_ids = {1008: "calories", 1003: "protein_g", 1005: "carbs_g", 1004: "fat_g"}

    # Check each nutrient returned by USDA and keep only the four we use.
    for nutrient in food.get("foodNutrients", []):
        key = nutrient_ids.get(nutrient.get("nutrientId"))
        if key is None: # Ignore nutrients such as sodium because this file does not need them.
            continue
        try: # Convert the API value to Decimal for consistent numeric handling.
            values[key] = Decimal(str(nutrient.get("value", 0)))
        except (InvalidOperation, TypeError): # Do not silently accept malformed nutrient data.
            raise ValueError(f"USDA returned an invalid value for {key}") from None

    # Pydantic checks that all values are valid, non-negative nutrient numbers.
    return NutrientsPer100g(**values)


# This list documents the names other files should import from this module.
__all__ = [
    "NutrientsPer100g",
    "USDAFood",
    "USDAClient",
]
