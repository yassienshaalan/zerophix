from typing import List, Dict
from ..config import RedactionConfig
from ..detectors.regex_detector import RegexDetector
from ..detectors.base import Span
from .consensus import ConsensusModel
from .context import ContextPropagator
from .allowlist import AllowListFilter

try:
    from ..detectors.openmed_detector import OpenMedDetector
except ImportError as e:
    print(f"DEBUG: Failed to import OpenMedDetector (ImportError): {e}")
    OpenMedDetector = None
except Exception as e:
    print(f"DEBUG: Failed to import OpenMedDetector: {e}")
    import traceback
    traceback.print_exc()
    OpenMedDetector = None

import hashlib

class RedactionPipeline:

    def __init__(self, cfg: RedactionConfig):
        self.cfg = cfg
        self.components = []
        self.components.append(RegexDetector(cfg.country, cfg.company, cfg.custom_patterns))
        if cfg.use_openmed:
            if OpenMedDetector is None:
                # Try to give a more helpful error message if we know why it failed
                import sys
                if 'transformers' not in sys.modules:
                     raise RuntimeError("OpenMed detector requested but transformers/torch not installed. Install zerophix[openmed].")
                else:
                     raise RuntimeError("OpenMed detector requested but failed to import. Check logs for DEBUG messages.")
            self.components.append(OpenMedDetector(models_dir=cfg.models_dir, conf=self.cfg.thresholds.get('ner_conf', 0.5)))
        
        # Initialize accuracy enhancement components
        self.consensus = ConsensusModel(cfg)
        self.context_propagator = ContextPropagator(cfg)
        self.allow_list = AllowListFilter(cfg)

    @classmethod
    def from_config(cls, cfg: RedactionConfig):
        return cls(cfg)

    def scan(self, text: str) -> List[Span]:
        """
        Scan text for entities without redacting.
        Returns a list of detected Span objects.
        """
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)
        return merged

    def _mask(self, s: str, label: str) -> str:
        style = self.cfg.masking_style
        if style == "mask":
            return "*" * len(s)
        if style == "replace":
            return f"<{label}>"
        if style == "brackets":
            return f"[{label}]"
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    def _process_spans(self, text: str, spans: List[Span]) -> List[Span]:
        """
        Apply consensus, context propagation, and allow-list filtering.
        """
        # 1. Resolve conflicts using Ensemble Voting
        resolved_spans = self.consensus.resolve(spans, text)
        
        # 2. Propagate context (Session Memory)
        # We run this after resolution so we propagate based on the "winner" labels
        propagated_spans = self.context_propagator.propagate(text, resolved_spans)
        
        # 3. Filter allow-listed terms
        final_spans = self.allow_list.filter(text, propagated_spans)
        
        # Sort for final output
        final_spans.sort(key=lambda x: (x.start, -x.end))
        
        return final_spans

    def redact(self, text: str, user_context: Dict = None, session_id: str = None) -> Dict[str, object]:
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)

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
        
        # Convert spans to dict and ensure JSON serializable types
        serializable_spans = []
        for s in merged:
            d = s.__dict__.copy()
            # Convert numpy/torch floats to python floats
            if hasattr(d['score'], 'item'):
                d['score'] = float(d['score'])
            serializable_spans.append(d)
            
        return {"text": "".join(out_text), "spans": serializable_spans}

    def scan(self, text: str) -> Dict[str, object]:
        """Scan text for PII/PHI without redacting. Returns detection report."""
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)

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
