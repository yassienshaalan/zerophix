import os
from pathlib import Path
from typing import Optional

REGISTRY = {
    "openmed-base": {
        "hf_repo": "StanfordAIMI/OpenMed-NER-base",
        "type": "transformers",
        "size": "400MB",
        "license": "Apache-2.0",
    },
    "openmed-large": {
        "hf_repo": "StanfordAIMI/OpenMed-NER-large",
        "type": "transformers",
        "size": "1.2GB",
        "license": "Apache-2.0",
    },
}

def ensure_model(name: str, models_dir: Optional[str] = None) -> str:
    models_root = Path(models_dir or os.environ.get("ZEROPHI_MODELS_DIR", Path.home() / ".cache" / "zerophi" / "models"))
    models_root.mkdir(parents=True, exist_ok=True)
    target = models_root / name
    if target.exists() and (target / "config.json").exists():
        return str(target)
    try:
        import subprocess, sys
        repo = REGISTRY[name]["hf_repo"]
        subprocess.check_call([sys.executable, "-m", "huggingface_hub", "snapshot_download", "--repo-id", repo, "--local-dir", str(target), "--local-dir-use-symlinks", "False"])
        return str(target)
    except Exception as e:
        raise RuntimeError(f"Model '{name}' not found locally and auto-download failed. Install 'huggingface_hub' or pre-download the repo {REGISTRY[name]['hf_repo']} into {target}. Error: {e}")
