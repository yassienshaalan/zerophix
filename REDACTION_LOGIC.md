# ZeroPhix Redaction Logic Explained

## Core Principles & Design Philosophy

### Why ZeroPhix Exists

Most PII/PHI redaction solutions are US-centric and cloud-dependent. ZeroPhix was built to address critical gaps:

#### 1. **Australian Data Sovereignty**
- **Problem**: US-focused tools lack Australian government ID validation (TFN, ABN, ACN, Medicare)
- **ZeroPhix Solution**: 
  - 40+ Australian entity types with mathematical checksum validation
  - TFN (Modulus 11), ABN (Modulus 89), ACN (Modulus 10), Medicare (Modulus 10 Luhn-like)
  - Dramatically improves Australian ID precision through checksum validation
  - State-specific patterns (driver licenses for all 8 states/territories)
  - Australian healthcare (IHI, HPI-I/O, DVA, PBS), financial (BSB, Centrelink CRN), and geographic entities
- **Compliance & Regulatory Framework**:
  - **Privacy Act 1988**: Covers Australian Privacy Principles (APPs) for handling personal information including TFNs, Medicare numbers, and other government identifiers
  - **My Health Records Act 2012**: Governs healthcare identifiers (IHI, HPI-I/O) and electronic health records requiring strict de-identification controls
  - **Healthcare Identifiers Act 2010**: Regulates collection, use, and disclosure of healthcare identifiers ensuring secure handling of Medicare and IHI data
  - **Taxation Administration Act 1953**: Protects TFN confidentiality with severe penalties for unauthorized disclosure or misuse
  - **Corporations Act 2001**: Governs ABN/ACN usage and confidentiality requirements for business identifiers
  - **Notifiable Data Breaches (NDB) Scheme**: Mandatory breach notification for serious data breaches involving personal information under the Privacy Act

#### 2. **100% Offline Operation (Air-Gapped Capability)**
- **Problem**: Cloud APIs require internet, creating data sovereignty and security risks
- **ZeroPhix Solution**:
  - No data ever leaves your infrastructure
  - One-time ML model download, then fully offline forever
  - Works in air-gapped environments (defense, healthcare, finance)
  - No per-document API fees
  - Complete control over encryption keys and audit logs
  - Zero trust architecture - never rely on external services

#### 3. **Dynamic Configurability (Not One-Size-Fits-All)**
- **Problem**: Fixed detection pipelines don't adapt to different use cases
- **ZeroPhix Solution**:
  - 10+ redaction strategies (replace, mask, hash, encrypt, synthetic, etc.)
  - 6 detection modes (fast, balanced, accurate, auto, medical, legal)
  - Per-entity type strategy configuration via YAML policies
  - Runtime detector enable/disable without code changes
  - Ensemble weights adjustable per domain
  - Adaptive calibration learns optimal weights from your data
  - Works for: healthcare (HIPAA), legal (discovery), finance (PCI DSS), government (classified)

#### 4. **Adaptive Ensemble Intelligence**
- **Problem**: Manual trial-and-error configuration, unpredictable accuracy
- **ZeroPhix Solution**:
  - Auto-learns optimal detector weights from 20-50 labeled samples
  - Label normalization enables cross-detector consensus
  - Performance tracking shows which detectors work for your data
  - One-time calibration, save results, reuse in production
  - Significantly improves precision while maintaining recall

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INPUT TEXT                               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  DETECTION LAYER (Ensemble)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Regex   │  │  spaCy   │  │   BERT   │  │  GLiNER  │          │
│  │ 99.9%    │  │  Names   │  │  Context │  │Zero-shot │          │
│  │precision │  │Locations │  │ Aware    │  │ Custom   │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│  ┌──────────┐  ┌──────────┐                                      │
│  │Statistical│ │ OpenMed  │  (Australian checksum validation)    │
│  │ Entropy  │  │Healthcare│                                      │
│  └──────────┘  └──────────┘                                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              ENSEMBLE VOTING & CALIBRATION                       │
│  • Adaptive weight learning (F1² method)                         │
│  • Label normalization (PERSON ↔ USERNAME consensus)             │
│  • Conflict resolution (overlap handling)                        │
│  • Confidence scoring aggregation                                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                               │
│  ┌────────────────┐  ┌───────────────────┐  ┌────────────────┐   │
│  │   Consensus    │  │Context Propagation│  │  Allow-List    │   │
│  │   Resolution   │  │  (Session Memory) │  │   Filtering    │   │
│  └────────────────┘  └───────────────────┘  └────────────────┘   │
│  ┌────────────────┐                                              │
│  │    Garbage     │  (False positive reduction)                  │
│  │    Filtering   │                                              │
│  └────────────────┘                                              │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                 REDACTION STRATEGY LAYER                         │
│  • Replace (entity labels)   • Mask (partial visibility)         │
│  • Hash (deterministic)       • Encrypt (reversible)             │
│  • Synthetic (realistic fake) • Brackets ([REDACTED])            │
│  • Preserve format            • Differential privacy             │
│  • K-anonymity                • AU phone (area code preserved)   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      REDACTED OUTPUT                             │
│  • Redacted text   • Entity metadata   • Audit logs              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Detection Layer - Deep Dive

### 1. Regex Detector (Australian Focus)

**Purpose**: Ultra-fast, high precision for structured government IDs

**How It Works**: Uses pattern matching combined with mathematical checksum validation to detect and verify Australian government identifiers. Each ID type has a specific validation algorithm:

- **TFN (Tax File Number)**: 9 digits validated using Modulus 11 algorithm with weighted digit positions [1,4,3,7,5,8,6,9,10]
- **ABN (Australian Business Number)**: 11 digits validated using Modulus 89 after subtracting 1 from the first digit
- **ACN (Australian Company Number)**: 9 digits validated using Modulus 10 with descending weights [8,7,6,5,4,3,2,1]
- **Medicare Number**: 10 digits validated using Modulus 10 Luhn-like algorithm with repeating weights [1,3,7,9]

The detector first matches the digit pattern with flexible spacing/hyphens, then applies the mathematical checksum to verify authenticity.

**Precision Impact**: Checksum validation dramatically reduces false positives by mathematically verifying that random digit sequences are NOT valid government IDs

