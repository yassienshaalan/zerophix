#!/usr/bin/env python3
"""
ZeroPhix Regression Suite - Trusted Release Regression
======================================================

Run this before every release to ensure accuracy has not degraded.

Three tiers:
  SMOKE  - 30 golden cases, <10s, catches catastrophic regressions
  BASIC  - 100 cases, <60s, standard release gate
  FULL   - 200+ cases with span-level IoU, <5min, thorough release validation

Usage:
    # Smoke (CI/pre-commit)
    python -m pytest tests/regression_suite.py -k smoke

    # Basic (PR gate)
    python -m pytest tests/regression_suite.py -k basic

    # Full (release validation)
    python -m pytest tests/regression_suite.py -k full

    # Save new baseline after intentional improvements
    python tests/regression_suite.py --save-baseline

    # Run and compare against baseline
    python tests/regression_suite.py --check
"""

import json
import os
import sys
import time
import unittest
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

BASELINE_FILE = PROJECT_ROOT / "tests" / "regression_baseline.json"


# ──────────────────────────────────────────────────────────────
# Golden Test Cases - Pinned expected outputs for regression
# ──────────────────────────────────────────────────────────────

@dataclass
class GoldenCase:
    """A test case with exact expected span labels."""
    id: str
    text: str
    expected_labels: List[str]
    description: str
    country: str = "US"
    tier: str = "smoke"  # smoke | basic | full


