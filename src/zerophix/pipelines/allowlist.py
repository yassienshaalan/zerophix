from typing import List, Set
from ..detectors.base import Span
from ..config import RedactionConfig

class AllowListFilter:
    """
    Filters out spans that match terms in the allow list.
    This is useful for common false positives like company names or specific terms
    that should never be redacted.
    """
    def __init__(self, config: RedactionConfig):
        self.allow_list: Set[str] = set(term.lower() for term in config.allow_list)

    def filter(self, text: str, spans: List[Span]) -> List[Span]:
        if not self.allow_list:
            return spans

        filtered_spans = []
        for span in spans:
            entity_text = text[span.start:span.end].lower()
            if entity_text not in self.allow_list:
                filtered_spans.append(span)
        
        return filtered_spans
