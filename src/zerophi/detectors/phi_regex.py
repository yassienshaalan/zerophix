import regex as re
from typing import List
from ..types import Span, Doc

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{2,4}\)|\d{2,4})[-.\s]?\d{3}[-.\s]?\d{3,4}\b")
_DATE = re.compile(r"\b(?:\d{1,2}[/-]){2}\d{2,4}\b")
_ADDRESS_HINT = re.compile(r"\b\d+\s+[A-Za-z][A-Za-z\s]+(St|Street|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Ln|Lane)\b", re.IGNORECASE)
_NAME_HINT = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")

class PHIRegexDetector:
    def __init__(self, detector_id: str = "phi_regex:v0.1"):
        self.detector_id = detector_id

    def detect(self, doc: Doc) -> List[Span]:
        spans: List[Span] = []
        text = doc.text
        for lab, pat in [
            ("PHI.EMAIL", _EMAIL),
            ("PHI.PHONE", _PHONE),
            ("PHI.DATE", _DATE),
            ("PHI.ADDRESS", _ADDRESS_HINT),
            ("PHI.NAME", _NAME_HINT),
        ]:
            for m in pat.finditer(text):
                spans.append(Span(m.start(), m.end(), lab, m.group(0), 0.99, self.detector_id, {}))
        return spans
