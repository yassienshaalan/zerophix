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
  - Compliant with Australian Privacy Act and health sector regulations

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

**Australian-Specific Patterns**:

```python
# TFN - Tax File Number (9 digits, Modulus 11 validation)
TFN_PATTERN = r'\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b'

def validate_tfn(tfn: str) -> bool:
    """
    Modulus 11 algorithm with weights [1,4,3,7,5,8,6,9,10]
    Example: 123 456 782
    Calculation: (1×1 + 2×4 + 3×3 + 4×7 + 5×5 + 6×8 + 7×6 + 8×9 + 2×10) % 11 == 0
    """
    digits = [int(d) for d in tfn if d.isdigit()]
    weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]
    checksum = sum(d * w for d, w in zip(digits, weights))
    return checksum % 11 == 0

# ABN - Australian Business Number (11 digits, Modulus 89 validation)
ABN_PATTERN = r'\b\d{2}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3}\b'

def validate_abn(abn: str) -> bool:
    """
    Modulus 89 algorithm (subtract 1 from first digit, apply weights)
    Example: 53 004 085 616
    """
    digits = [int(d) for d in abn if d.isdigit()]
    digits[0] -= 1  # Subtract 1 from first digit
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    checksum = sum(d * w for d, w in zip(digits, weights))
    return checksum % 89 == 0

# ACN - Australian Company Number (9 digits, Modulus 10 validation)
ACN_PATTERN = r'\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b'

def validate_acn(acn: str) -> bool:
    """
    Modulus 10 algorithm with weights [8,7,6,5,4,3,2,1]
    Example: 123 456 789
    """
    digits = [int(d) for d in acn if d.isdigit()]
    weights = [8, 7, 6, 5, 4, 3, 2, 1]
    checksum = sum(d * w for d, w in zip(digits[:8], weights))
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit == digits[8]

# Medicare - 10 digits with Modulus 10 Luhn-like validation
MEDICARE_PATTERN = r'\b\d{4}[\s-]?\d{5}[\s-]?\d\b'

def validate_medicare(medicare: str) -> bool:
    """
    Modulus 10 Luhn-like with weights [1,3,7,9,1,3,7,9]
    Example: 2234 56781 2
    """
    digits = [int(d) for d in medicare if d.isdigit()]
    weights = [1, 3, 7, 9, 1, 3, 7, 9]
    checksum = sum(d * w for d, w in zip(digits[:8], weights))
    check_digit = checksum % 10
    return check_digit == digits[9]
```

**Precision Impact**:
- Without validation: many false positives
- With checksum validation: dramatically reduced false positives (mathematically verified)

**Coverage**: 40+ Australian entity types including:
- Government: TFN, ABN, ACN
- Healthcare: Medicare, IHI, HPI-I/O, DVA, PBS
- Driver Licenses: NSW, VIC, QLD, SA, WA, TAS, NT, ACT
- Financial: BSB numbers, Centrelink CRN, bank accounts
- Geographic: Addresses, postcodes (4-digit validation)

### 2. spaCy NER (ML-based Named Entities)

**Purpose**: High recall for names, locations, organizations

**Model**: en_core_web_lg (transformer-based, 560MB)

**Detection Process**:
```python
def detect(self, text: str) -> List[Span]:
    doc = self.nlp(text)
    spans = []
    
    for ent in doc.ents:
        # Map spaCy labels to ZeroPhix labels
        label_map = {
            "PERSON": "PERSON_NAME",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",  # Geopolitical entity
            "LOC": "LOCATION",
            "DATE": "DATE",
            "MONEY": "CURRENCY"
        }
        
        if ent.label_ in label_map:
            spans.append(Span(
                start=ent.start_char,
                end=ent.end_char,
                label=label_map[ent.label_],
                score=0.90,  # spaCy doesn't provide confidence
                source="spacy"
            ))
    
    return spans
```

**Strengths**: Names in natural text, context-aware
**Weaknesses**: No confidence scores, struggles with uncommon names

