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
    if any(k in test_name for k in ['india ink', 'inhibin', 'fluke serology']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. Ferritin
    if 'ferritin' in test_name:
        row['ConceptID'] = '489004'
        row['FSN'] = 'Ferritin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Ki-67
    if 'ki-67' in test_name:
        row['ConceptID'] = '104328008'
        row['FSN'] = 'Immunohistochemistry (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Breast cyst fluid cytology
    if 'breast cyst fluid cytology' in test_name:
        row['ConceptID'] = '372295008'
        row['FSN'] = 'Cytologic examination of breast (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. ANA
    if 'ana ' in test_name or 'ana' == test_name:
        row['ConceptID'] = '359788000'
        row['FSN'] = 'Antinuclear antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. MuSK antibody
    if 'musk antibody' in test_name:
        row['ConceptID'] = '407519008'
        row['FSN'] = 'Antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Comprehensive toxicology screen
    if 'comprehensive toxicology screen' in test_name:
        row['ConceptID'] = '74763008'
        row['FSN'] = 'Toxicology substance measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 8. PNP enzyme activity
    if 'pnp enzyme activity' in test_name:
        row['ConceptID'] = '15220000'
        row['FSN'] = 'Laboratory test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 9. FISH
    if 'fish if targeted deletion' in test_name:
        row['ConceptID'] = '88960003'
        row['FSN'] = 'Chromosome analysis (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 10. Corresponding organ function test
    if 'corresponding organ function test' in test_name:
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 11) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
