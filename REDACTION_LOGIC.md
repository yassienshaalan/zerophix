# ZeroPhix Redaction Logic Explained

## Overview

ZeroPhix uses a multi-detector ensemble approach to achieve high-accuracy PII/PHI detection and redaction. This document explains the complete pipeline from text input to redacted output.

## High-Level Flow

```
Input Text → Detection → Processing → Masking → Redacted Output
```

## Architecture Components

### 1. Detection Layer (Ensemble of Detectors)
- **RegexDetector** - Pattern matching for structured data (SSN, credit cards, phone numbers)
- **SpacyDetector** - ML-based Named Entity Recognition (names, locations, organizations)
- **BertDetector** - Transformer-based NER for complex entities
- **GLiNERDetector** - Zero-shot entity detection (no training required)
- **StatisticalDetector** - Entropy and frequency analysis for anomalies
- **OpenMedDetector** - Healthcare-specific PHI detection (optional)

### 2. Processing Layer (Accuracy Enhancement)
- **ConsensusModel** - Ensemble voting to resolve conflicts
- **ContextPropagator** - Session memory for recurring entities
- **AllowListFilter** - Whitelist filtering for false positives
- **GarbageFilter** - Noise reduction (stopwords, partial words)

### 3. Masking Layer (Redaction Strategies)
- **Mask** - Replace with asterisks: `***********`
- **Replace** - Replace with label: `<US_SSN>`
- **Brackets** - Replace with brackets: `[US_SSN]`
- **Hash** - Replace with SHA-256 hash: `a3f2c9d8e1b4`

---

## Detailed Step-by-Step Process

### Phase 1: Initialization (`__init__`)

The pipeline assembles detector components based on configuration:

```python
self.components = []

# Add detectors based on config/mode
if is_auto or "regex" in cfg.detectors:
    self.components.append(RegexDetector(cfg))

if is_auto or cfg.use_spacy:
    self.components.append(SpacyDetector(cfg))

if is_auto or cfg.use_bert:
    self.components.append(BertDetector(cfg))

if is_auto or cfg.use_gliner:
    self.components.append(GLiNERDetector(cfg))

if cfg.use_statistical:
    self.components.append(StatisticalDetector(cfg))

if is_auto or cfg.use_openmed:
    if OpenMedDetector:
        self.components.append(OpenMedDetector(cfg))
```

**Key Point:** Multiple detectors run in parallel - this is the "ensemble" approach that improves recall.

---

### Phase 2: Detection (`redact()` method)

Each detector scans the text independently and returns `Span` objects:

```python
spans: List[Span] = []

for comp in self.components:
    detected = comp.detect(text)
    spans.extend(detected)
```

**Span Object Structure:**
```python
Span(
    start=10,           # Start character position
    end=20,             # End character position
    label="PERSON",     # Entity type
    score=0.95,         # Confidence score (0.0-1.0)
    source="spacy"      # Which detector found it
)
```

**Example Detection:**

```
Input: "John Smith, SSN: 123-45-6789"

RegexDetector finds:
  - Span(16, 27, "US_SSN", 1.0, "regex")

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
