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


class APIConfig(BaseModel):
    """Configuration for the ZeroPhi REST API server"""
    
    # Server settings
    host: str = Field(
        default=os.environ.get("ZEROPHIX_API_HOST", "127.0.0.1"),
        description="Host to bind the API server to (e.g., '0.0.0.0' for all interfaces)"
    )
    port: int = Field(
        default=int(os.environ.get("ZEROPHIX_API_PORT", "8000")),
        description="Port to bind the API server to"
    )
    workers: int = Field(
        default=int(os.environ.get("ZEROPHIX_API_WORKERS", "1")),
        description="Number of worker processes (for production deployment)"
    )
    reload: bool = Field(
        default=os.environ.get("ZEROPHIX_API_RELOAD", "false").lower() == "true",
        description="Enable auto-reload on code changes (development only)"
    )
    
    # CORS settings
    cors_enabled: bool = Field(
        default=os.environ.get("ZEROPHIX_CORS_ENABLED", "true").lower() == "true",
        description="Enable CORS middleware"
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: os.environ.get(
            "ZEROPHIX_CORS_ORIGINS", "*"
        ).split(",") if os.environ.get("ZEROPHIX_CORS_ORIGINS") else ["*"],
        description="Allowed CORS origins (comma-separated in env var)"
    )
    cors_credentials: bool = Field(
        default=os.environ.get("ZEROPHIX_CORS_CREDENTIALS", "true").lower() == "true",
        description="Allow credentials in CORS requests"
    )
    cors_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods for CORS"
    )
    cors_headers: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed headers for CORS"
    )
    
    # Security settings
    api_key_header: str = Field(
        default="Authorization",
        description="HTTP header name for API key authentication"
    )
    require_auth: bool = Field(
        default=os.environ.get("ZEROPHIX_REQUIRE_AUTH", "false").lower() == "true",
        description="Require authentication for all endpoints"
    )
    api_keys: List[str] = Field(
        default_factory=lambda: os.environ.get("ZEROPHIX_API_KEYS", "").split(",") if os.environ.get("ZEROPHIX_API_KEYS") else [],
        description="Valid API keys (comma-separated in env var)"
    )
    
    # TLS/SSL settings
    ssl_enabled: bool = Field(
        default=os.environ.get("ZEROPHIX_SSL_ENABLED", "false").lower() == "true",
        description="Enable SSL/TLS"
    )
    ssl_keyfile: Optional[str] = Field(
        default=os.environ.get("ZEROPHIX_SSL_KEYFILE"),
        description="Path to SSL private key file"
    )
    ssl_certfile: Optional[str] = Field(
        default=os.environ.get("ZEROPHIX_SSL_CERTFILE"),
        description="Path to SSL certificate file"
    )
    ssl_ca_certs: Optional[str] = Field(
        default=os.environ.get("ZEROPHIX_SSL_CA_CERTS"),
        description="Path to CA certificates file"
    )
    
    # Deployment settings
    environment: str = Field(
        default=os.environ.get("ZEROPHIX_ENV", "development"),
        description="Deployment environment: development, staging, production"
    )
    log_level: str = Field(
        default=os.environ.get("ZEROPHIX_LOG_LEVEL", "info"),
        description="Logging level: debug, info, warning, error, critical"
    )
    access_log: bool = Field(
        default=os.environ.get("ZEROPHIX_ACCESS_LOG", "true").lower() == "true",
        description="Enable access logging"
    )
    
    # API documentation settings
    docs_enabled: bool = Field(
        default=os.environ.get("ZEROPHIX_DOCS_ENABLED", "true").lower() == "true",
        description="Enable /docs and /redoc endpoints"
    )
    docs_url: Optional[str] = Field(
        default="/docs" if os.environ.get("ZEROPHIX_DOCS_ENABLED", "true").lower() == "true" else None,
        description="URL path for OpenAPI docs"
    )
    redoc_url: Optional[str] = Field(
        default="/redoc" if os.environ.get("ZEROPHIX_DOCS_ENABLED", "true").lower() == "true" else None,
        description="URL path for ReDoc documentation"
    )
    
    # Performance settings
    max_request_size: int = Field(
        default=int(os.environ.get("ZEROPHIX_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),  # 10 MB
        description="Maximum request size in bytes"
    )
    timeout: int = Field(
        default=int(os.environ.get("ZEROPHIX_TIMEOUT", "60")),
        description="Request timeout in seconds"
    )
    keep_alive: int = Field(
        default=int(os.environ.get("ZEROPHIX_KEEP_ALIVE", "5")),
        description="Keep-alive timeout in seconds"
    )
    
    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=os.environ.get("ZEROPHIX_RATE_LIMIT_ENABLED", "false").lower() == "true",
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=int(os.environ.get("ZEROPHIX_RATE_LIMIT_REQUESTS", "100")),
        description="Maximum requests per time window"
    )
    rate_limit_window: int = Field(
        default=int(os.environ.get("ZEROPHIX_RATE_LIMIT_WINDOW", "60")),
        description="Rate limit time window in seconds"
    )
    
    # Proxy settings (for deployment behind reverse proxy)
    proxy_headers: bool = Field(
        default=os.environ.get("ZEROPHIX_PROXY_HEADERS", "false").lower() == "true",
        description="Trust X-Forwarded-* headers (enable when behind proxy)"
    )
    forwarded_allow_ips: Optional[str] = Field(
        default=os.environ.get("ZEROPHIX_FORWARDED_ALLOW_IPS", "*"),
        description="Allowed IPs for forwarded headers"
    )
    
    class Config:
        extra = "allow"  # Allow additional configuration options
