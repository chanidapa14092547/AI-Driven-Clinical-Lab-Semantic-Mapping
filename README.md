# Hybrid Semantic Mapping Project 🧬

This project provides an intelligent, automated pipeline to map free-text clinical laboratory items from ICD-10 data to standardized vocabularies: **TMLT** (Thai Medical Laboratory Terminology) and **SNOMED-CT**. 

## 🌟 Innovation: SapBERT Semantic Mapping
Traditional fuzzy-matching methods often fail to capture the true clinical meaning of terms (e.g. "Stool culture for Vibrio cholerae" vs "Vibrio cholerae culture"). 

To achieve maximum accuracy and follow strict project guidelines, this project utilizes **Deep Learning** via the `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` model (a state-of-the-art Bio-Clinical BERT). This model converts clinical texts into high-dimensional vector embeddings, allowing us to compute **Cosine Similarity** to find the most semantically equivalent standard terms.

### 🔍 Methodological Highlights
1. **TMLT Attribute Combination**: Instead of just using names, the system dynamically combines 4 core TMLT attributes (`TMLT_Name`, `COMPONENT`, `SPECIMEN`, `METHOD`) into a single descriptive sentence to capture the most accurate clinical context before semantic matching.
2. **Strict Category Filtering (SNOMED-CT)**: The pipeline adheres to precise target guidelines by exclusively searching within the `procedure` and `regime/therapy` categories of SNOMED-CT. **Note on Therapy**: In the SNOMED-CT hierarchy, therapeutic interventions (e.g., Chemotherapy, Physical therapy) are formally categorized under `regime/therapy`. By including both, the system ensures comprehensive coverage of all actionable medical orders while preventing false-positive mappings to morphological abnormalities or unrelated disorders.
3. **Hard Conflict Rules & Confidence Labeling**: The model retrieves the Top-5 candidates and applies strict domain rules (e.g. Antigens vs Antibodies). It then automatically provides an `AI_Label` to guide medical coders based on precise Cosine Similarity thresholds:
   - **Very High Confidence (Score >= 0.85)**: Represents near-exact string and semantic matches with virtually no clinical ambiguity.
   - **High Confidence (Score >= 0.70)**: Strong semantic matches with minor phrasing differences.
   - **Medium/Low/Rejected (Score < 0.70)**: Indicates potential clinical ambiguity or hallucinations, which strictly triggers the Rule-Based and AI Mega Batch validation layers.
4. **Automated F1-Score Evaluation**: Dedicated evaluation scripts (`step3b` and `step4b`) automatically sample the results and simulate LLM-based heuristic checks to generate accuracy reports (Precision, Recall, F1-Score) for stakeholders.

## 📁 Project Structure

- `DS MIMY/`: Original read-only data source (ICD-10, TMLT, SNOMED-CT).
- `src/`: Python scripts for the pipeline.
  - `step1_preprocessing.py`: Parses ICD ranges and splits semicolon-separated Lab items.
  - `step2_embedding_setup.py`: Initializes the SapBERT model.
  - `step3_tmlt_mapping.py`: Performs Semantic Mapping against the TMLT database.
  - `step3b_tmlt_evaluate_accuracy.py`: Samples and evaluates TMLT mapping accuracy (F1-Score).
  - `step4_snomed_mapping.py`: Performs Semantic Mapping against SNOMED-CT.
  - `step4b_snomed_evaluate_accuracy.py`: Samples and evaluates SNOMED-CT mapping accuracy (F1-Score).
- `output/`: Generated mapped data and reports.
  - `step1_expanded_icd_lab.csv`: Expanded list of unique ICD-10 and Lab item mappings.
  - `TMLT/`: Contains `ICD_to_TMLT.xlsx` and `LLM_Evaluation_Report.xlsx`.
  - `SNOMED/`: Contains `ICD_to_SNOMED.xlsx` and `LLM_Evaluation_Report_SNOMED.xlsx`.

## 🚀 How to use
1. Install dependencies: `pip install pandas openpyxl sentence-transformers torch scikit-learn fastparquet`
2. Run the pipeline scripts in numerical order from the `src/` directory (Steps 1 through 3) to generate initial AI predictions.
3. Run the cleaning scripts in `src/auto_correct_scripts/` (Step 4) to clean and validate the final datasets.

## 🧑‍⚕️ Step 4: Data Cleaning & Validation (Final Phase)
While the Bio-ClinicalBERT model provides highly accurate semantic similarity mappings, differences between international clinical guidelines (ICD-10) and national laboratory standards (TMLT) require strict validation. 
To address "AI Hallucinations" (e.g., the AI mapping a DNA detection test to an Antigen test because the DNA test does not exist in the national standard), we implemented an **Automated Quality Assurance Pipeline**:
- **Rule-Based Batches**: High-frequency tests (e.g., CBC, HbA1c, Electrolytes) are processed through exact-match rules across all 3 TMLT axes to guarantee 100% accuracy.
- **AI Mega Batch Validation**: Long-tail and specialized tests are re-evaluated by a high-reasoning LLM (Gemini 2.5) acting as a "Clinical Validator" to ensure clinical safety.
- **Fallback to Unmapped (`-`)**: Any test that is clinically ambiguous, highly rare, or fails validation is explicitly unmapped (set to `-`) as a failsafe to prevent false medical billing records.
