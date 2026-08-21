# Dynamic Nutrition Orchestrator: A Trustworthy, Multi-Agent System for High-Protein Constraint Optimization

**Company / Org:** Other  
**Challenge Advisor:** FNU Sakshi, sakshi.lindner@gmail.com 

**AI Studio Coach:** Sai Duddu   
**Program:** Break Through Tech AI Studio - Fall 2026  

---

## 🏢 About the Organization
This organization operates in the health-tech sector, focusing on personalized nutrition and dietary wellness technology. The team aims to bridge the gap between traditional meal planning and data-driven precision by leveraging multi-agent systems to solve complex dietary constraint problems.

---

## 🎯 The Challenge
### Project Summary
This project involves building a Tool-Augmented Generation (TAG) system to automate high-protein Indian vegetarian meal planning while ensuring zero-hallucination arithmetic. By utilizing a hybrid architecture that pairs local recipe templates with real-time USDA nutrient density data, the team will develop a system capable of dynamically scaling ingredients to meet strict daily macro targets.

### Success Criteria
1) Macro Optimization Precision: The final orchestrator must achieve a Mean Absolute Error (MAE) of $< 2\%$ across a full 7-day generation cycle. If the target window requires exactly 140g of protein per day, the final composite calculations must consistently land between 137.2g and 142.8g based on USDA data.   

2) Entity Resolution Accuracy (F1-Score): The team’s string-matching and vector embedding pipeline must achieve an F1-score of $> 90\%$ on an unseen validation set of 30 common Indian vegetarian ingredients.   

3) Scheduling Constraint Adherence: The algorithm must demonstrate 100% compliance with zero-repeat ingredient logic rules across any consecutive 48-hour block to guarantee real-world lifestyle variety.

### Project Milestones

| Month | Milestone | Key Activities |
| :--- | :--- | :--- |
| September | Architecture, Data Pipelines & Deterministic Baseline | • Ingest and structure the local recipe seed database into normalized data structures.<br>• Integrate the USDA FoodData Central (FDC) REST API with Pydantic validation schemas.<br>• Build a baseline deterministic math engine to verify exact macronutrient totals and eliminate arithmetic errors.<br>• Define evaluation benchmarks (macro math variance, target compliance rate). |
| October | Multi-Agent Orchestration & Constraint Scaling Engine | • Construct a multi-agent state graph (using LangGraph or CrewAI) dividing tasks between Planner, Retriever, and Math Verifier agents.<br>• Implement dynamic ingredient quantity scaling algorithms to hit strict high-protein targets (e.g., 140g protein, <2,000 kcal/day).<br>• Set up vector indexing (ChromaDB / pgvector) for semantic recipe retrieval.<br>• Test multi-agent tool-calling and verify zero LLM mathematical hallucinations. |
| November / December | System Resiliency, UI Deployment & Capstone Deliverables | • Build an error-recovery state loop to gracefully intercept API timeouts or missing FDC records.<br>• Develop an interactive Streamlit application displaying 7-day meal plans and real-time macro math verification logs.<br>• Package a clean, production-ready GitHub repository with modular tool-calling methods.<br>• Finalize project documentation, evaluation reports, and stakeholder presentation deck. |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset
**Name and Source:** USDA FoodData Central API and curated internal JSON/CSV recipe seed bank.  
**Format:** JSON, CSV, and Vector Database Index.  
**Size:** 1gb to 5gb  
**Location:** Data folder, USDA API (refer to 'Other' section in 'Resources to get started'), https://fdc.nal.usda.gov/download-datasets (datasets can be downloaded from here as well)
### Key Details
- Google Docs for 2 weeks worth of Recipies and ingredients for initial prototype :
      - https://docs.google.com/document/d/1z0jDAp15grdH1b2sX_1RWf4ujwFWL8TQqnVDDiwhquk/edit?tab=t.0
      - https://docs.google.com/document/d/1gzs383g4_NduEGuVwtXjOARhem-ko_ctZIET7PpZneM/edit?tab=t.0
