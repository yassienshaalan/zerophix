from typing import List, Dict
import re
from ..config import RedactionConfig
from ..detectors.regex_detector import RegexDetector
from ..detectors.spacy_detector import SpacyDetector
from ..detectors.bert_detector import BertDetector
from ..detectors.gliner_detector import GLiNERDetector
from ..detectors.statistical_detector import StatisticalDetector
from ..detectors.base import Span
from .consensus import ConsensusModel
from .context import ContextPropagator
from .allowlist import AllowListFilter
from .post_processors import GarbageFilter

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
        
        is_auto = cfg.mode == "auto"
        
        # 1. Regex Detector
        if is_auto or "regex" in cfg.detectors:
            self.components.append(RegexDetector(cfg.country, cfg.company, cfg.custom_patterns))
        
        # 2. Spacy Detector
        if is_auto or cfg.use_spacy:
            self.components.append(SpacyDetector())

        # 3. BERT Detector
        if is_auto or cfg.use_bert:
            self.components.append(BertDetector(confidence_threshold=cfg.thresholds.get('bert_conf', 0.9)))

        # 4. GLiNER Detector
        if is_auto or cfg.use_gliner:
            self.components.append(GLiNERDetector(labels=cfg.gliner_labels))

        # 5. Statistical Detector (Skip in auto to reduce noise, unless explicitly enabled)
        if not is_auto and cfg.use_statistical:
            self.components.append(StatisticalDetector(confidence_threshold=cfg.thresholds.get('statistical_conf', 0.7)))

        # 6. OpenMed Detector
        if is_auto or cfg.use_openmed:
            if OpenMedDetector is not None:
                self.components.append(OpenMedDetector(models_dir=cfg.models_dir, conf=self.cfg.thresholds.get('ner_conf', 0.5)))
            elif not is_auto:
                # Only raise error if user explicitly asked for it and it failed
                import sys
                if 'transformers' not in sys.modules:
                     raise RuntimeError("OpenMed detector requested but transformers/torch not installed. Install zerophix[openmed].")
                else:
                     raise RuntimeError("OpenMed detector requested but failed to import. Check logs for DEBUG messages.")
        
        # Initialize accuracy enhancement components
        self.consensus = ConsensusModel(cfg)
        self.context_propagator = ContextPropagator(cfg)
        self.allow_list = AllowListFilter(cfg)
        self.garbage_filter = GarbageFilter(cfg)

    @classmethod
    def from_config(cls, cfg: RedactionConfig):
        return cls(cfg)

    def _detect_domain(self, text: str) -> str:
        """
        Intelligent layer to classify text domain.
        """
        text_lower = text.lower()
        
        # Medical Heuristics
        medical_score = 0
        medical_terms = ["patient", "doctor", "hospital", "diagnosis", "treatment", "clinical", "medical", "prescription", "symptoms", "ward", "clinic"]
        for term in medical_terms:
            if term in text_lower:
                medical_score += 1
        
        if medical_score >= 2:
            return "medical"
            
        # Legal Heuristics
        legal_score = 0
        legal_terms = ["court", "judge", "plaintiff", "defendant", "lawyer", "attorney", "case no", "v.", "jurisdiction", "article", "section", "applicant", "respondent"]
        for term in legal_terms:
            if term in text_lower:
                legal_score += 1
                
        if legal_score >= 2:
            return "legal"
            
        return "general"

    def scan(self, text: str) -> List[Span]:
        """
        Scan text for entities without redacting.
        Returns a list of detected Span objects.
        """
        spans: List[Span] = []
        
        # Determine which components to run
        active_components = self.components
        
        if self.cfg.mode == "auto":
            domain = self._detect_domain(text)
            active_components = []
            
            for comp in self.components:
                # Always run Regex (it's fast and handles basics like emails/dates)
                if isinstance(comp, RegexDetector):
                    active_components.append(comp)
                    continue
                    
                # Always run GLiNER (it's the smartest generalist)
                if isinstance(comp, GLiNERDetector):
                    active_components.append(comp)
                    continue
                
                # Domain specific routing
                if domain == "medical":
                    if OpenMedDetector and isinstance(comp, OpenMedDetector):
                        active_components.append(comp)
                    # Keep Spacy for basic names
                    elif isinstance(comp, SpacyDetector):
                        active_components.append(comp)
                        
                elif domain == "legal":
                    # In legal, Spacy and BERT are good. OpenMed is useless.
                    if isinstance(comp, (SpacyDetector, BertDetector)):
                        active_components.append(comp)
                        
                else: # General
                    # Run everything except specialized
                    if not (OpenMedDetector and isinstance(comp, OpenMedDetector)):
                        active_components.append(comp)

        for comp in active_components:
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
        allowed_spans = self.allow_list.filter(text, propagated_spans)
        
        # 4. Filter garbage (partial words, stopwords, etc.)
        final_spans = self.garbage_filter.filter(text, allowed_spans)
        
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
