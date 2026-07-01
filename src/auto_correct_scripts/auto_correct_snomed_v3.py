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
    
    # 1. T4 free
    if 'free t4' in test_name or 't4 free' in test_name:
        row['ConceptID'] = '5113004'
        row['FSN'] = 'T4 free measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 2. Carboxyhemoglobin
    if 'carboxyhemoglobin' in test_name:
        row['ConceptID'] = '19821003'
        row['FSN'] = 'Carboxyhemoglobin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. HIV-1/2
    if 'hiv-1/2' in test_name or 'hiv ag/ab' in test_name:
        row['ConceptID'] = '171121004'
        row['FSN'] = 'Human immunodeficiency virus screening (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. ALP
    if 'alp if abnormal' in test_name or 'alkaline phosphatase' in test_name:
        row['ConceptID'] = '88810008'
        row['FSN'] = 'Alkaline phosphatase measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Troponin
    if 'troponin' in test_name:
        row['ConceptID'] = '105000003'
        row['FSN'] = 'Troponin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. 22q11.2 deletion
    if '22q11.2' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Drug level
    if 'drug level if available' in test_name:
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 3) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
