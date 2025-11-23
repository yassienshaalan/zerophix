# ZeroPhi Quick Reference

## CLI Commands Quick Reference

### Scan Commands

```bash
# Basic scan
zerophi scan --text "Your text here"
zerophi scan --infile document.txt

# Statistics only
zerophi scan --infile document.txt --stats-only

# Generate reports
zerophi scan --infile doc.txt --format html --output report.html
zerophi scan --infile doc.txt --format json --output report.json
zerophi scan --infile doc.txt --format markdown --output report.md
zerophi scan --infile doc.txt --format csv --output report.csv
zerophi scan --infile doc.txt --format text --output report.txt

# Advanced options
zerophi scan --infile doc.txt --use-openmed --country AU --company acme
zerophi scan --infile doc.txt --verbose
```

### Redact Commands

```bash
# Basic redaction
zerophi redact --text "Your text here"
zerophi redact --infile document.txt

# With masking styles
zerophi redact --text "Test" --masking-style hash
zerophi redact --text "Test" --masking-style mask
zerophi redact --text "Test" --masking-style replace
zerophi redact --text "Test" --masking-style brackets

# With report generation
zerophi redact --infile doc.txt --report html --report-output audit.html
```

## Python API Quick Reference

### Setup
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig
from zerophi.reporting import ReportGenerator

cfg = RedactionConfig(country="AU", use_openmed=False)
pipe = RedactionPipeline.from_config(cfg)
```

### Scanning
```python
# Scan text
result = pipe.scan("Your text here")

# Access results
print(result['total_detections'])    # Number of PII/PHI found
print(result['has_pii'])             # Boolean: contains PII/PHI?
print(result['entity_counts'])       # Dict: {entity_type: count}
print(result['detections'])          # List of detection details
print(result['original_text'])       # Original text

# Iterate detections
for det in result['detections']:
    print(f"{det['label']}: {det['text']}")
    print(f"  Position: {det['start']}-{det['end']}")
    print(f"  Confidence: {det['score']}")
    print(f"  Context: {det['context']}")
```

### Redacting
```python
# Redact text
result = pipe.redact("Your text here")

# Access results
print(result['text'])    # Redacted text
print(result['spans'])   # List of redacted spans
```

### Report Generation
```python
# Generate reports
html = ReportGenerator.generate(scan_result, format="html")
json_report = ReportGenerator.generate(scan_result, format="json")
markdown = ReportGenerator.generate(scan_result, format="markdown")
csv = ReportGenerator.generate(scan_result, format="csv")
text = ReportGenerator.generate(scan_result, format="text")

# Save to file
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
```

## Configuration Options

### RedactionConfig Parameters
```python
RedactionConfig(
    country="AU",              # Country policy (AU, US, etc.)
    company=None,              # Company-specific policy overlay
    use_openmed=False,         # Use ML model for better detection
    masking_style="hash",      # hash, mask, replace, brackets
    models_dir=None,           # Custom model directory
    keep_surrogates=False,     # Keep surrogate values
    thresholds={'ner_conf': 0.5}  # Confidence thresholds
)
```

## Report Format Selection Guide

| When to Use  | Format     | CLI Flag         |
|--------------|------------|------------------|
| API/Automation | JSON     | `--format json`  |
| Human Review | HTML       | `--format html`  |
| Documentation | Markdown  | `--format markdown` |
| Excel Analysis | CSV      | `--format csv`   |
| Terminal/Logs | Text      | `--format text`  |

## Common Workflows

### 1. Quick Check
```bash
zerophi scan --infile document.txt --stats-only
```

### 2. Full Audit
```bash
zerophi scan --infile document.txt --format html --output audit.html
```

### 3. Batch Processing
```powershell
Get-ChildItem *.txt | ForEach-Object {
    zerophi scan --infile $_.Name --format html --output "reports/$($_.BaseName).html"
}
```

### 4. Redact with Audit Trail
```bash
zerophi redact --infile document.txt --report html --report-output audit.html > redacted.txt
```

### 5. Python Batch Processing
```python
import os
from pathlib import Path

for file in Path("documents").glob("*.txt"):
    text = file.read_text()
    result = pipe.scan(text)
    
    if result['has_pii']:
        report = ReportGenerator.generate(result, format="html")
        output = Path("reports") / f"{file.stem}_report.html"
        output.write_text(report)
```

## Entity Types (AU Policy)

| Entity Type     | Description                      |
|-----------------|----------------------------------|
| AU_MEDICARE     | Medicare card number             |
| AU_TFN          | Tax File Number                  |
| AU_ABN          | Australian Business Number       |
| AU_ACN          | Australian Company Number        |
| AU_IHI          | Individual Healthcare Identifier |
| AU_PHONE        | Australian phone numbers         |
| AU_DRIVER_LIC   | Driver license numbers           |
| EMAIL           | Email addresses                  |
| DATE            | Dates (DOB, etc.)                |
| PERSON          | Person names (with OpenMed)      |
| ADDRESS         | Physical addresses               |

## Masking Styles

| Style      | Example Input     | Example Output        |
|------------|-------------------|-----------------------|
| hash       | "0412 345 678"    | "a1b2c3d4e5f6"        |
| mask       | "0412 345 678"    | "*************"       |
| replace    | "0412 345 678"    | "<AU_PHONE>"          |
| brackets   | "0412 345 678"    | "[AU_PHONE]"          |

## Command Options Reference

### scan
- `--text TEXT`: Text to scan
- `--infile PATH`: Input file path
- `--country CODE`: Country policy (default: AU)
- `--company NAME`: Company policy
- `--use-openmed`: Use ML model
- `--format FORMAT`: Report format (json|markdown|html|csv|text)
- `--output PATH`: Output file path
- `--stats-only`: Show only statistics
- `--verbose`: Verbose output

### redact
- `--text TEXT`: Text to redact
- `--infile PATH`: Input file path
- `--country CODE`: Country policy (default: AU)
- `--company NAME`: Company policy
- `--use-openmed`: Use ML model
- `--masking-style STYLE`: Masking style (hash|mask|replace|brackets)
- `--report FORMAT`: Generate report
- `--report-output PATH`: Report output path

## Environment Variables

```bash
# Model download directory
export ZEROPHI_MODELS_DIR=/path/to/models

# Azure benchmark (optional)
export ZEROPHI_AZURE_ENDPOINT=https://...
export ZEROPHI_AZURE_KEY=...
```

## Tips & Best Practices

1. Use `--stats-only` for quick checks
2. Generate HTML reports for stakeholders
3. Use JSON for automation/integration
4. Keep audit trails with `--report` flag
5. Test with small samples first
6. Use `--use-openmed` for better accuracy (slower)
7. Batch process with PowerShell/Python scripts
8. Remember: scanning doesn't modify original text
9. HTML reports are self-contained (no external dependencies)
10. CSV format best for tabular analysis in Excel

## Getting Help

```bash
zerophi --help
zerophi scan --help
zerophi redact --help
zerophi show-policy --help
zerophi download-model --help
```

## Examples Location

- Python scanning: `examples/scan_example.py`
- Python reporting: `examples/report_example.py`
- CLI examples: `examples/CLI_EXAMPLES.md`
- JSON examples: `examples/run_json_examples.py`
