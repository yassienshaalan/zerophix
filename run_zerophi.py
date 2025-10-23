import argparse, os, json, sys
from zerophi.config_loader import load_config
from zerophi.engine import ZeroPHIEngine
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["offline","online"], default="offline")
    ap.add_argument("--allow-download", action="store_true")
    ap.add_argument("--tier", choices=["A","B","C"], default="A")
    ap.add_argument("--input", default="data/docs.sample.jsonl")
    ap.add_argument("--out_json", default="outputs/deid.output.jsonl")
    ap.add_argument("--out_audit", default="outputs/deid.audit.jsonl")
    ap.add_argument("--config", default="configs/offline.au.yaml")
    args = ap.parse_args()
    if args.mode == "online" or args.allow_download:
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        os.system(f"{sys.executable} scripts/bootstrap_models.py --config {args.config} --tier {args.tier} --mode {args.mode} " + ("--allow-download" if args.allow_download else ""))
    else:
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    os.makedirs(os.path.dirname(args.out_audit), exist_ok=True)
    cfg = load_config(args.config); eng = ZeroPHIEngine(cfg)
    cnt=0
    with open(args.input,"r",encoding="utf-8") as fin, open(args.out_json,"w",encoding="utf-8") as fout, open(args.out_audit,"w",encoding="utf-8") as faud:
        for line in fin:
            if not line.strip(): continue
            row = json.loads(line); out = eng.process(row["text"]); cnt += 1
            fout.write(json.dumps({"id": row.get("id"), "text": out.text, "entities": out.entities}, ensure_ascii=False)+"\n")
            for evt in out.audit:
                evt_row = {"id": row.get("id"), **evt}; faud.write(json.dumps(evt_row, ensure_ascii=False)+"\n")
    print(f"Processed {cnt} docs."); print(f"Wrote {args.out_json} and {args.out_audit}")
if __name__ == "__main__": main()
