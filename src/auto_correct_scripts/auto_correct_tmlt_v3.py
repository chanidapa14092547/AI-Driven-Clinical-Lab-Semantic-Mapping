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
# 🎯 TMLT BATCH 3 MAPPING RULES
# Format: "Test Name": ("TMLT_ID", "TMLT_Name", "Component", "Specimen", "Method", "LOINC_NUM", "Validation_Flag")
# -------------------------------------------------------------
mapping_rules = {
    "Prothrombin time": ("320265", "Coagulation tissue factor-induced.time [Time] in Platelet poor plasma by Coagulation assay", "Coagulation tissue factor-induced.time", "Platelet poor plasma", "Coagulation assay", "5902-2", "Auto Corrected (Rule)"),
    "INR": ("320077", "Coagulation tissue factor-induced.INR in Platelet poor plasma by Coagulation assay", "Coagulation tissue factor-induced.INR", "Platelet poor plasma", "Coagulation assay", "6301-6", "Auto Corrected (Rule)"),
    "Lipid profile": ("320255", "Lipid panel in Serum or Plasma", "Lipid panel", "Serum or Plasma", "-", "24331-1", "Auto Corrected (Rule)"),
    "Vitamin B12": ("320146", "Cobalamin [Mass/volume] in Serum or Plasma", "Cobalamin", "Serum or Plasma", "-", "2132-9", "Auto Corrected (Rule)"),
    "Potassium": ("320093", "Potassium [Moles/volume] in Serum or Plasma", "Potassium", "Serum or Plasma", "-", "2823-3", "Auto Corrected (Rule)"),
    "Activated partial thromboplastin time": ("320263", "Coagulation surface induced [Time] in Platelet poor plasma by Coagulation assay", "Coagulation surface induced", "Platelet poor plasma", "Coagulation assay", "14979-9", "Auto Corrected (Rule)"),
    "Magnesium": ("320090", "Magnesium [Mass/volume] in Serum or Plasma", "Magnesium", "Serum or Plasma", "-", "19123-9", "Auto Corrected (Rule)"),
    "Urine protein-to-creatinine ratio": ("320235", "Protein/Creatinine [Mass Ratio] in Urine", "Protein/Creatinine", "Urine", "-", "2890-2", "Auto Corrected (Rule)"),
    "Hemoglobin": ("320261", "Hemoglobin [Mass/volume] in Blood", "Hemoglobin", "Blood", "-", "718-7", "Auto Corrected (Rule)"),
    "Bilirubin": ("320041", "Bilirubin.total [Mass/volume] in Serum or Plasma", "Bilirubin.total", "Serum or Plasma", "-", "1975-2", "Auto Corrected (Rule)"),
    "Immunohistochemistry panel": ("321319", "Pathology report", "Pathology finding", "Tissue", "Immunohistochemistry", "-", "Auto Corrected (Rule)"),
    "Blood group and Rh typing": ("320260", "ABO and Rh group panel in Blood", "ABO and Rh group panel", "Blood", "-", "34532-2", "Auto Corrected (Rule)"),
    "Flow cytometry": ("321455", "Flow cytometry panel", "Cells", "Blood or Bone Marrow", "Flow cytometry", "-", "Auto Corrected (Rule)"),
    "Albumin": ("320036", "Albumin [Mass/volume] in Serum or Plasma", "Albumin", "Serum or Plasma", "-", "1751-7", "Auto Corrected (Rule)"),
    "Bone/tissue Gram stain and bacterial culture": ("350515", "Bacteria identified in Tissue by Culture", "Bacteria identified", "Tissue", "Culture", "619-7", "Auto Corrected (Rule)"),
    
    # Conditional / Unmapped Items
    "Carboxyhemoglobin if smoke inhalation suspected": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)"),
    "Chromosomal microarray if syndromic skeletal malformation suspected": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)"),
    "AFB smear/culture if tuberculosis suspected": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)"),
    "Laboratory test according to suspected bone disorder": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)"),
    "Free T4 if metabolic/endocrine myopathy suspected": ("-", "-", "-", "-", "-", "-", "Auto Corrected (Unmapped)"),
}

# Added general unmapped conditional catching
def apply_tmlt_rules_v3(row):
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
        
        # General catch for "if ... suspected" just like SNOMED
        elif 'if clinically indicated' in test_name.lower() or 'if suspected' in test_name.lower() or 'according to' in test_name.lower():
            row['TMLT_ID'] = '-'
            row['TMLT_Name'] = '-'
            row['Component'] = '-'
            row['Specimen'] = '-'
            row['Method'] = '-'
            row['LOINC_NUM'] = '-'
            row['CGD_CODE'] = '-'
            row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
            
    return row

print("Applying Batch 3 rules...")
df = df.apply(apply_tmlt_rules_v3, axis=1)

print("\n--- Current Validation Flag Distribution ---")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")
