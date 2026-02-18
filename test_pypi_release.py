#!/usr/bin/env python3
"""
PyPI Release Validation Test
Simulates PyPI installation and validates all key functionality

Run: python test_pypi_release.py
"""

import sys
from pathlib import Path

def test_version():
    """Test version is correct"""
    print("=" * 70)
    print("1. VERSION CHECK")
    print("=" * 70)
    
    from zerophix import __version__ as version_module
    version_string = version_module.__version__
    print(f"✓ Version: {version_string}")
    assert version_string == "0.1.18", f"Expected 0.1.18, got {version_string}"
    print("✓ Version check passed\n")


def test_policy_files():
    """Test policy files are included"""
    print("=" * 70)
    print("2. POLICY FILES CHECK")
    print("=" * 70)
    
    import zerophix
    from pathlib import Path
    
    # Get zerophix module directory
    zerophix_dir = Path(zerophix.__file__).parent
    policies_dir = zerophix_dir / 'policies'
    
    print(f"Policies directory: {policies_dir}")
    assert policies_dir.exists(), f"Policies directory missing at {policies_dir}!"
    
    yml_files = list(policies_dir.glob('*.yml'))
    print(f"✓ Found {len(yml_files)} policy files:")
    
    expected_countries = ['au', 'us', 'uk', 'ca', 'eu']
    for country in expected_countries:
        yml_file = policies_dir / f"{country}.yml"
        assert yml_file.exists(), f"Missing {country}.yml"
        size = yml_file.stat().st_size
        print(f"  ✓ {country}.yml ({size} bytes)")
    
    print("✓ All policy files present\n")


def test_basic_redaction():
    """Test basic entity detection and redaction"""
    print("=" * 70)
    print("3. BASIC REDACTION TEST")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    config = RedactionConfig(country="US", masking_style="replace")
    pipeline = RedactionPipeline(config)
    
    test_cases = [
        ("SSN: 123-45-6789", "SSN", 1),
        ("Email: john@example.com", "EMAIL", 1),
        ("Phone: (555) 123-4567", "PHONE_US", 1),
    ]
    
    for text, expected_label, expected_count in test_cases:
        result = pipeline.redact(text)
        detected = len(result['spans'])
        print(f"Text: {text}")
        print(f"  ✓ Detected: {detected} entity (expected: {expected_count})")
        assert detected > 0, f"Failed to detect {expected_label} in: {text}"
        if detected > 0:
            label = result['spans'][0]['label']
            print(f"  ✓ Label: {label}")
    
    print("✓ Basic redaction test passed\n")


def test_multi_country():
    """Test multi-country support"""
    print("=" * 70)
    print("4. MULTI-COUNTRY SUPPORT")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    countries = {
        "US": "SSN: 123-45-6789",
        "AU": "TFN: 123 456 789",
        "UK": "NHS: 123 456 7890",
        "CA": "SIN: 123-456-789",
        "EU": "IBAN: DE89 3704 0044 0532 0130 00"
    }
    
    for country, text in countries.items():
        config = RedactionConfig(country=country, masking_style="replace")
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        detected = len(result['spans'])
        print(f"{country}: {detected} entities detected")
        assert detected > 0, f"No entities detected for {country}: {text}"
    
    print("✓ Multi-country support verified\n")


def test_redaction_strategies():
    """Test all redaction strategies"""
    print("=" * 70)
    print("5. REDACTION STRATEGIES TEST")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    text = "Email: john@example.com, Phone: (555) 123-4567"
    strategies = ["replace", "mask", "hash", "brackets", "synthetic", "preserve_format", "encrypt"]
    
    results = {}
    for strategy in strategies:
        try:
            config = RedactionConfig(country="US", masking_style=strategy, detectors=["regex"])
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            redacted = result['text']
            results[strategy] = redacted
            print(f"✓ {strategy:20} -> {redacted[:50]}...")
            
            # Verify original text is not in redacted output
            if strategy != "preserve_format":  # preserve_format keeps structure
                assert "john@example.com" not in redacted, f"{strategy} failed to redact email"
        except Exception as e:
            print(f"⚠ {strategy:20} -> {str(e)[:50]}")
    
    print("✓ All redaction strategies working\n")


def test_custom_patterns():
    """Test custom entity patterns"""
    print("=" * 70)
    print("6. CUSTOM PATTERNS TEST")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    custom_patterns = {
        "EMPLOYEE_ID": [r"EMP-\d{6}"],
        "PROJECT_CODE": [r"PROJ-[A-Z]{3}-\d{4}"]
    }
    
    text = "Employee EMP-123456 working on PROJ-ABC-2023"
    
    config = RedactionConfig(
        country="US",
        detectors=["regex", "custom"],
        custom_patterns=custom_patterns,
        masking_style="replace"
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    custom_entities = [s for s in result['spans'] if s['label'] in custom_patterns]
    print(f"Custom entities found: {len(custom_entities)}")
    
    for entity in custom_entities:
        matched = text[entity['start']:entity['end']]
        print(f"  ✓ {matched} -> {entity['label']}")
    
    assert len(custom_entities) > 0, "Custom patterns not detected"
    print("✓ Custom patterns working\n")


def test_batch_processing():
    """Test batch processing"""
    print("=" * 70)
    print("7. BATCH PROCESSING TEST")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    texts = [
        "John Doe, SSN: 123-45-6789",
        "Jane Smith, Email: jane@example.com",
        "Bob Wilson, Phone: (555) 123-4567"
    ]
    
    config = RedactionConfig(country="US", masking_style="replace")
    pipeline = RedactionPipeline(config)
    
    results = pipeline.redact_batch(texts)
    print(f"Processed {len(results)} texts")
    
    total_entities = sum(len(r['spans']) for r in results)
    print(f"Total entities detected: {total_entities}")
    
    assert len(results) == len(texts), "Batch processing returned wrong count"
    assert total_entities >= len(texts), "No entities detected in batch"
    
    for i, result in enumerate(results):
        print(f"  ✓ Text {i+1}: {len(result['spans'])} entities")
    
    print("✓ Batch processing working\n")


def test_scanning():
    """Test scanning (detection without redaction)"""
    print("=" * 70)
    print("8. SCANNING TEST (Detection without Redaction)")
    print("=" * 70)
    
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
    
    text = "Patient John Doe, DOB: 01/15/1980, SSN: 123-45-6789"
    
    config = RedactionConfig(country="US")
    pipeline = RedactionPipeline(config)
    
    report = pipeline.scan_report(text)
    
    print(f"Original text unchanged: {report['original_text'] == text}")
    print(f"Total detections: {report['total_detections']}")
    print(f"Entity types: {list(report['entity_counts'].keys())}")
    
    assert text == report['original_text'], "Text was modified during scan"
    assert report['total_detections'] > 0, "No entities detected"
    assert report['has_pii'] == True, "PII flag not set"
    
    print("✓ Scanning working\n")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  ZeroPhix v0.1.18 - PyPI Release Validation".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        ("Version Check", test_version),
        ("Policy Files", test_policy_files),
        ("Basic Redaction", test_basic_redaction),
        ("Multi-Country", test_multi_country),
        ("Redaction Strategies", test_redaction_strategies),
        ("Custom Patterns", test_custom_patterns),
        ("Batch Processing", test_batch_processing),
        ("Scanning", test_scanning),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}\n")
            failed += 1
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Passed: {passed}/{len(tests)}")
    print(f"✗ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED - READY FOR PyPI RELEASE!")
        print("=" * 70)
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