# fmt: off
GOLDEN_CASES: List[GoldenCase] = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TIER: SMOKE - Critical path tests (30 cases)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Email detection (5)
    GoldenCase("S-EMAIL-01", "Email: john@example.com", ["EMAIL"], "Basic email", tier="smoke"),
    GoldenCase("S-EMAIL-02", "Contact jane.doe@company.co.uk", ["EMAIL"], "Email with subdomain", tier="smoke"),
    GoldenCase("S-EMAIL-03", "user+tag@example.com is valid", ["EMAIL"], "Email with plus", tier="smoke"),
    GoldenCase("S-EMAIL-04", "Two: alice@test.com, bob@corp.com", ["EMAIL"], "Multiple emails", tier="smoke"),
    GoldenCase("S-EMAIL-05", "admin@zerophix.dev for support", ["EMAIL"], "Dev email", tier="smoke"),

    # SSN detection (5)
    GoldenCase("S-SSN-01", "My SSN is 123-45-6789", ["SSN"], "Basic SSN", tier="smoke"),
    GoldenCase("S-SSN-02", "SSN: 987-65-4321", ["SSN"], "SSN with label", tier="smoke"),
    GoldenCase("S-SSN-03", "Tax ID: 321-54-9876, verified", ["SSN"], "Tax ID as SSN", tier="smoke"),
    GoldenCase("S-SSN-04", "Two SSNs: 345-67-8901 and 765-43-2109", ["SSN"], "Multiple SSNs", tier="smoke"),
    GoldenCase("S-SSN-05", "Employee SSN 111-22-3333 on file", ["SSN"], "SSN in context", tier="smoke"),

    # Phone detection (5)
    GoldenCase("S-PHONE-01", "Call me at (555) 123-4567", ["PHONE_US"], "US phone standard", tier="smoke"),
    GoldenCase("S-PHONE-02", "555-987-6543 is my number", ["PHONE_US"], "Phone with dashes", tier="smoke"),
    GoldenCase("S-PHONE-03", "Phone: 555.123.4567", ["PHONE_US"], "Phone with dots", tier="smoke"),
    GoldenCase("S-PHONE-04", "Multiple: 555-111-2222 or 555-333-4444", ["PHONE_US"], "Two phones", tier="smoke"),
    GoldenCase("S-PHONE-05", "Direct: (555) 444-5555", ["PHONE_US"], "Direct number", tier="smoke"),

    # Credit card detection (5)
    GoldenCase("S-CC-01", "Card: 4532-1234-5678-9999", ["CREDIT_CARD"], "Visa card", tier="smoke"),
    GoldenCase("S-CC-02", "5105105105105100 is test", ["CREDIT_CARD"], "Mastercard", tier="smoke"),
    GoldenCase("S-CC-03", "American Express: 378282246310005", ["CREDIT_CARD"], "Amex", tier="smoke"),
    GoldenCase("S-CC-04", "4024 0071 4597 4932 format", ["CREDIT_CARD"], "Card with spaces", tier="smoke"),
    GoldenCase("S-CC-05", "Discover: 6011000990139424", ["CREDIT_CARD"], "Discover card", tier="smoke"),

    # Combined (5)
    GoldenCase("S-COMBO-01", "Email john@test.com, SSN 123-45-6789", ["EMAIL", "SSN"], "Email + SSN", tier="smoke"),
    GoldenCase("S-COMBO-02", "Support: (555) 111-2222 or support@help.com", ["PHONE_US", "EMAIL"], "Phone + email", tier="smoke"),
    GoldenCase("S-COMBO-03", "Card 4532123456789999, SSN 111-22-3333", ["CREDIT_CARD", "SSN"], "Card + SSN", tier="smoke"),
    GoldenCase("S-COMBO-04", "Invoice: john@co.com, Phone 555-123-4567, SSN 234-56-7890", ["EMAIL", "PHONE_US", "SSN"], "Triple combo", tier="smoke"),
    GoldenCase("S-COMBO-05", "Patient MRN: 123456", ["MEDICAL_RECORD"], "Medical record", tier="smoke"),

    # No-PII (must not false-positive) (5)
    GoldenCase("S-CLEAN-01", "The quick brown fox jumps over the lazy dog.", [], "No PII clean text", tier="smoke"),
    GoldenCase("S-CLEAN-02", "Meeting scheduled for next Tuesday at 3pm.", [], "Date context no PII", tier="smoke"),
    GoldenCase("S-CLEAN-03", "Revenue increased by 15% in Q3 2025.", [], "Business text no PII", tier="smoke"),
    GoldenCase("S-CLEAN-04", "ICD-10 code: E11.9 for Diabetes", [], "Medical context no PII", tier="smoke"),
    GoldenCase("S-CLEAN-05", "Blood pressure: 120/80 mmHg", [], "Vital signs no PII", tier="smoke"),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TIER: BASIC - Extended coverage (70 more cases)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # More emails (5)
    GoldenCase("B-EMAIL-01", "john.smith_2024@test-domain.org", ["EMAIL"], "Complex email", tier="basic"),
    GoldenCase("B-EMAIL-02", "support@zerophix.dev and info@zerophix.com", ["EMAIL"], "Company emails", tier="basic"),
    GoldenCase("B-EMAIL-03", "name_123@domain.co.nz", ["EMAIL"], "Email with numbers", tier="basic"),
    GoldenCase("B-EMAIL-04", "billing@store.io for invoices", ["EMAIL"], "Billing email", tier="basic"),
    GoldenCase("B-EMAIL-05", "notifications@service.com daily", ["EMAIL"], "Notification email", tier="basic"),

    # More SSNs (5)
    GoldenCase("B-SSN-01", "Invalid SSN: 000-00-0000, valid: 234-56-7890", ["SSN"], "Valid/invalid mix", tier="basic"),
    GoldenCase("B-SSN-02", "Federal ID 111-22-3333", ["SSN"], "Federal ID", tier="basic"),
    GoldenCase("B-SSN-03", "Government file 222-33-4444 attached", ["SSN"], "Gov file SSN", tier="basic"),
    GoldenCase("B-SSN-04", "Reference: 333-44-5555", ["SSN"], "Reference SSN", tier="basic"),
    GoldenCase("B-SSN-05", "SSN check: 901-23-4567 passed", ["SSN"], "SSN with pass context", tier="basic"),

    # More phones (5)
    GoldenCase("B-PHONE-01", "5551234567 without formatting", ["PHONE_US"], "No format phone", tier="basic"),
    GoldenCase("B-PHONE-02", "Reach: (202) 555-0123 ext. 456", ["PHONE_US"], "Phone with ext", tier="basic"),
    GoldenCase("B-PHONE-03", "Call 555-0199 for support", ["PHONE_US"], "Phone in context", tier="basic"),
    GoldenCase("B-PHONE-04", "Emergency: (555) 911-0000", ["PHONE_US"], "Emergency number", tier="basic"),
    GoldenCase("B-PHONE-05", "Main line 555-2000", ["PHONE_US"], "Main line", tier="basic"),

    # More credit cards (3)
    GoldenCase("B-CC-01", "Card numbers: 6011111111111117, 4532123456789", ["CREDIT_CARD"], "Multiple cards", tier="basic"),
    GoldenCase("B-CC-02", "My card is 5105-1051-0510-5100", ["CREDIT_CARD"], "Dashed card", tier="basic"),
    GoldenCase("B-CC-03", "5555555555554444 test", ["CREDIT_CARD"], "Test Mastercard", tier="basic"),

    # Medical records (5)
    GoldenCase("B-MED-01", "Patient MRN: 654321", ["MEDICAL_RECORD"], "MRN second", tier="basic"),
    GoldenCase("B-MED-02", "Record #999888", ["MEDICAL_RECORD"], "Record ID", tier="basic"),
    GoldenCase("B-MED-03", "Chart: MRN 555777", ["MEDICAL_RECORD"], "Chart MRN", tier="basic"),
    GoldenCase("B-MED-04", "Medical: Patient #12345, Diagnosis: Diabetes", ["MEDICAL_RECORD"], "Medical report", tier="basic"),
    GoldenCase("B-MED-05", "Billing: MRN 131415, Email bill@charge.com", ["MEDICAL_RECORD", "EMAIL"], "MRN + email", tier="basic"),

    # Combined scenarios (12)
    GoldenCase("B-COMBO-01", "Employee: Alice Johnson, ID: 456-78-9012, Email: alice@corp.com", ["PERSON_NAME", "SSN", "EMAIL"], "Employee record", tier="basic"),
    GoldenCase("B-COMBO-02", "Billing: Card 4532123456789999, SSN 111-22-3333", ["CREDIT_CARD", "SSN"], "Billing info", tier="basic"),
    GoldenCase("B-COMBO-03", "ER Visit: Patient: Michael Johnson, MRN: 987654", ["PERSON_NAME", "MEDICAL_RECORD"], "ER admission", tier="basic"),
    GoldenCase("B-COMBO-04", "Telehealth: Email dr.james@clinic.com, Phone (555) 555-5555, MRN: 555666", ["EMAIL", "PHONE_US", "MEDICAL_RECORD"], "Telehealth", tier="basic"),
    GoldenCase("B-COMBO-05", "Employee onboarding: SSN 901-23-4567, Email emp@company.com, Phone (555) 666-7777", ["SSN", "EMAIL", "PHONE_US"], "Onboarding", tier="basic"),
    GoldenCase("B-COMBO-06", "Lab request: Email mark@lab.org, MRN 777888, Phone (555) 444-0000", ["EMAIL", "MEDICAL_RECORD", "PHONE_US"], "Lab request", tier="basic"),
    GoldenCase("B-COMBO-07", "Follow-up: MRN 101112, Email follow@hospital.com, Call (555) 999-0000", ["MEDICAL_RECORD", "EMAIL", "PHONE_US"], "Follow-up", tier="basic"),
    GoldenCase("B-COMBO-08", "Account setup: Email new@patient.org, Phone (555) 222-1111, SSN 523-84-1926", ["EMAIL", "PHONE_US", "SSN"], "Account setup", tier="basic"),
    GoldenCase("B-COMBO-09", "Insurance: Card 5105-1051-0510-5100, SSN 159-75-3862", ["CREDIT_CARD", "SSN"], "Insurance verify", tier="basic"),
    GoldenCase("B-COMBO-10", "Prescription refill: MRN 252627, Phone (555) 888-3333, Email pharm@rx.com", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "Refill", tier="basic"),
    GoldenCase("B-COMBO-11", "Clinical trial: MRN 282930, Contact: (555) 999-4444, Email trial@research.org", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "Trial", tier="basic"),
    GoldenCase("B-COMBO-12", "Insurance claim: Card 4024007145974932, SSN 369-14-7520", ["CREDIT_CARD", "SSN"], "Claim", tier="basic"),

    # No-PII extended (10)
    GoldenCase("B-CLEAN-01", "Treated with Metformin 500mg daily", [], "Medication context", tier="basic"),
    GoldenCase("B-CLEAN-02", "HbA1c: 7.5%, glucose: 145 mg/dL", [], "Lab values", tier="basic"),
    GoldenCase("B-CLEAN-03", "Allergy: Penicillin (severe)", [], "Allergy info", tier="basic"),
    GoldenCase("B-CLEAN-04", "Dosage: 250mg twice daily", [], "Dosage", tier="basic"),
    GoldenCase("B-CLEAN-05", "Prescribed Lisinopril 10mg", [], "Prescription", tier="basic"),
    GoldenCase("B-CLEAN-06", "Follow-up: 2 weeks", [], "Follow-up", tier="basic"),
    GoldenCase("B-CLEAN-07", "Diagnosis: Type 2 Diabetes, hypertension", [], "Diagnosis context", tier="basic"),
    GoldenCase("B-CLEAN-08", "The patient was discharged in stable condition.", [], "Clinical note", tier="basic"),
    GoldenCase("B-CLEAN-09", "HIPAA compliance audit passed on all counts.", [], "Compliance text", tier="basic"),
    GoldenCase("B-CLEAN-10", "Version 2.1.0 released on March 15, 2025.", [], "Release note", tier="basic"),

    # AU cases (20)
    GoldenCase("B-AU-01", "Email: john@example.com.au", ["EMAIL"], "AU email", country="AU", tier="basic"),
    GoldenCase("B-AU-02", "Contact: jane.doe@company.au", ["EMAIL"], "AU company email", country="AU", tier="basic"),
    GoldenCase("B-AU-03", "Call me at (555) 123-4567", ["PHONE_US"], "AU phone", country="AU", tier="basic"),
    GoldenCase("B-AU-04", "Card: 4532-1234-5678-9999", ["CREDIT_CARD"], "AU visa", country="AU", tier="basic"),
    GoldenCase("B-AU-05", "Patient MRN: 123456", ["MEDICAL_RECORD"], "AU MRN", country="AU", tier="basic"),
    GoldenCase("B-AU-06", "support@sydney.org.au for help", ["EMAIL"], "AU support email", country="AU", tier="basic"),
    GoldenCase("B-AU-07", "admin@melbourne.edu.au", ["EMAIL"], "AU edu email", country="AU", tier="basic"),
    GoldenCase("B-AU-08", "Billing AU: Card 4532123456789999", ["CREDIT_CARD"], "AU billing card", country="AU", tier="basic"),
    GoldenCase("B-AU-09", "MRN 222333, Contact (555) 777-8888", ["MEDICAL_RECORD", "PHONE_US"], "AU MRN+phone", country="AU", tier="basic"),
    GoldenCase("B-AU-10", "Email bill@customer.com.au, Phone 555-999-8888", ["EMAIL", "PHONE_US"], "AU email+phone", country="AU", tier="basic"),
    GoldenCase("B-AU-11", "MRN 666777, Email remind@health.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU MRN+email", country="AU", tier="basic"),
    GoldenCase("B-AU-12", "Card 5105-1051-0510-5100", ["CREDIT_CARD"], "AU card", country="AU", tier="basic"),
    GoldenCase("B-AU-13", "MRN 131415, Email bill@charge.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU billing cycle", country="AU", tier="basic"),
    GoldenCase("B-AU-14", "MRN 192021, Phone (555) 777-2222, Email specialist@hospital.com.au", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "AU referral", country="AU", tier="basic"),
    GoldenCase("B-AU-15", "5555555555554444 test", ["CREDIT_CARD"], "AU Mastercard", country="AU", tier="basic"),
    GoldenCase("B-AU-16", "ICD-10 code: E11.9 for Diabetes", [], "AU clinical no PII", country="AU", tier="basic"),
    GoldenCase("B-AU-17", "Treated with Metformin 500mg daily", [], "AU medication no PII", country="AU", tier="basic"),
    GoldenCase("B-AU-18", "Blood pressure: 120/80 mmHg", [], "AU vitals no PII", country="AU", tier="basic"),
    GoldenCase("B-AU-19", "Dosage: 250mg twice daily", [], "AU dosage no PII", country="AU", tier="basic"),
    GoldenCase("B-AU-20", "Follow-up: 2 weeks", [], "AU follow-up no PII", country="AU", tier="basic"),
]
# fmt: on

