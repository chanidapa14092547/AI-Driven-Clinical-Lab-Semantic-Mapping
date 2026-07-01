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
    
    # 1. 1p/19q codeletion
    if '1p/19q' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 2. Arbovirus/Arenavirus IgM
    if 'arbovirus' in test_name or 'arenavirus' in test_name or 'virus-specific igm' in test_name:
        row['ConceptID'] = '407519008'
        row['FSN'] = 'Antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Total IgE
    if 'total ige' in test_name:
        row['ConceptID'] = '41960005'
        row['FSN'] = 'Immunoglobulin E measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Respiratory virus NAAT
    if 'respiratory virus' in test_name or 'respiratory pathogen' in test_name:
        row['ConceptID'] = '122869004'
        row['FSN'] = 'Measurement of microbial nucleic acid (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Dark-field microscopy
    if 'dark-field microscopy' in test_name:
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 6. Gene mutations (NRAS, IDH1/IDH2, MGMT)
    if 'nras' in test_name or 'idh1' in test_name or 'mgmt' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Urine drug screen
    if 'urine drug screen if clinically indicated' in test_name:
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 7) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
