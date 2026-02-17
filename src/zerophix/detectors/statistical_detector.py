import re
import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from collections import Counter

try:
    from scipy import stats
    scipy_available = True
except ImportError:
    scipy_available = False
    stats = None

from .base import Detector, Span

class StatisticalDetector(Detector):
    """Statistical detector that learns patterns from text characteristics"""
    
    name = "statistical"
    
    def __init__(self, min_frequency: int = 2, confidence_threshold: float = 0.7):
        """
        Initialize statistical detector
        
        Args:
            min_frequency: Minimum frequency for pattern to be considered
            confidence_threshold: Minimum confidence for detection
        """
        if not scipy_available:
            raise RuntimeError(
                "Statistical detector requires scipy. Install with: pip install zerophix[statistical]"
            )
        
        self.min_frequency = min_frequency
        self.confidence_threshold = confidence_threshold
        
        # Statistical patterns learned from data
        self.learned_patterns = {
            'email_like': [],
            'phone_like': [],
            'id_like': [],
            'date_like': [],
            'name_like': []
        }
        
        # Entropy thresholds for different data types
        self.entropy_thresholds = {
            'high_entropy': 3.5,  # Random-looking data (IDs, tokens)
            'medium_entropy': 2.5,  # Semi-structured (names, addresses)
            'low_entropy': 1.5   # Structured (dates, numbers)
        }
    
    def detect(self, text: str) -> List[Span]:
        """Detect entities using statistical analysis"""
        spans = []
        
        # Tokenize text into potential entities
        tokens = self._tokenize_text(text)
        
        for token_info in tokens:
            token, start, end = token_info
            
            # Skip very short tokens
            if len(token) < 3:
                continue
            
            # Analyze token characteristics
            analysis = self._analyze_token(token)
            
            # Determine most likely entity type
            entity_type, confidence = self._classify_token(analysis)
            
            if entity_type and confidence >= self.confidence_threshold:
                spans.append(Span(
                    start=start,
                    end=end,
                    label=entity_type,
                    score=confidence,
                    source="statistical"
                ))
        
        return spans
    
    def _tokenize_text(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract potential entity tokens with positions"""
        tokens = []
        
        # Word boundaries
        for match in re.finditer(r'\b\w+(?:\s+\w+)*\b', text):
            tokens.append((match.group(), match.start(), match.end()))
        
        # Email-like patterns
        for match in re.finditer(r'\S+@\S+\.\w+', text):
            tokens.append((match.group(), match.start(), match.end()))
        
        # Number sequences
        for match in re.finditer(r'\d+(?:[-.\s]\d+)*', text):
            tokens.append((match.group(), match.start(), match.end()))
        
        # Mixed alphanumeric
        for match in re.finditer(r'\b\w*\d+\w*\b', text):
            if len(match.group()) > 3:
                tokens.append((match.group(), match.start(), match.end()))
        
        return tokens
    
    def _analyze_token(self, token: str) -> Dict[str, float]:
        """Analyze statistical characteristics of a token"""
        analysis = {
            'length': len(token),
            'entropy': self._calculate_entropy(token),
            'digit_ratio': sum(c.isdigit() for c in token) / len(token),
            'alpha_ratio': sum(c.isalpha() for c in token) / len(token),
            'special_ratio': sum(not c.isalnum() for c in token) / len(token),
            'uppercase_ratio': sum(c.isupper() for c in token) / len(token),
            'has_pattern': self._check_patterns(token),
            'repeated_chars': self._check_repetition(token),
            'sequential_chars': self._check_sequential(token)
        }
        
        return analysis
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        counter = Counter(text.lower())
        length = len(text)
        
        entropy = 0.0
        for count in counter.values():
            p = count / length
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _check_patterns(self, token: str) -> Dict[str, bool]:
        """Check for known patterns in token"""
        patterns = {
            'email': bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', token)),
            'phone': bool(re.match(r'^[\d\s\-\(\)\+]{7,}$', token)),
            'date': bool(re.match(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$', token)),
            'ssn': bool(re.match(r'^\d{3}-?\d{2}-?\d{4}$', token)),
            'credit_card': bool(re.match(r'^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$', token)),
            'uuid': bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', token.lower())),
            'ip_address': bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', token)),
            'time': bool(re.match(r'^\d{1,2}:\d{2}(:\d{2})?(\s?(AM|PM))?$', token.upper()))
        }
        
        return patterns
    
    def _check_repetition(self, token: str) -> float:
        """Check for character repetition patterns"""
        if len(token) < 2:
            return 0.0
        
        repeated = 0
        for i in range(1, len(token)):
            if token[i] == token[i-1]:
                repeated += 1
        
        return repeated / (len(token) - 1)
    
    def _check_sequential(self, token: str) -> bool:
        """Check for sequential character patterns"""
        if len(token) < 3:
            return False
        
        # Check for ascending sequences
        ascending = 0
        descending = 0
        
        for i in range(2, len(token)):
            if ord(token[i]) == ord(token[i-1]) + 1 == ord(token[i-2]) + 2:
                ascending += 1
            elif ord(token[i]) == ord(token[i-1]) - 1 == ord(token[i-2]) - 2:
                descending += 1
        
        return (ascending + descending) / max(1, len(token) - 2) > 0.3
    
    def _classify_token(self, analysis: Dict) -> Tuple[Optional[str], float]:
        """Classify token based on statistical analysis"""
        confidence = 0.0
        entity_type = None
        
        # Check explicit patterns first
        patterns = analysis['has_pattern']
        
        if patterns['email']:
            return 'EMAIL', 0.95
        elif patterns['ssn']:
            return 'SSN', 0.9
        elif patterns['credit_card']:
            return 'CREDIT_CARD', 0.9
        elif patterns['phone']:
            return 'PHONE', 0.85
        elif patterns['date']:
            return 'DATE', 0.8
        elif patterns['time']:
            return 'TIME', 0.8
        elif patterns['ip_address']:
            return 'IP_ADDRESS', 0.85
        elif patterns['uuid']:
            return 'UUID', 0.9
        
        # Statistical classification
        length = analysis['length']
        entropy = analysis['entropy']
        digit_ratio = analysis['digit_ratio']
        alpha_ratio = analysis['alpha_ratio']
        
        # High entropy with mixed characters - likely ID or token
        if entropy > self.entropy_thresholds['high_entropy']:
            if 0.3 < digit_ratio < 0.7 and alpha_ratio > 0.2:
                entity_type = 'IDENTIFIER'
                confidence = 0.7
        
        # Medium entropy, mostly letters - likely name
        elif entropy > self.entropy_thresholds['medium_entropy']:
            if alpha_ratio > 0.7 and analysis['uppercase_ratio'] > 0.1:
                if 4 <= length <= 20:
                    entity_type = 'PERSON_NAME'
                    confidence = 0.6
        
        # Mostly digits with some structure - likely numeric ID
        elif digit_ratio > 0.7:
            if 6 <= length <= 20 and not analysis['sequential_chars']:
                entity_type = 'NUMERIC_ID'
                confidence = 0.65
        
        # Long alphanumeric strings - possible sensitive data
        elif length > 12 and entropy > 2.0:
            if digit_ratio > 0.2 and alpha_ratio > 0.2:
                entity_type = 'SENSITIVE_CODE'
                confidence = 0.6
        
        return entity_type, confidence

class FrequencyDetector(Detector):
    """Detector that identifies entities based on frequency analysis"""
    
    name = "frequency"
    
    def __init__(self, rare_threshold: float = 0.01, common_threshold: float = 0.1):
        """
        Initialize frequency detector
        
        Args:
            rare_threshold: Threshold for identifying rare terms (potential PII)
            common_threshold: Threshold for common terms (likely not PII)
        """
        self.rare_threshold = rare_threshold
        self.common_threshold = common_threshold
        self.term_frequencies = {}
        self.total_terms = 0
    
    def learn_frequencies(self, texts: List[str]):
        """Learn term frequencies from a corpus of texts"""
        term_counts = Counter()
        
        for text in texts:
            tokens = re.findall(r'\b\w+\b', text.lower())
            term_counts.update(tokens)
            self.total_terms += len(tokens)
        
        # Convert to frequencies
        for term, count in term_counts.items():
            self.term_frequencies[term] = count / self.total_terms
    
    def detect(self, text: str) -> List[Span]:
        """Detect potential PII based on term rarity"""
        if not self.term_frequencies:
            return []  # Need to learn frequencies first
        
        spans = []
        
        for match in re.finditer(r'\b\w+\b', text):
            term = match.group().lower()
            frequency = self.term_frequencies.get(term, 0)
            
            # Rare terms might be PII
            if frequency < self.rare_threshold and len(term) > 2:
                # Additional checks to avoid false positives
                if not self._is_common_word(term):
                    confidence = min(0.8, (self.rare_threshold - frequency) / self.rare_threshold)
                    
                    spans.append(Span(
                        start=match.start(),
                        end=match.end(),
                        label='RARE_TERM',
                        score=confidence,
                        source="frequency"
                    ))
        
        return spans
    
    def _is_common_word(self, term: str) -> bool:
        """Check if term is a common English word"""
        common_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
            'one', 'all', 'would', 'there', 'their', 'what', 'so',
            'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than',
            'then', 'now', 'look', 'only', 'come', 'its', 'over',
            'think', 'also', 'back', 'after', 'use', 'two', 'how',
            'our', 'work', 'first', 'well', 'way', 'even', 'new',
            'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }
        
        return term in common_words