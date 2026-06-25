import pandas as pd
import os
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "DS MIMY"
output_dir = base_dir / "output"

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
def is_hard_conflict(lab_text, matched_text):
    lab = str(lab_text).lower()
    matched = str(matched_text).lower()
    
    # 1. Method Conflict
    if "antigen" in lab and "antibody" in matched: return True
    if "antibody" in lab and "antigen" in matched: return True
    
    lab_is_naat = any(x in lab for x in ["dna", "naat", "pcr", "rna"])
    if lab_is_naat and ("culture" in matched or "antibody" in matched or "igm" in matched or "igg" in matched): return True
    
    if "culture" in lab and any(x in matched for x in ["stain", "smear", "microscopic", "dna", "naat", "antibody", "igm"]): return True
    
    # 2. Pathogen Conflict
    words = [w for w in lab.replace('/', ' ').split() if len(w) > 3]
    if words:
        first_word = words[0]
        ignore_words = ["blood", "urine", "stool", "culture", "serum", "tissue", "wound", "respiratory", "csf", "other", "bacterial", "viral", "fungal", "parasite", "fluid", "swab", "smear", "stain", "naat", "pcr", "from", "with", "test", "testing", "panel", "screen"]
        if first_word not in ignore_words:
            if first_word not in matched:
                return True 

    # 3. Specimen Strict Conflict
    if "stool" in lab and any(x in matched for x in ["blood", "serum", "plasma", "csf"]): return True
    if "blood" in lab and any(x in matched for x in ["stool", "urine", "sputum"]): return True
    if "csf" in lab and any(x in matched for x in ["stool", "blood", "urine"]): return True
    
    return False

top_k = 5
top_k_indices = np.argsort(similarities, axis=1)[:, -top_k:][:, ::-1]

# Build a mapping dictionary for fast lookup
lab_to_tmlt_map = {}
for i, lab in enumerate(unique_labs):
    found_valid_match = False
    
    for rank in range(top_k):
        idx = top_k_indices[i, rank]
        score = similarities[i, idx]
        
        if score < 0.85:
            break
            
        matched_row = tmlt_df.iloc[idx]
        matched_text = f"{matched_row.get('TMLT_Name', '')} {matched_row.get('COMPONENT', '')} {matched_row.get('SPECIMEN', '')} {matched_row.get('METHOD', '')}"
        
        if not is_hard_conflict(lab, matched_text):
            lab_to_tmlt_map[lab] = {
                'TMLT_Code': matched_row.get('TMLT_Code', ''),
                'TMLT_Name': matched_row.get('TMLT_Name', ''),
                'COMPONENT': matched_row.get('COMPONENT', ''),
                'LOINC_NUM': matched_row.get('LOINC_NUM', ''),
                'CGD_CODE': matched_row.get('CGD_CODE', ''),
                'Similarity_Score': round(score, 4),
                'AI_Label': "High Confidence" if score >= 0.90 else "Review Required",
                'Validation_Flag': "Passed Rules"
            }
            found_valid_match = True
            break
            
    if not found_valid_match:
        lab_to_tmlt_map[lab] = {
            'TMLT_Code': '-', 'TMLT_Name': '-', 'COMPONENT': '-', 'LOINC_NUM': '-', 'CGD_CODE': '-',
            'Similarity_Score': '-', 'AI_Label': '-', 'Validation_Flag': 'Rejected by Rules'
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
            'AI_Label': '-',
            'Validation_Flag': '-'
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
            'AI_Label': match_info.get('AI_Label', ''),
            'Validation_Flag': match_info.get('Validation_Flag', '')
        })

final_df = pd.DataFrame(results)

# Clean up any potential NaNs in the output to be "-"
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "ICD_to_TMLT.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 3 Completed successfully!")
