from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os

DEFAULT_MODELS_DIR = os.environ.get("ZEROPHIX_MODELS_DIR", os.path.expanduser("~/.cache/zerophix/models"))

class RedactionConfig(BaseModel):
    # Core configuration
    country: str = Field(default="AU", description="Country code for policy selection")
    company: Optional[str] = Field(default=None, description="Optional company policy overlay name")
    
    # Detector configuration
    detectors: List[str] = Field(
        default_factory=lambda: ["regex", "custom", "spacy"],
        description="Order of detectors to apply: regex, custom, spacy, bert, openmed, statistical"
    )
    
    # ML Model flags
    use_openmed: bool = Field(default=False, description="Enable OpenMed model detector")
    use_spacy: bool = Field(default=True, description="Enable spaCy NER detector")
    use_bert: bool = Field(default=False, description="Enable BERT-based NER detector")
    use_statistical: bool = Field(default=False, description="Enable statistical pattern detector")
    use_contextual: bool = Field(default=True, description="Use contextual enhancement for ML detectors")
    
    # Advanced Accuracy Features
    enable_ensemble_voting: bool = Field(default=True, description="Enable weighted voting for conflict resolution")
    detector_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "regex": 2.0,      # High precision
            "custom": 2.0,     # User defined
            "openmed": 1.5,    # Specialized
            "bert": 1.2,       # General DL
            "spacy": 1.0,      # General ML
            "statistical": 0.8 # Heuristic
        },
        description="Weights for ensemble voting"
    )
    
    enable_context_propagation: bool = Field(default=True, description="Propagate high-confidence entities across document")
    context_propagation_threshold: float = Field(default=0.90, description="Confidence threshold to trigger propagation")
    
    allow_list: List[str] = Field(default_factory=list, description="List of terms to never redact")
    allow_list_file: Optional[str] = Field(default=None, description="Path to file containing allow-list terms")

    # Model specifications
    spacy_model: str = Field(default="en_core_web_sm", description="spaCy model name")
    bert_model: str = Field(default="dslim/bert-base-NER", description="BERT model for NER")
    models_dir: str = Field(default=DEFAULT_MODELS_DIR, description="Model cache directory")
    
    # Detection thresholds
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "ner_conf": 0.50,
            "bert_conf": 0.90,
            "spacy_conf": 0.80,
            "statistical_conf": 0.70,
            "custom_conf": 0.85
        },
        description="Confidence thresholds for different detectors"
    )
    
    # Redaction strategies
    masking_style: str = Field(
        default="hash",
        description="Default masking style: mask|replace|hash|brackets|encrypt|synthetic|preserve_format"
    )
    
    redaction_policies: Dict[str, str] = Field(
        default_factory=dict,
        description="Entity-specific redaction policies override"
    )
    
    # Processing options
    parallel_detection: bool = Field(default=True, description="Run detectors in parallel")
    use_async: bool = Field(default=False, description="Use async processing pipeline")
    max_workers: int = Field(default=4, description="Maximum worker threads for parallel processing")
    merge_overlapping: bool = Field(default=True, description="Merge overlapping detections")
    
    # Privacy and security
    encryption_key: Optional[bytes] = Field(default=None, description="Encryption key for secure redaction")
    audit_logging: bool = Field(default=True, description="Enable detailed audit logging")
    keep_surrogates: bool = Field(default=False, description="Keep synthetic placeholders")
    
    # Filtering and validation
    allowlist: List[str] = Field(default_factory=list, description="Terms never to redact")
    blocklist: List[str] = Field(default_factory=list, description="Additional terms to always redact")
    min_entity_length: int = Field(default=2, description="Minimum length for entity detection")
    max_entity_length: int = Field(default=100, description="Maximum length for entity detection")
    
    # Performance tuning
    cache_detections: bool = Field(default=True, description="Cache detection results")
    batch_size: int = Field(default=1000, description="Batch size for processing large texts")
    chunk_size: int = Field(default=5000, description="Chunk size for very large documents")
    
    # Custom patterns
    custom_patterns: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Custom regex patterns for specific entity types"
    )
    
    # API and integration settings
    api_timeout: int = Field(default=30, description="API timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed operations")
    
    # Output options
    include_confidence: bool = Field(default=True, description="Include confidence scores in output")
    include_detector_info: bool = Field(default=True, description="Include detector information in output")
    output_format: str = Field(default="json", description="Output format: json|xml|csv")
    
    class Config:
        extra = "allow"  # Allow additional configuration options
