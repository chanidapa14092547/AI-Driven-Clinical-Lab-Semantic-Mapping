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
# 🎯 TMLT BATCH 5 MAPPING RULES
# Format: "Test Name": ("TMLT_ID", "TMLT_Name", "Component", "Specimen", "Method", "LOINC_NUM", "Validation_Flag")
# -------------------------------------------------------------
mapping_rules = {
    "Prolactin": ("320152", "Prolactin [Mass/volume] in Serum or Plasma", "Prolactin", "Serum or Plasma", "-", "20568-2", "Auto Corrected (Rule)"),
    "High-sensitivity cardiac troponin I/T": ("320087", "Troponin I.cardiac [Mass/volume] in Serum or Plasma", "Troponin I.cardiac", "Serum or Plasma", "-", "10839-9", "Auto Corrected (Rule)"),
    "Serum uric acid": ("320108", "Urate [Mass/volume] in Serum or Plasma", "Urate", "Serum or Plasma", "-", "3084-1", "Auto Corrected (Rule)"),
    "Synovial fluid monosodium urate crystal examination": ("321458", "Crystal identification in Synovial fluid by Microscopy", "Crystal identification", "Synovial fluid", "Microscopy", "11624-4", "Auto Corrected (Rule)"),
    "Folate": ("320147", "Folate [Mass/volume] in Serum or Plasma", "Folate", "Serum or Plasma", "-", "2284-8", "Auto Corrected (Rule)"),
    "Quantitative beta-hCG": ("320216", "Choriogonadotropin.beta subunit [Mass/volume] in Serum or Plasma", "Choriogonadotropin.beta subunit", "Serum or Plasma", "-", "19080-1", "Auto Corrected (Rule)"),
    "Bone marrow aspiration/biopsy": ("321319", "Pathology report", "Pathology finding", "Bone marrow", "Histopathology", "-", "Auto Corrected (Rule)"),
    "MTB complex DNA detection": ("350847", "Mycobacterium tuberculosis complex DNA in Specimen by NAA with probe detection", "Mycobacterium tuberculosis complex DNA", "Specimen", "NAA with probe detection", "23985-5", "Auto Corrected (Rule)"),
    "Syphilis serology": ("320188", "Treponema pallidum Ab [Titer] in Serum or Plasma", "Treponema pallidum Ab", "Serum or Plasma", "-", "34112-3", "Auto Corrected (Rule)"),
    "Reticulocyte count": ("320272", "Reticulocytes [#/volume] in Blood", "Reticulocytes", "Blood", "-", "14196-0", "Auto Corrected (Rule)"),
    "Stool ova and parasite examination": ("321457", "Parasite identified in Stool by Microscopy", "Parasite identified", "Stool", "Microscopy", "10708-6", "Auto Corrected (Rule)"),
    "Genetic testing": ("321456", "Chromosome analysis", "Chromosome analysis", "Blood", "-", "-", "Auto Corrected (Rule)"),
    "Serum protein electrophoresis": ("321459", "Protein electrophoresis panel in Serum or Plasma", "Proteins", "Serum or Plasma", "Electrophoresis", "24351-9", "Auto Corrected (Rule)"),
    "Urine culture": ("350519", "Bacteria identified in Urine by Culture", "Bacteria identified", "Urine", "Culture", "630-4", "Auto Corrected (Rule)"),
    "Synovial fluid cell count": ("321460", "Leukocytes [#/volume] in Synovial fluid", "Leukocytes", "Synovial fluid", "-", "26485-3", "Auto Corrected (Rule)"),
    "RPR/VDRL": ("320187", "Treponema pallidum Ab.non-treponemal [Titer] in Serum or Plasma by VDRL", "Treponema pallidum Ab.non-treponemal", "Serum or Plasma", "VDRL", "5292-8", "Auto Corrected (Rule)"),
    "TPHA/TPPA/FTA-ABS": ("320188", "Treponema pallidum Ab [Titer] in Serum or Plasma", "Treponema pallidum Ab", "Serum or Plasma", "-", "34112-3", "Auto Corrected (Rule)"),
    "Oral glucose tolerance test": ("320258", "Glucose tolerance panel in Serum or Plasma", "Glucose tolerance panel", "Serum or Plasma", "-", "24353-5", "Auto Corrected (Rule)"),
    "Synovial fluid Gram stain and culture": ("350517", "Bacteria identified in Synovial fluid by Culture", "Bacteria identified", "Synovial fluid", "Culture", "626-2", "Auto Corrected (Rule)"),
    "HIV-1/2 Ag/Ab combination assay": ("320194", "HIV 1+2 Ab and HIV1 p24 Ag in Serum or Plasma", "HIV 1+2 Ab and HIV1 p24 Ag", "Serum or Plasma", "-", "56888-1", "Auto Corrected (Rule)")
}

def apply_tmlt_rules_v5(row):
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

print("Applying Batch 5 rules...")
df = df.apply(apply_tmlt_rules_v5, axis=1)

print("\n--- Current Validation Flag Distribution ---")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")
