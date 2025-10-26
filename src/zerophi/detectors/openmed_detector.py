
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
            top_k=None,
            batch_size=batch_size,
            truncation=True
        )
        self.conf = conf
        self.enable_assertion = enable_assertion

    # detect() as you have, optionally filter negated if enable_assertion
