import pandas as pd
import re

file_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED.xlsx'
output_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED_Auto_Corrected.xlsx'

df = pd.read_excel(file_path)

# Ensure columns are standard
original_columns = df.columns.tolist()
df.columns = ['ICD_10', 'Test_Name', 'ConceptID', 'FSN', 'Similarity', 'Confidence', 'Validation_Flag']

def apply_rules(row):
    # Only process Medium Confidence, Rejected, or '-'
    if row['Confidence'] not in ['Medium Confidence', 'Rejected', '-']:
        return row
    
    test_name = str(row['Test_Name']).lower()
    
    # 1. Microbiology Cultures
    if 'culture' in test_name:
        if 'fungal' in test_name:
            row['ConceptID'] = '41170006'
            row['FSN'] = 'Mycology culture (procedure)'
        else:
            row['ConceptID'] = '61594008'
            row['FSN'] = 'Microbial culture (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
        
    # 2. Stains & Preps
    if 'gram stain' in test_name:
        row['ConceptID'] = '389791008'
        row['FSN'] = 'Gram stain microscopy (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'koh preparation' in test_name:
        row['ConceptID'] = '27318003'
        row['FSN'] = 'Potassium hydroxide preparation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
        
    # 3. Pathology / IHC
    if 'immunohistochemistry' in test_name or 'ihc' in test_name.split():
        row['ConceptID'] = '117617002'
        row['FSN'] = 'Immunohistochemistry procedure (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'histopathology' in test_name:
        row['ConceptID'] = '252416005'
        row['FSN'] = 'Histopathology test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
        
    # 4. Genetics
    if 'rearrangement' in test_name:
        row['ConceptID'] = '118115009'
        row['FSN'] = 'Gene rearrangement analysis (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'htt gene cag repeat' in test_name:
        row['ConceptID'] = '437742006'
        row['FSN'] = 'Huntington disease gene mutation carrier detection test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'prothrombin g20210a' in test_name:
        row['ConceptID'] = '395158000'
        row['FSN'] = 'Prothrombin gene (20210) screen (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'atm gene' in test_name:
        row['ConceptID'] = '443982007'
        row['FSN'] = 'Targeted analysis for gene mutation (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'genetic testing' in test_name or 'genetic screening' in test_name:
        row['ConceptID'] = '473200002'
        row['FSN'] = 'Genetic screening for disorder (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
        
    # 5. Specific Lab Overrides
    if 'tb igra' in test_name:
        row['ConceptID'] = '35140007'
        row['FSN'] = 'Interferon gamma assay (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'hiv ag/ab' in test_name or 'hiv screening' in test_name:
        row['ConceptID'] = '171121004'
        row['FSN'] = 'Human immunodeficiency virus screening (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'beta-2 transferrin' in test_name:
        row['ConceptID'] = '121742007'
        row['FSN'] = 'Beta-2-transferrin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'c-reactive protein' in test_name:
        row['ConceptID'] = '55235003'
        row['FSN'] = 'C-reactive protein measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'ceruloplasmin' in test_name:
        row['ConceptID'] = '87365002'
        row['FSN'] = 'Ceruloplasmin measurement (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'parasite identification' in test_name:
        row['ConceptID'] = '122069003'
        row['FSN'] = 'Parasite identification (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
    if 'laboratory test according to' in test_name:
        row['ConceptID'] = '15220000'
        row['FSN'] = 'Laboratory test (procedure)'
        row['Validation_Flag'] = 'Auto Corrected (Rule)'
        return row
        
    # 6. Unmapped / Hallucinations
    unmapped_keywords = [
        'viral meningitis panel', 'pathogen-specific', 'viral dna/rna detection', 
        'antibody panel', 'beta-trace protein', 'dna detection according to suspected',
        'amyloid beta', 'he4', 'dihydrorhodamine', 'eosin-5-maleimide', 'vaccine antibody response'
    ]
    if any(k in test_name for k in unmapped_keywords):
        row['ConceptID'] = '-'
        row['FSN'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        return row

    # If it falls through all rules, mark as Needs Manual Review
    row['Validation_Flag'] = 'Needs Manual Review'
    return row

print("Applying rules to SNOMED dataset...")
df = df.apply(apply_rules, axis=1)

# Summary of changes
print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

# Restore original column names for saving
df.columns = original_columns

df.to_excel(output_path, index=False)
print(f"\nSaved auto-corrected file to: {output_path}")
