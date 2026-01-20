"""
Adaptive Ensemble Usage Examples
Demonstrates how to use the new adaptive calibration system to optimize ZeroPhix
"""

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

# =============================================================================
# Example 1: Basic Adaptive Ensemble with Label Normalization
# =============================================================================

def example_adaptive_ensemble():
    """
    Enable adaptive ensemble with label normalization
    This helps cross-detector consensus work properly
    """
    config = RedactionConfig(
        country="AU",
        use_gliner=True,
        use_openmed=True,
        use_spacy=True,
        
        # NEW: Enable adaptive features
        enable_adaptive_weights=True,  # Use performance-based weights
        enable_label_normalization=True,  # Normalize labels before voting
        adaptive_weight_method="f1_squared",  # Emphasize high performers
    )
    
    pipeline = RedactionPipeline(config)
    
    # Use normally - no changes to API
    result = pipeline.redact("John Smith has diabetes. Call 555-1234.")
    print(result['text'])


# =============================================================================
# Example 2: Calibrate on Validation Data (RECOMMENDED)
# =============================================================================

def example_calibration():
    """
    SOLVE THE MAIN PROBLEM: Calibrate once, use optimal config forever
    No more trial-and-error!
    """
    
    # 1. Prepare validation data (20-50 labeled samples)
    validation_texts = [
        "Patient John Smith, age 45, diagnosed with diabetes mellitus type 2.",
        "Contact Dr. Sarah Johnson at 555-123-4567 for consultation.",
        "Medicare number: 2123 45670 1. Date of birth: 15/03/1978.",
        "Prescribed metformin 500mg twice daily for blood glucose control.",
        # ... add more samples from your australian_pii_2500 dataset
    ]
    
    # Ground truth: [(start, end, label), ...]
    validation_ground_truth = [
        [(8, 18, "PERSON_NAME"), (33, 62, "DISEASE")],  # John Smith, diabetes mellitus type 2
        [(8, 21, "PERSON_NAME"), (25, 37, "PHONE_NUMBER")],  # Dr. Sarah Johnson, phone
        [(17, 30, "MEDICARE_NUMBER"), (47, 57, "DATE")],  # Medicare, DOB
        [(11, 21, "MEDICATION"), (22, 27, "DOSAGE")],  # metformin, 500mg
        # ... corresponding labels
    ]
    
    # 2. Create pipeline
    config = RedactionConfig(
        country="AU",
        use_gliner=True,
        use_openmed=True,
        use_spacy=True,
        
        # Enable adaptive features
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        track_detector_performance=True,  # Track metrics during calibration
    )
    
    pipeline = RedactionPipeline(config)
    
    # 3. Calibrate - this runs the validation set and learns optimal weights
    print("Calibrating pipeline on validation data...")
    results = pipeline.calibrate(
        validation_texts,
        validation_ground_truth,
        save_path="calibration_results.json"  # Save for reuse
    )
    
    # 4. Review results
    print("\n=== Calibration Results ===")
    print(f"Optimized Detector Weights: {results['detector_weights']}")
    print(f"Suggested Label Thresholds: {results['label_thresholds']}")
    
    print("\n=== Detector Performance ===")
    for detector, metrics in results['performance_summary'].items():
        print(f"{detector}: P={metrics['precision']:.2%}, R={metrics['recall']:.2%}, F1={metrics['f1']:.2%}")
    
    # 5. Pipeline is now optimized! Use normally
    test_text = "Jane Doe, Medicare 2234 56781 2, has hypertension."
    result = pipeline.redact(test_text)
    print(f"\nRedacted: {result['text']}")
    
    return pipeline, results


# =============================================================================
# Example 3: Load Pre-Calibrated Weights (Production Use)
# =============================================================================

def example_load_calibration():
    """
    In production: Load pre-calibrated weights from file
    No need to recalibrate every time!
    """
    config = RedactionConfig(
        country="AU",
        use_gliner=True,
        use_openmed=True,
        
        # Load saved calibration
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        calibration_file="calibration_results.json"  # From calibration step
    )
    
    pipeline = RedactionPipeline(config)
    # Ready to use with optimal weights!
    
    return pipeline


