#!/usr/bin/env python3
"""
ZeroPhi Quick Start Examples
============================

Simple, practical examples showing the most common ZeroPhi use cases.
Perfect for getting started quickly with real-world scenarios.

INSTALLATION:
  Minimal: pip install zerophix
  Full:    pip install "zerophix[all]"

FEATURES USED:
  ✓ Regex detection (always available)
  ✓ Custom patterns (always available)
  ✓ Batch processing (always available)

NOTE: This example works with minimal install. Run with:
  python examples/quick_start_examples.py
"""

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig


def example_1_basic_text_redaction():
    """Most basic example - redact text with default settings"""
    print("=" * 50)
    print("1. BASIC TEXT REDACTION")
    print("=" * 50)
    
    # Simple text with PII
    text = "Hi, I'm John Doe. My SSN is 123-45-6789 and email is john.doe@email.com"
    
    # Create basic US configuration
    config = RedactionConfig(country="US", masking_style="replace")
    pipeline = RedactionPipeline(config)
    
    # Redact the text
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print(f"Found {len(result['spans'])} sensitive entities")
    print()


def example_2_multiple_countries():
    """Show how to handle different countries"""
    print("=" * 50) 
    print("2. MULTI-COUNTRY SUPPORT")
    print("=" * 50)
    
    # Different country examples
    examples = {
        "US": "John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
        "AU": "Jane Doe, TFN: 123 456 789, Medicare: 2234 5678 9 1", 
        "EU": "Hans Mueller, IBAN: DE89 3704 0044 0532 0130 00",
        "UK": "Sarah Wilson, NHS: 123 456 7890, NI: AB 12 34 56 C",
        "CA": "Mike Brown, SIN: 123-456-789, postal: K1A 0A9"
    }
    
    for country, text in examples.items():
        config = RedactionConfig(country=country, masking_style="replace")
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        print(f"{country}: {text}")
        print(f"     -> {result['text']}")
        print()


def example_3_advanced_detection():
    """Use multiple detection engines for better accuracy"""
    print("=" * 50)
    print("3. ADVANCED ML DETECTION")
    print("=" * 50)
    
    # Complex text with various entities
    text = """
    Patient John Doe (born 1985-03-15) was treated for diabetes.
    Contact: john.doe@hospital.com, emergency: (555) 123-4567.
    Insurance: INS-123456, SSN: 123-45-6789.
    Prescribed Metformin 500mg twice daily.
    """
    
    # Try different detection combinations
    configs = [
        ("Fast (Regex only)", ["regex"]),
        ("Balanced (Regex + spaCy)", ["regex", "spacy"]),
        ("Best (All engines)", ["regex", "spacy", "bert"])
    ]
    
    for name, detectors in configs:
        try:
            config = RedactionConfig(
                country="US",
                detectors=detectors,
                masking_style="replace",
                confidence_threshold=0.8
            )
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            print(f"{name}:")
            print(f"  Found {len(result['spans'])} entities")
            # print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Result: {result['text'][:80]}...")
            print()
            
        except Exception as e:
            print(f"{name}: {e} (requires model installation)")
            print()


def example_4_redaction_strategies():
    """Different ways to redact sensitive data"""
    print("=" * 50)
    print("4. REDACTION STRATEGIES") 
    print("=" * 50)
    
    text = "Contact John Doe at john.doe@email.com or call (555) 123-4567"
    
    strategies = [
        ("replace", "Replace with asterisks"),
        ("mask", "Partial masking"), 
        ("synthetic", "Realistic fake data"),
        ("hash", "Consistent hashing")
    ]
    
    for strategy, description in strategies:
        try:
            config = RedactionConfig(
                country="US",
                masking_style=strategy,
                mask_percentage=0.6 if strategy == "mask" else None
            )
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            print(f"{description}:")
            print(f"  Original: {text}")
            print(f"  Redacted: {result['text']}")
            print()
            
        except Exception as e:
            print(f"{description}: {e}")
            print()


