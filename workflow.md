# 🧬 Hybrid Semantic Mapping Workflow

ICD-LAB Data
    ↓
1️⃣ **Preprocessing** (`step1`)
    - Expand semicolon-separated lab items
    ↓
2️⃣ **Semantic Embedding Setup** (`step2`)
    - Load `SapBERT` model
    ↓
3️⃣ **TMLT Semantic Mapping** (`step3`)
    - Combine 4 attributes (`TMLT_Name`, `COMPONENT`, `SPECIMEN`, `METHOD`)
    - Cosine Similarity (Top-5 search)
    - Hard Conflict Rules & AI Confidence Labeling
    ↓
3️⃣🅱️ **TMLT Accuracy Evaluation** (`step3b`)
    - Heuristic evaluation simulation
    - F1-Score Report Generation
    ↓
4️⃣ **SNOMED-CT Semantic Mapping** (`step4`)
    - Strict Category Filtering (Procedure / Regime)
    - Cosine Similarity (Top-5 search)
    - Hard Conflict Rules & AI Confidence Labeling
    ↓
4️⃣🅱️ **SNOMED Accuracy Evaluation** (`step4b`)
    - Heuristic evaluation simulation
    - F1-Score Report Generation
    ↓
5️⃣ **Export Final Results**
    - Cleaned output folders (`output/TMLT`, `output/SNOMED`)