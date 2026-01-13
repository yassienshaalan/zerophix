from pathlib import Path
from typing import Any

import pytest

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.security.encryption import EncryptionManager


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
    assert len(out.get("spans", [])) >= 1


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


def test_scan_returns_detections(basic_pipeline: RedactionPipeline):
    """Test that scan returns a dict with detections"""
    text = "Contact john@example.com or call 555-1234"
    result = basic_pipeline.scan(text)
    
    assert isinstance(result, dict)
    assert "detections" in result
    assert "total_detections" in result
    assert "has_pii" in result
    assert result["has_pii"] is True
    assert result["total_detections"] > 0


def test_scan_detects_email(basic_pipeline: RedactionPipeline):
    """Test that scan detects email addresses"""
    text = "Email me at test@example.com"
    result = basic_pipeline.scan(text)
    
    emails = [d for d in result["detections"] if d["label"] == "EMAIL"]
    assert len(emails) > 0
    assert "test@example.com" in emails[0]["text"]


def test_redact_batch_processes_multiple_texts(basic_pipeline: RedactionPipeline):
    """Test batch redaction of multiple texts"""
    texts = [
        "Email: test1@example.com",
        "Phone: 555-1234",
        "Name: John Smith"
    ]
    results = basic_pipeline.redact_batch(texts)
    
    assert len(results) == 3
    assert all("text" in r for r in results)
    assert all("spans" in r for r in results)


def test_scan_batch_processes_multiple_texts(basic_pipeline: RedactionPipeline):
    """Test batch scanning of multiple texts"""
    texts = [
        "Email: test1@example.com",
        "Phone: 555-1234",
        "Contact: jane@test.com"
    ]
    results = basic_pipeline.scan_batch(texts)
    
    assert len(results) == 3
    assert all("detections" in r for r in results)
    assert all("has_pii" in r for r in results)


def test_multiple_entities_same_type(basic_pipeline: RedactionPipeline):
    """Test redaction of multiple entities of the same type"""
    text = "Contact test1@example.com or test2@example.com"
    result = basic_pipeline.redact(text)
    
    assert "test1@example.com" not in result["text"]
    assert "test2@example.com" not in result["text"]
    assert len(result["spans"]) >= 2


def test_entity_at_start(basic_pipeline: RedactionPipeline):
    """Test entity at the start of text"""
    text = "test@example.com is my email"
    result = basic_pipeline.redact(text)
    
    assert "test@example.com" not in result["text"]
    assert result["text"].endswith("is my email")

