import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "data" / "benchmarks" / "tab"
PDF_DEID_DIR = ROOT / "data" / "benchmarks" / "pdf_deid"

def inspect_tab():
    print("\n=== Inspecting TAB Dataset ===")
    fpath = TAB_DIR / "echr_train.json"
    if not fpath.exists():
        print(f"File not found: {fpath}")
        return

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} documents.")
        if len(data) > 0:
            print("First document structure:")
            doc = data[0]
            print(json.dumps(doc, indent=2)[:500] + "...")
            
            if "annotations" in doc:
                print("\nAnnotations sample:")
                print(json.dumps(doc["annotations"], indent=2)[:500] + "...")
    except Exception as e:
        print(f"Error reading TAB: {e}")

def inspect_pdf_deid():
    print("\n=== Inspecting PDF Deid Dataset ===")
    mapping_dir = PDF_DEID_DIR / "Mapping"
    if not mapping_dir.exists():
        print(f"Directory not found: {mapping_dir}")
        return

    files = list(mapping_dir.glob("pdf_deid_gts_*.json"))
    print(f"Found {len(files)} GT files.")
    
    if len(files) > 0:
        fpath = files[0]
        print(f"Reading {fpath.name}...")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("File structure:")
            print(json.dumps(data, indent=2)[:500] + "...")
        except Exception as e:
            print(f"Error reading PDF Deid: {e}")

if __name__ == "__main__":
    inspect_tab()
    inspect_pdf_deid()
