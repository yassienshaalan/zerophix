from pathlib import Path
from typing import Any

import pytest

from zerophi.config import RedactionConfig
from zerophi.pipelines.redaction import RedactionPipeline
from zerophi.security.encryption import EncryptionManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_cfg() -> RedactionConfig:
    """Default AU config using regex detector."""
    return RedactionConfig(
        country="AU",
        detectors=["regex"],  # keep it simple & fast for unit tests
    )


@pytest.fixture
def basic_pipeline(basic_cfg: RedactionConfig) -> RedactionPipeline:
    """Pipeline with default replacement strategy."""
    return RedactionPipeline.from_config(basic_cfg)


@pytest.fixture
def hash_cfg() -> RedactionConfig:
    """Config that uses hashing as the redaction strategy."""
    return RedactionConfig(
        country="AU",
        detectors=["regex"],
        redaction_strategy="hash",
        preserve_format=False,
    )


@pytest.fixture
def hash_pipeline(hash_cfg: RedactionConfig) -> RedactionPipeline:
    return RedactionPipeline.from_config(hash_cfg)


@pytest.fixture
def pii_csv_path() -> Path:
    """
    Path to the synthetic PII CSV.
    Place `pii.csv` in the same directory as this test file,
    or adjust the path as needed.
    """
    return Path(__file__).resolve().parent / "pii.csv"


# ---------------------------------------------------------------------------
# 1. BASIC REDACTION
# ---------------------------------------------------------------------------

def test_basic_redact(basic_cfg: RedactionConfig):
    """Original minimal test you already had."""
    pipe = RedactionPipeline.from_config(basic_cfg)
    out = pipe.redact("Email me at a.b@example.com")
    assert "a.b@example.com" not in out["text"]


def test_email_and_phone_are_redacted(basic_pipeline: RedactionPipeline):
    text = "Contact Sam at sam@example.com or on +61-412-345-678."
    out = basic_pipeline.redact(text)

    redacted_text = out["text"]
    # Email and phone should not appear verbatim
    assert "sam@example.com" not in redacted_text
    assert "+61-412-345-678" not in redacted_text

    # We expect at least one entity to be detected
    assert len(out.get("entities", [])) >= 1


def test_does_not_return_empty_string_for_non_pii(basic_pipeline: RedactionPipeline):
    """Non-PII text should survive redaction (we don't blank everything)."""
    text = "This sentence has no identifiers."
    out = basic_pipeline.redact(text)
    assert out["text"].strip() != ""


# ---------------------------------------------------------------------------
# 2. HASH STRATEGY
# ---------------------------------------------------------------------------

def test_hash_strategy_changes_value(hash_pipeline: RedactionPipeline):
    text = "my secret email is jane.doe@example.com"
    out = hash_pipeline.redact(text)
    redacted_text = out["text"]

    # Hashed output should not contain the original literal
    assert "jane.doe@example.com" not in redacted_text
    # And it should not be identical to the original input string
    assert redacted_text != text


def test_hash_strategy_is_deterministic(hash_pipeline: RedactionPipeline):
    """Same input -> same hash output when config is identical."""
    text = "Phone: +61-499-111-000"

    out1 = hash_pipeline.redact(text)
    out2 = hash_pipeline.redact(text)

    assert out1["text"] == out2["text"], "Hashing must be deterministic"


def test_hash_strategy_differs_for_different_inputs(hash_pipeline: RedactionPipeline):
    """Different inputs should not hash to the same text (very unlikely)."""
    text1 = "Phone: +61-499-111-000"
    text2 = "Phone: +61-422-333-444"

    out1 = hash_pipeline.redact(text1)["text"]
    out2 = hash_pipeline.redact(text2)["text"]

    assert out1 != out2


# ---------------------------------------------------------------------------
# 3. STRATEGY CONFIGURATION SANITY
# ---------------------------------------------------------------------------

def test_can_switch_strategies_via_config(basic_cfg: RedactionConfig):
    """Ensure different strategies can be constructed without error."""
    strategies = ["replace", "hash"]

    for strategy in strategies:
        cfg = RedactionConfig(
            country=basic_cfg.country,
            detectors=basic_cfg.detectors,
            redaction_strategy=strategy,
        )
        pipe = RedactionPipeline.from_config(cfg)
        out = pipe.redact("Email: user@example.com")
        assert "user@example.com" not in out["text"]


# ---------------------------------------------------------------------------
# 4. CSV-BASED INTEGRATION (USING pii.csv)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("column", ["email", "phone", "medicare_number"])
def test_pii_csv_identifiers_are_redacted(
    basic_pipeline: RedactionPipeline,
    pii_csv_path: Path,
    column: str,
):
    """
    Light integration test: pull a few values from pii.csv and ensure
    they are redacted by the pipeline.
    """
    pytest.importorskip("pandas")  # skip cleanly if pandas is not installed
    import pandas as pd

    assert pii_csv_path.exists(), f"Expected test file not found: {pii_csv_path}"

    df = pd.read_csv(pii_csv_path)
    assert column in df.columns, f"Column {column} missing in {pii_csv_path.name}"

    # Take first non-null value
    value = next(
        (str(v) for v in df[column].dropna().tolist() if str(v).strip()),
        None,
    )
    assert value is not None, f"No non-empty values in column {column}"

    out = basic_pipeline.redact(value)
    assert value not in out["text"]


# ---------------------------------------------------------------------------
# 5. ENCRYPTION MANAGER TESTS
# ---------------------------------------------------------------------------

def test_encryption_round_trip():
    """
    EncryptionManager should be able to round-trip a value
    when using the same purpose.
    """
    manager = EncryptionManager()
    original = "Medical Record Number (MRN): CCH001234"

    encrypted = manager.encrypt(original, purpose="test_round_trip")
    assert isinstance(encrypted, str)
    assert encrypted != original  # should not store plaintext

    decrypted = manager.decrypt(encrypted, purpose="test_round_trip")
    assert decrypted == original


def test_encryption_wrong_purpose_fails_or_changes():
    """
    Decrypting with the wrong 'purpose' should not silently
    succeed to the correct plaintext.
    """
    manager = EncryptionManager()
    original = "Credit card 4532 1234 5678 9012"

    encrypted = manager.encrypt(original, purpose="correct-purpose")

    # Decrypt with a different purpose
    with pytest.raises(Exception):
        # If your implementation instead returns garbled data instead of raising,
        # replace this block with:
        #
        # wrong = manager.decrypt(encrypted, purpose="wrong-purpose")
        # assert wrong != original
        #
        manager.decrypt(encrypted, purpose="wrong-purpose")
