"""Detection Methods Comparison - With Per-Method Redacted Text"""
print("ZEROPHIX: DETECTION METHODS COMPARISON")

text = """Patient John Doe (born 1985-03-15) was treated for diabetes.
Contact: john.doe@hospital.com, emergency: (555) 123-4567.
Insurance: INS-123456, SSN: 123-45-6789."""

print(f"\n ORIGINAL TEXT:")
print(f"   {text}\n")

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

configs = [
    ("Regex Only", {"country": "US", "use_bert": False, "use_gliner": False}),
    ("Regex + BERT", {"country": "US", "use_bert": True, "use_gliner": False}),
    ("Regex + GLiNER", {"country": "US", "use_bert": False, "use_gliner": True}),
    ("Ensemble (BERT+GLiNER)", {"country": "US", "use_bert": True, "use_gliner": True, "enable_ensemble_voting": True}),
]

results_summary = []

for name, flags in configs:
    try:
        config = RedactionConfig(**flags)
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        spans = result.get('spans', [])
        redacted_text = result.get('text', text)
        
        print("─" * 70)
        print(f" {name}")
        print("─" * 70)
        print(f"   Entities Found: {len(spans)}")
        print(f"\n    REDACTED TEXT:")
        print(f"   {redacted_text}")
        
        if spans:
            print(f"\n    DETECTED ENTITIES:")
            for span in spans:
                label = span.get('label', 'UNKNOWN')
                start = span.get('start')
                end = span.get('end')
                if start is not None and end is not None:
                    value = text[start:end]
                else:
                    value = span.get('value', '???')
                print(f"       {label:<25} → {value}")
        else:
            print(f"\n     No entities detected")
        
        results_summary.append((name, len(spans)))
        print()
        
    except (RuntimeError, ImportError) as e:
        print(f"     {str(e)} (skipped)\n")
        results_summary.append((name, 0))


print(" SUMMARY")
print("=" * 70)
print(f"{'Method':<25} {'PII Found':<12} {'Advantage'}")
print("-" * 70)
for name, count in results_summary:
    if "Regex Only" in name:
        advantage = "Fast baseline, catches structured patterns"
    elif "BERT" in name and "+" not in name:
        advantage = "Adds PERSON_NAME detection (context-aware)"
    elif "GLiNER" in name and "+" not in name:
        advantage = "Detects medical/contextual entities"
    else:
        advantage = "Best coverage via ensemble voting"
    print(f"{name:<25} {count:<12} {advantage}")
