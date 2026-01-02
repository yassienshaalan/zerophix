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
    # 1) TAB benchmark (EU-ish legal text) - MANUAL
    # ----------------------------------------------------------
    print("\n[EVAL] Running TAB (Manual Config)...")
    tab_config_manual = RedactionConfig(
        mode="manual",
        country="EU",
        detectors=["regex", "spacy", "bert", "gliner"],
        use_bert=True,
        use_spacy=True,
        use_gliner=True,
        use_statistical=False,
        enable_context_propagation=True,
        enable_ensemble_voting=True,
        redaction_strategy="replace",
        min_confidence=0.5,
        allow_list=[
            "The Court", "the Court", "European Court of Human Rights",
            "The Government", "the Government", "Ministry of Foreign Affairs", "Ministry of Justice",
            "The applicant", "the applicant", "The applicants",
            "Article", "Section", "Convention", "Protocol", "Act", "Rule",
            "Commission", "Chamber", "Grand Chamber", "District Court", "High Court",
            "United Kingdom", "Turkey", "Russia", "Poland", "France", "Germany", "Cyprus",
            "Polish", "Turkish", "French", "German", "British",
            "million", "billion", "fees", "costs", "Department of Work and Pensions",
            "Convention for the Protection of Human Rights and Fundamental Freedoms",
            "Rights and Fundamental Freedoms", "Foreign and Commonwealth Office",
            "Republic of Poland", "Warsaw", "Istanbul", "İstanbul", "Adana", "Ankara"
        ],
        custom_patterns={
            "CASE_NUMBER": [r"\b\d{3,5}/\d{2}\b"], # E.g. 16757/90
            "DATE_FULL": [r"\b\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\b"],
            "DATE_YEAR_ONLY": [r"\b(19|20)\d{2}\b"], # Catch standalone years like "1989"
            "MONEY_GBP": [r"\bGBP\s[\d,]+\b"] # Catch "GBP 215"
        },
        gliner_labels=[
            "person", "judge", "lawyer", "applicant", 
            "organization", "location", "date", "money", "duration", "age"
        ]
    )
    tab_metrics_m, tab_gold_m, tab_pred_m = run_tab_benchmark(
        config=tab_config_manual, split="test", ignore_label=True
    )

    results["benchmarks"]["tab_manual"] = {
        "dataset": "TAB",
        "mode": "manual",
        "split": "test",
        "ignore_label": True,
        "n_gold_spans": tab_gold_m,
        "n_pred_spans": tab_pred_m,
        "metrics": tab_metrics_m.as_dict(),
        "config": tab_config_manual.dict()
    }

    # ----------------------------------------------------------
    # 2) TAB benchmark (EU-ish legal text) - AUTO
    # ----------------------------------------------------------
    print("\n[EVAL] Running TAB (Auto Config)...")
    tab_config_auto = RedactionConfig(
        mode="auto",
        country="EU",
        redaction_strategy="replace",
        min_confidence=0.5,
        # Auto mode should figure out detectors, but we can still provide hints/allowlists
        allow_list=tab_config_manual.allow_list,
        custom_patterns=tab_config_manual.custom_patterns,
        gliner_labels=tab_config_manual.gliner_labels
    )
    tab_metrics_a, tab_gold_a, tab_pred_a = run_tab_benchmark(
        config=tab_config_auto, split="test", ignore_label=True
    )

    results["benchmarks"]["tab_auto"] = {
        "dataset": "TAB",
        "mode": "auto",
        "split": "test",
        "ignore_label": True,
        "n_gold_spans": tab_gold_a,
        "n_pred_spans": tab_pred_a,
        "metrics": tab_metrics_a.as_dict(),
        "config": tab_config_auto.dict()
    }

    # ----------------------------------------------------------
    # 3) PDF Deid benchmark (synthetic medical PDFs) - MANUAL
    # ----------------------------------------------------------
    print("\n[EVAL] Running PDF Deid (Manual Config)...")
    pdf_config_manual = RedactionConfig(
        mode="manual",
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
    pdf_metrics_m, pdf_gold_m, pdf_pred_m = run_pdf_deid_benchmark(
        config=pdf_config_manual, ignore_label=True
    )

    results["benchmarks"]["pdf_deid_manual"] = {
        "dataset": "PDF Deid",
        "mode": "manual",
        "ignore_label": True,
        "n_gold_spans": pdf_gold_m,
        "n_pred_spans": pdf_pred_m,
        "metrics": pdf_metrics_m.as_dict(),
        "config": pdf_config_manual.dict()
    }

    # ----------------------------------------------------------
    # 4) PDF Deid benchmark (synthetic medical PDFs) - AUTO
    # ----------------------------------------------------------
    print("\n[EVAL] Running PDF Deid (Auto Config)...")
    pdf_config_auto = RedactionConfig(
        mode="auto",
        country="US",
        redaction_strategy="replace",
        min_confidence=0.35,
        custom_patterns=pdf_config_manual.custom_patterns,
        gliner_labels=pdf_config_manual.gliner_labels
    )
    pdf_metrics_a, pdf_gold_a, pdf_pred_a = run_pdf_deid_benchmark(
        config=pdf_config_auto, ignore_label=True
    )

    results["benchmarks"]["pdf_deid_auto"] = {
        "dataset": "PDF Deid",
        "mode": "auto",
        "ignore_label": True,
        "n_gold_spans": pdf_gold_a,
        "n_pred_spans": pdf_pred_a,
        "metrics": pdf_metrics_a.as_dict(),
        "config": pdf_config_auto.dict()
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
