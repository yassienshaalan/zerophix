import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Iterable

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.eval.metrics import Span, compute_span_metrics


ROOT = Path(__file__).resolve().parents[3]
TAB_DIR = ROOT / "data" / "benchmarks" / "tab"


@dataclass
class TabDoc:
    doc_id: str
    text: str
    gold_spans: List[Span]  # (doc_id, start, end, label)


def _load_tab_split(json_path: Path) -> List[TabDoc]:
    """
    Load a TAB JSON split (echr_train.json / echr_dev.json / echr_test.json).

    We treat any mention with identifier_type in {DIRECT, QUASI}
    as something that MUST be masked (i.e., PHI).
    """
    with json_path.open("r", encoding="utf-8") as f:
        docs_raw: List[Dict[str, Any]] = json.load(f)

    docs: List[TabDoc] = []

    for doc in docs_raw:
        doc_id = doc["doc_id"]
        text = doc["text"]
        annotations = doc["annotations"]

        spans: List[Span] = []
        # DEBUG: Print first annotation to check structure
        if len(docs) == 0 and len(annotations) > 0:
            first_key = next(iter(annotations))
            print(f"DEBUG: First annotation in TAB: {annotations[first_key]}")

        for ent in annotations.values():
            identifier_type = ent.get("identifier_type")
            # DEBUG: Check identifier types
            # if identifier_type not in ("DIRECT", "QUASI"):
            #    print(f"DEBUG: Skipping identifier_type: {identifier_type}")
            
            if identifier_type not in ("DIRECT", "QUASI"):
                continue  # not required to be masked

            start = int(ent["start_offset"])
            end = int(ent["end_offset"])
            label = ent.get("entity_type") or "PHI"

            spans.append((doc_id, start, end, label))

        docs.append(TabDoc(doc_id=doc_id, text=text, gold_spans=spans))

    return docs


def load_tab_corpus() -> Dict[str, List[TabDoc]]:
    """
    Load all splits if available. Requires `scripts/download_benchmarks.py`
    to have been run beforehand.
    """
    paths = {
        "train": TAB_DIR / "echr_train.json",
        "dev": TAB_DIR / "echr_dev.json",
        "test": TAB_DIR / "echr_test.json",
    }
    corpus: Dict[str, List[TabDoc]] = {}
    for split, p in paths.items():
        if not p.exists():
            raise FileNotFoundError(
                f"{p} not found. Run scripts/download_benchmarks.py first."
            )
        corpus[split] = _load_tab_split(p)
    return corpus


def _predict_spans(
    pipeline: RedactionPipeline, docs: Iterable[TabDoc]
) -> List[Span]:
    preds: List[Span] = []
    for d in docs:
        result = pipeline.redact(d.text)
        for ent in result.get("spans", []):
            start = int(ent.get("start", 0))
            end = int(ent.get("end", 0))
            label = ent.get("label") or ent.get("entity_type") or "PHI"
            preds.append((d.doc_id, start, end, label))
    return preds


def run_tab_benchmark(
    config: RedactionConfig | None = None,
    split: str = "test",
    ignore_label: bool = False,
):
    """
    Run ZeroPhi on the TAB benchmark and compute span-level metrics.

    Returns: (metrics, num_gold, num_pred)
    """
    corpus = load_tab_corpus()
    docs = corpus[split]

    if config is None:
        # simple, generic config
        config = RedactionConfig(
            country="EU",
            detectors=["regex", "spacy"],  # tweak as you like
            redaction_strategy="replace",
            min_confidence=0.5,
        )

    pipeline = RedactionPipeline.from_config(config)

    gold_spans: List[Span] = []
    for d in docs:
        gold_spans.extend(d.gold_spans)

    pred_spans = _predict_spans(pipeline, docs)

    metrics = compute_span_metrics(
        gold_spans=gold_spans, pred_spans=pred_spans, ignore_label=ignore_label
    )

    return metrics, len(gold_spans), len(pred_spans)


if __name__ == "__main__":
    metrics, n_gold, n_pred = run_tab_benchmark()
    print(f"TAB test split: gold={n_gold}, pred={n_pred}")
    print(f"Precision: {metrics.precision:.3f}")
    print(f"Recall   : {metrics.recall:.3f}")
    print(f"F1       : {metrics.f1:.3f}")
