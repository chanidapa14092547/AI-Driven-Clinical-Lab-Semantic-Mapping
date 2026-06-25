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

def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()

def create_rich_text(row):
    parts = []
    if pd.notna(row.get("TMLT_Name")):
        parts.append(f"Name: {row['TMLT_Name']}")
    if pd.notna(row.get("COMPONENT")):
        parts.append(f"Component: {row['COMPONENT']}")
    if pd.notna(row.get("SPECIMEN")):
        parts.append(f"Specimen: {row['SPECIMEN']}")
    if pd.notna(row.get("METHOD")):
        parts.append(f"Method: {row['METHOD']}")
    return " | ".join(parts)

def extract_specimen(text):
    text = safe_text(text)

    if any(k in text for k in ["urine", "ปัสสาวะ"]):
        return "urine"
    if any(k in text for k in ["stool", "feces", "faeces", "อุจจาระ"]):
        return "stool"
    if any(k in text for k in ["serum", "plasma", "blood", "เลือด"]):
        return "blood"
    if any(k in text for k in ["csf", "cerebrospinal"]):
        return "csf"
    if any(k in text for k in ["sputum", "เสมหะ"]):
        return "sputum"
    if any(k in text for k in ["swab"]):
        return "swab"

    return None

def extract_method(text):
    text = safe_text(text)

    if "antigen" in text:
        return "antigen"
    if "antibody" in text or "ab" in text:
        return "antibody"
    if "pcr" in text or "rt-pcr" in text:
        return "pcr"
    if "culture" in text:
        return "culture"
    if "microscopy" in text:
        return "microscopy"

    return None

def component_match_score(lab_text, component_text, tmlt_name):
    lab = safe_text(lab_text)
    component = safe_text(component_text)
    name = safe_text(tmlt_name)

    if component and component in lab:
        return 1.0

    if component and lab in component:
        return 0.9

    lab_words = set(lab.replace("-", " ").replace("/", " ").split())
    comp_words = set(component.replace("-", " ").replace("/", " ").split())
    name_words = set(name.replace("-", " ").replace("/", " ").split())

    if not lab_words:
        return 0

    comp_overlap = len(lab_words & comp_words) / len(lab_words)
    name_overlap = len(lab_words & name_words) / len(lab_words)

    return max(comp_overlap, name_overlap)

def specimen_match_score(lab_specimen, tmlt_specimen):
    tmlt_specimen = safe_text(tmlt_specimen)

    if lab_specimen is None:
        return 0.5

    if lab_specimen in tmlt_specimen:
        return 1.0

    if lab_specimen == "blood" and any(k in tmlt_specimen for k in ["serum", "plasma", "whole blood"]):
        return 1.0

    return 0.0

def method_match_score(lab_method, tmlt_method):
    tmlt_method = safe_text(tmlt_method)

    if lab_method is None:
        return 0.5

    if lab_method in tmlt_method:
        return 1.0

    return 0.0

def validation_flag(lab_text, matched_row, final_score, semantic_score):
    lab = safe_text(lab_text)
    specimen = safe_text(matched_row.get("SPECIMEN", ""))
    method = safe_text(matched_row.get("METHOD", ""))

    flags = []

    lab_specimen = extract_specimen(lab)
    lab_method = extract_method(lab)

    if lab_specimen and specimen_match_score(lab_specimen, specimen) == 0:
        flags.append(f"Possible specimen mismatch: lab={lab_specimen}, TMLT={specimen}")

    if lab_method and method_match_score(lab_method, method) == 0:
        flags.append(f"Possible method mismatch: lab={lab_method}, TMLT={method}")

    if semantic_score < 0.60:
        flags.append("Low semantic similarity")

    if final_score < 0.65:
        flags.append("Low final matching score")

    return "Pass" if not flags else "; ".join(flags)

tmlt_df["Rich_Text"] = tmlt_df.apply(create_rich_text, axis=1)

print("Loading Semantic Model...")
try:
    model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
    print("Using clinical model: pritamdeka/S-PubMedBert-MS-MARCO")
except Exception as e:
    print("Clinical model failed. Using fallback model: all-MiniLM-L6-v2")
    print(e)
    model = SentenceTransformer("all-MiniLM-L6-v2")

unique_labs = icd_lab_df["Lab_Item"].dropna().astype(str).unique().tolist()
tmlt_texts = tmlt_df["Rich_Text"].fillna("").astype(str).tolist()

print("Generating TMLT embeddings...")
tmlt_embs = model.encode(
    tmlt_texts,
    batch_size=128,
    show_progress_bar=True,
    convert_to_numpy=True
)

print("Generating Lab embeddings...")
lab_embs = model.encode(
    unique_labs,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True
)

print("Calculating hybrid matching...")

lab_to_tmlt_map = {}

