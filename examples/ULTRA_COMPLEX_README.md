# Ultra-Complex Real-World Examples

## Overview

This directory contains two **production-grade, ultra-complex examples** that demonstrate ZeroPhi's capabilities in real-world enterprise scenarios.

## Files

### `ultra_complex_examples.py`
Two comprehensive examples with realistic, detailed scenarios:

---

## Example 1: Healthcare Clinical Records

**Scenario:** Hospital preparing 3-patient clinical records for research sharing

**Complexity Factors:**
- 3 complete patient medical records
- 100+ PHI/PII items per patient
- Multiple data types: Medicare, IHI, TFN, DVA numbers
- Medical terminology and diagnoses
- Prescription details and pathology results
- Insurance and billing information
- Complex nested data structures
- Multiple healthcare providers and contacts

**What It Demonstrates:**
- Comprehensive PHI detection across diverse medical documents
- Risk assessment and compliance checking (Privacy Act, NHMRC guidelines)
- Per-patient data breakdown
- Multi-format report generation (HTML, JSON, CSV, Markdown)
- De-identification recommendations
- Audit trail creation

**Document Size:** ~14,000 characters  
**Expected Detections:** 150-300+ items depending on detectors enabled

---

## Example 2: Financial Services Compliance

**Scenario:** Bank processing home loan application before regulatory audit

**Complexity Factors:**
- Complete loan application package
- 2 applicants with full financial profiles
- Identity documents (licenses, passports, Medicare)
- Tax File Numbers and ABNs
- Bank account numbers and BSBs
- Credit card numbers (multiple types)
- Employment and income details
- Investment properties and assets
- Superannuation information
- Credit history and scores
- Detailed liabilities breakdown

**What It Demonstrates:**
- Financial PII/PSI detection
- Regulatory compliance assessment (Privacy Act, Banking Code, AML/CTF, APRA CPS 234)
- High-value data identification (TFNs, credit cards, bank accounts)
- Data retention and disposal requirements
- Privacy risk scoring
- Multi-regulation compliance checking

**Document Size:** ~18,000 characters  
**Expected Detections:** 200-400+ items

---

## How to Run

### Quick Start

```bash
# Run both examples
python examples/ultra_complex_examples.py
```

### What Happens

1. **Example 1 - Healthcare:**
   - Scans 3-patient clinical document
   - Detects ALL PHI/PII (names, Medicare, IHI, TFN, DVA, phones, emails, addresses)
   - Generates 7 reports (HTML, JSON, CSV, Markdown + summary)
   - Provides risk assessment and de-identification recommendations
   - Saves to: `reports/healthcare_audit/`

2. **Example 2 - Financial:**
   - Scans complete loan application package
   - Detects ALL PII/PSI (TFN, credit cards, bank accounts, identity docs)
   - Generates 3 compliance reports (HTML, JSON, CSV)
   - Assesses regulatory compliance status
   - Provides data protection recommendations
   - Saves to: `reports/financial_compliance/`

---

## Expected Output

### Console Output
```
================================================================================
EXAMPLE 1: HEALTHCARE CLINICAL RECORDS - COMPLEX MULTI-PATIENT ANALYSIS
================================================================================

1. SCANNING FOR PHI/PII IN COMPLEX CLINICAL DOCUMENT
--------------------------------------------------------------------------------

 STEP 1: Comprehensive PHI/PII Detection Scan

 Scan Complete!
  • Document Length: 13,847 characters
  • Total PHI/PII Detections: 287
  • Contains Sensitive Data: YES - RESTRICTED
  • Unique Entity Types: 15

 STEP 2: Entity Type Breakdown
--------------------------------------------------------------------------------
  [HIGH  ] AU_MEDICARE         :  45 occurrences
  [HIGH  ] AU_PHONE            :  38 occurrences
  [HIGH  ] EMAIL               :  32 occurrences
  [HIGH  ] AU_TFN              :  28 occurrences
  [MEDIUM] DATE                :  24 occurrences
  [MEDIUM] ADDRESS             :  18 occurrences
  ...

[continues with detailed analysis]
```

### Generated Reports

#### Healthcare Audit Reports
- `clinical_phi_audit_[timestamp].html` - Beautiful styled HTML report
- `clinical_phi_audit_[timestamp].json` - Machine-readable data
- `clinical_phi_audit_[timestamp].csv` - Spreadsheet for analysis
- `clinical_phi_audit_[timestamp].md` - Documentation format

