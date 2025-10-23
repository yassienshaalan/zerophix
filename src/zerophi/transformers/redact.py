import hashlib, os
def _hmac_token(value, salt_var):
    salt=os.environ.get(salt_var, 'dev-salt')
    return hashlib.sha256((salt+value).encode()).hexdigest()[:10].upper()
def apply_spans(text, spans, mode, salt_var, fmt_pres):
    audit=[]; offset=0
    for s in sorted(spans, key=lambda x: x.start):
        start=s.start+offset; end=s.end+offset; original=text[start:end]
        if mode=='redact': repl=f"[{s.label}]"
        elif mode=='remove': repl=""
        elif mode=='mask': repl="X"*len(original)
        else:
            token=_hmac_token(original, salt_var)
            repl = token[:min(8,len(original))] if (fmt_pres and any(c.isdigit() for c in original)) else f"[{s.label}:{token}]"
        text=text[:start]+repl+text[end:]
        offset += len(repl)-(end-start)
        audit.append({"span":[s.start,s.end],"label":s.label,"detector":s.detector,"action":mode,"replacement":repl})
    return text, audit
