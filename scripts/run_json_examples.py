import os, json, glob, argparse, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="examples", help="Directory containing *.json inputs")
    ap.add_argument("--models-dir", default=None, help="Optional model cache (e.g., /mnt/sda15/zerophix_models)")
    args = ap.parse_args()

    try:
        from zerophix.config import RedactionConfig
        from zerophix.pipelines.redaction import RedactionPipeline
    except ModuleNotFoundError:
        sys.path.insert(0, "src")
        from zerophix.config import RedactionConfig
        from zerophix.pipelines.redaction import RedactionPipeline

    files = sorted(glob.glob(os.path.join(args.dir, "*.json")))
    if not files:
        print(f"No JSON files found in {args.dir}")
        sys.exit(1)

    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            spec = json.load(fh)
        md = args.models_dir or os.environ.get("ZEROPHI_MODELS_DIR")
        cfg_kwargs = dict(
            country=spec.get("country","AU"),
            company=spec.get("company"),
            use_openmed=bool(spec.get("use_openmed", False)),
            masking_style=spec.get("masking_style","hash"),
        )
        if md:
            cfg_kwargs["models_dir"] = md  # only set when a string exists
        cfg = RedactionConfig(**cfg_kwargs)

        pipe = RedactionPipeline.from_config(cfg)
        out = pipe.redact(spec["text"])
        print("\n=== File:", f, "===")
        print(json.dumps({"id": spec.get("id"), "result": out}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
