#!/usr/bin/env python3
"""
Simple test to verify detection works
"""
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

# Test 1: US with default detectors
print("Test 1: US Default")
config = RedactionConfig(country="US")
pipeline = RedactionPipeline(config)
text = "John Doe, SSN: 123-45-6789, Email: john@example.com"
result = pipeline.redact(text)
print(f"  Input:  {text}")
print(f"  Output: {result['text']}")
print(f"  Found:  {len(result['spans'])} entities\n")

# Test 2: Explicit regex detector
print("Test 2: Explicit Regex")
config2 = RedactionConfig(country="US", detectors=["regex"])
pipeline2 = RedactionPipeline(config2)
result2 = pipeline2.redact(text)
print(f"  Input:  {text}")
print(f"  Output: {result2['text']}")
print(f"  Found:  {len(result2['spans'])} entities\n")

# Test 3: Debug - check what detectors are loaded
print("Test 3: Debug Detectors")
print(f"  Config detectors: {config2.detectors}")
print(f"  Pipeline components: {[c.__class__.__name__ for c in pipeline2.components]}")
print(f"  Spans detail: {result2['spans']}")
