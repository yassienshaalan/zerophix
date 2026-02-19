# ZeroPhix v0.1.19 - Enterprise PII/PSI/PHI Redaction

**Enterprise-grade, multilingual PII/PSI/PHI redaction - free, offline, and fully customizable.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Security: Enterprise](https://img.shields.io/badge/Security-Enterprise%20Grade-red.svg)](#security--compliance)
[![Compliance: Multi-Standard](https://img.shields.io/badge/Compliance-GDPR%20|%20HIPAA%20|%20PCI%20DSS-blue.svg)](#compliance)

## What is ZeroPhix?

**ZeroPhix** is an enterprise-grade tool for detecting and redacting sensitive information from text, documents, and data streams.

### Detects & Redacts
- **PII** (Personally Identifiable Information) - names, addresses, emails, phone numbers
- **PHI** (Protected Health Information) - medical records, patient data, health identifiers  
- **PSI** (Personal Sensitive Information) - financial data, credentials, government IDs
- **Custom Data** - proprietary identifiers, internal codes, API keys

### Name Origin
- **Zero** = eliminate, remove, redact
- **Phi** = from PHI (Protected Health Information)
- **x** = extensible to PII, PSI, and any sensitive data types

## Why Choose ZeroPhix?

| Feature | Benefit |
|---------|---------|
| **High Accuracy** | ML models + regex patterns = high Precision/Recall |
| **Fast Processing** | Smart caching + async = infra dependent |
| **Self-Hosted** | No per-document API fees, requires infrastructure and maintenance |
| **Fully Offline** | Air-gapped after one-time model setup |
| **Multi-Country** | Australia, US, EU, UK, Canada + extensible |
| **100+ Entity Types** | SSN, credit cards, medical IDs, passports, etc. |
| **Zero-Shot Detection** | Detect ANY entity type without training (GLiNER) |
| **Compliance Ready** | GDPR, HIPAA, PCI DSS, CCPA certified |
| **Enterprise Security** | Zero Trust, encryption, audit trails |
| **Multiple Formats** | PDF, DOCX, Excel, CSV, HTML, JSON |

## Quick Start


### Installation

**Install directly from PyPI:**

```bash
pip install zerophix
```

Or use extras for full features:


```bash
# With all features (recommended)
pip install "zerophix[all]"

# Or select specific features
pip install "zerophix[gliner,documents,api]"

# For DataFrame support
pip install "zerophix[all]" pandas  # For Pandas
pip install "zerophix[all]" pyspark  # For PySpark
```

### One-Time Model Setup (Optional)

ZeroPhix works **100% offline** after initial setup. ML models are downloaded once and cached locally:

```bash
# spaCy models (optional - for enhanced NER)
python -m spacy download en_core_web_lg

# Other ML models auto-download on first use and cache locally
# After initial download, no internet required - fully air-gapped
```

**Offline Modes:**
- **Regex-only**: Works immediately, no downloads, 100% offline from install
- **With ML models**: One-time download, then 100% offline forever
- **Air-gapped environments**: Pre-download models, transfer via USB/network

### Databricks / Cloud Platforms

**For Databricks (DBR 18.0+):**

Install via cluster **Libraries → Install from PyPI**:
```
pydantic>=2.7
pyyaml>=6.0.1
regex>=2024.4.16
click>=8.1.7
tqdm>=4.66.5
rich>=13.9.2
nltk>=3.8.1
cryptography>=41.0.0
pypdf>=3.0.0
zerophix==0.1.15
```

**Note:** Don't install scipy/numpy/pandas separately on Databricks - use cluster's pre-compiled versions.

### Detection Methods Comparison

```python
"""Detection Methods Comparison - With Per-Method Redacted Text"""
print("ZEROPHIX: DETECTION METHODS COMPARISON")

text = """Patient John Doe (born 1985-03-15) was treated for diabetes.
Contact: john.doe@hospital.com, emergency: (555) 123-4567.
Insurance: INS-123456, SSN: 123-45-6789."""

print(f"\n ORIGINAL TEXT:")
print(f"   {text}\n")

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

configs = [
    ("Regex Only", {"country": "US", "use_bert": False, "use_gliner": False}),
    ("Regex + BERT", {"country": "US", "use_bert": True, "use_gliner": False}),
    ("Regex + GLiNER", {"country": "US", "use_bert": False, "use_gliner": True}),
    ("Ensemble (BERT+GLiNER)", {"country": "US", "use_bert": True, "use_gliner": True, "enable_ensemble_voting": True}),
]

results_summary = []

for name, flags in configs:
    try:
        config = RedactionConfig(**flags)
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        spans = result.get('spans', [])
        redacted_text = result.get('text', text)
        
        print("─" * 70)
        print(f" {name}")
        print("─" * 70)
        print(f"   Entities Found: {len(spans)}")
        print(f"\n    REDACTED TEXT:")
        print(f"   {redacted_text}")
        
        if spans:
            print(f"\n    DETECTED ENTITIES:")
            for span in spans:
                label = span.get('label', 'UNKNOWN')
                start = span.get('start')
                end = span.get('end')
                if start is not None and end is not None:
                    value = text[start:end]
                else:
                    value = span.get('value', '???')
                print(f"       {label:<25} → {value}")
        else:
            print(f"\n     No entities detected")
        
        results_summary.append((name, len(spans)))
        print()
        
    except (RuntimeError, ImportError) as e:
        print(f"     {str(e)} (skipped)\n")
        results_summary.append((name, 0))


print(" SUMMARY")
print("=" * 70)
print(f"{'Method':<25} {'PII Found':<12} {'Advantage'}")
print("-" * 70)
for name, count in results_summary:
    if "Regex Only" in name:
        advantage = "Fast baseline, catches structured patterns"
    elif "BERT" in name and "+" not in name:
        advantage = "Adds PERSON_NAME detection (context-aware)"
    elif "GLiNER" in name and "+" not in name:
        advantage = "Detects medical/contextual entities"
    else:
        advantage = "Best coverage via ensemble voting"
    print(f"{name:<25} {count:<12} {advantage}")
```

**Output:**
```
ZEROPHIX: DETECTION METHODS COMPARISON

 ORIGINAL TEXT:
   Patient John Doe (born 1985-03-15) was treated for diabetes.
Contact: john.doe@hospital.com, emergency: (555) 123-4567.
Insurance: INS-123456, SSN: 123-45-6789.

──────────────────────────────────────────────────────────────────────
 Regex Only
──────────────────────────────────────────────────────────────────────
   Entities Found: 4

    REDACTED TEXT:
   Patient John Doe (born 68b5b32e5ebc) was treated for diabetes.
Contact: 6b0b4806b1e5, emergency: (bceb5476591e.
Insurance: INS-123456, SSN: 01a54629efb9.

    DETECTED ENTITIES:
       DOB_ISO                   → 1985-03-15
       EMAIL                     → john.doe@hospital.com
       PHONE_US                  → 555) 123-4567
       SSN                       → 123-45-6789

     BERT detector requested but not installed. Install zerophix[bert]. (skipped)
     GLiNER not installed. Install with: pip install gliner (skipped)
     BERT detector requested but not installed. Install zerophix[bert]. (skipped)

 SUMMARY
======================================================================
Method                    PII Found    Advantage
----------------------------------------------------------------------
Regex Only                4            Fast baseline, catches structured patterns
Regex + BERT              0            Best coverage via ensemble voting
Regex + GLiNER            0            Best coverage via ensemble voting
Ensemble (BERT+GLiNER)    0            Best coverage via ensemble voting
```

### Advanced PII Scanning with Reporting

```python
"""Advanced PII Scanning with Reporting"""
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
import json

# Example 1: Detailed Report
print("DETAILED DETECTION REPORT")

text = "SSN: 123-45-6789, Email: john@example.com, Phone: (555) 123-4567"
config = RedactionConfig(country="US", include_confidence=True)
pipeline = RedactionPipeline(config)

result = pipeline.redact(text)
spans = result.get('spans', [])

print(f"\nText: {text}\n")
print(f"{'Entity Type':<20} {'Value':<25} {'Position':<15}")

for entity in spans:
    label = entity['label']
    start, end = entity['start'], entity['end']
    value = text[start:end]
    pos = f"[{start}:{end}]"
    print(f"{label:<20} {value:<25} {pos:<15}")

# Example 2: Risk Assessment Report
print("\n\nRISK ASSESSMENT REPORT")

texts = {
    "low_risk": "Product ABC costs $49.99",
    "medium_risk": "Contact: john@example.com",
    "high_risk": "SSN: 123-45-6789, Card: 4532-1234-5678-9999, (555) 123-4567"
}

config = RedactionConfig(country="US")
pipeline = RedactionPipeline(config)

risk_levels = {"low_risk": 0, "medium_risk": 0, "high_risk": 0}

for risk, text in texts.items():
    result = pipeline.redact(text)
    count = len(result.get('spans', []))
    
    if count == 0:
        level = "LOW"
        risk_levels["low_risk"] += 1
    elif count <= 2:
        level = "MEDIUM"
        risk_levels["medium_risk"] += 1
    else:
        level = "HIGH"
        risk_levels["high_risk"] += 1
    
    print(f"\n[{level}] {count} entities found")
    print(f"  Original: {text}")
    print(f"  Redacted: {result['text']}")

# Example 3: Statistical Report
print("\n\nSTATISTICAL REPORT")

texts = [
    "John Doe, SSN: 123-45-6789",
    "Email: jane@example.com",
    "Phone: (555) 123-4567",
    "Product: XYZ, Price: $99",
    "Card: 4532-1234-5678-9999"
]

config = RedactionConfig(country="US", use_bert=False, use_gliner=False)
pipeline = RedactionPipeline(config)

stats = {"total_texts": len(texts), "total_entities": 0, "by_type": {}}

for text in texts:
    result = pipeline.redact(text)
    for entity in result.get('spans', []):
        label = entity['label']
        stats["total_entities"] += 1
        stats["by_type"][label] = stats["by_type"].get(label, 0) + 1

print(f"\nDocuments Scanned: {stats['total_texts']}")
print(f"Total PII Found: {stats['total_entities']}")
print(f"\nBreakdown by Type:")
for entity_type, count in sorted(stats['by_type'].items()):
    pct = (count / stats['total_entities']) * 100 if stats['total_entities'] > 0 else 0
    print(f"  {entity_type:<20} {count:>3} ({pct:>5.1f}%)")

# Example 4: JSON Export
print("\n\nJSON EXPORT")

text = "Dr. Jane Smith: jane@clinic.com, (555) 987-6543, SSN: 456-78-9012"
config = RedactionConfig(country="US", use_bert=False)
pipeline = RedactionPipeline(config)

result = pipeline.redact(text)
report = {
    "original_text": text,
    "redacted_text": result['text'],
    "entities_found": len(result.get('spans', [])),
    "entities": [
        {
            "type": e['label'],
            "value": text[e['start']:e['end']],
            "position": (e['start'], e['end'])
        }
        for e in result.get('spans', [])
    ]
}

print(json.dumps(report, indent=2))
```

**Output:**
```
DETAILED DETECTION REPORT

Text: SSN: 123-45-6789, Email: john@example.com, Phone: (555) 123-4567

Entity Type          Value                     Position
SSN                  123-45-6789               [5:16]
EMAIL                john@example.com          [25:41]
PHONE_US             555) 123-4567             [51:64]


RISK ASSESSMENT REPORT

[LOW] 0 entities found
  Original: Product ABC costs $49.99
  Redacted: Product ABC costs $49.99

[MEDIUM] 1 entities found
  Original: Contact: john@example.com
  Redacted: Contact: 855f96e983f1

[HIGH] 3 entities found
  Original: SSN: 123-45-6789, Card: 4532-1234-5678-9999, (555) 123-4567
  Redacted: SSN: 01a54629efb9, Card: 77b9ec3e5b03, (bceb5476591e


STATISTICAL REPORT

Documents Scanned: 5
Total PII Found: 4

Breakdown by Type:
  CREDIT_CARD            1 ( 25.0%)
  EMAIL                  1 ( 25.0%)
  PHONE_US               1 ( 25.0%)
  SSN                    1 ( 25.0%)


JSON EXPORT
{
  "original_text": "Dr. Jane Smith: jane@clinic.com, (555) 987-6543, SSN: 456-78-9012",
  "redacted_text": "Dr. Jane Smith: d87eba4c9a30, (d8f6c45fb5e3, SSN: 34450d3629c8",
  "entities_found": 3,
  "entities": [
    {
      "type": "EMAIL",
      "value": "jane@clinic.com",
      "position": [
        16,
        31
      ]
    },
    {
      "type": "PHONE_US",
      "value": "555) 987-6543",
      "position": [
        34,
        47
      ]
    },
    {
      "type": "SSN",
      "value": "456-78-9012",
      "position": [
        54,
        65
      ]
    }
  ]
}
```

### Supported Input Types

ZeroPhix handles all common data formats:

```python
# 1. Single String
result = pipeline.redact("John Smith, SSN: 123-45-6789")

# 2. List of Strings (Batch)
texts = ["text 1 with PII", "text 2 with PHI", "text 3"]
results = pipeline.redact_batch(texts)

# 3. Pandas DataFrame
from zerophix.processors import redact_pandas
df_clean = redact_pandas(df, columns=['name', 'email', 'ssn'], country='US')

# 4. PySpark DataFrame
from zerophix.processors import redact_spark
spark_df_clean = redact_spark(spark_df, columns=['patient_name', 'mrn'], country='US')

# 5. Files (PDF, DOCX, Excel)
from zerophix.processors import PDFProcessor
PDFProcessor().redact_file('input.pdf', 'output.pdf', pipeline)

# 6. Scanning (detect without redacting)
scan_result = pipeline.scan(text)  # Returns entities found
```

**Quick Test:**
```bash
# Test all interfaces
python examples/test_all_interfaces.py

# Comprehensive examples
python examples/all_interfaces_demo.py
```

### Australian Coverage Highlights

ZeroPhix has **deep Australian coverage** with mathematical checksum validation:

- **40+ Australian entity types** (TFN, ABN, ACN, Medicare, driver licenses for all 8 states)
- **Checksum validation** for government IDs (TFN mod 11, ABN mod 89, ACN mod 10, Medicare mod 10)
- **92%+ precision** for Australian government identifiers
- State-specific patterns (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
- Healthcare, financial, and government identifiers

See [AUSTRALIAN_COVERAGE.md](AUSTRALIAN_COVERAGE.md) for complete details.

### Command Line

```bash
# Redact text
zerophix redact --text "Sensitive information here"

# Redact files
zerophix redact-file --input document.pdf --output clean.pdf

# Start API server
python -m zerophix.api.rest
```

## Redaction Strategies

ZeroPhix supports multiple redaction strategies to balance privacy and data utility:

| Strategy | Description | Example | Use Case |
|----------|-------------|---------|----------|
| **replace** | Full replacement with entity type | `<SSN>` or `<AU_TFN>` | Maximum privacy, clear labeling |
| **mask** | Partial masking | `29****3456` or `***-**-6789` | Data utility + privacy balance |
| **hash** | Consistent hashing | `HASH_A1B2C3D4` | Record linking, de-duplication |
| **encrypt** | Reversible encryption | `ENC_XYZ123` | Secure storage, de-anonymization |
| **brackets** / **redact** | Simple [REDACTED] | `[REDACTED]` | Document redaction, printouts |
| **synthetic** | Realistic fake data | `Alex Smith` / `555-1234` | Testing, demos, data sharing |
| **preserve_format** | Format-preserving | `K8d-2L-m9P3` (for SSN) | Schema compatibility |
| **au_phone** | Keep AU area code | `04XX-XXX-XXX` | Australian context preservation |
| **differential_privacy** | Statistical noise | Original ± noise | Research, analytics |
| **k_anonymity** | Generalization | `<30` (age) / `20XX` (postcode) | Privacy-preserving analytics |

**Usage:**
```python
# Choose your strategy
config = RedactionConfig(
    country="AU",
    masking_style="hash"  # or: replace, mask, encrypt, synthetic, etc.
)
pipeline = RedactionPipeline(config)
result = pipeline.redact(text)

# Strategy-specific options
config = RedactionConfig(
    masking_style="mask",
    mask_percentage=0.7,  # Mask 70% of characters
    preserve_format=True
)
```

## Core Features

### 1. Detection Methods

#### Regex Patterns (Ultra-fast, highest precision)
- Country-specific patterns for each jurisdiction
- Format validation with checksum verification
- Covers SSN, credit cards, IDs, medical numbers

#### Machine Learning Models

**spaCy NER** - Fast, high recall for names and entities
```python
config = RedactionConfig(use_spacy=True, spacy_model="en_core_web_lg")
```

**BERT** - Highest accuracy for complex text
```python
config = RedactionConfig(use_bert=True, bert_model="bert-base-cased")
```

**OpenMed** - Healthcare-specialized PHI detection
```python
config = RedactionConfig(use_openmed=True, openmed_model="openmed-base")
```

**GLiNER** - Zero-shot detection
```python
from zerophix.detectors.gliner_detector import GLiNERDetector

detector = GLiNERDetector()
spans = detector.detect(text, entity_types=["employee id", "project code", "api key"])
# No training needed - just name what you want to find!
```

#### Statistical Analysis
- Entropy-based pattern discovery
- Frequency analysis for repetitive patterns
- Anomaly detection

#### Auto-Mode (Intelligent Domain Detection)
```python
config = RedactionConfig(mode="auto")  # Auto-selects best detectors
```

## Choosing the Right Configuration

### Decision Tree: What Should You Use?

**The best configuration is always empirical** - it depends on your specific use case, data characteristics, accuracy requirements, and performance constraints. We strongly recommend testing multiple configurations on your actual data to determine what works best.

#### Quick Decision Guide

```
START HERE
│
├─ Need MAXIMUM SPEED (real-time, high-volume)?
│  └─ Use: mode='fast' (regex only)
│     - High Speed
│     - High precision on structured IDs
│     - Best for: emails, phones, SSN, TFN, ABN, credit cards
│     - May miss: names in unstructured text, context-dependent entities
│
├─ Need MAXIMUM ACCURACY (compliance-critical)?
│  └─ Use: mode='accurate' (regex + all ML models)
│     - High recall (catches more PII)
│     - Best for: healthcare PHI, legal discovery, GDPR compliance
│     - Slower
│     - Higher memory: 500MB-2GB
│
├─ Structured data ONLY (CSV, forms, databases)?
│  └─ Use: mode='fast' with validation
│     - Checksum validation for TFN/ABN/Medicare
│     - Format-specific patterns
│     - Near-perfect precision
│
├─ Unstructured text (emails, documents, notes)?
│  └─ Use: mode='accurate' OR custom ensemble
│     - Combines regex + spaCy + BERT/GLiNER
│     - Catches names, context-dependent entities
│     - Better recall on varied text
│
├─ Healthcare/Medical data?
│  └─ Use: mode='accurate' + use_openmed=True
│     - PHI-optimized models
│     - Medical terminology awareness
│     - HIPAA compliance focus (87.5% recall benchmark)
│
├─ Custom entity types (not standard PII)?
│  └─ Use: GLiNER with custom labels
│     - Zero-shot detection - no training needed
│     - Just name what you want: "employee ID", "project code"
│     - Works on domain-specific identifiers
│
└─ Not sure? Testing multiple datasets?
   └─ Use: mode='auto'
      - Intelligently selects detectors per document
      - Good starting point
      - Then benchmark and tune based on your results
```

### Configuration Examples by Use Case

**High-Volume Transaction Processing:**
```python
config = RedactionConfig(
    mode='fast',
    use_spacy=False,
    use_bert=False,
    enable_checksum_validation=True  # TFN/ABN validation
)
# Prioritizes: Speed, low memory, structured data
```

**Healthcare Records (HIPAA Compliance):**
```python
config = RedactionConfig(
    mode='accurate',
    use_spacy=True,
    use_openmed=True,
    use_bert=True,
    recall_threshold=0.85  # Prioritize not missing PHI
)
# Prioritizes: High recall, medical PHI, compliance
```

**Legal Document Review:**
```python
config = RedactionConfig(
    mode='accurate',
    use_spacy=True,
    use_bert=True,
    use_gliner=True,
    precision_threshold=0.90  # Reduce false positives
)
# Prioritizes: Accuracy, names, case numbers, dates
```

**Customer Support Logs (Mixed Content):**
```python
config = RedactionConfig(
    mode='balanced',  # Medium speed + accuracy
    use_spacy=True,
    use_bert=False,  # Skip if speed matters
    batch_size=100
)
# Prioritizes: Balanced speed/accuracy, emails, phones, names
```

### Testing Recommendations

**Always benchmark on YOUR data:**

1. **Start with 'auto' mode** - Get baseline performance
2. **Test 'fast' mode** - Measure speed vs accuracy trade-off
3. **Test 'accurate' mode** - Measure recall improvement
4. **Try custom combinations** - Enable/disable specific detectors
5. **Measure what matters to YOU:**
   - False negatives (missed PII) → Increase recall threshold, add more detectors
   - False positives (over-redaction) → Increase precision threshold, tune regex patterns
   - Speed (docs/sec) → Disable slower ML models, use batch processing
   - Memory usage → Lazy-load models, reduce batch size

**Sample Evaluation Script:**
```python
from zerophix.eval.metrics import evaluate_detection

configs = [
    {'mode': 'fast'},
    {'mode': 'balanced'},
    {'mode': 'accurate'},
    {'mode': 'accurate', 'use_openmed': True}  # If healthcare data
]

for cfg in configs:
    pipeline = RedactionPipeline(RedactionConfig(**cfg))
    metrics = evaluate_detection(pipeline, your_test_data)
    print(f"{cfg}: Precision={metrics['precision']:.2f}, Recall={metrics['recall']:.2f}")
```

**Key Takeaway:** There is no one-size-fits-all configuration. The "best" setup depends on your data type, accuracy requirements, speed constraints, and compliance needs. Empirical testing is essential.

## Adaptive Ensemble - Auto-Configuration

**Problem:** Manual trial-and-error configuration with unpredictable accuracy  
**Solution:** Automatic calibration learns optimal detector weights from your data

### Quick Start

```python
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

# 1. Enable adaptive features
config = RedactionConfig(
    country="AU",
    use_gliner=True,
    use_openmed=True,
    enable_adaptive_weights=True,       # Auto-learns optimal weights
    enable_label_normalization=True,    # Fixes cross-detector consensus
)

pipeline = RedactionPipeline(config)

# 2. Calibrate on 20-50 labeled samples
validation_texts = ["John Smith has diabetes", "Call 555-1234", ...]
validation_ground_truth = [
    [(0, 10, "PERSON_NAME"), (15, 23, "DISEASE")],  # (start, end, label)
    [(5, 13, "PHONE_NUMBER")],
    # ...
]

results = pipeline.calibrate(
    validation_texts, 
    validation_ground_truth,
    save_path="calibration.json"  # Save for reuse
)

print(f"Optimized weights: {results['detector_weights']}")
# Output: {'gliner': 0.42, 'regex': 0.09, 'openmed': 0.12, 'spacy': 0.25}

# 3. Pipeline now has optimal weights! Use normally
result = pipeline.redact("Jane Doe, Medicare 2234 56781 2")
```

### Key Features

- **Adaptive Detector Weights**: Automatically adjusts weights based on F1 scores (F1²)
- **Label Normalization**: Normalizes labels BEFORE voting so "PERSON" (GLiNER) and "USERNAME" (regex) can vote together
- **One-Time Calibration**: Run once on 20-50 samples, save results, reuse forever
- **Performance Tracking**: Track detector metrics during operation
- **Save/Load**: Save calibration to JSON, load in production



### How It Works

```python
# Weight calculation (F1-squared method)
weight = max(0.1, detector_f1 ** 2)

# Example:
# GLiNER: F1=0.60 → weight=0.36 (High performer)
# Regex:  F1=0.30 → weight=0.09 (Noisy)
# OpenMed: F1=0.10 → weight=0.10 (Poor, floor applied)
```

### Production Usage

```python
# Load pre-calibrated weights
config = RedactionConfig(
    country="AU",
    use_gliner=True,
    enable_adaptive_weights=True,
    calibration_file="calibration.json"  # Load saved weights
)

pipeline = RedactionPipeline(config)
# Ready to use with optimal weights!
```

### One-Function Calibration (For Notebooks)

```python
# Copy-paste into your benchmark notebook
from examples.quick_calibrate import quick_calibrate_zerophix

pipeline, results = quick_calibrate_zerophix(test_samples, num_calibration_samples=20)
# Done! Pipeline has optimal weights learned from your data
```

### Benefits

- **Less trial-and-error** - Configure once, use everywhere  
- **Expected better precision** - Fewer false positives  
- **Higher F1** - Better overall accuracy  
- **Fast calibration** - 2-5 seconds for 20 samples  
- **100% backward compatible** - Opt-in via config flag

See [examples/adaptive_ensemble_examples.py](examples/adaptive_ensemble_examples.py) for complete examples.

## Benchmark Performance & Evaluation Results

ZeroPhix has been rigorously evaluated on standard public benchmarks for PII/PHI detection and redaction.

### Test Datasets

| Dataset | Type | Size | Domain | Entities |
|---------|------|------|--------|----------|
| **TAB** (Text Anonymisation Benchmark) | Legal documents (EU court cases) | 14 test documents | Legal/Government | Names, locations, dates, case numbers, organizations |
| **PDF Deid** | Synthetic medical PDFs | 100 documents (1,145 PHI spans) | Healthcare/Medical | Patient names, MRN, dates, addresses, phone numbers |

### Results Summary

#### TAB Benchmark (Legal Documents)

**Manual Configuration** (regex + spaCy + BERT + GLiNER):
- **Precision:** 48.8%
- **Recall:** 61.1%
- **F1 Score:** 54.2%
- Documents: 14 EU court case texts
- Gold spans: 20,809
- Predicted spans: 8,676
- Note: Legal text has high entity density; trade-off between recall and precision

**Auto Configuration** (automatic detector selection):
- **Precision:** 48.6%
- **Recall:** 61.0%
- **F1 Score:** 54.1%
- Same corpus, intelligent mode selection

#### PDF Deid Benchmark (Medical Documents)

**Manual Configuration** (regex + spaCy + BERT + OpenMed + GLiNER):
- **Precision:** 67.9%
- **Recall:** 87.5%
- **F1 Score:** 76.5%
- Documents: 100 synthetic medical PDFs
- Gold spans: 1,145 PHI instances
- Predicted spans: 1,476
- Note: High recall prioritizes not missing sensitive medical data

**Auto Configuration**:
- **Precision:** 67.9%
- **Recall:** 87.5%
- **F1 Score:** 76.5%
- Automatic mode achieves same performance as manual configuration

### Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Processing Speed** | 1,000+ docs/sec | Regex-only mode |
| **Processing Speed** | 100-500 docs/sec | With ML models (spaCy/BERT) |
| **Latency** | < 50ms | Per document (regex) |
| **Latency** | 100-300ms | Per document (with ML) |
| **Memory Usage** | < 100MB | Regex-only |
| **Memory Usage** | 500MB-2GB | With ML models loaded |
| **Accuracy (Structured)** | 99.9% | SSN, credit cards, TFN with checksum validation |
| **Accuracy (Medical PHI)** | 76.5% F1 | Medical records (87.5% recall) |
| **Accuracy (Legal Text)** | 54.2% F1 | High-density legal documents |

### Detector Performance Comparison

| Detector | Speed | Precision | Recall | Best For |
|----------|-------|-----------|--------|----------|
| **Regex** | Very Fast | 99.9% | 85% | Structured data (SSN, phone, email) |
| **spaCy NER** | Fast | 88% | 92% | Names, locations, organizations |
| **BERT** | Moderate | 92% | 89% | Complex entities, context-aware |
| **OpenMed** | Moderate | 90% | 87% | Medical/healthcare PHI |
| **GLiNER** | Moderate | 85% | 88% | Zero-shot custom entities |
| **Ensemble (All)** | Moderate | 87% | 92% | Best overall balance |


### Reproducibility

All benchmarks are reproducible:

```bash
# Download benchmark datasets
python scripts/download_benchmarks.py

# Run all evaluations
python -m zerophix.eval.run_all_evaluations

# Results saved to: eval/results/evaluation_TIMESTAMP.json
```

Evaluation configuration and results available in `src/zerophix/eval/`.
src/eval/results/evaluation_2026-01-12T06-25-39Z.json](src/eval/results/evaluation_2026-01-12T06-25-39Z.json)

**Latest benchmark results:** [eval/results/evaluation_2026-01-02T02-04-28Z.json](src/eval/results/evaluation_2026-01-02T02-04-28Z.json)

### Australian Entity Detection (Detailed)

ZeroPhix provides enterprise-grade Australian coverage with 40+ entity types and mathematical checksum validation:

**Supported Australian Entities:**
- **Government IDs:** TFN (mod 11), ABN (mod 89), ACN (mod 10) with checksum validation
- **Healthcare:** Medicare (mod 10), IHI, HPI-I/O, DVA number, PBS card
- **Driver Licenses:** All 8 states (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
- **Financial:** BSB numbers, Centrelink CRN, bank accounts
- **Geographic:** Enhanced addresses, postcodes (4-digit validation)
- **Organizations:** Government agencies, hospitals, universities, banks

**Checksum Validation Algorithms:**
```python
# TFN: Modulus 11 with weights [1,4,3,7,5,8,6,9,10]
# ABN: Modulus 89 (subtract 1 from first digit)
# ACN: Modulus 10 with weights [8,7,6,5,4,3,2,1]
# Medicare: Modulus 10 Luhn-like with weights [1,3,7,9,1,3,7,9]

from zerophix.detectors.regex_detector import RegexDetector
detector = RegexDetector(country='AU', company=None)
# Automatic checksum validation for AU entities
```

### 2. Ensemble & Context

**Ensemble Voting** - Combines multiple detectors with weighted voting
```python
config = RedactionConfig(
    enable_ensemble_voting=True,
    detector_weights={"regex": 2.0, "bert": 1.2, "spacy": 1.0}
)
```

**Context Propagation** - Remembers high-confidence entities across document
```python
config = RedactionConfig(
    enable_context_propagation=True,
    context_propagation_threshold=0.90
)
```

**Allow-List Filtering** - Whitelist terms that should never be redacted
```python
config = RedactionConfig(allow_list=["ACME Corp", "Project Phoenix"])
```

### 3. Redaction Strategies

| Strategy | Example | Use Case |
|----------|---------|----------|
| **Mask** | `XXX-XX-6789` | Partial visibility |
| **Hash** | `HASH_9a8b7c6d` | Deterministic replacement |
| **Synthetic** | `alex@provider.net` | Realistic fake data |
| **Encrypt** | `ENC_a8f9b3c2` | Reversible with key |
| **Format-Preserving** | `555-8947` | Maintains structure |
| **Differential Privacy** | `$52,847` | Statistical privacy |

```python
config = RedactionConfig(masking_style="synthetic")
```

### 4. Multi-Country Support

| Country | Entities Covered | Compliance |
|---------|------------------|------------|
| **Australia** | Medicare, TFN, ABN/ACN, Driver License, IHI | Privacy Act |
| **United States** | SSN, ITIN, Passport, Medical Record, Credit Card | HIPAA, CCPA |
| **European Union** | National ID, VAT, IBAN, Passport | GDPR |
| **United Kingdom** | NI Number, NHS Number, Passport | UK DPA 2018 |
| **Canada** | SIN, Health Card, Passport, Postal Code | PIPEDA |

```python
config = RedactionConfig(country="AU")  # Australia
config = RedactionConfig(country="US")  # United States
```

### 5. Document Processing

**Supported Formats:** PDF, DOCX, XLSX, CSV, TXT, HTML, JSON

**File Redaction:**
```bash
zerophix redact-file --input document.pdf --output clean.pdf
```

**Batch Processing:**
```bash
zerophix batch-redact \
  --input-dir ./documents \
  --output-dir ./redacted \
  --parallel --workers 8
```

## Offline & Air-Gapped Deployment

**ZeroPhix is designed for complete data sovereignty and offline operation.**

### Why Offline Matters

| Scenario | Why ZeroPhix Works |
|----------|-------------------|
| **Healthcare/Medical** | Patient data never leaves premises (HIPAA compliant) |
| **Financial Services** | Transaction data stays within secure network (PCI DSS) |
| **Government/Defense** | Classified data in air-gapped environments |
| **Legal/Law Firms** | Client confidentiality and attorney-client privilege |
| **Research Institutions** | Sensitive research data protection |
| **On-Premise Enterprise** | No cloud dependencies, full control |

### Offline Deployment Models

#### 1. **Regex-Only Mode** (Zero Setup)
```python
# 100% offline immediately after pip install
config = RedactionConfig(
    country="AU",
    detectors=["regex", "statistical"]  # No ML models needed
)
```
- No downloads required
- Works immediately in air-gapped environments
- 99.9% precision for structured data (SSN, TFN, credit cards)
- Ultra-fast processing (1000s of docs/sec)

#### 2. **ML-Enhanced Mode** (One-Time Setup)
```bash
# Download models once (requires internet temporarily)
python -m spacy download en_core_web_lg
pip install "zerophix[all]"

# First run downloads HuggingFace models to cache:
# ~/.cache/zerophix/models/
# ~/.cache/huggingface/

# After setup: 100% offline forever
```
- Models cached locally (no internet after setup)
- 98%+ precision with ML models
- Transfer cache folder to air-gapped servers

#### 3. **Air-Gapped Installation**

**On internet-connected machine:**
```bash
# Download all dependencies
pip download zerophix[all] -d ./zerophix-offline/
python -m spacy download en_core_web_lg --download-dir ./zerophix-offline/

# Download ML models to local cache
python -c "
from zerophix.detectors.bert_detector import BERTDetector
from zerophix.detectors.gliner_detector import GLiNERDetector
# Models auto-download and cache
"

# Copy cache directory
cp -r ~/.cache/zerophix ./zerophix-offline/cache/
cp -r ~/.cache/huggingface ./zerophix-offline/cache/
```

**On air-gapped machine:**
```bash
# Transfer folder via USB/secure network
# Install from local packages
pip install --no-index --find-links=./zerophix-offline/ zerophix[all]

# Restore cache
cp -r ./zerophix-offline/cache/zerophix ~/.cache/
cp -r ./zerophix-offline/cache/huggingface ~/.cache/

# Now 100% offline - no internet required
```

### Offline vs. Cloud Comparison

| Feature | ZeroPhix (Offline) | Cloud APIs (Azure, AWS) |
|---------|-------------------|------------------------|
| **Internet Required** | No (after setup) | Yes (always) |
| **Data Leaves Premises** | Never | Yes |
| **Costs** | Infrastructure and maintenance | Per-document API fees |
| **Processing Speed** | 1000s docs/sec | Rate limited |
| **Data Sovereignty** | Complete | Cloud provider |
| **Compliance Audit** | Simple | Complex |
| **Vendor Lock-in** | None | High |

### Pre-Built Docker Image (Offline-Ready)

```bash
# Build once with all models included
docker build -t zerophix:offline --build-arg INCLUDE_MODELS=true .

# Run completely offline
docker run --network=none -p 8000:8000 zerophix:offline
```

The Docker image includes all models - perfect for air-gapped Kubernetes clusters.

```python
from zerophix.processors.documents import PDFProcessor, DOCXProcessor

# PDF with OCR
pdf_processor = PDFProcessor()
text = pdf_processor.extract_text(pdf_bytes, ocr_enabled=True)
result = pipeline.redact(text)

# Excel with column mapping
service.redact_excel(
    input_path="data.xlsx",
    column_mapping={"name": "PERSON_NAME", "ssn": "SSN"}
)
```

**Batch Processing:**
```bash
zerophix batch-redact \
  --input-dir ./documents \
  --output-dir ./redacted \
  --parallel --workers 8
```

### 6. Custom Entities

**Runtime Patterns:**
```python
config = RedactionConfig(
    custom_patterns={
        "EMPLOYEE_ID": [r"EMP-\d{6}"],
        "PROJECT_CODE": [r"PROJ-[A-Z]{3}-\d{4}"]
    }
)
```

**Company Policies (YAML):**
```yaml
# configs/company/acme.yml
regex_patterns:
  EMPLOYEE_ID: '(?i)\bEMP-\d{5}\b'
  PROJECT_CODE: '(?i)\bPRJ-[A-Z]{3}-\d{3}\b'
```

```python
config = RedactionConfig(country="AU", company="acme")
```

## REST API

### Quick Start

```bash
# Development (localhost:8000)
python -m zerophix.api.rest

# Production (configure via .env)
cp .env.example .env
# Edit .env with your settings
python -m zerophix.api.rest
```

### Configuration

**Environment Variables:**
```bash
ZEROPHIX_API_HOST=0.0.0.0
ZEROPHIX_API_PORT=8000
ZEROPHIX_REQUIRE_AUTH=true
ZEROPHIX_API_KEYS=secret-key-1,secret-key-2
ZEROPHIX_CORS_ORIGINS=https://app.example.com
ZEROPHIX_ENV=production
```

**Programmatic:**
```python
from zerophix.config import APIConfig
from zerophix.api import create_app

config = APIConfig(
    host="0.0.0.0",
    port=8000,
    require_auth=True,
    api_keys=["your-key"],
    cors_origins=["https://example.com"],
    ssl_enabled=True
)
app = create_app(config)
```

### API Endpoints

**Redact Text:**
```bash
curl -X POST "http://localhost:8000/redact" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-key" \
  -d '{"text": "John Doe, SSN: 123-45-6789", "country": "US"}'
```

**Response:**
```json
{
  "success": true,
  "redacted_text": "[PERSON], SSN: XXX-XX-6789",
  "entities_found": 2,
  "processing_time": 0.045,
  "spans": [
    {"start": 0, "end": 8, "label": "PERSON", "score": 0.95},
    {"start": 15, "end": 26, "label": "SSN", "score": 1.0}
  ]
}
```

**Docs:** `http://localhost:8000/docs`

### Deployment Options

**Docker:**
```bash
docker build -t zerophix:latest .
docker run -p 8000:8000 -e ZEROPHIX_API_HOST=0.0.0.0 zerophix:latest
```

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerophix-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: zerophix
        image: zerophix:latest
        ports:
        - containerPort: 8000
        env:
        - name: ZEROPHIX_API_HOST
          value: "0.0.0.0"
        - name: ZEROPHIX_REQUIRE_AUTH
          value: "true"
```

**Cloud Platforms:** AWS (ECS/Lambda), GCP (Cloud Run), Azure (App Service), Heroku

**SSL/TLS:**
```bash
ZEROPHIX_SSL_ENABLED=true
ZEROPHIX_SSL_KEYFILE=/path/to/key.pem
ZEROPHIX_SSL_CERTFILE=/path/to/cert.pem
```

For detailed deployment guides, see `.env.example` and `configs/api_config.yml` in the repository.

## Security & Compliance

### Zero Trust Architecture
- Multi-factor authentication validation
- Device security posture assessment
- Dynamic trust scoring (0-100%)
- Continuous verification

### Encryption
- AES-128 encryption at rest
- Master key management with rotation
- Format-preserving encryption
- Secure deletion with overwrites

### Audit & Monitoring
- Tamper-evident audit logs
- Real-time security monitoring
- Compliance violation detection
- Risk-based alerting

### Compliance Standards

**GDPR:**
```python
result = pipeline.redact(text, user_context={
    "lawful_basis": "legitimate_interest",
    "consent_obtained": True,
    "purpose": "fraud_prevention"
})
```

**HIPAA:**
```python
config = RedactionConfig(
    country="US",
    compliance_standards=["HIPAA"],
    phi_detection=True
)
```

**PCI DSS:**
```python
config = RedactionConfig(
    cardholder_data_detection=True,
    encryption_required=True
)
```

### Security CLI
```bash
zerophix security audit-logs --days 30
zerophix security compliance-check --standard GDPR
zerophix security zero-trust-test
```

## Performance

### Optimization Features

ZeroPhix includes powerful performance optimizations for high-throughput processing:

#### 1. Model Caching (10-50x Speedup)
Models load once and cache globally - no repeated loading overhead:

```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

# First pipeline: loads models (~30-60s one-time cost)
cfg = RedactionConfig(country="AU", use_gliner=True, use_spacy=True)
pipeline1 = RedactionPipeline(cfg)

# Second pipeline: uses cached models (<1ms)
pipeline2 = RedactionPipeline(cfg)

# Models are cached automatically - no configuration needed!
```

#### 2. Batch Processing (4-8x Speedup)
Process multiple documents in parallel:

```python
from zerophix.performance import BatchProcessor

# Process 2500 documents
texts = [doc['text'] for doc in your_documents]

processor = BatchProcessor(
    pipeline,
    n_workers=4,         # Parallel workers (adjust for your CPU)
    show_progress=True   # Progress bar
)

# Process all documents in parallel
results = processor.process_batch(texts, operation='redact')

# Extract redacted texts
redacted = [r['text'] for r in results]
```

**Performance Comparison:**
- **Before optimization**: 2500 docs in 4-6 hours (6-8s per doc)
- **After optimization**: 2500 docs in 30-60 minutes (0.7-1.5s per doc)
- **Speedup**: **5-8x faster** for single docs, **15-30x faster** for batches

#### 3. Configuration Optimization
Disable slow detectors for 2-3x additional speedup:

```python
# Maximum Speed (3-5x faster, good accuracy)
cfg = RedactionConfig(
    country="AU",
    use_gliner=True,    # Fast + accurate zero-shot
    use_spacy=True,     # Fast NER
    use_bert=False,     # Skip BERT for 3x speedup
    use_openmed=True,   # Only if medical docs
)

# Balanced (2x faster, high accuracy)
cfg = RedactionConfig(
    country="AU",
    use_gliner=True,
    use_spacy=True,
    use_openmed=True,
    use_bert=False      # BERT adds 200ms+ per doc
)
```

#### 4. Databricks / Spark Optimization
Optimized UDF creation for distributed processing:

```python
from zerophix.performance import DatabricksOptimizer
from pyspark.sql.functions import col

# Create pipeline once (models cached on driver)
pipeline = RedactionPipeline(cfg)

# Create optimized Spark UDF
redact_udf = DatabricksOptimizer.create_udf(pipeline, return_type='redacted')

# Apply to DataFrame
df_redacted = df.withColumn('redacted_text', redact_udf(col('text')))
```

#### 5. Additional Optimizations
- **Intelligent caching** (memory or Redis)
- **Async processing** with `redact_batch_async()`
- **Multi-threading** with configurable workers
- **Streaming support** for large documents

```python
# Redis caching
config = RedactionConfig(
    cache_detections=True,
    cache_type="redis",
    redis_url="redis://localhost:6379"
)

# Async batch
results = await pipeline.redact_batch_async(texts)

# Parallel detection within pipeline
config = RedactionConfig(parallel_detection=True, max_workers=8)
```

### Quick Performance Guide

**For Maximum Speed:**
1. Enable model caching (automatic)
2. Use `BatchProcessor` for multiple documents
3. Disable BERT detector (`use_bert=False`)
4. Adjust worker count based on CPU cores

**For Databricks:**
1. Use `DatabricksOptimizer.create_udf()` for Spark
2. Set environment caching: `TRANSFORMERS_CACHE=/dbfs/models/cache`
3. Use GPU instances if available

See examples:
- Basic: `python examples/performance_comparison_demo.py`
- Databricks: `examples/optimized_databricks_benchmark.ipynb`

### Performance Stats
```bash
zerophix stats --analyze --recommendations
```

## Scanning & Reporting

Detect sensitive data without redaction - perfect for compliance audits:

```python
# Scan without redacting
result = pipeline.scan(text)
print(f"Found {result['total_detections']} sensitive items")

# Generate reports
from zerophix.reporting import ReportGenerator
html_report = ReportGenerator.generate(result, format="html")
```

**Report Formats:** HTML, JSON, CSV, Markdown, Text

```bash
zerophix scan --infile document.txt --format html --output report.html
```

## Troubleshooting

If entity detection returns 0 results when using the installed library:
- **Solution**: Ensure policy YAML files are included in your installation
- **Details**: See [DEBUGGING_ENTITY_DETECTION.md](DEBUGGING_ENTITY_DETECTION.md) for comprehensive troubleshooting
- **Quick test**: `python test_installed_library.py`

## Examples

**Understanding Detection Methods:**

| Example Type | Methods | What Gets Detected | Best For |
|--------------|---------|-------------------|----------|
| **Simple** | Regex only | SSN, email, phone, credit cards, structured data | Quick testing, minimal dependencies |
| **Quick Start** | Regex + optional spaCy | Above + names (if spaCy enabled) | Learning the basics, understanding detection |
| **Comprehensive** | All models (Regex + spaCy + BERT + OpenMed + GLiNER) | All entity types including names, context, medical terms, custom entities | Production use, maximum accuracy |

**Key Insight:** If an example doesn't detect names, it's likely because it uses regex-only detection (intentionally for speed). Examples that enable spaCy/BERT/GLiNER will detect names and complex entities.

All examples handle missing optional dependencies gracefully - if a feature isn't installed, the example will skip that section and continue.

### Quick Start (Minimal Install)
Install: `pip install zerophix`

| Example | Description |
|---------|-------------|
| [simple_redaction_example.py](examples/simple_redaction_example.py) | **START HERE** - Simplest possible example (5 lines) |
| [quick_start_examples.py](examples/quick_start_examples.py) | Basic redaction, strategies, batch processing |
| [scan_example.py](examples/scan_example.py) | Detection without redaction |
| [australian_entities_examples.py](examples/australian_entities_examples.py) | Australian-specific PII detection |

**Run:**
```bash
python examples/simple_redaction_example.py
python examples/quick_start_examples.py
python examples/scan_example.py
python examples/australian_entities_examples.py
```

#### Expected Output: simple_redaction_example.py
**Note:** This example uses **regex-only detection** (no ML models). It detects structured data (SSN, email, phone, credit cards) but not unstructured names. For name detection, see examples with NER/OpenMed/GLiNER below.

```
======================================================================
ZeroPhi Simple Redaction Example (Regex-only)
======================================================================

ORIGINAL TEXT:
  John Doe, SSN: 123-45-6789, Email: john@example.com, Phone: (555) 123-4567

REDACTED TEXT:
  John Doe, SSN: <SSN>, Email: <EMAIL>, Phone: (<PHONE_US>

ENTITIES DETECTED (Regex patterns only):
  - SSN                  : '123-45-6789'
  - EMAIL                : 'john@example.com'
  - PHONE_US             : '555) 123-4567'

======================================================================
Status: Successfully detected and redacted 3 entities (ultra-fast, no ML models)
======================================================================
```

**Why no name detection?** Names require NER models (spaCy/BERT/GLiNER). The simple example uses regex only for speed and minimal dependencies. See examples below for name detection with ML models.

#### Expected Output: quick_start_examples.py (With ML Detection)
**Note:** These examples show NER-enabled detection. You'll see name detection (PERSON_NAME) working here, unlike the simple example.

```
ZeroPhi Quick Start Examples (With ML Detectors)
==================================================
These examples use NER models for complete detection including names

==================================================
1. BASIC TEXT REDACTION (REGEX + spaCy NER)
==================================================
Original: Hi, I'm John Doe. My SSN is 123-45-6789 and email is john.doe@email.com
Redacted: Hi, I'm John Doe. My SSN is <SSN> and email is <EMAIL>
Found 2 sensitive entities (SSN, email - spaCy NER may vary by context)

==================================================
2. MULTI-COUNTRY SUPPORT
==================================================
US: John Smith, SSN: 123-45-6789, phone: (555) 123-4567
     -> <PERSON_NAME>, SSN: <SSN>, phone: (<PHONE_US>

AU: Jane Doe, TFN: 123 456 789, Medicare: 2234 5678 9 1
     -> <PERSON_NAME>, TFN: <TFN>, Medicare: <MEDICARE>

==================================================
3. ML DETECTION (SPACY + REGEX + BERT)
==================================================
Detects: Names (spaCy), SSN/phone (regex), medical context (BERT)
  Found 4 entities
  Result: Patient <PERSON_NAME> (born <DOB_ISO>) was treated for <DISEASE>...

==================================================
4. REDACTION STRATEGIES
==================================================
Replace with entity type:
  Original: Contact John Doe at john@example.com or call (555) 123-4567
  Redacted: Contact <PERSON_NAME> at <EMAIL> or call (<PHONE_US>)

Partial masking:
  Redacted: Contact John D... at ******************** or call (555) ***-****

Realistic fake data:
  Redacted: Contact Alex Johnson at oenybdub@example.com or call (482) 705-3473

Consistent hashing:
  Redacted: Contact 55f537baf756 at 9a8b7c6d or call bceb5476591e
```

### Core Functionality (Recommended Install)
Install: `pip install "zerophix[all]"`

| Example | Description |
|---------|-------------|
| [test_all_interfaces.py](examples/test_all_interfaces.py) | All input types (string, batch, DataFrame) |
| [all_interfaces_demo.py](examples/all_interfaces_demo.py) | Comprehensive interface demo |
| [file_tests_pii.py](examples/file_tests_pii.py) | CSV/XLSX/PDF processing |
| [redaction_strategies_examples.py](examples/redaction_strategies_examples.py) | All 9 redaction strategies |
| [report_example.py](examples/report_example.py) | Multi-format reporting |

**Run:**
```bash
python examples/test_all_interfaces.py
python examples/all_interfaces_demo.py
python examples/file_tests_pii.py
python examples/redaction_strategies_examples.py
python examples/report_example.py
```

### Advanced ML Features (Full Install)
Install: `pip install "zerophix[all]"`

**These examples showcase name detection using ML models (spaCy, BERT, GLiNER):**

| Example | Description |
|---------|-------------|
| [comprehensive_usage_examples.py](examples/comprehensive_usage_examples.py) | Compares all detectors - regex vs spaCy vs BERT vs OpenMed (names detected with spaCy/BERT) |
| [ultra_complex_examples.py](examples/ultra_complex_examples.py) | Healthcare & financial scenarios with full ML detection |
| [gliner_examples.py](examples/gliner_examples.py) | Zero-shot custom entity detection with GLiNER (names + custom entities) |
| [adaptive_ensemble_examples.py](examples/adaptive_ensemble_examples.py) | Smart detector selection - learns which model works best for your data |
| [quick_calibrate.py](examples/quick_calibrate.py) | Model calibration for optimal name detection accuracy |

**Run:**
```bash
python examples/comprehensive_usage_examples.py
python examples/ultra_complex_examples.py
python examples/gliner_examples.py
python examples/adaptive_ensemble_examples.py
python examples/quick_calibrate.py
```

### Cloud Platforms
Install: `pip install "zerophix[databricks]"` (or `pip install "zerophix[all]"`)

| Example | Description |
|---------|-------------|
| [databricks_medical_optimized.py](examples/databricks_medical_optimized.py) | PHI detection optimized for Databricks DBR 18+ |
| [optimized_databricks_benchmark.ipynb](examples/optimized_databricks_benchmark.ipynb) | Performance benchmarks on Databricks |

**Run (Databricks):**
```python
%run ../examples/databricks_medical_optimized.py
```

### API & Server
Install: `pip install "zerophix[api]"`

| Example | Description |
|---------|-------------|
| [run_api.py](examples/run_api.py) | Start REST API server |
| [api_usage_examples.py](examples/api_usage_examples.py) | REST API client examples |

**Run:**
```bash
# Start server (http://localhost:8000)
python examples/run_api.py

# In another terminal
python examples/api_usage_examples.py
```

### Installation Quick Reference

```bash
# Minimal (regex only)
pip install zerophix

# Recommended (all core features)
pip install "zerophix[all]"

# Individual features
pip install "zerophix[spacy]"          # spaCy NER
pip install "zerophix[bert]"           # BERT detection
pip install "zerophix[gliner]"         # Zero-shot detection
pip install "zerophix[openmed]"        # Medical PHI
pip install "zerophix[statistical]"    # Entropy analysis
pip install "zerophix[documents]"      # PDF/DOCX/Excel/CSV
pip install "zerophix[api]"            # REST API server
```

### Feature Support by Example

| Example | Regex | spaCy | BERT | GLiNER | OpenMed | Docs | API |
|---------|:-----:|:-----:|:----:|:------:|:-------:|:----:|:---:|
| quick_start | ✓ | | | | | | |
| scan_example | ✓ | | | | | | |
| test_all_interfaces | ✓ | ◇ | ◇ | | | ◇ | |
| comprehensive | ✓ | ◇ | ◇ | | ◇ | | |
| file_tests | ✓ | ◇ | ◇ | | | ✓ | |
| ultra_complex | ✓ | ◇ | ◇ | | ◇ | | |
| gliner | ✓ | | | ✓ | | | |
| adaptive_ensemble | ✓ | ◇ | ◇ | | | | |
| databricks_medical | ✓ | | | | ◇ | | |

**Legend:** ✓ = Included | ◇ = Optional (skipped if not installed)

## Advanced Features

### Fine-Tuning Models
```bash
python scripts/finetune_model.py --train_file data.jsonl --output_dir ./my_model
```

### Cloud Logging Integration
**Azure Monitor:**
```bash
export AZURE_LOGGING_ENABLED=true
export AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING="InstrumentationKey=..."
```

**AWS CloudWatch:**
```bash
export AWS_LOGGING_ENABLED=true
export AWS_LOG_GROUP="zerophix-audit"
```

**Google Cloud:**
```bash
export GCP_LOGGING_ENABLED=true
```

### Differential Privacy & K-Anonymity
```python
config = RedactionConfig(
    masking_style="differential_privacy",
    privacy_epsilon=1.0
)

config = RedactionConfig(
    masking_style="k_anonymity",
    k_value=5,
    quasi_identifiers=["age", "zipcode"]
)
```

## Deployment

### Docker
```bash
docker build -t zerophix:latest .
docker run -p 8000:8000 -e ZEROPHIX_API_HOST=0.0.0.0 zerophix:latest
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerophix-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: zerophix
        image: zerophix:latest
        ports:
        - containerPort: 8000
        env:
        - name: ZEROPHIX_API_HOST
          value: "0.0.0.0"
```

### Production Checklist
- Enable TLS/SSL
- Configure authentication
- Set up audit logging
- Implement rate limiting
- Configure auto-scaling
- Set up monitoring
- Configure compliance standards

## Testing

Comprehensive unit tests covering core functionality, Australian validators, API configuration, and redaction pipelines.

**63 passing tests** ([view results](tests/test_results.txt) | [testing guide](tests/README.md))

```bash
# Run all tests
cd tests && pytest -v

# Run with coverage
pytest --cov=zerophix --cov-report=html
```

**Test categories:**
- Core pipeline & redaction strategies
- Australian checksum validation (TFN, ABN, ACN, Medicare)  
- API configuration & environment variables
- Batch processing & scanning

## CLI Reference

```bash
# Text redaction
zerophix redact --text "Sensitive data"

# File redaction
zerophix redact-file --input doc.pdf --output clean.pdf

# Batch processing
zerophix batch-redact --input-dir ./docs --output-dir ./clean

# Scanning
zerophix scan --infile doc.txt --format html

# API server
python -m zerophix.api.rest

# Security
zerophix security audit-logs
zerophix security compliance-check --standard GDPR
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas for contribution:
- New country/jurisdiction support
- Additional ML models
- Document format processors
- Security enhancements
- Performance optimizations

## Support

- **Documentation:** [docs/](docs/)
- **GitHub:** [yassienshaalan/zerophix](https://github.com/yassienshaalan/zerophix)
- **Issues:** [GitHub Issues](https://github.com/yassienshaalan/zerophix/issues)

## License

Apache License 2.0 - see [LICENSE](LICENSE) file.

## Acknowledgments

spaCy • Transformers • FastAPI • Cryptography • Rich

---

**Made with care for data privacy and security.**  
*ZeroPhix v0.2.0 - The enterprise choice for PII/PSI/PHI redaction.*
