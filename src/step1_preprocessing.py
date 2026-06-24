import pandas as pd
import os
import re

# Set up paths
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "DS MIMY"
output_dir = base_dir / "output"

# Create output dir if not exists
os.makedirs(output_dir, exist_ok=True)

print("Loading data...")
# Read the reference ICD-10 codes
icd10_ref_df = pd.read_excel(os.path.join(data_dir, "ICD102016.xlsx"))
valid_icd_codes = icd10_ref_df['icd10'].astype(str).tolist()

# Read the mapping file
icd_lab_df = pd.read_excel(os.path.join(data_dir, "ICD-LAB.xlsx"))

def parse_icd_range(icd_str, valid_codes):
    """
    Parses an ICD string which might be a range (A000-A009) or a single code.
    Returns a list of valid ICD codes.
    """
    icd_str = str(icd_str).strip()
    # Replace the weird dash character with a standard dash
    icd_str = icd_str.replace('\ufffd', '-').replace('–', '-')
    
    if '-' in icd_str:
        start_code, end_code = icd_str.split('-')
        start_code = start_code.strip()
        end_code = end_code.strip()
        
        # Filter valid codes that fall alphabetically between start and end
        # assuming the valid_codes list is sorted, or we can just do string comparison
        matched_codes = [code for code in valid_codes if start_code <= code <= end_code]
        return matched_codes
    else:
        # Single code, check if it's valid
        # if the user provided A00, we might want to include A00.0 - A00.9, 
        # but for string matching, we'll just check starts with or exact match.
        matched_codes = [code for code in valid_codes if code.startswith(icd_str)]
        return matched_codes

print("Expanding ICD ranges and splitting Lab items...")
expanded_rows = []

for index, row in icd_lab_df.iterrows():
    icd_val = row['ICD']
    lab_val = str(row['Lab'])
    
    if pd.isna(icd_val) or pd.isna(lab_val):
        continue
        
    # 1. Expand ICD codes
    expanded_icds = parse_icd_range(icd_val, valid_icd_codes)
    
    # 2. Split Lab items by ';'
    # Sometimes it's comma or new line, but readme says ';'
    lab_items = [item.strip() for item in re.split(r';|\n', lab_val) if item.strip()]
    
    # Add pairs to list
    for code in expanded_icds:
        for lab in lab_items:
            expanded_rows.append({
                'ICD-10': code,
                'Lab_Item': lab,
                'Original_ICD_Range': icd_val
            })

# Create final DataFrame
expanded_df = pd.DataFrame(expanded_rows)

print(f"Original ICD-LAB rows: {len(icd_lab_df)}")
print(f"Expanded rows: {len(expanded_df)}")

# Save to intermediate CSV for next step
output_file = os.path.join(output_dir, "step1_expanded_icd_lab.csv")
expanded_df.to_csv(output_file, index=False)
print(f"Saved preprocessed data to: {output_file}")
print("Step 1 Completed successfully!")
