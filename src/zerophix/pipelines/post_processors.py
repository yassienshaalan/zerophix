import re
from typing import List
from ..detectors.base import Span
from ..config import RedactionConfig

class GarbageFilter:
    """
    Filters out spans that are likely 'garbage' or noise.
    Common issues in NER models include:
    - Partial words ("ing", "tion")
    - Punctuation-only spans
    - Spans starting with lowercase (often not proper nouns in legal text)
    - Very short spans (1-2 chars) that aren't initials
    - Common non-PII words falsely matched by regex (Test, Email, Patient, etc.)
    """
    def __init__(self, config: RedactionConfig):
        self.min_len = 3
        # Common English stopwords that should rarely be entities on their own
        self.stopwords = {
            "the", "and", "of", "to", "in", "a", "is", "that", "for", "on", "with", "as", "by", "at", "an", "be", "this", "which", "or", "from"
        }
        # Common false positive patterns for PERSON_NAME regex
        self.common_false_positives = {
            # Testing/example text
            "test text", "test data", "test case", "test user", "test patient", "sample data", "sample text",
            "example text", "example data", "demo data", "demo text",
            # Labels/headers that match person name pattern
            "email address", "phone number", "patient name", "full name", "first name", "last name",
            "patient id", "user id", "account number", "reference number",
            # Common metadata
            "date time", "time zone", "file name", "file path", "user name", "user type"
        }

    def filter(self, text: str, spans: List[Span]) -> List[Span]:
        filtered_spans = []
        
        for span in spans:
            entity_text = text[span.start:span.end]
            clean_text = entity_text.strip()
            
            # 1. Filter empty or whitespace-only
            if not clean_text:
                continue
                
            # 2. Filter very short spans (unless they look like initials e.g. "J.")
            if len(clean_text) < self.min_len:
                # Allow if it looks like an initial (e.g. "J.") or a number
                if not (re.match(r"^[A-Z]\.?$", clean_text) or clean_text.isdigit()):
                    continue

            # 3. Filter spans that are just punctuation
            if re.match(r"^[\W_]+$", clean_text):
                continue
                
            # 4. Filter spans that are just stopwords
            if clean_text.lower() in self.stopwords:
                continue
            
            # 5. Filter common false positives for PERSON_NAME (test text, email address, etc.)
            if span.label in ("PERSON_NAME", "person", "PERSON"):
                if clean_text.lower() in self.common_false_positives:
                    continue
                # Skip single common words that are not names
                if clean_text.lower() in {"email", "phone", "patient", "tfn", "abn", "medicare", "ssn", "address"}:
                    continue
                
            # 6. Filter spans starting with lowercase (for Person/Org/Location)
            # This is a strong heuristic for legal text which is usually well-formatted.
            # We skip this for 'date' or 'email' which might be lowercase.
            if span.label in ("person", "organization", "location", "judge", "lawyer", "applicant", "PERSON_NAME", "PERSON"):
                if clean_text[0].islower():
                    continue
            
            # 7. Filter partial word matches (starts or ends with alphanumeric but adjacent char in text is also alphanumeric)
            # Check previous char
            if span.start > 0 and text[span.start - 1].isalnum() and text[span.start].isalnum():
                continue
            # Check next char
            if span.end < len(text) and text[span.end - 1].isalnum() and text[span.end].isalnum():
                continue
            
            # 8. Filter POSTCODE_AU when it's part of a larger number (like SSN)
            if span.label == "POSTCODE_AU":
                # Check if preceded by digits (likely part of larger number)
                if span.start > 0 and text[span.start - 1].isdigit():
                    continue
                # Check if followed by more digits (likely part of larger number)
                if span.end < len(text) and text[span.end].isdigit():
                    continue

            filtered_spans.append(span)
            
        return filtered_spans
