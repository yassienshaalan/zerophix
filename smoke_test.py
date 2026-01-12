#!/usr/bin/env python3
"""
Smoke test for ZeroPhix installation and functionality
Run after installation to verify everything works
"""
import sys
sys.path.insert(0, 'src')

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

print("=" * 70)
print("ZEROPHIX SMOKE TEST")
print("=" * 70)

# Test 1: Regex-only (instant, no ML models)
print("\n[TEST 1] Regex-only detection (instant, offline)")
print("-" * 70)
config = RedactionConfig(
    use_spacy=False,
    use_gliner=False,
    use_bert=False,
    country='US'
)
pipeline = RedactionPipeline(config)

text1 = "John Smith SSN: 123-45-6789 Email: john@example.com Phone: 555-123-4567"
result1 = pipeline.redact(text1)
print(f"Original: {text1}")
print(f"Redacted: {result1['text']}")
print(f"Entities: {len(result1['spans'])} found")
for span in result1['spans']:
    print(f"  - {span['label']}: {text1[span['start']:span['end']]} (confidence: {span['score']:.2f})")

# Test 2: Australian with checksums
print("\n[TEST 2] Australian detection with checksum validation")
print("-" * 70)
config2 = RedactionConfig(
    use_spacy=False,
    use_gliner=False,
    use_bert=False,
    country='AU'
)
pipeline2 = RedactionPipeline(config2)

text2 = "TFN: 123-456-782 ABN: 51 824 753 556 Email: test@example.com Medicare: 2688 00123 3 1"
result2 = pipeline2.redact(text2)
print(f"Original: {text2}")
print(f"Redacted: {result2['text']}")
print(f"Entities: {len(result2['spans'])} found")
for span in result2['spans']:
    print(f"  - {span['label']}: {text2[span['start']:span['end']]} (confidence: {span['score']:.2f})")

# Test 3: With ML models (downloads on first run)
print("\n[TEST 3] ML models (spaCy + GLiNER + BERT)")
print("-" * 70)
print("Note: This will download models on first run (~2GB), then cache locally")
config3 = RedactionConfig(
    use_spacy=True,
    use_gliner=True,
    use_bert=True,
    country='AU'
)
pipeline3 = RedactionPipeline(config3)

text3 = """Patient: John Smith
TFN: 123-456-782
Email: john.smith@hospital.com.au
Phone: +61 2 9876 5432
Medicare: 2688 00123 3 1"""

result3 = pipeline3.redact(text3)
print("Original:")
print(text3)
print("\nRedacted:")
print(result3['text'])
print(f"\nEntities: {len(result3['spans'])} found")
for span in result3['spans'][:10]:  # Show first 10
    print(f"  - {span['label']}: {text3[span['start']:span['end']]} (confidence: {span['score']:.2f}, detector: {span.get('detector', 'unknown')})")

print("\n" + "=" * 70)
print("SMOKE TEST COMPLETE!")
print("=" * 70)
print("\nAll models downloaded and cached. ZeroPhix is now 100% offline.")
print("Next steps:")
print("  - Start API: python examples/run_api.py")
print("  - CLI usage: zerophix --help")
print("  - Run benchmarks: python scripts/run_json_examples.py")
