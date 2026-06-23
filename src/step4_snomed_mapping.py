import pandas as pd
import os
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import glob
import re

base_dir = r"C:\Users\USER\Downloads\DS MIMY\Mapping-Project"
data_dir = os.path.join(base_dir, "DS MIMY")
output_dir = os.path.join(base_dir, "output")

print("Loading step 1 data...")
icd_lab_df = pd.read_csv(os.path.join(output_dir, "step1_expanded_icd_lab.csv"))

print("Loading SNOMED-CT data...")
sct_dir = os.path.join(data_dir, "sct_concept")
parquet_files = glob.glob(os.path.join(sct_dir, "*.parquet"))
dfs = [pd.read_parquet(f) for f in parquet_files]
sct_df = pd.concat(dfs, ignore_index=True)

# Filter active concepts and relevant categories
sct_df = sct_df[sct_df['active'] == 1]
target_categories = ['procedure', 'observable entity']
sct_df = sct_df[sct_df['category'].isin(target_categories)]

# Clean FSN to remove semantic tags (e.g. " (procedure)") for better embedding match
def clean_fsn(fsn):
    if not isinstance(fsn, str):
        return ""
    # Remove trailing parentheses and their contents
    return re.sub(r'\s*\([^)]*\)$', '', fsn).strip()

sct_df['clean_term'] = sct_df['FSN'].apply(clean_fsn)
# Drop empty
sct_df = sct_df[sct_df['clean_term'] != '']

print(f"Total SNOMED candidates after filtering: {len(sct_df)}")

print("Loading Semantic Model...")
try:
    model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')
except:
    model = SentenceTransformer('all-MiniLM-L6-v2')

# 1. Get unique Lab items to speed up processing
unique_labs = icd_lab_df['Lab_Item'].dropna().unique().tolist()
print(f"Total rows: {len(icd_lab_df)}, Unique Lab items to process: {len(unique_labs)}")

# 2. Get SNOMED texts
sct_texts = sct_df['clean_term'].tolist()

print("Generating SNOMED embeddings (this will take 15-20 minutes)...")
sct_embs = model.encode(sct_texts, batch_size=128, show_progress_bar=True)

print("Generating Lab embeddings...")
lab_embs = model.encode(unique_labs, batch_size=64, show_progress_bar=False)

print("Calculating similarities and matching...")
# Compute similarity in chunks if memory is an issue, but 1700 x 60k is around 400MB, fits in RAM
similarities = cosine_similarity(lab_embs, sct_embs)
best_match_indices = np.argmax(similarities, axis=1)
best_match_scores = np.max(similarities, axis=1)

# Build a mapping dictionary for fast lookup
lab_to_snomed_map = {}
for i, lab in enumerate(unique_labs):
    best_idx = best_match_indices[i]
    matched_row = sct_df.iloc[best_idx]
    
    lab_to_snomed_map[lab] = {
        'conceptId': matched_row['conceptId'],
        'FSN': matched_row['FSN'],
        'category': matched_row['category'],
        'Similarity_Score': round(best_match_scores[i], 4)
    }

print("Constructing final DataFrame...")
results = []
for index, row in icd_lab_df.iterrows():
    lab_item = row['Lab_Item']
    match_info = lab_to_snomed_map.get(lab_item, {})
    
    results.append({
        'ICD-10': row['ICD-10'],
        'รายการตรวจ lab': lab_item,
        'SNOMED_ConceptId': match_info.get('conceptId', ''),
        'SNOMED_FSN': match_info.get('FSN', ''),
        'SNOMED_Category': match_info.get('category', ''),
        'Similarity_Score': match_info.get('Similarity_Score', 0)
    })

final_df = pd.DataFrame(results)

output_excel = os.path.join(output_dir, "ICD_to_SNOMED.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 4 Completed successfully!")
