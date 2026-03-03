"""
Confidence Calibration for ZeroPhix Detectors
==============================================

Problem: Raw model scores (0.0-1.0) are often poorly calibrated.
A score of 0.7 does NOT mean "70% chance this is correct."
This causes:
  - Threshold tuning to be trial-and-error
  - Ensemble voting to over/under-weight certain detectors
  - Unreliable confidence reporting to users

Solution: Platt Scaling (logistic calibration) and Isotonic Regression.
After calibrating on validation data, a score of 0.7 MEANS 70% correct.

Usage:
    calibrator = ConfidenceCalibrator()
    calibrator.fit(raw_scores, is_correct_labels)
    calibrated_score = calibrator.transform(raw_score)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import numpy as np


@dataclass
class CalibrationResult:
    """Result of calibration analysis."""
    method: str
    ece_before: float  # Expected Calibration Error before
    ece_after: float   # Expected Calibration Error after
    parameters: Dict
    n_samples: int


class ConfidenceCalibrator:
    """
    Calibrates detector confidence scores using Platt Scaling.

    Platt Scaling fits a logistic regression on the raw scores:
        P(correct | score) = 1 / (1 + exp(A * score + B))

    This is lightweight (2 parameters), works offline, and dramatically
    improves threshold selection reliability.
    """

    def __init__(self):
        self.a: float = 0.0  # logistic slope
        self.b: float = 0.0  # logistic intercept
        self.fitted: bool = False

    def fit(self, scores: List[float], labels: List[int], max_iter: int = 100, lr: float = 0.01) -> CalibrationResult:
        """
        Fit Platt scaling parameters using gradient descent.

        Args:
            scores: Raw confidence scores from detector (0-1)
            labels: Binary labels (1=correct detection, 0=incorrect)
            max_iter: Maximum optimization iterations
            lr: Learning rate

        Returns:
            CalibrationResult with before/after ECE
        """
        scores_arr = np.array(scores, dtype=np.float64)
        labels_arr = np.array(labels, dtype=np.float64)

        n = len(scores_arr)
        if n == 0:
            return CalibrationResult(method="platt", ece_before=0.0, ece_after=0.0, parameters={}, n_samples=0)

        ece_before = self._expected_calibration_error(scores_arr, labels_arr)

        # Initialize parameters
        a = -1.0
        b = 0.0

        # Newton-Raphson / gradient descent for log-loss
        for _ in range(max_iter):
            # Predicted probabilities
            logits = a * scores_arr + b
            probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -500, 500)))

            # Gradients of negative log-likelihood
            diff = probs - labels_arr
            grad_a = np.dot(diff, scores_arr) / n
            grad_b = np.mean(diff)

            # Hessian diagonal (approximate)
            w = probs * (1 - probs) + 1e-8
            hess_a = np.dot(w, scores_arr ** 2) / n
            hess_b = np.mean(w)

            # Newton update with damping
            a -= lr * grad_a / (hess_a + 1e-8)
            b -= lr * grad_b / (hess_b + 1e-8)

        self.a = float(a)
        self.b = float(b)
        self.fitted = True

        # Calculate after-calibration ECE
        calibrated = self.transform_batch(scores)
        ece_after = self._expected_calibration_error(np.array(calibrated), labels_arr)

        return CalibrationResult(
            method="platt",
            ece_before=ece_before,
            ece_after=ece_after,
            parameters={"a": self.a, "b": self.b},
            n_samples=n,
        )

    def transform(self, score: float) -> float:
        """Calibrate a single raw score."""
        if not self.fitted:
            return score
        logit = self.a * score + self.b
        return 1.0 / (1.0 + np.exp(-np.clip(logit, -500, 500)))

    def transform_batch(self, scores: List[float]) -> List[float]:
        """Calibrate a batch of raw scores."""
        return [float(self.transform(s)) for s in scores]

    def _expected_calibration_error(self, probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
        """
        Expected Calibration Error (ECE): measures how well-calibrated
        the confidence scores are. Lower is better. 0.0 = perfect.
        """
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n = len(probs)

        for i in range(n_bins):
            mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
            if i == n_bins - 1:
                mask = mask | (probs == bin_boundaries[i + 1])

            count = mask.sum()
            if count == 0:
                continue

            avg_confidence = probs[mask].mean()
            avg_accuracy = labels[mask].mean()
            ece += (count / n) * abs(avg_confidence - avg_accuracy)

        return float(ece)

    def save(self, filepath: str):
        """Save calibration parameters to JSON."""
        data = {
            "method": "platt",
            "a": self.a,
            "b": self.b,
            "fitted": self.fitted,
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        """Load calibration parameters from JSON."""
        with open(filepath, "r") as f:
            data = json.load(f)
        self.a = data["a"]
        self.b = data["b"]
        self.fitted = data["fitted"]


class PerDetectorCalibrator:
    """
    Manages per-detector and per-label calibration.

    Each detector has its own calibration curve because BERT at 0.9
    means something very different from GLiNER at 0.9.
    """

    def __init__(self):
        self.calibrators: Dict[str, Dict[str, ConfidenceCalibrator]] = {}
        # calibrators[detector_name][label] = ConfidenceCalibrator

    def fit_detector(
        self,
        detector_name: str,
        scores: List[float],
        labels: List[int],
        entity_labels: Optional[List[str]] = None,
    ) -> Dict[str, CalibrationResult]:
        """
        Fit calibration for a specific detector.

        Args:
            detector_name: Name of the detector (e.g., "bert", "gliner")
            scores: Raw confidence scores
            labels: Binary correctness labels
            entity_labels: Optional entity type labels for per-label calibration

        Returns:
            Dict of label -> CalibrationResult
        """
        results = {}

        # Global calibration for this detector
        if detector_name not in self.calibrators:
            self.calibrators[detector_name] = {}

        global_cal = ConfidenceCalibrator()
        results["_global"] = global_cal.fit(scores, labels)
        self.calibrators[detector_name]["_global"] = global_cal

        # Per-label calibration if labels provided
        if entity_labels:
            label_groups: Dict[str, Tuple[List[float], List[int]]] = {}
            for s, l, el in zip(scores, labels, entity_labels):
                if el not in label_groups:
                    label_groups[el] = ([], [])
                label_groups[el][0].append(s)
                label_groups[el][1].append(l)

            for entity_label, (label_scores, label_binary) in label_groups.items():
                if len(label_scores) >= 10:  # need minimum samples
                    cal = ConfidenceCalibrator()
                    results[entity_label] = cal.fit(label_scores, label_binary)
                    self.calibrators[detector_name][entity_label] = cal

        return results

    def calibrate(self, detector_name: str, score: float, entity_label: Optional[str] = None) -> float:
        """
        Calibrate a score from a specific detector.

        Uses per-label calibrator if available, falls back to global.
        """
        if detector_name not in self.calibrators:
            return score

        detector_cals = self.calibrators[detector_name]

        # Try per-label first
        if entity_label and entity_label in detector_cals:
            return detector_cals[entity_label].transform(score)

        # Fall back to global
        if "_global" in detector_cals:
            return detector_cals["_global"].transform(score)

        return score

    def save(self, filepath: str):
        """Save all calibrators to JSON."""
        data = {}
        for det_name, cals in self.calibrators.items():
            data[det_name] = {}
            for label, cal in cals.items():
                data[det_name][label] = {
                    "a": cal.a,
                    "b": cal.b,
                    "fitted": cal.fitted,
                }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        """Load all calibrators from JSON."""
        with open(filepath, "r") as f:
            data = json.load(f)
        for det_name, labels in data.items():
            self.calibrators[det_name] = {}
            for label, params in labels.items():
                cal = ConfidenceCalibrator()
                cal.a = params["a"]
                cal.b = params["b"]
                cal.fitted = params["fitted"]
                self.calibrators[det_name][label] = cal
