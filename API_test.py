# This is a simple example for testing the USDA client.
# It is separate from API_File.py so the API code can be reused by ourselves.

# 1. Before running this file, install the libraries in your terminal:
#     pip install httpx pydantic
#
# 2. Set your personal USDA key in the terminal, not in this file:
#     export USDA_API_KEY="your_actual_api_key_here"
#   !Replace the placeholder with your real key. Do not commit the key to Git please!
# If you dont have a key, you can get one at https://fdc.nal.usda.gov/api-key-signup#top


# asyncio runs Python functions that use `async` and `await`.
# Import the USDA client that does the actual API request.
import asyncio
from API_File import USDAClient


async def main() -> None:
    async with USDAClient() as client: # `async with` opens the HTTP connection and closes it automatically afterward.
        foods = await client.search_foods("paneer", page_size=5) # Ask USDA for up to five foods matching the search phrase.

        # Show how many matching foods USDA returned.
        print(f"Number of foods found: {len(foods)}")

        for food in foods: # Process each validated USDAFood object one at a time.
            # Store the nested nutrient object in a shorter variable for readability.
            nutrients = food.nutrients_per_100g

            # Print the food identity and nutrient values per 100 grams.
            print(f"\nFood: {food.description}")
            print(f"FDC ID: {food.fdc_id}")
            print(f"Calories per 100g: {nutrients.calories}")
            print(f"Protein per 100g: {nutrients.protein_g}g")
            print(f"Carbs per 100g: {nutrients.carbs_g}g")
            print(f"Fat per 100g: {nutrients.fat_g}g")


if __name__ == "__main__":
    # Start the example only when this file is run directly.
    asyncio.run(main())