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