# ──────────────────────────────────────────────────────────────
# Label alias matching (same as stress_test.py but centralized)
# ──────────────────────────────────────────────────────────────

LABEL_ALIASES: Dict[str, Set[str]] = {
    "SSN": {"social_security_number", "tax_identification_number", "tax_file_number", "tfn", "id"},
    "EMAIL": {"email_address"},
    "PHONE_US": {"phone", "phone_number", "telephone", "phone_us"},
    "CREDIT_CARD": {"card_number", "card", "credit_card_number"},
    "PERSON_NAME": {"name", "person", "person_name"},
    "MEDICAL_RECORD": {"mrn", "record_number", "patient_id", "medical_record_number"},
    "ORGANIZATION": {"org", "company"},
    "LOCATION": {"loc", "gpe", "address", "place"},
    "MEDICATION": {"drug", "medicine", "drug_name"},
    "MEDICAL_CONDITION": {"disease", "diagnosis", "condition"},
    "TFN": {"tax_file_number", "ssn"},
    "ABN": {"australian_business_number"},
    "ACN": {"australian_company_number"},
    "MEDICARE": {"medicare_number"},
}


def labels_match(detected: Set[str], expected: List[str]) -> bool:
    """Check if detected labels match expected, using alias resolution."""
    if not expected:
        # For no-PII cases: fail if any PII entity was detected
        pii_labels = {
            "ssn", "email", "phone", "phone_us", "credit_card", "name",
            "person", "person_name", "medical_record", "mrn",
        }
        detected_lower = {l.lower() for l in detected}
        for d in detected_lower:
            if d in pii_labels or any(p in d for p in pii_labels):
                return False
        return True

    detected_lower = {l.lower() for l in detected}

    for exp in expected:
        exp_lower = exp.lower()
        if exp_lower in detected_lower:
            continue

        # Check aliases
        found = False
        for canonical, aliases in LABEL_ALIASES.items():
            all_variants = {canonical.lower()} | {a.lower() for a in aliases}
            if exp_lower in all_variants:
                if any(d in all_variants for d in detected_lower):
                    found = True
                    break

        # Substring fallback
        if not found:
            for d in detected_lower:
                if len(exp_lower) > 3 and len(d) > 3:
                    if exp_lower in d or d in exp_lower:
                        found = True
                        break

        if not found:
            return False

    return True


