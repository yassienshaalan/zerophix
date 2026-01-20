"""
Test adaptive ensemble functionality
Run: python -m pytest tests/test_adaptive_ensemble.py -v
"""

import pytest
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.pipelines.adaptive_ensemble import (
    PerformanceTracker,
    LabelNormalizer,
    AdaptiveConsensusModel,
    ConfigurationOptimizer
)
from zerophix.detectors.base import Span


def test_performance_tracker():
    """Test detector performance tracking"""
    tracker = PerformanceTracker()
    
    # Add detector
    tracker.add_detector("test_detector")
    
    # Simulate predictions
    predictions = [
        Span(0, 10, "PERSON", 0.9, "test_detector"),
        Span(15, 25, "LOCATION", 0.8, "test_detector"),
        Span(30, 40, "ORG", 0.7, "test_detector"),
    ]
    
    ground_truth = [
        (0, 10, "PERSON"),  # TP
        (15, 25, "LOCATION"),  # TP
        (50, 60, "DATE"),  # FN (missed)
    ]
    # (30, 40, "ORG") is FP (false alarm)
    
    tracker.update_metrics("test_detector", predictions, ground_truth)
    
    # Check metrics
    metrics = tracker.metrics["test_detector"]
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == 2/3  # 2 TP / (2 TP + 1 FP)
    assert metrics.recall == 2/3  # 2 TP / (2 TP + 1 FN)
    
    # Check weight calculation
    weight = tracker.get_detector_weight("test_detector", method="f1_squared")
    assert 0.1 <= weight <= 1.0


def test_label_normalizer():
    """Test label normalization"""
    normalizer = LabelNormalizer()
    
    # Test standard mappings
    assert normalizer.normalize("PERSON") == "PERSON_NAME"
    assert normalizer.normalize("PER") == "PERSON_NAME"
    assert normalizer.normalize("NAME") == "PERSON_NAME"
    
    assert normalizer.normalize("DRUG") == "MEDICATION"
    assert normalizer.normalize("MEDICINE") == "MEDICATION"
    
    assert normalizer.normalize("DISEASE") == "MEDICAL_CONDITION"
    assert normalizer.normalize("DIAGNOSIS") == "MEDICAL_CONDITION"
    
    # Test case insensitivity
    assert normalizer.normalize("person") == "PERSON_NAME"
    assert normalizer.normalize("Person") == "PERSON_NAME"
    
    # Test unknown labels pass through
    assert normalizer.normalize("UNKNOWN_LABEL") == "UNKNOWN_LABEL"


def test_label_normalizer_on_spans():
    """Test normalizing spans"""
    normalizer = LabelNormalizer()
    
    spans = [
        Span(0, 10, "PERSON", 0.9, "gliner"),
        Span(15, 25, "NAME", 0.8, "regex"),
        Span(30, 40, "DRUG", 0.7, "openmed"),
    ]
    
    normalized = normalizer.normalize_spans(spans)
    
    assert normalized[0].label == "PERSON_NAME"
    assert normalized[1].label == "PERSON_NAME"
    assert normalized[2].label == "MEDICATION"
    
    # Original spans unchanged
    assert spans[0].label == "PERSON"


def test_adaptive_consensus():
    """Test adaptive consensus model"""
    config = RedactionConfig(
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        detector_weights={
            "gliner": 1.5,
            "regex": 1.0,
        }
    )
    
    tracker = PerformanceTracker()
    tracker.add_detector("gliner")
    tracker.add_detector("regex")
    
    # Simulate gliner being better
    tracker.metrics["gliner"].true_positives = 80
    tracker.metrics["gliner"].false_positives = 20
    tracker.metrics["gliner"].false_negatives = 10
    
    tracker.metrics["regex"].true_positives = 40
    tracker.metrics["regex"].false_positives = 60
    tracker.metrics["regex"].false_negatives = 50
    
    consensus = AdaptiveConsensusModel(config, tracker=tracker)
    
    # Check weights updated from tracker
    assert consensus.weights["gliner"] > consensus.weights["regex"]


def test_adaptive_consensus_label_normalization():
    """Test that label normalization happens before voting"""
    config = RedactionConfig(
        enable_label_normalization=True,
        detector_weights={
            "gliner": 1.0,
            "regex": 1.0,
        }
    )
    
    consensus = AdaptiveConsensusModel(config)
    
    # Two detectors find same entity with different labels
    spans = [
        Span(0, 10, "PERSON", 0.8, "gliner"),
        Span(0, 10, "NAME", 0.7, "regex"),
    ]
    
    resolved = consensus.resolve(spans, text="John Smith here")
    
    # Should resolve to one span with normalized label
    assert len(resolved) == 1
    assert resolved[0].label == "PERSON_NAME"


def test_calibration_basic():
    """Test basic calibration workflow"""
    config = RedactionConfig(
        country="AU",
        use_gliner=False,  # Skip to make test faster
        use_spacy=True,
        enable_adaptive_weights=True,
        enable_label_normalization=True,
        track_detector_performance=True,
    )
    
    pipeline = RedactionPipeline(config)
    
    # Minimal validation data
    texts = [
        "John Smith works at Acme Corp.",
        "Call 555-1234 for information.",
    ]
    
    ground_truth = [
        [(0, 10, "PERSON_NAME"), (20, 29, "ORGANIZATION")],
        [(5, 13, "PHONE_NUMBER")],
    ]
    
    # Run calibration
    results = pipeline.calibrate(texts, ground_truth)
    
    # Check results structure
    assert "detector_weights" in results
    assert "label_thresholds" in results
    assert "performance_summary" in results
    
    # Check that weights were calculated
    assert len(results["detector_weights"]) > 0
    
    # Check performance summary has metrics
    for detector, metrics in results["performance_summary"].items():
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics


def test_calibration_saves_and_loads():
    """Test saving and loading calibration results"""
    import tempfile
    import os
    
    config = RedactionConfig(
        country="AU",
        use_gliner=False,
        use_spacy=True,
        enable_adaptive_weights=True,
        track_detector_performance=True,
    )
    
    pipeline = RedactionPipeline(config)
    
    texts = ["John Smith at john@example.com"]
    ground_truth = [[(0, 10, "PERSON_NAME"), (14, 32, "EMAIL")]]
    
    # Save calibration
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        results = pipeline.calibrate(texts, ground_truth, save_path=temp_path)
        
        # Check file exists
        assert os.path.exists(temp_path)
        
        # Load in new tracker
        new_tracker = PerformanceTracker()
        loaded_weights = new_tracker.load_metrics(temp_path)
        
        # Check weights match
        assert loaded_weights == results["detector_weights"]
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_configuration_optimizer():
    """Test configuration optimizer"""
    config = RedactionConfig(
        country="AU",
        use_spacy=True,
        use_gliner=False,
    )
    
    pipeline = RedactionPipeline(config)
    optimizer = ConfigurationOptimizer(pipeline)
    
    texts = ["Jane Doe has diabetes"]
    ground_truth = [[(0, 8, "PERSON_NAME"), (13, 21, "DISEASE")]]
    
    results = optimizer.calibrate(texts, ground_truth)
    
    assert "detector_weights" in results
    assert "label_thresholds" in results
    assert "performance_summary" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