# =============================================================================
# Example 4: Integrate with Existing Benchmark
# =============================================================================

def example_benchmark_integration():
    """
    How to integrate calibration into your existing benchmark notebook
    """
    import json
    
    # Load your test_samples
    test_samples = []  # Your australian_pii_2500 data
    
    # Take a small calibration set (20-50 samples)
    calibration_samples = test_samples[:20]
    
    # Prepare ground truth (you already have 'entities' field)
    validation_texts = [s['text'] for s in calibration_samples]
    validation_ground_truth = []
    
    for sample in calibration_samples:
        # Convert your gold labels to (start, end, label) format
        ground_truth = []
        for entity in sample.get('entities', []):
            # Assuming entity format: {'text': '...', 'label': '...', 'start': ..., 'end': ...}
            ground_truth.append((entity['start'], entity['end'], entity['label']))
        validation_ground_truth.append(ground_truth)
    
    # Create and calibrate pipeline
    config = RedactionConfig(
        country="AU",
        use_gliner=True,
        use_openmed=True,
        use_spacy=True,
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        track_detector_performance=True,
        
        # Your existing GLiNER config
        gliner_labels=[
            "person", "organization", "location",
            "drug", "disease", "procedure",
            "phone_number", "email", "date",
            # ... all your labels
        ],
    )
    
    pipeline = RedactionPipeline(config)
    
    # CALIBRATE once
    print("Running calibration on 20 samples...")
    results = pipeline.calibrate(
        validation_texts,
        validation_ground_truth,
        save_path="australian_medical_calibration.json"
    )
    
    # Now benchmark on full dataset with optimized config
    print("\nRunning full benchmark with optimized weights...")
    for sample in test_samples:
        spans = pipeline.scan(sample['text'])
        # ... your existing evaluation logic
    
    return results


# =============================================================================
# Example 5: Runtime Performance Tracking
# =============================================================================

def example_runtime_tracking():
    """
    Track detector performance during actual usage
    Useful for online learning / drift detection
    """
    config = RedactionConfig(
        country="AU",
        use_gliner=True,
        enable_adaptive_weights=True,
        track_detector_performance=True,  # Track in real-time
    )
    
    pipeline = RedactionPipeline(config)
    
    # Use pipeline normally
    texts = ["...", "...", "..."]
    for text in texts:
        result = pipeline.redact(text)
        # ... use result
    
    # Periodically check performance
    summary = pipeline.get_performance_summary()
    print(f"Current detector performance: {summary}")
    
    # If performance degrades, recalibrate
    if summary['gliner']['f1'] < 0.3:
        print("Performance degraded, recalibrating...")
        # ... recalibrate logic


# =============================================================================
# Example 6: Complete Workflow for Your Use Case
# =============================================================================