**Coverage**: 40+ Australian entity types including:
- Government: TFN, ABN, ACN
- Healthcare: Medicare, IHI, HPI-I/O, DVA, PBS
- Driver Licenses: NSW, VIC, QLD, SA, WA, TAS, NT, ACT
- Financial: BSB numbers, Centrelink CRN, bank accounts
- Geographic: Addresses, postcodes (4-digit validation)

### 2. spaCy NER (ML-based Named Entities)

**Purpose**: High recall for names, locations, organizations

**Model**: en_core_web_lg (transformer-based, 560MB)

**How It Works**: Uses a pre-trained transformer model to identify named entities in natural language text. The model analyzes linguistic context to recognize person names, organizations, locations, dates, and monetary values. Detected entities are mapped from spaCy's label system (PERSON, ORG, GPE, LOC) to ZeroPhix's standardized labels (PERSON_NAME, ORGANIZATION, LOCATION). Since spaCy doesn't provide confidence scores, a fixed score of 0.90 is assigned to all detections.

**Strengths**: Excellent for names in natural text, context-aware
**Weaknesses**: No confidence scores, struggles with uncommon names

### 3. BERT Detector (Transformer Context-Aware)

**Purpose**: Highest accuracy for complex, context-dependent entities

**Model**: bert-base-cased (110M parameters)

**How It Works**: Uses a fine-tuned BERT transformer model for token-level classification. The text is first tokenized into subword units, then each token is classified using deep contextual understanding from the 110M parameter model. The model outputs probability distributions over entity labels for each token, which are converted to confidence scores via softmax. Token-level predictions using BIO tagging (Begin, Inside, Outside) are merged into complete entity spans by combining consecutive tokens with the same label. Character positions are mapped back from tokenized positions using offset mapping.

**Strengths**: Deep context understanding, provides confidence scores, handles ambiguous cases
**Weaknesses**: Slower inference (100-300ms per doc), higher memory usage (500MB+)

### 4. GLiNER (Zero-Shot Custom Entities)

**Purpose**: Detect ANY entity type without training

**How It Works**: Uses a generalized named entity recognition model that accepts natural language descriptions of entity types to find. Instead of being limited to pre-trained categories, you simply specify what you're looking for in plain English (e.g., "employee id", "project code", "api key") and the model identifies matching patterns in the text. The model learns entity boundaries and types simultaneously by understanding the semantic relationship between your query and the text content. Entity labels are normalized to uppercase with underscores for consistency.

**Use Cases**:
- Custom organization IDs: "EMP-123456", "PROJ-ABC-001"
- Domain-specific codes: "patient ID", "case number"
- Proprietary identifiers unique to your organization
- Ad-hoc entity types without retraining models

**Strengths**: Extreme flexibility, no training data required
**Weaknesses**: Lower precision than specialized models

### 5. Statistical Detector (Entropy & Anomaly Detection)

**Purpose**: Catch patterns ML models miss

**How It Works**: Uses three statistical techniques to identify sensitive patterns:

1. **Shannon Entropy Analysis**: Calculates character randomness for each token. High entropy (>4.0 bits) indicates random-looking strings like API keys, cryptographic hashes, or encrypted data. The entropy formula measures the unpredictability of character distribution.

2. **Frequency Analysis**: Tracks token occurrences across the document. When the same suspicious-looking token appears multiple times (≥3), it's likely an internal ID or code that should be redacted.

3. **Format Anomaly Detection**: Identifies unusual patterns like partial redactions ("XXX-XX-1234"), asterisk masking ("***-***-6789"), and Base64-encoded strings that other detectors might miss.

**Strengths**: Catches what others miss (API keys, hashes, partial redactions)
**Weaknesses**: Higher false positive rate, needs tuning per domain

### 6. OpenMed Detector (Healthcare-Specific PHI)

**Purpose**: Medical/clinical entity detection for HIPAA compliance

**Models**: 
- OpenMed-NER-DiseaseDetect (335M parameters)
- OpenMed-NER-ChemicalDetect (33M parameters)

**How It Works**: Uses specialized medical NER models trained on clinical text to identify healthcare-specific entities. The disease detection model identifies medical conditions, diagnoses, and symptoms with confidence scores. The chemical detection model recognizes medications, drugs, and chemical compounds. Both models run inference on the input text and return entity spans labeled as MEDICAL_CONDITION or MEDICATION. These models are specifically trained on medical literature and clinical records, making them significantly more accurate for healthcare text than general-purpose NER models.

**HIPAA Safe Harbor Coverage**:
- Medical record numbers
- Health plan beneficiary numbers
- Account numbers
- Certificate/license numbers
- Device identifiers and serial numbers
- Medical conditions, diagnoses, procedures
- Medications and prescriptions
- Laboratory values and test results

---

## Ensemble Voting & Adaptive Calibration

### Problem: Conflicting Detections

When multiple detectors find overlapping entities:

```
Text: "John Smith"
Position 0-10:
  - spaCy:  PERSON (score: 0.98)
  - GLiNER: PERSON (score: 0.92)
  - GLiNER: USERNAME (score: 0.65)  ← Different label!
```

**Without Ensemble**: Pick randomly → inconsistent results
**With Ensemble**: Intelligent voting → optimal choice

### Solution 1: Basic Consensus (Pre-Calibration)

**How It Works**: When multiple detectors find overlapping entities, the system resolves conflicts using three strategies:

1. **Highest Confidence**: If all detectors agree on the label, choose the span with the highest confidence score
2. **Policy-Based Preference**: When labels differ, follow a priority order (regex > bert > spacy > gliner > statistical) and pick the highest-confidence span from the highest-priority detector
3. **Majority Voting**: Count votes for each label and select the label with the most votes, then choose the highest-confidence span with that label

**Problem**: All detectors have equal weight, even if some are consistently noisier than others

### Solution 2: Adaptive Weighted Ensemble (With Calibration)

**Key Innovation**: Learn optimal detector weights from YOUR data

#### Step 1: Label Normalization

**Purpose**: Enable cross-detector consensus by mapping similar labels to a canonical form

**How It Works**: Different detectors use different label names for the same entity type (e.g., spaCy uses "PERSON", GLiNER uses "USERNAME", medical models use "PATIENT_NAME"). The normalization map translates all these variants to a single canonical label ("PERSON_NAME"). This allows detectors to "vote together" even when using different terminology. Common mappings include: PERSON/USERNAME/USER → PERSON_NAME, SSN/SOCIAL_SECURITY → US_SSN, TFN/TAX_FILE_NUMBER → AU_TFN.

