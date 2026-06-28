import pandas as pd
import os
import time
from pathlib import Path
from google import genai

base_dir = Path(__file__).resolve().parent.parent
output_dir = base_dir / "output"

# Parse .env manually
env_path = base_dir / ".env"
API_KEY = None
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=API_KEY)

print("Loading TMLT Mapping Results...")
df = pd.read_excel(os.path.join(output_dir, "ICD_to_TMLT.xlsx"))

# We want to sample across AI_Label to get a stratified sample
labels = df['AI_Label'].unique()
sample_size = 200

print(f"Total rows: {len(df)}")
# Perform stratified sampling
sampled_df = pd.DataFrame()
for label in labels:
    group = df[df['AI_Label'] == label]
    prop = len(group) / len(df)
    n = int(prop * sample_size)
    if n > 0:
        sampled_df = pd.concat([sampled_df, group.sample(n=min(n, len(group)), random_state=42)])

if len(sampled_df) < sample_size:
    remaining = sample_size - len(sampled_df)
    not_sampled = df.drop(sampled_df.index)
    sampled_df = pd.concat([sampled_df, not_sampled.sample(n=min(remaining, len(not_sampled)), random_state=42)])

sampled_df = sampled_df.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"Sampled {len(sampled_df)} rows for LLM evaluation.")

true_positive = 0
false_positive = 0
true_negative = 0
false_negative = 0
results_log = []

def call_gemini(lab_item, tmlt_name, tmlt_code):
    if tmlt_code == '-':
        prompt = f"""
You are an expert clinical laboratory coder.
The doctor ordered the following lab test: "{lab_item}"

The AI mapping system decided to REJECT this and mapped it to 'No Match' because the order was too broad, empty, or clinically unmappable.
Is this the CORRECT clinical decision?
Answer ONLY "True" (if it was correct to reject) or "False" (if it should have been mapped).
"""
    else:
        prompt = f"""
You are an expert clinical laboratory coder.
The doctor ordered the following lab test: "{lab_item}"

The AI mapping system matched it to this standard test name: "{tmlt_name}"
Are these two tests clinically equivalent?
Answer ONLY "True" (if it's a correct clinical match) or "False" (if it's a wrong match).
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10,
            )
        )
        if not response.text:
            return None
        text = response.text.strip().lower()
        if "true" in text:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

print("\nStarting LLM Evaluation (this will take about 15 minutes to respect rate limits)...")

for idx, row in sampled_df.iterrows():
    lab = row['รายการตรวจ lab']
    tmlt = row['ชื่อ TMLT']
    code = row['รหัส TMLT']
    ai_label = row['AI_Label']
    
    print(f"[{idx+1}/{len(sampled_df)}] Eval: {str(lab)[:30]} -> {str(tmlt)[:30]} ", end="", flush=True)
    
    system_predicted_positive = (code != '-')
    llm_agrees = call_gemini(lab, tmlt, code)
    
    if llm_agrees is None:
        print("[API Error, skipping]")
        time.sleep(5)
        continue
        
    print(f"[LLM says: {llm_agrees}]")
    
    if system_predicted_positive:
        if llm_agrees:
            true_positive += 1
        else:
            false_positive += 1
    else:
        if llm_agrees:
            true_negative += 1
        else:
            false_negative += 1
            
    results_log.append({
        'Lab_Item': lab,
        'TMLT_Name': tmlt,
        'AI_Label': ai_label,
        'System_Matched': system_predicted_positive,
        'LLM_Agreed': llm_agrees
    })
    
    time.sleep(13) # 13 seconds ensures we stay under 5 RPM for brand new accounts

print("\n=== Evaluation Results ===")
print(f"True Positives (Correct Matches): {true_positive}")
print(f"False Positives (Wrong Matches): {false_positive}")
print(f"True Negatives (Correct Rejections): {true_negative}")
print(f"False Negatives (Wrong Rejections): {false_negative}")

precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
accuracy = (true_positive + true_negative) / len(results_log) if len(results_log) > 0 else 0

print(f"\nAccuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1_score:.4f}")

report_df = pd.DataFrame(results_log)
report_path = os.path.join(output_dir, "LLM_Evaluation_Report.xlsx")
report_df.to_excel(report_path, index=False)
print(f"\nSaved detailed report to {report_path}")
