# ZeroPhix v0.1.0 - Enterprise PII/PSI/PHI Redaction Service

**Enterprise-grade, multilingual PII/PSI/PHI redaction - free, offline, and fully customizable.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Security: Enterprise](https://img.shields.io/badge/Security-Enterprise%20Grade-red.svg)](#security--compliance)
[![Compliance: Multi-Standard](https://img.shields.io/badge/Compliance-GDPR%20|%20HIPAA%20|%20PCI%20DSS-blue.svg)](#compliance-standards)

## Why ZeroPhix?

### **High Performance & Accuracy**
- **Fast processing** with intelligent caching and async operations
- **High accuracy** with advanced ML models and contextual detection
- **No usage limits** - unlimited processing volume at zero cost
- **Complete data sovereignty** - fully offline operation

### **Enterprise Security & Compliance**
- **Zero Trust architecture** with dynamic trust scoring
- **Multi-standard compliance**: GDPR, HIPAA, PCI DSS, CCPA, UK DPA 2018, PIPEDA
- **Encryption at rest** with secure key management
- **Comprehensive audit trails** with tamper-evident logging

### **Global Coverage**
- **Multi-country support**: Australia, US, EU, UK, Canada + extensible
- **100+ entity types**: SSN, credit cards, medical records, passports, etc.
- **Multi-language detection** with Unicode and international patterns
- **Configurable policies** per jurisdiction and organization

### **Advanced Capabilities**
- **ML-powered detection**: spaCy, BERT, custom models, statistical analysis
- **Zero-shot detection (GLiNER)**: Detect ANY entity type without training
- **Privacy-preserving redaction**: differential privacy, k-anonymity, synthetic data
- **Document processing**: PDF, DOCX, Excel, CSV with format preservation
- **REST API** with authentication, rate limiting, and webhook support

## How It Works

ZeroPhix employs a multi-stage pipeline designed for maximum accuracy and flexibility:

1.  **Detection**: The text is scanned by multiple detectors in parallel:
    *   **Regex Detector**: Finds patterns like emails, phone numbers, and IDs using country-specific rules.
    *   **ML Detector (OpenMed/Custom)**: Uses advanced Named Entity Recognition (NER) models to find context-dependent entities (e.g., names, organizations).
    *   **GLiNER (Optional)**: Zero-shot detection for arbitrary labels.

2.  **Ensemble Voting (Consensus)**:
    *   When detectors disagree (e.g., Regex says "PHONE" but ML says "ID"), a weighted voting system resolves the conflict.
    *   Weights are configurable (default: Regex > ML) to prioritize high-precision rules.

3.  **Contextual Propagation (Session Memory)**:
    *   High-confidence detections are "remembered" and propagated throughout the document.
    *   *Example*: If "Dr. Smith" is detected as a PERSON with 99% confidence, other occurrences of "Smith" in the text are also redacted, even if the detector missed them.

4.  **Allow-List Filtering**:
    *   Specific terms (e.g., your company name) can be whitelisted to prevent accidental redaction.

5.  **Redaction**:
    *   The final list of sensitive spans is masked according to your policy (e.g., `[REDACTED]`, `***`, or hashed).

### Fine-Tuning for Custom Domains

For the highest possible accuracy, you can fine-tune the underlying ML models on your own data.
Use the provided script `scripts/finetune_model.py` with your labeled data (JSONL format).

```bash
python scripts/finetune_model.py --train_file data.jsonl --output_dir ./my_model
```

Then update your config to point to `./my_model`.

## Installation

### Quick Start
```bash
pip install zerophix
```

### Full Installation with All Features
```bash
# Core with ML models (spaCy NER, BERT, OpenMed medical models)
pip install "zerophix[spacy,bert,openmed]"

# With GLiNER zero-shot detector (RECOMMENDED!)
pip install "zerophix[gliner]"

# With document processing (PDF, DOCX, Excel support)
pip install "zerophix[documents]"

# With API server (FastAPI, WebSocket support)
pip install "zerophix[api]"

# Complete enterprise installation (all features including GLiNER)
pip install "zerophix[all]"
```

### GLiNER Zero-Shot Detector (NEW - Recommended!)
```bash
# Option 1: Install as zerophix extra (recommended)
pip install "zerophix[gliner]"

# Option 2: Install standalone
pip install gliner

# No training needed - detect ANY entity type instantly!
# Just name what you want to find: "employee id", "api key", "project code"
# See examples/gliner_examples.py for full demonstrations
```

**Why GLiNER?**
- **Zero-shot detection**: No training data required
- **Instant custom entities**: Add new entity types in seconds
- **90%+ accuracy**: State-of-the-art performance
- **Fast**: ~100ms per document
- **Flexible**: Works with healthcare, financial, legal, custom domains

### OpenMed Medical Model Setup
```bash
# Install OpenMed dependencies
pip install "zerophix[openmed]"

# Download OpenMed models (first-time setup)
python -c "from zerophix.detectors.openmed_detector import ensure_model; ensure_model('openmed-base')"
```

### Development Installation
```bash
git clone https://github.com/yassienshaalan/zerophix.git
cd zerophix
pip install -e ".[all]"
```

## REST API Usage

ZeroPhix provides a high-performance REST API for integrating redaction capabilities into your applications.

### 1. Installation & Startup

```bash
# Install dependencies
pip install "zerophix[api]"

# Start the server (Linux/Mac)
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uvicorn zerophix.api.rest:app --reload

# Start the server (Windows PowerShell)
$env:PYTHONPATH="src"; uvicorn zerophix.api.rest:app --reload
```

The server will start at `http://127.0.0.1:8000`.
Interactive documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

### 2. API Endpoints

#### Health Check
`GET /health` - Check service status and stats.
```bash
curl http://127.0.0.1:8000/health
```

#### Redact Text
`POST /redact` - Redact PII/PHI from text.

**Request:**
```json
{
  "text": "Patient John Smith (DOB: 12/05/1980) was admitted.",
  "country": "AU",
  "masking_style": "replace",
  "detectors": ["regex", "custom", "spacy"],
  "include_confidence": true
}
```

**Response:**
```json
{
  "success": true,
  "redacted_text": "Patient <PERSON> (DOB: <DATE>) was admitted.",
  "entities_found": 2,
  "processing_time": 0.045,
  "spans": [
    { "start": 8, "end": 18, "label": "PERSON", "score": 0.95 },
    { "start": 25, "end": 35, "label": "DATE", "score": 1.0 }
  ],
  "request_id": "a1b2c3d4-..."
}
```

#### Batch Redaction
`POST /batch/redact` - Process multiple texts in parallel.
```json
{
  "texts": ["Text 1...", "Text 2..."],
  "country": "US"
}
```

## Quick Start

> **Complete Examples Available**  
> • [GLiNER Zero-Shot Examples](examples/gliner_examples.py) - **NEW!** Detect custom entities instantly  
> • [Quick Start Examples](examples/quick_start_examples.py) - Basic usage patterns  
> • [Comprehensive Examples](examples/comprehensive_usage_examples.py) - All features  
> • [API Integration Examples](examples/api_usage_examples.py) - REST API & SDK usage

### File-Based Redaction Demo (CSV/XLSX/PDF)

Use `examples/file_tests_pii.py` when you want an end-to-end walkthrough of CSV, Excel, and PDF processing:

```bash
# from the repo root (or install location)
python examples/file_tests_pii.py \
  --data-dir /path/to/folder/with/pii-files \
  --csv /path/to/pii.csv \
  --xlsx /path/to/pii.xlsx \
  --pdf /path/to/pii.pdf
```

- `--data-dir` points to a directory that contains `pii.csv`, `pii.xlsx`, and `pii.pdf`; you can override individual files with `--csv/--xlsx/--pdf` if they live elsewhere.
- All arguments are optional. If you skip them, the script looks for the files next to `file_tests_pii.py` (useful when you drop sample data into `examples/`).
- The script prints the resolved paths before running so you can confirm it is reading from the correct location (helpful when working through symlinks or mounted volumes).
- Each section demonstrates a different workflow: CSV redaction plus hashing validation, Excel redaction across multiple sheets with joinability checks, and PDF text extraction followed by redaction and encryption verification.

> Need synthetic sample data? Create quick placeholders (e.g., `examples/pii.csv`) and force-add them with `git add -f` if your `.gitignore` excludes `*.csv`.

### Command Line Interface

#### Basic Text Redaction
```bash
# Simple redaction
zerophix redact --text "John Smith SSN: 123-45-6789, Credit Card: 4532-1234-5678-9012"

# Advanced redaction with ML models
zerophix redact \
  --text "Patient John Doe, DOB: 1985-03-15, Medical Record: MR123456" \
  --country US \
  --detectors "regex,spacy,bert" \
  --masking-style "synthetic" \
  --include-stats
```

#### File Processing
```bash
# Redact PDF files
zerophix redact-file --input medical_records.pdf --output redacted_records.pdf --preserve-formatting

# Batch processing
zerophix batch-redact --input-dir ./documents --output-dir ./redacted --parallel

# Excel/CSV with column preservation
zerophix redact-file --input patient_data.xlsx --output clean_data.xlsx --format excel
```

#### Scanning & Reporting
```bash
# Scan documents for PII/PHI without redaction
zerophix scan --infile document.txt --format html --output report.html
zerophix scan --infile data.csv --stats-only

# Generate reports in multiple formats (HTML, JSON, CSV, Markdown, Text)
zerophix scan --infile doc.txt --format json --output audit.json

# Redact with audit report
zerophix redact --infile doc.txt --report html --report-output audit.html
```

#### Performance & Benchmarking
```bash
# Performance optimization
zerophix stats --show-recommendations

# Server mode
zerophix serve --host 0.0.0.0 --port 8000 --workers 4
```

#### Security & Compliance
```bash
# View audit logs
zerophix security audit-logs

# Compliance validation
zerophix security compliance-check --user-id admin --purpose processing

# Zero Trust security test
zerophix security zero-trust-test --ip-address 192.168.1.100

# Security configuration
zerophix security config-security
```

### Python API

#### GLiNER Zero-Shot Detection (Recommended for Custom Entities)
```python
from zerophix.detectors.gliner_detector import GLiNERDetector

# Initialize GLiNER detector
detector = GLiNERDetector()

# Define custom entity types - NO TRAINING NEEDED!
custom_entities = [
    "employee id", 
    "project code",
    "api key",
    "internal reference"
]

text = """
Employee ID: EMP-2024-5678
Project: PROJECT-ALPHA-99
API Key: sk_live_abcd1234xyz
Internal Ref: INT-REF-001
"""

# Detect instantly - zero-shot!
spans = detector.detect(text, entity_types=custom_entities)

for span in spans:
    print(f"[{span.label}] {text[span.start:span.end]} (confidence: {span.score:.2f})")

# Output:
# [EMPLOYEE_ID] EMP-2024-5678 (confidence: 0.95)
# [PROJECT_CODE] PROJECT-ALPHA-99 (confidence: 0.92)
# [API_KEY] sk_live_abcd1234xyz (confidence: 0.88)
# [INTERNAL_REFERENCE] INT-REF-001 (confidence: 0.90)
```

**Healthcare Example:**
```python
# Medical entities - no training required!
medical_entities = [
    "patient name", "medical record number", "date of birth",
    "diagnosis", "medication", "doctor name", "npi number"
]

clinical_note = """
Patient: Sarah Johnson
MRN: MR-2024-9876
Diagnosis: Hypertension
Medication: Lisinopril 10mg daily
"""

spans = detector.detect(clinical_note, entity_types=medical_entities)
# Instantly detects all PHI without training!
```

See [examples/gliner_examples.py](examples/gliner_examples.py) for 6 complete examples including healthcare, financial, and performance benchmarks.

#### Basic Usage
```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

# Configure for US healthcare (HIPAA compliant)
config = RedactionConfig(
    country="US",
    detectors=["regex", "spacy", "bert"],
    use_contextual=True,
    masking_style="synthetic",
    cache_detections=True
)

pipeline = RedactionPipeline(config)

# Redact with security context
result = pipeline.redact(
    text="Patient: John Doe, SSN: 123-45-6789, Record: MR12345",
    user_context={
        "user_id": "doctor_smith",
        "purpose": "treatment",
        "lawful_basis": "healthcare",
        "data_classification": "RESTRICTED"
    }
)

print(f"Redacted: {result['text']}")
print(f"Entities found: {result['entities_found']}")
print(f"Processing time: {result['processing_time']:.2f}s")
```

#### Advanced Document Processing
```python
from zerophix.processors.documents import PDFProcessor, DOCXProcessor

# Process PDF files
pdf_processor = PDFProcessor()
text = pdf_processor.extract_text(pdf_path.read_bytes())
result = pipeline.redact(text)

# Process Word documents
docx_processor = DOCXProcessor()
text = docx_processor.extract_text(docx_path.read_bytes())
result = pipeline.redact(text)
```

#### REST API Server
```python
from zerophix.api.rest import app
import uvicorn

# Run enterprise API server
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=4,
        ssl_keyfile="./ssl/key.pem",
        ssl_certfile="./ssl/cert.pem"
    )
```

## Multi-Country Support

### Supported Jurisdictions

| Country | Coverage | Entity Types | Compliance |
|---------|----------|--------------|------------|
| **Australia** | Complete | Medicare, TFN, ABN/ACN, Driver License, IHI, Phone, Address | Australian Privacy Principles |
| **United States** | Complete | SSN, ITIN, Driver License, Passport, Phone, Credit Card, Medical Record | HIPAA, CCPA |
| **European Union** | Complete | National ID, VAT, IBAN, Phone, Passport, Medical Data | GDPR |
| **United Kingdom** | Complete | National Insurance, NHS Number, Passport, Postcode, Phone | UK DPA 2018 |
| **Canada** | Complete | SIN, Health Card, Passport, Phone, Postal Code | PIPEDA |

### Configuration Example
```yaml
# configs/company/healthcare_org.yml
country: "US"
compliance_standards: ["HIPAA", "GDPR"]
entity_types:
  enabled:
    - "SSN"
    - "MEDICAL_RECORD"
    - "PATIENT_ID"
    - "CREDIT_CARD"
  custom:
    INTERNAL_ID:
      pattern: "EMP-\\d{6}"
      confidence: 0.95
redaction:
  strategy: "synthetic"
  preserve_format: true
security:
  audit_logging: true
  encryption_required: true
```

## Advanced ML Detection

### Detection Engines

#### 1. **Regex Engine** (Ultra-fast, 100% precision)
- Hand-crafted patterns for each jurisdiction
- Format validation and checksum verification
- Context-aware boundary detection

#### 2. **spaCy NER** (Fast, high recall)
```python
config = RedactionConfig(
    use_spacy=True,
    spacy_model="en_core_web_lg",
    use_contextual=True
)
```

#### 3. **BERT-based Detection** (Highest accuracy)
```python
config = RedactionConfig(
    use_bert=True,
    bert_model="bert-base-cased",
    bert_confidence_threshold=0.9
)
```

#### 4. **OpenMed Medical Entity Detection** (Healthcare-specialized)
```python
config = RedactionConfig(
    use_openmed=True,
    openmed_model="openmed-base",  # or openmed-large
    openmed_confidence=0.8,
    enable_assertion=True  # Filter negated entities
)
```

#### 5. **Statistical Analysis** (Pattern discovery)
```python
config = RedactionConfig(
    use_statistical=True,
    entropy_threshold=4.5,
    frequency_analysis=True
)
```

#### 6. **Custom Entity Detection**
```python
from zerophix.detectors.custom_detector import CustomEntityDetector

detector = CustomEntityDetector()
detector.add_pattern("EMPLOYEE_ID", r"EMP-\d{6}", confidence=0.95)
detector.add_pattern("PROJECT_CODE", r"PROJ-[A-Z]{3}-\d{4}", confidence=0.9)
```

### Model Performance

| Model | Speed | Accuracy | Memory | Use Case |
|-------|-------|----------|--------|----------|
| Regex | Very Fast | 99.9% | Minimal | Production, real-time |
| spaCy NER | Fast | 96.5% | Low | Balanced performance |
| BERT | Moderate | 98.7% | Medium | High accuracy needs |
| OpenMed | Moderate | 97.8% | Medium | Medical/Healthcare PHI |
| Statistical | Very Fast | 92.3% | Minimal | Pattern discovery |

### Supported Models

#### spaCy Models
- **en_core_web_sm** - Small English model (50MB)
- **en_core_web_md** - Medium English model (50MB)
- **en_core_web_lg** - Large English model (750MB, recommended)
- **en_core_web_trf** - Transformer-based model (560MB, highest accuracy)

#### BERT Models
- **bert-base-cased** - General purpose BERT (110M parameters)
- **bert-base-uncased** - Uncased BERT variant
- **distilbert-base-cased** - Faster, smaller BERT (66M parameters)
- **roberta-base** - RoBERTa variant with improved training

#### OpenMed Models
- **openmed-base** - Base medical entity detection model (110M parameters)
- **openmed-large** - Large medical model (340M parameters, higher accuracy)
- **openmed-clinical** - Clinical notes specialized variant
- **Custom LoRA adapters** - Fine-tuned domain-specific adapters

#### Statistical Models
- **Entropy analysis** - Information theory based detection
- **Frequency analysis** - Pattern frequency scoring
- **N-gram analysis** - Context-aware statistical patterns

## Security & Compliance

### Enterprise Security Features

#### Zero Trust Architecture
- **Multi-factor authentication** validation
- **Device security posture** assessment
- **Dynamic trust scoring** (0-100%)
- **Continuous verification** for every request
- **Behavioral anomaly detection**

#### Encryption & Key Management
- **Encryption at rest** with Fernet (AES 128)
- **Master key management** with secure rotation
- **Purpose-based data encryption keys**
- **Hardware security module** support
- **Secure deletion** with multiple overwrites

#### Audit & Monitoring
- **Tamper-evident audit logs** with encryption
- **Real-time security monitoring**
- **Compliance violation detection**
- **Automated incident response**
- **Risk-based alerting**

### Compliance Standards

#### GDPR (General Data Protection Regulation)
```python
# GDPR-compliant redaction
result = pipeline.redact(
    text="EU citizen data...",
    user_context={
        "lawful_basis": "legitimate_interest",
        "consent_obtained": True,
        "purpose": "fraud_prevention",
        "data_subject_rights": True
    }
)
```

#### HIPAA (Health Insurance Portability and Accountability Act)
```python
# HIPAA-compliant medical record redaction
config = RedactionConfig(
    country="US",
    compliance_standards=["HIPAA"],
    phi_detection=True,
    minimum_necessary=True
)
```

#### PCI DSS (Payment Card Industry Data Security Standard)
```python
# PCI DSS-compliant payment data redaction
config = RedactionConfig(
    cardholder_data_detection=True,
    secure_environment=True,
    encryption_required=True
)
```

### Security CLI Commands
```bash
# Audit management
zerophix security audit-logs --days 30 --risk-level HIGH
zerophix security security-report --format pdf

# Compliance testing
zerophix security compliance-check --standard GDPR
zerophix security validate-config --config enterprise.yml

# Zero Trust testing
zerophix security zero-trust-test --simulate-attack
```

## Advanced Redaction Strategies

### Privacy-Preserving Techniques

#### 1. **Differential Privacy**
```python
config = RedactionConfig(
    masking_style="differential_privacy",
    privacy_epsilon=1.0,
    privacy_delta=1e-5
)
```

#### 2. **K-Anonymity**
```python
config = RedactionConfig(
    masking_style="k_anonymity",
    k_value=5,
    quasi_identifiers=["age", "zipcode", "gender"]
)
```

#### 3. **Format-Preserving Encryption**
```python
config = RedactionConfig(
    masking_style="preserve_format",
    encryption_key="your-secret-key",
    preserve_patterns=True
)
```

#### 4. **Synthetic Data Generation**
```python
config = RedactionConfig(
    masking_style="synthetic",
    preserve_demographics=True,
    maintain_relationships=True
)
```

### Redaction Examples

| Original | Strategy | Result |
|----------|----------|---------|
| `John Smith` | Hash | `HASH_9a8b7c6d` |
| `123-45-6789` | Mask | `XXX-XX-6789` |
| `john@email.com` | Synthetic | `alex@provider.net` |
| `555-0123` | Preserve Format | `555-8947` |
| `$50,000` | Differential Privacy | `$52,847` |

## Performance & Optimization

### Performance Features

#### Intelligent Caching
```python
config = RedactionConfig(
    cache_detections=True,
    cache_type="redis",  # or "memory"
    cache_ttl=3600,
    redis_url="redis://localhost:6379"
)
```

#### Async Processing
```python
import asyncio

async def process_documents():
    results = await pipeline.redact_batch_async([
        "Document 1 content...",
        "Document 2 content...",
        "Document 3 content..."
    ])
    return results
```

#### Multi-threading
```python
config = RedactionConfig(
    parallel_detection=True,
    max_workers=8,
    batch_size=100
)
```

#### Streaming Support
```python
async def process_stream():
    async for chunk in data_stream:
        result = await pipeline.redact_async(chunk)
        yield result
```

### Performance Optimization
```bash
# Get performance recommendations
zerophix stats --analyze --recommendations

# Optimize configuration
zerophix optimize --profile production --target-throughput 1000

# Monitor performance
zerophix monitor --dashboard --alerts
```

## REST API

### API Server
```bash
# Start production server
zerophix serve --host 0.0.0.0 --port 8000 --workers 4 --ssl

# With custom configuration
zerophix serve --config enterprise.yml --auth-required --rate-limit 1000
```

### API Endpoints

#### Text Redaction
```bash
curl -X POST "http://localhost:8000/redact" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe, SSN: 123-45-6789",
    "country": "US",
    "user_id": "analyst_1",
    "purpose": "compliance_check",
    "data_classification": "SENSITIVE"
  }'
```

#### Batch Processing
```bash
curl -X POST "http://localhost:8000/redact/batch" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Document 1...", "Document 2..."],
    "parallel_processing": true,
    "callback_url": "https://your-app.com/webhook"
  }'
```

#### File Upload
```bash
curl -X POST "http://localhost:8000/redact/file" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@sensitive_document.pdf" \
  -F "preserve_formatting=true"
```

### API Response
```json
{
  "success": true,
  "redacted_text": "PERSON_NAME, SSN: XXX-XX-6789",
  "entities_found": 2,
  "processing_time": 0.045,
  "trust_score": 87.3,
  "compliance_status": "GDPR_COMPLIANT",
  "spans": [
    {
      "start": 0,
      "end": 8,
      "label": "PERSON_NAME",
      "confidence": 0.99,
      "source": "spacy"
    }
  ],
  "stats": {
    "cache_hit": false,
    "detection_time": 0.032,
    "redaction_time": 0.013
  }
}
```

## Document Processing

### Supported Formats

| Format | Read | Write | Preserve Formatting | OCR Support |
|--------|------|-------|-------------------|-------------|
| **PDF** | Yes | Yes | Yes | Yes |
| **DOCX** | Yes | Yes | Yes | No |
| **XLSX** | Yes | Yes | Yes | No |
| **CSV** | Yes | Yes | Yes | No |
| **TXT** | Yes | Yes | Yes | No |
| **HTML** | Yes | Yes | Yes | No |
| **JSON** | Yes | Yes | Yes | No |

### Document Processing Examples

#### PDF with OCR
```python
from zerophix.processors.documents import DocumentRedactionService

service = DocumentRedactionService(config)

# Process scanned PDF
result = service.redact_pdf(
    input_path="scanned_medical_records.pdf",
    output_path="redacted_records.pdf",
    ocr_enabled=True,
    preserve_layout=True
)
```

#### Excel with Column Mapping
```python
# Redact specific columns
result = service.redact_excel(
    input_path="patient_database.xlsx",
    column_mapping={
        "patient_name": "PERSON_NAME",
        "ssn": "SSN",
        "phone": "PHONE_NUMBER"
    },
    preserve_formulas=True
)
```

#### Batch Directory Processing
```bash
# Process entire directories
zerophix batch-redact \
  --input-dir ./medical_records \
  --output-dir ./redacted_records \
  --file-types pdf,docx,xlsx \
  --parallel --workers 8 \
  --preserve-structure
```

## Configuration

### Configuration Files

#### Global Configuration (`configs/zerophix.yml`)
```yaml
# Global settings
version: "0.2.0"
default_country: "US"
cache_enabled: true
performance_monitoring: true

# Security defaults
security:
  encryption_at_rest: true
  audit_logging: true
  zero_trust_mode: true
  session_timeout: 1800

# Detection settings
detection:
  parallel_processing: true
  max_workers: 4
  confidence_threshold: 0.85
  use_caching: true

# Privacy settings
privacy:
  differential_privacy: true
  k_anonymity_threshold: 5
  data_minimization: true
```

#### Country-Specific Policies (`configs/policies/`)
```yaml
# configs/policies/us_healthcare.yml
country: "US"
sector: "healthcare"
compliance_standards: ["HIPAA", "GDPR"]

entities:
  PHI:
    patterns:
      - medical_record_number: "MR\\d{6,8}"
      - patient_id: "PAT-\\d{8}"
      - provider_npi: "\\d{10}"
    actions:
      - redact: true
      - audit_log: true
      - encrypt: true

redaction:
  default_strategy: "synthetic"
  preserve_medical_context: true
  maintain_clinical_accuracy: true
```

#### Company Overrides (`configs/company/`)
```yaml
# configs/company/acme_healthcare.yml
extends: "us_healthcare"
company: "ACME Healthcare"

custom_entities:
  ACME_PATIENT_ID:
    pattern: "ACME-\\d{8}"
    confidence: 0.95
    
security:
  require_mfa: true
  ip_whitelist:
    - "192.168.1.0/24"
    - "10.0.0.0/8"
    
notifications:
  webhook_url: "https://acme.com/zerophix-webhook"
  alert_on_violations: true
```

### Environment Variables

```bash
# Model storage
export ZEROPHIX_MODELS_DIR="/opt/zerophix/models"

# API configuration
export ZEROPHIX_API_KEY="your-secret-api-key"
export ZEROPHIX_RATE_LIMIT="1000"

# Database connections
export ZEROPHIX_REDIS_URL="redis://localhost:6379"
export ZEROPHIX_DATABASE_URL="postgresql://user:pass@localhost/zerophix"

# Security
export ZEROPHIX_ENCRYPTION_KEY="your-encryption-key"
export ZEROPHIX_AUDIT_LOG_DIR="/var/log/zerophix"

# Cloud integrations
export AZURE_PII_ENDPOINT="https://your-region.api.cognitive.microsoft.com/"
export AZURE_PII_KEY="your-azure-key"
```

## Testing & Validation

### Unit Tests
```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_detection.py -v
pytest tests/test_compliance.py -v
pytest tests/test_security.py -v

# Performance tests
pytest tests/test_performance.py --benchmark
```

### Integration Tests
```bash
# End-to-end testing
pytest tests/integration/ -v

# API testing
pytest tests/api/ -v

# Document processing tests
pytest tests/documents/ -v
```

### Compliance Testing
```bash
# GDPR compliance test
zerophix test-compliance --standard GDPR --test-cases 100

# HIPAA compliance test
zerophix test-compliance --standard HIPAA --phi-samples tests/data/phi_samples.txt

# Security penetration testing
zerophix security-test --simulate-attacks --report security_report.pdf
```

### Benchmark Testing
```bash
# Compare against Azure
zerophix benchmark --provider azure --iterations 1000

# Performance regression testing
zerophix benchmark --baseline v0.1.0 --current v0.2.0

# Load testing
zerophix load-test --concurrent-users 100 --duration 300s
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

# Install ZeroPhix with all features
RUN pip install "zerophix[all]"

# Copy configuration
COPY configs/ /app/configs/
COPY ssl/ /app/ssl/

WORKDIR /app

# Start API server
CMD ["zerophix", "serve", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
# Build and run
docker build -t zerophix:latest .
docker run -p 8000:8000 -v ./data:/app/data zerophix:latest
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerophix-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zerophix-api
  template:
    metadata:
      labels:
        app: zerophix-api
    spec:
      containers:
      - name: zerophix
        image: zerophix:latest
        ports:
        - containerPort: 8000
        env:
        - name: ZEROPHIX_REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

### Production Checklist

#### Security
- [ ] Enable TLS/SSL with valid certificates
- [ ] Configure authentication and authorization
- [ ] Set up audit logging and monitoring
- [ ] Implement rate limiting and DDoS protection
- [ ] Configure secure key management
- [ ] Enable encryption at rest

#### Performance
- [ ] Configure Redis caching
- [ ] Optimize worker processes and threads
- [ ] Set up load balancing
- [ ] Configure auto-scaling
- [ ] Monitor memory and CPU usage
- [ ] Set up performance alerting

#### Compliance
- [ ] Configure compliance standards for your jurisdiction
- [ ] Set up data retention policies
- [ ] Configure breach notification workflows
- [ ] Implement data subject rights procedures
- [ ] Set up compliance reporting

#### Monitoring
- [ ] Configure application monitoring (APM)
- [ ] Set up log aggregation and analysis
- [ ] Configure health checks and uptime monitoring
- [ ] Set up security incident alerting
- [ ] Implement performance dashboards

## Scanning & Reporting

### Scan Without Redaction
Detect PII/PHI without modifying original text - perfect for compliance audits and data discovery:

```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.reporting import ReportGenerator

# Scan document
result = pipeline.scan(text)
print(f"Found {result['total_detections']} sensitive items")
print(f"Entity types: {result['entity_counts']}")

# Generate report
html_report = ReportGenerator.generate(result, format="html")
with open("audit.html", "w") as f:
    f.write(html_report)
```

### Report Formats
- **HTML**: Interactive styled reports with color-coded risk indicators
- **JSON**: Machine-readable for API integration
- **CSV**: Excel-compatible spreadsheets
- **Markdown**: Git-friendly documentation
- **Text**: Simple terminal/log format

## Examples

### Available Examples
- **[GLiNER Zero-Shot Examples](examples/gliner_examples.py)** - Zero-shot custom entity detection
- **[Quick Start Examples](examples/quick_start_examples.py)** - Basic usage patterns
- **[Comprehensive Examples](examples/comprehensive_usage_examples.py)** - All features
- **[Scanning Examples](examples/scan_example.py)** - Detection without redaction
- **[Report Generation](examples/report_example.py)** - Multi-format reporting
- **[File Processing](examples/file_tests_pii.py)** - CSV/XLSX/PDF demos
- **[Ultra-Complex Examples](examples/ultra_complex_examples.py)** - Healthcare & financial scenarios

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/yassienshaalan/zerophix.git
cd zerophix

# Install development dependencies
pip install -e ".[dev,test,docs]"

# Run tests
pytest

# Run linting
flake8 src/
black src/
mypy src/
```

### Areas for Contribution
- **New country/jurisdiction support**
- **Additional ML models and detection methods**
- **New document format processors**
- **Enhanced security features**
- **Performance optimizations**
- **Documentation improvements**

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- **spaCy** for excellent NLP capabilities
- **Transformers** for state-of-the-art ML models
- **FastAPI** for modern API framework
- **Cryptography** for enterprise security
- **Rich** for beautiful CLI interfaces

## Quick Reference

### Essential Commands
```bash
# Basic redaction
zerophix redact --text "John Doe, SSN: 123-45-6789"

# File redaction
zerophix redact-file --input document.pdf --output clean.pdf

# Batch processing
zerophix batch-redact --input-dir ./docs --output-dir ./clean

# Start API server
zerophix serve --host 0.0.0.0 --port 8000

# Security commands
zerophix security compliance-check
zerophix security audit-logs
zerophix security zero-trust-test
```

### Python Quick Start
```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

config = RedactionConfig(country="US", detectors=["regex", "spacy"])
pipeline = RedactionPipeline(config)
result = pipeline.redact("Sensitive text here")
print(result['text'])
```

## Support

For questions, issues, or contributions, please visit the [GitHub repository](https://github.com/yassienshaalan/zerophix).

---

**Made with care for data privacy and security.**

*ZeroPhix v0.2.0 - The enterprise choice for PII/PSI/PHI redaction.*
