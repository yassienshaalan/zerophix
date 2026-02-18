#!/usr/bin/env python3
"""
ZeroPhi Simple Redaction Example
================================

This is the simplest, working example to get started with ZeroPhi.
Perfect for first-time users - shows exactly what the output looks like.

INSTALLATION:
  pip install zerophix

Run this with:
  python examples/simple_redaction_example.py
"""

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig


def main():
    """Simple redaction example"""
    print("=" * 70)
    print("ZeroPhi Simple Redaction Example")
    print("=" * 70)
    print()
    
    # Sample text with sensitive information
    text = "John Doe, SSN: 123-45-6789, Email: john@example.com, Phone: (555) 123-4567"
    
    print("ORIGINAL TEXT:")
    print(f"  {text}")
    print()
    
    # Create configuration for US country
    # Note: Using regex-only detectors for speed and minimal dependencies.
    # Names (John Doe) require NER models - see quick_start_examples.py for that.
    config = RedactionConfig(
        country="US",
        detectors=["regex"],      # Regex-only: ultra-fast, structured data only
        masking_style="replace"   # Shows clear [ENTITY] labels
    )
    
    # Create pipeline
    pipeline = RedactionPipeline(config)
    
    # Redact the text
    result = pipeline.redact(text)
    
    print("REDACTED TEXT:")
    print(f"  {result['text']}")
    print()
    
    print("ENTITIES DETECTED:")
    for entity in result['spans']:
        original_text = text[entity['start']:entity['end']]
        print(f"  - {entity['label']:20} : '{original_text}'")
    print()
    
    print("=" * 70)
    print(f"Status: Successfully detected and redacted {len(result['spans'])} entities")
    print("=" * 70)


if __name__ == "__main__":
    main()
