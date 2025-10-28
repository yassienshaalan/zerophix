# ZeroPhi Usage Guide - Step by Step

This guide walks you through using ZeroPhi from installation to advanced enterprise deployment.

## Table of Contents

1. [Quick Start (5 minutes)](#quick-start-5-minutes)
2. [Basic Usage](#basic-usage)
3. [Advanced Configuration](#advanced-configuration)
4. [Enterprise Setup](#enterprise-setup)
5. [API Integration](#api-integration)
6. [Security & Compliance](#security--compliance)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start (5 minutes)

### Step 1: Install ZeroPhi
```bash
# Basic installation
pip install zerophi

# Or with all features
pip install "zerophi[spacy,bert,documents,api]"
```

### Step 2: Test Basic Redaction
```bash
# Simple command line test
zerophi redact --text "John Smith, SSN: 123-45-6789, Email: john@email.com"
```

**Expected Output:**
```json
{
  "redacted_text": "HASH_9a8b7c6d, SSN: XXX-XX-6789, Email: HASH_3e4f5a2b",
  "entities_found": 3,
  "processing_time": 0.05
}
```

### Step 3: Test with File
```bash
# Create a test file
echo "Patient: Jane Doe, Phone: 555-123-4567, Medical Record: MR123456" > test.txt

# Redact the file
zerophi redact --infile test.txt --outfile redacted.txt --include-stats
```

**Congratulations!** ZeroPhi is working. Continue below for advanced usage.

---

## Basic Usage

### Command Line Interface

#### 1. Text Redaction
```bash
# Basic redaction (US patterns)
zerophi redact \
  --text "John Doe, SSN: 123-45-6789, Phone: (555) 123-4567" \
  --country US

# Multiple countries
zerophi redact \
  --text "John Smith, Medicare: 2828 12345 1-7, Phone: 04 1234 5678" \
  --country AU

# Custom redaction style
zerophi redact \
  --text "Credit Card: 4532-1234-5678-9012" \
  --masking-style "preserve_format"
```

#### 2. File Processing
```bash
# Process different file types
zerophi redact-file --input document.pdf --output clean.pdf
zerophi redact-file --input spreadsheet.xlsx --output clean.xlsx --preserve-formatting
zerophi redact-file --input data.csv --output clean.csv
```

#### 3. Batch Processing
```bash
# Process multiple files
zerophi batch-redact \
  --input-dir ./sensitive_docs \
  --output-dir ./clean_docs \
  --file-types pdf,docx,xlsx \
  --parallel --workers 4
```

### Python API

#### 1. Basic Python Usage
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig

# Step 1: Create configuration
config = RedactionConfig(
    country="US",                    # Country for entity patterns
    detectors=["regex", "spacy"],    # Detection methods
    masking_style="hash",            # Redaction style
    cache_detections=True            # Enable caching
)

# Step 2: Initialize pipeline
pipeline = RedactionPipeline(config)

# Step 3: Redact text
text = "John Doe, SSN: 123-45-6789, Phone: (555) 123-4567"
result = pipeline.redact(text)

# Step 4: Use results
print(f"Original: {text}")
print(f"Redacted: {result['text']}")
print(f"Found {result['entities_found']} sensitive entities")
```

#### 2. Advanced Python Usage
```python
# Advanced configuration
config = RedactionConfig(
    country="US",
    detectors=["regex", "spacy", "bert", "statistical"],
    use_contextual=True,             # Context-aware detection
    parallel_detection=True,         # Parallel processing
    masking_style="synthetic",       # Generate synthetic data
    cache_detections=True,
    use_async=True                   # Async processing
)

pipeline = RedactionPipeline(config)

# Redact with user context for security/compliance
user_context = {
    "user_id": "analyst_123",
    "purpose": "compliance_check",
    "lawful_basis": "legitimate_interest",
    "data_classification": "SENSITIVE"
}

result = pipeline.redact(
    text="Patient John Doe, Medical Record: MR123456",
    user_context=user_context,
    session_id="session_789"
)
```

---

## Advanced Configuration

### Step 1: Create Configuration Files

#### Global Configuration (`zerophi_config.yml`)
```yaml
# Global settings
default_country: "US"
cache_enabled: true
performance_monitoring: true

# Detection settings
detection:
  parallel_processing: true
  max_workers: 4
  confidence_threshold: 0.85
  
# Privacy settings
privacy:
  differential_privacy: true
  k_anonymity_threshold: 5
```

#### Country-Specific Policy (`policies/healthcare_us.yml`)
```yaml
country: "US"
sector: "healthcare"
compliance_standards: ["HIPAA", "GDPR"]

entities:
  PHI:
    patterns:
      - medical_record: "MR\\d{6,8}"
      - patient_id: "PAT-\\d{8}"
    actions:
      - redact: true
      - audit_log: true

redaction:
  default_strategy: "synthetic"
  preserve_medical_context: true
```

#### Company Override (`company/acme_corp.yml`)
```yaml
extends: "healthcare_us"
company: "ACME Healthcare"

custom_entities:
  ACME_EMPLOYEE_ID:
    pattern: "EMP-\\d{6}"
    confidence: 0.95
    
security:
  require_mfa: true
  audit_all_access: true
```

### Step 2: Use Custom Configuration
```bash
# Command line with config
zerophi redact \
  --text "Employee EMP-123456 accessed Patient PAT-12345678" \
  --config policies/healthcare_us.yml \
  --company acme_corp

# Python with config
config = RedactionConfig.from_file("policies/healthcare_us.yml")
config.load_company_overrides("company/acme_corp.yml")
pipeline = RedactionPipeline(config)
```

---

## Enterprise Setup

### Step 1: Install with All Enterprise Features
```bash
# Complete enterprise installation
pip install "zerophi[all]"

# Install specific dependencies
pip install spacy transformers torch
pip install fastapi uvicorn redis
pip install cryptography
```

### Step 2: Configure Security
```python
from zerophi.security import SecureConfiguration, SecureAuditLogger

# Initialize secure configuration
secure_config = SecureConfiguration("enterprise_config.json")

# Configure security settings
secure_config.set("security.encryption_at_rest", True)
secure_config.set("security.audit_logging", True)
secure_config.set("security.zero_trust_mode", True)
secure_config.set("compliance.standards", ["GDPR", "HIPAA", "PCI_DSS"])

# Initialize audit logging
audit_logger = SecureAuditLogger(
    log_directory="./audit_logs",
    compliance_standards=["GDPR", "HIPAA"],
    encryption_key=secure_config.get("security.encryption_key")
)
```

### Step 3: Production Pipeline Setup
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.performance.optimization import PerformanceCache

# Production configuration
config = RedactionConfig(
    country="US",
    detectors=["regex", "spacy", "bert"],
    use_contextual=True,
    parallel_detection=True,
    max_workers=8,
    cache_detections=True,
    cache_type="redis",
    redis_url="redis://localhost:6379",
    use_async=True
)

# Initialize with security
pipeline = RedactionPipeline(config)

# Test enterprise pipeline
test_text = "CONFIDENTIAL: Patient John Doe, SSN: 123-45-6789, Record: MR123456"
result = pipeline.redact(
    text=test_text,
    user_context={
        "user_id": "enterprise_user",
        "authorized": True,
        "purpose": "healthcare_processing",
        "data_classification": "RESTRICTED"
    }
)
```

---

## API Integration

### Step 1: Start API Server
```bash
# Development server
zerophi serve --host localhost --port 8000

# Production server
zerophi serve \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --ssl-cert ./ssl/cert.pem \
  --ssl-key ./ssl/key.pem
```

### Step 2: Test API Endpoints

#### Text Redaction API
```bash
curl -X POST "http://localhost:8000/redact" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "text": "John Doe, SSN: 123-45-6789",
    "country": "US",
    "user_id": "api_user_123",
    "purpose": "compliance_check",
    "data_classification": "SENSITIVE"
  }'
```

#### Batch Processing API
```bash
curl -X POST "http://localhost:8000/redact/batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "texts": [
      "Document 1: John Smith, Phone: 555-1234",
      "Document 2: Jane Doe, Email: jane@email.com"
    ],
    "parallel_processing": true
  }'
```

#### File Upload API
```bash
curl -X POST "http://localhost:8000/redact/file" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@sensitive_document.pdf" \
  -F "preserve_formatting=true"
```

### Step 3: Python API Client
```python
import requests

class ZeroPhiClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    def redact_text(self, text, country="US", **kwargs):
        response = requests.post(
            f"{self.base_url}/redact",
            json={"text": text, "country": country, **kwargs},
            headers=self.headers
        )
        return response.json()
    
    def redact_batch(self, texts, **kwargs):
        response = requests.post(
            f"{self.base_url}/redact/batch",
            json={"texts": texts, **kwargs},
            headers=self.headers
        )
        return response.json()

# Usage
client = ZeroPhiClient(api_key="your-api-key")
result = client.redact_text("John Doe, SSN: 123-45-6789")
print(result['redacted_text'])
```

---

## Security & Compliance

### Step 1: Configure Compliance Standards
```bash
# Test compliance validation
zerophi security compliance-check \
  --user-id compliance_officer \
  --purpose gdpr_audit \
  --data-classification RESTRICTED
```

### Step 2: Setup Audit Logging
```python
from zerophi.security import SecureAuditLogger, ComplianceStandard

# Initialize audit logger
audit_logger = SecureAuditLogger(
    log_directory="./enterprise_audit",
    compliance_standards=[
        ComplianceStandard.GDPR,
        ComplianceStandard.HIPAA,
        ComplianceStandard.PCI_DSS
    ],
    retention_days=2555  # 7 years
)

# Manual audit logging
audit_logger.log_redaction_event(
    operation="MANUAL_REDACTION",
    text_length=len(sensitive_text),
    entities_found=5,
    entity_types=["SSN", "PHONE", "EMAIL"],
    user_id="compliance_officer",
    country="US",
    data_classification="RESTRICTED"
)
```

### Step 3: Zero Trust Validation
```bash
# Test Zero Trust security
zerophi security zero-trust-test \
  --ip-address 192.168.1.100 \
  --user-id security_admin
```

### Step 4: Generate Security Reports
```bash
# Daily security report
zerophi security security-report --days 1

# Weekly compliance report
zerophi security security-report --days 7 --event-type COMPLIANCE_EVENT

# View audit logs
zerophi security audit-logs
```

---

## Performance Optimization

### Step 1: Performance Testing
```bash
# Benchmark against baseline
zerophi benchmark --iterations 1000 --output benchmark.json

# Performance statistics
zerophi stats --show-recommendations
```

### Step 2: Optimize Configuration
```python
from zerophi.performance.optimization import PerformanceOptimizer

# Auto-optimize configuration
optimizer = PerformanceOptimizer()
optimized_config = optimizer.optimize_config(
    current_config=config,
    target_throughput=1000,  # docs per second
    max_latency=50,          # milliseconds
    available_memory=8       # GB
)

# Apply optimizations
pipeline = RedactionPipeline(optimized_config)
```

### Step 3: Caching Setup
```python
# Redis caching for production
config = RedactionConfig(
    cache_detections=True,
    cache_type="redis",
    redis_url="redis://production-redis:6379",
    cache_ttl=3600,  # 1 hour
    cache_max_items=100000
)

# Memory caching for development
config = RedactionConfig(
    cache_detections=True,
    cache_type="memory",
    cache_max_items=10000
)
```

### Step 4: Monitor Performance
```python
from zerophi.performance.optimization import PerformanceMonitor

monitor = PerformanceMonitor()

# Get performance metrics
metrics = monitor.get_current_metrics()
print(f"Avg throughput: {metrics.avg_throughput:.2f} chars/sec")
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")

# Get recommendations
recommendations = monitor.get_recommendations()
for rec in recommendations:
    print(f"Recommendation: {rec}")
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Installation Issues
```bash
# Missing dependencies
pip install --upgrade pip setuptools wheel
pip install "zerophi[all]"

# spaCy model download
python -m spacy download en_core_web_sm

# NLTK data download
python -c "import nltk; nltk.download('punkt')"
```

#### 2. Performance Issues
```bash
# Check system resources
zerophi validate --performance-check

# Optimize configuration
zerophi optimize --profile production

# Monitor real-time performance
zerophi monitor --dashboard
```

#### 3. Detection Issues
```python
# Test individual detectors
from zerophi.detectors.regex_detector import RegexDetector
from zerophi.detectors.spacy_detector import SpacyDetector

# Test regex detector
regex_detector = RegexDetector("US")
spans = regex_detector.detect("SSN: 123-45-6789")
print(f"Regex found: {len(spans)} entities")

# Test spaCy detector
spacy_detector = SpacyDetector()
spans = spacy_detector.detect("John Doe lives in New York")
print(f"spaCy found: {len(spans)} entities")
```

#### 4. Security Issues
```bash
# Validate security configuration
zerophi security config-security

# Test encryption
zerophi security test-encryption

# Check audit logs
zerophi security audit-logs --days 1 --risk-level HIGH
```

#### 5. API Issues
```bash
# Check API health
curl http://localhost:8000/health

# Validate API configuration
zerophi validate --api-config

# Debug API requests
curl -v -X POST "http://localhost:8000/redact" \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

### Debug Mode
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Detailed pipeline debugging
config = RedactionConfig(debug_mode=True)
pipeline = RedactionPipeline(config)

# This will show detailed processing steps
result = pipeline.redact("Debug text with SSN: 123-45-6789")
```

### Getting Help
```bash
# CLI help
zerophi --help
zerophi redact --help
zerophi security --help

# Configuration validation
zerophi validate --config your-config.yml

# Health check
zerophi health --full-check
```

---

## Next Steps

1. **Production Deployment**: Follow the [Deployment Guide](docs/deployment.md)
2. **Custom Entities**: Create custom detection patterns for your organization
3. **Integration**: Integrate with your existing data pipeline
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Training**: Train your team on ZeroPhi features and best practices

For more detailed information, see the complete documentation at [docs.zerophi.com](https://docs.zerophi.com).