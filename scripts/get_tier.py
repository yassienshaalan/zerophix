import argparse, os, sys, yaml, subprocess, traceback

def log(msg): print(f"[get_tier] {msg}", flush=True)

def ensure_deps():
    try:
        import transformers  # noqa: F401
        log("transformers is available")
    except Exception:
        log("installing transformers>=4.41 …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers>=4.41"])

def fetch(repo_id: str, out_dir: str):
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    log(f"downloading {repo_id} → {out_dir}")
    tok = AutoTokenizer.from_pretrained(repo_id)
    mdl = AutoModelForTokenClassification.from_pretrained(repo_id)
    os.makedirs(out_dir, exist_ok=True)
    tok.save_pretrained(out_dir); mdl.save_pretrained(out_dir)
    log(f"saved to {out_dir}")

def main():
    ap = argparse.ArgumentParser(description="Download OpenMed tier to local_models/")
    ap.add_argument("--tier", choices=["A","B","C"], default="A")
    ap.add_argument("--tiers_yaml", default="configs/tiers.yaml")
    ap.add_argument("--dest_root", default="local_models")
    args = ap.parse_args()

    # ensure we can download
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    log(f"TRANSFORMERS_OFFLINE set to {os.environ['TRANSFORMERS_OFFLINE']}")
    log(f"HF_HOME={os.environ.get('HF_HOME')!r}")

    ensure_deps()

    spec = yaml.safe_load(open(args.tiers_yaml, "r", encoding="utf-8"))
    items = spec["tiers"].get(args.tier, [])
    if not items:
        log(f"Tier {args.tier} is empty."); sys.exit(1)

    for it in items:
        repo_id = it["repo_id"]; local_dir = os.path.join(args.dest_root, it["local_dir"])
        try:
            fetch(repo_id, local_dir)
        except Exception as e:
            log(f"FAILED: {repo_id} → {local_dir}: {e}")
            traceback.print_exc()
            sys.exit(2)

    log(f"Done. Local models under {args.dest_root}")

if __name__ == "__main__":
    main()
