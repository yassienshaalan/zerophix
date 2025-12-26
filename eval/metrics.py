from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Iterable, Set


Span = Tuple[str, int, int, Optional[str]]  # (doc_id, start, end, label)


@dataclass
class SpanMetrics:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "tp": float(self.tp),
            "fp": float(self.fp),
            "fn": float(self.fn),
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


def _span_key(span: Span, ignore_label: bool) -> Tuple:
    doc_id, start, end, label = span
    return (doc_id, start, end) if ignore_label else (doc_id, start, end, label)


def compute_span_metrics(
    gold_spans: Iterable[Span],
    pred_spans: Iterable[Span],
    ignore_label: bool = False,
) -> SpanMetrics:
    """
    Compute micro-averaged precision/recall/F1 over span-level entities.

    gold_spans/pred_spans: iterable of (doc_id, start, end, label)
    ignore_label: if True, only offsets must match.
    """
    gold_keys: Set[Tuple] = {_span_key(s, ignore_label) for s in gold_spans}
    pred_keys: Set[Tuple] = {_span_key(s, ignore_label) for s in pred_spans}

    tp = len(gold_keys & pred_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)

    return SpanMetrics(tp=tp, fp=fp, fn=fn)
