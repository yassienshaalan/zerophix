import os
import json
from pathlib import Path

import pytest

from zerophix.eval.run_all_evaluations import run_all, save_results

MIN_TAB_F1 = float(os.getenv("ZEROPHIX_MIN_TAB_F1", "0.90"))
MIN_PDF_F1 = float(os.getenv("ZEROPHIX_MIN_PDF_F1", "0.90"))


@pytest.mark.slow
@pytest.mark.benchmark
def test_full_evaluation_snapshot():
    results = run_all()
    out_path = save_results(results)

    tab = results["benchmarks"]["tab"]["metrics"]
    pdf = results["benchmarks"]["pdf_deid"]["metrics"]

    print(f"Results saved to: {out_path}")
    print(f"TAB  F1: {tab['f1']:.3f}")
    print(f"PDF  F1: {pdf['f1']:.3f}")

    assert tab["f1"] >= MIN_TAB_F1
    assert pdf["f1"] >= MIN_PDF_F1
