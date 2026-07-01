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
    
    # 1. EBV-EBER
    if 'ebv-eber' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 2. Cholinesterase
    if 'cholinesterase' in test_name:
        row['ConceptID'] = '66128007'
        row['FSN'] = 'Cholinesterase measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Electrolyte panel
    if 'electrolyte panel' in test_name:
        row['ConceptID'] = '113066009'
        row['FSN'] = 'Electrolyte panel (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. HLA-B27
    if 'hla-b27' in test_name:
        row['ConceptID'] = '314096001'
        row['FSN'] = 'HLA B27 antigen screening test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Tumor marker
    if 'tumor marker' in test_name:
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 6. Enzyme / genetic test
    if 'enzyme / genetic test' in test_name:
        row['ConceptID'] = '15220000'
        row['FSN'] = 'Laboratory test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. DHEA-S
    if 'dhea-s' in test_name:
        row['ConceptID'] = '28437009'
        row['FSN'] = 'Dehydroepiandrosterone sulfate measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 8. G6PD
    if 'g6pd' in test_name:
        row['ConceptID'] = '411995000'
        row['FSN'] = 'Glucose-6-phosphate dehydrogenase measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 9. Indirect bilirubin
    if 'indirect bilirubin' in test_name:
        row['ConceptID'] = '313842008'
        row['FSN'] = 'Serum unconjugated bilirubin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    return row

print("Applying New Rules (Batch 8) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
