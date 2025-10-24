import os, argparse, yaml, sys, subprocess, traceback

def log(msg): print(f"[bootstrap] {msg}", flush=True)

def ensure_deps():
    try:
        import transformers  # noqa: F401
        log("transformers is available")
    except Exception:
        log("installing transformers>=4.41 …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers>=4.41"])

def need_local_dir(path: str) -> bool:
    return (not path) or (not os.path.isdir(path)) or (not os.listdir(path))

def from_repo_to_local(repo_id: str, local_dir: str):
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    log(f"downloading {repo_id} → {local_dir}")
    tok = AutoTokenizer.from_pretrained(repo_id)
    mdl = AutoModelForTokenClassification.from_pretrained(repo_id)
    os.makedirs(local_dir, exist_ok=True)
    tok.save_pretrained(local_dir); mdl.save_pretrained(local_dir)
    log(f"saved to {local_dir}")

def main():
    ap = argparse.ArgumentParser(description="Prepare local models based on policy config and tier manifest.")
    ap.add_argument("--config", default="configs/offline.au.yaml")
    ap.add_argument("--tiers_yaml", default="configs/tiers.yaml")
    ap.add_argument("--allow-download", action="store_true")
    ap.add_argument("--mode", choices=["offline","online"], default="offline")
    ap.add_argument("--tier", choices=["A","B","C"], default="A")
    args = ap.parse_args()

    log(f"args: mode={args.mode} allow_download={args.allow_download} tier={args.tier}")
    log(f"TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')!r}")
    log(f"HF_HOME={os.environ.get('HF_HOME')!r}")

    # If we're supposed to download, force online for this step only
    if args.mode == "offline" and args.allow_download:
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        log("temporarily set TRANSFORMERS_OFFLINE=0 for download step")

    try:
        cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
        tiers = yaml.safe_load(open(args.tiers_yaml, "r", encoding="utf-8"))["tiers"]
    except Exception as e:
        log(f"failed to read yaml files: {e}")
        sys.exit(1)

    desired = []
    om = cfg.get("phi", {}).get("detectors", {}).get("openmed", {})
    # Collect all local paths referenced by config
    for k in ["disease","drug","gene","species"]:
        ent = om.get(k, {}); lp = ent.get("local_path")
        if lp and isinstance(lp, str):
            desired.append((k, lp))

    missing = [(k, lp) for (k, lp) in desired if need_local_dir(lp)]
    if not missing:
        log("all referenced local model dirs exist; nothing to download")
        return

    # If we cannot download, bail with explicit message
    if args.mode == "offline" and not args.allow_download:
        log("missing local models and downloads disabled (--mode offline, no --allow-download)")
        for k, lp in missing: log(f" - {k}: {lp} (missing)")
        sys.exit(2)

    ensure_deps()

    # Build mapping local_dir_name -> repo_id from tier
    tier_items = tiers.get(args.tier, [])
    repo_map = { it["local_dir"]: it["repo_id"] for it in tier_items }

    # For each missing path, find the repo by matching the basename of the local path
    for k, lp in missing:
        local_dir_name = os.path.basename(lp.rstrip("/\\"))
        repo_id = repo_map.get(local_dir_name)
        if not repo_id:
            log(f"no repo mapping for local dir '{local_dir_name}' in tier {args.tier}; skipping")
            continue
        try:
            from_repo_to_local(repo_id, lp)
        except Exception as e:
            log(f"FAILED downloading {repo_id} → {lp}: {e}")
            traceback.print_exc()
            sys.exit(3)

    log("bootstrap complete.")

if __name__ == "__main__":
    main()
