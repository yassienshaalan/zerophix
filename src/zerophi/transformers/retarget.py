from typing import List, Dict
from ..types import Span

def inline_minimal(text: str, spans: List[Span]) -> str:
    non_phi = [s for s in spans if not s.label.startswith("PHI.")]
    non_phi.sort(key=lambda s: s.start)
    offset = 0
    for s in non_phi:
        start = s.start + offset
        end = s.end + offset
        tag = f"[{s.label}: {s.text}]"
        text = text[:start] + tag + text[end:]
        offset += len(tag) - (end - start)
    return text

def to_sidecar(spans: List[Span]) -> List[Dict]:
    ents = []
    for s in spans:
        if s.label.startswith("PHI."):
            continue
        ents.append({
            "type": s.label,
            "text": s.text,
            "start": s.start,
            "end": s.end,
            "confidence": s.confidence,
            "detector": s.detector
        })
    return ents
