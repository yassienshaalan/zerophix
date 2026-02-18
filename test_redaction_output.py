#!/usr/bin/env python3
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

text = "John Doe, SSN: 123-45-6789, Email: john@example.com"

print("=" * 60)
print("Testing Different Redaction Strategies")
print("=" * 60)
print(f"\nOriginal text: {text}\n")

strategies = ["hash", "replace", "mask", "brackets", "synthetic"]

for strategy in strategies:
    try:
        config = RedactionConfig(country="US", masking_style=strategy)
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        print(f"{strategy.upper():15} -> {result['text']}")
    except Exception as e:
        print(f"{strategy.upper():15} -> ERROR: {e}")

print("\n" + "=" * 60)
