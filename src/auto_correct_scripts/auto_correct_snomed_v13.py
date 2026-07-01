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
    if any(k in test_name for k in ['cestode species identification', 'streptococcus pneumoniae urinary antigen']):
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 2. Liver function tests
    if 'liver function test if severe drug reaction' in test_name:
        row['ConceptID'] = '269992001'
        row['FSN'] = 'Liver function tests (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. Targeted gene mutation analysis
    if any(k in test_name for k in ['epidermolysis bullosa gene panel', 'pax6 gene testing', 'mecp2 gene testing', 'her2 fish']):
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. Microbial nucleic acid
    if 'diarrheagenic escherichia coli dna' in test_name:
        row['ConceptID'] = '122869004'
        row['FSN'] = 'Measurement of microbial nucleic acid (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. Iodine
    if 'urinary iodine' in test_name:
        row['ConceptID'] = '104759008'
        row['FSN'] = 'Iodine measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. Salivary cortisol
    if 'late-night salivary cortisol' in test_name:
        row['ConceptID'] = '313795000'
        row['FSN'] = 'Salivary cortisol level (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Tau protein
    if 'phosphorylated tau in csf' in test_name:
        row['ConceptID'] = '412923001'
        row['FSN'] = 'Cerebrospinal fluid Tau protein measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 8. Unmapped Generics
    if any(k in test_name for k in ['hormone level / metabolic test according to suspected adverse effect', 'fungal antigen/naat according to', 'drug level / toxicology screen if']):
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 13) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
