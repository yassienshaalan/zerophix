import spacy
from typing import List, Optional, Dict, Any
from .base import Detector, Span

try:
    from ..performance.model_cache import get_model_cache
    MODEL_CACHE_AVAILABLE = True
except ImportError:
    MODEL_CACHE_AVAILABLE = False

class SpacyDetector(Detector):
    """Advanced NER detector using spaCy models with custom entity recognition"""
    
    name = "spacy"
    
    def __init__(self, model_name: str = "en_core_web_sm", custom_entities: Optional[Dict[str, List[str]]] = None):
        """
        Initialize spaCy detector
        
        Args:
            model_name: spaCy model to use (en_core_web_sm, en_core_web_lg, etc.)
            custom_entities: Dict mapping entity labels to lists of patterns
        """
        cache_key = f"spacy_{model_name}"
        
        try:
            if MODEL_CACHE_AVAILABLE:
                model_cache = get_model_cache()
                if model_cache.has(cache_key):
                    self.nlp = model_cache.get(cache_key)
                    print(f"spaCy model loaded from cache: {model_name}")
                else:
                    self.nlp = spacy.load(model_name)
                    model_cache.set(cache_key, self.nlp)
            else:
                self.nlp = spacy.load(model_name)
        except OSError:
            # Fallback to blank model if specific model not available
            self.nlp = spacy.blank("en")
            
        self.custom_entities = custom_entities or {}
        self._setup_custom_entities()
        
    def _setup_custom_entities(self):
        """Add custom entity patterns to the spaCy pipeline"""
        if not self.custom_entities:
            return
            
        # Add entity ruler for custom patterns
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")
            
        patterns = []
        for label, entity_patterns in self.custom_entities.items():
            for pattern in entity_patterns:
                patterns.append({"label": label, "pattern": pattern})
                
        ruler.add_patterns(patterns)
    
    def detect(self, text: str) -> List[Span]:
        """Detect entities using spaCy NER"""
        doc = self.nlp(text)
        spans = []
        
        for ent in doc.ents:
            # Map spaCy labels to our standardized labels
            label = self._map_spacy_label(ent.label_)
            if label:
                spans.append(Span(
                    start=ent.start_char,
                    end=ent.end_char,
                    label=label,
                    score=self._calculate_confidence(ent),
                    source="spacy"
                ))
                
        return spans
    
    def _map_spacy_label(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our standardized labels"""
        mapping = {
            "PERSON": "PERSON_NAME",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "DATE": "DATE",
            "TIME": "TIME",
            "MONEY": "FINANCIAL",
            "CARDINAL": "NUMBER",
            "ORDINAL": "NUMBER",
            "PERCENT": "PERCENTAGE",
            "QUANTITY": "QUANTITY",
            "EMAIL": "EMAIL",
            "PHONE": "PHONE",
            "SSN": "SSN",
            "CREDIT_CARD": "CREDIT_CARD",
            "MEDICAL_LICENSE": "MEDICAL_LICENSE",
            "DEA_NUMBER": "DEA_NUMBER",
            "IP_ADDRESS": "IP_ADDRESS",
            "MAC_ADDRESS": "MAC_ADDRESS",
            "URL": "URL"
        }
        return mapping.get(spacy_label, spacy_label)
    
    def _calculate_confidence(self, ent) -> float:
        """Calculate confidence score for spaCy entities"""
        # spaCy doesn't provide confidence scores by default
        # We can use heuristics based on entity length, context, etc.
        base_score = 0.8
        
        # Longer entities tend to be more reliable
        if len(ent.text) > 10:
            base_score += 0.1
        elif len(ent.text) < 3:
            base_score -= 0.2
            
        # Known patterns get higher scores
        if ent.label_ in self.custom_entities:
            base_score += 0.1
            
        return min(1.0, max(0.1, base_score))