"""
Verify generated Australian test numbers
"""
from src.zerophix.detectors.au_validators import (
    validate_tfn,
    validate_abn,
    validate_acn,
    validate_medicare,
)

print("Verifying Generated Test Numbers")
print("=" * 50)

# Generated numbers
tfn = "123456789"
medicare = "26880012311"
abn = "51824753556"
acn = "000000019"

print(f"\nTFN {tfn}: {validate_tfn(tfn)}")
print(f"Medicare {medicare}: {validate_medicare(medicare)}")
print(f"ABN {abn}: {validate_abn(abn)}")
print(f"ACN {acn}: {validate_acn(acn)}")

# Test invalid versions
print("\nTesting invalid versions:")
print(f"TFN 123456788 (wrong check): {validate_tfn('123456788')}")
print(f"Medicare 26880012312 (wrong check): {validate_medicare('26880012312')}")
print(f"ABN 51824753557 (wrong check): {validate_abn('51824753557')}")
print(f"ACN 000000018 (wrong check): {validate_acn('000000018')}")
