#!/usr/bin/env python3
"""
ZeroPhix Redaction Strategies Examples
======================================

Comprehensive examples of all redaction strategies supported by ZeroPhix.
Shows how to use each strategy and when to choose which one.

Run: python examples/redaction_strategies_examples.py
"""

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig
from zerophix.redaction.strategies import (
    MaskingStrategy,
    HashStrategy,
    EncryptionStrategy,
    SyntheticDataStrategy,
    FormatPreservingStrategy,
    DifferentialPrivacyStrategy,
    KAnonymityStrategy,
    ReplaceStrategy,
    BracketsStrategy,
    AustralianPhoneStrategy
)


def print_section(title: str):
    """Helper to print section headers"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_subsection(title: str):
    """Helper to print subsection headers"""
    print(f"\n{'-'*70}")
    print(f"  {title}")
    print(f"{'-'*70}")


def example_1_replace_strategy():
    """Example 1: Replace strategy - Simple replacement with entity labels"""
    print_section("1. REPLACE STRATEGY - Entity Type Labels")
    
    print("""
    USE CASE: Maximum privacy with clear labeling
    - Compliance documentation
    - Security audit reports  
    - When you need to know what was redacted
    - Complete removal of sensitive data
    """)
    
    text = "Contact John Doe at john.doe@company.com or call 555-123-4567. SSN: 123-45-6789"
    
    config = RedactionConfig(
        country="US",
        masking_style="replace",  # <ENTITY_TYPE> format
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print(f"Entities: {len(result['spans'])} sensitive items found")


def example_2_mask_strategy():
    """Example 2: Mask strategy - Partial masking with asterisks"""
    print_section("2. MASK STRATEGY - Partial Masking")
    
    print("""
    USE CASE: Balance privacy and data utility
    - Show first/last characters for verification
    - Customer service (verify caller identity)
    - Testing environments
    - Pattern recognition while protecting full data
    """)
    
    text = "Card: 4532-1234-5678-9010, SSN: 123-45-6789, Phone: (555) 123-4567"
    
    # Mask everything
    config1 = RedactionConfig(
        country="US",
        masking_style="mask",
        detectors=["regex"]
    )
    pipeline1 = RedactionPipeline(config1)
    result1 = pipeline1.redact(text)
    
    print(f"Original: {text}")
    print(f"Full Mask: {result1['text']}")
    
    # Note: Partial masking (show first/last N chars) requires custom strategy
    print("\nNote: For partial masking (show last 4 digits), use custom MaskingStrategy")


def example_3_hash_strategy():
    """Example 3: Hash strategy - Consistent deterministic hashing"""
    print_section("3. HASH STRATEGY - Deterministic Hashing")
    
    print("""
    USE CASE: Record linking and de-duplication
    - Same value always produces same hash
    - Join redacted datasets
    - Track entities across documents
    - Irreversible but consistent
    """)
    
    text = "Patient: John Doe, MRN: 12345, SSN: 123-45-6789"
    
    config = RedactionConfig(
        country="US",
        masking_style="hash",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    
    # First redaction
    result1 = pipeline.redact(text)
    print(f"Original:     {text}")
    print(f"First Hash:   {result1['text']}")
    
    # Second redaction - should produce same hash
    result2 = pipeline.redact(text)
    print(f"Second Hash:  {result2['text']}")
    print(f"Consistent:   {result1['text'] == result2['text']}")


def example_4_encrypt_strategy():
    """Example 4: Encrypt strategy - Reversible encryption"""
    print_section("4. ENCRYPT STRATEGY - Reversible Encryption")
    
    print("""
    USE CASE: Secure storage with ability to decrypt
    - Data warehouse with controlled decryption
    - Compliance requirements for reversibility
    - Authorized personnel can decrypt
    - Secure key management required
    """)
    
    try:
        from cryptography.fernet import Fernet
        
        text = "Account: 9876543210, SSN: 123-45-6789, Email: john@company.com"
        
        config = RedactionConfig(
            country="US",
            masking_style="encrypt",
            detectors=["regex"]
        )
        
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        print(f"Original:  {text}")
        print(f"Encrypted: {result['text']}")
        print("\nNote: Encrypted data can be decrypted with proper encryption key")
        print("Note: Requires secure key management infrastructure")
        
    except ImportError:
        print("ERROR: Encryption requires cryptography library:")
        print("   pip install cryptography")


def example_5_synthetic_strategy():
    """Example 5: Synthetic strategy - Realistic fake data"""
    print_section("5. SYNTHETIC STRATEGY - Realistic Fake Data")
    
    print("""
    USE CASE: Testing and data sharing
    - Generate realistic test datasets
    - Share data with external parties
    - Demos and presentations
    - Maintains realistic format and structure
    """)
    
    text = "Employee: John Doe, Email: john.doe@company.com, Phone: 555-123-4567, SSN: 123-45-6789"
    
    config = RedactionConfig(
        country="US",
        masking_style="synthetic",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original:  {text}")
    print(f"Synthetic: {result['text']}")
    print("\nNote: Each run generates different but realistic synthetic data")
    print("Note: Maintains format: emails look like emails, phones like phones")


def example_6_brackets_strategy():
    """Example 6: Brackets strategy - [REDACTED] format"""
    print_section("6. BRACKETS STRATEGY - [REDACTED] Format")
    
    print("""
    USE CASE: Document redaction and printouts
    - Legal documents
    - Freedom of Information Act (FOIA) requests
    - Public document releases
    - Traditional redaction appearance
    """)
    
    text = "Witness John Doe testified about incident on 2024-01-15 at 555-123-4567"
    
    config = RedactionConfig(
        country="US",
        masking_style="brackets",  # or "redact" - same thing
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")


def example_7_preserve_format_strategy():
    """Example 7: Format-preserving strategy - Maintain structure"""
    print_section("7. PRESERVE FORMAT STRATEGY - Maintain Structure")
    
    print("""
    USE CASE: Schema compatibility and testing
    - Database migrations requiring same format
    - APIs expecting specific formats
    - Testing with realistic-looking data
    - Preserves character types (digit→digit, letter→letter)
    """)
    
    text = "License: ABC-123-XYZ, Code: K8d2L9P3, Phone: 555-1234"
    
    config = RedactionConfig(
        country="US",
        masking_style="preserve_format",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Preserved: {result['text']}")
    print("\nNote: Structure maintained: ABC-123 -> XYZ-789 (format preserved)")


def example_8_australian_phone_strategy():
    """Example 8: Australian phone strategy - Keep area code"""
    print_section("8. AUSTRALIAN PHONE STRATEGY - Preserve Area Code")
    
    print("""
    USE CASE: Australian context preservation
    - Keep geographic/mobile context (04XX, 02, 03, etc.)
    - Useful for service area analysis
    - Balance privacy with regional data utility
    """)
    
    text = "Mobile: 0412-345-678, Sydney: (02) 9876-5432, Melbourne: 03-8765-4321"
    
    config = RedactionConfig(
        country="AU",
        masking_style="au_phone",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print("\nNote: Area codes preserved: 04XX-XXX-XXX, (02) XXXX-XXXX")


def example_9_differential_privacy_strategy():
    """Example 9: Differential privacy - Statistical noise"""
    print_section("9. DIFFERENTIAL PRIVACY - Statistical Noise")
    
    print("""
    USE CASE: Privacy-preserving analytics
    - Research datasets
    - Statistical analysis
    - Aggregate queries
    - Protects individual records while allowing analytics
    """)
    
    # Note: Differential privacy typically applies to numerical data
    text = "Age: 42, Income: $75000, Zip: 90210"
    
    config = RedactionConfig(
        country="US",
        masking_style="differential_privacy",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"With DP:  {result['text']}")
    print("\nNote: Adds calibrated noise to numerical values")
    print("Note: Privacy parameter epsilon controls privacy/utility trade-off")


def example_10_k_anonymity_strategy():
    """Example 10: K-anonymity - Generalization"""
    print_section("10. K-ANONYMITY STRATEGY - Generalization")
    
    print("""
    USE CASE: Privacy-preserving data publishing
    - Public datasets
    - Research data sharing
    - Ensures each record matches k-1 other records
    - Generalizes quasi-identifiers
    """)
    
    text = "Age: 42, Zip: 90210, Gender: M"
    
    config = RedactionConfig(
        country="US",
        masking_style="k_anonymity",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original:    {text}")
    print(f"K-Anonymous: {result['text']}")
    print("\nNote: Generalizes: Age 42 -> Age 40-50, Zip 90210 -> Zip 902**")


def example_11_strategy_comparison():
    """Example 11: Compare all strategies on same text"""
    print_section("11. STRATEGY COMPARISON - Same Text, Different Strategies")
    
    text = "John Doe, SSN: 123-45-6789, Email: john@company.com"
    
    strategies = [
        ("replace", "Entity labels"),
        ("mask", "Full masking"),
        ("hash", "Deterministic hash"),
        ("brackets", "[REDACTED] format"),
        ("synthetic", "Fake but realistic"),
    ]
    
    print(f"Original Text: {text}\n")
    
    for strategy, description in strategies:
        try:
            config = RedactionConfig(
                country="US",
                masking_style=strategy,
                detectors=["regex"]
            )
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            print(f"{strategy:15} ({description:20}): {result['text']}")
            
        except Exception as e:
            print(f"{strategy:15} - Error: {e}")


def example_12_strategy_by_entity_type():
    """Example 12: Different strategies for different entity types"""
    print_section("12. MIXED STRATEGIES - Different Types Use Different Strategies")
    
    print("""
    ADVANCED: Use different strategies per entity type
    - SSN: full replacement (most sensitive)
    - Email: preserve format (less sensitive)
    - Phone: partial masking (moderate sensitivity)
    - Name: synthetic (for realism in testing)
    """)
    
    print("Note: This requires custom configuration per entity type")
    print("See configs/company/acme.yml for policy-based examples")
    
    # Example from policy file
    print("""