#### Financial Compliance Reports
- `financial_pii_assessment_[timestamp].html` - Privacy Impact Assessment
- `financial_pii_assessment_[timestamp].json` - System integration format
- `financial_pii_assessment_[timestamp].csv` - Audit trail spreadsheet

---

## Report Contents

### HTML Reports Include:
- Executive summary with risk indicators
- Entity type breakdown table
- Detailed detection cards with context
- Risk assessment and recommendations
- Compliance checklist
- Professional styling (self-contained, no external CSS)

### JSON Reports Include:
- Scan timestamp
- Summary statistics
- Complete detection array with:
  - Entity type and label
  - Detected text
  - Confidence score
  - Position in document
  - Surrounding context
- Entity count breakdown

### CSV Reports Include:
- Detection number
- Entity type
- Detected text
- Confidence score
- Start/end positions
- Context snippet

---

## Use Cases

### Healthcare Scenario
**Before Research Sharing:**
- Identify all PHI before sharing with research partners
- Generate compliance report for ethics committee
- Create audit trail of what was detected
- Get de-identification recommendations

**Regulatory Compliance:**
- Privacy Act 1988 compliance
- Health Records Act compliance
- NHMRC ethics guidelines

### Financial Scenario
**Before Regulatory Audit:**
- Identify all PII/PSI in loan applications
- Assess compliance with multiple regulations
- Generate privacy impact assessment
- Document data protection measures

**Regulatory Compliance:**
- Privacy Act 1988
- Banking Code of Practice
- AML/CTF Act 2006
- APRA CPS 234 (Information Security)

---

## Customization

### Modify for Your Needs

```python
# Adjust configuration
cfg = RedactionConfig(
    country="AU",           # Change country: "AU", "US", "EU", etc.
    use_openmed=True,      # Enable ML for better person name detection
    masking_style="hash"    # Choose: hash, mask, replace, brackets
)

# Generate specific report format
report = ReportGenerator.generate(scan_result, format="html")

# Save with custom filename
output_file = Path("my_custom_report.html")
output_file.write_text(report, encoding="utf-8")
```

---

## Key Features Demonstrated

### 1. **Realistic Data Complexity**
- Multi-section documents
- Nested information structures
- Multiple individuals per document
- Mixed PII/PHI/PSI types
- Professional formatting

### 2. **Comprehensive Detection**
- Names and personal identifiers
- Government IDs (Medicare, TFN, DVA, IHI, ABN, Driver License)
- Financial data (credit cards, bank accounts, BSB)
- Contact information (phones, emails, addresses)
- Dates and dates of birth
- Medical and financial details

### 3. **Enterprise-Grade Reporting**
- Multi-format output (HTML, JSON, CSV, Markdown)
- Professional styling and presentation
- Detailed statistics and breakdowns
- Risk assessment and scoring
- Compliance checking
- Actionable recommendations

### 4. **Regulatory Alignment**
- Privacy Act 1988 (Commonwealth)
- Health Records Act 2001 (Victoria)
- Banking Code of Practice
- AML/CTF Act 2006
- APRA CPS 234
- NHMRC Guidelines

---

## Performance Notes

- **Processing Time:** ~2-5 seconds per document (without OpenMed)
- **With OpenMed:** ~10-20 seconds per document (more accurate person name detection)
- **Memory Usage:** ~50-100 MB per document
- **Report Generation:** <1 second per format

---

## Next Steps

1. **Run the examples:**
   ```bash
   python examples/ultra_complex_examples.py
   ```

2. **Review the generated reports:**
   ```bash
   # Open HTML reports in browser
   start reports/healthcare_audit/*.html
   start reports/financial_compliance/*.html
   ```

3. **Customize for your data:**
   - Modify the example text
   - Adjust configuration options
   - Add your own document types

4. **Integrate into your workflow:**
   - Use the patterns from these examples
   - Build custom pipelines
   - Add automated scanning to your CI/CD

---

## Questions?

See the main README.md or check:
- `examples/scan_example.py` - Basic scanning
- `examples/report_example.py` - Report generation
- `examples/comprehensive_usage_examples.py` - More features
- `QUICK_REFERENCE.md` - Command reference

---

**These are production-ready examples showing real-world complexity!** 
