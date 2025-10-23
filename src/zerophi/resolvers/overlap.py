from ..types import Span
def resolve_overlaps(spans, priority_fn):
    spans_sorted = sorted(spans, key=lambda s: (s.start, -priority_fn(s.label)))
    kept=[]
    for s in spans_sorted:
        conflict=False
        for k in kept:
            if not (s.end <= k.start or s.start >= k.end):
                if priority_fn(k.label) >= priority_fn(s.label): conflict=True; break
        if not conflict: kept.append(s)
    return kept
