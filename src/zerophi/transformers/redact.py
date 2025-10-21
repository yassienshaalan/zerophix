import hashlib
import os
from typing import List, Tuple
from ..types import Span, Doc

def _hmac_token(value: str, salt_env_var: str) -> str:
    salt = os.environ.get(salt_env_var, "dev-salt")
    dig = hashlib.sha256((salt + value).encode()).hexdigest()[:10]
    return dig.upper()

def apply_phi(doc: Doc, spans: List[Span], mode: str, salt_env_var: str, format_preserving: bool) -> Tuple[str, List[dict]]:
    text = doc.text
    audit = []
    offset = 0
    spans_by_start = sorted([s for s in spans if s.label.startswith("PHI.")], key=lambda s: s.start)
    for s in spans_by_start:
        start = s.start + offset
        end = s.end + offset
        original = text[start:end]
        if mode == "redact":
            repl = f"[{s.label}]"
        elif mode == "remove":
            repl = ""
        elif mode == "mask":
            repl = "X" * len(original)
        else:
            token = _hmac_token(original, salt_env_var)
            if format_preserving and any(c.isdigit() for c in original):
                repl = token[:min(8, len(original))]
            else:
                repl = f"[{s.label}:{token}]"
        text = text[:start] + repl + text[end:]
        delta = len(repl) - (end - start)
        offset += delta
        audit.append({
            "span": [s.start, s.end],
            "label": s.label,
            "detector": s.detector,
            "action": mode,
            "replacement": repl
        })
    return text, audit