def complete_workflow_for_australian_medical():
    """
    Complete recommended workflow for Australian medical data
    """
    
    # STEP 1: Load and prepare data
    print("Step 1: Loading data...")
    # Your existing data loading code
    import json
    with open("/path/to/australian_pii_2500.jsonl") as f:
        all_samples = [json.loads(line) for line in f]
    
    # Split: 20 for calibration, rest for testing
    calibration_samples = all_samples[:20]
    test_samples = all_samples[20:70]  # 50 for testing
    
    # STEP 2: Prepare calibration data
    print("Step 2: Preparing calibration data...")
    cal_texts = []
    cal_gt = []
    
    for sample in calibration_samples:
        cal_texts.append(sample['text'])
        
        # Convert entities to (start, end, label) format
        entities = []
        for ent in sample.get('entities', []):
            entities.append((ent['start'], ent['end'], ent['label']))
        cal_gt.append(entities)
    
    # STEP 3: Create pipeline with good defaults
    print("Step 3: Creating pipeline...")
    config = RedactionConfig(
        country="AU",
        
        # Enable all relevant detectors
        use_gliner=True,
        use_openmed=True,
        use_spacy=True,
        
        # Adaptive features
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        track_detector_performance=True,
        
        # GLiNER labels (your existing list)
        gliner_labels=[
            "person", "organization", "location", "facility",
            "drug", "medication", "disease", "medical_condition",
            "procedure", "treatment", "symptom",
            "phone_number", "email", "date", "identifier",
            "medicare_number", "abn", "tfn", "acn",
        ],
        
        # Context features
        enable_context_propagation=True,
        context_propagation_threshold=0.90,
    )
    
    pipeline = RedactionPipeline(config)
    
    # STEP 4: CALIBRATE (the magic happens here!)
    print("Step 4: Calibrating on 20 samples...")
    calibration_results = pipeline.calibrate(
        cal_texts,
        cal_gt,
        save_path="australian_medical_calibration.json"
    )
    
    print("\n=== Calibration Complete ===")
    print("Optimized weights:")
    for detector, weight in calibration_results['detector_weights'].items():
        metrics = calibration_results['performance_summary'][detector]
        print(f"  {detector}: weight={weight:.3f} (P={metrics['precision']:.2%}, F1={metrics['f1']:.2%})")
    
    # STEP 5: Benchmark with optimized config
    print("\nStep 5: Running benchmark on 50 samples...")
    from collections import defaultdict
    
    results = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    
    for sample in test_samples:
        # Get predictions
        detected_spans = pipeline.scan(sample['text'])
        
        # Convert to comparable format
        predictions = {(s.start, s.end, s.label) for s in detected_spans}
        ground_truth = {(e['start'], e['end'], e['label']) for e in sample.get('entities', [])}
        
        # Calculate metrics per label
        for label in set([e[2] for e in predictions | ground_truth]):
            pred_label = {e for e in predictions if e[2] == label}
            gt_label = {e for e in ground_truth if e[2] == label}
            
            results[label]["tp"] += len(pred_label & gt_label)
            results[label]["fp"] += len(pred_label - gt_label)
            results[label]["fn"] += len(gt_label - pred_label)
    
    # STEP 6: Report results
    print("\n=== Benchmark Results ===")
    overall_tp = sum(r["tp"] for r in results.values())
    overall_fp = sum(r["fp"] for r in results.values())
    overall_fn = sum(r["fn"] for r in results.values())
    
    overall_p = overall_tp / (overall_tp + overall_fp) if overall_tp + overall_fp > 0 else 0
    overall_r = overall_tp / (overall_tp + overall_fn) if overall_tp + overall_fn > 0 else 0
    overall_f1 = 2 * overall_p * overall_r / (overall_p + overall_r) if overall_p + overall_r > 0 else 0
    
    print(f"Overall: P={overall_p:.1%}, R={overall_r:.1%}, F1={overall_f1:.1%}")
    print("\nPer-label:")
    for label, metrics in sorted(results.items()):
        tp, fp, fn = metrics["tp"], metrics["fp"], metrics["fn"]
        p = tp / (tp + fp) if tp + fp > 0 else 0
        r = tp / (tp + fn) if tp + fn > 0 else 0
        f1 = 2 * p * r / (p + r) if p + r > 0 else 0
        print(f"  {label}: P={p:.1%}, R={r:.1%}, F1={f1:.1%} (TP={tp}, FP={fp}, FN={fn})")
    
    return pipeline, calibration_results


if __name__ == "__main__":
    # Run the complete workflow
    print("=" * 80)
    print("ZeroPhix Adaptive Ensemble - Complete Workflow Example")
    print("=" * 80)
    
    # For quick testing, run basic example
    print("\n1. Basic adaptive ensemble:")
    example_adaptive_ensemble()
    
    print("\n2. Calibration example:")
    # example_calibration()  # Uncomment with real data
    
    print("\n3. Complete workflow:")
    # complete_workflow_for_australian_medical()  # Uncomment with real data
    
    print("\n" + "=" * 80)
    print("Key Takeaways:")
    print("- Use calibrate() once on 20-50 samples to learn optimal weights")
    print("- Save results to file and load in production")
    print("- No more manual trial-and-error configuration!")
    print("- Adaptive weights automatically favor high-performing detectors")
    print("- Label normalization ensures cross-detector consensus works")
    print("=" * 80)
