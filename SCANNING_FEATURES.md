# ZeroPhi - Scanning & Reporting Features Summary

## What's New

ZeroPhi now supports comprehensive **scanning** and **reporting** capabilities, allowing you to detect PII/PHI without redacting the original text and generate beautiful, actionable reports.

## Features Added

### 1. Scan Mode (Detection without Redaction)
- Detect all PII/PHI entities without modifying the original text
- Get detailed statistics about detected entities
- View entity counts, positions, confidence scores, and context
- Perfect for compliance audits, data discovery, and risk assessment

### 2. Multi-Format Report Generation
Generate professional reports in 5 formats:
- **JSON**: Structured data for programmatic processing
- **HTML**: Beautifully styled, interactive reports with color-coded risk indicators
- **Markdown**: Git-friendly documentation format
- **CSV**: Spreadsheet-compatible for Excel/Google Sheets analysis
- **Plain Text**: Simple, clean format for terminals and logs

### 3. Enhanced CLI Commands

#### New: `zerophi scan`
```bash
# Quick statistics
zerophi scan --infile document.txt --stats-only

# Generate HTML report
zerophi scan --infile document.txt --format html --output report.html

# Multiple formats available
zerophi scan --text "Sample" --format json|markdown|html|csv|text
```

#### Enhanced: `zerophi redact`
```bash
# Redact and generate detection report
zerophi redact --infile document.txt --report html --report-output audit.html
```

### 4. Python API Additions

#### Scanning
```python
result = pipe.scan(text)
# Returns: {
#   "original_text": str,
#   "total_detections": int,
#   "entity_counts": dict,
#   "detections": list,
#   "has_pii": bool
# }
```

#### Report Generation
```python
from zerophi.reporting import ReportGenerator

report = ReportGenerator.generate(scan_result, format="html")
```

## New Files Created

### Core Implementation
- `src/zerophi/reporting/__init__.py` - Reporting module package
- `src/zerophi/reporting/generator.py` - Report generation engine (5 formats)
- Updated `src/zerophi/pipelines/redaction.py` - Added `scan()` method
- Updated `src/zerophi/cli.py` - Added scan command and report options

### Documentation & Examples
- `examples/scan_example.py` - 8 comprehensive scanning examples
- `examples/report_example.py` - 8 report generation examples
- `examples/CLI_EXAMPLES.md` - Extensive CLI usage guide
- Updated `README.md` - Complete documentation of new features

## Use Cases

1. **Compliance Auditing**: Scan documents to identify PII/PHI for GDPR, HIPAA compliance
2. **Data Discovery**: Find what sensitive data exists in your systems
3. **Pre-Send Checks**: Verify emails/documents before sharing
4. **Risk Assessment**: Generate reports showing PII/PHI exposure levels
5. **Batch Processing**: Scan multiple files and generate audit reports
6. **Redaction Planning**: See what will be redacted before making changes

## Quick Start

### Scan a document
```bash
zerophi scan --infile medical_record.txt --format html --output audit.html
```

### Batch scan all text files
```powershell
Get-ChildItem *.txt | ForEach-Object {
    zerophi scan --infile $_.Name --format html --output "reports/$($_.BaseName).html"
}
```

### Python scanning
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig
from zerophi.reporting import ReportGenerator

cfg = RedactionConfig(country="AU")
pipe = RedactionPipeline.from_config(cfg)

# Scan
result = pipe.scan(text)
print(f"Found {result['total_detections']} PII/PHI entities")

# Generate report
html_report = ReportGenerator.generate(result, format="html")
with open("report.html", "w") as f:
    f.write(html_report)
```

## Report Format Comparison

| Format     | Best For                          | Features                                    |
|------------|-----------------------------------|---------------------------------------------|
| JSON       | APIs, automation, integration     | Structured, parseable, complete data        |
| HTML       | Human review, presentations       | Styled, interactive, color-coded            |
| Markdown   | Documentation, version control    | Clean, git-friendly, readable               |
| CSV        | Spreadsheet analysis              | Excel-compatible, tabular data              |
| Plain Text | Terminal output, logs             | Simple, universal compatibility             |

## What Gets Detected

For AU country policy:
- Medicare numbers
- Tax File Numbers (TFN)
- ABN/ACN
- Driver licenses
- Individual Healthcare Identifiers (IHI)
- Phone numbers (mobile and landline)
- Email addresses
- Dates of birth
- Names (with OpenMed)
- Addresses
- And more...

## Report Contents

All reports include:
- **Scan timestamp**: When the scan was performed
- **Summary statistics**: Total detections, PII/PHI presence indicator
- **Entity counts**: Breakdown by entity type
- **Detailed detections**: Each found entity with:
  - Entity type (label)
  - Detected text
  - Confidence score
  - Position in document
  - Context (surrounding text)

## HTML Report Features

The HTML report includes:
- Professional styling with responsive design
- Color-coded risk indicators (Low, Medium, High)
- Interactive summary cards
- Sortable entity type table
- Detailed detection cards with context
- Print-friendly layout
- No external dependencies (all CSS inline)

## Tips

1. Start with `--stats-only` for a quick overview
2. Use HTML format for stakeholder presentations
3. Use JSON format for integration with other tools
4. Use CSV format for bulk data analysis in Excel
5. Combine `redact` with `--report` to maintain audit trails
6. Use batch processing for large document sets

## Next Steps

1. Try the examples:
   ```bash
   python examples/scan_example.py
   python examples/report_example.py
   ```

2. Read the CLI examples:
   ```bash
   code examples/CLI_EXAMPLES.md
   ```

3. Check the updated README:
   ```bash
   code README.md
   ```

## Testing

Test the new features:
```bash
# Basic scan
zerophi scan --text "Medicare: 2424 12345 1-2, Phone: 0412 345 678" --stats-only

# Generate all report formats
zerophi scan --text "Test: 0412 345 678" --format html
zerophi scan --text "Test: 0412 345 678" --format json
zerophi scan --text "Test: 0412 345 678" --format markdown
zerophi scan --text "Test: 0412 345 678" --format csv
zerophi scan --text "Test: 0412 345 678" --format text
```

---

**Built for privacy and compliance**
