import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Iterable, Tuple

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.eval.metrics import Span, compute_span_metrics

ROOT = Path(__file__).resolve().parents[3]
PDF_DEID_DIR = ROOT / "data" / "benchmarks" / "pdf_deid"


@dataclass
class PdfPageDoc:
    doc_id: str
    page: int
    text: str
    gold_spans: List[Span]


def _load_pdf_deid_ground_truth() -> List[PdfPageDoc]:
    """
    Load PDF Deid 'Mapping/pdf_deid_gts_*.json'.

    Each GT JSON describes PHI entities by page, coordinates, and text; here we
    simplify to TEXT-LEVEL evaluation (not bbox IoU), so we only need:
        - page index
        - 'text' or 'value' field
        - category label

    Adapt based on the actual JSON format if your pipeline needs more fidelity.
    """
    mapping_dir = PDF_DEID_DIR / "Mapping"
    if not mapping_dir.exists():
        raise FileNotFoundError(
            f"{mapping_dir} not found. Did you run scripts/download_benchmarks.py?"
        )

    docs: List[PdfPageDoc] = []

    for gt_file in mapping_dir.glob("pdf_deid_gts_*.json"):
        with gt_file.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        # This part is schema-dependent; you may need to adjust based on their JSON
        # For now we assume structure like:
        # {
        #   "file_name": ...,
        #   "pages": [
        #     {
        #       "page_num": 1,
        #       "text": "...",
        #       "entities": [
        #         {"start": int, "end": int, "label": "NAME", "text": "..."},
        #         ...
        #       ]
        #     }, ...
        #   ]
        # }
        file_id = Path(data.get("file_name", gt_file.stem)).stem

        for page in data.get("pages", []):
            page_num = int(page.get("page_num", 1))
            text = page.get("text", "")

            spans: List[Span] = []
            for ent in page.get("entities", []):
                start = int(ent.get("start", 0))
                end = int(ent.get("end", 0))
                label = ent.get("label", "PHI")
                spans.append((f"{file_id}_p{page_num}", start, end, label))

            docs.append(
                PdfPageDoc(
                    doc_id=f"{file_id}_p{page_num}",
                    page=page_num,
                    text=text,
                    gold_spans=spans,
                )
            )

    return docs


def _predict_pdf_spans(
    pipeline: RedactionPipeline, docs: Iterable[PdfPageDoc]
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


def run_pdf_deid_benchmark(
    config: RedactionConfig | None = None, ignore_label: bool = False
):
    docs = _load_pdf_deid_ground_truth()

    if config is None:
        config = RedactionConfig(
            country="US",
            detectors=["regex"],
            redaction_strategy="replace",
            min_confidence=0.5,
        )

    pipeline = RedactionPipeline.from_config(config)

    gold_spans: List[Span] = []
    for d in docs:
        gold_spans.extend(d.gold_spans)

    pred_spans = _predict_pdf_spans(pipeline, docs)

    metrics = compute_span_metrics(
        gold_spans=gold_spans, pred_spans=pred_spans, ignore_label=ignore_label
    )
    return metrics, len(gold_spans), len(pred_spans)


if __name__ == "__main__":
    metrics, n_gold, n_pred = run_pdf_deid_benchmark()
    print(f"PDF Deid: gold={n_gold}, pred={n_pred}")
    print(f"Precision: {metrics.precision:.3f}")
    print(f"Recall   : {metrics.recall:.3f}")
    print(f"F1       : {metrics.f1:.3f}")
