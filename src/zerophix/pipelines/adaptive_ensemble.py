"""
Adaptive Ensemble System for ZeroPhix
Learns optimal detector weights and thresholds from validation data
Reduces manual trial-and-error configuration
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path
import numpy as np

from ..detectors.base import Span
from ..config import RedactionConfig


@dataclass
class DetectorMetrics:
    """Track performance metrics for a single detector"""
    detector_name: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_predictions: int = 0
    
    # Label-specific metrics
    label_metrics: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0}))
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)
    
    def get_label_f1(self, label: str) -> float:
        """Get F1 score for a specific label"""
        m = self.label_metrics.get(label, {})
        tp = m.get("tp", 0)
        fp = m.get("fp", 0)
        fn = m.get("fn", 0)
        
        if tp + fp == 0:
            p = 0.0
        else:
            p = tp / (tp + fp)
        
        if tp + fn == 0:
            r = 0.0
        else:
            r = tp / (tp + fn)
        
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)


class PerformanceTracker:
    """
    Tracks detector performance in real-time or during calibration
    Enables adaptive weight adjustment based on actual accuracy
    """
    
    def __init__(self):
        self.metrics: Dict[str, DetectorMetrics] = {}
        self.calibration_samples = []
        
    def add_detector(self, name: str):
        """Register a detector for tracking"""
        if name not in self.metrics:
            self.metrics[name] = DetectorMetrics(detector_name=name)
    
    def update_metrics(self, 
                      detector_name: str,
                      predictions: List[Span],
                      ground_truth: List[Tuple[int, int, str]]):
        """
        Update metrics for a detector based on predictions vs ground truth
        
        Args:
            detector_name: Name of the detector
            predictions: List of predicted Spans
            ground_truth: List of (start, end, label) tuples
        """
        if detector_name not in self.metrics:
            self.add_detector(detector_name)
        
        metrics = self.metrics[detector_name]
        
        # Convert ground truth to set of (start, end, label) for matching
        gt_set = set(ground_truth)
        pred_set = {(s.start, s.end, s.label) for s in predictions}
        
        # Calculate TP, FP, FN
        true_positives = pred_set & gt_set
        false_positives = pred_set - gt_set
        false_negatives = gt_set - pred_set
        
        metrics.true_positives += len(true_positives)
        metrics.false_positives += len(false_positives)
        metrics.false_negatives += len(false_negatives)
        metrics.total_predictions += len(predictions)
        
        # Update label-specific metrics
        for tp in true_positives:
            label = tp[2]
            metrics.label_metrics[label]["tp"] += 1
        
        for fp in false_positives:
            label = fp[2]
            metrics.label_metrics[label]["fp"] += 1
        
        for fn in false_negatives:
            label = fn[2]
            metrics.label_metrics[label]["fn"] += 1
    
    def get_detector_weight(self, detector_name: str, method: str = "f1_squared") -> float:
        """
        Calculate optimal weight for a detector based on its performance
        
        Args:
            detector_name: Name of detector
            method: Weight calculation method
                - "f1_squared": weight = F1^2 (default, emphasizes high performers)
                - "precision": weight = precision (for high-precision needs)
                - "f1_linear": weight = F1 (linear relationship)
                - "harmonic": weight based on harmonic mean of P and R
        
        Returns:
            Suggested weight (0.0 to 1.0+)
        """
        if detector_name not in self.metrics:
            return 1.0  # Default neutral weight
        
        metrics = self.metrics[detector_name]
        
        if method == "f1_squared":
            # Emphasize high performers, penalize poor ones heavily
            return max(0.1, metrics.f1 ** 2)
        
        elif method == "precision":
            # For use cases where false positives are costly
            return max(0.1, metrics.precision)
        
        elif method == "f1_linear":
            return max(0.1, metrics.f1)
        
        elif method == "harmonic":
            # Balanced but more forgiving than squared
            return max(0.1, metrics.f1 ** 1.5)
        
        return 1.0
    
    def get_all_weights(self, method: str = "f1_squared") -> Dict[str, float]:
        """Get adaptive weights for all tracked detectors"""
        return {name: self.get_detector_weight(name, method) 
                for name in self.metrics.keys()}
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get performance summary for all detectors"""
        return {
            name: {
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "total_predictions": metrics.total_predictions,
                "true_positives": metrics.true_positives,
                "false_positives": metrics.false_positives,
                "false_negatives": metrics.false_negatives,
            }
            for name, metrics in self.metrics.items()
        }
    
    def save_metrics(self, filepath: str):
        """Save calibration metrics to file"""
        data = {
            "summary": self.get_summary(),
            "recommended_weights": self.get_all_weights("f1_squared"),
            "label_specific": {
                name: {
                    label: {
                        "f1": metrics.get_label_f1(label),
                        **metrics.label_metrics[label]
                    }
                    for label in metrics.label_metrics.keys()
                }
                for name, metrics in self.metrics.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_metrics(self, filepath: str) -> Dict[str, float]:
        """Load pre-calibrated weights from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get("recommended_weights", {})


class LabelNormalizer:
    """
    Normalizes detector labels BEFORE ensemble voting
    Ensures cross-detector consensus works properly
    """
    
    def __init__(self, label_map: Optional[Dict[str, str]] = None):
        """
        Args:
            label_map: Custom label mapping, or None for default
        """
        self.label_map = label_map or self._default_label_map()
    
    def _default_label_map(self) -> Dict[str, str]:
        """Default label normalization mapping"""
        return {
            # Person names
            'PERSON': 'PERSON_NAME',
            'PER': 'PERSON_NAME',
            'NAME': 'PERSON_NAME',
            'INDIVIDUAL': 'PERSON_NAME',
            
            # Organizations
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'COMPANY': 'ORGANIZATION',
            'BUSINESS': 'ORGANIZATION',
            
            # Locations
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'GPE': 'LOCATION',
            'PLACE': 'LOCATION',
            'ADDRESS': 'LOCATION',
            
            # Medical
            'DRUG': 'MEDICATION',
            'MEDICATION': 'MEDICATION',
            'MEDICINE': 'MEDICATION',
            'PHARMACEUTICAL': 'MEDICATION',
            
            'DISEASE': 'MEDICAL_CONDITION',
            'MEDICAL_CONDITION': 'MEDICAL_CONDITION',
            'DIAGNOSIS': 'MEDICAL_CONDITION',
            'CONDITION': 'MEDICAL_CONDITION',
            'ILLNESS': 'MEDICAL_CONDITION',
            
            # Identifiers
            'ID': 'IDENTIFIER',
            'IDENTIFIER': 'IDENTIFIER',
            'ID_NUMBER': 'IDENTIFIER',
            
            # Dates/Times
            'DATE': 'DATE',
            'TIME': 'TIME',
            'DATETIME': 'DATE',
            
            # Contact
            'EMAIL': 'EMAIL',
            'EMAIL_ADDRESS': 'EMAIL',
            'PHONE': 'PHONE_NUMBER',
            'PHONE_NUMBER': 'PHONE_NUMBER',
            'TEL': 'PHONE_NUMBER',
            'TELEPHONE': 'PHONE_NUMBER',
        }
    
    def normalize(self, label: str) -> str:
        """Normalize a label to standard form"""
        # Try uppercase match first
        upper_label = label.upper()
        if upper_label in self.label_map:
            return self.label_map[upper_label]
        
        # Try exact match
        if label in self.label_map:
            return self.label_map[label]
        
        # Try case-insensitive match
        for k, v in self.label_map.items():
            if k.lower() == label.lower():
                return v
        
        # Return original if no match
        return label
    
    def normalize_spans(self, spans: List[Span]) -> List[Span]:
        """Normalize labels in a list of spans"""
        normalized = []
        for span in spans:
            normalized_span = Span(
                start=span.start,
                end=span.end,
                label=self.normalize(span.label),
                score=span.score,
                source=span.source
            )
            normalized.append(normalized_span)
        return normalized


class AdaptiveConsensusModel:
    """
    Enhanced consensus model with:
    - Adaptive detector weights based on performance
    - Label normalization before voting
    - Performance-aware conflict resolution
    """
    
    def __init__(self, 
                 config: RedactionConfig,
                 tracker: Optional[PerformanceTracker] = None,
                 normalizer: Optional[LabelNormalizer] = None):
        self.config = config
        self.tracker = tracker
        self.normalizer = normalizer or LabelNormalizer()
        
        # Start with config weights, update with tracker if available
        self.weights = config.detector_weights.copy()
        if tracker:
            self.update_weights_from_tracker()
    
    def update_weights_from_tracker(self):
        """Update detector weights based on tracked performance"""
        if not self.tracker:
            return
        
        adaptive_weights = self.tracker.get_all_weights(method="f1_squared")
        
        # Blend config weights with adaptive weights (80% adaptive, 20% config)
        for detector, adaptive_weight in adaptive_weights.items():
            config_weight = self.weights.get(detector, 1.0)
            self.weights[detector] = 0.8 * adaptive_weight + 0.2 * config_weight
    
    def resolve(self, spans: List[Span], text: str = None) -> List[Span]:
        """
        Resolve conflicts with adaptive weights and label normalization
        """
        if not spans:
            return []
        
        # CRITICAL: Normalize labels BEFORE voting
        normalized_spans = self.normalizer.normalize_spans(spans)
        
        # Sort by start position
        normalized_spans.sort(key=lambda x: x.start)
        
        resolved = []
        current_group = []
        group_end = -1
        
        for span in normalized_spans:
            if not current_group:
                current_group.append(span)
                group_end = span.end
                continue
            
            # Check overlap
            if span.start < group_end:
                current_group.append(span)
                group_end = max(group_end, span.end)
            else:
                # Resolve current group
                winner = self._pick_winner(current_group)
                resolved.append(winner)
                
                # Start new group
                current_group = [span]
                group_end = span.end
        
        if current_group:
            winner = self._pick_winner(current_group)
            resolved.append(winner)
        
        return resolved
    
    def _pick_winner(self, group: List[Span]) -> Span:
        """Pick best span from overlapping group using adaptive weights"""
        if len(group) == 1:
            return group[0]
        
        best_span = None
        best_score = -1.0
        
        for span in group:
            # Get adaptive weight for this detector
            weight = self.weights.get(span.source, 1.0)
            
            # Length bonus: prefer longer matches (more specific)
            length = span.end - span.start
            length_factor = 1.0 + (min(length, 20) / 100.0)
            
            # If we have performance data, use label-specific F1 as additional signal
            label_bonus = 1.0
            if self.tracker and span.source in self.tracker.metrics:
                label_f1 = self.tracker.metrics[span.source].get_label_f1(span.label)
                # Boost entities where this detector historically performs well
                label_bonus = 1.0 + (label_f1 * 0.5)
            
            final_score = span.score * weight * length_factor * label_bonus
            
            if final_score > best_score:
                best_score = final_score
                best_span = span
        
        return best_span


class ConfigurationOptimizer:
    """
    Auto-tunes pipeline configuration using grid search on sample data
    Reduces manual trial-and-error
    """
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.tracker = PerformanceTracker()
    
    def calibrate(self,
                  texts: List[str],
                  ground_truth: List[List[Tuple[int, int, str]]],
                  label_map: Optional[Dict[str, str]] = None) -> Dict[str, any]:
        """
        Calibrate pipeline on labeled validation data
        
        Args:
            texts: List of text samples
            ground_truth: List of ground truth annotations for each text
                         Each annotation is (start, end, label)
            label_map: Optional label normalization map
        
        Returns:
            Dictionary with optimized configuration
        """
        normalizer = LabelNormalizer(label_map)
        
        # Run each detector separately to measure individual performance
        for component in self.pipeline.components:
            detector_name = getattr(component, 'name', component.__class__.__name__)
            self.tracker.add_detector(detector_name)
            
            for text, gt in zip(texts, ground_truth):
                # Get predictions from this detector
                predictions = component.detect(text)
                
                # Normalize labels for fair comparison
                predictions = normalizer.normalize_spans(predictions)
                gt_normalized = [(s, e, normalizer.normalize(l)) for s, e, l in gt]
                
                # Update metrics
                self.tracker.update_metrics(detector_name, predictions, gt_normalized)
        
        # Get optimized weights
        optimized_weights = self.tracker.get_all_weights(method="f1_squared")
        
        # Analyze label-specific performance to suggest thresholds
        suggested_label_thresholds = self._suggest_label_thresholds()
        
        return {
            "detector_weights": optimized_weights,
            "label_thresholds": suggested_label_thresholds,
            "performance_summary": self.tracker.get_summary(),
            "label_normalizer": normalizer
        }
    
    def _suggest_label_thresholds(self) -> Dict[str, float]:
        """
        Suggest label-specific thresholds based on precision/recall trade-offs
        """
        suggestions = {}
        
        for detector_name, metrics in self.tracker.metrics.items():
            for label, label_metrics in metrics.label_metrics.items():
                tp = label_metrics["tp"]
                fp = label_metrics["fp"]
                fn = label_metrics["fn"]
                
                if tp + fp == 0:
                    continue
                
                precision = tp / (tp + fp)
                
                # If precision is low, suggest higher threshold
                if precision < 0.3:
                    suggested_threshold = 0.6
                elif precision < 0.5:
                    suggested_threshold = 0.5
                elif precision < 0.7:
                    suggested_threshold = 0.4
                else:
                    suggested_threshold = 0.3
                
                # Take minimum threshold across detectors (most permissive)
                if label not in suggestions or suggested_threshold < suggestions[label]:
                    suggestions[label] = suggested_threshold
        
        return suggestions
    
    def calibrate_with_validation(self,
                                   train_texts: List[str],
                                   train_ground_truth: List[List[Tuple[int, int, str]]],
                                   val_texts: List[str],
                                   val_ground_truth: List[List[Tuple[int, int, str]]],
                                   max_gap_threshold: float = 0.15) -> Dict:
        """
        Calibrate with generalization validation on held-out data
        
        Args:
            train_texts: Calibration texts (for learning weights)
            train_ground_truth: Calibration ground truth
            val_texts: Validation texts (unseen, for checking generalization)
            val_ground_truth: Validation ground truth
            max_gap_threshold: Maximum acceptable F1 gap (default: 0.15)
        
        Returns:
            Dictionary with calibration results and validation metrics
        """
        # Step 1: Calibrate on training set
        train_results = self.calibrate(train_texts, train_ground_truth)
        
        # Step 2: Get normalizer
        normalizer = train_results.get("label_normalizer") or LabelNormalizer()
        
        # Step 3: Test on validation set (unseen data)
        val_tp = val_fp = val_fn = 0
        
        for text, gt in zip(val_texts, val_ground_truth):
            # Get predictions from pipeline
            predictions = []
            for component in self.pipeline.components:
                predictions.extend(component.detect(text))
            
            # Normalize
            predictions = normalizer.normalize_spans(predictions)
            gt_normalized = [(s, e, normalizer.normalize(l)) for s, e, l in gt]
            
            # Apply pipeline processing (consensus, etc.)
            processed = self.pipeline._process_spans(text, predictions)
            
            # Calculate matches
            pred_set = {(s.start, s.end, s.label) for s in processed}
            gt_set = set(gt_normalized)
            
            val_tp += len(pred_set & gt_set)
            val_fp += len(pred_set - gt_set)
            val_fn += len(gt_set - pred_set)
        
        # Calculate validation metrics
        val_precision = val_tp / (val_tp + val_fp) if (val_tp + val_fp) > 0 else 0
        val_recall = val_tp / (val_tp + val_fn) if (val_tp + val_fn) > 0 else 0
        val_f1 = 2 * val_precision * val_recall / (val_precision + val_recall) if (val_precision + val_recall) > 0 else 0
        
        # Calculate generalization gap
        train_perf = train_results.get("performance_summary", {})
        train_tp = sum(m.get("true_positives", 0) for m in train_perf.values())
        train_fp = sum(m.get("false_positives", 0) for m in train_perf.values())
        train_fn = sum(m.get("false_negatives", 0) for m in train_perf.values())
        
        train_precision = train_tp / (train_tp + train_fp) if (train_tp + train_fp) > 0 else 0
        train_f1 = 2 * train_precision * (train_tp / (train_tp + train_fn)) / (train_precision + (train_tp / (train_tp + train_fn))) if (train_tp + train_fn) > 0 and (train_precision + (train_tp / (train_tp + train_fn))) > 0 else 0
        
        precision_gap = abs(train_precision - val_precision)
        f1_gap = abs(train_f1 - val_f1)
        
        # Determine generalization status
        if f1_gap < 0.10:
            status = "excellent"
            message = "✅ Excellent generalization - weights are highly reliable"
        elif f1_gap < max_gap_threshold:
            status = "good"
            message = "✅ Good generalization - weights are reliable"
        elif f1_gap < 0.20:
            status = "acceptable"
            message = "⚠️  Acceptable generalization - some drift detected"
        else:
            status = "poor"
            message = "❌ Poor generalization - increase calibration samples"
        
        # Add validation info to results
        train_results["validation_metrics"] = {
            "precision": val_precision,
            "recall": val_recall,
            "f1": val_f1,
            "true_positives": val_tp,
            "false_positives": val_fp,
            "false_negatives": val_fn,
        }
        
        train_results["generalization"] = {
            "precision_gap": precision_gap,
            "f1_gap": f1_gap,
            "status": status,
            "message": message,
            "threshold": max_gap_threshold
        }
        
        return train_results
    
    def grid_search_thresholds(self,
                               texts: List[str],
                               ground_truth: List[List[Tuple[int, int, str]]],
                               threshold_range: List[float] = None) -> Dict[str, float]:
        """
        Find optimal confidence thresholds using grid search
        
        Args:
            texts: Validation texts
            ground_truth: Ground truth annotations
            threshold_range: List of thresholds to try (default: [0.3, 0.4, 0.5, 0.6, 0.7])
        
        Returns:
            Dictionary of label -> optimal threshold
        """
        if threshold_range is None:
            threshold_range = [0.3, 0.4, 0.5, 0.6, 0.7]
        
        # TODO: Implement grid search over threshold space
        # For now, return suggested thresholds from calibration
        return self._suggest_label_thresholds()