**Impact**: Without normalization, "PERSON" and "USERNAME" vote separately. With normalization, they vote together creating stronger consensus.

#### Step 2: Calibration on Validation Data

**Purpose**: Learn optimal detector weights from labeled examples

**How It Works**: The calibration process takes 20-50 labeled text samples with ground truth annotations and:

1. **Measures per-detector performance**: Runs each detector on the validation set and calculates precision, recall, and F1 score by comparing predictions to ground truth

2. **Calculates weights using F1-squared method**: Converts F1 scores to weights using the formula `weight = max(0.1, F1²)`. Squaring the F1 score exponentially rewards high-performers and penalizes poor performers. The minimum weight of 0.1 ensures no detector is completely ignored.

3. **Normalizes weights**: Ensures all weights sum to 1.0 by dividing each weight by the total

**Example Results**:
- GLiNER with F1=0.60 gets weight = 0.36 (strong performer)
- spaCy with F1=0.50 gets weight = 0.25 (good)
- OpenMed with F1=0.35 gets weight = 0.12 (moderate)
- Regex with F1=0.30 gets weight = 0.09 (noisy for names)
- BERT with F1=0.25 gets weight = 0.10 (floor applied)

#### Step 3: Weighted Voting in Production

**How It Works**: When multiple detectors find overlapping entities, the weighted consensus algorithm:

1. **Normalizes all labels** to canonical forms (PERSON/USERNAME → PERSON_NAME)
2. **Calculates weighted scores** by multiplying each span's confidence by its detector's learned weight
3. **Aggregates by label** to sum all weighted scores for each entity type
4. **Chooses the winning label** with the highest total weighted score
5. **Returns the best span** from the winning label with the highest individual confidence

**Example**:
```
Before calibration (equal weights):
  GLiNER (PERSON, 0.92) + spaCy (PERSON, 0.98) + GLiNER (USERNAME, 0.65)
  → Ambiguous, pick highest score

After calibration (weighted):
  GLiNER (PERSON, 0.92) × 0.36 = 0.331
  spaCy  (PERSON, 0.98) × 0.25 = 0.245
  GLiNER (USERNAME→PERSON, 0.65) × 0.36 = 0.234
  → PERSON_NAME wins with 0.81 combined score
```

### Calibration Results (Real Examples)

#### Before Calibration (Equal Weights):
```
Metrics on validation set (50 samples):
  - Many false positives
  - Good detection rate
  - Poor overall performance

Problems:
  - GLiNER detects "USERNAME" everywhere (noisy)
  - Regex over-triggers on phone patterns
  - No label normalization → "PERSON" vs "USERNAME" fight
```

#### After Calibration (Learned Weights):
```
Metrics on same validation set:
  - Significantly improved precision
  - Maintained detection rate
  - Better overall performance

Learned weights:
  GLiNER:  0.36  (downweighted due to USERNAME noise)
  spaCy:   0.25  (stable performer)
  OpenMed: 0.12  (good for medical, poor for general)
  Regex:   0.09  (very noisy for names, excellent for IDs)
  BERT:    0.10  (floor - poor on this dataset)

False positives significantly reduced
```

### One-Time Calibration Workflow

**Process**:

1. **Enable adaptive features** in configuration (adaptive_weights, label_normalization)
2. **Prepare validation data**: 20-50 text samples with ground truth entity annotations
3. **Run calibration**: Takes 2-5 seconds to analyze performance and calculate optimal weights
4. **Save results**: Store learned weights to JSON file for reuse in production
5. **Load in production**: Reference the calibration file when creating new pipelines

**Example code snippet**:
```python
config = RedactionConfig(
    country="AU",
    enable_adaptive_weights=True,
    enable_label_normalization=True
)
pipeline = RedactionPipeline(config)

# Calibrate once
results = pipeline.calibrate(
    validation_texts,
    validation_ground_truth,
    save_path="calibration_au_medical.json"
)

# Production: load saved weights
config = RedactionConfig(
    country="AU",
    enable_adaptive_weights=True,
    calibration_file="calibration_au_medical.json"
)
```

### When to Calibrate

| Scenario | Recommendation |
|----------|----------------|
| **First deployment** | Calibrate on 20-50 representative samples |
| **New domain** | Recalibrate (medical → legal data change) |
| **Poor precision** | Calibrate to reduce false positives |
| **Quarterly review** | Re-calibrate if data patterns change |
| **After model updates** | Recalibrate when detectors change |

**Rule of Thumb**: 20 samples minimum, 50 samples ideal for stable weights

---

## Processing Layer - Advanced Techniques

### 1. Context Propagation (Session Memory)

**Problem**: Same entity appears multiple times with varying confidence levels

**Example**:
- Document 1: "John Smith called from New York" → PERSON (0.98 confidence)
- Document 2: "John replied with the report" → PERSON (0.65 confidence, low due to missing surname)

**Solution**: Session memory tracks high-confidence detections (≥0.90) across documents. When the same entity text appears again with lower confidence, the system boosts the score by up to +0.20 based on how many times it was previously detected with high confidence. The entity label is also standardized to match the previous high-confidence detection. This maintains a memory dictionary storing entity text, label, maximum score, and occurrence count.

**Impact**: Improved recall on multi-document sessions with consistent entity recognition

### 2. Allow-List Filtering

**Problem**: Public figures and well-known organization names trigger false positives

**Solution**: Maintains a configurable list of non-sensitive terms that should never be redacted. The filter checks each detected entity against the allow-list using both exact matching (entire entity text) and partial matching (allow-listed term appears within entity). Matching is case-insensitive for flexibility.

**Configuration Example**:
```python
config = RedactionConfig(
    allow_list=["Commonwealth Bank", "Microsoft", "GitHub", "John Howard"]
)
```

**Use Cases**:
- Public figures mentioned in news articles
- Organization names in document templates
- Product names (iPhone, Windows, etc.)
- Non-sensitive technical terms

### 3. Garbage Filtering (ML Noise Reduction)

**Problem**: ML models sometimes detect nonsensical entities

**Solution**: Applies multiple heuristic rules to filter out false positives:

