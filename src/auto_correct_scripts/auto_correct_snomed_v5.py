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
    
    # 1. Fecal calprotectin
    if 'fecal calprotectin' in test_name:
        row['ConceptID'] = '445881005'
        row['FSN'] = 'Measurement of fecal calprotectin (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 2. Congo red stain
    if 'congo red' in test_name:
        row['ConceptID'] = '127790008'
        row['FSN'] = 'Special stain technique (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. ENA panel & EBV
    if 'ena panel' in test_name or 'epstein-barr' in test_name:
        if str(row['ConceptID']) != '-' and str(row['ConceptID']).strip() != '':
            row['Validation_Flag'] = 'Auto Corrected (Rule)'
            return row

    # 4. Anti-dsDNA
    if 'anti-dsdna' in test_name:
        row['ConceptID'] = '314402008'
        row['FSN'] = 'Measurement of anti-double stranded DNA antibody (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 5. NT-proBNP
    if 'nt-probnp' in test_name:
        row['ConceptID'] = '423403002'
        row['FSN'] = 'Measurement of N-terminal pro-B-type natriuretic peptide (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 6. ACTH
    if 'acth' in test_name:
        row['ConceptID'] = '44908004'
        row['FSN'] = 'Adrenocorticotropic hormone measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 7. Drug level
    if 'drug level if applicable' in test_name:
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    return row

print("Applying New Rules (Batch 5) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
