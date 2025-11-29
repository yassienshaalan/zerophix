#!/usr/bin/env python3
"""
ZeroPhi File-Based Test Examples (PII Files)
===========================================

This script demonstrates how to use ZeroPhi with three local files:
- pii.csv
- pii.xlsx
- pii.pdf

Place this script in a directory with those three files next to it.

Author: ZeroPhi Team
"""

import argparse
from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd

from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.config import RedactionConfig
from zerophi.processors.documents import PDFProcessor
from zerophi.security.encryption import EncryptionManager


def print_section(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subsection(title: str) -> None:
    print("\n" + "-" * 50)
    print(f" {title}")
    print("-" * 50)


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "pii.csv"
XLSX_PATH = BASE_DIR / "pii.xlsx"
PDF_PATH = BASE_DIR / "pii.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run file-based ZeroPhi redaction demos with optional custom file paths."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Directory containing pii.csv/pii.xlsx/pii.pdf (defaults to this script's folder)",
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to pii.csv (overrides --data-dir)",
    )
    parser.add_argument(
        "--xlsx",
        type=str,
        help="Path to pii.xlsx (overrides --data-dir)",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to pii.pdf (overrides --data-dir)",
    )
    return parser.parse_args()


def resolve_paths(args: argparse.Namespace) -> Tuple[Path, Path, Path]:
    def normalize_arg_path(value: Optional[str]) -> Optional[Path]:
        if value is None:
            return None
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).absolute()
        return path

    data_dir = normalize_arg_path(args.data_dir) or BASE_DIR

    def choose_path(arg_value: Optional[str], default_name: str) -> Path:
        normalized = normalize_arg_path(arg_value)
        return normalized if normalized else (data_dir / default_name)

    csv_path = choose_path(args.csv, "pii.csv")
    xlsx_path = choose_path(args.xlsx, "pii.xlsx")
    pdf_path = choose_path(args.pdf, "pii.pdf")
    return csv_path, xlsx_path, pdf_path


def assert_file_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected file not found: {path}")


def test_csv_redaction_and_hashing() -> None:
    print_section("1. CSV REDACTION AND HASHING (pii.csv)")
    assert_file_exists(CSV_PATH)

    df = pd.read_csv(CSV_PATH)
    print_subsection("1.1 Loaded CSV")
    print(f"Shape: {df.shape}")
    print("Columns:", list(df.columns))

    # Simple redaction preview on 'notes'
    config_replace = RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="replace",
        replacement_char="*",
    )
    pipeline_replace = RedactionPipeline(config_replace)

    sample_notes = str(df.loc[0, "notes"])
    result = pipeline_replace.redact(sample_notes)

    print_subsection("1.2 Redaction preview (notes[0])")
    print("Original:")
    print(sample_notes)
    print("\nRedacted:")
    print(result["text"])
    print("\nEntities:")
    for ent in result.get("entities", [])[:10]:
        print(f"  - {ent['text']} ({ent['label']}) @ {ent['start']}–{ent['end']}")

    # Hashing test for key identifier columns
    config_hash = RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="hash",
        preserve_format=False,
    )
    pipeline_hash = RedactionPipeline(config_hash)

    def hash_cell(text: Any) -> str:
        if pd.isna(text):
            return ""
        return pipeline_hash.redact(str(text))["text"]

    hash_cols = ["medicare_number", "credit_card_number"]
    df_hashed = df.copy()
    for col in hash_cols:
        if col in df_hashed.columns:
            df_hashed[col] = df_hashed[col].apply(hash_cell)

    print_subsection("1.3 Hash determinism check (first 3 medicare_number)")
    for i in range(min(3, len(df))):
        original = df.loc[i, "medicare_number"]
        first = hash_cell(original)
        second = hash_cell(original)
        print(f"Row {i}: {original} -> {first} | repeat same: {first == second}")


