from typing import List, Dict
from ..config import RedactionConfig
from ..detectors.regex_detector import RegexDetector
from ..detectors.base import Span
try:
    from ..detectors.openmed_detector import OpenMedDetector
except Exception:
    OpenMedDetector = None

import hashlib

class RedactionPipeline:

    def __init__(self, cfg: RedactionConfig):
        self.cfg = cfg
        self.components = []
        self.components.append(RegexDetector(cfg.country, cfg.company))
        if cfg.use_openmed:
            if OpenMedDetector is None:
                raise RuntimeError("OpenMed detector requested but transformers/torch not installed. Install zerophi[openmed].")
            self.components.append(OpenMedDetector(models_dir=cfg.models_dir, conf=self.cfg.thresholds.get('ner_conf', 0.5)))

    @classmethod
    def from_config(cls, cfg: RedactionConfig):
        return cls(cfg)

    def _mask(self, s: str, label: str) -> str:
        style = self.cfg.masking_style
        if style == "mask":
            return "*" * len(s)
        if style == "replace":
            return f"<{label}>"
        if style == "brackets":
            return f"[{label}]"
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    def redact(self, text: str) -> Dict[str, object]:
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        spans.sort(key=lambda x: (x.start, -x.end))
        merged: List[Span] = []
        for s in spans:
            if merged and not (s.start >= merged[-1].end or s.end <= merged[-1].start):
                a = merged[-1]
                if (s.end - s.start) > (a.end - a.start) or s.score >= a.score:
                    merged[-1] = s
                continue
            merged.append(s)

        from ..policies.loader import load_policy
        policy = load_policy(self.cfg.country, self.cfg.company)
        actions = policy.get("actions", {})
        out_text = []
        i = 0
        for s in merged:
            out_text.append(text[i:s.start])
            action = actions.get(s.label, actions.get("default", "hash"))
            out_text.append(self._mask(text[s.start:s.end], s.label if not self.cfg.keep_surrogates else action.upper()))
            i = s.end
        out_text.append(text[i:])
        return {"text": "".join(out_text), "spans": [s.__dict__ for s in merged]}

    def scan(self, text: str) -> Dict[str, object]:
        """Scan text for PII/PHI without redacting. Returns detection report."""
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        spans.sort(key=lambda x: (x.start, -x.end))
        merged: List[Span] = []
        for s in spans:
            if merged and not (s.start >= merged[-1].end or s.end <= merged[-1].start):
                a = merged[-1]
                if (s.end - s.start) > (a.end - a.start) or s.score >= a.score:
                    merged[-1] = s
                continue
            merged.append(s)

        # Calculate statistics
        entity_counts = {}
        for s in merged:
            entity_counts[s.label] = entity_counts.get(s.label, 0) + 1

        # Extract matched text snippets
        detections = []
        for s in merged:
            detections.append({
                "start": s.start,
                "end": s.end,
                "label": s.label,
                "score": s.score,
                "text": text[s.start:s.end],
                "context": text[max(0, s.start-20):min(len(text), s.end+20)]
            })

        return {
            "original_text": text,
            "total_detections": len(merged),
            "entity_counts": entity_counts,
            "detections": detections,
            "has_pii": len(merged) > 0
        }
