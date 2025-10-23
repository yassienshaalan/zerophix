def inline_minimal(text, clinical_spans):
    ents=sorted(clinical_spans, key=lambda s: s.start); offset=0
    for s in ents:
        start=s.start+offset; end=s.end+offset; tag=f"[{s.label}: {s.text}]"
        text=text[:start]+tag+text[end:]; offset += len(tag)-(end-start)
    return text
def to_sidecar(spans):
    return [{"type":s.label,"text":s.text,"start":s.start,"end":s.end,"confidence":s.confidence,"detector":s.detector} for s in spans]
