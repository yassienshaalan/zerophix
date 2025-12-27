import importlib
from .base import Detector
from zerophix.models.manager import ensure_model

class OpenMedDetector(Detector):
    def __init__(self, model_name="openmed-base", models_dir=None, conf=0.5,
                 max_seq_len=512, batch_size=8, device="auto", lora_adapter_id=None,
                 enable_assertion=False):
        path = ensure_model(model_name, models_dir=models_dir)
        tr = importlib.import_module("transformers")

        # device map
        kwargs = {}
        if device != "auto":
            kwargs["device_map"] = {"": 0} if device == "cuda" else "cpu"

        self.tokenizer = tr.AutoTokenizer.from_pretrained(path)
        self.model = tr.AutoModelForTokenClassification.from_pretrained(path, **kwargs)

        # Optional: load LoRA adapter
        if lora_adapter_id:
            peft = importlib.import_module("peft")
            self.model = peft.PeftModel.from_pretrained(self.model, lora_adapter_id)

        self.pipe = tr.pipeline(
            "token-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            # top_k=None,  # Removed as it causes TypeError in newer transformers
            batch_size=batch_size,
            # truncation=True # Removed as it causes TypeError in newer transformers
        )
        self.conf = conf
        self.enable_assertion = enable_assertion

    def detect(self, text: str):
        from .base import Span
        results = self.pipe(text)
        spans = []
        # results is a list of dicts or list of lists of dicts
        # If batch_size > 1 and we passed a list, it would be list of lists.
        # Here we pass a single string, so it's a list of dicts.
        
        # Handle case where pipeline returns list of lists (sometimes happens with aggregation)
        if results and isinstance(results[0], list):
            results = results[0]

        for r in results:
            # r: {'entity_group': 'LABEL', 'score': 0.99, 'word': 'foo', 'start': 0, 'end': 3}
            # or {'entity': 'LABEL', ...} depending on aggregation
            label = r.get("entity_group", r.get("entity"))
            score = r.get("score")
            start = r.get("start")
            end = r.get("end")
            
            if score < self.conf:
                continue
                
            spans.append(Span(start, end, label, score, "openmed"))
            
        return spans
