# API_File.py

This file is responsible for connecting the project to the **USDA FoodData Central API**. Its main purpose is to search for foods and convert the USDA's response into a simple, consistent format the rest of the project can use.

The code follows this general process:

**Food Search → USDA API Request → USDA Response → Nutrient Extraction → Validated Food Data**

When a food is searched, such as **"chicken breast,"** the program sends the search request to the USDA FoodData Central API. The USDA returns information about foods that match the search. The program then extracts only the information needed by the project.

## `NutrientsPer100g`

`NutrientsPer100g` stores the nutritional information for a food per 100 grams. It currently uses:

- Calories
- Protein
- Carbohydrates
- Fat

The model also ensures that nutrient values cannot be negative.

## `USDAFood`

`USDAFood` represents a food returned by the USDA. It stores:

- The USDA FoodData Central ID (`fdc_id`)
- The food's description or name
- The type of USDA food record
- The food's nutritional information

## `USDAClient`

The `USDAClient` class handles communication with the USDA FoodData Central API.

Before making a request, the client checks for a valid USDA API key. The key can either be provided directly or retrieved from the `USDA_API_KEY` environment variable.

### `search_foods()`

The `search_foods()` function handles food searches.

Before sending the search to USDA, the function:

- Cleans unnecessary spaces from the user's search query
- Verifies that the search is not empty
- Verifies that the requested number of results is between 1 and 50

The search query is then sent to the USDA FoodData Central API.

After receiving the response, the program converts the USDA's JSON response into Python data. Each result is then converted into a `USDAFood` object so that the data has a predictable structure and can be validated before being used elsewhere in the project.

### `_nutrient_amounts()`

The `_nutrient_amounts()` function extracts the nutritional information needed by the project.

The function identifies these nutrients using their USDA nutrient IDs:

| USDA Nutrient ID | Nutrient |
|---|---|
| `1008` | Calories |
| `1003` | Protein |
| `1005` | Carbohydrates |
| `1004` | Fat |

If one of the required nutrients is missing from the USDA response, its value defaults to zero.

Nutrient values are stored using Python's `Decimal` type to provide more predictable decimal calculations.

## Error Handling and Validation

The code includes several checks to prevent invalid data from being used by the project. For example, it checks for:

- A missing USDA API key
- An empty food search
- An invalid number of requested results
- Failed USDA API requests
- Invalid nutrient values
- Negative nutrient values

---

# API_test.py

This file is a simple testing program used to verify that the USDA client from `API_File.py` is working correctly.

Rather than containing the API logic itself, this file uses the previously created `USDAClient` to perform a food search and display the results.

The code follows this general process:

**Start Program → Connect to USDA Client → Search for Food → Receive Results → Display Food and Nutrient Information**

In this example, the program searches the USDA FoodData Central database for **"paneer"** and requests up to five matching foods.

## Setup

Before running the program, the required Python libraries, `httpx` and `pydantic`, must be installed.

```bash
pip install httpx pydantic
```

The user must also provide a USDA API key through the `USDA_API_KEY` environment variable.

The API key is stored outside of the Python file to prevent private credentials from accidentally being included in the project's source code or uploaded to Git.

For example:

```bash
export USDA_API_KEY="your_actual_api_key_here"
```

## Asynchronous Programming

The program imports Python's `asyncio` library because the `USDAClient` uses asynchronous functions.

Asynchronous programming allows the program to wait for the USDA API to respond without unnecessarily blocking other operations.

The following statement starts the asynchronous `main()` function when the file is run:

```python
asyncio.run(main())
```

## `main()` Function

Inside the `main()` function, the program creates a `USDAClient` using an `async with` statement.

```python
async with USDAClient() as client:
```

This opens the HTTP connection needed to communicate with the USDA API. Once the search is finished, the connection is automatically closed.

The program performs the following search:

```python
foods = await client.search_foods("paneer", page_size=5)
```

It requests a maximum of five results from USDA.

The actual searching and processing of USDA data are handled by the `search_foods()` function from `API_File.py`. It receives the search term and returns the processed food results.

## Displaying the Results

After receiving the results, the program first displays the total number of foods found. It then loops through each returned food one at a time.

Because the results have already been processed and validated by `API_File.py`, each result is available as a `USDAFood` object.

For each food, the program accesses its `nutrients_per_100g` information and displays:

- Food description
- USDA FoodData Central ID
- Calories per 100 grams
- Protein per 100 grams
- Carbohydrates per 100 grams
- Fat per 100 grams

## Running the Program

The final section checks whether the Python file is being run directly:

```python
if __name__ == "__main__":
    asyncio.run(main())
```

If the file is run directly, the program starts the `main()` function using `asyncio.run()`.

This keeps `API_test.py` as a simple test program while allowing the USDA API functionality in `API_File.py` to remain reusable by other parts of the project.
