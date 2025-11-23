"""
Example: Generating Reports from PII/PHI Scans

This example demonstrates how to generate reports in various formats
(JSON, Markdown, HTML, CSV, Plain Text) from scan results.
"""

from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig
from zerophi.reporting import ReportGenerator
from pathlib import Path

# Sample text with PII/PHI
SAMPLE_TEXT = """
Patient Medical Record - Confidential

Patient Name: Emily Thompson
Date of Birth: 15/08/1990
Medicare Number: 2428 98765 4-3
Individual Healthcare Identifier (IHI): 8003608166690503

Contact Information:
Mobile: 0412 987 654
Email: emily.thompson@email.com.au
Address: 456 Lonsdale Street, Melbourne VIC 3000

Tax File Number: 987 654 321
Driver License: 12345678 (VIC)

Emergency Contact:
Name: David Thompson
Phone: 03 9876 5432

Medical Notes:
Patient presented with symptoms on 2024-11-15.
Prescribed medication. Follow-up scheduled.
Insurance claim reference: INS-2024-0012345
"""


def example_generate_json_report():
    """Generate a JSON report"""
    print("=" * 70)
    print("EXAMPLE 1: Generate JSON Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    # Scan the text
    scan_result = pipe.scan(SAMPLE_TEXT)
    
    # Generate JSON report
    report = ReportGenerator.generate(scan_result, format="json")
    
    print("\nJSON Report:")
    print(report)
    print("\nJSON report generated successfully!")


def example_generate_markdown_report():
    """Generate a Markdown report"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Generate Markdown Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    report = ReportGenerator.generate(scan_result, format="markdown")
    
    print("\nMarkdown Report Preview:")
    print(report[:500] + "...\n")
    
    # Save to file
    output_path = Path("reports/sample_report.md")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(f"Markdown report saved to: {output_path}")


def example_generate_html_report():
    """Generate an HTML report"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Generate HTML Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    report = ReportGenerator.generate(scan_result, format="html")
    
    # Save to file
    output_path = Path("reports/sample_report.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(f"HTML report saved to: {output_path}")
    print(f"  Open in browser: file:///{output_path.absolute()}")


def example_generate_csv_report():
    """Generate a CSV report"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Generate CSV Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    report = ReportGenerator.generate(scan_result, format="csv")
    
    print("\nCSV Report Preview:")
    lines = report.split('\n')[:5]
    for line in lines:
        print(line)
    print("...\n")
    
    # Save to file
    output_path = Path("reports/sample_report.csv")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(f"CSV report saved to: {output_path}")


def example_generate_text_report():
    """Generate a plain text report"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Generate Plain Text Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    report = ReportGenerator.generate(scan_result, format="text")
    
    print("\n" + report)
    
    # Save to file
    output_path = Path("reports/sample_report.txt")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(f"\nText report saved to: {output_path}")


def example_batch_report_generation():
    """Generate all report formats at once"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Batch Generate All Report Formats")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    
    formats = ["json", "markdown", "html", "csv", "text"]
    extensions = {"json": "json", "markdown": "md", "html": "html", "csv": "csv", "text": "txt"}
    
    output_dir = Path("reports/batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating reports in all formats...")
    for fmt in formats:
        report = ReportGenerator.generate(scan_result, format=fmt)
        output_path = output_dir / f"pii_scan_report.{extensions[fmt]}"
        output_path.write_text(report, encoding="utf-8")
        print(f"  {fmt.upper()}: {output_path}")
    
    print(f"\nAll reports saved to: {output_dir.absolute()}")


def example_custom_report_with_summary():
    """Create a custom summary report"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Custom Summary Report")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    scan_result = pipe.scan(SAMPLE_TEXT)
    
    # Create custom summary
    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY - PII/PHI DETECTION")
    print("="*60)
    print(f"\nRisk Level: {'HIGH' if scan_result['total_detections'] > 5 else 'MEDIUM' if scan_result['total_detections'] > 0 else 'LOW'}")
    print(f"Total Sensitive Items Found: {scan_result['total_detections']}")
    print(f"Document Contains PII/PHI: {'YES' if scan_result['has_pii'] else 'NO'}")
    
    if scan_result['has_pii']:
        print("\n" + "-"*60)
        print("DETECTED SENSITIVE INFORMATION CATEGORIES:")
        print("-"*60)
        
        for entity_type, count in sorted(scan_result['entity_counts'].items(), key=lambda x: -x[1]):
            risk_level = "[HIGH]" if count > 2 else "[MED]" if count > 1 else "[LOW]"
            print(f"  {risk_level} {entity_type}: {count} occurrence(s)")
        
        print("\n" + "-"*60)
        print("RECOMMENDATIONS:")
        print("-"*60)
        print("  • This document contains sensitive PII/PHI")
        print("  • Consider redacting before sharing")
        print("  • Ensure proper access controls are in place")
        print("  • Review data handling policies")
    
    print("\n" + "="*60)


def example_compare_reports():
    """Compare different text samples"""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Comparative Report")
    print("=" * 70)
    
    samples = {
        "Medical Record": SAMPLE_TEXT,
        "Business Email": "Contact us at info@acme.com.au or call 1300 123 456. ABN: 11 111 111 111",
        "Clean Text": "This is a sample document without any sensitive information.",
    }
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    print("\nScanning multiple documents...\n")
    print(f"{'Document':<20} {'Detections':<12} {'Has PII':<10} {'Entity Types'}")
    print("-" * 70)
    
    for name, text in samples.items():
        result = pipe.scan(text)
        entity_types = ", ".join(result['entity_counts'].keys()) if result['entity_counts'] else "None"
        has_pii_status = "Yes" if result['has_pii'] else "No"
        
        print(f"{name:<20} {result['total_detections']:<12} {has_pii_status:<10} {entity_types}")


if __name__ == "__main__":
    print("\nZeroPhi Report Generation Examples\n")
    
    # Create reports directory
    Path("reports").mkdir(exist_ok=True)
    
    example_generate_json_report()
    example_generate_markdown_report()
    example_generate_html_report()
    example_generate_csv_report()
    example_generate_text_report()
    example_batch_report_generation()
    example_custom_report_with_summary()
    example_compare_reports()
    
    print("\n" + "=" * 70)
    print("All report examples completed!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - reports/sample_report.md")
    print("  - reports/sample_report.html")
    print("  - reports/sample_report.csv")
    print("  - reports/sample_report.txt")
    print("  - reports/batch/pii_scan_report.*")
