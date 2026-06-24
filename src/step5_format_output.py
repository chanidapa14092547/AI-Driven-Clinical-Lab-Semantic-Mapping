import pandas as pd
import os

from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
output_dir = base_dir / "output"

tmlt_path = os.path.join(output_dir, "ICD_to_TMLT.xlsx")
snomed_path = os.path.join(output_dir, "ICD_to_SNOMED.xlsx")

print("Processing TMLT...")
tmlt_df = pd.read_excel(tmlt_path)
# Find rows where Lab_Item is null
null_mask = tmlt_df['รายการตรวจ lab'].isnull()

tmlt_df.loc[null_mask, 'รายการตรวจ lab'] = "-"
tmlt_df.loc[null_mask, 'รหัส TMLT'] = "-"
tmlt_df.loc[null_mask, 'ชื่อ TMLT'] = "-"
tmlt_df.loc[null_mask, 'Component TMLT'] = "-"
tmlt_df.loc[null_mask, 'รหัส LOINC_NUM'] = "-"
tmlt_df.loc[null_mask, 'รหัส CGD_CODE'] = "-"
tmlt_df.loc[null_mask, 'Similarity_Score'] = None

# Fill other NaN with empty string for cleaner Excel
tmlt_df = tmlt_df.fillna("-")
tmlt_df.to_excel(tmlt_path, index=False)


print("Processing SNOMED...")
snomed_df = pd.read_excel(snomed_path)
null_mask_s = snomed_df['รายการตรวจ lab'].isnull()

snomed_df.loc[null_mask_s, 'รายการตรวจ lab'] = "-"
snomed_df.loc[null_mask_s, 'SNOMED_ConceptId'] = "-"
snomed_df.loc[null_mask_s, 'SNOMED_FSN'] = "-"
snomed_df.loc[null_mask_s, 'SNOMED_Category'] = "-"
snomed_df.loc[null_mask_s, 'Similarity_Score'] = None

snomed_df = snomed_df.fillna("-")
snomed_df.to_excel(snomed_path, index=False)

print("Formatting completed successfully!")
