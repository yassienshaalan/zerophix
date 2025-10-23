from ..types import Span, Doc
import os
class OpenMedLocalDetector:
    def __init__(self,label,local_path,min_conf=0.6,aggregation_strategy='simple'):
        self.label=label; self.local_path=local_path; self.min_conf=min_conf; self.aggregation_strategy=aggregation_strategy; self._pipe=None
        self._available = os.path.isdir(local_path) if local_path else False
    def _ensure_pipe(self):
        if self._pipe is None:
            try:
                from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
                tok = AutoTokenizer.from_pretrained(self.local_path, local_files_only=True)
                mdl = AutoModelForTokenClassification.from_pretrained(self.local_path, local_files_only=True)
                self._pipe = pipeline('token-classification', model=mdl, tokenizer=tok, aggregation_strategy=self.aggregation_strategy)
            except Exception: self._available=False
    def detect(self, doc:Doc):
        if not self._available: return []
        self._ensure_pipe(); 
        if not self._pipe: return []
        out=self._pipe(doc.text); spans=[]
        for ent in out:
            sc=float(ent.get('score',0.0))
            if sc<self.min_conf: continue
            spans.append(Span(int(ent['start']), int(ent['end']), self.label, ent['word'], sc, f'openmed_local:{self.local_path}', {}))
        return spans