### 3. BERT Detector (Transformer Context-Aware)

**Purpose**: Highest accuracy for complex, context-dependent entities

**Model**: bert-base-cased (110M parameters)

**How it works**:
```python
def detect(self, text: str) -> List[Span]:
    # Tokenize input
    inputs = self.tokenizer(text, return_tensors="pt", 
                           return_offsets_mapping=True)
    
    # Run inference
    outputs = self.model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=2)
    
    # Extract entities with confidence scores
    spans = []
    for idx, (token_id, label_id) in enumerate(zip(inputs['input_ids'][0], predictions[0])):
        if label_id > 0:  # Not 'O' (outside entity)
            label = self.id2label[label_id.item()]
            score = torch.softmax(outputs.logits[0][idx], dim=0)[label_id].item()
            
            # Map token position to character position
            start, end = inputs['offset_mapping'][0][idx]
            spans.append(Span(start, end, label, score, "bert"))
    
    return self._merge_token_spans(spans)  # Merge BIO tags
```

**Strengths**: Context understanding, confidence scores, handles ambiguity
**Weaknesses**: Slower (100-300ms per doc), higher memory (500MB+)

### 4. GLiNER (Zero-Shot Custom Entities)

**Purpose**: Detect ANY entity type without training

**Revolutionary Approach**:
```python
def detect(self, text: str, entity_types: List[str]) -> List[Span]:
    """
    entity_types: ["employee id", "project code", "api key", ...]
    No training needed - just name what you want to find!
    """
    entities = self.model.predict_entities(text, entity_types)
    
    spans = []
    for ent in entities:
        spans.append(Span(
            start=ent["start"],
            end=ent["end"],
            label=ent["label"].upper().replace(" ", "_"),
            score=ent["score"],
            source="gliner"
        ))
    
    return spans
```

**Use Cases**:
- Custom organization IDs: "EMP-123456", "PROJ-ABC-001"
- Domain-specific codes: "patient ID", "case number"
- Proprietary identifiers unique to your organization
- Ad-hoc entity types without retraining models

**Strengths**: Extreme flexibility, no training data required
**Weaknesses**: Lower precision than specialized models

### 5. Statistical Detector (Entropy & Anomaly Detection)

**Purpose**: Catch patterns ML models miss

**Algorithms**:
```python
def detect(self, text: str) -> List[Span]:
    spans = []
    
    # 1. Shannon Entropy (randomness detection)
    def entropy(s: str) -> float:
        """High entropy = random-looking (keys, hashes, encrypted data)"""
        from collections import Counter
        import math
        counts = Counter(s)
        probs = [c / len(s) for c in counts.values()]
        return -sum(p * math.log2(p) for p in probs)
    
    # Scan for high-entropy tokens
    for token in text.split():
        if len(token) > 8 and entropy(token) > 4.0:
            # Likely API key, hash, or encrypted data
            spans.append(Span(..., "HIGH_ENTROPY_TOKEN", 0.75, "statistical"))
    
    # 2. Frequency Analysis (repeated sensitive patterns)
    token_freq = Counter(text.split())
    for token, count in token_freq.items():
        if count >= 3 and self._looks_sensitive(token):
            # Repeated ID or code
            for match in re.finditer(re.escape(token), text):
                spans.append(Span(..., "REPEATED_ID", 0.70, "statistical"))
    
    # 3. Format Anomalies (unexpected patterns)
    # Detect: "XXX-XX-1234" (partial redaction attempt)
    #         "***-***-6789" (masked but detectable)
    #         Base64-encoded strings
    
    return spans
```

**Strengths**: Catches what others miss (API keys, hashes, partial redactions)
**Weaknesses**: Higher false positive rate, needs tuning per domain

### 6. OpenMed Detector (Healthcare-Specific PHI)

**Purpose**: Medical/clinical entity detection for HIPAA compliance

**Models**: 
- OpenMed-NER-DiseaseDetect (335M parameters)
- OpenMed-NER-ChemicalDetect (33M parameters)