Example YAML configuration:
    
actions:
  PERSON_NAME: 'synthetic'
  SSN: 'replace'
  EMAIL: 'preserve_format'
  PHONE: 'mask'
  CREDIT_CARD: 'mask'
  BANK_ACCOUNT: 'encrypt'
    """)


def example_13_encryption_with_key_management():
    """Example 13: Encryption with proper key management"""
    print_section("13. ENCRYPTION WITH KEY MANAGEMENT")
    
    print("""
    PRODUCTION ENCRYPTION: Proper key management required
    - Store keys in secure vault (AWS KMS, Azure Key Vault, HashiCorp Vault)
    - Rotate keys regularly (90-day rotation)
    - Separate encryption keys from encrypted data
    - Implement key versioning
    - Audit key access
    """)
    
    try:
        from zerophix.security.encryption import KeyManager, EncryptionManager
        
        print("\nSUCCESS: EncryptionManager and KeyManager available")
        print("Supports: AES-128, master key encryption, key rotation")
        
        # Example key management
        print("""
Example usage:

from zerophix.security.encryption import KeyManager, EncryptionManager

# Initialize key manager
key_mgr = KeyManager(key_store_path="./keys")

# Generate encryption key
key_info = key_mgr.generate_data_encryption_key(purpose="pii_redaction")