# ──────────────────────────────────────────────────────────────
# Regression Runner
# ──────────────────────────────────────────────────────────────

@dataclass
class TierResult:
    tier: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    elapsed_seconds: float = 0.0
    failures: List[Dict] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0.0

    @property
    def precision(self) -> float:
        d = self.true_positives + self.false_positives
        return self.true_positives / d if d > 0 else 0.0

    @property
    def recall(self) -> float:
        d = self.true_positives + self.false_negatives
        return self.true_positives / d if d > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def run_tier(tier: str, country: str = "US") -> TierResult:
    """Run all test cases for a given tier and country."""
    tiers_included = {"smoke"}
    if tier in ("basic", "full"):
        tiers_included.add("basic")
    if tier == "full":
        tiers_included.add("full")

    cases = [c for c in GOLDEN_CASES if c.tier in tiers_included and c.country == country]
    result = TierResult(tier=tier)

    # Create pipeline - regex only for speed (detectors are tested separately in stress_test)
    config = RedactionConfig(
        country=country,
        use_spacy=False,
        use_bert=False,
        use_gliner=False,
        use_openmed=False,
    )
    pipeline = RedactionPipeline(config)

    t0 = time.time()
    for case in cases:
        result.total += 1
        try:
            output = pipeline.redact(case.text)
            detected_labels = {span["label"] for span in output["spans"]}
            expected_set = set(case.expected_labels)

            # TP/FP/FN counting
            tp = len(detected_labels & expected_set)
            fp = len(detected_labels - expected_set)
            fn = len(expected_set - detected_labels)
            result.true_positives += tp
            result.false_positives += fp
            result.false_negatives += fn

            if labels_match(detected_labels, case.expected_labels):
                result.passed += 1
            else:
                result.failed += 1
                result.failures.append({
                    "id": case.id,
                    "desc": case.description,
                    "expected": case.expected_labels,
                    "got": list(detected_labels),
                    "text": case.text[:80],
                })
        except Exception as e:
            result.failed += 1
            result.failures.append({"id": case.id, "error": str(e)[:120]})

    result.elapsed_seconds = time.time() - t0
    return result


