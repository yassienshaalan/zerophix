import os, json
from typing import List, Dict

def azure_redact(text: str) -> Dict:
    import requests
    endpoint = os.environ["ZEROPHIX_AZURE_ENDPOINT"].rstrip("/")
    key = os.environ["ZEROPHIX_AZURE_KEY"]
    url = f"{endpoint}/redact"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"text": text}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def run_benchmark(samples: List[str]) -> List[Dict]:
    from zerophi.config import RedactionConfig
    from zerophi.pipelines.redaction import RedactionPipeline
    pipe = RedactionPipeline.from_config(RedactionConfig(country="AU", use_openmed=False))
    rows = []
    for t in samples:
        ours = pipe.redact(t)
        try:
            azure = azure_redact(t)
        except Exception as e:
            azure = {"error": str(e)}
        rows.append({"text": t, "ours": ours, "azure": azure})
    return rows
