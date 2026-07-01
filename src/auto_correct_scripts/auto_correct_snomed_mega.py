import pandas as pd
import json
import time
from google import genai
from google.genai import types

file_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED_Auto_Corrected.xlsx'
output_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/SNOMED/ICD_to_SNOMED_Auto_Corrected.xlsx'

df = pd.read_excel(file_path)
original_columns = df.columns.tolist()
df.columns = ['ICD_10', 'Test_Name', 'ConceptID', 'FSN', 'Similarity', 'Confidence', 'Validation_Flag']

# 1. Handle "No Data" rows
no_data_mask = (df['Validation_Flag'] == 'Needs Manual Review') & (df['Test_Name'] == '-')
df.loc[no_data_mask, 'ConceptID'] = '-'
df.loc[no_data_mask, 'FSN'] = '-'
df.loc[no_data_mask, 'Validation_Flag'] = 'Auto Corrected (No Data)'

# 2. Extract remaining unique Test Names
needs_review_mask = df['Validation_Flag'] == 'Needs Manual Review'
unique_tests = df.loc[needs_review_mask, 'Test_Name'].unique().tolist()
unique_tests = [t for t in unique_tests if str(t) != 'nan']

print(f"Total unique test names to map: {len(unique_tests)}")

key = "AQ.Ab8RN6LpxFJLYbt8AVtOAv-hS_sSLdnn6kEfau_qUaRM2VRywA"
client = genai.Client(api_key=key)

prompt_template = """You are a medical coding expert mapping laboratory and clinical tests to SNOMED CT procedure codes.
I will give you a list of test names. For each test, provide the best matching SNOMED CT procedure Concept ID and its Fully Specified Name (FSN).
If a test is too generic (e.g., "Hormone level", "Drug screen according to...", "Comprehensive toxicology"), output Concept ID "-" and FSN "-".
Return the result strictly as a valid JSON array of objects, with keys "Test_Name", "ConceptID", and "FSN".
Do NOT include any markdown formatting, code blocks, or extra text. Just output raw JSON.

Tests to map:
{tests}
"""

mapped_results = {}

batch_size = 50
for i in range(0, len(unique_tests), batch_size):
    batch = unique_tests[i:i+batch_size]
    tests_str = "\n".join(batch)
    prompt = prompt_template.format(tests=tests_str)
    
    print(f"Processing batch {i//batch_size + 1}/{(len(unique_tests)+batch_size-1)//batch_size}...")
    
    retries = 3
    while retries > 0:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            data = json.loads(text.strip())
            for item in data:
                mapped_results[item['Test_Name']] = (item['ConceptID'], item['FSN'])
            break
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(2)
            retries -= 1
            if retries == 0:
                print("Failed to process batch.")

# 3. Apply the results
def apply_final_mapping(row):
    if row['Validation_Flag'] != 'Needs Manual Review':
        return row
    
    test_name = row['Test_Name']
    if test_name in mapped_results:
        concept, fsn = mapped_results[test_name]
        row['ConceptID'] = concept
        row['FSN'] = fsn
        if concept == '-':
            row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
        else:
            row['Validation_Flag'] = 'Auto Corrected (AI Batch)'
    return row

print("Applying AI batch results to dataset...")
df = df.apply(apply_final_mapping, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved final auto-corrected file to: {output_path}")
