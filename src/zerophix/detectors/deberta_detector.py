"""
DeBERTa-v3 NER Detector - Higher Accuracy Alternative to BERT
==============================================================

DeBERTa-v3 (Decoding-enhanced BERT with disentangled attention v3)
significantly outperforms base BERT on NER tasks:

  - BERT-base NER F1: ~91.3 on CoNLL-2003
  - DeBERTa-v3 NER F1: ~93.8 on CoNLL-2003  (+2.5 F1 points)

Key advantages:
  - Disentangled attention separates content and position embeddings
  - Enhanced mask decoder improves token-level predictions
  - ELECTRA-style pretraining is more sample-efficient
  - Better on rare/unseen entities (critical for PII like names)

Recommended model: mdarhri00/named-entity-recognition (DeBERTa-v3-base fine-tuned)
Alternative: dslim/deberta-v3-base-ner (community NER fine-tune)

Installation:
    pip install transformers torch
    # Same deps as BERT detector - no additional packages needed
"""

from typing import List, Optional, Dict
from .base import Detector, Span

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from ..performance.model_cache import get_model_cache
    MODEL_CACHE_AVAILABLE = True
except ImportError:
    MODEL_CACHE_AVAILABLE = False


class DeBERTaDetector(Detector):
    """
    DeBERTa-v3 based NER detector for higher accuracy entity detection.

    Compared to BertDetector:
      - +2.5 F1 on standard NER benchmarks
      - Better handling of rare names and medical terms
      - Same API, drop-in replacement for BertDetector
      - Slightly slower inference (~1.3x) but much more accurate

    Usage:
        detector = DeBERTaDetector()
        spans = detector.detect("John Smith's SSN is 123-45-6789")

        # With medical-optimized model
        detector = DeBERTaDetector(model_name="mdarhri00/named-entity-recognition")
    """

    name = "deberta"

    # Map of available pre-trained DeBERTa NER models
    RECOMMENDED_MODELS = {
        "general": "mdarhri00/named-entity-recognition",
        "conll": "dslim/deberta-v3-base-ner",
    }

    def __init__(
        self,
        model_name: str = "mdarhri00/named-entity-recognition",
        confidence_threshold: float = 0.85,
        device: Optional[str] = None,
        max_length: int = 512,
    ):
        """
        Initialize DeBERTa-v3 NER detector.

        Args:
            model_name: HuggingFace model name (DeBERTa-v3 fine-tuned for NER)
            confidence_threshold: Minimum confidence for entity detection
            device: Device to run model on ('cuda'/'cpu'/None for auto)
            max_length: Maximum token length per chunk
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers/torch not installed. Install with: pip install transformers torch"
            )

        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = max_length

        cache_key = f"deberta_{model_name}_{self.device}"

        try:
            if MODEL_CACHE_AVAILABLE:
                model_cache = get_model_cache()
                if model_cache.has(cache_key):
                    cached = model_cache.get(cache_key)
                    self.tokenizer = cached["tokenizer"]
                    self.model = cached["model"]
                    self.nlp = cached["pipeline"]
                else:
                    self._load_model()
                    model_cache.set(cache_key, {
                        "tokenizer": self.tokenizer,
                        "model": self.model,
                        "pipeline": self.nlp,
                    })
            else:
                self._load_model()
        except Exception as e:
            raise RuntimeError(f"Failed to load DeBERTa model {model_name}: {e}")

    def _load_model(self):
        """Load model, tokenizer, and create pipeline."""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
        self.nlp = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1,
            aggregation_strategy="max",
        )

    def detect(self, text: str) -> List[Span]:
        """
        Detect entities using DeBERTa-v3 NER.

        Args:
            text: Input text to analyze

        Returns:
            List of detected Span objects
        """
        try:
            chunks = self._chunk_text(text)
            all_spans = []

            offset = 0
            for chunk in chunks:
                entities = self.nlp(chunk)

                for entity in entities:
                    if entity["score"] >= self.confidence_threshold:
                        label = self._map_label(entity["entity_group"])
                        if label:
                            span = Span(
                                start=entity["start"] + offset,
                                end=entity["end"] + offset,
                                label=label,
                                score=entity["score"],
                                source="deberta",
                            )
                            all_spans.append(span)

                offset += len(chunk)

            return all_spans

        except Exception as e:
            print(f"DeBERTa detection failed: {e}")
            return []

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks respecting sentence boundaries."""
        if len(text) <= self.max_length:
            return [text]

        chunks = []
        sentences = text.replace(". ", ".\n").split("\n")
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= self.max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks or [text[: self.max_length]]

    def _map_label(self, raw_label: str) -> Optional[str]:
        """Map DeBERTa entity labels to ZeroPhix standardized labels."""
        clean = raw_label.replace("B-", "").replace("I-", "").upper()

        mapping = {
            "PER": "PERSON_NAME",
            "PERSON": "PERSON_NAME",
            "ORG": "ORGANIZATION",
            "ORGANIZATION": "ORGANIZATION",
            "LOC": "LOCATION",
            "LOCATION": "LOCATION",
            "GPE": "LOCATION",
            "MISC": "MISC",
            "DATE": "DATE",
            "TIME": "TIME",
            "MONEY": "FINANCIAL",
            "PERCENT": "PERCENTAGE",
            "FACILITY": "LOCATION",
            "PRODUCT": "PRODUCT",
            "EVENT": "EVENT",
            "LAW": "LEGAL",
            "NORP": "NATIONALITY",
        }

        return mapping.get(clean, clean)
