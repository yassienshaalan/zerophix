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
        # Labels that are allowed to be very short (1-2 chars)
        self.short_allowed_labels = {
            "USERNAME", "BUILDING", "AGE", "TIME", "STATE", 
            "TITLE", "POSTCODE", "COUNTRY", "IDCARD"
        }
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
        
        # Medical entity labels that should never be filtered
        self.medical_labels = {
            "DRUG", "MEDICATION", "MEDICINE", "MEDICAL_CONDITION", "DISEASE",
            "DIAGNOSIS", "PROCEDURE", "TREATMENT", "SYMPTOM", "ANATOMY"
        }
        
        # Medication suffix patterns (pattern-based detection instead of fixed list)
        self.medication_patterns = [
            r'\b\w+mycin\b',      # Antibiotics: erythromycin, azithromycin
            r'\b\w+cillin\b',     # Penicillins: amoxicillin, penicillin
            r'\b\w+statin\b',     # Statins: atorvastatin, simvastatin
            r'\b\w+pril\b',       # ACE inhibitors: lisinopril, enalapril
            r'\b\w+sartan\b',     # ARBs: losartan, valsartan
            r'\b\w+olol\b',       # Beta blockers: metoprolol, atenolol
            r'\b\w+prazole\b',    # PPIs: omeprazole, lansoprazole
            r'\b\w+dipine\b',     # Calcium channel blockers: amlodipine
            r'\b\w+zolam\b',      # Benzodiazepines: alprazolam, diazepam
            r'\b\w+pam\b',        # Benzodiazepines: diazepam, lorazepam
            r'\b\w+barbital\b',   # Barbiturates
            r'\b\w+caine\b',      # Local anesthetics: lidocaine
            r'\b\w+adol\b',       # Analgesics: tramadol
            r'\b\w+formin\b',     # Antidiabetics: metformin
            r'\b\w+flurane\b',    # Anesthetics: sevoflurane
            r'\b\w+oxacin\b',     # Fluoroquinolones: ciprofloxacin
            r'\b\w+tidine\b',     # H2 blockers: ranitidine
            r'\b\w+cycline\b',    # Tetracyclines: doxycycline
        ]
        
        # Medical condition suffix patterns
        self.condition_patterns = [
            r'\b\w+itis\b',       # Inflammation: arthritis, hepatitis
            r'\b\w+oma\b',        # Tumors: carcinoma, lymphoma
            r'\b\w+osis\b',       # Conditions: cirrhosis, osteoporosis
            r'\b\w+pathy\b',      # Diseases: neuropathy, nephropathy
            r'\b\w+emia\b',       # Blood conditions: anemia, leukemia
            r'\b\w+algia\b',      # Pain: neuralgia, myalgia
            r'\b\w+plegia\b',     # Paralysis: paraplegia, hemiplegia
            r'\b\w+trophy\b',     # Growth disorders: hypertrophy, atrophy
        ]
        
        # Compile patterns for efficiency
        self.medication_regex = [re.compile(p, re.IGNORECASE) for p in self.medication_patterns]
        self.condition_regex = [re.compile(p, re.IGNORECASE) for p in self.condition_patterns]

    def _is_medical_entity(self, text: str, span: Span) -> bool:
        """
        Pattern-based detection of medical entities using suffix patterns.
        More robust than hardcoded lists.
        """
        # Check if label indicates medical entity
        if span.label in self.medical_labels:
            return True
        
        # Check medication patterns
        for pattern in self.medication_regex:
            if pattern.search(text):
                return True
        
        # Check condition patterns
        for pattern in self.condition_regex:
            if pattern.search(text):
                return True
        
        # Check if it contains medical dosage patterns (e.g., "1000mg", "5mg", "100ml")
        if re.search(r'\d+\s*(mg|ml|mcg|g|l|cc|iu|units?)\b', text, re.IGNORECASE):
            return True
        
        return False
    
    def filter(self, text: str, spans: List[Span]) -> List[Span]:
        filtered_spans = []
        
        for span in spans:
            entity_text = text[span.start:span.end]
            clean_text = entity_text.strip()
            
            # 0. NEVER filter medical entities (pattern-based detection)
            if self._is_medical_entity(clean_text, span):
                filtered_spans.append(span)
                continue
            
            # 1. Filter empty or whitespace-only
            if not clean_text:
                continue
                
            # 2. Filter very short spans (unless allowed for specific labels)
            if len(clean_text) < self.min_len:
                # Allow short entities for specific labels
                if span.label.upper() in self.short_allowed_labels:
                    filtered_spans.append(span)
                    continue
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
                
                # Filter medical terms misidentified as person names
                medical_false_positives = [
                    r'^(?:Type|diabetes|mellitus|prescribed|diagnosed|treated|increase)$',
                    r'^\d+(?:mg|ml|mcg|g|l|BD|TDS|QD|daily)$',
                    r'^(?:Chief|Complaint|Treatment|Medication|Condition)$',
                ]
                if any(re.match(pattern, clean_text, re.IGNORECASE) for pattern in medical_false_positives):
                    continue
                
                # Require higher confidence for person names (reduce false positives)
                if span.score < 0.7:
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
