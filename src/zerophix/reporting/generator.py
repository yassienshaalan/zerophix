import json
import csv
from typing import Dict, List
from datetime import datetime
from io import StringIO


class ReportGenerator:
    """Generate formatted reports from scan results"""

    @staticmethod
    def generate(scan_result: Dict, format: str = "json") -> str:
        """Generate a report in the specified format.
        
        Args:
            scan_result: The result from RedactionPipeline.scan()
            format: One of 'json', 'markdown', 'html', 'csv', 'text'
        
        Returns:
            Formatted report as a string
        """
        format = format.lower()
        if format == "json":
            return ReportGenerator._generate_json(scan_result)
        elif format == "markdown" or format == "md":
            return ReportGenerator._generate_markdown(scan_result)
        elif format == "html":
            return ReportGenerator._generate_html(scan_result)
        elif format == "csv":
            return ReportGenerator._generate_csv(scan_result)
        elif format == "text" or format == "txt":
            return ReportGenerator._generate_text(scan_result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def _generate_json(scan_result: Dict) -> str:
        """Generate JSON report"""
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_detections": scan_result["total_detections"],
                "has_pii": scan_result["has_pii"],
                "entity_counts": scan_result["entity_counts"]
            },
            "detections": scan_result["detections"]
        }
        return json.dumps(report, ensure_ascii=False, indent=2)

    @staticmethod
    def _generate_markdown(scan_result: Dict) -> str:
        """Generate Markdown report"""
        lines = ["# PII/PHI Scan Report", ""]
        lines.append(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Detections:** {scan_result['total_detections']}")
        lines.append(f"**Contains PII/PHI:** {'Yes' if scan_result['has_pii'] else 'No'}")
        lines.append("")
        
        if scan_result['total_detections'] > 0:
            lines.append("## Summary by Entity Type")
            lines.append("")
            lines.append("| Entity Type | Count |")
            lines.append("|-------------|-------|")
            for entity, count in sorted(scan_result['entity_counts'].items()):
                lines.append(f"| {entity} | {count} |")
            lines.append("")
            
            lines.append("## Detected Entities")
            lines.append("")
            for i, det in enumerate(scan_result['detections'], 1):
                lines.append(f"### Detection {i}")
                lines.append(f"- **Type:** {det['label']}")
                lines.append(f"- **Text:** `{det['text']}`")
                lines.append(f"- **Confidence:** {det['score']:.2f}")
                lines.append(f"- **Position:** {det['start']}-{det['end']}")
                lines.append(f"- **Context:** ...{det['context']}...")
                lines.append("")
        else:
            lines.append("*No PII/PHI detected in the text.*")
        
        return "\n".join(lines)

    @staticmethod
    def _generate_html(scan_result: Dict) -> str:
        """Generate HTML report"""
        html = ['<!DOCTYPE html>', '<html lang="en">', '<head>',
                '<meta charset="UTF-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                '<title>PII/PHI Scan Report</title>',
                '<style>',
                'body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }',
                '.container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
                'h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }',
                'h2 { color: #555; margin-top: 30px; }',
                '.summary { background: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0; }',
                '.summary-item { margin: 10px 0; font-size: 16px; }',
                '.summary-item strong { color: #007acc; }',
                'table { width: 100%; border-collapse: collapse; margin: 20px 0; }',
                'th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }',
                'th { background-color: #007acc; color: white; }',
                'tr:hover { background-color: #f5f5f5; }',
                '.detection { background: #fff9e6; padding: 15px; margin: 15px 0; border-left: 4px solid #ffa500; border-radius: 4px; }',
                '.detection-header { font-weight: bold; color: #d9534f; margin-bottom: 10px; }',
                '.detection-item { margin: 5px 0; }',
                '.label { display: inline-block; background: #007acc; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }',
                '.text-highlight { background: #ffeb3b; padding: 2px 4px; border-radius: 2px; font-family: monospace; }',
                '.context { color: #666; font-style: italic; }',
                '.no-pii { color: #5cb85c; font-size: 18px; text-align: center; padding: 20px; }',
                '</style>',
                '</head>', '<body>', '<div class="container">']
        
        html.append('<h1>PII/PHI Scan Report</h1>')
        
        html.append('<div class="summary">')
        html.append(f'<div class="summary-item"><strong>Scan Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>')
        html.append(f'<div class="summary-item"><strong>Total Detections:</strong> {scan_result["total_detections"]}</div>')
        has_pii = '<span style="color: #d9534f;">Yes</span>' if scan_result['has_pii'] else '<span style="color: #5cb85c;">No</span>'
        html.append(f'<div class="summary-item"><strong>Contains PII/PHI:</strong> {has_pii}</div>')
        html.append('</div>')
        
        if scan_result['total_detections'] > 0:
            html.append('<h2>Summary by Entity Type</h2>')
            html.append('<table>')
            html.append('<tr><th>Entity Type</th><th>Count</th></tr>')
            for entity, count in sorted(scan_result['entity_counts'].items()):
                html.append(f'<tr><td><span class="label">{entity}</span></td><td>{count}</td></tr>')
            html.append('</table>')
            
            html.append('<h2>Detected Entities</h2>')
            for i, det in enumerate(scan_result['detections'], 1):
                html.append('<div class="detection">')
                html.append(f'<div class="detection-header">Detection #{i}</div>')
                html.append(f'<div class="detection-item"><strong>Type:</strong> <span class="label">{det["label"]}</span></div>')
                html.append(f'<div class="detection-item"><strong>Text:</strong> <span class="text-highlight">{det["text"]}</span></div>')
                html.append(f'<div class="detection-item"><strong>Confidence:</strong> {det["score"]:.2f}</div>')
                html.append(f'<div class="detection-item"><strong>Position:</strong> {det["start"]}-{det["end"]}</div>')
                html.append(f'<div class="detection-item"><strong>Context:</strong> <span class="context">...{det["context"]}...</span></div>')
                html.append('</div>')
        else:
            html.append('<div class="no-pii">No PII/PHI detected in the text.</div>')
        
        html.extend(['</div>', '</body>', '</html>'])
        return '\n'.join(html)

    @staticmethod
    def _generate_csv(scan_result: Dict) -> str:
        """Generate CSV report"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Detection #', 'Entity Type', 'Text', 'Confidence', 'Start Position', 'End Position', 'Context'])
        
        # Data rows
        for i, det in enumerate(scan_result['detections'], 1):
            writer.writerow([
                i,
                det['label'],
                det['text'],
                f"{det['score']:.2f}",
                det['start'],
                det['end'],
                det['context']
            ])
        
        return output.getvalue()

    @staticmethod
    def _generate_text(scan_result: Dict) -> str:
        """Generate plain text report"""
        lines = ["=" * 60]
        lines.append("PII/PHI SCAN REPORT")
        lines.append("=" * 60)
        lines.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Detections: {scan_result['total_detections']}")
        lines.append(f"Contains PII/PHI: {'Yes' if scan_result['has_pii'] else 'No'}")
        lines.append("")
        
        if scan_result['total_detections'] > 0:
            lines.append("SUMMARY BY ENTITY TYPE")
            lines.append("-" * 60)
            for entity, count in sorted(scan_result['entity_counts'].items()):
                lines.append(f"  {entity}: {count}")
            lines.append("")
            
            lines.append("DETECTED ENTITIES")
            lines.append("-" * 60)
            for i, det in enumerate(scan_result['detections'], 1):
                lines.append(f"\nDetection #{i}")
                lines.append(f"  Type: {det['label']}")
                lines.append(f"  Text: {det['text']}")
                lines.append(f"  Confidence: {det['score']:.2f}")
                lines.append(f"  Position: {det['start']}-{det['end']}")
                lines.append(f"  Context: ...{det['context']}...")
        else:
            lines.append("No PII/PHI detected in the text.")
        
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