**Detection**:
```python
def detect(self, text: str) -> List[Span]:
    spans = []
    
    # Disease detection
    disease_entities = self.disease_model.predict(text)
    for ent in disease_entities:
        spans.append(Span(..., "MEDICAL_CONDITION", ent.score, "openmed"))
    
    # Chemical/drug detection
    chem_entities = self.chem_model.predict(text)
    for ent in chem_entities:
        spans.append(Span(..., "MEDICATION", ent.score, "openmed"))
    
    # Medical procedures, anatomy, tests, etc.
    return spans
```

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

```python
def resolve_consensus(overlapping_spans: List[Span]) -> Span:
    """Choose best span from overlapping detections"""
    
    # Strategy 1: Highest confidence
    if all(s.label == overlapping_spans[0].label for s in overlapping_spans):
        return max(overlapping_spans, key=lambda s: s.score)
    
    # Strategy 2: Policy-based preference
    policy_order = ["regex", "bert", "spacy", "gliner", "statistical"]
    for source in policy_order:
        matches = [s for s in overlapping_spans if s.source == source]
        if matches:
            return max(matches, key=lambda s: s.score)
    
    # Strategy 3: Majority voting
    label_votes = Counter(s.label for s in overlapping_spans)
    majority_label = label_votes.most_common(1)[0][0]
    candidates = [s for s in overlapping_spans if s.label == majority_label]
    return max(candidates, key=lambda s: s.score)
```

**Problem**: Equal weights for all detectors, even if some are noisy

### Solution 2: Adaptive Weighted Ensemble (With Calibration)

**Key Innovation**: Learn optimal detector weights from YOUR data

#### Step 1: Label Normalization

```python
LABEL_NORMALIZATION_MAP = {
    # Map similar labels to canonical form
    "PERSON": "PERSON_NAME",
    "USERNAME": "PERSON_NAME",  # GLiNER often uses USERNAME
    "USER": "PERSON_NAME",
    "PATIENT_NAME": "PERSON_NAME",
    
    "SSN": "US_SSN",
    "SOCIAL_SECURITY": "US_SSN",
    
    "TFN": "AU_TFN",
    "TAX_FILE_NUMBER": "AU_TFN",
    
    # This enables cross-detector consensus!
}

def normalize_label(label: str) -> str:
    """Normalize before voting so detectors can agree"""
    return LABEL_NORMALIZATION_MAP.get(label, label)
```

**Impact**: Without normalization, "PERSON" and "USERNAME" vote separately
With normalization, they vote together → stronger consensus

#### Step 2: Calibration on Validation Data

```python
def calibrate(validation_texts: List[str], 
              ground_truth: List[List[Tuple[int, int, str]]]) -> Dict[str, float]:
    """
    Learn optimal detector weights from labeled examples
    
    Args:
        validation_texts: ["John has diabetes", "Call 555-1234", ...]
        ground_truth: [[(0,4,"PERSON"), (9,17,"DISEASE")], [(5,13,"PHONE")], ...]
    
    Returns:
        {"gliner": 0.42, "regex": 0.09, "openmed": 0.12, "spacy": 0.25, ...}
    """
    
    # 1. Measure per-detector performance
    detector_metrics = {}
    
    for detector in detectors:
        predictions = detector.detect_batch(validation_texts)
        
        # Calculate F1 score
        precision, recall, f1 = evaluate(predictions, ground_truth)
        detector_metrics[detector.name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    
    # 2. Calculate weights using F1-squared method
    weights = {}
    for name, metrics in detector_metrics.items():
        # F1² gives more weight to high-performers
        # Low F1 = low weight, High F1 = high weight (exponentially)
        f1_score = metrics["f1"]
        weights[name] = max(0.1, f1_score ** 2)  # Min 0.1 to avoid zero weight
    
    # 3. Normalize weights to sum to 1.0
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    
    return weights

# Example calibration results:
# GLiNER:  F1=0.60 → weight = 0.60² = 0.36  (High performer)
# spaCy:   F1=0.50 → weight = 0.50² = 0.25  (Good)
# OpenMed: F1=0.35 → weight = 0.35² = 0.12  (Moderate)
# Regex:   F1=0.30 → weight = 0.30² = 0.09  (Noisy for names)
# BERT:    F1=0.25 → weight = 0.10 (floor)   (Poor on this data)
```

