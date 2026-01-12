"""
Australian-specific validation functions for checksum verification.
Implements mathematical validation for TFN, ABN, ACN, and Medicare numbers.
"""
from typing import Optional


def validate_tfn(tfn: str) -> bool:
    """
    Validate Tax File Number using modulus 11 algorithm.
    
    TFN format: XXX-XXX-XXX (9 digits)
    Algorithm: Sum of (digit × weight) mod 11 = 0
    Weights: 1, 4, 3, 7, 5, 8, 6, 9, 10
    
    Args:
        tfn: Tax File Number (with or without formatting)
        
    Returns:
        bool: True if valid TFN
    """
    # Remove formatting
    digits = ''.join(c for c in tfn if c.isdigit())
    
    if len(digits) != 9:
        return False
    
    # TFN weights
    weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]
    
    # Calculate weighted sum
    total = sum(int(digit) * weight for digit, weight in zip(digits, weights))
    
    # Valid if divisible by 11
    return total % 11 == 0


def validate_abn(abn: str) -> bool:
    """
    Validate Australian Business Number using modulus 89 algorithm.
    
    ABN format: XX-XXX-XXX-XXX (11 digits)
    Algorithm: 
    1. Subtract 1 from first digit
    2. Multiply each digit by weight (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
    3. Sum mod 89 = 0
    
    Args:
        abn: Australian Business Number (with or without formatting)
        
    Returns:
        bool: True if valid ABN
    """
    # Remove formatting
    digits = ''.join(c for c in abn if c.isdigit())
    
    if len(digits) != 11:
        return False
    
    # ABN weights
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    
    # Subtract 1 from first digit
    first_digit = int(digits[0]) - 1
    remaining_digits = [int(d) for d in digits[1:]]
    
    # Calculate weighted sum
    total = first_digit * weights[0]
    total += sum(digit * weight for digit, weight in zip(remaining_digits, weights[1:]))
    
    # Valid if divisible by 89
    return total % 89 == 0


def validate_acn(acn: str) -> bool:
    """
    Validate Australian Company Number using modulus 10 algorithm.
    
    ACN format: XXX-XXX-XXX (9 digits)
    Algorithm: Similar to Luhn algorithm with specific weights
    Weights: 8, 7, 6, 5, 4, 3, 2, 1
    
    Args:
        acn: Australian Company Number (with or without formatting)
        
    Returns:
        bool: True if valid ACN
    """
    # Remove formatting
    digits = ''.join(c for c in acn if c.isdigit())
    
    if len(digits) != 9:
        return False
    
    # ACN weights (first 8 digits)
    weights = [8, 7, 6, 5, 4, 3, 2, 1]
    
    # Calculate weighted sum (exclude last digit - it's the check digit)
    total = sum(int(digit) * weight for digit, weight in zip(digits[:8], weights))
    
    # Calculate check digit
    remainder = total % 10
    check_digit = (10 - remainder) % 10
    
    # Compare with actual last digit
    return check_digit == int(digits[8])


def validate_medicare(medicare: str) -> bool:
    """
    Validate Medicare card number using modulus 10 algorithm.
    
    Medicare format: XXXX-XXXXX-X-X (11 digits total)
    First 10 digits: card number
    11th digit: check digit
    Algorithm: Luhn-like with specific weights
    
    Args:
        medicare: Medicare number (with or without formatting)
        
    Returns:
        bool: True if valid Medicare number
    """
    # Remove formatting
    digits = ''.join(c for c in medicare if c.isdigit())
    
    if len(digits) != 11:
        return False
    
    # Validate first digit (must be 2-6)
    if not (2 <= int(digits[0]) <= 6):
        return False
    
    # Medicare weights (first 8 digits)
    weights = [1, 3, 7, 9, 1, 3, 7, 9]
    
    # Calculate weighted sum
    total = sum(int(digit) * weight for digit, weight in zip(digits[:8], weights))
    
    # Calculate check digit
    check_digit = total % 10
    
    # Compare with actual 9th digit
    return check_digit == int(digits[8])


def validate_bsb(bsb: str) -> bool:
    """
    Validate Bank State Branch number (basic format check).
    
    BSB format: XXX-XXX (6 digits)
    No checksum algorithm, just format validation.
    
    Args:
        bsb: Bank State Branch number (with or without formatting)
        
    Returns:
        bool: True if valid format
    """
    # Remove formatting
    digits = ''.join(c for c in bsb if c.isdigit())
    
    # Must be exactly 6 digits
    return len(digits) == 6


def validate_centrelink_crn(crn: str) -> bool:
    """
    Validate Centrelink Customer Reference Number (basic format check).
    
    CRN format: XXXXXXXXXA (9 digits + 1 letter)
    
    Args:
        crn: Centrelink CRN
        
    Returns:
        bool: True if valid format
    """
    # Remove whitespace
    crn = crn.strip().upper()
    
    # Must be 10 characters: 9 digits + 1 letter
    if len(crn) != 10:
        return False
    
    # First 9 must be digits
    if not crn[:9].isdigit():
        return False
    
    # Last character must be a letter
    return crn[9].isalpha()


def get_au_validator(entity_type: str):
    """
    Get the appropriate validator function for an Australian entity type.
    
    Args:
        entity_type: The entity type label (e.g., 'TFN', 'ABN', 'MEDICARE')
        
    Returns:
        Optional[callable]: Validator function or None if no validator exists
    """
    validators = {
        'TFN': validate_tfn,
        'ABN': validate_abn,
        'ACN': validate_acn,
        'MEDICARE': validate_medicare,
        'BSB': validate_bsb,
        'CENTRELINK_CRN': validate_centrelink_crn,
    }
    
    return validators.get(entity_type)


def validate_span_checksum(text: str, start: int, end: int, entity_type: str) -> bool:
    """
    Validate a detected span using checksum validation if available.
    
    Args:
        text: The full text
        start: Start position of the span
        end: End position of the span
        entity_type: The entity type label
        
    Returns:
        bool: True if valid or no validator exists (pass-through)
    """
    validator = get_au_validator(entity_type)
    
    if validator is None:
        # No validator for this type, assume valid
        return True
    
    # Extract the span text
    span_text = text[start:end]
    
    # Validate
    return validator(span_text)
