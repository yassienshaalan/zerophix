import regex as re, yaml, csv, os
from ..types import Span, Doc
class RegexDetector:
    def __init__(self, label_prefix, builtin_packs, custom_files, detector_id):
        self.label_prefix=label_prefix; self.detector_id=detector_id; pats=[]
        bank={
          "global_core":[("EMAIL",r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
                         ("PHONE",r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{2,4}\)|\d{2,4})[-.\s]?\d{3}[-.\s]?\d{3,4}\b"),
                         ("IPV4",r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"),
                         ("DATE",r"\b(?:\d{1,2}[/-]){2}\d{2,4}\b"),
                         ("URL",r"\bhttps?://[^\s]+"),("ADDRESS",r"\b\d+\s+[A-Za-z][A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Ln|Lane)\b"),
                         ("NAME_HINT",r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")],
          "au_ids":[("TFN",r"\b\d{3}\s?\d{3}\s?\d{3}\b"),("ABN",r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b"),("MEDICARE",r"\b\d{4}\s?\d{5}\s?\d\b")],
          "psi_corporate":[("API_KEY",r"\b[A-Za-z0-9_\-]{20,}\b"),("INTERNAL_HOST",r"\b([a-z0-9\-]+\.)+(corp|internal|intra|svc)\b"),("FILEPATH",r"(?:[A-Za-z]:)?[\\/](?:[^\s\\/]+[\\/])+[^\s\\/]+")]
        }
        for pack in (builtin_packs or []): pats += [(f"{label_prefix}.{n}", re.compile(p)) for n,p in bank.get(pack,[])]
        for path in (custom_files or []):
            if path and os.path.exists(path):
                if path.endswith(('.yaml','.yml')): 
                    for it in yaml.safe_load(open(path,'r',encoding='utf-8')): pats.append((it['label'], re.compile(it['pattern'])))
                elif path.endswith('.csv'):
                    import csv
                    for r in csv.DictReader(open(path, newline='', encoding='utf-8')): pats.append((r['label'], re.compile(r['pattern'])))
        self._pats=pats
    def detect(self, doc:Doc):
        spans=[]; 
        for label,pat in self._pats:
            for m in pat.finditer(doc.text):
                spans.append(Span(m.start(), m.end(), label, m.group(0), 0.99, "regex", {}))
        return spans
