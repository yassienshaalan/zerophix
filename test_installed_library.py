#!/usr/bin/env python3
"""
Test script to verify ZeroPhix detects Australian entities when installed as library
This replicates the user's issue where entities aren't being detected
"""

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig
from zerophix.detectors.au_validators import (
    validate_tfn,
    validate_abn,
    validate_acn,
    validate_medicare
)

def test_basic_tfn_abn():
    """Test basic TFN and ABN detection"""
    print("="*70)
    print("TEST 1: Basic TFN and ABN Detection")
    print("="*70)
    
    text = "Employee Records:\n- John Smith: TFN 123 456 782, ABN 53 004 085 616\n- Jane Doe: TFN 987 654 321, ACN 123 456 789"
    
    # Test validators work
    print("\nValidators:")
    print(f"  TFN 123 456 782 valid: {validate_tfn('123 456 782')}")
    print(f"  ABN 53 004 085 616 valid: {validate_abn('53 004 085 616')}")
    
    # Test pipeline
    print("\nPipeline Test:")
    config = RedactionConfig(
        country="AU",
        detectors=["regex"]
    )
    
    print(f"Config country: {config.country}")
    print(f"Config detectors: {config.detectors}")
    print(f"Config company: {config.company}")
    print(f"Config custom_patterns: {config.custom_patterns}")
    
    pipeline = RedactionPipeline(config)
    print(f"Pipeline components: {[c.name for c in pipeline.components]}")
    
    result = pipeline.redact(text)
    
    print(f"\nOriginal text: {text[:60]}...")
    print(f"Redacted text: {result['text'][:60]}...")
    print(f"Entities found: {len(result.get('spans', []))}")
    
    if result.get('spans'):
        for span in result['spans'][:5]:
            print(f"  - {span}")
    else:
        print("  ⚠️  NO ENTITIES FOUND!")
        
    return len(result.get('spans', [])) > 0

def test_medicare():
    """Test Medicare detection"""
    print("\n" + "="*70)
    print("TEST 2: Medicare Detection")
    print("="*70)
    
    text = "Medicare: 2234 5678 9 1, IHI: 8003 6012 3456 7890"
    
    config = RedactionConfig(
        country="AU",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print(f"Entities found: {len(result.get('spans', []))}")
    
    if result.get('spans'):
        for span in result['spans']:
            print(f"  - {span}")
    else:
        print("  ⚠️  NO ENTITIES FOUND!")
        
    return len(result.get('spans', [])) > 0

def test_addresses():
    """Test address and postcode detection"""
    print("\n" + "="*70)
    print("TEST 3: Address and Postcode Detection")
    print("="*70)
    
    text = "123 George St, Sydney NSW 2000\n45 Collins St, Melbourne VIC 3000"
    
    config = RedactionConfig(
        country="AU",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text[:50]}...")
    print(f"Redacted: {result['text'][:50]}...")
    print(f"Entities found: {len(result.get('spans', []))}")
    
    if result.get('spans'):
        for span in result['spans'][:5]:
            print(f"  - {span}")
    else:
        print("  ⚠️  NO ENTITIES FOUND!")
        
    return len(result.get('spans', [])) > 0

def test_phones():
    """Test phone number detection"""
    print("\n" + "="*70)
    print("TEST 4: Phone Number Detection")
    print("="*70)
    
    text = "Mobile: 0412 345 678\nLandline: (02) 9876 5432\nToll-free: 1800 123 456"
    
    config = RedactionConfig(
        country="AU",
        detectors=["regex"]
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print(f"Entities found: {len(result.get('spans', []))}")
    
    if result.get('spans'):
        for span in result['spans']:
            print(f"  - {span}")
    else:
        print("  ⚠️  NO ENTITIES FOUND!")
        
    return len(result.get('spans', [])) > 0

if __name__ == "__main__":
    print("\nTesting ZeroPhix Australian Entity Detection\n")
    
    tests = [
        ("Basic TFN/ABN", test_basic_tfn_abn),
        ("Medicare", test_medicare),
        ("Addresses", test_addresses),
        ("Phones", test_phones),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed - check output above")
        
    exit(0 if all_passed else 1)
