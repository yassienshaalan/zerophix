import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from typing import List, Optional, Dict, Any
from .base import Detector, Span
import numpy as np

class BertDetector(Detector):
    """Advanced BERT-based NER detector with context awareness"""
    
    name = "bert"
    
    def __init__(self, 
                 model_name: str = "dslim/bert-base-NER",
                 confidence_threshold: float = 0.9,
                 device: Optional[str] = None):
        """
        Initialize BERT detector
        
        Args:
            model_name: HuggingFace model name for NER
            confidence_threshold: Minimum confidence for entity detection
            device: Device to run model on (cuda/cpu)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.nlp = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                aggregation_strategy="max"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load BERT model {model_name}: {e}")
    
    def detect(self, text: str) -> List[Span]:
        """Detect entities using BERT NER"""
        try:
            # Handle long texts by chunking
            chunks = self._chunk_text(text, max_length=512)
            all_spans = []
            
            offset = 0
            for chunk in chunks:
                entities = self.nlp(chunk)
                
                for entity in entities:
                    if entity['score'] >= self.confidence_threshold:
                        label = self._map_bert_label(entity['entity_group'])
                        if label:
                            span = Span(
                                start=entity['start'] + offset,
                                end=entity['end'] + offset,
                                label=label,
                                score=entity['score'],
                                source="bert"
                            )
                            all_spans.append(span)
                
                offset += len(chunk)
            
            return all_spans
            
        except Exception as e:
            # Graceful degradation
            print(f"BERT detection failed: {e}")
            return []
    
    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into chunks that fit within model's max length"""
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks or [text[:max_length]]
    
    def _map_bert_label(self, bert_label: str) -> Optional[str]:
        """Map BERT entity labels to our standardized labels"""
        # Remove B- and I- prefixes from BIO tagging
        clean_label = bert_label.replace('B-', '').replace('I-', '')
        
        mapping = {
            "PER": "PERSON_NAME",
            "PERSON": "PERSON_NAME", 
            "ORG": "ORGANIZATION",
            "LOC": "LOCATION",
            "MISC": "MISC",
            "GPE": "LOCATION",
            "DATE": "DATE",
            "TIME": "TIME",
            "MONEY": "FINANCIAL",
            "PERCENT": "PERCENTAGE",
            "FACILITY": "LOCATION",
            "PRODUCT": "PRODUCT",
            "EVENT": "EVENT",
            "WORK_OF_ART": "WORK_OF_ART",
            "LAW": "LEGAL",
            "LANGUAGE": "LANGUAGE",
            "NORP": "NATIONALITY"
        }
        
        return mapping.get(clean_label.upper(), clean_label)

class ContextualDetector(Detector):
    """Context-aware detector that uses surrounding text to improve accuracy"""
    
    name = "contextual"
    
    def __init__(self, base_detector: Detector, context_window: int = 50):
        """
        Initialize contextual detector
        
        Args:
            base_detector: Base detector to enhance with context
            context_window: Number of characters around entity to consider
        """
        self.base_detector = base_detector
        self.context_window = context_window
        
        # Context patterns that increase confidence
        self.context_patterns = {
            "PERSON_NAME": [
                r"\b(mr|mrs|ms|dr|prof|patient|client|employee)\b",
                r"\b(born|dob|age)\b",
                r"\b(contact|call|email|phone)\b"
            ],
            "MEDICAL_RECORD": [
                r"\b(patient|medical|record|chart|diagnosis)\b",
                r"\b(hospital|clinic|doctor|physician)\b",
                r"\b(treatment|medication|prescription)\b"
            ],
            "FINANCIAL": [
                r"\b(account|payment|transaction|balance)\b",
                r"\b(bank|credit|debit|invoice)\b",
                r"\$([\d,]+\.?\d*)"
            ]
        }
    
    def detect(self, text: str) -> List[Span]:
        """Detect entities with context enhancement"""
        base_spans = self.base_detector.detect(text)
        enhanced_spans = []
        
        for span in base_spans:
            # Extract context around the entity
            start_ctx = max(0, span.start - self.context_window)
            end_ctx = min(len(text), span.end + self.context_window)
            context = text[start_ctx:end_ctx].lower()
            
            # Calculate context-enhanced confidence
            enhanced_score = self._calculate_contextual_score(span, context)
            
            enhanced_span = Span(
                start=span.start,
                end=span.end,
                label=span.label,
                score=enhanced_score,
                source=f"{span.source}_contextual"
            )
            enhanced_spans.append(enhanced_span)
        
        return enhanced_spans
    
    def _calculate_contextual_score(self, span: Span, context: str) -> float:
        """Calculate confidence score based on context"""
        base_score = span.score
        context_boost = 0.0
        
        # Check for relevant context patterns
        patterns = self.context_patterns.get(span.label, [])
        for pattern in patterns:
            import re
            if re.search(pattern, context, re.IGNORECASE):
                context_boost += 0.1
        
        # Penalize if entity appears in unlikely contexts
        penalty_patterns = {
            "PERSON_NAME": [r"\b(table|column|field|variable)\b"],
            "DATE": [r"\b(version|build|release)\b"]
        }
        
        penalties = penalty_patterns.get(span.label, [])
        for pattern in penalties:
            import re
            if re.search(pattern, context, re.IGNORECASE):
                context_boost -= 0.2
        
        return min(1.0, max(0.1, base_score + context_boost))