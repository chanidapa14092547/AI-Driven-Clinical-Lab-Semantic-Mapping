import pandas as pd
import json
import time
from google import genai
from google.genai import types

file_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/TMLT/ICD_to_TMLT.xlsx'
output_path = 'C:/Users/USER/Downloads/Mapping-Project-Final/output/TMLT/ICD_to_TMLT.xlsx'

print("Reading dataset...")
df = pd.read_excel(file_path)
original_columns = df.columns.tolist()
df.columns = [
    'ICD_10', 'Test_Name', 'TMLT_ID', 'TMLT_Name', 'Component', 'Specimen', 'Method',
    'LOINC_NUM', 'CGD_CODE', 'Similarity', 'Comp_Score', 'Spec_Score', 'Meth_Score',
    'Final_Score', 'AI_Label', 'Validation_Flag'
]

# 1. Handle "No Data" rows just in case
no_data_mask = (df['Validation_Flag'] == 'Needs Manual Review') & (df['Test_Name'] == '-')
df.loc[no_data_mask, 'TMLT_ID'] = '-'
df.loc[no_data_mask, 'TMLT_Name'] = '-'
df.loc[no_data_mask, 'Component'] = '-'
df.loc[no_data_mask, 'Specimen'] = '-'
df.loc[no_data_mask, 'Method'] = '-'
df.loc[no_data_mask, 'LOINC_NUM'] = '-'
df.loc[no_data_mask, 'Validation_Flag'] = 'Auto Corrected (No Data)'

# 2. Extract remaining unique rows
needs_review_mask = df['Validation_Flag'] == 'Needs Manual Review'
unique_items = df[needs_review_mask][['Test_Name', 'TMLT_ID', 'TMLT_Name', 'Component', 'Specimen', 'Method', 'LOINC_NUM']].drop_duplicates()
unique_items = unique_items.dropna(subset=['Test_Name'])
unique_items = unique_items[unique_items['Test_Name'] != '-']

items_list = unique_items.to_dict('records')
print(f"Total unique test mappings to evaluate: {len(items_list)}")

key = "AQ.Ab8RN6LpxFJLYbt8AVtOAv-hS_sSLdnn6kEfau_qUaRM2VRywA"
client = genai.Client(api_key=key)

prompt_template = """You are an expert clinical laboratory data mapping evaluator.
I will give you a list of proposed TMLT (Thai Medical Laboratory Terminology) / LOINC mappings.
For each item, you are given the original Test_Name, and the AI's predicted mapping (TMLT_Name, Component, Specimen, Method).
Your job is to determine if the mapping is CLINICALLY ACCURATE and SAFE to use.
If the prediction is completely hallucinated (e.g. matching a bacteria to a completely different virus) or makes no sense, output "Valid": false.
If the prediction is reasonable, accurate, and safe, output "Valid": true.
If the Test_Name is too generic, ambiguous, or conditional (e.g. "Lab test if available", "Additional stain"), output "Valid": false.

Return the result strictly as a valid JSON array of objects, with keys "Test_Name" and "Valid" (boolean).
Do NOT include any markdown formatting, code blocks, or extra text. Just output raw JSON.

Items to evaluate:
{items}
"""

evaluation_results = {}

batch_size = 30
for i in range(0, len(items_list), batch_size):
    batch = items_list[i:i+batch_size]
    
    # Format batch for prompt
    batch_str_list = []
    for item in batch:
        s = f"Test_Name: {item['Test_Name']} | Predicted: [{item['TMLT_Name']} | Comp: {item['Component']} | Spec: {item['Specimen']} | Meth: {item['Method']}]"
        batch_str_list.append(s)
        
    tests_str = "\n".join(batch_str_list)
    prompt = prompt_template.format(items=tests_str)
    
    print(f"Processing batch {i//batch_size + 1}/{(len(items_list)+batch_size-1)//batch_size}...")
    
    retries = 3
    while retries > 0:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            data = json.loads(text.strip())
            for item in data:
                evaluation_results[item['Test_Name']] = item['Valid']
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
    if test_name in evaluation_results:
        is_valid = evaluation_results[test_name]
        
        if is_valid:
            row['Validation_Flag'] = 'Auto Corrected (AI Batch)'
        else:
            row['TMLT_ID'] = '-'
            row['TMLT_Name'] = '-'
            row['Component'] = '-'
            row['Specimen'] = '-'
            row['Method'] = '-'
            row['LOINC_NUM'] = '-'
            row['CGD_CODE'] = '-'
            row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
    else:
        # Failsafe if API missed something
        row['TMLT_ID'] = '-'
        row['TMLT_Name'] = '-'
        row['Component'] = '-'
        row['Specimen'] = '-'
        row['Method'] = '-'
        row['LOINC_NUM'] = '-'
        row['CGD_CODE'] = '-'
        row['Validation_Flag'] = 'Auto Corrected (Unmapped)'
            
    return row

print("Applying AI batch results to dataset...")
df = df.apply(apply_final_mapping, axis=1)

print("\nSummary of Validation Flags:")
print(df['Validation_Flag'].value_counts())

df.columns = original_columns
df.to_excel(output_path, index=False)
print(f"\nSaved final auto-corrected file to: {output_path}")
