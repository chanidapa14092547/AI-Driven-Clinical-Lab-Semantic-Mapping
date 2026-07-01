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
# 🎯 TMLT BATCH 1 MAPPING RULES (Top 10 High Frequency Labs)
# Format: "Test Name": ("TMLT_ID", "TMLT_Name", "Component", "Specimen", "Method", "LOINC_NUM")
# -------------------------------------------------------------
mapping_rules = {
    # 1. Complete blood count
    "Complete blood count": (
        "320257", "Complete blood count in Blood by Automated count", 
        "Complete blood count", "Blood", "Automated count", "58410-2"
    ),
    # 2. Calcium
    "Calcium": (
        "320078", "Calcium [Mass/volume] in Serum or Plasma", 
        "Calcium", "Serum or Plasma", "-", "17861-6"
    ),
    # 3. Serum creatinine
    "Serum creatinine": (
        "320083", "Creatinine [Mass/volume] in Serum or Plasma", 
        "Creatinine", "Serum or Plasma", "-", "2160-0"
    ),
    # 4. C-reactive protein
    "C-reactive protein": (
        "320245", "C reactive protein [Mass/volume] in Serum or Plasma", 
        "C reactive protein", "Serum or Plasma", "-", "1988-5"
    ),
    # 5. TSH
    "TSH": (
        "320141", "Thyrotropin [Units/volume] in Serum or Plasma", 
        "Thyrotropin", "Serum or Plasma", "-", "11579-0"
    ),
    # 6. eGFR
    "eGFR": (
        "320084", "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum, Plasma or Blood by Creatinine-based formula (MDRD)", 
        "Glomerular filtration rate/1.73 sq M.predicted", "Serum, Plasma or Blood", "Creatinine-based formula (MDRD)", "33914-3"
    ),
    # 7. Phosphate
    "Phosphate": (
        "320092", "Phosphate [Mass/volume] in Serum or Plasma", 
        "Phosphate", "Serum or Plasma", "-", "2777-1"
    ),
    # 8. ALP
    "ALP": (
        "320037", "Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma", 
        "Alkaline phosphatase", "Serum or Plasma", "-", "6768-6"
    ),
    # 9. ESR
    "ESR": (
        "320268", "Erythrocyte sedimentation rate", 
        "Erythrocyte sedimentation rate", "Blood", "-", "30341-2"
    ),
    # 10. 25-hydroxyvitamin D
    "25-hydroxyvitamin D": (
        "320129", "25-hydroxycholecalciferol [Mass/volume] in Serum or Plasma", 
        "25-hydroxycholecalciferol", "Serum or Plasma", "-", "1649-3"
    )
}

def apply_tmlt_rules(row):
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
            row['CGD_CODE'] = '-' # CGD varies by hospital, safe to leave blank or mapped if known
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
    return row

print("Applying Batch 1 rules...")
df = df.apply(apply_tmlt_rules, axis=1)

print("\n--- Current Validation Flag Distribution ---")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")