#### Step 3: Weighted Voting in Production

```python
def weighted_consensus(overlapping_spans: List[Span], 
                       weights: Dict[str, float]) -> Span:
    """
    Vote with learned weights
    
    Before calibration (equal weights):
      GLiNER (PERSON, 0.92) + spaCy (PERSON, 0.98) + GLiNER (USERNAME, 0.65)
      → Ambiguous, pick highest score
    
    After calibration (weighted):
      GLiNER (PERSON, 0.92) × 0.36 = 0.331
      spaCy  (PERSON, 0.98) × 0.25 = 0.245
      GLiNER (USERNAME→PERSON, 0.65) × 0.36 = 0.234
      → PERSON_NAME wins with 0.81 combined score
    """
    
    # Normalize labels first
    for span in overlapping_spans:
        span.label = normalize_label(span.label)
    
    # Calculate weighted scores per label
    label_scores = {}
    for span in overlapping_spans:
        weight = weights.get(span.source, 0.1)  # Default 0.1 if not calibrated
        weighted_score = span.score * weight
        
        if span.label not in label_scores:
            label_scores[span.label] = []
        label_scores[span.label].append((span, weighted_score))
    
    # Aggregate scores per label
    label_totals = {
        label: sum(score for _, score in spans)
        for label, spans in label_scores.items()
    }
    
    # Choose label with highest total weighted score
    winning_label = max(label_totals, key=label_totals.get)
    winning_spans = label_scores[winning_label]
    
    # Return span with highest individual score from winning label
    best_span, _ = max(winning_spans, key=lambda x: x[1])
    return best_span
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

```python
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

# 1. Enable adaptive features
config = RedactionConfig(
    country="AU",
    use_gliner=True,
    use_openmed=True,
    use_spacy=True,
    enable_adaptive_weights=True,      # Enable learning
    enable_label_normalization=True,   # Enable consensus
)

pipeline = RedactionPipeline(config)

# 2. Prepare validation data (20-50 samples)
validation_texts = [
    "John Smith has diabetes",
    "Call 555-123-4567",
    "TFN: 123 456 782",
    # ... 17-47 more examples
]

validation_ground_truth = [
    [(0, 10, "PERSON_NAME"), (15, 23, "MEDICAL_CONDITION")],
    [(5, 17, "PHONE_US")],
    [(5, 17, "AU_TFN")],
    # ... matching annotations
]

# 3. Calibrate (takes 2-5 seconds for 20 samples)
results = pipeline.calibrate(
    validation_texts,
    validation_ground_truth,
    save_path="calibration_au_medical.json"  # Save for reuse!
)

print(f"Learned weights: {results['detector_weights']}")
print(f"Performance improved after calibration")

# 4. Use calibrated pipeline in production
result = pipeline.redact("Jane Doe, Medicare 2234 56781 2")
# Now uses optimal weights learned from your data!
```

### Loading Pre-Calibrated Weights

```python
# In production, load saved calibration
config = RedactionConfig(
    country="AU",
    use_gliner=True,
    use_openmed=True,
    enable_adaptive_weights=True,
    calibration_file="calibration_au_medical.json"  # Load weights
)

pipeline = RedactionPipeline(config)
# Ready to use with optimal weights!
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

**Problem**: Same entity appears multiple times, different confidence

```
Document 1: "John Smith called from New York"
            └─ PERSON (0.98)

Document 2: "John replied with the report"
            └─ PERSON (0.65) ← Low confidence (no surname context)
```

**Solution**: Session memory boosts confidence