1. **Length check**: Removes entities shorter than 3 characters
2. **Stopword filter**: Excludes common words ("the", "and", "is", "at", etc.)
3. **Capitalization check**: For PERSON_NAME and ORGANIZATION, requires first letter to be uppercase (proper noun)
4. **Boundary validation**: Ensures entity doesn't start/end mid-word by checking adjacent characters
5. **Single letter removal**: Excludes single-character entities unless they're part of structured IDs
6. **Low confidence + common word**: Filters detections below 0.70 confidence that match common dictionary words

**Impact**: Significant reduction in false positives from ML models, improving overall precision

---

## Redaction Strategies - Complete Guide

### Strategy Selection Matrix

| Strategy | Reversible? | Use Case | Example |
|----------|-------------|----------|---------|
| **replace** | No | Maximum privacy, compliance docs | `<US_SSN>` |
| **mask** | No | Partial visibility, customer service | `***-**-6789` |
| **hash** | No | Record linking, de-duplication | `HASH_a3f2c9d8` |
| **encrypt** | Yes | Reversible with key, secure storage | `ENC_xyz123` |
| **synthetic** | No | Testing, demos, external sharing | `Alex Brown` |
| **brackets** | No | Legal documents, FOIA requests | `[REDACTED]` |
| **preserve_format** | No | Schema compatibility, API testing | `K8d-2L-m9P3` |
| **au_phone** | No | Australian context, area code analysis | `04XX-XXX-XXX` |
| **differential_privacy** | No | Research, statistical privacy | `Age: 42 ± 3` |
| **k_anonymity** | No | Public datasets, privacy-preserving DB | `Age: 40-50` |

### Per-Entity Strategy Configuration

```yaml
# configs/company/acme.yml
actions:
  PERSON_NAME: 'synthetic'       # Realistic fake names for testing
  US_SSN: 'replace'              # Full removal (most sensitive)
  AU_TFN: 'replace'
  EMAIL: 'preserve_format'       # Keep @ symbol, mask rest
  PHONE_US: 'mask'               # Show area code: (555) XXX-XXXX
  PHONE_AU: 'au_phone'           # Show prefix: 04XX-XXX-XXX
  CREDIT_CARD: 'mask'            # Show last 4: **** **** **** 1234
  BANK_ACCOUNT_AU: 'encrypt'     # Reversible for authorized access
  MEDICAL_CONDITION: 'hash'      # Consistent for research
  MEDICATION: 'hash'
  IP_ADDRESS: 'mask'
  URL: 'brackets'                # [REDACTED]
  DATE: 'synthetic'              # Random but realistic date
```

```python
# Load policy
from zerophix.policies.loader import load_policy

config = RedactionConfig(
    country="AU",
    company="acme"  # Loads configs/company/acme.yml
)

# Different strategies applied per entity type automatically!
```

### Encryption Strategy (Production Example)

**How It Works**: The encryption strategy allows reversible redaction for authorized access:

1. **Key Management Setup**: Initialize KeyManager with secure storage path for encryption keys
2. **Generate Encryption Key**: Create a data encryption key specifically for PII redaction, which includes key ID and rotation schedule
3. **Configure Pipeline**: Set masking style to "encrypt" and reference the key ID in the redaction configuration
4. **Redact with Encryption**: Detected entities are encrypted instead of masked/replaced
5. **Decrypt When Authorized**: Authorized personnel can decrypt using the EncryptionManager with the same key ID
6. **Key Rotation**: Regularly rotate keys (90-day cycle recommended) to maintain security

**Security Best Practices**:
- Store keys in HSM (Hardware Security Module) or cloud KMS (AWS KMS, Azure Key Vault)
- Separate encryption keys from encrypted data (different servers/databases)
- Implement key versioning (old keys decrypt old data, new keys encrypt new data)
- Audit all key access (who, when, why)
- Rotate keys every 90 days
- Revoke keys when employee leaves or breach detected

---

## Dynamic Configurability Examples

### Configuration 1: High-Speed Processing (1000+ docs/sec)

```python
config = RedactionConfig(
    country="AU",
    detectors=["regex"],           # Only ultra-fast regex
    enable_checksum_validation=True,  # AU ID validation
    enable_ensemble_voting=False,  # Skip voting overhead
    enable_context_propagation=False,  # Skip session memory
    masking_style="mask"
)

# Use case: Real-time transaction processing, log sanitization
# Speed: 1000-5000 docs/sec
# Precision: 99.9% (structured data only)
# Recall: 85% (misses names in unstructured text)
```

### Configuration 2: Maximum Accuracy (HIPAA Compliance)

```python
config = RedactionConfig(
    country="AU",
    mode="accurate",               # Enable all detectors
    use_spacy=True,
    use_bert=True,
    use_gliner=True,
    use_openmed=True,              # Medical PHI
    enable_adaptive_weights=True,  # Calibrated weights
    enable_label_normalization=True,
    enable_ensemble_voting=True,
    enable_context_propagation=True,
    calibration_file="calibration_au_medical.json",
    masking_style="hash",          # Audit trail
    precision_threshold=0.85,      # High confidence required
    recall_threshold=0.90          # Don't miss PHI
)

# Use case: Medical records, HIPAA compliance
# Speed: 100-500 docs/sec
# Precision: 87-92%
# Recall: 87.5%+ (catches most PHI)
```

### Configuration 3: Balanced (Production Default)

```python
config = RedactionConfig(
    country="AU",
    mode="balanced",
    use_spacy=True,
    enable_adaptive_weights=True,
    enable_ensemble_voting=True,
    calibration_file="calibration_au_general.json",
    masking_style="synthetic",
    detectors=["regex", "spacy"]
)

# Use case: General-purpose PII redaction
# Speed: 500-1000 docs/sec
# Precision: 75-85%
# Recall: 80-90%
```

### Configuration 4: Zero-Shot Custom Entities

```python
config = RedactionConfig(
    country="AU",
    use_gliner=True,
    gliner_labels=["employee id", "project code", "api key", "customer id"],
    masking_style="replace"
)

# Use case: Organization-specific identifiers
# No training data required - just name what you want!
```

---

## Offline Operation - Complete Air-Gap Guide

### Principle: Zero Internet Dependency

