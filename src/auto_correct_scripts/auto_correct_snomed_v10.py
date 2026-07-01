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
    
    # 1. Accept AI
    if any(k in test_name for k in ['methemoglobin', 'chlamydia trachomatis dna', 'treponemal igm']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. ADA
    if 'ada enzyme' in test_name:
        row['ConceptID'] = '104471003'
        row['FSN'] = 'Adenosine deaminase measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Skeletal dysplasia
    if 'skeletal dysplasia' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Dermatophyte DNA
    if 'dermatophyte dna' in test_name:
        row['ConceptID'] = '122869004'
        row['FSN'] = 'Measurement of microbial nucleic acid (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Metanephrine
    if 'plasma free metanephrine' in test_name:
        row['ConceptID'] = '15220000'
        row['FSN'] = 'Laboratory test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. PLA2R
    if 'pla2r antibody' in test_name:
        row['ConceptID'] = '407519008'
        row['FSN'] = 'Antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Generic drugs/toxicology -> Unmapped
    if any(k in test_name for k in ['therapeutic drug monitoring', 'opioid/cocaine', 'drug/toxicology test according to']):
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 10) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
