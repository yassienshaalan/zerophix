"""
Example: Scanning text for PII/PHI without redac    scan_result = pipe.scan(sample_texts[0])
    
    print(f"\nScan complete!")
    print(f"  Total detections: {result['total_detections']}")

This example demonstrates how to use the scan() method to detect
PII/PHI entities without modifying the original text.
"""

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig
import json

# Sample text with various PII/PHI types
sample_texts = [
    # Australian PII
    """
    Patient Record:
    Name: John Smith
    DOB: 1977-04-02
    Medicare: 2424 12345 1-2
    Phone: 04 1234 5678
    Email: john.smith@example.com
    Address: 123 Collins Street, Melbourne VIC 3000
    """,
    
    # Business information
    """
    Company: ACME Corporation
    ABN: 11 111 111 111
    ACN: 123 456 789
    Contact: Jane Doe
    Mobile: 0412 345 678
    TFN: 123 456 782
    """,
    
    # Medical records
    """
    Patient consultation notes:
    IHI: 8003608166690503
    Dr. Sarah Johnson reviewed patient Michael Brown (DOB 15/03/1985)
    Prescription issued. Follow-up in 2 weeks.
    Contact: 03 9876 5432
    """,
]

def example_basic_scan():
    """Basic scan example - detect PII/PHI and show results"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Scan")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    result = pipe.scan(sample_texts[0])
    
    print(f"\nScan complete!")
    print(f"  Total detections: {result['total_detections']}")
    print(f"  Contains PII/PHI: {result['has_pii']}")
    print(f"\nEntity breakdown:")
    for entity_type, count in result['entity_counts'].items():
        print(f"  - {entity_type}: {count}")


def example_detailed_scan():
    """Detailed scan with full detection information"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Detailed Scan with Detection Details")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    result = pipe.scan(sample_texts[1])
    
    print(f"\nFound {result['total_detections']} PII/PHI entities:\n")
    
    for i, detection in enumerate(result['detections'], 1):
        print(f"Detection #{i}:")
        print(f"  Type: {detection['label']}")
        print(f"  Text: '{detection['text']}'")
        print(f"  Confidence: {detection['score']:.2f}")
        print(f"  Position: {detection['start']}-{detection['end']}")
        print()


def example_batch_scan():
    """Scan multiple texts and aggregate results"""
    print("=" * 70)
    print("EXAMPLE 3: Batch Scanning Multiple Documents")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    total_docs = len(sample_texts)
    total_detections = 0
    docs_with_pii = 0
    all_entity_types = {}
    
    for i, text in enumerate(sample_texts, 1):
        result = pipe.scan(text)
        
        print(f"\nDocument {i}/{total_docs}:")
        print(f"  Detections: {result['total_detections']}")
        
        if result['has_pii']:
            docs_with_pii += 1
            total_detections += result['total_detections']
            
            # Aggregate entity types
            for entity_type, count in result['entity_counts'].items():
                all_entity_types[entity_type] = all_entity_types.get(entity_type, 0) + count
    
    print("\n" + "-" * 70)
    print("BATCH SUMMARY:")
    print(f"  Total documents: {total_docs}")
    print(f"  Documents with PII/PHI: {docs_with_pii}")
    print(f"  Total detections: {total_detections}")
    print(f"\nAll entity types found:")
    for entity_type, count in sorted(all_entity_types.items(), key=lambda x: -x[1]):
        print(f"  - {entity_type}: {count}")


def example_json_export():
    """Export scan results as JSON"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Export Scan Results as JSON")
    print("=" * 70)
    
    cfg = RedactionConfig(country="AU", use_openmed=False)
    pipe = RedactionPipeline.from_config(cfg)
    
    result = pipe.scan(sample_texts[2])
    
    # Export as JSON
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    print("\nJSON Output:")
    print(json_output)


def example_scan_and_redact_comparison():
    """Compare scan vs redact - show what would be redacted"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Scan vs Redact Comparison")
    print("=" * 70)
    
    text = "Contact Dr. Smith at 0412 345 678 or email dr.smith@hospital.com.au"
    
    cfg = RedactionConfig(country="AU", use_openmed=False, masking_style="replace")
    pipe = RedactionPipeline.from_config(cfg)
    
    # First scan
    scan_result = pipe.scan(text)
    print(f"\nSCAN Results:")
    print(f"  Original text: {text}")
    print(f"  Detections: {scan_result['total_detections']}")
    for det in scan_result['detections']:
        print(f"    - {det['label']}: '{det['text']}'")
    
    # Then redact
    redact_result = pipe.redact(text)
    print(f"\nREDACTION Results:")
    print(f"  Redacted text: {redact_result['text']}")
    print(f"  Entities redacted: {len(redact_result['spans'])}")


if __name__ == "__main__":
    print("\nZeroPhix Scanning Examples\n")
    
    example_basic_scan()
    example_detailed_scan()
    example_batch_scan()
    example_json_export()
    example_scan_and_redact_comparison()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
