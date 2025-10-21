from pydantic import BaseModel, Field
from typing import Dict, Optional

class PHIPseudonym(BaseModel):
    algorithm: str = Field(default="hmac_sha256")
    salt_env_var: str = Field(default="ZEROPHI_SALT")
    format_preserving: bool = True

class DatePolicy(BaseModel):
    strategy: str = Field(default="shift_by_patient")
    max_shift_days: int = 365

class GeoPolicy(BaseModel):
    generalize_to: str = Field(default="state")

class PHIPolicy(BaseModel):
    mode: str = Field(default="pseudonymize")  # redact|pseudonymize|mask|remove
    min_conf: Dict[str, float] = Field(default_factory=lambda: {"default":0.5})
    pseudonym: PHIPseudonym = PHIPseudonym()
    date_policy: DatePolicy = DatePolicy()
    geo_policy: GeoPolicy = GeoPolicy()
    allowlists: Dict[str, list] = Field(default_factory=lambda: {"terms": []})

class OpenMedModelCfg(BaseModel):
    model_id: str
    min_conf: float = 0.6
    aggregation_strategy: str = "simple"

class OpenMedCfg(BaseModel):
    disease: Optional[OpenMedModelCfg] = None
    drug: Optional[OpenMedModelCfg] = None
    gene: Optional[OpenMedModelCfg] = None
    species: Optional[OpenMedModelCfg] = None

class RetargetCfg(BaseModel):
    mode: str = Field(default="inline_minimal")  # inline_minimal|contextualized|sidecar_only
    ontology_map: Optional[str] = None

class OutputsCfg(BaseModel):
    format: str = Field(default="jsonl")
    sidecar_entities: bool = True
    write_audit_log: bool = True

class Config(BaseModel):
    phi: PHIPolicy = PHIPolicy()
    openmed: OpenMedCfg = OpenMedCfg(
        disease=OpenMedModelCfg(model_id="OpenMed/OpenMed-NER-DiseaseDetect-SuperClinical-434M"),
        drug=None,
        gene=None,
        species=None
    )
    retarget: RetargetCfg = RetargetCfg()
    outputs: OutputsCfg = OutputsCfg()
