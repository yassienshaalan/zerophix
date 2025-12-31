#!/usr/bin/env python3
"""
Run all ZeroPhix evaluation benchmarks and save results.

This script:
- Runs TAB (Text Anonymisation Benchmark)
- Runs PDF Deid benchmark
- Writes a single JSON summary under eval/results/

Usage:
    python -m zerophix.eval.run_all_evaluations
or:
    python zerophix/eval/run_all_evaluations.py
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from zerophix.eval.tab_benchmark import run_tab_benchmark
from zerophix.eval.pdf_deid_benchmark import run_pdf_deid_benchmark
from zerophix.config import RedactionConfig


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "eval"
RESULTS_DIR = EVAL_DIR / "results"


def get_git_commit() -> Optional[str]:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(ROOT)
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return None


def run_all() -> Dict[str, Any]:
    """
    Run all benchmarks and return a nested dict with results.
    """

    # Ensure directories exist
    EVAL_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    git_commit = get_git_commit()

    results: Dict[str, Any] = {
        "timestamp_utc": timestamp,
        "git_commit": git_commit,
        "benchmarks": {},
    }

    # ----------------------------------------------------------
    # 1) TAB benchmark (EU-ish legal text)
    # ----------------------------------------------------------
    tab_config = RedactionConfig(
        country="EU",
        detectors=["spacy", "bert", "gliner"],
        use_bert=True,
        use_spacy=True,
        use_gliner=True,
        use_statistical=False,
        enable_context_propagation=True,
        enable_ensemble_voting=True,
        redaction_strategy="replace",
        min_confidence=0.4,
        gliner_labels=[
            "person", "organization", "location", "date", "case number"
        ]
    )
    tab_metrics, tab_gold, tab_pred = run_tab_benchmark(
        config=tab_config, split="test", ignore_label=True
    )

    results["benchmarks"]["tab"] = {
        "dataset": "TAB",
        "split": "test",
        "ignore_label": True,
        "n_gold_spans": tab_gold,
        "n_pred_spans": tab_pred,
        "metrics": tab_metrics.as_dict(),
        "config": {
            "country": tab_config.country,
            "detectors": tab_config.detectors,
            "redaction_strategy": tab_config.redaction_strategy,
        },
    }

    # ----------------------------------------------------------
    # 2) PDF Deid benchmark (synthetic medical PDFs)
    # ----------------------------------------------------------
    pdf_config = RedactionConfig(
        country="US",
        detectors=["regex", "spacy", "bert", "openmed", "gliner"],
        use_openmed=True,
        use_spacy=True,
        use_bert=True,
        use_gliner=True,
        use_statistical=False,
        enable_context_propagation=True,
        enable_ensemble_voting=True,
        redaction_strategy="replace",
        min_confidence=0.35,
        custom_patterns={
            "DATE_INTL": [r"\b(0?[1-9]|[12]\d|3[01])[./](0?[1-9]|1[0-2])[./](19|20)\d{2}\b"]
        },
        gliner_labels=[
            "patient name", "doctor name", "hospital", "medical record number", 
            "date", "age", "phone number", "address", "organization"
        ]
    )
    pdf_metrics, pdf_gold, pdf_pred = run_pdf_deid_benchmark(
        config=pdf_config, ignore_label=True
    )

    results["benchmarks"]["pdf_deid"] = {
        "dataset": "PDF Deid",
        "ignore_label": True,
        "n_gold_spans": pdf_gold,
        "n_pred_spans": pdf_pred,
        "metrics": pdf_metrics.as_dict(),
        "config": {
            "country": pdf_config.country,
            "detectors": pdf_config.detectors,
            "redaction_strategy": pdf_config.redaction_strategy,
        },
    }

    return results


def save_results(results: Dict[str, Any]) -> Path:
    """
    Save results JSON into eval/results/ with a timestamped filename.
    """
    timestamp = results.get("timestamp_utc", datetime.utcnow().isoformat(timespec="seconds") + "Z")
    # Safe-ish filename timestamp: 2025-11-30T02:13:45Z -> 2025-11-30T02-13-45Z
    safe_ts = timestamp.replace(":", "-")
    out_path = RESULTS_DIR / f"evaluation_{safe_ts}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)

    return out_path


def main():
    print(f"[INFO] Running ZeroPhi evaluations from root: {ROOT}")
    results = run_all()
    out_path = save_results(results)
    print(f"[OK] Evaluation results written to: {out_path}")


if __name__ == "__main__":
    main()
