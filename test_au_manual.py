"""
Manual test of Australian validators
"""
from src.zerophix.detectors.au_validators import (
    validate_tfn,
    validate_abn,
    validate_acn,
    validate_medicare,
    validate_bsb,
    validate_centrelink_crn
)

print("Testing Australian Validators")
print("=" * 50)

# Test TFN
print("\nTFN Validation:")
print(f"123456782 (valid): {validate_tfn('123456782')}")
print(f"123456789 (invalid): {validate_tfn('123456789')}")
print(f"123 456 782 (formatted valid): {validate_tfn('123 456 782')}")

# Test ABN
print("\nABN Validation:")
print(f"51824753556 (valid): {validate_abn('51824753556')}")
print(f"51824753557 (invalid): {validate_abn('51824753557')}")
print(f"51 824 753 556 (formatted valid): {validate_abn('51 824 753 556')}")

# Test ACN
print("\nACN Validation:")
print(f"000000019 (valid): {validate_acn('000000019')}")
print(f"000000018 (invalid): {validate_acn('000000018')}")
print(f"000 000 019 (formatted valid): {validate_acn('000 000 019')}")

# Test Medicare
print("\nMedicare Validation:")
print(f"26880012391 (valid): {validate_medicare('26880012391')}")
print(f"26880012392 (invalid): {validate_medicare('26880012392')}")
print(f"2688 00123 9 1 (formatted valid): {validate_medicare('2688 00123 9 1')}")

# Test BSB
print("\nBSB Validation:")
print(f"032000 (valid): {validate_bsb('032000')}")
print(f"032-000 (formatted valid): {validate_bsb('032-000')}")
print(f"03200 (invalid length): {validate_bsb('03200')}")

# Test CRN
print("\nCentrelink CRN Validation:")
print(f"123456789A (valid): {validate_centrelink_crn('123456789A')}")
print(f"12345678A (invalid length): {validate_centrelink_crn('12345678A')}")
print(f"123456789a (lowercase valid): {validate_centrelink_crn('123456789a')}")

print("\n" + "=" * 50)
print("All tests completed!")
