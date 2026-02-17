#!/usr/bin/env python3
"""
GLiNER Zero-Shot Detector Examples
===================================

GLiNER (Generalist Named Entity Recognition) enables zero-shot entity 
detection without any fine-tuning. Just name the entities you want to 
find - no training data required!

INSTALLATION REQUIRED:
  pip install "zerophix[gliner]"
  # This also installs torch, transformers, and gliner

FEATURES USED:
  ✓ GLiNER zero-shot detection
  ✓ Custom entity type detection
  ✓ Multi-label entity detection

Features:
- Zero-shot: No training data needed
- Flexible: Detect any entity type by naming it
- Accurate: 90%+ F1 score on standard benchmarks
- Fast: ~100ms per document

"""

# Check if GLiNER is available
try:
    from zerophix.detectors.gliner_detector import GLiNERDetector
except ImportError:
    print("ERROR: GLiNER not installed")
    print("Please run: pip install 'zerophix[gliner]'")
    print("This example requires transformers, torch, and gliner>=0.1.0")
    exit(1)
"""
Installation:
    pip install gliner

Usage:
    python examples/gliner_examples.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zerophi.detectors.gliner_detector import GLiNERDetector


def example_basic_usage():
    """Example 1: Basic PII detection"""
    print("=" * 70)
    print("EXAMPLE 1: Basic PII Detection")
    print("=" * 70)
    
    detector = GLiNERDetector()
    
    text = """
    Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted 
    on 2024-11-20. Contact: john.smith@email.com, (555) 123-4567.
    Medical Record: MR-2024-001234. Diagnosed with hypertension.
    """
    
    spans = detector.detect(text)
    
    print(f"\nText: {text}\n")
    print(f"Detected {len(spans)} entities:\n")
    
    for span in spans:
        entity_text = text[span.start:span.end]
        print(f"  [{span.label}] {entity_text} (confidence: {span.score:.2f})")


def example_custom_entities():
    """Example 2: Custom entity types (zero-shot!)"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Entity Types (No Training!)")
    print("=" * 70)
    
    detector = GLiNERDetector()
    
    text = """
    Employee ID: EMP-2024-5678
    Project: PROJECT-ALPHA-99
    API Key: sk_live_abcd1234xyz
    Internal IP: 192.168.1.100
    Budget Code: BDG-2024-Q4-1000
    """
    
    # Define custom entities - NO TRAINING NEEDED!
    custom_entities = [
        "employee id",
        "project code", 
        "api key",
        "ip address",
        "budget code"
    ]
    
    spans = detector.detect(text, entity_types=custom_entities)
    
    print(f"\nText: {text}\n")
    print(f"Custom entities detected:\n")
    
    for span in spans:
        entity_text = text[span.start:span.end]
        print(f"  [{span.label}] {entity_text} (confidence: {span.score:.2f})")


def example_medical_scenario():
    """Example 3: Healthcare-specific detection"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Healthcare Scenario")
    print("=" * 70)
    
    detector = GLiNERDetector()
    
    clinical_note = """
    PATIENT: Emily Johnson
    MRN: MR-2024-9876
    DOB: 08/22/1978
    
    CHIEF COMPLAINT: Chest pain
    
    HISTORY: Patient presents with acute chest pain radiating to left arm.
    Known history of hypertension and type 2 diabetes.
    
    MEDICATIONS:
    - Metformin 1000mg BID
    - Lisinopril 10mg daily
    - Aspirin 81mg daily
    
    VITALS:
    BP: 145/92, HR: 88, Temp: 98.6F, SpO2: 97%
    
    ASSESSMENT: Possible acute coronary syndrome
    
    PLAN: 
    - EKG ordered
    - Troponin levels
    - Cardiology consult (Dr. Sarah Martinez, NPI: 1234567890)
    """
    
    medical_entities = [
        "patient name",
        "medical record number",
        "date of birth",
        "diagnosis",
        "medication",
        "dosage",
        "vital signs",
        "doctor name",
        "npi number",
        "medical condition"
    ]
    
    results = detector.detect_with_context(
        clinical_note, 
        medical_entities,
        context_window=30
    )
    
    print(f"\nClinical Note Analysis:\n")
    print(f"Found {len(results)} PHI elements:\n")
    
    for r in results[:10]:  # Show first 10
        print(f"  [{r['label']}] {r['text']}")
        print(f"  Context: ...{r['context']}...")
        print(f"  Confidence: {r['score']:.2f}\n")


def example_financial_scenario():
    """Example 4: Financial services detection"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Financial Services Scenario")
    print("=" * 70)
    
    detector = GLiNERDetector()
    
    loan_app = """
    LOAN APPLICATION
    
    Applicant: Michael Chen
    SSN: 456-78-9012
    DOB: 05/10/1982
    
    Employment: Senior Engineer at Tech Corp
    Annual Income: $185,000
    
    Account Information:
    - Checking: Account #1234567890 (Bank of America, Routing: 026009593)
    - Credit Card: 4532-1234-5678-9012 (Visa)
    - Credit Score: 780
    
    Property Address: 123 Oak Street, San Francisco, CA 94102
    Loan Amount: $850,000
    """
    
    financial_entities = [
        "person name",
        "social security number",
        "date of birth",
        "annual income",
        "bank account number",
        "routing number",
        "credit card number",
        "credit score",
        "address",
        "loan amount"
    ]
    
    spans = detector.detect(loan_app, entity_types=financial_entities)
    
    print(f"\nLoan Application Analysis:\n")
    print(f"Found {len(spans)} PII/PSI elements:\n")
    
    # Group by type
    by_type = {}
    for span in spans:
        entity_text = loan_app[span.start:span.end]
        if span.label not in by_type:
            by_type[span.label] = []
        by_type[span.label].append(entity_text)
    
    for entity_type, values in sorted(by_type.items()):
        print(f"  {entity_type}:")
        for val in values:
            print(f"    - {val}")