# Use for encryption
enc_mgr = EncryptionManager(key_id=key_info['key_id'])
encrypted = enc_mgr.encrypt_text("123-45-6789")
decrypted = enc_mgr.decrypt_text(encrypted)
        """)
        
    except ImportError:
        print("ERROR: Full encryption features require cryptography library:")
        print("   pip install cryptography")


def main():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║          ZeroPhix Redaction Strategies - Complete Guide              ║
║                                                                      ║
║  This example demonstrates all 10+ redaction strategies and when    ║
║  to use each one. Choose the right strategy for your use case!      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_1_replace_strategy()
        example_2_mask_strategy()
        example_3_hash_strategy()
        example_4_encrypt_strategy()
        example_5_synthetic_strategy()
        example_6_brackets_strategy()
        example_7_preserve_format_strategy()
        example_8_australian_phone_strategy()
        example_9_differential_privacy_strategy()
        example_10_k_anonymity_strategy()
        example_11_strategy_comparison()
        example_12_strategy_by_entity_type()
        example_13_encryption_with_key_management()
        
        print_section("SUMMARY - Choosing the Right Strategy")
        
        print("""
Quick Reference Guide:

┌─────────────────────┬──────────────────────────────────────────┐
│ Strategy            │ Best For                                 │
├─────────────────────┼──────────────────────────────────────────┤
│ replace             │ Maximum privacy, compliance docs         │
│ mask                │ Partial visibility, customer service     │
│ hash                │ Record linking, de-duplication           │
│ encrypt             │ Reversible redaction, controlled access  │
│ synthetic           │ Testing, demos, external data sharing    │
│ brackets            │ Legal docs, traditional redaction look   │
│ preserve_format     │ Schema compatibility, format validation  │
│ au_phone            │ Australian context with area codes       │
│ differential_privacy│ Research, statistical analysis           │
│ k_anonymity         │ Public datasets, privacy-preserving DB   │
└─────────────────────┴──────────────────────────────────────────┘

Performance Considerations:
  Fast:     replace, brackets, mask (regex only)
  Moderate: hash, preserve_format, synthetic
  Slower:   encrypt (requires crypto), differential_privacy

Security Considerations:
  Irreversible: replace, mask, hash, brackets, synthetic
  Reversible:   encrypt (requires key management)
  
Choose based on your privacy requirements, data utility needs, and 
performance constraints.
        """)
        
    except Exception as e:
        print(f"\nERROR: Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
