"""
Calculate valid TFN manually
"""

# Try different base numbers
bases = ["12345678", "87654321", "11111111", "32456789"]

weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]

for base in bases:
    print(f"\nTrying base: {base}")
    for last_digit in range(10):
        tfn = base + str(last_digit)
        total = sum(int(digit) * weight for digit, weight in zip(tfn, weights))
        remainder = total % 11
        print(f"  {tfn}: sum={total}, mod 11={remainder}, valid={remainder == 0}")
        if remainder == 0:
            print(f"  ✓ VALID TFN FOUND: {tfn}")
            break