def example_performance_benchmark():
    """Example 5: Performance comparison"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Performance Benchmark")
    print("=" * 70)
    
    import time
    
    detector = GLiNERDetector()
    
    # Sample text
    text = "John Doe's SSN is 123-45-6789, email: john@example.com" * 20
    
    # Benchmark
    iterations = 100
    start = time.time()
    
    for _ in range(iterations):
        detector.detect(text)
    
    duration = time.time() - start
    avg_time = duration / iterations
    
    print(f"\nProcessed {iterations} documents")
    print(f"Total time: {duration:.2f}s")
    print(f"Average per document: {avg_time*1000:.2f}ms")
    print(f"Throughput: {iterations/duration:.1f} docs/second")
    
    print(f"\nScalability estimate:")
    print(f"  - 1,000 documents: ~{(avg_time * 1000)/60:.1f} minutes")
    print(f"  - 10,000 documents: ~{(avg_time * 10000)/3600:.1f} hours")
    print(f"  - 100,000 documents: ~{(avg_time * 100000)/3600:.1f} hours")


def example_integration_with_pipeline():
    """Example 6: Using GLiNER with RedactionPipeline"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Integration with ZeroPhi Pipeline")
    print("=" * 70)
    
    from zerophi.config import RedactionConfig
    from zerophi.pipelines.redaction import RedactionPipeline
    
    # Configure to use GLiNER
    config = RedactionConfig(
        country="AU",
        detectors=["gliner"],  # Use GLiNER detector
        masking_style="hash"
    )
    
    pipeline = RedactionPipeline.from_config(config)
    
    text = """
    Employee: Sarah Johnson
    Employee ID: EMP-2024-1234
    Email: sarah.j@company.com
    Project: ALPHA-SECRET-99
    """
    
    # Redact with GLiNER
    result = pipeline.redact(text)
    
    print(f"\nOriginal:")
    print(text)
    
    print(f"\nRedacted:")
    print(result['text'])
    
    print(f"\nDetected entities:")
    for entity in result['entities']:
        print(f"  - {entity['label']}: {entity['text']}")


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("GLiNER Zero-Shot Detector - Advanced Examples")
    print("=" * 70)
    print("\nGLiNER enables zero-shot entity detection without fine-tuning!")
    print("Just name the entities you want to find - no training needed.\n")
    
    try:
        example_basic_usage()
        example_custom_entities()
        example_medical_scenario()
        example_financial_scenario()
        example_performance_benchmark()
        example_integration_with_pipeline()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  1. Zero-shot: No training data required")
        print("  2. Flexible: Add any entity type instantly")
        print("  3. Accurate: 90%+ F1 score on standard benchmarks")
        print("  4. Fast: ~100ms per document")
        print("  5. Easy: 3 lines of code to get started")
        print("\nNext Steps:")
        print("  - Try with your own data")
        print("  - Define custom entity types for your domain")
        print("  - Integrate into your production pipeline")
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nTo run these examples, install GLiNER:")
        print("  pip install gliner")
        print("\nAnd make sure transformers and torch are installed:")
        print("  pip install transformers torch")
