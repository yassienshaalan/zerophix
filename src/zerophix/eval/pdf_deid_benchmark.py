import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Iterable, Tuple
import pypdf

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
    Load PDF Deid dataset.
    
    The dataset consists of:
    1. JSON files in Mapping/all_phi/ containing lists of PHI strings per filename.
    2. Original PDF files in PDF_Original/.
    
    We extract text from PDFs and search for the PHI strings to create gold spans.
    """
    mapping_dir = PDF_DEID_DIR / "Mapping"
    pdf_dir = PDF_DEID_DIR / "PDF_Original"
    
    if not mapping_dir.exists():
        raise FileNotFoundError(
            f"{mapping_dir} not found. Did you run scripts/download_benchmarks.py?"
        )

    # 1. Load Ground Truth Map: filename -> list of PHI strings
    gt_map: Dict[str, List[str]] = {}
    
    # Find all JSON files recursively
    json_files = list(mapping_dir.glob("**/*.json"))
    # Filter out result files
    json_files = [f for f in json_files if "result" not in f.name]
    
    if not json_files:
        print(f"DEBUG: No ground truth JSON files found in {mapping_dir}")
        return []
        
    print(f"DEBUG: Loading ground truth from {len(json_files)} files...")
    for gt_file in json_files:
        try:
            with gt_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge into main map
                # Format: {"filename.pdf": ["phi1", "phi2"], ...}
                if isinstance(data, dict):
                    gt_map.update(data)
        except Exception as e:
            print(f"Error loading {gt_file}: {e}")

    # 2. Find and Process PDFs
    docs: List[PdfPageDoc] = []
    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    
    print(f"DEBUG: Found {len(pdf_files)} PDF files. Matching with {len(gt_map)} GT entries...")
    
    for pdf_file in pdf_files:
        fname = pdf_file.name
        if fname not in gt_map:
            # Maybe the key in JSON doesn't have .pdf extension?
            if pdf_file.stem in gt_map:
                fname = pdf_file.stem
            else:
                # print(f"DEBUG: Skipping {fname} (no GT found)")
                continue
            
        gt_strings = gt_map[fname]
        # Ensure gt_strings is a list of strings
        if not isinstance(gt_strings, list):
            continue
        gt_strings = [s for s in gt_strings if isinstance(s, str)]
        
        try:
            reader = pypdf.PdfReader(pdf_file)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                spans: List[Span] = []
                # Naive matching: find all occurrences of GT strings in this page
                # We use a set of unique PHI strings to search, but we find ALL occurrences
                unique_phis = set(gt_strings)
                
                for phi_str in unique_phis:
                    if not phi_str.strip(): continue
                    
                    start = 0
                    while True:
                        idx = text.find(phi_str, start)
                        if idx == -1:
                            break
                        # Add span: (doc_id, start, end, label)
                        # doc_id needs to be unique per page
                        doc_id = f"{fname}_p{page_idx+1}"
                        spans.append((doc_id, idx, idx + len(phi_str), "PHI"))
                        start = idx + 1
                
                if spans:
                    docs.append(PdfPageDoc(
                        doc_id=f"{fname}_p{page_idx+1}",
                        page=page_idx + 1,
                        text=text,
                        gold_spans=spans
                    ))
                    
        except Exception as e:
            print(f"Error reading PDF {pdf_file}: {e}")

    print(f"DEBUG: Loaded {len(docs)} pages with ground truth.")
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
