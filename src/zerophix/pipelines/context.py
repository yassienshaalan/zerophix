import regex as re
from typing import List, Set, Dict
from ..detectors.base import Span
from ..config import RedactionConfig

class ContextPropagator:
    """
    Implements Session Memory to propagate high-confidence entities.
    If an entity is detected with high confidence in one place, 
    other occurrences of the same text should also be redacted, 
    even if the detector missed them (e.g. due to lack of context).
    """
    def __init__(self, config: RedactionConfig):
        self.threshold = config.context_propagation_threshold
        self.enabled = config.enable_context_propagation

    def propagate(self, text: str, spans: List[Span]) -> List[Span]:
        if not self.enabled:
            return spans

        # 1. Identify high-confidence entities and their labels
        # We use a voting mechanism: if "John Smith" is PERSON 3 times and ORG 1 time, treat as PERSON.
        text_counts: Dict[str, Dict[str, int]] = {}
        
        for span in spans:
            if span.score >= self.threshold:
                entity_text = text[span.start:span.end]
                # Ignore very short words to avoid noise (e.g. "is", "at")
                if len(entity_text) > 3:
                    if entity_text not in text_counts:
                        text_counts[entity_text] = {}
                    text_counts[entity_text][span.label] = text_counts[entity_text].get(span.label, 0) + 1

        # Resolve best label for each text
        memory: Dict[str, str] = {}
        for txt, labels in text_counts.items():
            best_label = max(labels.items(), key=lambda x: x[1])[0]
            memory[txt] = best_label

        if not memory:
            return spans

        # 2. Scan for missed occurrences
        new_spans = list(spans)
        
        # Create a set of occupied indices for fast lookup to avoid overlapping existing spans
        occupied = set()
        for s in spans:
            for i in range(s.start, s.end):
                occupied.add(i)

        # Sort memory keys by length (descending) to handle substrings correctly if needed, 
        # though we check occupied indices so it matters less.
        sorted_entities = sorted(memory.keys(), key=len, reverse=True)

        for entity_text in sorted_entities:
            label = memory[entity_text]
            pattern = re.escape(entity_text)
            
            # Use word boundaries if the entity starts/ends with alphanumeric characters
            # This prevents "Sam" from matching inside "Sample"
            prefix = r'\b' if entity_text[0].isalnum() else ''
            suffix = r'\b' if entity_text[-1].isalnum() else ''
            full_pattern = f"{prefix}{pattern}{suffix}"
                
            for match in re.finditer(full_pattern, text):
                start, end = match.span()
                
                # Check if this range overlaps with any existing span
                overlap = False
                for i in range(start, end):
                    if i in occupied:
                        overlap = True
                        break
                
                if not overlap:
                    # Add new span with very high confidence since it matched a high-conf peer
                    new_spans.append(Span(start, end, label, score=0.99, source="context_memory"))
                    
                    # Mark these indices as occupied
                    for i in range(start, end):
                        occupied.add(i)
                        
        return new_spans
