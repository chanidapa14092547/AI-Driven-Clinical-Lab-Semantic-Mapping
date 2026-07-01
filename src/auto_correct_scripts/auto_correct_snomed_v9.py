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
    if any(k in test_name for k in ['synovial fluid analysis', 'toxicology / substance level', 'toxic solvent', 'sedative-hypnotic']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. NAAT / DNA
    if 'stool bacterial pathogen naat' in test_name or 'borrelia dna' in test_name:
        row['ConceptID'] = '122869004'
        row['FSN'] = 'Measurement of microbial nucleic acid (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Albumin
    if 'albumin' in test_name and 'malabsorption' in test_name:
        row['ConceptID'] = '104485008'
        row['FSN'] = 'Albumin measurement, serum (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Allergen-specific IgG
    if 'allergen-specific igg' in test_name:
        row['ConceptID'] = '45293001'
        row['FSN'] = 'Allergen specific immunoglobulin G antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Gene mutations
    if any(k in test_name for k in ['kras', 'acvr1', 'kit']):
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. AMH
    if 'müllerian' in test_name or 'mullerian' in test_name:
        row['ConceptID'] = '44933006'
        row['FSN'] = 'Mullerian-inhibiting substance measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. HPLC hemoglobin
    if 'hplc hemoglobin' in test_name:
        row['ConceptID'] = '104689000'
        row['FSN'] = 'Hemoglobin analysis (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 8. Lyme serology
    if 'lyme serology' in test_name:
        row['ConceptID'] = '408169002'
        row['FSN'] = 'Borrelia burgdorferi serology (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 9. ESR
    if 'esr if inflammatory' in test_name:
        row['ConceptID'] = '38031006'
        row['FSN'] = 'Erythrocyte sedimentation rate test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 10. Anti-CCP
    if 'anti-ccp' in test_name:
        row['ConceptID'] = '408200008'
        row['FSN'] = 'Cyclic citrullinated peptide antibody measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    return row

print("Applying New Rules (Batch 9) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
