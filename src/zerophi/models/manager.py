# src/zerophi/models/manager.py
import os
from pathlib import Path
from typing import Optional

REGISTRY = {
    "openmed-base": {
        "hf_repo": "StanfordAIMI/OpenMed-NER-base",
        "type": "transformers",
        "size": "≈400MB",
        "license": "Apache-2.0",
    },
    "openmed-large": {
        "hf_repo": "StanfordAIMI/OpenMed-NER-large",
        "type": "transformers",
        "size": "≈1.2GB",
        "license": "Apache-2.0",
    },
}
REGISTRY.update({
    # Disease / Anatomy
    "openmed-ner-disease-149m": {
        "hf_repo": "OpenMed/OpenMed-NER-DiseaseDetect-ModernClinical-149M",
        "task": "token-classification", "size": "149M", "license": "Apache-2.0"
    },
    "openmed-ner-anatomy-149m": {
        "hf_repo": "OpenMed/OpenMed-NER-AnatomyDetect-ModernClinical-149M",
        "task": "token-classification", "size": "149M", "license": "Apache-2.0"
    },

    # Pathology tiny (fast CPU)
    "openmed-ner-pathology-65m": {
        "hf_repo": "OpenMed/OpenMed-NER-PathologyDetect-TinyMed-65M",
        "task": "token-classification", "size": "65M", "license": "Apache-2.0"
    },

    # Base suite aliases (bundle picks one of each domain)
    "openmed-suite-base": {
        "bundle": [
            "openmed-ner-disease-149m",
            "openmed-ner-anatomy-149m",
            "openmed-ner-pathology-65m"
        ]
    }
})

def ensure_model(name: str, models_dir: Optional[str] = None) -> str:
    """
    Ensure a HF model snapshot is present locally. Prefer Python API, fallback to CLI.
    Uses HF_TOKEN env var if present.
    """
    repo = REGISTRY[name]["hf_repo"]
    models_root = Path(models_dir or os.environ.get("ZEROPHI_MODELS_DIR", Path.home() / ".cache" / "zerophi" / "models"))
    target = models_root / name
    target.mkdir(parents=True, exist_ok=True)

    # If already looks like a HF snapshot, just return
    if (target / "config.json").exists() or any(target.glob("*.bin")) or any(target.glob("*.safetensors")):
        return str(target)

    # Try Python API first (recommended)
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=repo,
            local_dir=str(target),
            local_dir_use_symlinks=False,
            resume_download=True,
            token=os.environ.get("HF_TOKEN")
        )
        return str(target)
    except Exception as e_py:
        # Fallback to CLI (huggingface-cli)
        try:
            import subprocess, shutil
            cli = shutil.which("huggingface-cli")
            if not cli:
                raise RuntimeError("huggingface-cli not found on PATH")
            cmd = [
                cli, "download", repo,
                "--local-dir", str(target),
                "--local-dir-use-symlinks", "False",
                "--resume"
            ]
            # Allow token via env
            env = os.environ.copy()
            subprocess.check_call(cmd, env=env)
            return str(target)
        except Exception as e_cli:
            raise RuntimeError(
                f"Failed to download model '{name}' from '{repo}'. "
                f"Install/upgrade 'huggingface_hub' or 'huggingface_hub[cli]' and set HF_TOKEN if required. "
                f"Python error: {e_py}; CLI error: {e_cli}"
            )