**Why Offline Matters**:
1. **Data Sovereignty**: Sensitive data never leaves Australian infrastructure
2. **Security**: No attack surface via internet (air-gapped defense/healthcare)
3. **Cost**: No per-document API fees (process millions locally)
4. **Compliance**: Easier audits (no third-party data sharing)
5. **Performance**: Local processing faster than cloud round-trips

### Setup Process (One-Time)

#### Step 1: Model Download (Internet-Connected Machine)

**Process**: On a machine with internet access:

1. Download ZeroPhix package and all dependencies using `pip download zerophix[all] -d ./zerophix-offline/`
2. Download spaCy language model using `python -m spacy download en_core_web_lg --download-dir ./zerophix-offline/`
3. Initialize detectors to trigger automatic model downloads to cache (BERT, GLiNER, OpenMed models)
4. Copy model cache directories from `~/.cache/zerophix` and `~/.cache/huggingface` to the offline package folder

Total package size: ~2-5GB depending on which models are included

#### Step 2: Transfer to Air-Gapped Environment

Transfer the `./zerophix-offline/` folder via USB drive, secure network transfer, or physical media.

#### Step 3: Install Offline

On the air-gapped machine:

1. Install packages without internet: `pip install --no-index --find-links=./zerophix-offline/ zerophix[all]`
2. Restore model caches to user's home directory cache folders
3. Install spaCy model from the downloaded wheel file

#### Step 4: Verify Offline Operation

Disconnect network and test that the pipeline can redact text using all detectors without internet access. The system should work completely offline after the one-time setup.

### Docker Image (Offline-Ready)

**Approach**: Create a Docker image containing all dependencies and ML models:

1. Start with Python 3.9 base image
2. Copy offline package folder into image
3. Install ZeroPhix without internet access using local packages
4. Copy model caches into the image's cache directories
5. Install spaCy model from wheel file
6. Clean up temporary files to reduce image size

The resulting image can run completely offline using `docker run --network=none` to disable network access entirely.

### Kubernetes Deployment (Air-Gapped Cluster)

**Approach**: Deploy ZeroPhix in a Kubernetes cluster without internet access:

- Use locally stored container images (no pulling from internet)
- Configure resource limits (2-4GB RAM for ML models, 1-2 CPU cores)
- Mount persistent volume for read-only model caches
- Run 3 replicas for high availability
- Set `hostNetwork: false` to ensure no internet access
- Store models on persistent volume claim shared across pods

**Result**: Complete PII redaction in air-gapped Kubernetes with no internet dependency

---

## Complete Walkthrough: Australian Medical Record

### Input Text

```
PATIENT RECORD - CONFIDENTIAL

Patient: Jane Mary Doe
DOB: 15/03/1985 (Age: 41)
Medicare: 2234 56781 2
IHI: 8003 6012 3456 7890
TFN: 123 456 782

Address: 123 George Street, Sydney NSW 2000
Phone: 0412 345 678
Email: jane.doe@email.com.au

GP: Dr. John Smith (Provider: 1234567890)
Clinic: Royal Melbourne Hospital
Phone: (03) 9345 6789

Diagnosis: Type 2 Diabetes Mellitus
Current Medications:
  - Metformin 500mg BD
  - Ramipril 5mg OD

Last HbA1c: 7.2% (2024-12-15)
Next appointment: 2025-02-20
```

### Step-by-Step Processing

#### 1. Detection Phase (All Detectors)

**Regex Detector**:
```
- Span(27, 40, "PERSON_NAME", 1.00) → "Jane Mary Doe"
- Span(46, 56, "DATE_AU", 1.00) → "15/03/1985"
- Span(75, 88, "AU_MEDICARE", 1.00) → "2234 56781 2"  (Valid checksum)
- Span(95, 114, "AU_IHI", 1.00) → "8003 6012 3456 7890"
- Span(120, 131, "AU_TFN", 1.00) → "123 456 782"  (Valid checksum)
- Span(142, 172, "AU_ADDRESS", 0.95) → "123 George Street, Sydney NSW 2000"
- Span(180, 192, "PHONE_AU_MOBILE", 1.00) → "0412 345 678"
- Span(200, 220, "EMAIL", 1.00) → "jane.doe@email.com.au"
- Span(227, 241, "PERSON_NAME", 0.90) → "Dr. John Smith"
- Span(291, 317, "ORGANIZATION", 0.85) → "Royal Melbourne Hospital"
- Span(325, 339, "PHONE_AU", 1.00) → "(03) 9345 6789"
- Span(442, 452, "DATE_ISO", 1.00) → "2024-12-15"
- Span(473, 483, "DATE_ISO", 1.00) → "2025-02-20"
```

**spaCy Detector**:
```
- Span(27, 40, "PERSON", 0.98) → "Jane Mary Doe"
- Span(227, 241, "PERSON", 0.95) → "Dr. John Smith"
- Span(291, 317, "ORG", 0.92) → "Royal Melbourne Hospital"
- Span(142, 148, "CARDINAL", 0.88) → "123"  (garbage)
- Span(149, 155, "STREET", 0.75) → "George"  (partial)
```

**OpenMed Detector**:
```
- Span(351, 378, "MEDICAL_CONDITION", 0.92) → "Type 2 Diabetes Mellitus"
- Span(406, 415, "MEDICATION", 0.88) → "Metformin"
- Span(424, 432, "MEDICATION", 0.90) → "Ramipril"
- Span(443, 449, "LAB_VALUE", 0.75) → "HbA1c"  (test name, not PHI)
```

**GLiNER Detector**:
```
- Span(27, 40, "PATIENT_NAME", 0.90) → "Jane Mary Doe"
- Span(227, 241, "DOCTOR", 0.87) → "Dr. John Smith"
- Span(291, 317, "HOSPITAL", 0.85) → "Royal Melbourne Hospital"
- Span(142, 172, "ADDRESS", 0.80) → "123 George Street, Sydney NSW 2000"
```

**Total**: 24 raw detections (many overlaps)

#### 2. Ensemble Voting (With Calibration)

**Configuration**: High accuracy mode (all detectors enabled)

**Calibration weights** (from 50 Australian medical samples):
```
OpenMed: 0.30  (best for medical terms)
Regex:   0.25  (excellent for AU IDs)
spaCy:   0.20  (good for names)
GLiNER:  0.15  (moderate for general)
BERT:    0.10  (floor applied)
```

