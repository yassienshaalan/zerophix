# zerophi

Zero-PII/PHI redaction library with AU-first coverage. It composes **high-precision regex/patterns** with **ML NER models** (e.g., OpenMed) and supports **country/company-specific policies**.

## Highlights
- 🇦🇺 AU-first policy: Medicare #, TFN, ABN/ACN, driver licence, IHI, AU phones/addresses.
- Tiered detectors: `regex` → `ner` → `openmed` (download on demand).
- Pluggable policies: country + company overrides via YAML.
- CLI and Python API.
- Benchmark harness (including an Azure PII Redaction comparison stub).

## Install

Base (regex + core):
```bash
pip install zerophi
```

With OpenMed/Transformers:
```bash
pip install "zerophi[openmed]"
```

With Azure benchmark client:
```bash
pip install "zerophi[azurebench]"
```

## Quickstart
```bash
zerophi redact --text "John Smith DOB 1977-04-02 medicare 2424 12345 1-2" --country AU
```

Python:
```python
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig

cfg = RedactionConfig(country="AU", use_openmed=False)
pipe = RedactionPipeline.from_config(cfg)
print(pipe.redact("Call me on 04 1234 5678; ABN 11 111 111 111"))
```

## Model downloads
Models are **not bundled**. Use:
```bash
zerophi download-model --name openmed-base
```
Downloads to `$ZEROPHI_MODELS_DIR` or `~/.cache/zerophi/models`.

## Policies
See `src/zerophi/policies/au.yml` for AU PII/PHI patterns and actions. Override with a company config in `configs/company/yourco.yml` and pass `--company yourco`.

## Benchmarks
Use `scripts/bench_against_azure.py` (requires `ZEROPHI_AZURE_ENDPOINT` + `ZEROPHI_AZURE_KEY`).
