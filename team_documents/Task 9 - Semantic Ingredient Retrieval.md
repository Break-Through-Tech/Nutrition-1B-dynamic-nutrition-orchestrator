# Task 9: Semantic Ingredient Retrieval

## My Notes and Reflection
### 1. What I Worked On
For Task 9, I worked on setting up a semantic ingredient retrieval system for our nutrition project. 
The main goal was to see if we could use embeddings and a vector database to find ingredients that are similar to the ones in our recipe database.

I ended up using ChromaDB as the vector database and the Sentence Transformers model **all-MiniLM-L6-v2** to generate embeddings. 
I indexed all 126 unique ingredients from our recipe database and created scripts that allow us to build, update, and search the index.
After getting everything set up, I tested different ingredients like moong dal, rajma, atta, ajwain, kala namak, and paneer. 
I noticed that semantic search was able to find different variations of ingredient names, which was useful because not every recipe uses the exact same wording.

I also compared the results with our Phase 1 keyword matcher. What I found was that both approaches had their own strengths. 
The keyword matcher worked well when it had the right synonyms available, while semantic search was helpful for finding variations in ingredient names.

However, semantic search wasn't always accurate. For example, when I searched for "dragonfruit powder," it returned "cumin powder" with a similarity score of 0.614. 
This helped me understand that just because two ingredients have a relatively high similarity score doesn't mean they are actually the same ingredient.

Overall, I found that semantic search could be useful for suggesting possible ingredient matches, but we would still need another step to verify the results before assigning USDA IDs.

### 2. Challenges I Had
One of the biggest things I struggled with was figuring out how to actually measure whether the semantic search was working well. 
At first, I thought I could just use precision, recall, and F1 scores to compare it with our Phase 1 matcher. But after looking into our existing validation dataset, 
I realized that it was designed for checking USDA ingredient matches, not semantic search results.

This made it harder to come up with actual conclusions about which approach was better. I had to figure out what we were really trying to measure and why our existing 
metrics weren't necessarily appropriate. I eventually decided to do a qualitative comparison instead of trying to calculate numbers that wouldn't accurately represent the results.

Another challenge was working with such a small dataset. We only had 126 unique ingredients, so there was a limit to how much I could test and what I could conclude from the results. 
I could see how the system performed on certain examples, but I couldn't confidently say that it would perform the same way with a much larger database.

I also struggled with understanding what the actual code changes were doing. There were multiple files being created and modified, and I sometimes found it 
difficult to understand how everything connected. I had to spend time figuring out what the embedding model was doing, how ChromaDB stored the embeddings, and 
how the search process actually worked instead of just looking at whether the code ran successfully.

Another thing I had to learn was how to work more comfortably in the terminal and with Git. I practiced running Python scripts, installing dependencies, 
testing my code, checking file changes, creating a separate branch, committing changes, and pushing everything to GitHub. I wasn't completely comfortable with 
all of these commands at first, but working through Task 9 helped me get more familiar with them.

### 3. Things I Learned
* Learned how embeddings work and how text can be converted into numerical representations.
* Got experience using ChromaDB to store and retrieve embeddings.
* Learned that semantic similarity doesn't always mean two ingredients are actually the same.
* Better understood why choosing the right evaluation metrics and having good validation data matters.
* Got more comfortable reading code changes and understanding how different files connect.
* Learned more terminal commands and how to use Git branches, commits, and pushes to manage my work.

One of my biggest takeaways from this task was that getting something to work is only part of the process. I also need to understand what the results actually mean, 
whether they are reliable, and what limitations the system has.

I definitely had to spend time figuring things out along the way, especially with the evaluation and understanding the code, but I feel 
like I have a much better understanding of semantic search and how it can be used in an actual project now.