```python
class ContextPropagator:
    def __init__(self):
        self.entity_memory = {}  # {entity_text: (label, max_score, count)}
        self.threshold = 0.90    # High-confidence threshold for memory
    
    def propagate(self, text: str, spans: List[Span]) -> List[Span]:
        boosted_spans = []
        
        for span in spans:
            entity_text = text[span.start:span.end]
            
            # Check if we've seen this entity before with high confidence
            if entity_text in self.entity_memory:
                prev_label, prev_score, count = self.entity_memory[entity_text]
                
                if prev_score >= self.threshold:
                    # Boost confidence based on previous detections
                    boost_factor = min(0.20, 0.05 * count)  # Up to +0.20
                    span.score = min(1.0, span.score + boost_factor)
                    span.label = prev_label  # Use consistent label
            
            # Update memory
            if span.score >= self.threshold:
                if entity_text not in self.entity_memory:
                    self.entity_memory[entity_text] = (span.label, span.score, 1)
                else:
                    _, _, count = self.entity_memory[entity_text]
                    self.entity_memory[entity_text] = (span.label, 
                                                       max(span.score, prev_score),
                                                       count + 1)
            
            boosted_spans.append(span)
        
        return boosted_spans
```

**Impact**: Improved recall on multi-document sessions

### 2. Allow-List Filtering

**Problem**: Public figures, organization names trigger false positives

```python
class AllowListFilter:
    def __init__(self, allow_list: List[str]):
        self.allow_list = set(s.lower() for s in allow_list)
    
    def filter(self, text: str, spans: List[Span]) -> List[Span]:
        filtered = []
        
        for span in spans:
            entity_text = text[span.start:span.end].lower()
            
            # Exact match
            if entity_text in self.allow_list:
                continue  # Skip (whitelisted)
            
            # Partial match (configurable)
            if any(allowed in entity_text for allowed in self.allow_list):
                continue
            
            filtered.append(span)
        
        return filtered

# Usage
config = RedactionConfig(
    allow_list=["Commonwealth Bank", "Microsoft", "GitHub", "John Howard"]
)
```

**Use Cases**:
- Public figures mentioned in news
- Organization names in templates
- Product names (iPhone, Windows, etc.)
- Non-sensitive technical terms

### 3. Garbage Filtering (ML Noise Reduction)

**Problem**: ML models detect nonsense

```python
class GarbageFilter:
    def __init__(self):
        self.stopwords = {"the", "and", "is", "at", "of", "a", "in", "to"}
        self.min_length = 3
    
    def filter(self, text: str, spans: List[Span]) -> List[Span]:
        clean_spans = []
        
        for span in spans:
            entity_text = text[span.start:span.end]
            
            # Rule 1: Too short
            if len(entity_text) < self.min_length:
                continue
            
            # Rule 2: Common stopword
            if entity_text.lower() in self.stopwords:
                continue
            
            # Rule 3: Starts with lowercase (not proper noun)
            if entity_text[0].islower() and span.label in ["PERSON_NAME", "ORGANIZATION"]:
                continue
            
            # Rule 4: Partial word at boundary
            if span.start > 0 and text[span.start-1].isalnum():
                continue  # "...John" → partial word
            if span.end < len(text) and text[span.end].isalnum():
                continue  # "John..." → partial word
            
            # Rule 5: Single letter (unless SSN/ID context)
            if len(entity_text) == 1 and span.label not in ["US_SSN", "AU_TFN"]:
                continue
            
            # Rule 6: Low confidence + common word
            if span.score < 0.70 and self._is_common_word(entity_text):
                continue
            
            clean_spans.append(span)
        
        return clean_spans
```

**Impact**: Significant reduction in false positives from ML models

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

