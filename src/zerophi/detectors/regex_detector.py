import regex as re
from typing import List
from .base import Detector, Span
from ..policies.loader import load_policy

class RegexDetector(Detector):
    name = "regex"

    def __init__(self, country: str, company: str | None):
        self.patterns = load_policy(country, company).get("regex_patterns", {})

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for label, pat in self.patterns.items():
            for m in re.finditer(pat, text, flags=re.IGNORECASE | re.MULTILINE):
                spans.append(Span(m.start(), m.end(), label=label, score=1.0, source="regex"))
        return spans
