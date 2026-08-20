---

> ## Challenge Advisor: Update & Finalize Your Project Overview
>
> > 💡 **These grey text instructions are just for you, the team's Challenge Advisor; please delete them once you have completed the steps below.**
>
> We've pre-populated this Challenge Project Overview page — which is what will be shared with your Break Through Tech student team in August — using the details from your submission form. You should have received an email inviting you to join this repo as a Collaborator, enabling you to add files and make edits.
> 
> In order for your project to be finalized and assigned to a team, please:
> 1. **Review all sections below** and update or expand any content as needed, making sure to address the SME Feedback in the section immediately below. Look for square brackets to find the places below that require additional inputs from you (e.g., "About [Company / Org Name]").
> 2. **Add your dataset** to the [data folder](data) in this repo.
> 3. **Close the Issue assigned to you in this repo** to let us know that you have made your edits and the overview page is ready for final review. You can do this by going to the _Issues_ tab in the top left section of the menu above, add a comment that says "CA review complete", and click the button to Close the Issue. 
>
> If you're unfamiliar with how to edit a page like this in GitHub, check out [this tutorial](https://ubc-lib-geo.github.io/gis-workshop-waml-template/content/handson/edit-readme.html) for a quick overview (start with step 2 and only edit this page), and [this guide](https://ubc-lib-geo.github.io/gis-workshop-waml-template/content/markdown.html) on how to use Markdown to compose text.
>
>
> ❌ Remember that this is a public repo. Do NOT include: Proprietary data, PII, API keys, credentials, or anything confidential.

---
## 📋 BTT Internal Evaluation Notes
*(This section is for BTT staff and CAs only — remove before sharing with students)*

### Technical Vetting
| Check | Status | Notes |
| :--- | :--- | :--- |
| Python Compatibility | 🟢 | Fully compliant, as shifting from live async API wrappers and complex VLM orchestration to static pre-cached subsets and deterministic math loops removes execution-blocking dependencies in free-tier Colab environments. |
| Data Readiness | 🟢  | Highly accessible, as swapping live multi-modal web-scraping and live USDA endpoints for a pre-cached local JSON/CSV seed dataset ensures immediate pipeline ingestion. |
| Resource Check | 🟢 | The provision of a pre-cached local JSON/CSV file is a fully optimized replacement; live e-commerce API pipelines stay strictly within the compute, memory, and rate limits of Google Colab's free tier. |

### Internal Scores
- **Student Fit Score:** 7/10
- **Technical Depth Score:** 8/10
- **Overall Recommendation:** REVISE

### Advisor Feedback Draft
The project demonstrates strong technical ambition, particularly in using Python for deterministic math to avoid LLM hallucinations. To succeed, please consider these two adjustments: first, restrict the agentic complexity by replacing multi-agent frameworks with a simpler ReAct pattern to ensure stability; second, swap proprietary LLM calls for a high-quality local model (e.g., Llama-3-8B via Ollama or HuggingFace) to eliminate dependency on paid APIs and ensure the project remains free-tier compliant. I look forward to seeing your refined project plan.

---

# Dynamic Nutrition Orchestrator: A Trustworthy, Multi-Agent System for High-Protein Constraint Optimization

**Company / Org:** Other  
**Challenge Advisor:** FNU Sakshi, sakshi.lindner@gmail.com  
**Program:** Break Through Tech AI Studio - Fall 2026  

---

## 🏢 About Other
This organization operates in the health-tech sector, focusing on personalized nutrition and dietary wellness technology. The team aims to bridge the gap between traditional meal planning and data-driven precision by leveraging multi-agent systems to solve complex dietary constraint problems.

---

## 🎯 The Challenge
### Project Summary
This project involves building a Tool-Augmented Generation (TAG) system to automate high-protein Indian vegetarian meal planning while ensuring zero-hallucination arithmetic. By utilizing a hybrid architecture that pairs local recipe templates with real-time USDA nutrient density data, the team will develop a system capable of dynamically scaling ingredients to meet strict daily macro targets.

### Success Criteria
1)Macro Optimization Precision: The final orchestrator must achieve a Mean Absolute Error (MAE) of $< 2\%$ across a full 7-day generation cycle. If the target window requires exactly 140g of protein per day, the final composite calculations must consistently land between 137.2g and 142.8g based on USDA data.
2)Entity Resolution Accuracy (F1-Score): The team’s string-matching and vector embedding pipeline must achieve an F1-score of $> 90\%$ on an unseen validation set of 30 common Indian vegetarian ingredients.
3)Scheduling Constraint Adherence: The algorithm must demonstrate 100% compliance with zero-repeat ingredient logic rules across any consecutive 48-hour block to guarantee real-world lifestyle variety.

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

**ML Problem Type:** [e.g., Classification, Regression, NLP, Computer Vision, LLM/RAG]

**Recommended Libraries:**
- [e.g., pandas, scikit-learn, TensorFlow, Hugging Face]

**Evaluation Metrics:**
- [e.g., Accuracy, Precision/Recall, RMSE, BLEU score]
  
---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project:
Purpose : https://www.youtube.com/watch?v=MxV7L3rvgRw&t=5s

**Background Reading:**
- [e.g., Link to an article or blog post about the problem domain]
- [e.g., Link to an industry report or case study]
- Similar solution in market : https://www.hungryroot.com/?utm_source=bing&utm_medium=paid%20search&utm_campaign=409491910_1142394305641669&utm_content=ai%20for%20meal%20planning&wm_source=microsoft&wm_medium=ads&wm_ad_id=71399799407238&msclkid=08f58e2a2b2a141783b0e4ad111565f7

**Technical Tutorials:**
- [e.g., Link to a free tutorial on the ML technique(s) involved]
- [e.g., Link to documentation for a key library or tool]
- Hugging Face model Quantization : https://huggingface.co/docs/transformers/main/en/quantization/overview

**Code Examples:**
- [e.g., Link to a relevant GitHub repo]
- [e.g., Link to a sample implementation or starter code]
- Loading Huggingface models : https://huggingface.co/docs/transformers/models

**Other:**
- USDA API key info : https://fdc.nal.usda.gov/api-guide?ref=apitemple
- USDA Data Documentation : https://fdc.nal.usda.gov/data-documentation 
*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🤝 How We'll Work Together

**Official check-ins:** During our biweekly 45-minute AI Studio Lab Section meeting block (2nd and 4th week of every month)

 **Other ways to reach out to me with questions (in order of priority):** 
* [ Your team's channel within Break Through Tech’s Discord space]
* [sakshi.lindner@gmail.com; please copy your teammates and AI Studio Coach]
* [Request a team check-in on Zoom]
* [Note: I will aim to respond within 48 hours. Please reach out to your AI Studio Coach with urgent questions.]

> 💡 **Challenge Advisor: Please update the above based on your availability and preference. If you are not able to answer questions or meet with fellows outside of the biweekly Lab Section check-ins, simply write in "N/A (only available during the official check-in times)"**

**Recommended free coding / collaboration tools**
* […]
* […]

---

## 🚀 Getting Started

1. **Review this overview document** and note any questions for our first meeting
2. **Begin reviewing the dataset** using the link above
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

I’m excited to work with you!

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th (Break Through Tech’s Bridge to Studio - Session C). 
