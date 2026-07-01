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
    if any(k in test_name for k in ['cytology, respiratory specimen', 'toxicology / exposure testing only if', 'toxicology test according to prior', 'toxic shock toxin testing']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. Calcium
    if 'calcium if secondary constipation' in test_name:
        row['ConceptID'] = '71878006'
        row['FSN'] = 'Calcium measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Yersinia pestis
    if 'yersinia pestis dna' in test_name:
        row['ConceptID'] = '122869004'
        row['FSN'] = 'Measurement of microbial nucleic acid (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Cytology (Pleural / Ocular)
    if 'cytology, pleural fluid' in test_name or 'cytology, ocular fluid' in test_name:
        row['ConceptID'] = '372274006'
        row['FSN'] = 'Cytological examination (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Urine metanephrine
    if 'urine fractionated metanephrine' in test_name:
        row['ConceptID'] = '15220000'
        row['FSN'] = 'Laboratory test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. HER2 FISH
    if 'her2 fish' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Generic / Unmapped
    if any(k in test_name for k in ['fungal antigen/naat according to suspected organism', 'hormone/drug level according to suspected agent', 'drug level / toxicology screen if clinically indicated']):
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 12) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