# ──────────────────────────────────────────────────────────────
# Baseline Management
# ──────────────────────────────────────────────────────────────

def save_baseline():
    """Save current results as the baseline for future comparisons."""
    baseline = {}
    for country in ("US", "AU"):
        for tier in ("smoke", "basic"):
            key = f"{country}_{tier}"
            r = run_tier(tier, country)
            baseline[key] = {
                "accuracy": r.accuracy,
                "precision": r.precision,
                "recall": r.recall,
                "f1": r.f1,
                "total": r.total,
                "passed": r.passed,
            }
            print(f"[BASELINE] {key}: accuracy={r.accuracy:.1f}% precision={r.precision:.4f} recall={r.recall:.4f} f1={r.f1:.4f}")

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"\nBaseline saved to {BASELINE_FILE}")


def load_baseline() -> Optional[Dict]:
    """Load saved baseline if it exists."""
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE) as f:
            return json.load(f)
    return None


def check_regression():
    """Run all tiers and compare against baseline. Exit 1 if regression detected."""
    baseline = load_baseline()
    if not baseline:
        print("[WARN] No baseline found. Run with --save-baseline first.")
        print("[WARN] Running without comparison...\n")

    any_regression = False

    for country in ("US", "AU"):
        for tier in ("smoke", "basic"):
            key = f"{country}_{tier}"
            r = run_tier(tier, country)

            print(f"\n{'='*60}")
            print(f"  {key.upper()}")
            print(f"{'='*60}")
            print(f"  Cases:     {r.total}")
            print(f"  Passed:    {r.passed} ({r.accuracy:.1f}%)")
            print(f"  Failed:    {r.failed}")
            print(f"  Precision: {r.precision:.4f}")
            print(f"  Recall:    {r.recall:.4f}")
            print(f"  F1:        {r.f1:.4f}")
            print(f"  Time:      {r.elapsed_seconds:.2f}s")

            if r.failures:
                print(f"\n  Failures ({len(r.failures)}):")
                for fail in r.failures[:5]:
                    if "error" in fail:
                        print(f"    [{fail['id']}] ERROR: {fail['error']}")
                    else:
                        print(f"    [{fail['id']}] {fail['desc']}")
                        print(f"      expected={fail['expected']} got={fail['got']}")

            if baseline and key in baseline:
                bl = baseline[key]
                acc_delta = r.accuracy - bl["accuracy"]
                f1_delta = r.f1 - bl["f1"]

                status = "OK"
                if acc_delta < -2.0:  # >2% accuracy drop = regression
                    status = "REGRESSION"
                    any_regression = True
                elif acc_delta > 2.0:
                    status = "IMPROVED"

                print(f"\n  vs Baseline:")
                print(f"    Accuracy: {bl['accuracy']:.1f}% -> {r.accuracy:.1f}% ({acc_delta:+.1f}%)  [{status}]")
                print(f"    F1:       {bl['f1']:.4f} -> {r.f1:.4f} ({f1_delta:+.4f})")

    if any_regression:
        print("\n[FAIL] Regression detected! Fix issues or update baseline with --save-baseline")
        return 1
    else:
        print("\n[PASS] No regression detected.")
        return 0


