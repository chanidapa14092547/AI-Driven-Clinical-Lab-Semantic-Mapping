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
    
    # 1. beta-hCG
    if 'beta-hcg' in test_name or 'beta hcg' in test_name:
        row['ConceptID'] = '386558001'
        row['FSN'] = 'Chorionic gonadotropin, beta-subunit measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 2. Blood group and crossmatch
    if 'blood group' in test_name or 'crossmatch' in test_name:
        row['ConceptID'] = '104065003'
        row['FSN'] = 'Blood compatibility test, crossmatch by incubation technique (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 3. RPR / VDRL
    if 'rpr' in test_name or 'vdrl' in test_name:
        row['ConceptID'] = '143185008'
        row['FSN'] = 'Syphilis infectious titer test (& [TPI] or [VDRL] or [Wassermann\'s]) (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    # 4. TPHA / TPPA / FTA-ABS
    if 'tpha' in test_name or 'tppa' in test_name or 'fta-abs' in test_name:
        row['ConceptID'] = '40675008'
        row['FSN'] = 'Serologic test for syphilis (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row

    return row

print("Applying New Rules (Batch 4: beta-hCG, Blood Group, VDRL, TPHA) to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