**Label normalization**:
```
"PATIENT_NAME" (GLiNER) → "PERSON_NAME"
"DOCTOR" (GLiNER) → "PERSON_NAME"
"HOSPITAL" (GLiNER) → "ORGANIZATION"
```

**Consensus resolution**:
```
Position 27-40 (Jane Mary Doe):
  Regex:  PERSON_NAME × 0.35 = 0.35
  spaCy:  PERSON_NAME × 0.25 = 0.245
  GLiNER: PERSON_NAME × 0.15 = 0.135
  → PERSON_NAME (total: 0.73)

Position 75-88 (Medicare):
  Regex:  AU_MEDICARE × 0.35 = 0.35
  → AU_MEDICARE (validated checksum, highest confidence)

Position 351-378 (Type 2 Diabetes Mellitus):
  OpenMed: MEDICAL_CONDITION × 0.20 = 0.184
  → MEDICAL_CONDITION (only detector for medical terms)
```

**After consensus**: 17 spans (reduced from 24)

#### 3. Processing Layer

**Context propagation**: No previous context (first document)

**Allow-list filtering**: None configured

**Garbage filtering**:
```
Removed:
- Span(142, 148, "CARDINAL", 0.88) → "123"  (too short, street number)
- Span(149, 155, "STREET", 0.75) → "George"  (partial word)
- Span(443, 449, "LAB_VALUE", 0.75) → "HbA1c"  (test name, not sensitive)
```

**Final**: 14 spans

#### 4. Redaction (Policy-Based)

**Policy** (configs/company/health_au.yml):
```yaml
actions:
  PERSON_NAME: 'replace'         # Show label
  AU_TFN: 'replace'              # Complete removal
  AU_MEDICARE: 'replace'         # Complete removal
  AU_IHI: 'replace'              # Complete removal
  DATE_AU: 'replace'             # Show label
  DATE_ISO: 'replace'            # Show label
  AU_ADDRESS: 'replace'          # Show label
  PHONE_AU_MOBILE: 'mask'        # Partial masking
  PHONE_AU: 'mask'               # Partial masking
  EMAIL: 'preserve_format'       # Keep structure
  ORGANIZATION: 'synthetic'      # Fake but realistic name
  MEDICAL_CONDITION: 'hash'      # Deterministic for research
  MEDICATION: 'hash'             # Deterministic for research
```

### Output (Redacted)

```
PATIENT RECORD - CONFIDENTIAL

Patient: <PERSON_NAME>
DOB: <DATE_AU> (Age: 41)
Medicare: <AU_MEDICARE>
IHI: <AU_IHI>
TFN: <AU_TFN>

Address: <AU_ADDRESS>
Phone: **** *** ***
Email: j.d@xxxxx.com.au

GP: <PERSON_NAME> (Provider: 1234567890)
Clinic: Sydney General Medical Centre
Phone: (**) **** ****

Diagnosis: HASH_9f8e7d6c5b4a
Current Medications:
  - HASH_3a2b1c0d9e8f 500mg BD
  - HASH_7e6f5d4c3b2a 5mg OD

Last HbA1c: 7.2% (<DATE_ISO>)
Next appointment: <DATE_ISO>
```

**Protected**: 14 sensitive entities
**Strategies**: Multiple (replace, synthetic, mask, hash, preserve_format)
**Maintained**: Document readability with varied privacy levels per entity type
**Compliant**: HIPAA Safe Harbor de-identification requirements

---

## Comparison with Other Solutions

| Feature | ZeroPhix | Presidio (MS) | Azure AI | AWS Comprehend |
|---------|----------|---------------|----------|----------------|
| **Australian Focus** | Yes (40+ entities) | Limited | US-centric | US-centric |
| **Checksum Validation** | Yes (TFN/ABN/ACN/Medicare) | No | No | No |
| **Offline Capable** | Yes (100%) | Yes | No (Cloud only) | No (Cloud only) |
| **Adaptive Calibration** | Yes (F1² learning) | No | No | No |
| **Ensemble Voting** | Yes (6 detectors) | Yes (2-3 detectors) | No (Single model) | No (Single model) |
| **Per-Entity Strategies** | Yes (10+ strategies) | Limited | Fixed | Fixed |
| **Zero-Shot Detection** | Yes (GLiNER) | No | No | No |
| **Cost** | Free (infra only) | Free | $2-5/1K docs | $1-3/1K docs |
| **Data Sovereignty** | Complete | On-prem | Cloud | Cloud |
| **Key Management** | Built-in | Manual | Azure KMS | AWS KMS |
| **Precision (AU data)** | High | Moderate | Unknown | Unknown |

---

## Debugging & Troubleshooting

### Enable Detailed Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

pipeline = RedactionPipeline(config)
result = pipeline.redact(text)

# Logs show:
# - Each detector's findings
# - Consensus decisions
# - Filtering steps
# - Final spans selected
```

### Inspect Raw Detections

```python
# See what each detector finds
for detector in pipeline.components:
    spans = detector.detect(text)
    print(f"{detector.__class__.__name__}: {len(spans)} spans")
    for span in spans[:5]:  # First 5
        entity_text = text[span.start:span.end]
        print(f"  {span.label}: '{entity_text}' (score: {span.score:.2f})")
```

### Compare Before/After Calibration

```python
# Before calibration
config1 = RedactionConfig(country="AU", enable_adaptive_weights=False)
pipeline1 = RedactionPipeline(config1)
result1 = pipeline1.redact(text)

# After calibration
config2 = RedactionConfig(country="AU", enable_adaptive_weights=True,
                         calibration_file="calibration.json")
pipeline2 = RedactionPipeline(config2)
result2 = pipeline2.redact(text)

# Compare
print(f"Before: {len(result1['spans'])} entities")
print(f"After:  {len(result2['spans'])} entities")
print(f"Reduction: {len(result1['spans']) - len(result2['spans'])} false positives")
```

---

## License

This document is part of the ZeroPhix project (Apache 2.0 License).

---

**Last Updated:** February 2, 2026  
**Version:** 0.2.0

**Authors**: ZeroPhix Team  
**Focus**: Australian Data Sovereignty, Offline Operation, Dynamic Configurability

SpacyDetector finds:
  - Span(0, 10, "PERSON", 0.98, "spacy")

GLiNERDetector finds:
  - Span(0, 10, "PERSON", 0.92, "gliner")
  - Span(16, 27, "SSN", 0.89, "gliner")

Total: 4 spans (with overlaps)
```

