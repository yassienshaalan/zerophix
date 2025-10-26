from typing import List
from .base import Detector, Span
from ..models.manager import ensure_model
import importlib

class OpenMedDetector(Detector):
    name = "openmed"

    def __init__(self, model_name: str = "openmed-base", models_dir: str | None = None, conf: float = 0.50):
        self.model_path = ensure_model(model_name, models_dir=models_dir)
        self.conf = conf
        tr = importlib.import_module("transformers")
        self.pipe = tr.pipeline("token-classification", model=self.model_path, aggregation_strategy="simple")

    def detect(self, text: str) -> List[Span]:
        out = []
        for ent in self.pipe(text):
            score = float(ent.get("score", 0))
            if score < self.conf:
                continue
            out.append(Span(int(ent["start"]), int(ent["end"]), label=str(ent["entity_group"]), score=score, source="openmed"))
        return out