- USDA food DB csv, preferable to get ingredients and save local copy directly from the USDA API (free)
  
  
---

## 🛠️ Suggested Approach

**ML Problem Type:** NLP, LLM/RAG

**Recommended Libraries:**
- ollama, huggingface transformers

**Evaluation Metrics:**
- Provided in success criteria

  - First Phase : Build a small prototype with fixed set of recipes (provided in data section). To do this download from USDA API and create a local data set of ingredients in the given recipe. Build a React style single agent that accepts as input user requirements and then calls the macro calculation tool (created by students) to create a daily and then weekly plan with constraints specified by the user. The macro calculation tool makes AP calls/local database of ingredients calculates the macros/protein for the day. The NLP tool match can do the NLP match to select the right ingredient FDC ID and pass it on to the macro calculation tool.
  - Use a local quantized model using hugging face transformers/ ollama as the memory requirements will be lower.
  
    Second Phase : The first phase depended on NLP/keyword based match to select ingredients. In second phase we expand to create a vector DB of ingredients that allows for semantic match for ingredients to fit in existing recipes when the provided macros are not achievable by the provided ingredients in the existing recipes.
    Use a localized LLM using whatever architecture was used in the first phase, either Hugging Face Transformers or LLMs, for this phase, as the memory requirements will increase compared to the first phase.
    
    - 3rd Phase :  This phase the LLM, using the existing recipes as reference, can create entirely new recipes which hold the cultural influence and the user constraints to create new recipes. 
---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project: https://www.youtube.com/watch?v=MxV7L3rvgRw&t=5s

**Background Reading:**
- Title :  AI-Driven Personalized Meal Planning: A Web-based Platform for Tailored Nutrition
      - Type: Peer-reviewed research paper
      - Summary: Describes a web-based AI platform that generates weekly meal plans based on user health data, dietary preferences, and restrictions. It             uses optimization algorithms to balance nutrition, taste, and convenience.
      - Link : https://www.ijcaonline.org/archives/volume187/number57/hussain-2025-ijca-925913.pdf
-Title :NutriGen: Personalized Meal Plan Generator Leveraging Large Language Models
      - Type: preprint research paper
      - Summary: Describes a web-based AI platform that generates weekly meal plans based on user health data, dietary preferences, and restrictions. It             uses optimization algorithms to balance nutrition, taste, and convenience.
      - Link : https://arxiv.org/pdf/2502.20601
- Similar solution in market : https://www.hungryroot.com/?utm_source=bing&utm_medium=paid%20search&utm_campaign=409491910_1142394305641669&utm_content=ai%20for%20meal%20planning&wm_source=microsoft&wm_medium=ads&wm_ad_id=71399799407238&msclkid=08f58e2a2b2a141783b0e4ad111565f7

**Technical Tutorials:**
- Loading Huggingface models : https://huggingface.co/docs/transformers/models
- Hugging Face model Quantization : https://huggingface.co/docs/transformers/main/en/quantization/overview
- Working with Ollama : https://computingforgeeks.com/ollama-models-cheat-sheet/

**Other:**
- USDA API key info : https://fdc.nal.usda.gov/api-guide?ref=apitemple
- USDA Data Documentation : https://fdc.nal.usda.gov/data-documentation 
*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🤝 How We'll Work Together

**Official check-ins:** During our biweekly 45-minute AI Studio Lab Section meeting block (2nd and 4th week of every month)

 **Other ways to reach out to me with questions (in order of priority):** 
* Your team's channel within Break Through Tech’s Discord space
* sakshi.lindner@gmail.com; please copy your teammates and AI Studio Coach
* Request a team check-in on Zoom
* Note: I will aim to respond within 48 hours. Please reach out to your AI Studio Coach with urgent questions.

---

## 🚀 Getting Started

1. **Review this overview document** and note any questions for our first meeting
2. **Begin reviewing the dataset** using the link above
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

I’m excited to work with you!

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th (Break Through Tech’s Bridge to Studio - Session C). 