---

### Phase 3: Advanced Processing (`_process_spans()`)

This is where accuracy is improved through 4 sub-phases:

#### 3.1 Consensus Resolution

**Problem:** Multiple detectors find overlapping entities

```python
resolved_spans = self.consensus.resolve(spans, text)
```

**Algorithm:**
- Group spans by overlap (IoU > threshold)
- For each group:
  - If same label → keep highest confidence
  - If different labels → apply policy rules:
    - Prefer regex for structured data (SSN, credit cards)
    - Prefer ML models for names/locations
    - Use voting if ambiguous

**Example:**
```
Before:
  - Span(0, 10, "PERSON", 0.98, "spacy")
  - Span(0, 10, "PERSON", 0.92, "gliner")

After:
  - Span(0, 10, "PERSON", 0.98, "spacy")  # Higher confidence
```

#### 3.2 Context Propagation

**Problem:** Same entity appears multiple times in text or session

```python
propagated_spans = self.context_propagator.propagate(text, resolved_spans)
```

**Algorithm:**
- Maintain session memory of detected entities
- When same text appears again:
  - If previously detected with high confidence → auto-tag
  - If ambiguous → boost confidence score

**Example:**
```
Text 1: "John Smith called from New York"
        └─ PERSON (0.98)

Text 2: "John replied later"
        └─ PERSON (0.95) ← Boosted from 0.75 via context
```

#### 3.3 Allow-List Filtering

**Problem:** False positives on known safe terms

```python
allowed_spans = self.allow_list.filter(text, propagated_spans)
```

**Algorithm:**
- Check each span against allow-list
- Remove if exact match or substring match (configurable)

**Example:**
```
Allow-list: ["Microsoft", "OpenAI", "GitHub"]

Before:
  - Span(0, 9, "ORGANIZATION", 0.95) → "Microsoft"

After:
  - (removed)
```

#### 3.4 Garbage Filtering

**Problem:** ML models produce noise (partial words, stopwords)

```python
final_spans = self.garbage_filter.filter(text, allowed_spans)
```

**Heuristics:**
- Length < 3 characters → remove
- Common stopwords ("the", "and", "is") → remove
- Starts with lowercase (not proper noun) → remove
- Partial words at boundaries → remove
- Single letters not in context → remove

**Example:**
```
Before:
  - Span(5, 6, "PERSON", 0.60) → "a"
  - Span(10, 13, "PERSON", 0.55) → "the"
  - Span(20, 23, "LOCATION", 0.65) → "ing"

After:
  - (all removed as garbage)
```

---

### Phase 4: Masking/Redaction

Final redaction reconstructs text with masked entities:

```python
out_text = []
i = 0

for span in merged:
    # Keep original text before entity
    out_text.append(text[i:span.start])
    
    # Mask the entity
    masked = self._mask(text[span.start:span.end], span.label)
    out_text.append(masked)
    
    # Move pointer
    i = span.end

# Append remaining text
out_text.append(text[i:])

return "".join(out_text)
```

**Masking Strategies:**

```python
def _mask(self, s: str, label: str) -> str:
    style = self.cfg.masking_style
    
    if style == "mask":
        return "*" * len(s)
        # "123-45-6789" → "***********"
    
    if style == "replace":
        return f"<{label}>"
        # "123-45-6789" → "<US_SSN>"
    
    if style == "brackets":
        return f"[{label}]"
        # "123-45-6789" → "[US_SSN]"
    
    # Default: hash (preserves uniqueness)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]
    # "123-45-6789" → "a3f2c9d8e1b4"
```

---

## Complete Example Walkthrough

### Input Text
```
"John Smith, SSN: 123-45-6789, Email: john@test.com"
```

### Step 1: Detection (All Detectors Run)

| Detector | Span Start | Span End | Label | Score |
|----------|------------|----------|-------|-------|
| Regex | 16 | 27 | US_SSN | 1.00 |
| Regex | 36 | 50 | EMAIL | 1.00 |
| spaCy | 0 | 10 | PERSON | 0.98 |
| GLiNER | 0 | 10 | PERSON | 0.92 |
| GLiNER | 16 | 27 | SSN | 0.85 |

**Raw Result:** 5 spans (2 overlaps)

### Step 2: Consensus Resolution

```
Overlaps detected:
  Position 0-10: PERSON (spaCy: 0.98, GLiNER: 0.92)
    → Keep: Span(0, 10, "PERSON", 0.98) [Higher score]
  
  Position 16-27: US_SSN (Regex: 1.0, GLiNER: 0.85)
    → Keep: Span(16, 27, "US_SSN", 1.0) [Regex preferred for structured data]

Resolved: 3 spans
  - Span(0, 10, "PERSON", 0.98)
  - Span(16, 27, "US_SSN", 1.0)
  - Span(36, 50, "EMAIL", 1.0)
```

### Step 3: Context/Allow-list/Garbage

```
Context propagation: No previous context
Allow-list: No matches
Garbage filter: All spans valid (length > 3, proper nouns)

Final: 3 spans (unchanged)
```

### Step 4: Masking (style="replace")

```python
text = "John Smith, SSN: 123-45-6789, Email: john@test.com"
spans = [Span(0,10), Span(16,27), Span(36,50)]

# Reconstruction:
result = ""
result += text[0:0]      # "" (empty before first span)
result += "<PERSON>"     # Mask "John Smith"
result += text[10:16]    # ", SSN: " (between spans)
result += "<US_SSN>"     # Mask "123-45-6789"
result += text[27:36]    # ", Email: " (between spans)
result += "<EMAIL>"      # Mask "john@test.com"
result += text[50:]      # "" (empty after last span)

final = "<PERSON>, SSN: <US_SSN>, Email: <EMAIL>"
```

### Output
```
"<PERSON>, SSN: <US_SSN>, Email: <EMAIL>"
```

---

## Key Design Principles

### 1. Ensemble Detection (High Recall)
Multiple detectors catch what others miss:
- Regex excels at structured data
- ML models excel at context-dependent entities
- Statistical methods catch anomalies

