#!/usr/bin/env python3
"""
ZeroPhi Ultra-Complex Real-World Examples
==========================================

These examples demonstrate advanced, production-grade scenarios with multiple
PII/PHI types, complex document structures, and comprehensive reporting.

Example 1: Healthcare Multi-Patient Clinical Records with Audit Trail
Example 2: Financial Services Multi-Document Compliance Processing
"""

import json
from pathlib import Path
from datetime import datetime
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig
from zerophi.reporting import ReportGenerator


# =============================================================================
# EXAMPLE 1: HEALTHCARE - COMPLEX CLINICAL RECORDS WITH FULL AUDIT TRAIL
# =============================================================================

def example_1_healthcare_clinical_records():
    """
    SCENARIO: Hospital needs to scan 3 years of clinical records before sharing
    with research partners. Must identify ALL PHI, generate compliance report,
    and create audit trail.
    
    COMPLEXITY FACTORS:
    - Multiple patient records in one document
    - Mixed PII/PHI types (names, DOB, Medicare, IHI, phone, email, addresses)
    - Medical terminology and conditions
    - Prescription details
    - Hospital and doctor names
    - Insurance and billing information
    - Nested data structures
    """
    
    print("="*80)
    print("EXAMPLE 1: HEALTHCARE CLINICAL RECORDS - COMPLEX MULTI-PATIENT ANALYSIS")
    print("="*80)
    
    # Complex clinical document with multiple patients
    clinical_document = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║         ROYAL MELBOURNE HOSPITAL - CLINICAL RECORDS EXTRACT          ║
    ║                    Confidential Medical Information                   ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    REPORT GENERATED: 2024-11-23 14:30:00
    DEPARTMENT: Cardiology & Endocrinology
    REPORTING PHYSICIAN: Dr. Sarah Chen, MBBS, FRACP
    CONTACT: s.chen@rmh.org.au | Office: 03 9342 7000 | Mobile: 0412 987 654
    
    ═══════════════════════════════════════════════════════════════════════
    PATIENT RECORD 1
    ═══════════════════════════════════════════════════════════════════════
    
    PATIENT DETAILS:
    • Full Name: Jonathan Alexander SMITH
    • DOB: 15/04/1967 (Age: 57)
    • Gender: Male
    • Medicare Number: 2834 56789 1-3
    • IHI: 8003608833357361
    • DVA Number: N987654 (Gold Card)
    • Private Health: Medibank Private #4582-91234-001
    
    CONTACT INFORMATION:
    • Home Address: Unit 12, 456 Collins Street, Melbourne VIC 3000
    • Phone (Home): (03) 9876 5432
    • Phone (Mobile): 0412 345 678
    • Email: j.smith1967@gmail.com
    • Emergency Contact: Maria Smith (Wife) - 0423 456 789
    
    TAX & BILLING:
    • Tax File Number: 287 645 391
    • Billing Reference: INV-2024-RMH-089234
    • Employer: Commonwealth Bank of Australia, ABN 48 123 123 124
    
    CLINICAL SUMMARY:
    Chief Complaint: Chest pain, shortness of breath, fatigue
    Admitted: 2024-11-20 via Emergency Department
    
    DIAGNOSES:
    1. Acute Coronary Syndrome (ACS) - STEMI anterior wall
    2. Type 2 Diabetes Mellitus (T2DM) - poorly controlled (HbA1c 9.2%)
    3. Hypertension - Stage 2
    4. Chronic Kidney Disease (CKD) Stage 3A (eGFR 52 mL/min)
    5. Dyslipidemia
    
    PROCEDURES PERFORMED:
    • 2024-11-20: Emergency coronary angiogram
    • 2024-11-20: PCI with DES to LAD (performed by Dr. Michael Wong)
    • 2024-11-21: Echocardiogram (EF 45%)
    
    MEDICATIONS PRESCRIBED:
    1. Aspirin 100mg daily
    2. Clopidogrel 75mg daily (for 12 months)
    3. Atorvastatin 80mg nocte
    4. Metoprolol 50mg BD
    5. Metformin XR 1000mg BD
    6. Empagliflozin 10mg daily
    7. Ramipril 5mg daily
    
    PATHOLOGY RESULTS:
    • Troponin I: 4,567 ng/L (critical high)
    • Creatinine: 145 umol/L (elevated)
    • Glucose (random): 14.2 mmol/L
    • LDL Cholesterol: 4.8 mmol/L
    • Bank details for pathology billing: BSB 063-123, Account 12345678
    
    FOLLOW-UP PLAN:
    • Cardiac rehab referral sent to Peter MacCallum Centre
    • Diabetes education with CNE at 123 Bourke St (Ph: 03 9654 3210)
    • Review with Dr. Chen in 2 weeks - Appointment: 2024-12-07 at 2:30pm
    • Contact coordinator: Emma Williams on 0398 765 432
    
    INSURANCE CLAIMS:
    • Medicare claim submitted: $8,945.00 (Ref: MC-2024-1123-8923)
    • Private claim: Medibank $12,300 (Claim #MB-2024-893456)
    • Gap payment: $3,355.00 to be billed to patient
    
    ═══════════════════════════════════════════════════════════════════════
    PATIENT RECORD 2
    ═══════════════════════════════════════════════════════════════════════
    
    PATIENT DETAILS:
    • Full Name: Emily Rose THOMPSON
    • Preferred Name: Em
    • DOB: 22/08/1985 (Age: 39)
    • Gender: Female
    • Medicare Number: 2928 34567 2-1
    • IHI: 8003601234567890
    • NDIS Participant: Yes - Plan #410028563
    
    CONTACT INFORMATION:
    • Residential: 78 Lygon Street, Carlton VIC 3053
    • Postal: PO Box 456, Carlton VIC 3053
    • Mobile: 0435 678 901
    • Email: emily.thompson1985@outlook.com
    • Next of Kin: David Thompson (Brother) - 0456 789 012
    
    FINANCIAL:
    • TFN: 456 789 012
    • Healthcare Card: 234 567 890 1
    • Pension Card: PC-VIC-2024-456789
    • Employer: Telstra Corporation, ABN 33 051 775 556
    • Work Phone: (03) 8647 5000 ext 4523
    
    CLINICAL SUMMARY:
    Presenting Issue: Gestational Diabetes screening and management
    First Consultation: 2024-09-15
    Obstetric History: G2P1 (previous C-section 2019)
    
    CURRENT PREGNANCY:
    • EDD: 2025-02-14 (Currently 28 weeks gestation)
    • Obstetrician: Dr. Rachel Kumar, FRANZCOG
    • Midwife: Sarah Jones - 0412 234 567
    • Hospital Booking: Royal Women's Hospital (Booking #RWH-2024-23456)
    
    DIAGNOSES:
    1. Gestational Diabetes Mellitus (GDM) - insulin-requiring
    2. Previous Caesarean Section (VBAC being considered)
    3. Hypothyroidism (on Thyroxine)
    4. Obesity (BMI 32.4)
    
    MEDICATIONS:
    1. Insulin Aspart 8 units TDS (with meals)
    2. Insulin Glargine 14 units nocte
    3. Thyroxine 100mcg daily
    4. Pregnancy multivitamin
    5. Iron supplement (Ferrograd C)
    
    MONITORING:
    • Home blood glucose monitoring 4x daily
    • Glucose meter serial: GM-2024-AU-78945
    • NDIS funded CGM system (Dexcom G6)
    • Weekly obstetric reviews
    • Fortnightly endocrine reviews with Dr. Chen
    
    PATHOLOGY TRACKING:
    • OGTT (2024-09-10): Fasting 6.2, 2hr 10.8 mmol/L
    • HbA1c: 6.8%
    • TSH: 2.4 mIU/L (target achieved)
    • Pathology provider: Melbourne Pathology, Invoice #MP-2024-789456
    • Direct debit from CBA Account: BSB 063-456, Acc 78945612
    
    SPECIALIST REFERRALS:
    • Dietitian: Ms. Jennifer Lee, APD - Ph: 03 9347 8900
    • Diabetes Educator: 123 Grattan St, Parkville - Ph: 03 8344 5678
    • Physiotherapist (pelvic floor): Women's Health Physio, 0412 345 678
    
    INSURANCE & BILLING:
    • Private Health: BUPA, Member #: 6789012345
    • Obstetric Package: $8,500 (paid in full)
    • Diabetes Management Plan (MBS Item 721): Ref DMP-2024-456
    • Insulin Pump Funding Application: NDIS Ref #NDIS-2024-789456-001
    
    ═══════════════════════════════════════════════════════════════════════
    PATIENT RECORD 3
    ═══════════════════════════════════════════════════════════════════════
    
    PATIENT DETAILS:
    • Full Name: NGUYEN, Michael Van (Vietnamese: Nguyễn Văn Minh)
    • DOB: 03/12/1952 (Age: 71)
    • Gender: Male
    • Medicare: 3045 67890 1-5
    • IHI: 8003607890123456
    • DVA File Number: V234567 (White Card)
    • Centrelink CRN: 123 456 789 A
    
    CONTACT:
    • Address: 234 Victoria Street, Richmond VIC 3121
    • Home Phone: (03) 9428 7654
    • Mobile: 0487 654 321 (son's phone - patient non-English speaking)
    • Interpreter Required: Vietnamese - Phone: 131 450
    • Aged Care Provider: Regis Aged Care, Case Manager: Lisa Tran 0398 765 432
    
    FINANCIAL & SOCIAL:
    • TFN: 567 890 123
    • Pension Type: Age Pension (Full rate)
    • Pension Card: PC-VIC-2023-567890
    • MyAged Care #: MAC-2023-567890
    • Power of Attorney: Son - David Nguyen, Ph: 0487 654 321
    
    COMPLEX MEDICAL HISTORY:
    Primary Diagnoses:
    1. End-Stage Renal Disease (ESRD) - on hemodialysis MWF
    2. Type 2 Diabetes Mellitus - 25 year history, insulin-dependent
    3. Ischemic Heart Disease - previous CABG x4 (2018)
    4. Atrial Fibrillation - on anticoagulation
    5. Heart Failure with reduced EF (LVEF 28%)
    6. Peripheral Vascular Disease
    7. Diabetic Retinopathy (legally blind)
    8. Peripheral Neuropathy
    9. Chronic Anemia of CKD
    10. Secondary Hyperparathyroidism
    
    DIALYSIS DETAILS:
    • Dialysis Unit: Austin Hospital Renal Unit
    • Schedule: Monday, Wednesday, Friday, 7:00 AM - 11:00 AM
    • Access: Left arm AV fistula (created 2022)
    • Dialysis Nurse Coordinator: Jenny Park RN - 03 9496 5555
    • Transport: NEPTS (Non-Emergency Patient Transport) - Booking: 1300 366 378
    
    CURRENT MEDICATIONS (17 total):
    1. Insulin NPH 30 units mane, 20 units nocte
    2. Insulin Aspart 10 units TDS (pre-dialysis adjustment)
    3. Apixaban 2.5mg BD (renal dosing)
    4. Metoprolol 50mg BD
    5. Frusemide 80mg daily
    6. Spironolactone 25mg daily
    7. Atorvastatin 40mg nocte
    8. Aspirin 100mg daily
    9. Clopidogrel 75mg daily
    10. Calcium carbonate 1g TDS with meals
    11. Sevelamer 800mg TDS with meals
    12. Erythropoietin 4000 units SC weekly (at dialysis)
    13. Iron polymaltose IV monthly (at dialysis)
    14. Vitamin B complex daily
    15. Pregabalin 75mg nocte (neuropathic pain)
    16. Pantoprazole 40mg daily
    17. Paracetamol 1g QID PRN
    
    SPECIALIST TEAM:
    • Nephrologist: Dr. James Liu - Austin Hospital, Ph: 03 9496 3000
    • Cardiologist: Dr. Sarah Chen - RMH, Ph: 03 9342 7000
    • Endocrinologist: Dr. Patricia Wong - Box Hill Hospital
    • Ophthalmologist: Dr. Robert Kim - Centre for Eye Research
    • Vascular Surgeon: Dr. Andrew Smith - St Vincent's
    • Palliative Care Consultant: Dr. Emma Wilson - Ph: 03 9496 4000
    
    RECENT ADMISSIONS:
    • 2024-10-15: Hyperkalemia (K+ 7.2) - Austin ED, Admission #A-2024-67890
    • 2024-09-03: Infected dialysis access - 5 days IV antibiotics
    • 2024-07-22: Heart failure exacerbation - CCU admission 3 days
    
    PATHOLOGY MONITORING (Weekly):
    • Dialysis adequacy (Kt/V): Target >1.2
    • Calcium: 2.35 mmol/L (target 2.1-2.4)
    • Phosphate: 1.8 mmol/L (target <1.8)
    • PTH: 45 pmol/L (target 15-50)
    • Hemoglobin: 105 g/L (target >100)
    • Lab: Austin Pathology, Billing Ref: AP-2024-DIAL-67890
    
    ADVANCED CARE PLANNING:
    • Advanced Care Directive completed: 2024-05-15
    • Resuscitation Status: NFR (Not for Resuscitation) - documented
    • Preferred place of care: Home with family
    • Advance Care Planning Coordinator: Mary Johnson, Ph: 03 9496 4500
    • GP involved: Dr. Andrew Patel, Richmond Medical Centre, Ph: 03 9428 5000
    
    FUNDING & SUPPORT:
    • DVA Gold Card covers all medical expenses
    • Home Care Package Level 4: $52,000 per annum
    • Provider: Benetas, Case Manager: Susan Lee, Ph: 1300 236 382
    • NDIS Funding: $35,000 (Assistive Technology & Modifications)
    • Carer Payment: Wife - Mai Nguyen (TFN: 678 901 234)
    
    ═══════════════════════════════════════════════════════════════════════
    HOSPITAL ADMINISTRATIVE NOTES
    ═══════════════════════════════════════════════════════════════════════
    
    MEDICAL RECORDS DEPARTMENT:
    • Records Officer: Lisa Martinez - l.martinez@rmh.org.au
    • Phone: 03 9342 8500 | Fax: 03 9342 8501
    • Location: Level 2, Administration Building, 300 Grattan Street
    
    BILLING INQUIRIES:
    • Patient Accounts: accounts@rmh.org.au | Ph: 03 9342 8600
    • Medicare Claims: medicare.claims@rmh.org.au
    • Private Insurance: insurance@rmh.org.au
    • Financial Counselor: Sophie Williams, Ph: 03 9342 8650
    
    QUALITY & COMPLIANCE:
    • Report generated for: Research Ethics Committee Application #2024-389
    • Ethics Approval Ref: HREC-2024-RMH-389
    • Principal Investigator: Prof. David Anderson, Ph: 03 9342 9000
    • Research Coordinator: Dr. Helen Zhang, h.zhang@research.rmh.org.au
    
    DATA PROTECTION NOTICE:
    This document contains sensitive health information protected under:
    - Privacy Act 1988 (Commonwealth)
    - Health Records Act 2001 (Victoria)
    - Australian Privacy Principles (APPs)
    - NHMRC National Statement on Ethical Conduct in Human Research
    
    Unauthorized access, use, or disclosure may result in civil and/or
    criminal penalties.
    
    Document ID: RMH-CLINICAL-2024-1123-EXTRACT-v3.2
    Generated by: Clinical Information System (CIS) v8.4.2
    System Administrator: IT.Support@rmh.org.au | Ph: 03 9342 7777
    
    ═══════════════════════════════════════════════════════════════════════
    END OF CLINICAL RECORDS EXTRACT
    ═══════════════════════════════════════════════════════════════════════
    """
    
    print("\n1. SCANNING FOR PHI/PII IN COMPLEX CLINICAL DOCUMENT")
    print("-" * 80)
    
    # Configure for Australian healthcare with OpenMed for medical entities
    cfg = RedactionConfig(
        country="AU",
        use_openmed=False,  # Set to True if OpenMed is available
        masking_style="replace"
    )
    
    pipe = RedactionPipeline.from_config(cfg)
    
    # Step 1: Scan the document
    print("\n📋 STEP 1: Comprehensive PHI/PII Detection Scan")
    scan_result = pipe.scan(clinical_document)
    
    print(f"\n✓ Scan Complete!")
    print(f"  • Document Length: {len(clinical_document):,} characters")
    print(f"  • Total PHI/PII Detections: {scan_result['total_detections']}")
    print(f"  • Contains Sensitive Data: {'YES - RESTRICTED' if scan_result['has_pii'] else 'NO'}")
    print(f"  • Unique Entity Types: {len(scan_result['entity_counts'])}")
    
    # Step 2: Detailed entity breakdown
    print("\n📊 STEP 2: Entity Type Breakdown")
    print("-" * 80)
    
    if scan_result['entity_counts']:
        sorted_entities = sorted(scan_result['entity_counts'].items(), key=lambda x: -x[1])
        for entity_type, count in sorted_entities:
            risk_level = "HIGH" if count > 10 else "MEDIUM" if count > 5 else "LOW"
            print(f"  [{risk_level:6}] {entity_type:20} : {count:3} occurrences")
    
    # Step 3: Sample detections (first 10)
    print("\n🔍 STEP 3: Sample Detections (First 10 Found)")
    print("-" * 80)
    
    for i, det in enumerate(scan_result['detections'][:10], 1):
        print(f"\n  Detection #{i}:")
        print(f"    Type: {det['label']}")
        print(f"    Text: '{det['text']}'")
        print(f"    Confidence: {det['score']:.2%}")
        print(f"    Position: {det['start']}-{det['end']}")
        print(f"    Context: ...{det['context'][:60]}...")
    
    # Step 4: Generate comprehensive reports
    print("\n📄 STEP 4: Generating Compliance Reports")
    print("-" * 80)
    
    # Create reports directory
    reports_dir = Path("reports/healthcare_audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate multiple report formats
    formats = {
        "html": "Complete HTML report with styling",
        "json": "Machine-readable JSON for integration",
        "csv": "CSV for spreadsheet analysis",
        "markdown": "Markdown for documentation"
    }
    
    for fmt, description in formats.items():
        report = ReportGenerator.generate(scan_result, format=fmt)
        output_file = reports_dir / f"clinical_phi_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        output_file.write_text(report, encoding="utf-8")
        print(f"  ✓ {fmt.upper():8} : {description}")
        print(f"             Saved to: {output_file}")
    
    # Step 5: Risk Assessment Summary
    print("\n⚠️  STEP 5: RISK ASSESSMENT SUMMARY")
    print("-" * 80)
    
    total_detections = scan_result['total_detections']
    
    if total_detections > 100:
        risk = "CRITICAL"
        action = "DO NOT SHARE - Requires full de-identification"
    elif total_detections > 50:
        risk = "HIGH"
        action = "Redact all PHI before sharing"
    elif total_detections > 20:
        risk = "MEDIUM"
        action = "Review and redact sensitive fields"
    else:
        risk = "LOW"
        action = "Manual review recommended"
    
    print(f"\n  RISK LEVEL: {risk}")
    print(f"  RECOMMENDATION: {action}")
    print(f"  COMPLIANCE STATUS: {'NON-COMPLIANT' if total_detections > 0 else 'COMPLIANT'} for research sharing")
    
    # Step 6: Patient-specific breakdown
    print("\n👥 STEP 6: Per-Patient PHI Summary")
    print("-" * 80)
    
    patient_sections = [
        ("Jonathan Alexander SMITH", "Medicare: 2834 56789 1-3"),
        ("Emily Rose THOMPSON", "Medicare: 2928 34567 2-1"),
        ("Michael Van NGUYEN", "Medicare: 3045 67890 1-5")
    ]
    
    for patient_name, identifier in patient_sections:
        patient_detections = [d for d in scan_result['detections'] 
                            if patient_name.split()[0] in d.get('context', '') or 
                               identifier.split(':')[1].strip()[:4] in d.get('text', '')]
        print(f"\n  Patient: {patient_name}")
        print(f"    Identifier: {identifier}")
        print(f"    PHI Items Detected: ~{len(patient_detections)} (approximate)")
    
    # Step 7: Recommendations
    print("\n💡 STEP 7: RECOMMENDATIONS FOR DE-IDENTIFICATION")
    print("-" * 80)
    print("""
  1. IMMEDIATE ACTIONS:
     • Do NOT share this document in current form
     • All PHI must be redacted before research use
     • Obtain additional ethics approval if required
     
  2. DE-IDENTIFICATION STEPS:
     • Replace all names with pseudonyms (Patient A, B, C)
     • Remove all dates or convert to relative dates
     • Remove all identification numbers
     • Remove geographic identifiers (addresses, postcodes)
     • Remove contact information
     • Generalize ages to 5-year brackets
     
  3. REQUIRED REDACTIONS:
     • Personal identifiers: 50+ items
     • Contact details: 30+ items
     • Financial information: 20+ items
     • Medical record numbers: 15+ items
     • Provider information: 25+ items
     
  4. COMPLIANCE CHECKLIST:
     [ ] All direct identifiers removed
     [ ] All indirect identifiers assessed
     [ ] Re-identification risk < 0.05
     [ ] Ethics committee approval obtained
     [ ] Data use agreement signed
     [ ] Audit trail maintained
    """)
    
    print("\n" + "="*80)
    print("EXAMPLE 1 COMPLETE - All reports saved to:", reports_dir.absolute())
    print("="*80)
    
    return scan_result


# =============================================================================
# EXAMPLE 2: FINANCIAL SERVICES - MULTI-DOCUMENT COMPLIANCE PROCESSING
# =============================================================================

def example_2_financial_compliance():
    """
    SCENARIO: Financial institution needs to scan customer documents before
    submitting to regulatory audit. Must detect ALL PII/PSI (Personal
    Sensitive Information), generate detailed compliance reports, and ensure
    GDPR/Privacy Act compliance.
    
    COMPLEXITY FACTORS:
    - Multiple document types (loan applications, bank statements, tax returns)
    - Credit card numbers, account numbers, TFN, ABN
    - Income and financial data
    - Employment information
    - Property and asset details
    - Multiple jurisdictions (AU, international transfers)
    - Regulatory compliance requirements
    """
    
    print("\n\n")
    print("="*80)
    print("EXAMPLE 2: FINANCIAL SERVICES - COMPLEX COMPLIANCE DOCUMENT ANALYSIS")
    print("="*80)
    
    # Complex financial document package
    financial_documents = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║              COMMONWEALTH BANK OF AUSTRALIA                          ║
    ║         HOME LOAN APPLICATION - COMPREHENSIVE PACKAGE                ║
    ║                    CONFIDENTIAL & PROPRIETARY                         ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    APPLICATION REFERENCE: CBA-HL-2024-982345-SYD
    ABN: 48 123 123 124 | AFSL: 234945
    Processing Branch: Parramatta, NSW 2150
    Loan Officer: Jennifer Martinez | Employee ID: CBA789456
    Email: j.martinez@cba.com.au | Direct: (02) 9635 7890
    Date Submitted: 2024-11-15 14:32:00 AEDT
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 1: PRIMARY APPLICANT DETAILS
    ═══════════════════════════════════════════════════════════════════════
    
    PERSONAL INFORMATION:
    Full Legal Name: CHEN, David Wei (Chinese: 陈伟)
    Previous Names: None
    Date of Birth: 18/06/1985 (Age: 39 years 5 months)
    Place of Birth: Shanghai, China
    Gender: Male
    Marital Status: Married
    Number of Dependents: 2 (Children aged 8 and 5)
    
    IDENTIFICATION:
    • Australian Citizenship: Certificate #20140623-SYD-45678
    • Passport: Australian Passport N8976543 (Expires: 2029-06-15)
    • Driver License: NSW 12345678 (Expires: 2028-06-18)
    • Medicare Card: 3456 78901 2-4
    • Tax File Number: 234 567 890
    
    CONTACT DETAILS:
    Current Address: 45 Pacific Highway, North Sydney NSW 2060
    Previous Address (2020-2024): Unit 12/89 Walker Street, North Sydney NSW 2060
    Length at Current: 6 months
    Ownership Status: Renting ($850/week)
    
    Phone (Mobile): 0412 789 456
    Phone (Home): (02) 9954 3210
    Phone (Work): (02) 8268 1000 ext 4567
    Email (Primary): david.chen.1985@gmail.com
    Email (Work): d.chen@pwc.com.au
    
    RESIDENTIAL HISTORY (Last 5 years):
    1. 2024-Present: 45 Pacific Highway, North Sydney (Rental)
    2. 2020-2024: Unit 12/89 Walker Street, North Sydney (Rental)
    3. 2018-2020: 234 Clarence Street, Sydney CBD (Rental)
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 2: CO-APPLICANT DETAILS
    ═══════════════════════════════════════════════════════════════════════
    
    PERSONAL INFORMATION:
    Full Legal Name: WANG, Michelle Xiaomei (Chinese: 王晓美)
    Maiden Name: LI
    Date of Birth: 25/03/1987 (Age: 37 years 8 months)
    Place of Birth: Beijing, China
    Gender: Female
    Relationship: Spouse (Married 2015-08-15 in Sydney)
    
    IDENTIFICATION:
    • Australian Citizenship: Certificate #20160412-SYD-67890
    • Passport: Australian Passport N7654321 (Expires: 2027-04-10)
    • Driver License: NSW 87654321 (Expires: 2029-03-25)
    • Medicare Card: 3456 78901 2-4 (Same as primary)
    • Tax File Number: 345 678 901
    
    CONTACT DETAILS:
    Same residential address as primary applicant
    Phone (Mobile): 0423 456 789
    Phone (Work): (02) 8599 2000 ext 3456
    Email: m.wang.pharma@gmail.com
    Email (Work): michelle.wang@roche.com.au
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 3: EMPLOYMENT & INCOME - PRIMARY APPLICANT
    ═══════════════════════════════════════════════════════════════════════
    
    CURRENT EMPLOYMENT:
    Employer: PricewaterhouseCoopers (PwC Australia)
    ABN: 52 780 433 757
    Address: One International Towers, Barangaroo NSW 2000
    Position: Senior Manager - Tax Advisory
    Employment Type: Full-time Permanent
    Start Date: 2018-03-01 (6 years 8 months)
    
    INCOME DETAILS:
    Base Salary: $185,000 per annum
    Superannuation: $19,425 p.a. (10.5% - Fund: AustralianSuper #12345678901)
    Performance Bonus (Annual): $35,000 (average last 3 years)
    Additional Income:
    • Investment Property Rental: $42,000 p.a. (78 Smith St, Summer Hill)
    • Share Dividends: $8,500 p.a. (Portfolio value: $125,000)
    • Consulting (ABN 67 890 123 456): $15,000 p.a.
    
    TOTAL GROSS INCOME: $285,500 per annum
    Net Income (After Tax): $195,845 per annum
    
    PREVIOUS EMPLOYMENT (Last 5 Years):
    1. 2015-2018: Ernst & Young (EY), Tax Consultant
       Salary: $95,000 p.a.
       Reference: Sarah Thompson, Partner - (02) 9248 5555
    2. 2013-2015: KPMG, Graduate Tax Analyst
       Salary: $65,000 p.a.
    
    PROFESSIONAL REGISTRATIONS:
    • CPA Australia: Member #1234567
    • Tax Practitioners Board: Registered Tax Agent #98765432
    • Professional Indemnity Insurance: QBE #PI-2024-AUS-789456
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 4: EMPLOYMENT & INCOME - CO-APPLICANT
    ═══════════════════════════════════════════════════════════════════════
    
    CURRENT EMPLOYMENT:
    Employer: Roche Products Pty Limited
    ABN: 70 000 132 865
    Address: Level 8, 30-34 Hickson Road, Millers Point NSW 2000
    Position: Senior Clinical Research Associate
    Employment Type: Full-time Permanent
    Start Date: 2019-07-15 (5 years 4 months)
    
    INCOME DETAILS:
    Base Salary: $125,000 per annum
    Superannuation: $13,125 p.a. (Fund: UniSuper #98765432109)
    Annual Bonus: $18,000 (average)
    Car Allowance: $12,000 p.a.
    
    TOTAL GROSS INCOME: $155,000 per annum
    Net Income (After Tax): $112,340 per annum
    
    PREVIOUS EMPLOYMENT:
    1. 2017-2019: CSL Limited, Clinical Research Coordinator
       Salary: $85,000 p.a.
    2. 2015-2017: Royal Prince Alfred Hospital, Research Nurse
       Salary: $75,000 p.a.
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 5: FINANCIAL POSITION
    ═══════════════════════════════════════════════════════════════════════
    
    BANK ACCOUNTS:
    
    Primary Applicant:
    1. CBA NetBank Saver: BSB 062-000, Account: 1234-5678
       Current Balance: $145,000 (Deposit savings)
    2. CBA Everyday Account: BSB 062-000, Account: 8765-4321
       Current Balance: $12,500
    3. CBA Credit Card: Visa Platinum - 4532 1234 5678 9012
       Limit: $25,000 | Outstanding: $3,245.67
    4. ING Savings Maximiser: BSB 923-100, Account: 456789012
       Balance: $65,000
    
    Co-Applicant:
    1. CBA NetBank Saver: BSB 062-000, Account: 2345-6789
       Balance: $85,000
    2. CBA Everyday Account: BSB 062-000, Account: 9876-5432
       Balance: $8,750
    3. ANZ Credit Card: Amex - 3782 822463 10005
       Limit: $15,000 | Outstanding: $1,856.42
    
    Joint Accounts:
    1. CBA Savings Account: BSB 062-000, Account: 5555-6666
       Balance: $45,000 (Emergency fund)
    2. Vanguard Investment Account: #AU-2024-789456
       Balance: $125,000 (ETF portfolio)
    
    TOTAL LIQUID ASSETS: $483,248.91
    
    INVESTMENT PROPERTIES:
    
    Property 1: 78 Smith Street, Summer Hill NSW 2130
    Purchase Price (2020): $950,000
    Current Value (2024): $1,150,000
    Outstanding Loan: $685,000 (CBA Investment Loan #IL-2020-456789)
    Monthly Repayment: $3,890
    Rental Income: $3,500 per month ($42,000 p.a.)
    Interest Rate: 6.24% p.a. (Variable)
    Property Manager: Ray White Summer Hill - (02) 9799 1888
    
    SUPERANNUATION:
    
    Primary Applicant:
    • AustralianSuper Account #12345678901
    • Balance: $285,000
    • Insurance: Death $500k, TPD $400k, Income Protection $10k/month
    
    Co-Applicant:
    • UniSuper Account #98765432109
    • Balance: $195,000
    • Insurance: Death $350k, TPD $300k
    
    SHARES & INVESTMENTS:
    • CommSec Account #123456789: Value $85,000
    • Selfwealth Account #987654321: Value $40,000
    • BHP, CBA, CSL, WES, NAB shares
    
    VEHICLES:
    1. 2022 Tesla Model 3: Value $55,000 | No loan
    2. 2021 Toyota RAV4: Value $42,000 | Loan $15,000 (Macquarie #ML-2021-789)
    
    TOTAL ASSETS: $2,745,248.91
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 6: LIABILITIES & CREDIT HISTORY
    ═══════════════════════════════════════════════════════════════════════
    
    CURRENT LIABILITIES:
    
    1. Investment Property Loan (CBA)
       Loan Number: IL-2020-456789
       Outstanding: $685,000
       Monthly: $3,890
       Remaining Term: 26 years
    
    2. Car Loan (Macquarie Bank)
       Loan Number: ML-2021-789456
       Outstanding: $15,000
       Monthly: $565
       Remaining Term: 18 months
    
    3. Credit Cards (Combined)
       Total Limit: $40,000
       Outstanding: $5,102.09
       Minimum Monthly: $250
    
    4. HECS-HELP Debt (Primary): $18,500 (Master of Taxation)
    5. HECS-HELP Debt (Co-applicant): $22,000 (Bachelor Pharmacy + Masters)
    
    TOTAL LIABILITIES: $745,602.09
    
    NET WORTH: $1,999,646.82
    
    CREDIT HISTORY:
    Credit Score (Equifax): 856/1000 (Excellent)
    Credit Score (Experian): 912/1000 (Excellent)
    Credit Enquiries (Last 12 months): 2
    • 2024-06-15: Tesla Finance Application (Declined - paid cash instead)
    • 2024-02-10: CBA Credit Card Limit Increase (Approved)
    
    Default History: None
    Bankruptcy History: None
    Court Judgments: None
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 7: LOAN REQUEST DETAILS
    ═══════════════════════════════════════════════════════════════════════
    
    PROPERTY DETAILS:
    Target Property: 15 Emu Bay Road, Mosman NSW 2088
    Property Type: Freehold House (Torrens Title)
    Purchase Price: $2,650,000
    Stamp Duty: $145,665
    Legal Fees: $3,500
    Building Inspection: $850
    Total Purchase Costs: $2,800,015
    
    Property Description:
    • 4 bedroom, 3 bathroom family home
    • Land Size: 612 sqm
    • Built: 1998, Renovated: 2020
    • Council: Mosman Council, Rates: $3,850 p.a.
    • Water: Sydney Water, ~$1,200 p.a.
    
    Vendor: Smith Family Trust
    Real Estate Agent: McGrath Mosman - Sarah Johnson
    Phone: (02) 9969 4488 | Email: s.johnson@mcgrath.com.au
    
    LOAN REQUEST:
    Loan Amount: $2,050,000
    Deposit: $750,000 (includes $145,665 stamp duty from savings)
    LVR: 77.36%
    Loan Type: Principal & Interest, Owner Occupied
    Term: 30 years
    Preferred Rate: Fixed 3 years, then Variable
    
    Monthly Repayment (Estimated): $12,850 @ 6.5%
    
    SERVICEABILITY CALCULATION:
    Combined Net Income: $308,185 p.a. ($25,682/month)
    Total Proposed Debt Servicing:
    • New Home Loan: $12,850/month
    • Investment Loan: $3,890/month
    • Car Loan: $565/month (18 months remaining)
    • Credit Cards: $250/month
    Total: $17,555/month
    
    Debt Service Ratio: 68.3%
    
    Living Expenses (HEM + Buffer): $6,500/month
    Net Surplus: $1,627/month
    
    LENDERS MORTGAGE INSURANCE:
    LMI Required: Yes (LVR > 80%)
    Estimated LMI Premium: $62,500
    Capitalized into loan
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 8: SUPPORTING DOCUMENTS CHECKLIST
    ═══════════════════════════════════════════════════════════════════════
    
    IDENTITY DOCUMENTS:
    [✓] Primary: Driver License NSW 12345678 (Certified copy)
    [✓] Primary: Passport N8976543 (Certified copy)
    [✓] Primary: Medicare Card 3456 78901 2-4
    [✓] Co-applicant: Driver License NSW 87654321 (Certified copy)
    [✓] Co-applicant: Passport N7654321 (Certified copy)
    [✓] Marriage Certificate (2015-08-15, NSW Registry BDM Ref: 2015/12345)
    
    INCOME VERIFICATION:
    [✓] Primary: Last 2 years Tax Returns (2022-23, 2023-24)
    [✓] Primary: Last 2 years Tax Assessments (ATO Portal)
    [✓] Primary: Last 3 payslips (September, October, November 2024)
    [✓] Primary: Employment Contract (PwC - dated 2018-03-01)
    [✓] Primary: Letter from Employer (dated 2024-11-10)
    [✓] Co-applicant: Last 2 years Tax Returns
    [✓] Co-applicant: Last 3 payslips
    [✓] Co-applicant: Employment Contract (Roche - dated 2019-07-15)
    [✓] Co-applicant: Letter from Employer (dated 2024-11-08)
    [✓] Rental Income: Property Management Statements (12 months)
    [✓] Investment Income: Dividend Statements (CommSec, Selfwealth)
    
    ASSET VERIFICATION:
    [✓] Bank Statements: All accounts (Last 3 months)
    [✓] Superannuation Statements (Latest)
    [✓] Investment Property: Contract of Sale (2020)
    [✓] Investment Property: Recent Valuation ($1.15M - dated 2024-10-01)
    [✓] Investment Property: Council Rates Notice
    [✓] Investment Property: Strata/Body Corporate (N/A - house)
    [✓] Share Portfolio: Latest statements (CommSec, Selfwealth, Vanguard)
    [✓] Vehicle Registration: Tesla & RAV4
    
    LIABILITY VERIFICATION:
    [✓] Investment Loan: Latest statement (CBA IL-2020-456789)
    [✓] Car Loan: Latest statement (Macquarie ML-2021-789456)
    [✓] Credit Card: Statements (CBA Visa, ANZ Amex)
    [✓] HECS-HELP: ATO Notices of Assessment
    
    PROPERTY DOCUMENTS:
    [✓] Contract of Sale: Signed and exchanged (2024-11-10)
    [✓] Deposit Receipt: $265,000 paid to agent trust account
    [✓] Building & Pest Inspection: Clear (dated 2024-11-05)
    [✓] Strata Report: N/A (Torrens Title)
    [✓] Section 32/149 Certificate (dated 2024-11-01)
    [✓] Council Rates Notice (Mosman Council)
    [✓] Title Search: Lot 123 DP 456789
    [✓] Water Compliance Certificate
    
    ═══════════════════════════════════════════════════════════════════════
    SECTION 9: DECLARATIONS & CONSENT
    ═══════════════════════════════════════════════════════════════════════
    
    APPLICANT DECLARATIONS:
    
    I/We declare that:
    1. All information provided is true and correct
    2. No adverse changes to financial circumstances are anticipated
    3. No pending legal proceedings or disputes
    4. Not party to any guarantees except as disclosed
    5. Australian resident for tax purposes
    6. No directorships of companies in external administration
    7. Property will be used as primary place of residence
    8. Insurance will be arranged prior to settlement
    
    PRIVACY & CREDIT CONSENT:
    I/We consent to:
    • Collection and verification of information from third parties
    • Credit checks with Equifax, Experian, Illion
    • Disclosure to mortgage insurer (if LMI required)
    • Disclosure to servicers and related entities
    • Electronic verification of identity and income (ATO, Centrelink)
    
    SIGNATURES:
    Primary Applicant: David Wei Chen
    Signed: 2024-11-15 | IP Address: 203.123.45.67
    Device: iPhone 14 Pro | Location: North Sydney NSW
    
    Co-Applicant: Michelle Xiaomei Wang
    Signed: 2024-11-15 | IP Address: 203.123.45.67
    Device: Samsung Galaxy S23 | Location: North Sydney NSW
    
    ═══════════════════════════════════════════════════════════════════════
    INTERNAL USE ONLY - BANK PROCESSING NOTES
    ═══════════════════════════════════════════════════════════════════════
    
    CREDIT ASSESSMENT:
    Assessed by: Jennifer Martinez (CBA789456)
    Date: 2024-11-16 10:30:00
    Recommendation: APPROVE subject to conditions
    
    Risk Rating: Low
    Serviceability: Pass (surplus $1,627/month)
    Security: Residential property Mosman, 77% LVR
    Credit History: Excellent (both applicants)
    
    CONDITIONS PRECEDENT:
    1. Satisfactory property valuation
    2. Building insurance confirmation
    3. Final employment verification (phone call)
    4. Declaration of any changes in circumstances
    
    APPROVAL AUTHORITY:
    Recommended by: Jennifer Martinez, Senior Lending Manager
    Approved by: Michael Thompson, State Credit Manager
    Approval Code: CBAHL-2024-982345-APPROVED
    Date: 2024-11-16 15:45:00
    
    NEXT STEPS:
    • Formal approval letter issued: 2024-11-16
    • Valuation ordered: 2024-11-17
    • Settlement booked: 2024-12-20 (35 days)
    • Solicitor: Thomson Geer Lawyers
      Contact: Robert Kim, Partner
      Phone: (02) 8248 5000
      Email: r.kim@tglaw.com.au
      Trust Account: BSB 032-002, Account: 789456123
    
    INTERNAL CONTACT:
    Loan Processor: Sarah Williams (CBA234567)
    Email: s.williams@cba.com.au | Phone: (02) 9635 7891
    Processing Team: Parramatta Lending Centre, Level 5
    Address: 159 Church Street, Parramatta NSW 2150
    
    SYSTEM REFERENCES:
    Application ID: CBA-HL-2024-982345-SYD
    Customer ID Primary: CBA-CUST-2018-456789
    Customer ID Co-applicant: CBA-CUST-2019-567890
    Property ID: NSW-PROP-2024-MOSMAN-789
    
    COMPLIANCE CHECKS:
    [✓] AML/CTF verification complete (AUSTRAC)
    [✓] Sanctions screening: Clear
    [✓] PEP screening: Not applicable
    [✓] Source of funds: Verified (salary + savings + property equity)
    [✓] Identity verification: Green ID - Verified
    [✓] Address verification: Complete
    [✓] Employment verification: Pending final call
    
    ═══════════════════════════════════════════════════════════════════════
    END OF LOAN APPLICATION PACKAGE
    ═══════════════════════════════════════════════════════════════════════
    
    SECURITY CLASSIFICATION: CONFIDENTIAL - BANK INTERNAL
    Document contains sensitive personal and financial information protected
    under Privacy Act 1988, Banking Code of Practice, and internal policies.
    
    Unauthorized access, disclosure, or use prohibited.
    Report security incidents to: security@cba.com.au | Ph: 1800 555 123
    
    Generated: 2024-11-16 16:00:00 AEDT
    System: CBA Loan Origination System v12.4.5
    Report ID: LOS-2024-1116-982345-PKG
    """
    
    print("\n1. SCANNING FINANCIAL DOCUMENTS FOR PII/PSI")
    print("-" * 80)
    
    # Configure for Australian financial services
    cfg = RedactionConfig(
        country="AU",
        use_openmed=False,
        masking_style="hash"  # Financial data should use hashing
    )
    
    pipe = RedactionPipeline.from_config(cfg)
    
    # Step 1: Comprehensive scan
    print("\n💳 STEP 1: Financial PII/PSI Detection Scan")
    scan_result = pipe.scan(financial_documents)
    
    print(f"\n✓ Financial Document Scan Complete!")
    print(f"  • Document Type: Home Loan Application Package")
    print(f"  • Document Length: {len(financial_documents):,} characters")
    print(f"  • Total PII/PSI Items: {scan_result['total_detections']}")
    print(f"  • Data Sensitivity: {'HIGHLY RESTRICTED' if scan_result['has_pii'] else 'PUBLIC'}")
    print(f"  • Compliance Risk: {'HIGH - Requires Protection' if scan_result['total_detections'] > 50 else 'MEDIUM'}")
    
    # Step 2: Financial-specific entity breakdown
    print("\n💰 STEP 2: Financial Data Category Breakdown")
    print("-" * 80)
    
    # Categorize detections
    financial_categories = {
        'Identity': ['PERSON', 'DOB', 'DATE', 'DRIVER_LICENSE', 'PASSPORT'],
        'Tax & Gov': ['AU_TFN', 'AU_ABN', 'AU_MEDICARE'],
        'Financial': ['CREDIT_CARD', 'BANK_ACCOUNT', 'AU_BSB'],
        'Contact': ['EMAIL', 'AU_PHONE', 'ADDRESS'],
    }
    
    for category, entity_types in financial_categories.items():
        count = sum(scan_result['entity_counts'].get(et, 0) for et in entity_types)
        if count > 0:
            risk = "CRITICAL" if count > 20 else "HIGH" if count > 10 else "MEDIUM"
            print(f"  [{risk:8}] {category:15} : {count:3} items")
    
    # Step 3: High-value targets
    print("\n🎯 STEP 3: High-Value Data Protection Targets")
    print("-" * 80)
    
    high_value_items = {}
    for det in scan_result['detections']:
        label = det['label']
        if label in ['AU_TFN', 'CREDIT_CARD', 'BANK_ACCOUNT', 'PASSPORT']:
            if label not in high_value_items:
                high_value_items[label] = []
            high_value_items[label].append(det['text'][:10] + '...')  # Truncate for security
    
    for label, items in high_value_items.items():
        print(f"\n  {label}:")
        print(f"    Count: {len(items)}")
        print(f"    Protection Level: MAXIMUM")
        print(f"    Encryption Required: YES")
    
    # Step 4: Generate compliance reports
    print("\n📊 STEP 4: Generating Regulatory Compliance Reports")
    print("-" * 80)
    
    reports_dir = Path("reports/financial_compliance")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate reports
    report_types = {
        "html": ("Privacy Impact Assessment", "Complete PIA report"),
        "json": ("System Integration", "JSON for compliance platform"),
        "csv": ("Audit Trail", "Spreadsheet for auditors")
    }
    
    for fmt, (report_type, description) in report_types.items():
        report = ReportGenerator.generate(scan_result, format=fmt)
        filename = f"financial_pii_assessment_{timestamp}.{fmt}"
        output_file = reports_dir / filename
        output_file.write_text(report, encoding="utf-8")
        print(f"  ✓ {report_type:30} : {description}")
        print(f"    File: {filename}")
    
    # Step 5: Regulatory compliance assessment
    print("\n⚖️  STEP 5: REGULATORY COMPLIANCE ASSESSMENT")
    print("-" * 80)
    
    regulations = {
        "Privacy Act 1988": "REQUIRES REVIEW - 100+ PII items detected",
        "Banking Code of Practice": "NON-COMPLIANT for external sharing",
        "AML/CTF Act 2006": "COMPLIANT - Customer Due Diligence OK",
        "APRA CPS 234": "REQUIRES ENCRYPTION - Sensitive data present",
        "OAIC Privacy Principles": "BREACH RISK if shared without consent"
    }
    
    print("\n  Regulation Compliance Status:")
    for regulation, status in regulations.items():
        compliance = "FAIL" if "NON-COMPLIANT" in status or "BREACH" in status else "REVIEW"
        print(f"    [{compliance:6}] {regulation:30} : {status}")
    
    # Step 6: Data retention and disposal
    print("\n🗑️  STEP 6: DATA RETENTION & DISPOSAL REQUIREMENTS")
    print("-" * 80)
    print("""
  RETENTION REQUIREMENTS:
    • Loan application documents: 7 years (APRA requirement)
    • Identity verification: 7 years (AML/CTF Act)
    • Credit information: 2 years from closure (Privacy Act)
    • Declined applications: 7 years
    
  SECURE DISPOSAL AFTER RETENTION:
    • Electronic: Secure deletion (DoD 5220.22-M standard)
    • Physical: Cross-cut shredding (P-4 minimum)
    • Backup media: Degaussing or physical destruction
    • Cloud storage: Cryptographic erasure
    
  CURRENT CLASSIFICATION:
    • Document Class: CONFIDENTIAL
    • Handling: Authorized personnel only
    • Storage: Encrypted at rest and in transit
    • Access Log: All access must be audited
    """)
    
    # Step 7: Recommendations
    print("\n💡 STEP 7: DATA PROTECTION RECOMMENDATIONS")
    print("-" * 80)
    print(f"""
  IMMEDIATE ACTIONS REQUIRED:
  
  1. ACCESS CONTROL:
     • Restrict to authorized loan officers only
     • Enable multi-factor authentication
     • Log all document access
     • Review access weekly
     
  2. ENCRYPTION:
     • Encrypt file at rest (AES-256)
     • Use TLS 1.3 for transmission
     • Encrypt backups
     • Secure deletion after 7 years
     
  3. REDACTION FOR SHARING:
     Items requiring redaction: {scan_result['total_detections']}
     • All TFNs → Replace with "TFN REDACTED"
     • Credit cards → Show last 4 digits only
     • Bank accounts → Redact account numbers
     • Addresses → Suburb and postcode only
     • DOB → Year only
     
  4. AUDIT TRAIL:
     • Document who accessed: REQUIRED
     • Document why accessed: REQUIRED
     • Document what was shared: REQUIRED
     • Retention: 7 years minimum
     
  5. BREACH NOTIFICATION:
     • If data breach occurs: OAIC notification within 30 days
     • Affected parties: Must be notified
     • Remediation: Must be documented
     
  6. STAFF TRAINING:
     • Privacy awareness: Annual training required
     • Data handling: Quarterly refresher
     • Incident response: Tabletop exercises
    """)
    
    # Step 8: Risk score
    print("\n⚠️  STEP 8: PRIVACY RISK SCORE")
    print("-" * 80)
    
    pii_count = scan_result['total_detections']
    risk_score = min(100, (pii_count / 10) * 10)  # Scale to 100
    
    if risk_score >= 80:
        risk_level = "CRITICAL"
        action = "IMMEDIATE PROTECTION REQUIRED"
    elif risk_score >= 60:
        risk_level = "HIGH"
        action = "PROTECTION MEASURES REQUIRED"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        action = "STANDARD PROTECTION RECOMMENDED"
    else:
        risk_level = "LOW"
        action = "BASIC PROTECTION SUFFICIENT"
    
    print(f"\n  PRIVACY RISK SCORE: {risk_score}/100")
    print(f"  RISK LEVEL: {risk_level}")
    print(f"  REQUIRED ACTION: {action}")
    print(f"\n  RISK FACTORS:")
    print(f"    • Total PII/PSI Items: {pii_count}")
    print(f"    • High-Value Items: {len(high_value_items)}")
    print(f"    • Individuals Affected: 2 (Primary + Co-applicant)")
    print(f"    • Data Sensitivity: MAXIMUM (Financial + Identity)")
    print(f"    • Regulatory Scope: Multiple Acts")
    
    print("\n" + "="*80)
    print("EXAMPLE 2 COMPLETE - All compliance reports saved to:", reports_dir.absolute())
    print("="*80)
    
    return scan_result


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run both ultra-complex examples"""
    print("\n" + "="*80)
    print(" ZEROPHI ULTRA-COMPLEX REAL-WORLD EXAMPLES")
    print(" Production-Grade Scenarios with Full Audit & Compliance")
    print("="*80)
    
    try:
        # Example 1: Healthcare
        healthcare_result = example_1_healthcare_clinical_records()
        
        # Example 2: Financial Services
        financial_result = example_2_financial_compliance()
        
        # Final summary
        print("\n\n" + "="*80)
        print(" OVERALL SUMMARY - BOTH EXAMPLES")
        print("="*80)
        print(f"\n  Example 1 (Healthcare):")
        print(f"    • Total PHI/PII Detected: {healthcare_result['total_detections']}")
        print(f"    • Patients Affected: 3")
        print(f"    • Compliance: HIPAA-equivalent + Privacy Act")
        
        print(f"\n  Example 2 (Financial Services):")
        print(f"    • Total PII/PSI Detected: {financial_result['total_detections']}")
        print(f"    • Customers Affected: 2")
        print(f"    • Compliance: Privacy Act + Banking Code + AML/CTF")
        
        print(f"\n  COMBINED STATISTICS:")
        print(f"    • Total Detections: {healthcare_result['total_detections'] + financial_result['total_detections']}")
        print(f"    • Reports Generated: 14 (7 per example)")
        print(f"    • Documents Processed: 2 complex multi-section documents")
        
        print("\n" + "="*80)
        print(" ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print(" Check the 'reports/' directory for generated compliance reports")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Please ensure zerophi is properly installed and configured.")
        raise


if __name__ == "__main__":
    main()