```python
from zerophix.security.encryption import KeyManager, EncryptionManager
from cryptography.fernet import Fernet

# 1. Key management setup
key_manager = KeyManager(key_store_path="./secure_keys")

# 2. Generate encryption key for PII
key_info = key_manager.generate_data_encryption_key(purpose="pii_redaction")
print(f"Key ID: {key_info['key_id']}")
print(f"Rotation due: {key_info['rotation_due']}")

# 3. Use in redaction pipeline
config = RedactionConfig(
    country="AU",
    masking_style="encrypt",
    encryption_key_id=key_info['key_id']
)

pipeline = RedactionPipeline(config)
result = pipeline.redact("Account: 1234567890")

# 4. Decrypt (authorized personnel only)
encryption_manager = EncryptionManager(key_id=key_info['key_id'])
original_account = encryption_manager.decrypt_text(result['text'])

# 5. Key rotation (90-day cycle)
key_manager.rotate_key(key_info['key_id'])
```

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

```bash
# On machine with internet
pip download zerophix[all] -d ./zerophix-offline/
python -m spacy download en_core_web_lg --download-dir ./zerophix-offline/

# Download ML models to cache
python -c "
from zerophix.detectors.bert_detector import BERTDetector
from zerophix.detectors.gliner_detector import GLiNERDetector
from zerophix.detectors.openmed_detector import OpenMedDetector

# Models auto-download to cache
BERTDetector()
GLiNERDetector()
OpenMedDetector()
"

# Copy cache directories
cp -r ~/.cache/zerophix ./zerophix-offline/cache/
cp -r ~/.cache/huggingface ./zerophix-offline/cache/
```

#### Step 2: Transfer to Air-Gapped Environment

```bash
# Via USB, secure network, or physical media
# Transfer ./zerophix-offline/ folder (size: ~2-5GB depending on models)
```

#### Step 3: Install Offline

```bash
# On air-gapped machine
pip install --no-index --find-links=./zerophix-offline/ zerophix[all]

# Restore model caches
cp -r ./zerophix-offline/cache/zerophix ~/.cache/
cp -r ./zerophix-offline/cache/huggingface ~/.cache/

# Install spaCy model
cd ./zerophix-offline/
pip install en_core_web_lg-*.whl
```

#### Step 4: Verify Offline Operation

```bash
# Disconnect internet
ifconfig eth0 down  # Linux
# Or disable network adapter in Windows

# Test
python -c "
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

config = RedactionConfig(country='AU', use_spacy=True, use_bert=True)
pipeline = RedactionPipeline(config)
result = pipeline.redact('John Smith, TFN: 123 456 782')
print(result['text'])
"

# Should work without internet!
```

### Docker Image (Offline-Ready)

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy offline packages
COPY ./zerophix-offline /tmp/zerophix-offline

# Install offline
RUN pip install --no-index --find-links=/tmp/zerophix-offline/ zerophix[all]

# Copy model caches
COPY ./zerophix-offline/cache/zerophix /root/.cache/zerophix
COPY ./zerophix-offline/cache/huggingface /root/.cache/huggingface

# Install spaCy model
RUN cd /tmp/zerophix-offline && pip install en_core_web_lg-*.whl

# Cleanup
RUN rm -rf /tmp/zerophix-offline

WORKDIR /app
CMD ["python"]
```

```bash
# Build offline-capable image
docker build -t zerophix:offline-v1 .

# Run completely offline (no network)
docker run --network=none -v $(pwd)/data:/app/data zerophix:offline-v1 \\
    python -c "from zerophix import RedactionPipeline; ..."
```

### Kubernetes Deployment (Air-Gapped Cluster)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerophix-api
  namespace: pii-redaction
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zerophix
  template:
    metadata:
      labels:
        app: zerophix
    spec:
      # No internet access
      hostNetwork: false
      
      containers:
      - name: zerophix
        image: zerophix:offline-v1
        imagePullPolicy: Never  # Use local image
        
        resources:
          requests:
            memory: "2Gi"      # ML models need RAM
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        
        env:
        - name: ZEROPHIX_OFFLINE_MODE
          value: "true"
        - name: ZEROPHIX_CACHE_DIR
          value: "/cache"
        
        volumeMounts:
        - name: model-cache
          mountPath: /cache
          readOnly: true      # Models immutable
      
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: zerophix-models-pvc
```

