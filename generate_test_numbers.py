"""
Generate valid Australian test numbers
"""

def generate_valid_tfn():
    """Generate a valid TFN"""
    # TFN: 123 456 78X where X is check digit
    base = "12345678"
    weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]
    
    total = sum(int(digit) * weight for digit, weight in zip(base, weights[:8]))
    remainder = total % 11
    check_digit = (11 - remainder) % 11
    
    if check_digit == 10:
        check_digit = 0  # Use 0 for check digit 10
    
    return base + str(check_digit)


def generate_valid_medicare():
    """Generate a valid Medicare number"""
    # Medicare: 2688 00123 X 1 where X is check digit
    base = "26880012"  # First 8 digits
    weights = [1, 3, 7, 9, 1, 3, 7, 9]
    
    total = sum(int(digit) * weight for digit, weight in zip(base, weights))
    check_digit = total % 10
    
    # Return with IRN=1
    return base + str(check_digit) + "11"  # 11 = check digit + IRN


def generate_valid_abn():
    """Generate a valid ABN"""
    # Use known valid: 51 824 753 556
    return "51824753556"


def generate_valid_acn():
    """Generate a valid ACN"""
    # ACN: 000 000 01X where X is check digit
    base = "00000001"  # First 8 digits
    weights = [8, 7, 6, 5, 4, 3, 2, 1]
    
    total = sum(int(digit) * weight for digit, weight in zip(base, weights))
    remainder = total % 10
    check_digit = (10 - remainder) % 10
    
    return base + str(check_digit)


if __name__ == "__main__":
    print("Valid Australian Test Numbers:")
    print(f"TFN: {generate_valid_tfn()}")
    print(f"Medicare: {generate_valid_medicare()}")
    print(f"ABN: {generate_valid_abn()}")
    print(f"ACN: {generate_valid_acn()}")
