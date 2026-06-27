import pandas as pd
import os
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from pathlib import Path
import difflib

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

print("Loading Semantic Model (SapBERT)...")
try:
    # Use SapBERT for State-of-the-art Medical Concept Normalization
    model = SentenceTransformer('cambridgeltl/SapBERT-from-PubMedBERT-fulltext')
except:
    print("Failed to load SapBERT. Falling back to BioBERT.")
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
    match_is_naat = has_any(matched, ["dna", "naat", "pcr", "rna"])
    lab_is_culture = has_any(lab, ["culture"])
    match_is_culture = has_any(matched, ["culture"])
    match_is_stain = has_any(matched, ["stain", "smear", "microscopic", "microscopy"])
    
    if lab_is_naat and (match_is_culture or match_is_ab or match_is_ag or match_is_stain): return True
    if lab_is_culture and (match_is_stain or match_is_naat or match_is_ab or match_is_ag): return True
    if lab_is_ag and match_is_stain: return True
    if lab_is_ab and match_is_stain: return True
    if has_any(lab, ["smear", "stain"]) and (match_is_culture or match_is_naat or match_is_ab or match_is_ag): return True
    
    # 2. Pathogen Conflict
    words = [w for w in lab.replace('/', ' ').replace('-', ' ').split() if len(w) > 3]
    ignore_words = ["blood", "urine", "stool", "culture", "serum", "tissue", "wound", "respiratory", "other", "bacterial", "viral", "fungal", "parasite", "fluid", "swab", "smear", "stain", "naat", "test", "testing", "panel", "screen", "detection", "examination", "drug", "susceptibility", "complex", "disease", "infection", "anti", "antibodies", "antibody", "antigen"]
    
    pathogen_words = [w for w in words if w not in ignore_words]
    general_terms = ["bacteria identified", "virus identified", "fungus identified", "fungi identified", "parasite", "ova", "pathogen", "microscopic observation", "organism specific culture", "culture", "identification"]
    
    if len(pathogen_words) > 0:
        first_pathogen = pathogen_words[0]
        prefix = first_pathogen[:6]
        
        if prefix not in matched:
            if not any(g in matched for g in general_terms):
                return True 
            
        if len(pathogen_words) > 1:
            second_pathogen = pathogen_words[1]
            if len(second_pathogen) > 3 and second_pathogen not in ["spp.", "spp", "species"]:
                prefix2 = second_pathogen[:5]
                if prefix2 not in matched:
                    if " sp " not in matched and " sp." not in matched and "species" not in matched:
                        if not any(g in matched for g in general_terms):
                            if "virus" not in second_pathogen:
                                pass 

    # 3. Specimen Strict Conflict
    if has_any(lab, ["stool", "feces"]) and has_any(matched, ["blood", "serum", "plasma", "csf", "urine", "sputum", "bronchoalveolar", "lavage"]): return True
    if has_any(lab, ["blood", "serum", "plasma"]) and has_any(matched, ["stool", "urine", "sputum", "feces", "csf"]): return True
    if has_any(lab, ["csf"]) and has_any(matched, ["stool", "blood", "urine", "sputum", "serum", "plasma"]): return True
    
    return False

def fuzzy_score(text1, text2):
    if not isinstance(text1, str) or not isinstance(text2, str): return 0.0
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

top_k = 5
top_k_indices = np.argsort(similarities, axis=1)[:, -top_k:][:, ::-1]

# Build a mapping dictionary for fast lookup
lab_to_tmlt_map = {}
for i, lab in enumerate(unique_labs):
    best_candidate = None
    best_final_score = -1
    
    for rank in range(top_k):
        idx = top_k_indices[i, rank]
        sim_score = similarities[i, idx]
        
        # In SapBERT, scores might be generally higher or lower, but we still threshold at 0.80
        if sim_score < 0.80:
            break
            
        matched_row = tmlt_df.iloc[idx]
        matched_text = f"{matched_row.get('TMLT_Name', '')} {matched_row.get('COMPONENT', '')} {matched_row.get('SPECIMEN', '')} {matched_row.get('METHOD', '')}"
        
        # Hard conflict check (Gatekeeper)
        if is_hard_conflict(lab, matched_text):
            continue
            
        # Calculate Sub-scores
        c_score = fuzzy_score(lab, str(matched_row.get('COMPONENT', '')))
        s_score = fuzzy_score(lab, str(matched_row.get('SPECIMEN', '')))
        m_score = fuzzy_score(lab, str(matched_row.get('METHOD', '')))
        
        # Weighted Final Score (Emphasis on SapBERT's semantic similarity)
        final_match_score = (sim_score * 0.5) + (c_score * 0.3) + (s_score * 0.1) + (m_score * 0.1)
        
        if final_match_score > best_final_score:
            best_final_score = final_match_score
            
            best_candidate = {
                'TMLT_Code': matched_row.get('TMLT_Code', ''),
                'TMLT_Name': matched_row.get('TMLT_Name', ''),
                'COMPONENT': matched_row.get('COMPONENT', ''),
                'SPECIMEN': matched_row.get('SPECIMEN', ''),
                'METHOD': matched_row.get('METHOD', ''),
                'LOINC_NUM': matched_row.get('LOINC_NUM', ''),
                'CGD_CODE': matched_row.get('CGD_CODE', ''),
                'Similarity_Score': round(sim_score, 4),
                'Component_Score': round(c_score, 2),
                'Specimen_Score': round(s_score, 2),
                'Method_Score': round(m_score, 2),
                'Final_Match_Score': round(best_final_score, 4),
                'AI_Label': "High Confidence" if best_final_score >= 0.70 else "Review Required",
                'Validation_Flag': "Passed Rules"
            }
            
    if best_candidate is not None:
        lab_to_tmlt_map[lab] = best_candidate
    else:
        lab_to_tmlt_map[lab] = {
            'TMLT_Code': '-', 'TMLT_Name': '-', 'COMPONENT': '-', 'SPECIMEN': '-', 'METHOD': '-', 'LOINC_NUM': '-', 'CGD_CODE': '-',
            'Similarity_Score': '-', 'Component_Score': '-', 'Specimen_Score': '-', 'Method_Score': '-', 'Final_Match_Score': '-',
            'AI_Label': '-', 'Validation_Flag': 'Rejected by Rules'
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
            'Specimen TMLT': '-',
            'Method TMLT': '-',
            'รหัส LOINC_NUM': '-',
            'รหัส CGD_CODE': '-',
            'Similarity_Score': '-',
            'Component_Score': '-',
            'Specimen_Score': '-',
            'Method_Score': '-',
            'Final_Match_Score': '-',
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
            'Specimen TMLT': match_info.get('SPECIMEN', ''),
            'Method TMLT': match_info.get('METHOD', ''),
            'รหัส LOINC_NUM': match_info.get('LOINC_NUM', ''),
            'รหัส CGD_CODE': match_info.get('CGD_CODE', ''),
            'Similarity_Score': match_info.get('Similarity_Score', 0),
            'Component_Score': match_info.get('Component_Score', 0),
            'Specimen_Score': match_info.get('Specimen_Score', 0),
            'Method_Score': match_info.get('Method_Score', 0),
            'Final_Match_Score': match_info.get('Final_Match_Score', 0),
            'AI_Label': match_info.get('AI_Label', ''),
            'Validation_Flag': match_info.get('Validation_Flag', '')
        })

final_df = pd.DataFrame(results)
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "ICD_to_TMLT.xlsx")
print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 3 Completed successfully!")