for i, lab in enumerate(unique_labs):
    lab_specimen = extract_specimen(lab)
    lab_method = extract_method(lab)

    semantic_scores = cosine_similarity(
        lab_embs[i].reshape(1, -1),
        tmlt_embs
    )[0]

    candidate_scores = []

    for idx, row in tmlt_df.iterrows():
        semantic_score = semantic_scores[idx]

        comp_score = component_match_score(
            lab,
            row.get("COMPONENT", ""),
            row.get("TMLT_Name", "")
        )

        spec_score = specimen_match_score(
            lab_specimen,
            row.get("SPECIMEN", "")
        )

        meth_score = method_match_score(
            lab_method,
            row.get("METHOD", "")
        )

        final_score = (
            0.50 * semantic_score +
            0.25 * comp_score +
            0.15 * spec_score +
            0.10 * meth_score
        )

        if lab_specimen is not None and spec_score == 0:
            final_score -= 0.20

        if lab_method is not None and meth_score == 0:
            final_score -= 0.15

        candidate_scores.append((idx, final_score, semantic_score, comp_score, spec_score, meth_score))

    best_idx, final_score, semantic_score, comp_score, spec_score, meth_score = max(
        candidate_scores,
        key=lambda x: x[1]
    )

    matched_row = tmlt_df.iloc[best_idx]

    final_score_round = round(float(final_score), 2)
    semantic_score_round = round(float(semantic_score), 2)

    if final_score >= 0.85:
        label = "High Confidence"
    elif final_score >= 0.65:
        label = "Review Required"
    else:
        label = "Low Confidence"

    flag = validation_flag(lab, matched_row, final_score, semantic_score)

    lab_to_tmlt_map[lab] = {
        "TMLT_Code": matched_row.get("TMLT_Code", ""),
        "TMLT_Name": matched_row.get("TMLT_Name", ""),
        "COMPONENT": matched_row.get("COMPONENT", ""),
        "SPECIMEN": matched_row.get("SPECIMEN", ""),
        "METHOD": matched_row.get("METHOD", ""),
        "LOINC_NUM": matched_row.get("LOINC_NUM", ""),
        "CGD_CODE": matched_row.get("CGD_CODE", ""),
        "Similarity_Score": semantic_score_round,
        "Final_Match_Score": final_score_round,
        "Component_Score": round(float(comp_score), 2),
        "Specimen_Score": round(float(spec_score), 2),
        "Method_Score": round(float(meth_score), 2),
        "AI_Label": label,
        "Validation_Flag": flag
    }

print("Constructing final DataFrame...")

results = []

for index, row in icd_lab_df.iterrows():
    lab_item = row["Lab_Item"]

    if pd.isna(lab_item) or str(lab_item).strip() == "":
        results.append({
            "ICD-10": row["ICD-10"],
            "รายการตรวจ lab": "-",
            "รหัส TMLT": "-",
            "ชื่อ TMLT": "-",
            "Component TMLT": "-",
            "Specimen TMLT": "-",
            "Method TMLT": "-",
            "รหัส LOINC_NUM": "-",
            "รหัส CGD_CODE": "-",
            "Similarity_Score": "-",
            "Final_Match_Score": "-",
            "Component_Score": "-",
            "Specimen_Score": "-",
            "Method_Score": "-",
            "AI_Label": "-",
            "Validation_Flag": "-"
        })
    else:
        lab_item = str(lab_item)
        match_info = lab_to_tmlt_map.get(lab_item, {})

        results.append({
            "ICD-10": row["ICD-10"],
            "รายการตรวจ lab": lab_item,
            "รหัส TMLT": match_info.get("TMLT_Code", ""),
            "ชื่อ TMLT": match_info.get("TMLT_Name", ""),
            "Component TMLT": match_info.get("COMPONENT", ""),
            "Specimen TMLT": match_info.get("SPECIMEN", ""),
            "Method TMLT": match_info.get("METHOD", ""),
            "รหัส LOINC_NUM": match_info.get("LOINC_NUM", ""),
            "รหัส CGD_CODE": match_info.get("CGD_CODE", ""),
            "Similarity_Score": match_info.get("Similarity_Score", 0),
            "Final_Match_Score": match_info.get("Final_Match_Score", 0),
            "Component_Score": match_info.get("Component_Score", 0),
            "Specimen_Score": match_info.get("Specimen_Score", 0),
            "Method_Score": match_info.get("Method_Score", 0),
            "AI_Label": match_info.get("AI_Label", ""),
            "Validation_Flag": match_info.get("Validation_Flag", "")
        })

final_df = pd.DataFrame(results)
final_df = final_df.fillna("-")

output_excel = os.path.join(output_dir, "ICD_to_TMLT_1.xlsx")

print(f"Saving results to {output_excel}...")
final_df.to_excel(output_excel, index=False)

print("Step 3 Completed successfully!")