"""
Integration test for Australian entity detection with checksum validation
"""
import sys
sys.path.insert(0, 'src')

from zerophix.pipelines.redaction import RedactionPipeline

# Test text with Australian entities
test_text = """
John Smith works in Sydney, NSW 2000 Australia.
His Tax File Number is 123-456-782 and his ABN is 51 824 753 556.
Company ACN: 000-000-019
Medicare: 2688 00123 3 1
BSB: 032-000 Account: 12345678
Driver License NSW: 12345678
Phone: +61 2 9876 5432
Email: john.smith@company.com.au
Invalid TFN: 123-456-789 (should be rejected by checksum)
Invalid ABN: 51 824 753 557 (should be rejected by checksum)
"""

print("Australian Entity Detection with Checksum Validation")
print("=" * 60)
print("\nTest Text:")
print(test_text)
print("=" * 60)

# Initialize pipeline with Australian policy
pipeline = RedactionPipeline(policy='au')

# Detect entities
results = pipeline.detect(test_text)

print(f"\nDetected {len(results)} entities:")
print("-" * 60)
for i, entity in enumerate(results, 1):
    text_span = test_text[entity['start']:entity['end']]
    print(f"{i}. {entity['type']:<20} | {text_span:<25} | Score: {entity['score']:.3f}")
    if 'validated' in entity:
        print(f"   {'Checksum validated' if entity['validated'] else 'Checksum INVALID'}")

print("\n" + "=" * 60)

# Verify that invalid checksums were rejected
valid_tfn_found = any('123-456-782' in test_text[e['start']:e['end']] and e['type'] == 'TFN' for e in results)
invalid_tfn_found = any('123-456-789' in test_text[e['start']:e['end']] and e['type'] == 'TFN' for e in results)
valid_abn_found = any('51 824 753 556' in test_text[e['start']:e['end']] and e['type'] == 'ABN' for e in results)
invalid_abn_found = any('51 824 753 557' in test_text[e['start']:e['end']] and e['type'] == 'ABN' for e in results)

print("\nValidation Results:")
print(f"[PASS] Valid TFN detected: {valid_tfn_found}")
print(f"[PASS] Invalid TFN rejected: {not invalid_tfn_found}")
print(f"[PASS] Valid ABN detected: {valid_abn_found}")
print(f"[PASS] Invalid ABN rejected: {not invalid_abn_found}")

if valid_tfn_found and not invalid_tfn_found and valid_abn_found and not invalid_abn_found:
    print("\n[SUCCESS] ALL CHECKSUM VALIDATIONS PASSED!")
else:
    print("\n[FAIL] Some validation checks failed")

# Redact the text
redacted = pipeline.redact(test_text)
print("\n" + "=" * 60)
print("Redacted Text:")
print(redacted)
