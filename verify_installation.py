#!/usr/bin/env python3
"""
Verification test for installed ZeroPhix library
Tests that entities are detected after wheel installation
"""
import sys
from pathlib import Path

def test_policies_available():
    """Verify policy files are accessible"""
    from zerophix.policies.loader import load_policy
    
    au_policy = load_policy("AU", None)
    patterns = au_policy.get('regex_patterns', {})
    
    assert len(patterns) > 0, "No regex patterns loaded for AU"
    assert 'TFN' in patterns, "TFN pattern not found"
    assert 'ABN' in patterns, "ABN pattern not found"
    
    print(f"✓ Policies loaded: {len(patterns)} patterns found")
    return True

def test_detection_works():
    """Verify entity detection works"""
    from zerophix.config import RedactionConfig
    from zerophix.pipelines.redaction import RedactionPipeline
    
    text = "John Smith, TFN: 123 456 782, Email: john@example.com"
    config = RedactionConfig(country="AU", detectors=["regex"])
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    spans = result.get('spans', [])
    assert len(spans) > 0, f"No entities detected in: {text}"
    
    # Check if TFN was detected
    entities = [s['label'] for s in spans]
    assert 'TFN' in entities, f"TFN not detected. Found: {entities}"
    
    print(f"✓ Detection works: Found {len(spans)} entities")
    print(f"  - Entities: {sorted(set(entities))}")
    return True

def test_australian_entities():
    """Test Australian specific entities"""
    from zerophix.config import RedactionConfig
    from zerophix.pipelines.redaction import RedactionPipeline
    
    test_cases = [
        ("TFN: 123 456 782", "TFN"),
        ("ABN: 53 004 085 616", "ABN"),
        ("Phone: 0412 345 678", "PHONE_AU"),
        ("Address: 123 George St, Sydney NSW 2000", "ADDRESS_STREET"),
    ]
    
    config = RedactionConfig(country="AU", detectors=["regex"])
    pipeline = RedactionPipeline(config)
    
    all_passed = True
    for text, expected_entity in test_cases:
        result = pipeline.redact(text)
        entities = [s['label'] for s in result.get('spans', [])]
        
        if expected_entity in entities:
            print(f"✓ {expected_entity}: detected")
        else:
            print(f"✗ {expected_entity}: NOT detected (found {entities})")
            all_passed = False
    
    return all_passed

def main():
    print("="*70)
    print("ZeroPhix Installed Library Verification")
    print("="*70)
    
    tests = [
        ("Policies Available", test_policies_available),
        ("Detection Works", test_detection_works),
        ("Australian Entities", test_australian_entities),
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\nTest: {name}")
        print("-" * 70)
        try:
            results[name] = test_func()
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            results[name] = False
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✓ All verification tests PASSED!")
        print("  ZeroPhix is correctly installed and working.")
    else:
        print("✗ Some tests FAILED!")
        print("  See above for details.")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
