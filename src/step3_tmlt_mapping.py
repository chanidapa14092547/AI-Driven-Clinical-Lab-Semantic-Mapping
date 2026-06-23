import pandas as pd
import os
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

base_dir = r"C:\Users\USER\Downloads\DS MIMY\Mapping-Project"
data_dir = os.path.join(base_dir, "DS MIMY")
output_dir = os.path.join(base_dir, "output")

print("Loading step 1 data...")
icd_lab_df = pd.read_csv(os.path.join(output_dir, "step1_expanded_icd_lab.csv"))

print("Loading TMLT data...")
tmlt_df = pd.read_excel(os.path.join(data_dir, "TMLT_FULL20260602.xlsx"))
# Clean TMLT dataframe
tmlt_df = tmlt_df.dropna(subset=['TMLT_Name'])
tmlt_df['TMLT_Name_clean'] = tmlt_df['TMLT_Name'].astype(str).str.strip()

print("Loading Semantic Model...")
try:
    model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')
except:
    model = SentenceTransformer('all-MiniLM-L6-v2')

# 1. Get unique Lab items to speed up processing
unique_labs = icd_lab_df['Lab_Item'].dropna().unique().tolist()
print(f"Total rows: {len(icd_lab_df)}, Unique Lab items to process: {len(unique_labs)}")

# 2. Get TMLT texts
tmlt_texts = tmlt_df['TMLT_Name_clean'].tolist()
print(f"Total TMLT records: {len(tmlt_texts)}")

print("Generating TMLT embeddings (this may take a minute)...")
tmlt_embs = model.encode(tmlt_texts, batch_size=64, show_progress_bar=False)

print("Generating Lab embeddings...")
lab_embs = model.encode(unique_labs, batch_size=64, show_progress_bar=False)

print("Calculating similarities and matching...")
# Compute similarity in chunks if memory is an issue, but arrays are small here
similarities = cosine_similarity(lab_embs, tmlt_embs)
best_match_indices = np.argmax(similarities, axis=1)
best_match_scores = np.max(similarities, axis=1)

# Build a mapping dictionary for fast lookup
lab_to_tmlt_map = {}
for i, lab in enumerate(unique_labs):
    best_idx = best_match_indices[i]
    matched_row = tmlt_df.iloc[best_idx]
    
    lab_to_tmlt_map[lab] = {
        'TMLT_Code': matched_row.get('TMLT_Code', ''),
        'TMLT_Name': matched_row.get('TMLT_Name', ''),
        'COMPONENT': matched_row.get('COMPONENT', ''),
        'LOINC_NUM': matched_row.get('LOINC_NUM', ''),
        'CGD_CODE': matched_row.get('CGD_CODE', ''),
        'Similarity_Score': round(best_match_scores[i], 4)
    }

print("Constructing final DataFrame...")
results = []
for index, row in icd_lab_df.iterrows():
    lab_item = row['Lab_Item']
    match_info = lab_to_tmlt_map.get(lab_item, {})
    
    results.append({
        'ICD-10': row['ICD-10'],
        'รายการตรวจ lab': lab_item,
        'รหัส TMLT': match_info.get('TMLT_Code', ''),
        'ชื่อ TMLT': match_info.get('TMLT_Name', ''),
        'Component TMLT': match_info.get('COMPONENT', ''),
        'รหัส LOINC_NUM': match_info.get('LOINC_NUM', ''),
        'รหัส CGD_CODE': match_info.get('CGD_CODE', ''),
        'Similarity_Score': match_info.get('Similarity_Score', 0)
    })

final_df = pd.DataFrame(results)

output_excel = os.path.join(output_dir, "ICD_to_TMLT.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 3 Completed successfully!")