def test_excel_redaction_and_hashing() -> None:
    print_section("2. EXCEL REDACTION AND HASHING (pii.xlsx)")
    assert_file_exists(XLSX_PATH)

    xls = pd.ExcelFile(XLSX_PATH)
    print_subsection("2.1 Sheets")
    print("Sheets:", xls.sheet_names)

    patients_df = pd.read_excel(xls, sheet_name="patients")
    claims_df = pd.read_excel(xls, sheet_name="claims")

    print(f"Patients shape: {patients_df.shape}")
    print(f"Claims shape:   {claims_df.shape}")

    # Redact PHI in free-text diagnosis column
    config_text = RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="replace",
        replacement_char="*",
    )
    pipeline_text = RedactionPipeline(config_text)

    def redact_text(text: Any) -> str:
        if pd.isna(text):
            return ""
        return pipeline_text.redact(str(text))["text"]

    if "diagnosis_free_text" in patients_df.columns:
        patients_redacted = patients_df.copy()
        patients_redacted["diagnosis_free_text"] = patients_redacted[
            "diagnosis_free_text"
        ].apply(redact_text)

        print_subsection("2.2 diagnosis_free_text redaction preview")
        print("Original:")
        print(patients_df.loc[0, "diagnosis_free_text"])
        print("\nRedacted:")
        print(patients_redacted.loc[0, "diagnosis_free_text"])
    else:
        print("Column 'diagnosis_free_text' not found in patients sheet.")

    # Hash patient_id across sheets to check joinability
    config_hash = RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="hash",
    )
    pipeline_hash = RedactionPipeline(config_hash)

    def hash_value(text: Any) -> str:
        if pd.isna(text):
            return ""
        return pipeline_hash.redact(str(text))["text"]

    patients_h = patients_df.copy()
    claims_h = claims_df.copy()

    if "patient_id" in patients_h.columns:
        patients_h["patient_id_hashed"] = patients_h["patient_id"].apply(hash_value)
    if "patient_id" in claims_h.columns:
        claims_h["patient_id_hashed"] = claims_h["patient_id"].apply(hash_value)

    print_subsection("2.3 patient_id hash comparison (first 5 rows)")
    for i in range(min(5, len(patients_h), len(claims_h))):
        op = patients_df.loc[i, "patient_id"]
        oc = claims_df.loc[i, "patient_id"]
        hp = patients_h.loc[i, "patient_id_hashed"]
        hc = claims_h.loc[i, "patient_id_hashed"]
        print(
            f"Row {i}: patients={op} -> {hp} | claims={oc} -> {hc} | match={hp == hc}"
        )


def test_pdf_redaction_and_encryption() -> None:
    print_section("3. PDF REDACTION AND ENCRYPTION (pii.pdf)")
    assert_file_exists(PDF_PATH)

    processor = PDFProcessor()
    print_subsection("3.1 Extract text")
    text = processor.extract_text(PDF_PATH.read_bytes())
    print("First 400 chars of extracted text:")
    print(text[:400])
    print("\n...")

    # Redact extracted text
    config_redact = RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="replace",
        replacement_char="*",
    )
    pipeline = RedactionPipeline(config_redact)
    result = pipeline.redact(text)

    print_subsection("3.2 Redacted text preview")
    print(result["text"][:400])
    print("\nEntities (up to 10):")
    for ent in result.get("entities", [])[:10]:
        print(
            f"  - {ent['text']} ({ent['label']}) "
            f"@ {ent['start']}–{ent['end']} "
            f"score={ent.get('confidence', 0):.2f}"
        )

    # Encryption round-trip test
    print_subsection("3.3 Encryption round-trip")
    manager = EncryptionManager()
    sample = "Medical Record Number (MRN): CCH001234"

    encrypted = manager.encrypt(sample, purpose="pii_pdf_test")
    decrypted = manager.decrypt(encrypted, purpose="pii_pdf_test")

    print(f"Original : {sample}")
    print(f"Encrypted: {encrypted[:80]}...")
    print(f"Decrypted: {decrypted}")
    print(f"Round-trip OK: {sample == decrypted}")

    print("\nWrong purpose test (should fail or yield invalid data):")
    try:
        wrong = manager.decrypt(encrypted, purpose="wrong-purpose")
        print(f"Decrypted with wrong purpose: {wrong}")
    except Exception as exc:
        print(f"Failed as expected: {exc}")


def main() -> None:
    global CSV_PATH, XLSX_PATH, PDF_PATH

    args = parse_args()
    CSV_PATH, XLSX_PATH, PDF_PATH = resolve_paths(args)

    print("ZeroPhi File-Based Test Examples (PII Files)")
    print("===========================================")
    print(f"Script directory: {BASE_DIR}")
    print("Using the following files (override with --data-dir/--csv/--xlsx/--pdf):")
    print(f"  - {CSV_PATH.name}")
    print(f"  - {XLSX_PATH.name}")
    print(f"  - {PDF_PATH.name}")
    print("Resolved paths:")
    print(f"  CSV : {CSV_PATH}")
    print(f"  XLSX: {XLSX_PATH}")
    print(f"  PDF : {PDF_PATH}")

    test_csv_redaction_and_hashing()
    test_excel_redaction_and_hashing()
    test_pdf_redaction_and_encryption()

    print_section("ALL TESTS COMPLETED")


if __name__ == "__main__":
    main()
