# ZeroPhi CLI Examples for Scanning and Reporting

This file contains practical CLI command examples for scanning text and generating reports.

## Basic Scanning

### Scan text directly
```bash
zerophi scan --text "John Smith, Medicare: 2424 12345 1-2, Phone: 0412 345 678"
```

### Scan a file
```bash
zerophi scan --infile medical_records.txt
```

### Scan with statistics only
```bash
zerophi scan --infile patient_data.txt --stats-only
```

## Report Generation

### Generate JSON report
```bash
zerophi scan --infile document.txt --format json --output report.json
```

### Generate HTML report (great for viewing in browser)
```bash
zerophi scan --infile document.txt --format html --output report.html
```

### Generate Markdown report
```bash
zerophi scan --infile document.txt --format markdown --output report.md
```

### Generate CSV report (for spreadsheet analysis)
```bash
zerophi scan --infile document.txt --format csv --output report.csv
```

### Generate plain text report
```bash
zerophi scan --infile document.txt --format text --output report.txt
```

## Advanced Options

### Scan with OpenMed model (more accurate)
```bash
zerophi scan --infile document.txt --use-openmed --format html --output report.html
```

### Scan with company-specific policies
```bash
zerophi scan --infile document.txt --country AU --company acme --format json
```

### Verbose output
```bash
zerophi scan --infile document.txt --verbose
```

### Print report to stdout instead of file
```bash
zerophi scan --text "Sample text" --format markdown
```

## Redaction with Report

### Redact and generate report simultaneously
```bash
zerophi redact --infile document.txt --report html --report-output detection_report.html
```

### Redact with custom masking and JSON report
```bash
zerophi redact --text "John: 0412 345 678" --masking-style replace --report json
```

## Batch Processing Examples

### Scan multiple files and save reports
```bash
# Windows PowerShell
Get-ChildItem *.txt | ForEach-Object { zerophi scan --infile $_.Name --format html --output "reports/$($_.BaseName)_report.html" }
```

### Scan all text files and create summary
```bash
# Windows PowerShell
Get-ChildItem *.txt | ForEach-Object { 
    Write-Host "Processing: $($_.Name)"
    zerophi scan --infile $_.Name --stats-only
}
```

## Real-World Scenarios

### Scenario 1: Audit medical records
```bash
zerophi scan --infile patient_records.txt --format html --output audit_report.html --verbose
```

### Scenario 2: Check email for PII before sending
```bash
zerophi scan --infile draft_email.txt --stats-only
```

### Scenario 3: Generate compliance report
```bash
zerophi scan --infile company_data.csv --format csv --output compliance_report.csv
```

### Scenario 4: Quick check with stats
```bash
zerophi scan --text "Check this: ABN 11 111 111 111, TFN 123 456 789" --stats-only
```

### Scenario 5: Full audit trail
```bash
# Scan and create multiple report formats
zerophi scan --infile document.txt --format json --output reports/audit.json
zerophi scan --infile document.txt --format html --output reports/audit.html
zerophi scan --infile document.txt --format markdown --output reports/audit.md
```

## Integration Examples

### Export to JSON for further processing
```bash
zerophi scan --infile data.txt --format json --output scan_results.json
# Then process with other tools: jq, Python, etc.
```

### Generate HTML report and open in browser
```bash
zerophi scan --infile document.txt --format html --output report.html
Start-Process report.html  # Windows
```

## Tips

1. **Always use --stats-only first** for a quick overview before generating detailed reports
2. **HTML reports** are best for human review (styled, easy to read)
3. **JSON reports** are best for programmatic processing
4. **CSV reports** are best for spreadsheet analysis
5. **Markdown reports** are best for documentation and version control
6. **Text reports** are best for terminal output and logging

## Common Workflows

### Workflow 1: Review → Report → Redact
```bash
# Step 1: Quick stats
zerophi scan --infile document.txt --stats-only

# Step 2: Full report if PII found
zerophi scan --infile document.txt --format html --output review.html

# Step 3: Redact if needed
zerophi redact --infile document.txt > redacted.txt
```

### Workflow 2: Batch audit with reports
```bash
# Create reports directory
New-Item -ItemType Directory -Force -Path reports

# Scan all documents
Get-ChildItem *.txt | ForEach-Object {
    zerophi scan --infile $_.Name --format html --output "reports/$($_.BaseName)_scan.html"
}
```

### Workflow 3: CI/CD Pipeline check
```bash
# Check if document contains PII (exit code based check)
zerophi scan --infile document.txt --format json --output scan.json
# Parse scan.json to check has_pii field
```
