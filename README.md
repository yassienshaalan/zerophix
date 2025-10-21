# ZeroPHI PoC

De-identify clinical text then re-target safe medical entities using OpenMed models.

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .
export ZEROPHI_SALT="change-me"
uvicorn zerophi.server.app:app --reload
```

Test:
```bash
curl -s -X POST localhost:8000/deid  -H 'Content-Type: application/json'  -d '{"text":"John Smith (DOB 02/11/1956) at 12 King St, Austin. Dx melanoma. Started pembrolizumab 200mg."}' | jq
```

## Python usage
```python
from zerophi import ZeroPHI, Config
zp = ZeroPHI(Config())
out = zp.process("John Smith, 67, started pembrolizumab 200mg on 02/11/2024")
print(out.text)
print(out.entities)
```

## Notes
- PoC uses regex PHI detector + OpenMed disease wrapper (lazy-loaded HF pipeline).
- Overlap resolution gives precedence to PHI spans.
- PHI actions: redact | remove | mask | pseudonymize (default).
- Retargeting: inline minimal tags + sidecar JSON entities.
