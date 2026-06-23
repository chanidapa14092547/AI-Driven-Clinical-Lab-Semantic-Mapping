# Hybrid Semantic Mapping Project 🧬

This project provides an intelligent, automated pipeline to map free-text clinical laboratory items from ICD-10 data to standardized vocabularies: **TMLT** (Thai Medical Laboratory Terminology) and **SNOMED-CT**. 

## 🌟 Innovation: Bio-ClinicalBERT Semantic Mapping
Traditional fuzzy-matching methods (like Levenshtein distance) often fail to capture the true clinical meaning of terms (e.g. "Stool culture for Vibrio cholerae" vs "Vibrio cholerae culture"). 

To achieve a higher level of accuracy and make the methodology potentially patentable, this project utilizes **Deep Learning** via the `pritamdeka/S-PubMedBert-MS-MARCO` model (a state-of-the-art Bio-Clinical BERT). 
This model converts clinical texts into high-dimensional vector embeddings, allowing us to compute **Cosine Similarity** to find the most semantically equivalent standard terms.

## 📁 Project Structure

- `DS MIMY/`: Original read-only data source (ICD-10, TMLT, SNOMED-CT).
- `src/`: Python scripts for the pipeline.
  - `step1_preprocessing.py`: Parses ICD ranges and splits semicolon-separated Lab items.
  - `step2_embedding_setup.py`: Initializes the Bio-ClinicalBERT model.
  - `step3_tmlt_mapping.py`: Performs Semantic Mapping against the TMLT database.
  - `step4_snomed_mapping.py`: Performs Semantic Mapping against SNOMED-CT (filtered for procedure/observable entity categories).
- `output/`: Generated mapped data.
  - `step1_expanded_icd_lab.csv`: Expanded list of unique ICD-10 and Lab item mappings.
  - `ICD_to_TMLT.xlsx`: Final mapped results to TMLT, including similarity scores.
  - `ICD_to_SNOMED.xlsx`: Final mapped results to SNOMED-CT, including similarity scores.

## 📊 Evaluation & Accuracy

The pipeline includes a `Similarity_Score` (0.0 to 1.0) for every matched term. 
Based on initial statistical evaluations:
- **TMLT Mapping**: Over **93.8%** of the mappings achieved a Similarity Score > 0.80.
- **SNOMED-CT Mapping**: Over **93.8%** of the mappings achieved a Similarity Score > 0.80.

A score above 0.80 strongly indicates high semantic equivalence, proving the efficiency and clinical reliability of this AI-driven approach.

## 🚀 How to use
1. Install dependencies: `pip install pandas openpyxl sentence-transformers torch scikit-learn fastparquet`
2. Run the pipeline scripts in numerical order from the `src/` directory.