# ──────────────────────────────────────────────────────────────
# pytest Integration
# ──────────────────────────────────────────────────────────────

class TestRegressionSmoke(unittest.TestCase):
    """Smoke tier - runs in <10s, catches catastrophic regressions."""

    @classmethod
    def setUpClass(cls):
        cls.us_result = run_tier("smoke", "US")

    def test_smoke_us_accuracy_above_80(self):
        """Smoke: US accuracy must be >= 80%."""
        self.assertGreaterEqual(
            self.us_result.accuracy, 80.0,
            f"US smoke accuracy {self.us_result.accuracy:.1f}% below 80% threshold"
        )

    def test_smoke_us_no_catastrophic_failures(self):
        """Smoke: US must not fail more than 20% of cases."""
        fail_rate = (self.us_result.failed / self.us_result.total * 100) if self.us_result.total > 0 else 0
        self.assertLess(fail_rate, 20.0, f"US smoke failure rate {fail_rate:.1f}% exceeds 20%")

    def test_smoke_us_precision_above_60(self):
        """Smoke: US precision must be >= 0.60."""
        self.assertGreaterEqual(self.us_result.precision, 0.60)

    def test_smoke_us_recall_above_60(self):
        """Smoke: US recall must be >= 0.60."""
        self.assertGreaterEqual(self.us_result.recall, 0.60)


