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
    
    # Helper to check lists of terms
    def has_any(text, terms):
        # use word boundaries or just simple in
        # For 'ab' and 'ag', simple 'in' might match 'swab' or 'flag'. 
        # So we pad with spaces: f" {term} " or check boundaries.
        import re
        for t in terms:
            if re.search(r'\b' + re.escape(t) + r'\b', text):
                return True
        return False

    # 1. Method Conflict
    lab_is_ag = has_any(lab, ["antigen", "ag"])
    lab_is_ab = has_any(lab, ["antibody", "ab", "igm", "igg"])
    match_is_ag = has_any(matched, ["antigen", "ag"])
    match_is_ab = has_any(matched, ["antibody", "ab", "igm", "igg", "igg+igm"])

    if lab_is_ag and match_is_ab: return True
    if lab_is_ab and match_is_ag: return True
    
    lab_is_naat = has_any(lab, ["dna", "naat", "pcr", "rna"])
    match_is_culture = has_any(matched, ["culture"])
    match_is_stain = has_any(matched, ["stain", "smear", "microscopic", "microscopy"])
    
    if lab_is_naat and (match_is_culture or match_is_ab or match_is_ag or match_is_stain): return True
    
    lab_is_culture = has_any(lab, ["culture"])
    if lab_is_culture and (match_is_stain or lab_is_naat or match_is_ab or match_is_ag): return True
    
    # 2. Pathogen Conflict
    # Get all words longer than 3
    words = [w for w in lab.replace('/', ' ').replace('-', ' ').split() if len(w) > 3]
    ignore_words = ["blood", "urine", "stool", "culture", "serum", "tissue", "wound", "respiratory", "other", "bacterial", "viral", "fungal", "parasite", "fluid", "swab", "smear", "stain", "naat", "test", "testing", "panel", "screen", "detection", "examination", "drug", "susceptibility", "complex", "disease", "infection"]
    
    # Filter to only potential pathogen words
    pathogen_words = [w for w in words if w not in ignore_words]
    
    if len(pathogen_words) > 0:
        first_pathogen = pathogen_words[0]
        # Handle variations like mycobacterial -> mycobacter
        prefix = first_pathogen[:6]
        if prefix not in matched:
            return True 
            
        # Check species if available (e.g. clostridium perfringens vs tetani)
        if len(pathogen_words) > 1:
            second_pathogen = pathogen_words[1]
            if len(second_pathogen) > 3 and second_pathogen not in ["spp.", "spp", "species"]:
                prefix2 = second_pathogen[:5]
                if prefix2 not in matched:
                    # Only reject if the matched text has a specific different species
                    # We can't strictly reject if missing, because TMLT might just say "Clostridium sp"
                    # But if TMLT says "tetani", it's a mismatch.
                    if " sp " not in matched and " sp." not in matched and "species" not in matched:
                        if "virus" not in second_pathogen:
                            pass # Too complex to strict reject, let it pass and review

    # 3. Specimen Strict Conflict
    if has_any(lab, ["stool", "feces"]) and has_any(matched, ["blood", "serum", "plasma", "csf"]): return True
    if has_any(lab, ["blood", "serum", "plasma"]) and has_any(matched, ["stool", "urine", "sputum", "feces"]): return True
    if has_any(lab, ["csf"]) and has_any(matched, ["stool", "blood", "urine", "sputum"]): return True
    
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