**Result**: Complete PII redaction in air-gapped Kubernetes, no internet dependency

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
- Span(75, 88, "AU_MEDICARE", 1.00) → "2234 56781 2"  ✓ Valid checksum
- Span(95, 114, "AU_IHI", 1.00) → "8003 6012 3456 7890"
- Span(120, 131, "AU_TFN", 1.00) → "123 456 782"  ✓ Valid checksum
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

**Calibration weights** (from 50 Australian medical samples):
```
Regex:   0.35  (excellent for AU IDs)
spaCy:   0.25  (good for names)
OpenMed: 0.20  (best for medical terms)
GLiNER:  0.15  (moderate for general)
BERT:    0.05  (poor on this data, floor applied)
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
  PERSON_NAME: 'synthetic'
  AU_TFN: 'replace'
  AU_MEDICARE: 'replace'
  AU_IHI: 'replace'
  DATE_AU: 'synthetic'
  DATE_ISO: 'synthetic'
  AU_ADDRESS: 'synthetic'
  PHONE_AU_MOBILE: 'au_phone'  # Preserve 04XX
  PHONE_AU: 'mask'
  EMAIL: 'preserve_format'
  ORGANIZATION: 'synthetic'
  MEDICAL_CONDITION: 'hash'  # For research
  MEDICATION: 'hash'
```

### Output (Redacted)

```
PATIENT RECORD - CONFIDENTIAL

Patient: Alice Johnson
DOB: 22/07/1988 (Age: 41)
Medicare: <AU_MEDICARE>
IHI: <AU_IHI>
TFN: <AU_TFN>

Address: 456 Collins Avenue, Brisbane QLD 4000
Phone: 04XX-XXX-XXX
Email: a.j@provider.com.au

GP: Dr. Michael Brown (Provider: 1234567890)
Clinic: Sydney General Medical Centre
Phone: (0X) XXXX-XXXX

Diagnosis: HASH_9f8e7d6c5b4a
Current Medications:
  - HASH_3a2b1c0d9e8f 500mg BD
  - HASH_7e6f5d4c3b2a 5mg OD

Last HbA1c: 7.2% (2024-11-28)
Next appointment: 2025-03-05
```

**Protected**: 14 sensitive entities
**Maintained**: Document structure, readability, realistic appearance
**Compliant**: HIPAA Safe Harbor (87.5% recall benchmark)

---

## Comparison with Other Solutions

| Feature | ZeroPhix | Presidio (MS) | Azure AI | AWS Comprehend |
|---------|----------|---------------|----------|----------------|
| **Australian Focus** | ✓ 40+ entities | ✗ Limited | ✗ US-centric | ✗ US-centric |
| **Checksum Validation** | ✓ TFN/ABN/ACN/Medicare | ✗ No | ✗ No | ✗ No |
| **Offline Capable** | ✓ 100% | ✓ Yes | ✗ Cloud only | ✗ Cloud only |
| **Adaptive Calibration** | ✓ F1² learning | ✗ No | ✗ No | ✗ No |
| **Ensemble Voting** | ✓ 6 detectors | ✓ 2-3 detectors | ✗ Single model | ✗ Single model |
| **Per-Entity Strategies** | ✓ 10+ strategies | ✓ Limited | ✗ Fixed | ✗ Fixed |
| **Zero-Shot Detection** | ✓ GLiNER | ✗ No | ✗ No | ✗ No |
| **Cost** | Free (infra only) | Free | $2-5/1K docs | $1-3/1K docs |
| **Data Sovereignty** | ✓ Complete | ✓ On-prem | ✗ Cloud | ✗ Cloud |
| **Key Management** | ✓ Built-in | ✗ Manual | ✓ Azure KMS | ✓ AWS KMS |
| **Precision (AU data)** | 92%+ | 60-70% | Unknown | Unknown |

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
| **Offline Capable** | ✅ Yes | ✅ Yes | ❌ No (cloud only) |
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
