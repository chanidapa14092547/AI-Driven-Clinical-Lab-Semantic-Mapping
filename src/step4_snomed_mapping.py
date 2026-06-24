import pandas as pd
import os
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import glob
import re

from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "DS MIMY"
output_dir = base_dir / "output"

print("Loading step 1 data...")
icd_lab_df = pd.read_csv(os.path.join(output_dir, "step1_expanded_icd_lab.csv"))

print("Loading SNOMED-CT data...")
sct_dir = os.path.join(data_dir, "sct_concept")
parquet_files = glob.glob(os.path.join(sct_dir, "*.parquet"))
dfs = [pd.read_parquet(f) for f in parquet_files]
sct_df = pd.concat(dfs, ignore_index=True)

# STRICT FILTERING based on guidelines: 'procedure' and 'regime/therapy'
sct_df = sct_df[sct_df['active'] == 1]
target_categories = ['procedure', 'regime/therapy']
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

print(f"Total SNOMED candidates after strict filtering: {len(sct_df)}")

print("Loading Semantic Model...")
MODEL_NAME = 'pritamdeka/S-PubMedBert-MS-MARCO'
try:
    model = SentenceTransformer(MODEL_NAME)
except:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    MODEL_NAME = 'all-MiniLM-L6-v2'

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
similarities = cosine_similarity(lab_embs, sct_embs)
best_match_indices = np.argmax(similarities, axis=1)
best_match_scores = np.max(similarities, axis=1)

# Build a mapping dictionary for fast lookup
lab_to_snomed_map = {}
for i, lab in enumerate(unique_labs):
    best_idx = best_match_indices[i]
    matched_row = sct_df.iloc[best_idx]
    score = round(best_match_scores[i], 4)
    
    if score >= 0.90:
        label = "High Confidence"
    elif score >= 0.80:
        label = "Review Required"
    else:
        label = "Low Confidence"
    
    lab_to_snomed_map[lab] = {
        'conceptId': matched_row['conceptId'],
        'FSN': matched_row['FSN'],
        'Similarity_Score': score,
        'AI_Label': label
    }

print("Constructing final DataFrame...")
results = []
for index, row in icd_lab_df.iterrows():
    lab_item = row['Lab_Item']
    
    if pd.isna(lab_item) or str(lab_item).strip() == "":
        results.append({
            'ICD-10': row['ICD-10'],
            'รายการตรวจ lab': '-',
            'รหัส ConceptID': '-',
            'ชื่อ FSN': '-',
            'AI_Label': '-'
        })
    else:
        match_info = lab_to_snomed_map.get(lab_item, {})
        score_text = str(match_info.get('Similarity_Score', 0))
        mapping_code = f"Model: {MODEL_NAME} | Score: {score_text}"
        
        results.append({
            'ICD-10': row['ICD-10'],
            'รายการตรวจ lab': lab_item,
            'รหัส ConceptID': match_info.get('conceptId', ''),
            'ชื่อ FSN': match_info.get('FSN', ''),
            'AI_Label': match_info.get('AI_Label', '')
        })

final_df = pd.DataFrame(results)
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "ICD_to_SNOMED.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 4 Completed successfully!")