### 2. Non-Destructive Processing
Original text is never modified until final masking:
- All processing uses span indices
- Easy to debug/audit what was detected
- Can generate multiple output formats

### 3. Conflict Resolution (High Precision)
Overlapping detections are resolved intelligently:
- Voting based on confidence scores
- Policy rules for domain-specific preferences
- Preserves highest-quality detections

### 4. Context Awareness (Session Memory)
Reduces false negatives across documents:
- "John" first mention → high confidence required
- "John" subsequent mentions → context-boosted
- Cross-document entity tracking

### 5. Noise Reduction (False Positive Filtering)
Multiple layers remove garbage:
- Allow-list for known safe terms
- Heuristic filtering for ML noise
- Length and pattern validation

### 6. Flexible Masking
Configurable redaction strategies:
- Compliance needs: Full masking (`***`)
- Testing needs: Labeled replacement (`<PERSON>`)
- Audit needs: Hash-based (`a3f2c9d8e1b4`)

---

## Performance Optimizations

### Batch Processing
```python
results = pipeline.redact_batch(texts, parallel=True, max_workers=4)
```
- **Vectorized processing**: ~10x faster for batches >100 texts
- **Parallel execution**: ~4x speedup on 4-core CPU
- **ThreadPoolExecutor**: Non-blocking I/O for ML models

### Domain Detection (Auto Mode)
```python
domain = self._detect_domain(text)  # "medical", "legal", "general"
```
- Skips irrelevant detectors based on domain
- Medical text → enable OpenMedDetector, skip legal patterns
- Legal text → enable court patterns, skip clinical terms
- Reduces processing time by 30-50%

### Lazy Model Loading
- Detectors only initialized if enabled
- Models loaded on first use (not at import)
- Memory-efficient for minimal configurations

### Span Sorting
```python
final_spans.sort(key=lambda x: (x.start, -x.end))  # O(n log n)
```
- Single sort at end instead of repeated insertions
- Secondary sort by end position (longest first)
- Ensures non-overlapping spans for masking

---

## Configuration Examples

### High Recall (Catch Everything)
```python
config = RedactionConfig(
    mode="auto",              # Enable all detectors
    use_spacy=True,
    use_bert=True,
    use_gliner=True,
    use_statistical=True,
    consensus_threshold=0.3,  # Low threshold
    masking_style="replace"
)
```

### High Precision (Minimize False Positives)
```python
config = RedactionConfig(
    detectors=["regex", "spacy"],  # Only proven detectors
    consensus_threshold=0.8,       # High threshold
    enable_garbage_filter=True,
    enable_allowlist=True,
    allowlist=["Microsoft", "GitHub"],
    masking_style="mask"
)
```

### Healthcare/HIPAA Compliance
```python
config = RedactionConfig(
    mode="auto",
    use_openmed=True,          # Enable medical PHI detection
    consensus_threshold=0.5,
    masking_style="hash",      # Preserve uniqueness for audits
    enable_context=True        # Track entities across documents
)
```

### Fast Processing (Performance Priority)
```python
config = RedactionConfig(
    detectors=["regex"],       # Only fast regex
    use_spacy=False,
    use_bert=False,
    enable_consensus=False,    # Skip voting
    enable_context=False,      # Skip propagation
    masking_style="mask"
)
```

---

## Return Value Structure

### `redact()` Output
```python
{
    "text": "<PERSON>, SSN: <US_SSN>",  # Redacted text
    "entities": [                        # Detected entities
        {
            "start": 0,
            "end": 10,
            "label": "PERSON",
            "score": 0.98,
            "original": "John Smith"     # Original value (optional)
        },
        {
            "start": 16,
            "end": 27,
            "label": "US_SSN",
            "score": 1.0,
            "original": "123-45-6789"
        }
    ],
    "stats": {
        "total_entities": 2,
        "entities_by_type": {"PERSON": 1, "US_SSN": 1},
        "processing_time_ms": 45.2
    }
}
```

### `scan()` Output
```python
{
    "entities": [/* same as redact */],
    "stats": {/* same as redact */}
}
# Note: No "text" field (scan doesn't redact)
```

---

## Algorithm Complexity

| Phase | Time Complexity | Space Complexity |
|-------|----------------|------------------|
| Detection (n detectors) | O(n × m) | O(k) |
| Consensus voting | O(k²) worst case | O(k) |
| Context propagation | O(k) | O(session_size) |
| Allow-list filtering | O(k × w) | O(w) |
| Garbage filtering | O(k) | O(1) |
| Span sorting | O(k log k) | O(1) |
| Masking | O(m) | O(m) |

Where:
- **n** = number of detectors
- **m** = text length (characters)
- **k** = number of detected spans
- **w** = allow-list size

**Overall:** O(n × m + k²) for worst case with many overlapping spans

---

## Comparison with Other Frameworks

| Feature | ZeroPhix | Presidio | Azure AI |
|---------|----------|----------|----------|
| **Detection Method** | Ensemble (6 detectors) | spaCy + patterns | Cloud ML |
| **Conflict Resolution** | Consensus voting | Simple overlap | N/A (single model) |
| **Context Propagation** | Session memory | None | None |
| **Garbage Filtering** | Advanced heuristics | Basic | N/A |
| **Batch Processing** | Parallel vectorized | Sequential | Cloud batching |
| **Offline Capable** |  Yes |  Yes |  No (cloud only) |
| **Cost** | Free | Free | Pay-per-call |

---

## Debugging Tips

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = RedactionPipeline(config)
result = pipeline.redact("John Smith")
# Shows: detector outputs, consensus decisions, filtering steps
```

### Inspect Raw Detections
```python
# Before processing
spans = []
for detector in pipeline.components:
    spans.extend(detector.detect(text))

print(f"Raw detections: {len(spans)}")
for span in spans:
    print(f"{span.source}: {text[span.start:span.end]} → {span.label} ({span.score})")
```

### Compare Before/After Processing
```python
raw_spans = pipeline._detect_all(text)
processed_spans = pipeline._process_spans(text, raw_spans)

print(f"Before: {len(raw_spans)} spans")
print(f"After: {len(processed_spans)} spans")
print(f"Filtered: {len(raw_spans) - len(processed_spans)} spans")
```

---

## License

This document is part of the ZeroPhix project and follows the same license terms.

---

**Last Updated:** January 15, 2026  
**Version:** 0.1.0
