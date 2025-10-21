from typing import List
from .types import Doc, Span, Result
from .policy import Config
from .detectors.phi_regex import PHIRegexDetector
from .detectors.openmed import OpenMedDetector
from .resolvers.overlap import resolve_overlaps
from .transformers.redact import apply_phi
from .transformers.retarget import inline_minimal, to_sidecar

class ZeroPHI:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.phi_det = PHIRegexDetector()
        self.om_detectors: List[OpenMedDetector] = []
        if cfg.openmed.disease:
            self.om_detectors.append(OpenMedDetector("DISEASE", cfg.openmed.disease.model_id, cfg.openmed.disease.min_conf, cfg.openmed.disease.aggregation_strategy))
        if cfg.openmed.drug:
            self.om_detectors.append(OpenMedDetector("DRUG", cfg.openmed.drug.model_id, cfg.openmed.drug.min_conf, cfg.openmed.drug.aggregation_strategy))
        if cfg.openmed.gene:
            self.om_detectors.append(OpenMedDetector("GENE", cfg.openmed.gene.model_id, cfg.openmed.gene.min_conf, cfg.openmed.gene.aggregation_strategy))
        if cfg.openmed.species:
            self.om_detectors.append(OpenMedDetector("SPECIES", cfg.openmed.species.model_id, cfg.openmed.species.min_conf, cfg.openmed.species.aggregation_strategy))

    def process(self, text: str) -> Result:
        doc = Doc(text=text, spans=[])
        spans: List[Span] = []
        spans += self.phi_det.detect(doc)
        for det in self.om_detectors:
            spans += det.detect(doc)
        spans = resolve_overlaps(spans)
        redacted_text, audit = apply_phi(doc, spans, self.cfg.phi.mode, self.cfg.phi.pseudonym.salt_env_var, self.cfg.phi.pseudonym.format_preserving)
        if self.cfg.retarget.mode == "sidecar_only":
            final_text = redacted_text
        else:
            final_text = inline_minimal(redacted_text, spans)
        entities = to_sidecar(spans) if self.cfg.outputs.sidecar_entities else []
        return Result(text=final_text, entities=entities, audit=audit)