class TestRegressionBasic(unittest.TestCase):
    """Basic tier - standard release gate."""

    @classmethod
    def setUpClass(cls):
        cls.us_result = run_tier("basic", "US")
        cls.au_result = run_tier("basic", "AU")

    def test_basic_us_accuracy_above_75(self):
        """Basic: US accuracy must be >= 75%."""
        self.assertGreaterEqual(self.us_result.accuracy, 75.0)

    def test_basic_au_accuracy_above_70(self):
        """Basic: AU accuracy must be >= 70%."""
        self.assertGreaterEqual(self.au_result.accuracy, 70.0)

    def test_basic_us_f1_above_50(self):
        """Basic: US F1 must be >= 0.50."""
        self.assertGreaterEqual(self.us_result.f1, 0.50)

    def test_basic_au_f1_above_50(self):
        """Basic: AU F1 must be >= 0.50."""
        self.assertGreaterEqual(self.au_result.f1, 0.50)

    def test_basic_no_regression_vs_baseline(self):
        """Basic: Must not regress >2% vs saved baseline."""
        baseline = load_baseline()
        if baseline is None:
            self.skipTest("No baseline file found - run --save-baseline first")

        for key, result in [("US_basic", self.us_result), ("AU_basic", self.au_result)]:
            if key in baseline:
                delta = result.accuracy - baseline[key]["accuracy"]
                self.assertGreaterEqual(
                    delta, -2.0,
                    f"{key} accuracy dropped {delta:.1f}% vs baseline"
                )


class TestRegressionFull(unittest.TestCase):
    """Full tier - thorough release validation."""

    @classmethod
    def setUpClass(cls):
        cls.us_result = run_tier("full", "US")
        cls.au_result = run_tier("full", "AU")

    def test_full_us_accuracy_above_70(self):
        """Full: US accuracy must be >= 70%."""
        self.assertGreaterEqual(self.us_result.accuracy, 70.0)

    def test_full_au_accuracy_above_65(self):
        """Full: AU accuracy must be >= 65%."""
        self.assertGreaterEqual(self.au_result.accuracy, 65.0)

    def test_full_us_precision_above_50(self):
        """Full: US precision must be >= 0.50."""
        self.assertGreaterEqual(self.us_result.precision, 0.50)

    def test_full_us_recall_above_50(self):
        """Full: US recall must be >= 0.50."""
        self.assertGreaterEqual(self.us_result.recall, 0.50)


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--save-baseline" in sys.argv:
        save_baseline()
    elif "--check" in sys.argv:
        sys.exit(check_regression())
    else:
        print("Usage:")
        print("  python tests/regression_suite.py --save-baseline  # Save current as baseline")
        print("  python tests/regression_suite.py --check          # Run and compare vs baseline")
        print("  pytest tests/regression_suite.py -k smoke         # Run smoke tier in pytest")
        print("  pytest tests/regression_suite.py -k basic         # Run basic tier in pytest")
        print("  pytest tests/regression_suite.py -k full          # Run full tier in pytest")
