import pandas as pd
import sys

file_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/TMLT/ICD_to_TMLT.xlsx'
output_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/TMLT/ICD_to_TMLT.xlsx'

print("Reading dataset...")
df = pd.read_excel(file_path)

original_columns = df.columns.tolist()
df.columns = [
    'ICD_10', 'Test_Name', 'TMLT_ID', 'TMLT_Name', 'Component', 'Specimen', 'Method',
    'LOINC_NUM', 'CGD_CODE', 'Similarity', 'Comp_Score', 'Spec_Score', 'Meth_Score',
    'Final_Score', 'AI_Label', 'Validation_Flag'
]

# -------------------------------------------------------------
# 🎯 TMLT BATCH 2 MAPPING RULES (Next Top 20)
# Format: "Test Name": ("TMLT_ID", "TMLT_Name", "Component", "Specimen", "Method", "LOINC_NUM", "Validation_Flag")
# -------------------------------------------------------------
mapping_rules = {
    "Parathyroid hormone": ("320150", "Parathyrin.intact [Mass/volume] in Serum or Plasma", "Parathyrin.intact", "Serum or Plasma", "-", "2777-1", "Auto Corrected (Rule)"),
    "Histopathology, tissue biopsy": ("321319", "Pathology report", "Pathology finding", "Tissue", "-", "11526-1", "Auto Corrected (Rule)"),
    "Electrolyte panel": ("320253", "Electrolytes panel in Serum or Plasma", "Electrolytes panel", "Serum or Plasma", "-", "24326-1", "Auto Corrected (Rule)"),
    "Free T4": ("320140", "Thyroxine.free [Mass/volume] in Serum or Plasma", "Thyroxine.free", "Serum or Plasma", "-", "3024-7", "Auto Corrected (Rule)"),
    "Chromosomal microarray": ("321456", "Chromosome analysis", "Chromosome analysis", "Blood", "Microarray", "-", "Auto Corrected (Rule)"),
    "Blood gas": ("320042", "Blood gas panel in Arterial blood", "Blood gas panel", "Arterial blood", "-", "24338-6", "Auto Corrected (Rule)"),
    "Blood culture": ("350513", "Bacteria identified in Blood by Culture", "Bacteria identified", "Blood", "Culture", "600-7", "Auto Corrected (Rule)"),
    "Urinalysis": ("320256", "Urinalysis panel", "Urinalysis panel", "Urine", "-", "24356-8", "Auto Corrected (Rule)"),
    "Creatine kinase": ("320049", "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma", "Creatine kinase", "Serum or Plasma", "-", "2157-6", "Auto Corrected (Rule)"),
    "Lactate": ("320096", "Lactate [Mass/volume] in Serum or Plasma", "Lactate", "Serum or Plasma", "-", "2524-7", "Auto Corrected (Rule)"),
    "Rheumatoid factor": ("320242", "Rheumatoid factor [Units/volume] in Serum or Plasma", "Rheumatoid factor", "Serum or Plasma", "-", "11572-5", "Auto Corrected (Rule)"),
    "Hemoglobin A1c": ("320058", "Hemoglobin A1c/Hemoglobin.total in Blood", "Hemoglobin A1c/Hemoglobin.total", "Blood", "-", "4548-4", "Auto Corrected (Rule)"),
    "Anti-CCP antibody": ("320172", "Cyclic citrullinated peptide Ab [Units/volume] in Serum or Plasma", "Cyclic citrullinated peptide Ab", "Serum or Plasma", "-", "32218-0", "Auto Corrected (Rule)"),
    "Glucose": ("320054", "Glucose [Mass/volume] in Serum or Plasma", "Glucose", "Serum or Plasma", "-", "2345-7", "Auto Corrected (Rule)"),
    "Platelet count": ("320259", "Platelets [#/volume] in Blood by Automated count", "Platelets", "Blood", "Automated count", "777-3", "Auto Corrected (Rule)"),
    "AST": ("320040", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "Aspartate aminotransferase", "Serum or Plasma", "-", "1920-8", "Auto Corrected (Rule)"),
    "Fasting plasma glucose": ("320054", "Glucose [Mass/volume] in Serum or Plasma", "Glucose", "Serum or Plasma", "-", "1558-6", "Auto Corrected (Rule)"),
    "ALT": ("320038", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "Alanine aminotransferase", "Serum or Plasma", "-", "1742-6", "Auto Corrected (Rule)"),
    "ANA": ("320163", "Antinuclear Ab [Titer] in Serum or Plasma", "Antinuclear Ab", "Serum or Plasma", "-", "5048-4", "Auto Corrected (Rule)"),
    # Unmapped items
    "Laboratory test according to underlying disease": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)")
}

def apply_tmlt_rules_v2(row):
    if row['Validation_Flag'] == 'Needs Manual Review':
        test_name = str(row['Test_Name']).strip()
        if test_name in mapping_rules:
            mapped = mapping_rules[test_name]
            row['TMLT_ID'] = mapped[0]
            row['TMLT_Name'] = mapped[1]
            row['Component'] = mapped[2]
            row['Specimen'] = mapped[3]
            row['Method'] = mapped[4]
            row['LOINC_NUM'] = mapped[5]
            row['CGD_CODE'] = '-'
            row['Validation_Flag'] = mapped[6]
    return row

print("Applying Batch 2 rules...")
df = df.apply(apply_tmlt_rules_v2, axis=1)

print("\n--- Current Validation Flag Distribution ---")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")
