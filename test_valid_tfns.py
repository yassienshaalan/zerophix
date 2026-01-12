"""
Test valid TFNs
"""
from src.zerophix.detectors.au_validators import validate_tfn

valid_tfns = ["123456782", "876543210", "324567899"]
invalid_tfns = ["123456789", "111111111", "000000000"]

print("Testing Valid TFNs:")
for tfn in valid_tfns:
    result = validate_tfn(tfn)
    print(f"  {tfn}: {result} {'[PASS]' if result else '[FAIL]'}")

print("\nTesting Invalid TFNs:")
for tfn in invalid_tfns:
    result = validate_tfn(tfn)
    print(f"  {tfn}: {result} {'[PASS]' if not result else '[FAIL]'}")
