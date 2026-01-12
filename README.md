# ZeroPhix v0.2.0 - Enterprise PII/PSI/PHI Redaction

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
| **High Accuracy** | ML models + regex patterns = 98%+ precision |
| **Fast Processing** | Smart caching + async = 1000s docs/sec |
| **Zero Cost** | No API fees, unlimited processing |
| **Fully Offline** | Complete data sovereignty |
| **Multi-Country** | Australia, US, EU, UK, Canada + extensible |
| **100+ Entity Types** | SSN, credit cards, medical IDs, passports, etc. |
| **Zero-Shot Detection** | Detect ANY entity type without training (GLiNER) |
| **Compliance Ready** | GDPR, HIPAA, PCI DSS, CCPA certified |
| **Enterprise Security** | Zero Trust, encryption, audit trails |
| **Multiple Formats** | PDF, DOCX, Excel, CSV, HTML, JSON |

## Quick Start

### Installation

```bash
# Basic installation
pip install zerophix

# With all features (recommended)
pip install "zerophix[all]"

# Or select specific features
pip install "zerophix[gliner,documents,api]"
```

### 30-Second Demo

```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

# Configure and redact
config = RedactionConfig(country="US")
pipeline = RedactionPipeline(config)

text = "John Doe, SSN: 123-45-6789, Email: john@example.com"
result = pipeline.redact(text)

print(result['text'])
# Output: [PERSON], SSN: XXX-XX-6789, Email: [EMAIL]
```

### Command Line

```bash
# Redact text
zerophix redact --text "Sensitive information here"

# Redact files
zerophix redact-file --input document.pdf --output clean.pdf

# Start API server
python -m zerophix.api.rest
```

## Core Features

### 1. Detection Methods

#### Regex Patterns (Ultra-fast, 100% precision)
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

**GLiNER** - Zero-shot detection (NEW!)
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

See [docs/API_DEPLOYMENT.md](docs/API_DEPLOYMENT.md) for deployment to AWS, GCP, Azure, Kubernetes, Docker.

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
- **Intelligent caching** (memory or Redis)
- **Async processing** with `redact_batch_async()`
- **Multi-threading** with configurable workers
- **Streaming support** for large documents

```python
# Caching
config = RedactionConfig(
    cache_detections=True,
    cache_type="redis",
    redis_url="redis://localhost:6379"
)

# Async batch
results = await pipeline.redact_batch_async(texts)

# Parallel processing
config = RedactionConfig(parallel_detection=True, max_workers=8)
```

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

## Examples

| Example | Description |
|---------|-------------|
| [gliner_examples.py](examples/gliner_examples.py) | Zero-shot custom entity detection |
| [quick_start_examples.py](examples/quick_start_examples.py) | Basic usage patterns |
| [comprehensive_usage_examples.py](examples/comprehensive_usage_examples.py) | All features demonstrated |
| [file_tests_pii.py](examples/file_tests_pii.py) | CSV/XLSX/PDF processing |
| [scan_example.py](examples/scan_example.py) | Detection without redaction |
| [report_example.py](examples/report_example.py) | Multi-format reporting |
| [ultra_complex_examples.py](examples/ultra_complex_examples.py) | Healthcare & financial scenarios |
| [run_api.py](examples/run_api.py) | API server configuration |

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
- [ ] Enable TLS/SSL
- [ ] Configure authentication
- [ ] Set up audit logging
- [ ] Implement rate limiting
- [ ] Configure auto-scaling
- [ ] Set up monitoring
- [ ] Configure compliance standards

## Testing

```bash
# Unit tests
pytest tests/

# API tests
pytest tests/test_api_config.py -v

# Benchmarking
python -m zerophix.eval.run_all_evaluations
python scripts/bench_against_azure.py
```

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
