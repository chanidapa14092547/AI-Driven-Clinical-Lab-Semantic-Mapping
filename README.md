# AI-Driven Clinical Lab Semantic Mapping (ICD-10 to TMLT & SNOMED-CT)

*🇹🇭 [คลิกที่นี่เพื่ออ่านเวอร์ชันภาษาไทย (Click here for Thai version)](#เวอร์ชันภาษาไทย-thai-version)*

This project provides an intelligent, automated pipeline to map free-text clinical laboratory items from ICD-10 data to standardized vocabularies: **TMLT** (Thai Medical Laboratory Terminology) and **SNOMED-CT**. 

## Innovation: SapBERT Semantic Mapping
Traditional fuzzy-matching methods often fail to capture the true clinical meaning of terms (e.g. "Stool culture for Vibrio cholerae" vs "Vibrio cholerae culture"). 

To achieve maximum accuracy and follow strict project guidelines, this project utilizes **Deep Learning** via the `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` model (a state-of-the-art Bio-Clinical BERT). This model converts clinical texts into high-dimensional vector embeddings, allowing us to compute **Cosine Similarity** to find the most semantically equivalent standard terms.

### Methodological Highlights
1. **TMLT Attribute Combination**: Instead of just using names, the system dynamically combines 4 core TMLT attributes (`TMLT_Name`, `COMPONENT`, `SPECIMEN`, `METHOD`) into a single descriptive sentence to capture the most accurate clinical context before semantic matching.
2. **Strict Category Filtering (SNOMED-CT)**: The pipeline adheres to precise target guidelines by exclusively searching within the `procedure` and `regime/therapy` categories of SNOMED-CT, preventing false-positive mappings to morphological abnormalities or unrelated disorders.
3. **Hard Conflict Rules & Confidence Labeling**: The model retrieves the Top-5 candidates and applies strict domain rules (e.g. Antigens vs Antibodies). It then automatically provides an `AI_Label` (`High Confidence` for scores >= 0.85, etc.) to guide medical coders.
4. **Automated F1-Score Evaluation**: Dedicated evaluation scripts (`step3b` and `step4b`) automatically sample the results and simulate LLM-based heuristic checks to generate accuracy reports (Precision, Recall, F1-Score) for stakeholders.

## Project Structure

- `src/`: Python scripts for the pipeline.
  - `step1_preprocessing.py`: Parses ICD ranges and splits semicolon-separated Lab items.
  - `step2_embedding_setup.py`: Initializes the SapBERT model.
  - `step3_tmlt_mapping.py`: Performs Semantic Mapping against the TMLT database.
  - `step3b_tmlt_evaluate_accuracy.py`: Samples and evaluates TMLT mapping accuracy (F1-Score).
  - `step4_snomed_mapping.py`: Performs Semantic Mapping against SNOMED-CT.
  - `step4b_snomed_evaluate_accuracy.py`: Samples and evaluates SNOMED-CT mapping accuracy (F1-Score).
- `output/`: Generated mapped data and reports.
  - `step1_expanded_icd_lab.csv`: Expanded list of unique ICD-10 and Lab item mappings.
  - `TMLT/`: Contains `ICD_to_TMLT.xlsx` and `LLM_Evaluation_Report.xlsx`.
  - `SNOMED/`: Contains `ICD_to_SNOMED.xlsx` and `LLM_Evaluation_Report_SNOMED.xlsx`.

## How to use
1. Install dependencies: `pip install pandas openpyxl sentence-transformers torch scikit-learn fastparquet`
2. Run the pipeline scripts in numerical order from the `src/` directory.

## Manual QA & Expert Review (Current Phase)
While the Bio-ClinicalBERT model provides highly accurate semantic similarity mappings, differences between international clinical guidelines (ICD-10) and national laboratory standards (TMLT) require expert review. 
To address "AI Hallucinations" (e.g., the AI mapping a DNA detection test to an Antigen test because the DNA test does not exist in the national standard), we have implemented a **Manual Quality Assurance** phase:
- **Line-by-Line Review**: Expert medical coders review the AI's output (`ICD_to_TMLT.xlsx`) in batches.
- **Strict Method & Specimen Rules**: Ensuring that the requested specimen (e.g., Sputum vs. CSF) and method (e.g., Culture vs. NAAT) precisely match the TMLT constraints.
- **Fallback to Unmapped (`-`)**: Any test that cannot be safely and clinically mapped to the TMLT standard is explicitly unmapped (set to `-`) to prevent false or non-compliant medical billing records.

---
---

# เวอร์ชันภาษาไทย (Thai Version)

โปรเจกต์นี้คือระบบสำหรับการจับคู่คำสั่งตรวจทางห้องปฏิบัติการ (Lab Orders) แบบข้อความอิสระ (Free-text) จากฐานข้อมูลรหัสโรค ICD-10 ให้เข้ากับรหัสมาตรฐานสากล 2 มาตรฐาน ได้แก่: **TMLT** (รหัสมาตรฐานทางห้องปฏิบัติการทางการแพทย์ไทย) และ **SNOMED-CT**

## นวัตกรรม: การวิเคราะห์ความหมายด้วย SapBERT
การจับคู่คำด้วยวิธี Fuzzy-matching มักจะล้มเหลวในการทำความเข้าใจบริบททางการแพทย์ (เช่น "Stool culture for Vibrio cholerae" กับ "Vibrio cholerae culture")

เพื่อให้ได้ความแม่นยำสูงสุดและเป็นไปตามข้อกำหนดที่เข้มงวด โปรเจกต์นี้จึงนำเทคโนโลยี **Deep Learning** มาใช้ผ่านโมเดล `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` ซึ่งสามารถแปลงข้อความทางการแพทย์ให้เป็นตัวเลขเวกเตอร์มิติสูง (Embeddings) ทำให้เราสามารถคำนวณหา **ความคล้ายคลึงทางความหมาย (Cosine Similarity)** เพื่อจับคู่รหัสที่ถูกต้องที่สุดได้

### จุดเด่นของกระบวนการทำงาน
1. **ผสมผสานมิติข้อมูล TMLT (Attribute Combination)**: ระบบไม่ได้อ่านแค่ชื่อแล็บ แต่นำ 4 แกนข้อมูลของ TMLT (`TMLT_Name`, `COMPONENT`, `SPECIMEN`, `METHOD`) มารวมกันเป็นประโยคเดียว เพื่อให้ AI เข้าใจบริบทครบทุกมิติ
2. **การตีกรอบหมวดหมู่ SNOMED-CT**: ระบบตีกรอบการค้นหาไว้อย่างเข้มงวดเฉพาะหมวด `procedure` และ `regime/therapy` เท่านั้น **(หมายเหตุเรื่อง Therapy):** ใน SNOMED-CT หัตถการเชิงบำบัดรักษา (เช่น เคมีบำบัด) จะถูกจัดอยู่ในหมวด `regime/therapy` การรวมหมวดนี้เข้ามาจึงมีความครอบคลุมโดยไม่ไปดึงพวกรหัสชื่อโรคมาปน
3. **ระบบกฎเหล็กและการให้คะแนน (Rules & Confidence)**: AI จะดึง 5 อันดับแรก มาผ่าน "กฎเหล็ก" (เช่น ดักจับ Antigen vs Antibody) และติดป้ายความมั่นใจ (AI_Label) ตามเกณฑ์ดังนี้:
   - **Very High Confidence (คะแนน >= 0.85)**: ตรงและถูกต้องแทบจะไม่มีข้อผิดพลาด   
   - **High Confidence (คะแนน >= 0.70)**: ความหมายตรงกัน แต่อาจเขียนคนละรูปแบบ
   - **Medium/Low/Rejected (คะแนน < 0.70)**: อาจมีความกำกวม ระบบจะส่งต่อให้ระบบกฎ (Rule-Based) และ Gemini ตรวจสอบ
4. **จำลองการตรวจวัดผลอัตโนมัติ (F1-Score)**: สคริปต์ `step3b` และ `step4b` จะสุ่มตรวจผลลัพธ์เพื่อคำนวณค่า Precision, Recall และ F1-Score สำหรับนำไปทำรายงาน

## โครงสร้างโปรเจกต์

- `src/`: โฟลเดอร์เก็บโค้ด Python ทั้งหมด
  - `step1_preprocessing.py`: คลีนและแยกชื่อ Lab จากฐานข้อมูล
  - `step3_tmlt_mapping.py` / `step4_snomed_mapping.py`: รัน AI SapBERT เพื่อจับคู่รหัส
  - `step3b_...` / `step4b_...`: สคริปต์สร้างรายงานประเมินความแม่นยำ F1-Score
  - `auto_correct_scripts/`: สคริปต์สำหรับระบบ Rule-based และ Gemini
- `output/`: โฟลเดอร์เก็บผลลัพธ์
  - `TMLT/`: ไฟล์ Excel ผลลัพธ์ของ TMLT และรายงาน F1-Score
  - `SNOMED/`: ไฟล์ Excel ผลลัพธ์ของ SNOMED และรายงาน F1-Score

## วิธีการใช้งาน
1. ติดตั้ง Dependencies: `pip install pandas openpyxl sentence-transformers torch scikit-learn fastparquet`
2. รันสคริปต์ Step 1 ถึง 4 ตามลำดับตัวเลขในโฟลเดอร์ `src/` เพื่อสร้างผลลัพธ์และทำความสะอาดข้อมูล

## Data Cleaning & Validation (ระบบตรวจสอบขั้นสุดท้าย)
แม้ว่า SapBERT จะฉลาดมาก แต่วิธีการเขียนสั่งแล็บมักมีความซับซ้อน เราจึงพัฒนาระบบตรวจสอบอัตโนมัติ 2 ชั้น:
- **Rule-Based Batches**: แล็บที่พบการจับคู่ผิดมากที่สุด (เช่น CBC, HbA1c) ถูกตั้งกฎล็อกบังคับจับคู่ให้มีความถุกต้อง
- **AI Mega Batch Validation**: แล็บหายากหรือมีความกำกวม จะถูกรวบรวมส่งให้ LLM ระดับสูง (Gemini 1.5 Pro) ทำงานเป็น "Medical Coder" ตรวจสอบและให้เหตุผลทางการแพทย์
- **ระบบ Failsafe (`-`)**: แล็บใดที่ระบบหรือ Gemini มองว่าหาคู่ที่ตรงสเปคไม่ได้จริงๆ จะถูกปัดตกให้เป็นค่าว่าง (`-`) ทันที เพื่อป้องกันการนำรหัสที่ผิดไปใช้งาน
