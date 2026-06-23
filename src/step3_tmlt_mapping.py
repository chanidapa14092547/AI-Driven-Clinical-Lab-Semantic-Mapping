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

# Create rich semantic text by combining all 4 columns for TMLT
def create_rich_text(row):
    parts = []
    if pd.notna(row.get('TMLT_Name')): parts.append(f"Name: {row['TMLT_Name']}")
    if pd.notna(row.get('COMPONENT')): parts.append(f"Component: {row['COMPONENT']}")
    if pd.notna(row.get('SPECIMEN')): parts.append(f"Specimen: {row['SPECIMEN']}")
    if pd.notna(row.get('METHOD')): parts.append(f"Method: {row['METHOD']}")
    return " | ".join(parts)

tmlt_df['Rich_Text'] = tmlt_df.apply(create_rich_text, axis=1)

print("Loading Semantic Model...")
# Use clinical BERT
try:
    model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')
except:
    model = SentenceTransformer('all-MiniLM-L6-v2')

unique_labs = icd_lab_df['Lab_Item'].dropna().unique().tolist()
tmlt_texts = tmlt_df['Rich_Text'].tolist()

print("Generating TMLT embeddings (this may take a minute)...")
tmlt_embs = model.encode(tmlt_texts, batch_size=128, show_progress_bar=True)

print("Generating Lab embeddings...")
lab_embs = model.encode(unique_labs, batch_size=64, show_progress_bar=False)

print("Calculating similarities and matching...")
similarities = cosine_similarity(lab_embs, tmlt_embs)
best_match_indices = np.argmax(similarities, axis=1)
best_match_scores = np.max(similarities, axis=1)

# Build a mapping dictionary for fast lookup
lab_to_tmlt_map = {}
for i, lab in enumerate(unique_labs):
    best_idx = best_match_indices[i]
    matched_row = tmlt_df.iloc[best_idx]
    score = round(best_match_scores[i], 4)
    
    # AI Labeling logic
    label = "High Confidence" if score >= 0.85 else "Review Required"
    
    lab_to_tmlt_map[lab] = {
        'TMLT_Code': matched_row.get('TMLT_Code', ''),
        'TMLT_Name': matched_row.get('TMLT_Name', ''),
        'COMPONENT': matched_row.get('COMPONENT', ''),
        'LOINC_NUM': matched_row.get('LOINC_NUM', ''),
        'CGD_CODE': matched_row.get('CGD_CODE', ''),
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
            'รหัส TMLT': '-',
            'ชื่อ TMLT': '-',
            'Component TMLT': '-',
            'รหัส LOINC_NUM': '-',
            'รหัส CGD_CODE': '-',
            'Similarity_Score': '-',
            'AI_Label': '-'
        })
    else:
        match_info = lab_to_tmlt_map.get(lab_item, {})
        results.append({
            'ICD-10': row['ICD-10'],
            'รายการตรวจ lab': lab_item,
            'รหัส TMLT': match_info.get('TMLT_Code', ''),
            'ชื่อ TMLT': match_info.get('TMLT_Name', ''),
            'Component TMLT': match_info.get('COMPONENT', ''),
            'รหัส LOINC_NUM': match_info.get('LOINC_NUM', ''),
            'รหัส CGD_CODE': match_info.get('CGD_CODE', ''),
            'Similarity_Score': match_info.get('Similarity_Score', 0),
            'AI_Label': match_info.get('AI_Label', '')
        })

final_df = pd.DataFrame(results)

# Clean up any potential NaNs in the output to be "-"
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "ICD_to_TMLT.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 3 Completed successfully!")
