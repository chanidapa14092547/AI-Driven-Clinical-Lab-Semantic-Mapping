import pandas as pd
import sys
import re

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
# 🎯 TMLT BATCH 4 MAPPING RULES
# Format: "Test Name": ("TMLT_ID", "TMLT_Name", "Component", "Specimen", "Method", "LOINC_NUM", "Validation_Flag")
# -------------------------------------------------------------
mapping_rules = {
    "Sodium": ("320102", "Sodium [Moles/volume] in Serum or Plasma", "Sodium", "Serum or Plasma", "-", "2951-2", "Auto Corrected (Rule)"),
    "Gamma-glutamyl transferase": ("320050", "Gamma glutamyl transferase [Enzymatic activity/volume] in Serum or Plasma", "Gamma glutamyl transferase", "Serum or Plasma", "-", "2324-2", "Auto Corrected (Rule)"),
    "Histopathology": ("321319", "Pathology report", "Pathology finding", "Tissue", "Histopathology", "11526-1", "Auto Corrected (Rule)"),
    "Complement C3": ("320131", "Complement C3 [Mass/volume] in Serum or Plasma", "Complement C3", "Serum or Plasma", "-", "4485-9", "Auto Corrected (Rule)"),
    "Neisseria gonorrhoeae DNA detection by NAAT": ("350849", "Neisseria gonorrhoeae DNA in Specimen by NAA with probe detection", "Neisseria gonorrhoeae DNA", "Specimen", "NAA with probe detection", "24111-7", "Auto Corrected (Rule)"),
    "ANCA": ("320164", "Antineutrophil cytoplasmic Ab [Titer] in Serum or Plasma", "Antineutrophil cytoplasmic Ab", "Serum or Plasma", "-", "47297-7", "Auto Corrected (Rule)"),
    "Ferritin": ("320148", "Ferritin [Mass/volume] in Serum or Plasma", "Ferritin", "Serum or Plasma", "-", "2276-4", "Auto Corrected (Rule)"),
    "Peripheral blood smear": ("320262", "Blood smear finding", "Blood smear finding", "Blood", "Microscopy", "-", "Auto Corrected (Rule)"),
    "Mycobacterial culture": ("350516", "Mycobacterium sp identified in Specimen by Culture", "Mycobacterium sp identified", "Specimen", "Culture", "543-9", "Auto Corrected (Rule)"),
    "Fungal culture": ("351105", "Fungus identified in Specimen by Culture", "Fungus identified", "Specimen", "Culture", "580-1", "Auto Corrected (Rule)"),
    "Kidney biopsy histopathology": ("321319", "Pathology report", "Pathology finding", "Kidney", "Histopathology", "11526-1", "Auto Corrected (Rule)"),
    "Skin biopsy histopathology": ("321319", "Pathology report", "Pathology finding", "Skin", "Histopathology", "11526-1", "Auto Corrected (Rule)"),
    "Chlamydia trachomatis DNA detection by NAAT": ("350848", "Chlamydia trachomatis DNA in Specimen by NAA with probe detection", "Chlamydia trachomatis DNA", "Specimen", "NAA with probe detection", "21613-5", "Auto Corrected (Rule)"),
    "HIV Ag/Ab": ("320194", "HIV 1+2 Ab and HIV1 p24 Ag in Serum or Plasma", "HIV 1+2 Ab and HIV1 p24 Ag", "Serum or Plasma", "-", "56888-1", "Auto Corrected (Rule)"),
    "Synovial fluid crystal examination": ("321458", "Crystal identification in Synovial fluid by Microscopy", "Crystal identification", "Synovial fluid", "Microscopy", "-", "Auto Corrected (Rule)"),
    "Urine drug screen": ("320311", "Drug screen [Presence] in Urine", "Drug screen", "Urine", "-", "43105-6", "Auto Corrected (Rule)"),
}

def apply_tmlt_rules_v4(row):
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
        
        # Enhanced sweeping rule for conditional orders
        elif ' if ' in test_name.lower() or 'according to' in test_name.lower() or 'as indicated' in test_name.lower():
            row['TMLT_ID'] = '-'
            row['TMLT_Name'] = '-'
            row['Component'] = '-'
            row['Specimen'] = '-'
            row['Method'] = '-'
            row['LOINC_NUM'] = '-'
            row['CGD_CODE'] = '-'
            row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
            
    return row

print("Applying Batch 4 rules...")
df = df.apply(apply_tmlt_rules_v4, axis=1)

print("\n--- Current Validation Flag Distribution ---")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")
