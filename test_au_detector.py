"""
Direct test of Australian regex detector with checksum validation
"""
import sys
sys.path.insert(0, 'src')

from zerophix.detectors.regex_detector import RegexDetector

# Test text with Australian entities
test_text = """
Valid Australian Entities:
TFN: 123-456-782
ABN: 51 824 753 556
ACN: 000-000-019
Medicare: 2688 00123 3 1

Invalid Australian Entities (wrong checksums):
TFN: 123-456-789
ABN: 51 824 753 557
ACN: 000-000-018
"""

print("Australian Entity Detection with Checksum Validation")
print("=" * 70)
print("\nTest Text:")
print(test_text)
print("=" * 70)

# Initialize regex detector with Australian policy
detector = RegexDetector(country='AU', company=None)

# Detect entities
detected = detector.detect(test_text)

print(f"\nDetected {len(detected)} entities:")
print("-" * 70)
for i, span in enumerate(detected, 1):
    text_span = test_text[span.start:span.end]
    print(f"{i}. {span.label:<15} | '{text_span:<20}' | Score: {span.score:.3f}")

print("\n" + "=" * 70)

# Count valid vs invalid
tfn_valid = sum(1 for s in detected if '123-456-782' in test_text[s.start:s.end] and s.label == 'TFN')
tfn_invalid = sum(1 for s in detected if '123-456-789' in test_text[s.start:s.end] and s.label == 'TFN')
abn_valid = sum(1 for s in detected if '51 824 753 556' in test_text[s.start:s.end] and s.label == 'ABN')
abn_invalid = sum(1 for s in detected if '51 824 753 557' in test_text[s.start:s.end] and s.label == 'ABN')
acn_valid = sum(1 for s in detected if '000-000-019' in test_text[s.start:s.end] and s.label == 'ACN')
acn_invalid = sum(1 for s in detected if '000-000-018' in test_text[s.start:s.end] and s.label == 'ACN')

print("\nValidation Results:")
print(f"[PASS] Valid TFN (123-456-782) detected: {tfn_valid == 1}")
print(f"[PASS] Invalid TFN (123-456-789) rejected: {tfn_invalid == 0}")
print(f"[PASS] Valid ABN (51 824 753 556) detected: {abn_valid == 1}")
print(f"[PASS] Invalid ABN (51 824 753 557) rejected: {abn_invalid == 0}")
print(f"[PASS] Valid ACN (000-000-019) detected: {acn_valid == 1}")
print(f"[PASS] Invalid ACN (000-000-018) rejected: {acn_invalid == 0}")

all_passed = (tfn_valid == 1 and tfn_invalid == 0 and 
              abn_valid == 1 and abn_invalid == 0 and
              acn_valid == 1 and acn_invalid == 0)

if all_passed:
    print("\n[SUCCESS] ALL CHECKSUM VALIDATIONS PASSED!")
    print("Australian entity detection with mathematical validation is working correctly.")
else:
    print("\n[FAIL] Some validation checks failed")
    print(f"  TFN valid: {tfn_valid}, invalid: {tfn_invalid}")
    print(f"  ABN valid: {abn_valid}, invalid: {abn_invalid}")
    print(f"  ACN valid: {acn_valid}, invalid: {acn_invalid}")
