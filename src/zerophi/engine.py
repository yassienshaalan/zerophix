import os, json
from .types import Doc, Result
from .detectors.regex_custom import RegexDetector
from .detectors.openmed_local import OpenMedLocalDetector
from .resolvers.overlap import resolve_overlaps
from .transformers.redact import apply_spans
from .transformers.retarget import inline_minimal, to_sidecar
class ZeroPHIEngine:
    def __init__(self,cfg):
        self.cfg=cfg
        if cfg.get("engine",{}).get("offline",True): os.environ["TRANSFORMERS_OFFLINE"]="1"
        self.detectors=[]; self._init_detectors(); self.precedence=cfg["engine"]["precedence"]
    def _init_detectors(self):
        if self.cfg.get("pii",{}).get("enabled",False):
            r=self.cfg["pii"]["detectors"]["regex"]
            self.detectors.append(RegexDetector("PII", r.get("builtin_packs"), r.get("custom_files"), "pii_regex:v1"))
        if self.cfg.get("phi",{}).get("enabled",False):
            om=self.cfg["phi"]["detectors"].get("openmed",{})
            def add(k,out):
                ent=om.get(k,{}); lp=ent.get("local_path")
                if lp: self.detectors.append(OpenMedLocalDetector(out, lp, ent.get("min_conf",0.6)))
            add("disease","DISEASE"); add("drug","DRUG"); add("gene","GENE"); add("species","SPECIES")
        if self.cfg.get("psi",{}).get("enabled",False):
            r=self.cfg["psi"]["detectors"]["regex"]
            self.detectors.append(RegexDetector("PSI", r.get("builtin_packs"), r.get("custom_files"), "psi_regex:v1"))
    def _priority(self,label):
        for idx,pat in enumerate(self.precedence):
            if pat.endswith(".*") and label.startswith(pat[:-2]): return 1000-idx
            if pat==label: return 1000-idx
        return 1
    def process(self,text):
        raw=[]; doc=Doc(text=text,spans=[])
        for det in self.detectors:
            try: raw += det.detect(doc)
            except Exception: pass
        spans=resolve_overlaps(raw, self._priority)
        pii=[s for s in spans if s.label.startswith("PII.")]
        phi=[s for s in spans if s.label.startswith("PHI.")]
        psi=[s for s in spans if s.label.startswith("PSI.")]
        clinical=[s for s in spans if not s.label.startswith(("PII.","PHI.","PSI."))]
        out=text; audit=[]
        if self.cfg.get("pii",{}).get("enabled",False) and pii:
            out,a=apply_spans(out, pii, self.cfg["pii"]["mode"], "ZEROPHI_SALT", self.cfg["pii"]["format_preserving"]); audit+=a
        if self.cfg.get("phi",{}).get("enabled",False) and phi:
            out,a=apply_spans(out, phi, self.cfg["phi"]["mode"], "ZEROPHI_SALT", True); audit+=a
        if self.cfg.get("psi",{}).get("enabled",False) and psi:
            out,a=apply_spans(out, psi, self.cfg["psi"]["mode"], "ZEROPHI_SALT", False); audit+=a
        out=inline_minimal(out, clinical); ents=to_sidecar(clinical) if self.cfg["outputs"]["sidecar_entities"] else []
        ap=self.cfg["outputs"].get("audit_log_path")
        if ap:
            os.makedirs(os.path.dirname(ap), exist_ok=True)
            with open(ap,"a",encoding="utf-8") as f:
                for e in audit: f.write(json.dumps(e, ensure_ascii=False)+"\n")
        return Result(text=out, entities=ents, audit=audit)
