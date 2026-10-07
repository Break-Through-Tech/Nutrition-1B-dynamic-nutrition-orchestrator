**Gesell**

As I worked through tasks 1 and 3 (Setting up the USDA FoodData Central API and creating the Pydantic validation schemas), I had to learn a lot about APIs, as I had previously (and only once) worked with APIs, but it was still new to me. It helped to have knowledge of how it works, but it took time to first figure out how to create the Python script with the Pydantic validation schemas. I did not know what that was or how to implement it, so I did research online as I worked through the script. With help from the internet, I was able to overcome these technical challenges.

Along the way, my personal life and school life have also been time-consuming, so making sure that I allotted time for the project was crucial. I made sure to give myself time to work and take the necessary breaks when needed. By putting this time in my calendar, I kept myself accountable and responsible for the work I was doing. 

**Sadia**

I worked on Task 2 (Building the local recipe seed database), and as usual when working with data, I had to first check if the data I was trying to extract was clean. I checked through the formats to normalize input data. I applied lowercasing and unique title constraints during my batch inserts to automatically reject duplicates.

I was wrapping up my internship and in the process of several moves, so I was having trouble setting extra time aside from our meetings to complete extra work. However, I was able to complete my given task and get access to the repo for the team to use my findings. I didn't let this small obstacle stop me.

**Lakshmi** 
I’m tasked with completing Task #11, which requires building an error recovery state loop. To begin this task, all the previous tasks must be completed, so I have yet to officially start. The challenge I’m facing is that I don’t have experience building anything similar in the past, but I have begun doing some research regarding the structure of an error-recovery state loop. 

I have learned the basic logic behind how an error-recovery state loop works, and I have a general idea of how to break down the different validation loops for this specific project to ensure smooth functionality. I also learned that implementing an infinite loop would cause major issues and that it is better to have a retry limit. 

**Shirina**
I worked on the deterministic nutrition engine and evaluation benchmarks. I built the calculations for calories, protein, carbohydrates, and fat from ingredient quantities, then added scaling to help recipes meet protein and calorie targets. I also created benchmark measures for macro error, F1 score, and dietary constraint compliance, and added automated tests to check the results.

One challenge was that the recipe database contains ingredient names that are not all present in the nutrition catalog. Calculating macros for those ingredients without verified data could produce misleading results. I addressed this by keeping recipe selection separate from nutrition arithmetic and making the system report or avoid unsupported calculations instead of guessing. I also added dietary restriction filtering and an optional Ollama selection layer, with deterministic checks and a fallback so the model cannot bypass the restrictions. Testing the system helped me catch issues and confirm the expected behavior.
