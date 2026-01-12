import os
from pathlib import Path
from typing import Optional, Dict, Any, List

REGISTRY = {
    # Aliases (map your old names to valid OpenMed repos)
    "openmed-base": {  # default “base” for your pipeline
        "alias": "openmed-ner-disease-149m"
    },
    "openmed-large": {  # you can point this to a larger/backbone if you like later
        "alias": "openmed-ner-genome-395m"
    },

    # OpenMed domain NERs (VALID repos)
    "openmed-ner-disease-149m": {
        "hf_repo": "OpenMed/OpenMed-NER-DiseaseDetect-ModernClinical-149M",
        "type": "transformers", "task": "token-classification", "size": "149M", "license": "Apache-2.0"
    },
    "openmed-ner-anatomy-149m": {
        "hf_repo": "OpenMed/OpenMed-NER-AnatomyDetect-ModernClinical-149M",
        "type": "transformers", "task": "token-classification", "size": "149M", "license": "Apache-2.0"
    },
    "openmed-ner-pathology-65m": {
        "hf_repo": "OpenMed/OpenMed-NER-PathologyDetect-TinyMed-65M",
        "type": "transformers", "task": "token-classification", "size": "65M", "license": "Apache-2.0"
    },
    "openmed-ner-genome-109m": {
        "hf_repo": "OpenMed/OpenMed-NER-GenomeDetect-BioMed-109M",
        "type": "transformers", "task": "token-classification", "size": "109M", "license": "Apache-2.0"
    },
    "openmed-ner-genome-395m": {
        "hf_repo": "OpenMed/OpenMed-NER-GenomeDetect-ModernMed-395M",
        "type": "transformers", "task": "token-classification", "size": "395M", "license": "Apache-2.0"
    },

    # Bundle example (your convenience preset)
    "openmed-suite-base": {
        "bundle": [
            "openmed-ner-disease-149m",
            "openmed-ner-anatomy-149m",
            "openmed-ner-pathology-65m"
        ]
    },
}


def _models_root(models_dir: Optional[str]) -> Path:
    # Priority: explicit arg > env > sane default
    root = Path(models_dir or os.environ.get("ZEROPHIX_MODELS_DIR", Path.home() / ".cache" / "zerophix" / "models"))
    root.mkdir(parents=True, exist_ok=True)
    return root

def _already_present(path: Path) -> bool:
    return (path / "config.json").exists() or any(path.glob("*.bin")) or any(path.glob("*.safetensors"))

def _download_hf(repo: str, dest: Path):
    # Prefer Python API
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=repo,
            local_dir=str(dest),
            local_dir_use_symlinks=False,
            resume_download=True,
            token=os.environ.get("HF_TOKEN")
        )
        return
    except Exception as e_py:
        # Fallback to huggingface-cli
        import shutil, subprocess
        cli = shutil.which("huggingface-cli")
        if not cli:
            raise RuntimeError(f"huggingface-cli not found; Python API error: {e_py}")
        cmd = [
            cli, "download", repo,
            "--local-dir", str(dest),
            "--local-dir-use-symlinks", "False",
            "--resume"
        ]
        env = os.environ.copy()
        subprocess.check_call(cmd, env=env)

def ensure_model(name: str, models_dir: Optional[str] = None) -> str:
    """
    Ensures one model (or bundle) is available under models_dir (mounted drive).
    - Supports alias entries mapping to another REGISTRY key.
    - Supports bundle entries listing multiple keys (downloads all, returns parent dir).
    """
    entry = REGISTRY.get(name)
    if entry is None:
        raise KeyError(f"Model key '{name}' not found in REGISTRY.")

    # Alias
    if "alias" in entry:
        return ensure_model(entry["alias"], models_dir=models_dir)

    # Bundle (download all children; return their parent)
    if "bundle" in entry:
        parent = _models_root(models_dir) / name
        parent.mkdir(parents=True, exist_ok=True)
        for child in entry["bundle"]:
            ensure_model(child, models_dir=models_dir)
        return str(parent)

    # Single model
    repo = entry["hf_repo"]
    root = _models_root(models_dir)
    target = root / name
    target.mkdir(parents=True, exist_ok=True)
    if not _already_present(target):
        _download_hf(repo, target)
    return str(target)