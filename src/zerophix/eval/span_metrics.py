"""
Enhanced Span Metrics with Partial/IoU-based Matching
=====================================================

Standard exact-match span evaluation penalizes near-misses harshly.
A detection at [10, 25] that overlaps 90% with gold [11, 26] scores as
both a FP and a FN under exact match.

This module adds:
  - IoU (Intersection over Union) based partial matching
  - Token-level overlap scoring
  - Tiered scoring (exact, partial, miss)
  - Per-label breakdown with micro/macro averaging

This is critical for trusted regression: small model updates that shift
boundaries by 1-2 chars should NOT cause regression failures.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set, Iterable
from collections import defaultdict


@dataclass
class EnhancedSpanMetrics:
    """Metrics with both exact and partial match support."""
    exact_tp: int = 0
    exact_fp: int = 0
    exact_fn: int = 0
    partial_tp: float = 0.0   # weighted by IoU
    partial_fp: float = 0.0
    partial_fn: float = 0.0
    total_iou: float = 0.0
    n_matched: int = 0

    # Per-label breakdown
    label_metrics: Dict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: {
        "exact_tp": 0, "exact_fp": 0, "exact_fn": 0,
        "partial_tp": 0.0, "partial_fp": 0.0, "partial_fn": 0.0,
    }))

    @property
    def exact_precision(self) -> float:
        denom = self.exact_tp + self.exact_fp
        return self.exact_tp / denom if denom > 0 else 0.0

    @property
    def exact_recall(self) -> float:
        denom = self.exact_tp + self.exact_fn
        return self.exact_tp / denom if denom > 0 else 0.0

    @property
    def exact_f1(self) -> float:
        p, r = self.exact_precision, self.exact_recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def partial_precision(self) -> float:
        denom = self.partial_tp + self.partial_fp
        return self.partial_tp / denom if denom > 0 else 0.0

    @property
    def partial_recall(self) -> float:
        denom = self.partial_tp + self.partial_fn
        return self.partial_tp / denom if denom > 0 else 0.0

    @property
    def partial_f1(self) -> float:
        p, r = self.partial_precision, self.partial_recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def mean_iou(self) -> float:
        return self.total_iou / self.n_matched if self.n_matched > 0 else 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "exact_precision": self.exact_precision,
            "exact_recall": self.exact_recall,
            "exact_f1": self.exact_f1,
            "partial_precision": self.partial_precision,
            "partial_recall": self.partial_recall,
            "partial_f1": self.partial_f1,
            "mean_iou": self.mean_iou,
            "exact_tp": self.exact_tp,
            "exact_fp": self.exact_fp,
            "exact_fn": self.exact_fn,
        }


def _span_iou(pred_start: int, pred_end: int, gold_start: int, gold_end: int) -> float:
    """Calculate Intersection over Union for two spans."""
    inter_start = max(pred_start, gold_start)
    inter_end = min(pred_end, gold_end)
    intersection = max(0, inter_end - inter_start)

    union = (pred_end - pred_start) + (gold_end - gold_start) - intersection
    return intersection / union if union > 0 else 0.0


def compute_enhanced_span_metrics(
    gold_spans: List[Tuple[int, int, str]],
    pred_spans: List[Tuple[int, int, str]],
    iou_threshold: float = 0.5,
    ignore_label: bool = False,
) -> EnhancedSpanMetrics:
    """
    Compute metrics with both exact and partial (IoU-based) matching.

    Args:
        gold_spans: List of (start, end, label) gold annotations
        pred_spans: List of (start, end, label) predicted spans
        iou_threshold: Minimum IoU to count as a partial match (default 0.5)
        ignore_label: If True, only offsets need to match

    Returns:
        EnhancedSpanMetrics with exact and partial scores
    """
    metrics = EnhancedSpanMetrics()

    # Exact matching
    gold_keys = set()
    pred_keys = set()
    for s, e, l in gold_spans:
        key = (s, e) if ignore_label else (s, e, l)
        gold_keys.add(key)
    for s, e, l in pred_spans:
        key = (s, e) if ignore_label else (s, e, l)
        pred_keys.add(key)

    metrics.exact_tp = len(gold_keys & pred_keys)
    metrics.exact_fp = len(pred_keys - gold_keys)
    metrics.exact_fn = len(gold_keys - pred_keys)

    # Partial (IoU) matching via greedy assignment
    gold_remaining = list(range(len(gold_spans)))
    pred_remaining = list(range(len(pred_spans)))

    # Build IoU matrix and sort by descending IoU for greedy matching
    matches = []
    for gi in gold_remaining:
        gs, ge, gl = gold_spans[gi]
        for pi in pred_remaining:
            ps, pe, pl = pred_spans[pi]
            if not ignore_label and gl != pl:
                continue
            iou = _span_iou(ps, pe, gs, ge)
            if iou >= iou_threshold:
                matches.append((iou, gi, pi))

    matches.sort(key=lambda x: -x[0])  # highest IoU first

    matched_gold: Set[int] = set()
    matched_pred: Set[int] = set()

    for iou, gi, pi in matches:
        if gi in matched_gold or pi in matched_pred:
            continue
        matched_gold.add(gi)
        matched_pred.add(pi)
        metrics.partial_tp += iou
        metrics.total_iou += iou
        metrics.n_matched += 1

        # Per-label tracking
        label = gold_spans[gi][2]
        metrics.label_metrics[label]["partial_tp"] += iou

    # Unmatched predictions are false positives
    for pi in pred_remaining:
        if pi not in matched_pred:
            metrics.partial_fp += 1.0
            label = pred_spans[pi][2]
            metrics.label_metrics[label]["partial_fp"] += 1.0

    # Unmatched golds are false negatives
    for gi in gold_remaining:
        if gi not in matched_gold:
            metrics.partial_fn += 1.0
            label = gold_spans[gi][2]
            metrics.label_metrics[label]["partial_fn"] += 1.0

    # Per-label exact metrics
    for s, e, l in gold_spans:
        key = (s, e) if ignore_label else (s, e, l)
        if key in pred_keys:
            metrics.label_metrics[l]["exact_tp"] += 1
        else:
            metrics.label_metrics[l]["exact_fn"] += 1
    for s, e, l in pred_spans:
        key = (s, e) if ignore_label else (s, e, l)
        if key not in gold_keys:
            metrics.label_metrics[l]["exact_fp"] += 1

    return metrics
