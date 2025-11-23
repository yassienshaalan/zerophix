# zerophi

Zero-PII/PHI redaction library with AU-first coverage. It composes **high-precision regex/patterns** with **ML NER models** (e.g., OpenMed) and supports **country/company-specific policies**.

## Highlights
- AU-first policy: Medicare #, TFN, ABN/ACN, driver licence, IHI, AU phones/addresses.
- **Scan mode**: Detect PII/PHI without redacting - perfect for audits and compliance checks.
- **Rich reporting**: Generate reports in JSON, HTML, Markdown, CSV, or plain text formats.
- Tiered detectors: `regex` → `ner` → `openmed` (download on demand).
- Pluggable policies: country + company overrides via YAML.
- CLI and Python API.
- Benchmark harness (including an Azure PII Redaction comparison stub).

## Install

Base (regex + core):
```bash
pip install zerophi
```

With OpenMed/Transformers:
```bash
pip install "zerophi[openmed]"
```

With Azure benchmark client:
```bash
pip install "zerophi[azurebench]"
```

## Quickstart

### Redaction
```bash
zerophi redact --text "John Smith DOB 1977-04-02 medicare 2424 12345 1-2" --country AU
```

### Scanning (Detection without Redaction)
```bash
# Quick scan with statistics
zerophi scan --text "John Smith, Medicare: 2424 12345 1-2, Phone: 0412 345 678" --stats-only

# Detailed scan with report
zerophi scan --infile document.txt --format html --output report.html
```

### Python API

#### Redaction
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig

cfg = RedactionConfig(country="AU", use_openmed=False)
pipe = RedactionPipeline.from_config(cfg)
result = pipe.redact("Call me on 04 1234 5678; ABN 11 111 111 111")
print(result["text"])  # Redacted text
print(result["spans"])  # Detected entities
```

#### Scanning
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig

cfg = RedactionConfig(country="AU", use_openmed=False)
pipe = RedactionPipeline.from_config(cfg)
result = pipe.scan("Call me on 04 1234 5678; ABN 11 111 111 111")

print(f"Total detections: {result['total_detections']}")
print(f"Has PII/PHI: {result['has_pii']}")
print(f"Entity counts: {result['entity_counts']}")
for detection in result['detections']:
    print(f"  - {detection['label']}: {detection['text']}")
```

#### Report Generation
```python
from zerophi.reporting import ReportGenerator

# Generate report in various formats
html_report = ReportGenerator.generate(result, format="html")
json_report = ReportGenerator.generate(result, format="json")
markdown_report = ReportGenerator.generate(result, format="markdown")

# Save to file
with open("report.html", "w") as f:
    f.write(html_report)
```

## Model downloads
Models are **not bundled**. Use:
```bash
zerophi download-model --name openmed-base
```
Downloads to `$ZEROPHI_MODELS_DIR` or `~/.cache/zerophi/models`.

## Policies
See `src/zerophi/policies/au.yml` for AU PII/PHI patterns and actions. Override with a company config in `configs/company/yourco.yml` and pass `--company yourco`.

## CLI Commands

### `zerophi scan` - Detect PII/PHI without Redaction

Scan text for sensitive information without modifying it. Perfect for audits, compliance checks, and understanding what PII/PHI exists in your documents.

**Basic Usage:**
```bash
# Scan text directly
zerophi scan --text "Your text here"

# Scan a file
zerophi scan --infile document.txt

# Quick statistics only
zerophi scan --infile document.txt --stats-only
```

**Report Generation:**
```bash
# Generate HTML report (great for viewing)
zerophi scan --infile document.txt --format html --output report.html

# Generate JSON report (for programmatic processing)
zerophi scan --infile document.txt --format json --output report.json

# Generate Markdown report (for documentation)
zerophi scan --infile document.txt --format markdown --output report.md

# Generate CSV report (for spreadsheet analysis)
zerophi scan --infile document.txt --format csv --output report.csv

# Print to stdout
zerophi scan --text "Sample text" --format text
```

**Options:**
- `--text`: Text to scan directly
- `--infile`: Path to input file
- `--country`: Country policy (default: AU)
- `--company`: Company-specific policy overlay
- `--use-openmed`: Use OpenMed ML model for better accuracy
- `--format`: Report format (json, markdown, html, csv, text)
- `--output`: Save report to file (omit to print to stdout)
- `--stats-only`: Show only summary statistics
- `--verbose`: Show detailed processing information

### `zerophi redact` - Redact PII/PHI

Redact sensitive information from text.

**Basic Usage:**
```bash
# Redact text
zerophi redact --text "John: 0412 345 678"

# Redact a file
zerophi redact --infile document.txt
```

**With Report Generation:**
```bash
# Redact and generate detection report
zerophi redact --infile document.txt --report html --report-output detections.html
```

**Options:**
- `--text`: Text to redact
- `--infile`: Path to input file
- `--country`: Country policy (default: AU)
- `--company`: Company-specific policy
- `--use-openmed`: Use OpenMed ML model
- `--masking-style`: Redaction style (hash, mask, replace, brackets)
- `--report`: Generate report (json, markdown, html, csv, text)
- `--report-output`: Save report to file

### Other Commands

**Download Models:**
```bash
zerophi download-model --name openmed-base
```

**View Active Policy:**
```bash
zerophi show-policy --country AU --company acme
```

## Report Formats

### JSON
Structured data perfect for programmatic processing and integration with other tools.
```json
{
  "scan_timestamp": "2025-11-23T10:30:00",
  "summary": {
    "total_detections": 5,
    "has_pii": true,
    "entity_counts": {"AU_PHONE": 2, "AU_MEDICARE": 1}
  },
  "detections": [...]
}
```

### HTML
Beautifully styled, interactive report perfect for human review. Includes:
- Color-coded summary with risk indicators
- Entity type breakdown table
- Detailed detection cards with context
- Responsive design

### Markdown
Clean, readable format perfect for:
- Documentation
- Version control (git-friendly)
- Integration with static site generators
- README files

### CSV
Spreadsheet-compatible format for:
- Excel/Google Sheets analysis
- Data processing
- Bulk reporting
- Statistical analysis

### Plain Text
Simple, clean format for:
- Terminal output
- Log files
- Email reports
- Legacy systems

## Examples

See the `examples/` directory for comprehensive examples:
- **`scan_example.py`**: Python examples of scanning functionality
- **`report_example.py`**: Python examples of report generation
- **`CLI_EXAMPLES.md`**: Extensive CLI usage examples
- **`run_json_examples.py`**: JSON processing examples

## Use Cases

### 1. Compliance Auditing
```bash
# Scan all documents and generate audit reports
zerophi scan --infile contracts.pdf --format html --output audit_report.html
```

### 2. Pre-Send Email Checks
```bash
# Quick check before sending an email
zerophi scan --infile draft_email.txt --stats-only
```

### 3. Data Discovery
```bash
# Find what PII exists in your database exports
zerophi scan --infile db_export.csv --format csv --output pii_inventory.csv
```

### 4. Redaction with Audit Trail
```bash
# Redact and keep a record of what was found
zerophi redact --infile document.txt --report html --report-output audit.html > redacted.txt
```

### 5. Batch Processing
```powershell
# Scan multiple files
Get-ChildItem *.txt | ForEach-Object {
    zerophi scan --infile $_.Name --format html --output "reports/$($_.BaseName).html"
}
```

## Benchmarks
Use `scripts/bench_against_azure.py` (requires `ZEROPHI_AZURE_ENDPOINT` + `ZEROPHI_AZURE_KEY`).
