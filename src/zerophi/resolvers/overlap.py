from typing import List
from ..types import Span

_PRIORITY = {
    "PHI.NAME": 100,
    "PHI.ID": 95,
    "PHI.DATE": 90,
    "PHI.EMAIL": 85,
    "PHI.PHONE": 85,
    "PHI.ADDRESS": 80,
}

def _priority(label: str) -> int:
    if label.startswith("PHI."):
        return _PRIORITY.get(label, 70)
    return 10

def resolve_overlaps(spans: List[Span]) -> List[Span]:
    spans_sorted = sorted(spans, key=lambda s: (s.start, -_priority(s.label)))
    kept: List[Span] = []
    for s in spans_sorted:
        conflict = False
        for k in kept:
            if not (s.end <= k.start or s.start >= k.end):
                if _priority(k.label) >= _priority(s.label):
                    conflict = True
                    break
        if not conflict:
            kept.append(s)
    return kept
