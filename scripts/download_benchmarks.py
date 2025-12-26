#!/usr/bin/env python3
"""
Download public benchmarks for ZeroPhi evaluation.

Datasets:
- TAB (Text Anonymisation Benchmark) [court cases with PHI annotations]
- PDF Deid Dataset (synthetic medical PDFs with PHI annotations)

This script does NOT ship any data itself; it just downloads from:
- TAB: https://github.com/NorskRegnesentral/text-anonymisation-benchmark
- PDF Deid: https://github.com/JohnSnowLabs/pdf-deid-dataset
"""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "benchmarks"


def git_clone_or_pull(repo_url: str, dest: Path):
    if dest.exists():
        # Pull latest
        print(f"[INFO] Updating existing repo at {dest}")
        subprocess.check_call(["git", "-C", str(dest), "pull"])
    else:
        print(f"[INFO] Cloning {repo_url} into {dest}")
        subprocess.check_call(["git", "clone", repo_url, str(dest)])


def download_tab():
    tab_dir = DATA_DIR / "tab"
    git_clone_or_pull(
        "https://github.com/NorskRegnesentral/text-anonymisation-benchmark.git",
        tab_dir,
    )
    print(f"[OK] TAB dataset available at: {tab_dir}")


def download_pdf_deid():
    pdf_dir = DATA_DIR / "pdf_deid"
    git_clone_or_pull(
        "https://github.com/JohnSnowLabs/pdf-deid-dataset.git",
        pdf_dir,
    )
    print(f"[OK] PDF Deid dataset available at: {pdf_dir}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    download_tab()
    download_pdf_deid()
    print("\n[DONE] All benchmark datasets downloaded/updated.")


if __name__ == "__main__":
    main()
