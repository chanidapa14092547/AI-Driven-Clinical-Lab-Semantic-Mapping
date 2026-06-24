# Hybrid Semantic Mapping Project 🧬

This project provides an intelligent, automated pipeline to map free-text clinical laboratory items from ICD-10 data to standardized vocabularies: **TMLT** (Thai Medical Laboratory Terminology) and **SNOMED-CT**. 

## 🌟 Innovation: Bio-ClinicalBERT Semantic Mapping
Traditional fuzzy-matching methods often fail to capture the true clinical meaning of terms (e.g. "Stool culture for Vibrio cholerae" vs "Vibrio cholerae culture"). 

To achieve maximum accuracy and follow strict project guidelines, this project utilizes **Deep Learning** via the `pritamdeka/S-PubMedBert-MS-MARCO` model (a state-of-the-art Bio-Clinical BERT). This model converts clinical texts into high-dimensional vector embeddings, allowing us to compute **Cosine Similarity** to find the most semantically equivalent standard terms.

### 🔍 Methodological Highlights
1. **TMLT Attribute Combination**: Instead of just using names, the system dynamically combines 4 core TMLT attributes (`TMLT_Name`, `COMPONENT`, `SPECIMEN`, `METHOD`) into a single descriptive sentence to capture the most accurate clinical context before semantic matching.
2. **Strict Category Filtering (SNOMED-CT)**: The pipeline adheres to precise target guidelines by exclusively searching within the `procedure` and `regime/therapy` categories of SNOMED-CT, preventing false-positive mappings to morphological abnormalities or unrelated disorders.
3. **Automated AI Labeling (Label Set)**: The model automatically evaluates its own predictions and provides an `AI_Label` (`High Confidence` for scores >= 0.85, and `Review Required` for scores < 0.85) to guide medical coders, directly answering the requirement to "use AI to check the results as a label set".

## 📁 Project Structure

- `DS MIMY/`: Original read-only data source (ICD-10, TMLT, SNOMED-CT).
- `src/`: Python scripts for the pipeline.
  - `step1_preprocessing.py`: Parses ICD ranges and splits semicolon-separated Lab items.
  - `step2_embedding_setup.py`: Initializes the Bio-ClinicalBERT model.
  - `step3_tmlt_mapping.py`: Performs Semantic Mapping against the TMLT database (Using combined 4 attributes).
  - `step4_snomed_mapping.py`: Performs Semantic Mapping against SNOMED-CT (Strictly Procedure & Regime/Therapy).
- `output/`: Generated mapped data.
  - `step1_expanded_icd_lab.csv`: Expanded list of unique ICD-10 and Lab item mappings.
  - `ICD_to_TMLT.xlsx`: Final mapped results to TMLT, exactly matching the requested column structure.
  - `ICD_to_SNOMED.xlsx`: Final mapped results to SNOMED-CT, exactly matching the requested column structure.

## 🚀 How to use
1. Install dependencies: `pip install pandas openpyxl sentence-transformers torch scikit-learn fastparquet`
2. Run the pipeline scripts in numerical order from the `src/` directory.

## 🧑‍⚕️ Manual QA & Expert Review (Current Phase)
While the Bio-ClinicalBERT model provides highly accurate semantic similarity mappings, differences between international clinical guidelines (ICD-10) and national laboratory standards (TMLT) require expert review. 
To address "AI Hallucinations" (e.g., the AI mapping a DNA detection test to an Antigen test because the DNA test does not exist in the national standard), we have implemented a **Manual Quality Assurance** phase:
- **Line-by-Line Review**: Expert medical coders review the AI's output (`ICD_to_TMLT.xlsx`) in batches.
- **Strict Method & Specimen Rules**: Ensuring that the requested specimen (e.g., Sputum vs. CSF) and method (e.g., Culture vs. NAAT) precisely match the TMLT constraints.
- **Fallback to Unmapped (`-`)**: Any test that cannot be safely and clinically mapped to the TMLT standard is explicitly unmapped (set to `-`) to prevent false or non-compliant medical billing records.
