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

def is_hard_conflict(lab_item, sct_fsn):
    lab = str(lab_item).lower().replace('/', ' ').replace('-', ' ')
    sct = str(sct_fsn).lower().replace('/', ' ').replace('-', ' ')
    
    words = [w for w in lab.split() if len(w) > 3]
    ignore_words = ["blood", "urine", "stool", "culture", "serum", "tissue", "wound", "respiratory", "other", "bacterial", "viral", "fungal", "parasite", "fluid", "swab", "smear", "stain", "naat", "test", "testing", "panel", "screen", "detection", "examination", "drug", "susceptibility", "complex", "disease", "infection", "anti", "antibodies", "antibody", "antigen", "identified", "specific", "organism", "method", "microscopy", "microscopic", "observation", "procedure", "measurement"]
    
    pathogen_words = [w for w in words if w not in ignore_words]
    
    # Check Antigen vs Antibody first
    lab_ag = "antigen" in lab or " ag " in lab
    lab_ab = "antibody" in lab or " ab " in lab or "igm" in lab or "igg" in lab
    sct_ag = "antigen" in sct or " ag " in sct
    sct_ab = "antibody" in sct or " ab " in sct or "igm" in sct or "igg" in sct
    
    if (lab_ag and sct_ab) or (lab_ab and sct_ag):
        return True

    if not pathogen_words:
        return False
        
    first_pathogen = pathogen_words[0]
    prefix = first_pathogen[:5]
    
    general_terms = ["bacteria", "virus", "fungus", "fungi", "parasite", "ova", "pathogen", "organism"]
    
    if prefix not in sct:
        if not any(g in sct for g in general_terms):
            return True 
            
    return False

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
    return re.sub(r'\s*\([^)]*\)$', '', fsn).strip()

sct_df['clean_term'] = sct_df['FSN'].apply(clean_fsn)
sct_df = sct_df[sct_df['clean_term'] != '']
sct_df = sct_df.reset_index(drop=True)

print(f"Total SNOMED candidates after strict filtering: {len(sct_df)}")

print("Loading Semantic Model (SapBERT)...")
MODEL_NAME = 'cambridgeltl/SapBERT-from-PubMedBERT-fulltext'
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
sct_embs = model.encode(sct_texts, batch_size=32, show_progress_bar=True)

print("Generating Lab embeddings...")
lab_embs = model.encode(unique_labs, batch_size=16, show_progress_bar=False)

print("Calculating similarities and matching (Top-5 with Rules)...")
top_k = 5

# Build a mapping dictionary for fast lookup
lab_to_snomed_map = {}
for i, lab in enumerate(unique_labs):
    # Calculate similarity for just THIS ONE lab item to save memory (prevents 400MB+ alloc error)
    row_sims = cosine_similarity(lab_embs[i:i+1], sct_embs)[0]
    # Find top_k indices efficiently without allocating a huge array
    top_k_indices_row = np.argpartition(-row_sims, top_k)[:top_k]
    # Sort only those top_k elements
    top_k_indices_row = top_k_indices_row[np.argsort(-row_sims[top_k_indices_row])]
    
    best_candidate = None
    best_score = 0
    passed_rules = False
    
    for idx in top_k_indices_row:
        score = row_sims[idx]
        row_sct = sct_df.iloc[idx]
        
        is_conflict = is_hard_conflict(lab, row_sct['FSN'])
        
        if not is_conflict:
            best_candidate = row_sct
            best_score = score
            passed_rules = True
            break
            
    # If all Top-5 failed the rules, just pick the top 1 and mark as rejected
    if not passed_rules:
        idx = top_k_indices_row[0]
        best_candidate = sct_df.iloc[idx]
        best_score = row_sims[idx]
        
    score = round(float(best_score), 4)
    
    if not passed_rules or score < 0.50:
        label = "Rejected"
        val_flag = "Rejected by Rules"
        conceptId = "-"
        fsn = "-"
    elif score >= 0.85:
        label = "Very High Confidence"
        val_flag = "Passed Rules"
        conceptId = best_candidate['conceptId']
        fsn = best_candidate['FSN']
    elif score >= 0.70:
        label = "High Confidence"
        val_flag = "Passed Rules"
        conceptId = best_candidate['conceptId']
        fsn = best_candidate['FSN']
    else:
        label = "Medium Confidence"
        val_flag = "Passed Rules"
        conceptId = best_candidate['conceptId']
        fsn = best_candidate['FSN']
        
    lab_to_snomed_map[lab] = {
        'conceptId': conceptId,
        'FSN': fsn,
        'Similarity_Score': score,
        'AI_Label': label,
        'Validation_Flag': val_flag
    }

print("Constructing final DataFrame...")
results = []
for index, row in icd_lab_df.iterrows():
    lab_item = row['Lab_Item']
    
    if pd.isna(lab_item) or str(lab_item).strip() == "" or str(lab_item).strip() == "-":
        results.append({
            'ICD-10': row['ICD-10'],
            'รายการตรวจ lab': lab_item if pd.notna(lab_item) else "-",
            'รหัส ConceptID': '-',
            'ชื่อ FSN': '-',
            'Similarity_Score': '-',
            'AI_Label': '-',
            'Validation_Flag': '-'
        })
    else:
        match_info = lab_to_snomed_map.get(lab_item, {})
        
        results.append({
            'ICD-10': row['ICD-10'],
            'รายการตรวจ lab': lab_item,
            'รหัส ConceptID': match_info.get('conceptId', ''),
            'ชื่อ FSN': match_info.get('FSN', ''),
            'Similarity_Score': match_info.get('Similarity_Score', ''),
            'AI_Label': match_info.get('AI_Label', ''),
            'Validation_Flag': match_info.get('Validation_Flag', '')
        })

final_df = pd.DataFrame(results)
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "SNOMED", "ICD_to_SNOMED.xlsx")
os.makedirs(os.path.dirname(output_excel), exist_ok=True)
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 4 Completed successfully!")
