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
    import os
    from huggingface_hub import snapshot_download
    # Force cache inside repo
    repo_root = os.path.abspath(os.path.join(out_dir, "..", ".."))
    hf_home = os.path.join(repo_root, "local_models", ".hf")
    hf_cache = os.path.join(repo_root, "local_models", ".cache")
    os.makedirs(hf_home, exist_ok=True)
    os.makedirs(hf_cache, exist_ok=True)
    os.environ["HF_HOME"] = hf_home
    os.environ["TRANSFORMERS_CACHE"] = hf_cache
    os.environ["HF_DATASETS_CACHE"] = hf_cache

    # Download entire repo snapshot (no torch required)
    snapshot_download(repo_id, local_dir=out_dir, ignore_patterns=["*.h5", "*.msgpack"])
    print(f"[get_tier] saved snapshot to {out_dir}")


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
