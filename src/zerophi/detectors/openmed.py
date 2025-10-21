from typing import List
from ..types import Span, Doc

class OpenMedDetector:
    def __init__(self, label: str, model_id: str, min_conf: float = 0.6, aggregation_strategy: str = "simple"):
        self.label = label
        self.model_id = model_id
        self.min_conf = min_conf
        self.aggregation_strategy = aggregation_strategy
        self._pipe = None

    def _ensure_pipe(self):
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline(
                "token-classification",
                model=self.model_id,
                aggregation_strategy=self.aggregation_strategy
            )

    def detect(self, doc: Doc) -> List[Span]:
        self._ensure_pipe()
        out = self._pipe(doc.text)
        spans: List[Span] = []
        for ent in out:
            score = float(ent.get("score", 0))
            if score < self.min_conf:
                continue
            start = int(ent["start"]); end = int(ent["end"]); text = ent["word"]
            spans.append(Span(start, end, self.label, text, score, f"openmed:{self.model_id}", {}))
        return spans