def example_5_file_processing():
    """Process files instead of just text"""
    print("=" * 50)
    print("5. FILE PROCESSING")
    print("=" * 50)
    
    # Create a sample file
    import tempfile
    import os
    
    # Create sample text file
    sample_content = """
    CONFIDENTIAL DOCUMENT
    
    Employee: John Doe
    SSN: 123-45-6789
    Email: john.doe@company.com
    Phone: (555) 123-4567
    
    This document contains sensitive information.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_content)
        temp_file = f.name
    
    try:
        # Read file
        with open(temp_file, 'r') as f:
            content = f.read()
        
        # Redact content
        config = RedactionConfig(country="US", masking_style="replace")
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(content)
        
        # Write redacted version
        redacted_file = temp_file.replace('.txt', '_redacted.txt')
        with open(redacted_file, 'w') as f:
            f.write(result['text'])
        
        print(f"Original file: {temp_file}")
        print(f"Redacted file: {redacted_file}")
        print(f"Found {len(result['spans'])} sensitive entities")
        
        print("\nRedacted content:")
        print(result['text'])
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(redacted_file):
            os.remove(redacted_file)


def example_6_custom_patterns():
    """Add custom patterns for your specific needs"""
    print("=" * 50)
    print("6. CUSTOM ENTITY PATTERNS")
    print("=" * 50)
    
    # Text with custom entities
    text = """
    Employee EMP-123456 is working on project PROJ-ABC-2023.
    Internal server: 192.168.1.100, access code: AC-789123.
    Salary information: $75,000 annually.
    """
    
    # Define custom patterns as dictionary
    # This is passed to the CustomEntityDetector via config
    custom_patterns = {
        "EMPLOYEE_ID": [r"EMP-\d{6}"],
        "PROJECT_CODE": [r"PROJ-[A-Z]{3}-\d{4}"],
        "INTERNAL_IP": [r"192\.168\.\d{1,3}\.\d{1,3}"],
        "ACCESS_CODE": [r"AC-\d{6}"]
    }
    
    # Pass custom patterns to config
    config = RedactionConfig(
        country="US",
        detectors=["regex", "custom"],
        custom_patterns=custom_patterns,
        masking_style="replace"
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print("\nCustom entities found:")
    for entity in result['spans']:
        if entity['label'] in ['EMPLOYEE_ID', 'PROJECT_CODE', 'INTERNAL_IP', 'ACCESS_CODE']:
            entity_text = text[entity['start']:entity['end']]
            print(f"  - {entity_text} ({entity['label']})")


def example_7_batch_processing():
    """Process multiple texts efficiently"""
    print("=" * 50)
    print("7. BATCH PROCESSING") 
    print("=" * 50)
    
    # Multiple texts to process
    texts = [
        "John Doe, SSN: 123-45-6789, email: john@email.com",
        "Jane Smith, phone: (555) 987-6543, DOB: 1990-05-15", 
        "Bob Johnson, credit card: 4532-1234-5678-9012",
        "Alice Brown, driver license: D12345678, SSN: 555-44-3333"
    ]
    
    print(f"Processing {len(texts)} texts in batch...")
    
    # Process all texts
    config = RedactionConfig(country="US", masking_style="replace")
    pipeline = RedactionPipeline(config)
    
    results = []
    total_entities = 0
    
    for i, text in enumerate(texts, 1):
        result = pipeline.redact(text)
        results.append(result)
        total_entities += len(result['spans'])
        
        print(f"Text {i}: {result['text']}")
    
    print(f"\nBatch complete: {total_entities} total entities redacted")


def example_8_configuration_profiles():
    """Pre-configured settings for common use cases"""
    print("=" * 50)
    print("8. CONFIGURATION PROFILES")
    print("=" * 50)
    
    text = "Patient John Doe, DOB: 1985-03-15, SSN: 123-45-6789, diagnosed with diabetes"
    
    # Different configuration profiles
    profiles = {
        "Fast": RedactionConfig(
            country="US",
            detectors=["regex"],
            masking_style="replace"
        ),
        "Balanced": RedactionConfig(
            country="US", 
            detectors=["regex", "spacy"],
            # confidence_threshold=0.8  # Not a direct field, but in thresholds dict
        ),
        "Healthcare": RedactionConfig(
            country="US",
            detectors=["regex", "openmed"],
            masking_style="synthetic",
            # compliance_standards=["HIPAA"] # Not in config
        ),
        "High Security": RedactionConfig(
            country="US",
            detectors=["regex", "bert"],
            masking_style="encrypt",
            encryption_key=b"some-key", # encryption_enabled is not a field, encryption_key is
            audit_logging=True
        )
    }
    
    for name, config in profiles.items():
        try:
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            print(f"{name} Profile:")
            print(f"  Result: {result['text']}")
            print(f"  Entities: {len(result['spans'])}")
            # print(f"  Confidence: {result['confidence']:.2f}")
            print()
            
        except Exception as e:
            print(f"{name} Profile: {e} (requires additional setup)")
            print()


def main():
    """Run all quick start examples"""
    print("ZeroPhi Quick Start Examples")
    print("============================")
    print("These examples show common ZeroPhi usage patterns")
    print("Start here to learn the basics!\n")
    
    # Run examples in order
    example_1_basic_text_redaction()
    example_2_multiple_countries()
    example_3_advanced_detection()
    example_4_redaction_strategies()
    example_5_file_processing()
    example_6_custom_patterns()
    example_7_batch_processing()
    example_8_configuration_profiles()
    
    print("=" * 50)
    print("QUICK START COMPLETE!")
    print("=" * 50)
    print("You've seen the core ZeroPhi functionality.")
    print("\nNext steps:")
    print("1. Try modifying these examples with your data")
    print("2. Check out comprehensive_usage_examples.py for advanced features")
    print("3. Read the documentation for production deployment")
    print("4. Configure security and compliance for your needs")


if __name__ == "__main__":
    main()