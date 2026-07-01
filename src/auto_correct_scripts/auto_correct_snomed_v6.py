import pandas as pd

file_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED_Auto_Corrected.xlsx'
output_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED_Auto_Corrected.xlsx'

df = pd.read_excel(file_path)
original_columns = df.columns.tolist()
df.columns = ['ICD_10', 'Test_Name', 'ConceptID', 'FSN', 'Similarity', 'Confidence', 'Validation_Flag']

def apply_rules(row):
    if row['Validation_Flag'] != 'Needs Manual Review':
        return row
    
    test_name = str(row['Test_Name']).lower()
    
    # 1. Accept AI for these groups
    if any(keyword in test_name for keyword in ['htlv 1/2', 'west nile', 'total immunoglobulin', 'dark field', 'influenza a virus pcr', 'influenza a pcr']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. BRAF mutation
    if 'braf' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Anti-DNase B
    if 'anti-dnase b' in test_name:
        row['ConceptID'] = '69649005'
        row['FSN'] = 'Anti DNase B test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. FISH for...
    if 'fish for' in test_name:
        row['ConceptID'] = '88960003'
        row['FSN'] = 'Chromosome analysis (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    return row

print("Applying New Rules (Batch 6) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
