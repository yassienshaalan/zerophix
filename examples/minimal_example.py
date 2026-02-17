#!/usr/bin/env python3
"""
ZeroPhix Minimal Working Example

This is the simplest possible example to get started.

INSTALLATION:
  pip install zerophix

Run with:
  python examples/minimal_example.py
"""

import sys
import os

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

try:
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig
except ImportError as e:
    print(f"Error: ZeroPhix not installed")
    print(f"Run: pip install zerophix")
    sys.exit(1)

# ============================================================================
# Example 1: Simplest Working Example - US Data
# ============================================================================
print("=" * 60)
print("SIMPLE EXAMPLE: Basic PII Redaction")
print("=" * 60)

# Text with PII
text = "John Doe, SSN: 123-45-6789, Email: john@example.com"
print(f"\nOriginal:  {text}")

# Create pipeline (simplest configuration)
config = RedactionConfig(country="US")
pipeline = RedactionPipeline(config)

# Redact
result = pipeline.redact(text)

print(f"Redacted:  {result['text']}")
print(f"Entities Found: {len(result['spans'])}")

if result['spans']:
    print("\nDetected entities:")
    for span in result['spans']:
        print(f"  - {span['label']}: {text[span['start']:span['end']]}")
else:
    print("\nWarning: No entities detected!")
    print("Debugging info:")
    print(f"  Pipeline detectors: {[c.__class__.__name__ for c in pipeline.components]}")
    print(f"  Config detectors list: {config.detectors}")

# ============================================================================
# Example 2: Australian Data
# ============================================================================
print("\n" + "=" * 60)
print("EXAMPLE 2: Australian TFN Detection")
print("=" * 60)

au_text = "Jane Doe, TFN: 123 456 789"
print(f"\nOriginal:  {au_text}")

config_au = RedactionConfig(country="AU")
pipeline_au = RedactionPipeline(config_au)
result_au = pipeline_au.redact(au_text)

print(f"Redacted:  {result_au['text']}")
print(f"Entities Found: {len(result_au['spans'])}")

# ============================================================================
# Example 3: Explicit Hash Strategy
# ============================================================================
print("\n" + "=" * 60)
print("EXAMPLE 3: Hash Redaction Strategy")
print("=" * 60)

text3 = "Contact john.doe@example.com or call (555) 123-4567"
print(f"\nOriginal:  {text3}")

config3 = RedactionConfig(country="US", masking_style="hash")
pipeline3 = RedactionPipeline(config3)
result3 = pipeline3.redact(text3)

print(f"Redacted:  {result3['text']}")
print(f"Entities Found: {len(result3['spans'])}")

print("\n" + "=" * 60)
print("Examples complete!")
print("=" * 60)
