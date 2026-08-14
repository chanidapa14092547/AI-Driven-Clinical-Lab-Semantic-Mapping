# Read Me

## Objective
- เชื่อมโยงข้อมูลการตรวจ LAB ที่แนะนำกับ ICD-10  ไปสู่ 
    - TMLT
    - SNOMED-CT
        - กลุ่ม Procedure
        - กลุ่ม Regime/Therapy

## Data
### ICD-LAB.xlsx
ตารางเชื่อมโยงระหว่างกลุ่ม ICD-10 และ รายการตรวจ LAB ที่แนะนำ

### ICD102016.xlsx
รายการ ICD-10 ทั้งหมด

### TMLT_FULL20260602.xlsx
รายการ TMLT โดย column หลักที่ใช้ในการ map มีดังนี้
- TMLT_Name: ชื่อทางการของการตรวจ Lab
- COMPONENT: องค์ประกอบ/สารเคมี ที่ต้องการตรวจ
- SPECIMEN: สารคัดหลั่ง/ประเภท ของสิ่งส่งตรวจ
- METHOD: วิธีการตรวจ (ถ้ามี)

### sct_concept
ชื่อของ SNOMED-CT

### sct_term
ชื่ออื่นของ SNOMED-CT



## output ที่ต้องการ
1. ไฟล์ .xlsx map ไปหา TMLT โดยมี column ดังนี้
    - ICD-10 (รหัสที่กระจายแล้ว)
    - รายกายตรวจ lab
    - รหัส TMLT
    - ชื่อ TMLT
    - Component TMLT
    - รหัส LOINC_NUM (ได้จากไฟล์ TMLT (ถ้ามี))
    - รหัส CGD_CODE (ได้จากไฟล์ TMLT (ถ้ามี))

2. ไฟล์ .xlsx map ไปหา SNOMED-CT โดยมี column ดังนี้
    - ICD-10 (รหัสที่กระจายแล้ว)
    - รายกายตรวจ lab
    - รหัส ConceptID
    - ชื่อ FSN

3. โค้ดที่ใช้ในการ Map
### หมายเหตุ
**แนะนำให้ใช้ AI ในการตรวจผลลัพธ์เป็น label set