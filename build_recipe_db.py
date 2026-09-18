"""Build the local recipe seed database (Task 2).

Ingests the recipes from the two Google Docs shared in the project
("High-Protein Indian Vegetarian Meal Plan & Grocery List" and the
companion "Grocery Matrix" doc) and produces two outputs:

  1. recipes.json     - full normalized recipe records, validated via Pydantic
  2. ingredients.csv  - a deduplicated, flat list of every ingredient name
                         used across all recipes, for Task 6's NLP/keyword
                         matcher to map to USDA FDC IDs.

Two source docs, two recipe styles:
  - GROCERY_LIST doc: clean per-person quantities (servings=1), used as the
    primary/canonical set (breakfast, lunch, dinner, snack — 16 recipes,
    each repeated on two weekdays per the schedule but stored once).
  - GROCERY_MATRIX doc: family-scale (servings=4) dinners, several with
    separate "adult" and "kids" versions of the same night. Stored as
    additional recipes, tagged in `notes`.

Run: python build_recipe_db.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from recipe_schema import Recipe

GROCERY_LIST_DOC = "High-Protein Indian Vegetarian Meal Plan & Grocery List"
GROCERY_MATRIX_DOC = "High-Protein Indian Vegetarian Meal Plan & Grocery Matrix"

RAW_RECIPES: list[dict] = [
    # ------------------------------------------------------------------
    # BREAKFASTS (Grocery List doc, per-person)
    # ------------------------------------------------------------------
    {
        "recipe_id": "protein-oats-upma",
        "name": "Savory Protein Oats Upma",
        "meal_type": "breakfast",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "oats", "quantity": 50, "unit": "g"},
            {"name": "low-fat Greek yogurt", "quantity": 150, "unit": "g"},
            {"name": "unflavored whey protein", "quantity": 15, "unit": "g"},
            {"name": "mustard seeds", "quantity": 0.25, "unit": "tsp"},
            {"name": "curry leaves", "quantity_text": "5-6 leaves"},
            {"name": "green chili", "quantity_text": "to taste"},
            {"name": "minced ginger", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Dry roast the oats in a pan for 3-4 minutes until aromatic; set aside.",
            "Whisk the Greek yogurt with the whey and 50ml water until smooth to prevent clumping.",
            "Heat the oil, add mustard seeds, curry leaves, ginger, and green chili; saute 60 seconds.",
            "Add 100ml water, bring to a boil, reduce heat, and slowly stir in the yogurt-whey mixture.",
            "Add the toasted oats, stir, cover, and steam on low heat 3-4 minutes until water is absorbed.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Monday and Thursday. Target ~30g protein for the meal.",
    },
    {
        "recipe_id": "moong-dal-cheela",
        "name": "High-Protein Moong Dal Cheela",
        "meal_type": "breakfast",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "moong dal, soaked overnight", "quantity": 60, "unit": "g"},
            {"name": "low-fat paneer, crumbled", "quantity": 75, "unit": "g"},
            {"name": "coriander", "quantity_text": "to taste"},
            {"name": "green chili", "quantity_text": "to taste"},
            {"name": "salt", "quantity_text": "to taste"},
            {"name": "hing", "quantity_text": "pinch"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Drain the soaked moong dal and blend with green chili, ginger, hing, salt, and minimal water into a smooth batter.",
            "Season the crumbled paneer with salt, chaat masala, and chopped coriander for the filling.",
            "Heat a lightly oiled non-stick tawa, pour a ladle of batter, and spread thin in a circle.",
            "Cook on medium heat until the edges lift, flip, and cook the other side for 1 minute.",
            "Flip back, add the paneer filling to the center, fold the cheela over, and serve hot.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Tuesday and Friday. Target ~30g protein for the meal.",
    },
    {
        "recipe_id": "tofu-scramble-toast",
        "name": "Tofu Scramble Toast",
        "meal_type": "breakfast",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "extra-firm tofu", "quantity": 150, "unit": "g"},
            {"name": "whole wheat bread", "quantity": 2, "unit": "piece", "notes": "slices"},
            {"name": "turmeric", "quantity": 0.25, "unit": "tsp"},
            {"name": "kala namak (black salt)", "quantity": 0.25, "unit": "tsp"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
            {"name": "cilantro", "quantity_text": "chopped, to taste"},
        ],
        "instructions": [
            "Drain the tofu, press with a paper towel to remove moisture, and mash coarsely with a fork.",
            "Heat the oil, optionally add a pinch of cumin seeds, then add the mashed tofu.",
            "Add turmeric, salt, and kala namak; stir-fry 4-5 minutes on medium heat.",
            "Toast the bread.",
            "Top the toast with the warm tofu scramble and garnish with cilantro.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Wednesday and Saturday. Target ~30g protein for the meal.",
    },
    {
        "recipe_id": "modified-paneer-paratha",
        "name": "Modified Paneer Paratha",
        "meal_type": "breakfast",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "whole wheat flour (atta)", "quantity": 50, "unit": "g"},
            {"name": "low-fat paneer, grated", "quantity": 100, "unit": "g"},
            {"name": "carom seeds (ajwain)", "quantity": 0.5, "unit": "tsp"},
            {"name": "red chili powder", "quantity_text": "to taste"},
            {"name": "garam masala", "quantity_text": "to taste"},
            {"name": "ghee", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Knead the atta with water into a soft dough; rest 10 minutes.",
            "Mix the grated paneer with ajwain, salt, red chili powder, garam masala, and coriander.",
            "Roll the dough into a disc, place the paneer filling in the center, seal the edges, and flatten gently.",
            "Roll out into a paratha, taking care not to rupture the dough wrapper.",
            "Cook on a hot tawa with exactly 1 tsp ghee spread evenly on both sides until golden-brown spots appear.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Sunday only. Target ~30g protein for the meal.",
    },
    # ------------------------------------------------------------------
    # LUNCHES (Grocery List doc, per-person)
    # ------------------------------------------------------------------
    {
        "recipe_id": "soya-chunks-matar-curry-brown-rice",
        "name": "Soya Chunks Matar Curry with Brown Rice",
        "meal_type": "lunch",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "dry soya chunks", "quantity": 60, "unit": "g"},
            {"name": "green peas", "quantity": 50, "unit": "g"},
            {"name": "brown rice", "quantity": 60, "unit": "g"},
            {"name": "onion-tomato gravy base", "quantity": 3, "unit": "tbsp", "notes": "or 1 onion + 2 tomatoes, pureed"},
            {"name": "garam masala", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Boil the soya chunks 10 minutes until soft; drain, rinse, and squeeze out all excess water.",
            "Cook the brown rice using your preferred method and set aside.",
            "Heat the oil, add the gravy base with ginger-garlic paste, turmeric, coriander powder, and chili powder; cook until the raw smell disappears.",
            "Add the squeezed soya chunks and peas; toss into the masala for 2 minutes.",
            "Add 150ml water, cover, simmer 10 minutes, finish with garam masala, and serve with the rice.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Monday and Thursday. Target ~40g protein for the meal.",
    },
    {
        "recipe_id": "kadhai-tofu-with-quinoa",
        "name": "Kadhai Tofu with Quinoa",
        "meal_type": "lunch",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "extra-firm tofu", "quantity": 200, "unit": "g"},
            {"name": "quinoa", "quantity": 60, "unit": "g"},
            {"name": "capsicum, diced", "quantity": 0.5, "unit": "piece"},
            {"name": "onion, diced", "quantity": 0.5, "unit": "piece"},
            {"name": "kadhai spice mix (crushed coriander seeds / dry red chili)", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Rinse the quinoa and boil in 120ml water with a pinch of salt until fluffy; set aside.",
            "Cut the tofu into uniform cubes and blot dry.",
            "Heat the oil, add the crushed kadhai spices, then onions and capsicum; saute on high heat 2 minutes.",
            "Add tomato puree, turmeric, and salt; cook 2 minutes.",
            "Fold in the tofu cubes and toss on medium heat 4-5 minutes until coated and heated through; serve with the quinoa.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Tuesday and Friday. Target ~40g protein for the meal.",
    },
    {
        "recipe_id": "soya-keema-masala-with-roti",
        "name": "Soya Keema Masala with Roti",
        "meal_type": "lunch",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "dry soya granules", "quantity": 60, "unit": "g"},
            {"name": "atta, for 2 rotis", "quantity": 50, "unit": "g"},
            {"name": "onion-tomato gravy base", "quantity_text": "as needed"},
            {"name": "kasuri methi", "quantity": 0.5, "unit": "tsp"},
            {"name": "garam masala", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Soak the soya granules in hot water 15 minutes, then drain and press thoroughly to remove all water.",
            "Knead the atta into dough, roll into two thin rotis, and cook on a hot tawa without oil.",
            "Heat the oil, add ginger-garlic paste and the gravy base, and saute with coriander, cumin, and chili powder.",
            "Add the squeezed soya granules and stir-fry 3-4 minutes until dry.",
            "Add 100ml water, cover, cook 5-7 minutes, crumble kasuri methi over the top, and serve with the rotis.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Wednesday and Saturday. Target ~40g protein for the meal.",
    },
    {
        "recipe_id": "chickpea-chole-biryani",
        "name": "Chickpea (Chole) Biryani",
        "meal_type": "lunch",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "kabuli chana, soaked and boiled", "quantity": 80, "unit": "g"},
            {"name": "basmati rice", "quantity": 50, "unit": "g"},
            {"name": "biryani spice mix", "quantity_text": "to taste"},
            {"name": "low-fat curd", "quantity": 150, "unit": "g"},
            {"name": "mint leaves", "quantity_text": "to taste"},
            {"name": "cucumber, grated", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Boil the basmati rice until 80% cooked; drain and set aside.",
            "Heat the oil, saute onions until golden, then add ginger-garlic paste, tomato puree, and biryani masala.",
            "Add the boiled kabuli chana and cook 5 minutes until thick.",
            "Layer the partially cooked rice over the chana masala, scatter mint leaves, and add a splash of water.",
            "Cover tightly and cook on ultra-low heat (dum) 12-15 minutes.",
            "Whisk the curd with grated cucumber and roasted cumin powder to make the side raita.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Sunday only. Target ~40g protein for the meal.",
    },
    # ------------------------------------------------------------------
    # DINNERS (Grocery List doc, per-person)
    # ------------------------------------------------------------------
    {
        "recipe_id": "paneer-bhurji-with-roti",
        "name": "Paneer Bhurji with Whole Wheat Roti",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "low-fat paneer", "quantity": 150, "unit": "g"},
            {"name": "atta, for 2 rotis", "quantity": 50, "unit": "g"},
            {"name": "onion, finely chopped", "quantity": 1, "unit": "piece"},
            {"name": "tomato, finely chopped", "quantity": 1, "unit": "piece"},
            {"name": "green chili", "quantity_text": "to taste"},
            {"name": "turmeric", "quantity": 0.25, "unit": "tsp"},
            {"name": "ghee", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Knead dough from the atta and roll/cook 2 plain rotis.",
            "Heat the ghee, saute onions and green chilies until translucent.",
            "Add tomatoes, turmeric, and salt; cook until the tomatoes soften completely.",
            "Crumble the paneer directly into the pan and stir well to integrate with the masala.",
            "Cook on medium-low heat no more than 3-4 minutes to keep the paneer moist; garnish with coriander.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Monday and Thursday. Target ~35g+ protein for the meal.",
    },
    {
        "recipe_id": "black-chana-chaat-sprouts",
        "name": "Black Chana Chaat & Sprouts",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "kala chana, soaked overnight and boiled", "quantity": 80, "unit": "g"},
            {"name": "mixed sprouts, steamed", "quantity": 50, "unit": "g"},
            {"name": "cucumber, chopped", "quantity": 0.5, "unit": "piece"},
            {"name": "tomato, chopped", "quantity": 1, "unit": "piece", "notes": "small"},
            {"name": "chaat masala", "quantity_text": "to taste"},
            {"name": "lemon juice", "quantity_text": "to taste"},
            {"name": "olive oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Drain the boiled kala chana of all surface liquid and cool to room temperature.",
            "Lightly steam the mixed sprouts 3 minutes to remove raw starchiness, then cool.",
            "Combine the chana, sprouts, cucumber, and tomatoes in a large bowl.",
            "Drizzle exactly 1 tsp olive oil over the mixture.",
            "Season with chaat masala, black salt, roasted cumin powder, and lemon juice; toss and serve cold.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Tuesday and Friday. Target ~35g+ protein for the meal.",
    },
    {
        "recipe_id": "high-protein-dal-makhani-paneer",
        "name": "High-Protein Dal Makhani & Paneer",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "whole black urad dal", "quantity": 40, "unit": "g"},
            {"name": "rajma", "quantity": 10, "unit": "g"},
            {"name": "low-fat milk", "quantity": 50, "unit": "ml"},
            {"name": "low-fat paneer", "quantity": 120, "unit": "g"},
            {"name": "ginger, julienned", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Pressure cook the soaked urad dal and rajma with salt and water ~6-8 whistles until mashable; mash some against the pot wall for creaminess.",
            "Heat the oil, add ginger-garlic paste and a small amount of tomato puree, and cook until dark red.",
            "Pour the mashed dal into the pan and simmer 20-30 minutes, gradually adding the milk to develop a creamy emulsion.",
            "Cut the paneer into thick slabs, season with salt and chili, and sear dry on a hot non-stick pan until lightly browned.",
            "Serve the dal topped with ginger juliennes alongside the grilled paneer.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Wednesday and Saturday. Target ~35g+ protein for the meal.",
    },
    {
        "recipe_id": "soya-tofu-stir-fry",
        "name": "Soya & Tofu Stir-Fry",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "dry soya chunks, boiled and squeezed", "quantity": 40, "unit": "g"},
            {"name": "extra-firm tofu, cubed", "quantity": 100, "unit": "g"},
            {"name": "broccoli and bell peppers, mixed", "quantity": 1, "unit": "cup"},
            {"name": "soy sauce", "quantity": 1, "unit": "tbsp"},
            {"name": "vinegar", "quantity": 1, "unit": "tsp"},
            {"name": "garlic, minced", "quantity_text": "to taste"},
            {"name": "oil", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Prepare the soya chunks by boiling, rinsing, and squeezing thoroughly; halve if large.",
            "Heat the oil in a wok on high heat, add minced garlic, and saute 30 seconds.",
            "Add broccoli and bell pepper strips; stir-fry aggressively 2-3 minutes until bright but crisp.",
            "Add the tofu cubes and squeezed soya chunks.",
            "Pour the soy sauce and vinegar around the edges of the wok and toss 2 minutes until glazed.",
        ],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Sunday only. Target ~35g+ protein for the meal.",
    },
    # ------------------------------------------------------------------
    # SNACKS (Grocery List doc, per-person)
    # ------------------------------------------------------------------
    {
        "recipe_id": "roasted-chickpeas-almonds",
        "name": "Roasted Chickpeas & Almonds",
        "meal_type": "snack",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "dry-roasted chana", "quantity": 40, "unit": "g"},
            {"name": "almonds", "quantity": 10, "unit": "piece"},
        ],
        "instructions": ["Combine and consume as a dry, ready-to-go portion."],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Monday and Thursday. Target ~15g+ protein for the meal.",
    },
    {
        "recipe_id": "protein-shake",
        "name": "Protein Shake",
        "meal_type": "snack",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "whey isolate", "quantity": 1, "unit": "piece", "notes": "1 scoop"},
            {"name": "soy milk", "quantity": 200, "unit": "ml"},
            {"name": "chia seeds", "quantity": 10, "unit": "g"},
        ],
        "instructions": ["Blend the whey isolate into the soy milk, stir in the chia seeds, and let hydrate 5 minutes before drinking."],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Tuesday and Friday. Target ~15g+ protein for the meal.",
    },
    {
        "recipe_id": "spiced-edamame",
        "name": "Spiced Edamame",
        "meal_type": "snack",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "whole edamame pods", "quantity": 150, "unit": "g"},
            {"name": "sea salt", "quantity_text": "to taste"},
            {"name": "red chili flakes", "quantity_text": "to taste"},
        ],
        "instructions": ["Steam the edamame pods 5 minutes, then toss immediately in sea salt and red chili flakes; shell before eating."],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Wednesday and Saturday. Target ~15g+ protein for the meal.",
    },
    {
        "recipe_id": "roasted-soya-nuts",
        "name": "Roasted Soya Nuts",
        "meal_type": "snack",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 1,
        "ingredients": [
            {"name": "dry-roasted soya nuts", "quantity": 45, "unit": "g"},
        ],
        "instructions": ["Weigh out a clean 45g portion and consume directly."],
        "source_doc": GROCERY_LIST_DOC,
        "notes": "Served Sunday only. Target ~15g+ protein for the meal.",
    },
    # ------------------------------------------------------------------
    # ADDITIONAL DINNERS (Grocery Matrix doc, family-scale, servings=4)
    # ------------------------------------------------------------------
    {
        "recipe_id": "spicy-paneer-bhurji-adult",
        "name": "Spicy Paneer Bhurji (Adult Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "low-fat paneer, crumbled", "quantity": 600, "unit": "g"},
            {"name": "onions, finely chopped", "quantity": 2, "unit": "piece"},
            {"name": "tomatoes", "quantity": 3, "unit": "piece"},
            {"name": "green chilies", "quantity": 2, "unit": "piece"},
            {"name": "ginger-garlic paste", "quantity": 1, "unit": "tbsp"},
            {"name": "turmeric", "quantity": 1, "unit": "tsp"},
            {"name": "red chili powder", "quantity": 1, "unit": "tsp"},
            {"name": "garam masala", "quantity": 2, "unit": "tsp"},
            {"name": "mustard oil", "quantity": 1, "unit": "tbsp"},
            {"name": "coriander leaves", "quantity_text": "fresh, for garnish"},
        ],
        "instructions": [
            "Heat oil in a heavy skillet; saute onions and ginger-garlic paste until caramelized.",
            "Add tomatoes, chilies, and dry spices; cook until the oil begins to separate slightly.",
            "Toss in the crumbled paneer and stir rapidly on high heat 3-4 minutes to avoid moisture loss.",
            "Garnish with coriander; serve with 2 measured oats-wheat rotis per adult.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Monday dinner, adult path (dual-path night; kids get a separate mild version). Serves 4 adults.",
    },
    {
        "recipe_id": "mild-paneer-tikka-skewers-kids",
        "name": "Mild Paneer Tikka Skewers + Soft Paratha (Kids Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein", "kid-friendly"],
        "servings": 4,
        "ingredients": [
            {"name": "regular paneer, cubed thick", "quantity": 400, "unit": "g"},
            {"name": "mild Greek yogurt", "quantity": 1, "unit": "cup"},
            {"name": "Kashmiri red chili powder", "quantity": 1, "unit": "tsp"},
            {"name": "cumin powder", "quantity": 1, "unit": "tsp"},
            {"name": "chaat masala", "quantity": 1, "unit": "tsp"},
            {"name": "bell peppers, diced", "quantity_text": "to taste"},
            {"name": "onions, diced", "quantity_text": "to taste"},
            {"name": "soft readymade parathas", "quantity_text": "as needed"},
        ],
        "instructions": [
            "Whisk yogurt with Kashmiri chili, cumin, and chaat masala; marinate paneer cubes and veggies 30 minutes.",
            "Thread onto wooden skewers.",
            "Sear on a non-stick tawa with minimal butter until golden on all edges; serve with heated soft parathas.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Monday dinner, kids path (dual-path night). Serves 4 kids.",
    },
    {
        "recipe_id": "kala-chana-chaat-sprouted-moong-salad-matrix",
        "name": "Kala Chana Chaat & Sprouted Moong Salad Matrix (Adult Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "kala chana, boiled", "quantity": 600, "unit": "g"},
            {"name": "raw sprouted moong", "quantity": 400, "unit": "g"},
            {"name": "cucumber, large, diced", "quantity": 1, "unit": "piece"},
            {"name": "tomatoes, diced", "quantity": 2, "unit": "piece"},
            {"name": "red onion, diced", "quantity": 1, "unit": "piece"},
            {"name": "green chilies", "quantity": 2, "unit": "piece"},
            {"name": "chaat masala", "quantity": 1, "unit": "tbsp"},
            {"name": "roasted cumin powder", "quantity": 1, "unit": "tsp"},
            {"name": "lemon juice, freshly squeezed", "quantity_text": "to taste"},
            {"name": "black salt", "quantity_text": "to taste"},
        ],
        "instructions": [
            "Combine boiled chana and raw sprouts in a large mixing bowl.",
            "Toss in the diced vegetables and green chilies.",
            "Drizzle lemon juice, sprinkle dry spices, and massage the flavors together; serve chilled.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Tuesday dinner, adult path (dual-path night). Serves 4 adults.",
    },
    {
        "recipe_id": "cheesy-moong-dal-quesadillas-kids",
        "name": "Cheesy Moong Dal Quesadillas (Kids Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein", "kid-friendly"],
        "servings": 4,
        "ingredients": [
            {"name": "moong dal, soaked, ground into paste", "quantity": 1, "unit": "cup"},
            {"name": "flour tortillas", "quantity_text": "as needed"},
            {"name": "mozzarella/cheddar shredded blend", "quantity": 1, "unit": "cup"},
            {"name": "sweet corn kernels, mild", "quantity_text": "to taste"},
        ],
        "instructions": [
            "Spread a thin layer of the moong dal batter onto a hot greased tawa to form a mild cheela base; flip once cooked.",
            "Sprinkle one half with cheese blend and sweet corn.",
            "Fold a tortilla over it (or fold the cheela itself) and press until the cheese melts; slice into triangles.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Tuesday dinner, kids path (dual-path night). Serves 4 kids.",
    },
    {
        "recipe_id": "high-protein-dal-makhani-matrix-adult",
        "name": "High-Protein Dal Makhani Matrix (Adult Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "whole black urad dal", "quantity": 400, "unit": "g"},
            {"name": "rajma, soaked overnight", "quantity": 100, "unit": "g"},
            {"name": "soya chunks, processed into fine grains", "quantity": 200, "unit": "g"},
            {"name": "tomato puree", "quantity": 2, "unit": "cup"},
            {"name": "ginger-garlic paste", "quantity": 1, "unit": "tbsp"},
            {"name": "degi mirch", "quantity": 1, "unit": "tsp"},
            {"name": "garam masala", "quantity": 1, "unit": "tsp"},
            {"name": "fat-free Greek yogurt", "quantity": 1, "unit": "cup"},
            {"name": "spray oil", "quantity_text": "minimal"},
        ],
        "instructions": [
            "Pressure cook the urad dal, rajma, and processed soya grains together 6-8 whistles until creamed.",
            "In a separate pan, saute ginger-garlic paste in minimal oil, add tomato puree and spices, and cook down.",
            "Pour the creamed dal into the gravy and simmer 45 minutes; off heat, fold in Greek yogurt for a creamy texture.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Wednesday dinner, adult path (dual-path night). Serves 4 adults.",
    },
    {
        "recipe_id": "creamy-butter-dal-jeera-rice-kids",
        "name": "Creamy Butter Dal with Jeera Rice (Kids Path)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein", "kid-friendly"],
        "servings": 4,
        "ingredients": [
            {"name": "yellow moong/toor dal", "quantity": 1, "unit": "cup"},
            {"name": "premium butter", "quantity": 2, "unit": "tbsp"},
            {"name": "cumin seeds", "quantity": 1, "unit": "tsp"},
            {"name": "turmeric", "quantity_text": "pinch"},
            {"name": "salt", "quantity_text": "to taste"},
            {"name": "long-grain basmati rice", "quantity_text": "as needed"},
        ],
        "instructions": [
            "Boil the dal with turmeric and salt until completely soft and smooth.",
            "Melt butter in a small pan, add cumin seeds until they splutter, and pour over the dal as a tadka; serve over jeera basmati rice.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Wednesday dinner, kids path (dual-path night). Serves 4 kids.",
    },
    {
        "recipe_id": "saag-paneer-universal",
        "name": "Low-Fat Paneer & Spinach Curry (Saag Paneer)",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "fresh spinach", "quantity": 1, "unit": "kg"},
            {"name": "low-fat paneer, cubed and seared", "quantity": 800, "unit": "g"},
            {"name": "onions", "quantity": 2, "unit": "piece"},
            {"name": "ginger-garlic paste", "quantity": 2, "unit": "tbsp"},
            {"name": "cumin seeds", "quantity": 1, "unit": "tsp"},
            {"name": "garam masala", "quantity": 1, "unit": "tsp"},
            {"name": "kasuri methi", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Blanch spinach 2 minutes, shock in ice water, then puree with minimal water.",
            "Saute cumin seeds, onions, and ginger-garlic paste; add the spinach puree and spices and simmer 10 minutes.",
            "Fold in the paneer cubes gently and finish with crushed kasuri methi; serve with whole wheat rotis.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Thursday dinner, universal (whole family, no adult/kids split). Serves 4.",
    },
    {
        "recipe_id": "tofu-kofta-curry-quinoa-rice-universal",
        "name": "Tofu Kofta Curry in Light Tomato Gravy + Quinoa Rice",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "firm tofu, mashed", "quantity": 800, "unit": "g"},
            {"name": "soy flour", "quantity": 4, "unit": "tbsp", "notes": "binder"},
            {"name": "garam masala", "quantity": 1, "unit": "tsp"},
            {"name": "fresh tomato puree", "quantity": 4, "unit": "cup"},
            {"name": "onion paste", "quantity": 1, "unit": "piece"},
            {"name": "ginger-garlic paste", "quantity_text": "to taste"},
            {"name": "quinoa-rice blend", "quantity": 0.5, "unit": "cup", "notes": "per person"},
        ],
        "instructions": [
            "Mix mashed tofu, soy flour, salt, and garam masala; roll into dense koftas and bake or air-fry at 400F (200C) until firm.",
            "Simmer onion paste, ginger-garlic paste, and tomato puree with mild aromatics for the curry base; drop in the koftas 5 minutes before serving alongside the quinoa-rice blend.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Friday dinner, universal (whole family, no adult/kids split). Serves 4.",
    },
    {
        "recipe_id": "mixed-dal-chilla-wraps-universal",
        "name": "Mixed Dal Chilla Wraps with Mint Chutney",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "split moong dal", "quantity_text": "equal parts, soaked overnight and ground"},
            {"name": "split chana dal", "quantity_text": "equal parts, soaked overnight and ground"},
            {"name": "split urad dal", "quantity_text": "equal parts, soaked overnight and ground"},
            {"name": "hing", "quantity_text": "to taste"},
            {"name": "carom seeds (ajwain)", "quantity_text": "to taste"},
            {"name": "mint-cilantro-yogurt chutney", "quantity_text": "as needed"},
            {"name": "shredded cucumber", "quantity_text": "to taste"},
            {"name": "shredded carrots", "quantity_text": "to taste"},
        ],
        "instructions": [
            "Season the mixed dal batter with hing, salt, and ajwain; ladle onto a hot flat-top and spread thin, cooking until crispy on both sides.",
            "Spread mint chutney across the interior, layer with shredded vegetables, roll tightly, and slice down the center.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Saturday dinner, universal (whole family, no adult/kids split). Serves 4.",
    },
    {
        "recipe_id": "soya-tofu-vegetable-stir-fry-glaze-universal",
        "name": "Soya & Tofu Vegetable Stir-Fry with Garlic-Ginger Glaze",
        "meal_type": "dinner",
        "diet_tags": ["vegetarian", "high-protein"],
        "servings": 4,
        "ingredients": [
            {"name": "large soya chunks, triple-boiled and hard-squeezed", "quantity": 500, "unit": "g"},
            {"name": "firm tofu, cubed", "quantity": 500, "unit": "g"},
            {"name": "broccoli florets", "quantity": 2, "unit": "cup"},
            {"name": "mixed bell peppers", "quantity": 2, "unit": "cup"},
            {"name": "low-sodium soy sauce", "quantity": 4, "unit": "tbsp"},
            {"name": "garlic, minced", "quantity": 2, "unit": "tbsp"},
            {"name": "ginger, minced", "quantity": 1, "unit": "tbsp"},
            {"name": "cornstarch", "quantity": 1, "unit": "tsp", "notes": "dissolved in 2 tbsp water"},
        ],
        "instructions": [
            "Sear tofu cubes and pre-prepped soya chunks in a smoking-hot wok with minimal oil until crispy.",
            "Toss in broccoli and bell peppers; flash fry 3 minutes to preserve texture, then add soy sauce, ginger, and garlic and stir rapidly.",
            "Pour the cornstarch slurry into the center of the wok to bind the sauce into a glossy glaze coating everything.",
        ],
        "source_doc": GROCERY_MATRIX_DOC,
        "notes": "Sunday dinner, universal (whole family, no adult/kids split). Serves 4.",
    },
]


def build_database(raw_recipes: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate every recipe against the schema — catches typos/missing fields early.
    recipes = [Recipe(**r) for r in raw_recipes]

    # --- Output 1: recipes.json ---
    recipes_path = output_dir / "recipes.json"
    with recipes_path.open("w") as f:
        json.dump([r.model_dump() for r in recipes], f, indent=2)

    # --- Output 2: ingredients.csv (deduplicated, for Task 6 matching) ---
    seen: dict[str, dict] = {}
    for recipe in recipes:
        for ing in recipe.ingredients:
            key = ing.name.strip().lower()
            if key not in seen:
                seen[key] = {
                    "ingredient_name": ing.name,
                    "example_unit": ing.unit or "",
                    "has_numeric_quantity": ing.quantity is not None,
                }

    ingredients_path = output_dir / "ingredients.csv"
    with ingredients_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ingredient_name", "example_unit", "has_numeric_quantity"])
        writer.writeheader()
        for row in seen.values():
            writer.writerow(row)

    print(f"Wrote {len(recipes)} recipes to {recipes_path}")
    print(f"Wrote {len(seen)} unique ingredients to {ingredients_path}")


if __name__ == "__main__":
    build_database(RAW_RECIPES, output_dir=Path("data"))
