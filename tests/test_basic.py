from zerophi.config import RedactionConfig
from zerophi.pipelines.redaction import RedactionPipeline

def test_basic_redact():
    cfg = RedactionConfig(country="AU")
    pipe = RedactionPipeline.from_config(cfg)
    out = pipe.redact("Email me at a.b@example.com")
    assert "a.b@example.com" not in out["text"]
