from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import os

DEFAULT_MODELS_DIR = os.environ.get("ZEROPHI_MODELS_DIR", os.path.expanduser("~/.cache/zerophi/models"))

class RedactionConfig(BaseModel):
    country: str = Field(default="AU", description="Country code for policy selection")
    company: Optional[str] = Field(default=None, description="Optional company policy overlay name")
    detectors: List[str] = Field(default_factory=lambda: ["regex", "ner"], description="Order of detectors to apply")
    use_openmed: bool = Field(default=False, description="Enable OpenMed model detector (downloads on demand)")
    models_dir: str = Field(default=DEFAULT_MODELS_DIR, description="Where optional models are cached")
    thresholds: Dict[str, float] = Field(default_factory=lambda: {"ner_conf": 0.50}, description="Detector thresholds")
    masking_style: str = Field(default="hash", description="mask|replace|hash|brackets")
    keep_surrogates: bool = Field(default=False, description="Keep synthetic placeholders rather than removing")
    allowlist: List[str] = Field(default_factory=list, description="Terms never to redact")
