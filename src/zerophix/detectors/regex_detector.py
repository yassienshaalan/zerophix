import regex as re
from typing import List
from .base import Detector, Span
from ..policies.loader import load_policy

# Import Australian validators
try:
    from .au_validators import validate_span_checksum
    AU_VALIDATION_AVAILABLE = True
except ImportError:
    AU_VALIDATION_AVAILABLE = False

class RegexDetector(Detector):
    name = "regex"

    def __init__(self, country: str, company: str | None, custom_patterns: dict[str, list[str]] | None = None):
        self.country = country
        self.patterns = load_policy(country, company).get("regex_patterns", {})
        
        # Merge dynamic custom patterns
        if custom_patterns:
            for label, patterns in custom_patterns.items():
                # If it's a list, join them or handle multiple. 
                # The current implementation expects a single regex string per label in self.patterns.
                # But config.py defines custom_patterns as Dict[str, List[str]].
                # We should probably iterate and add them.
                # However, self.patterns is Dict[str, str] (label -> regex).
                # Let's support both or just append to the regex with OR | if multiple?
                # Or better, just treat them as separate entries if possible, but the dict key is the label.
                
                # Simple approach: Join with | if multiple patterns for same label
                combined_pattern = "|".join(f"(?:{p})" for p in patterns)
                
                if label in self.patterns:
                    # Append to existing pattern
                    self.patterns[label] = f"{self.patterns[label]}|{combined_pattern}"
                else:
                    self.patterns[label] = combined_pattern

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for label, pat in self.patterns.items():
            for m in re.finditer(pat, text, flags=re.IGNORECASE | re.MULTILINE):
                # Apply checksum validation for Australian entities
                is_valid = True
                
                if self.country == "AU" and AU_VALIDATION_AVAILABLE:
                    # Validate using checksum if available for this entity type
                    is_valid = validate_span_checksum(text, m.start(), m.end(), label)
                
                if is_valid:
                    spans.append(Span(m.start(), m.end(), label=label, score=1.0, source="regex"))
        
        return spans
