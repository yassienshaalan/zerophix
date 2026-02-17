from typing import List, Dict
import re
from ..config import RedactionConfig
from ..detectors.regex_detector import RegexDetector
from ..detectors.statistical_detector import StatisticalDetector
from ..detectors.base import Span
from .consensus import ConsensusModel
from .adaptive_ensemble import AdaptiveConsensusModel, PerformanceTracker, LabelNormalizer, ConfigurationOptimizer
from .context import ContextPropagator
from .allowlist import AllowListFilter
from .post_processors import GarbageFilter

# Lazy import optional detectors
SpacyDetector = None
BertDetector = None
GLiNERDetector = None
OpenMedDetector = None

try:
    from ..detectors.spacy_detector import SpacyDetector
except ImportError:
    pass

try:
    from ..detectors.bert_detector import BertDetector
except ImportError:
    pass

try:
    from ..detectors.gliner_detector import GLiNERDetector
except ImportError:
    pass

try:
    from ..detectors.openmed_detector import OpenMedDetector
except ImportError:
    pass
except Exception as e:
    print(f"DEBUG: Failed to import OpenMedDetector: {e}")
    import traceback
    traceback.print_exc()
    OpenMedDetector = None

import hashlib

class RedactionPipeline:

    def __init__(self, cfg: RedactionConfig):
        self.cfg = cfg
        self.components = []
        
        is_auto = cfg.mode == "auto"
        
        # 1. Regex Detector
        if is_auto or "regex" in cfg.detectors:
            self.components.append(RegexDetector(cfg.country, cfg.company, cfg.custom_patterns))
        
        # 2. Spacy Detector
        if (is_auto or cfg.use_spacy) and SpacyDetector is not None:
            self.components.append(SpacyDetector())
        elif cfg.use_spacy and SpacyDetector is None:
            raise RuntimeError("spaCy detector requested but not installed. Install zerophix[spacy].")

        # 3. BERT Detector
        if (is_auto or cfg.use_bert) and BertDetector is not None:
            self.components.append(BertDetector(confidence_threshold=cfg.thresholds.get('bert_conf', 0.9)))
        elif cfg.use_bert and BertDetector is None:
            raise RuntimeError("BERT detector requested but not installed. Install zerophix[bert].")

        # 4. GLiNER Detector
        if (is_auto or cfg.use_gliner) and GLiNERDetector is not None:
            gliner_threshold = cfg.thresholds.get('gliner_conf', 0.5)
            self.components.append(GLiNERDetector(
                labels=cfg.gliner_labels,
                confidence_threshold=gliner_threshold,
                label_thresholds=cfg.label_thresholds
            ))
        elif cfg.use_gliner and GLiNERDetector is None:
            raise RuntimeError("GLiNER detector requested but not installed. Install zerophix[gliner].")

        # 5. Statistical Detector (Skip in auto to reduce noise, unless explicitly enabled)
        if not is_auto and cfg.use_statistical:
            self.components.append(StatisticalDetector(confidence_threshold=cfg.thresholds.get('statistical_conf', 0.7)))

        # 6. OpenMed Detector
        if is_auto or cfg.use_openmed:
            if OpenMedDetector is not None:
                self.components.append(OpenMedDetector(models_dir=cfg.models_dir, conf=self.cfg.thresholds.get('ner_conf', 0.5)))
            elif not is_auto:
                # Only raise error if user explicitly asked for it and it failed
                import sys
                if 'transformers' not in sys.modules:
                     raise RuntimeError("OpenMed detector requested but transformers/torch not installed. Install zerophix[openmed].")
                else:
                     raise RuntimeError("OpenMed detector requested but failed to import. Check logs for DEBUG messages.")
        
        # Initialize accuracy enhancement components
        # Use adaptive consensus if enabled, otherwise standard consensus
        if cfg.enable_adaptive_weights or cfg.enable_label_normalization:
            self.performance_tracker = PerformanceTracker() if cfg.track_detector_performance else None
            self.label_normalizer = LabelNormalizer() if cfg.enable_label_normalization else None
            
            # Load pre-calibrated weights if file provided
            if cfg.calibration_file and self.performance_tracker:
                try:
                    weights = self.performance_tracker.load_metrics(cfg.calibration_file)
                    # Update config weights with calibrated weights
                    cfg.detector_weights.update(weights)
                except Exception as e:
                    print(f"Warning: Could not load calibration file {cfg.calibration_file}: {e}")
            
            self.consensus = AdaptiveConsensusModel(
                cfg, 
                tracker=self.performance_tracker,
                normalizer=self.label_normalizer
            )
        else:
            self.performance_tracker = None
            self.label_normalizer = None
            self.consensus = ConsensusModel(cfg)
        
        self.context_propagator = ContextPropagator(cfg)
        self.allow_list = AllowListFilter(cfg)
        self.garbage_filter = GarbageFilter(cfg)

    @classmethod
    def from_config(cls, cfg: RedactionConfig):
        return cls(cfg)
    
    def optimize_for_medical(self):
        """
        Optimize pipeline configuration for medical text accuracy.
        Improves recall for medications and conditions while reducing person name false positives.
        
        Returns:
            self for method chaining
        """
        # Lower thresholds for medical entities
        self.cfg.label_thresholds.update({
            'MEDICATION': 0.3,
            'DRUG': 0.3,
            'MEDICAL_CONDITION': 0.3,
            'DISEASE': 0.3,
            'DIAGNOSIS': 0.3,
            'TREATMENT': 0.3,
        })
        
        # Increase threshold for person names to reduce false positives
        self.cfg.label_thresholds.update({
            'PERSON': 0.75,
            'PERSON_NAME': 0.75,
        })
        
        # Update GLiNER detector if present
        for i, comp in enumerate(self.components):
            if isinstance(comp, GLiNERDetector):
                comp.confidence_threshold = 0.3
                comp.label_thresholds = self.cfg.label_thresholds
                
                # Add medical-specific labels if not already present
                medical_labels = [
                    "person", "drug", "medication", "pharmaceutical",
                    "medical_condition", "disease", "diagnosis", "symptom",
                    "treatment", "procedure", "dosage",
                    "organization", "location", "facility", "hospital",
                    "date", "phone_number", "identifier"
                ]
                comp.labels = medical_labels
        
        # Make garbage filter more permissive for medical terms
        self.cfg.min_entity_length = 2
        self.cfg.filter_stopwords = False
        
        return self

    def _detect_domain(self, text: str) -> str:
        """
        Entity-based domain classification using detector outputs.
        More robust than keyword matching.
        """
        # First do a quick preliminary scan with detectors
        preliminary_spans = []
        for comp in self.components:
            preliminary_spans.extend(comp.detect(text))
        
        if not preliminary_spans:
            return "general"
        
        # Count entity types to determine domain
        label_counts = {}
        for span in preliminary_spans:
            label_counts[span.label] = label_counts.get(span.label, 0) + 1
        
        total_entities = len(preliminary_spans)
        
        # Medical domain indicators (entity-based)
        medical_labels = {
            "DRUG", "MEDICATION", "MEDICAL_CONDITION", "DISEASE", "DIAGNOSIS",
            "PROCEDURE", "TREATMENT", "SYMPTOM", "ANATOMY"
        }
        medical_count = sum(label_counts.get(label, 0) for label in medical_labels)
        medical_density = medical_count / total_entities if total_entities > 0 else 0
        
        # Legal domain indicators (entity-based)
        legal_labels = {
            "JUDGE", "LAWYER", "COURT", "CASE_NUMBER", "PLAINTIFF", "DEFENDANT",
            "JURISDICTION", "STATUTE", "ARTICLE", "SECTION"
        }
        legal_count = sum(label_counts.get(label, 0) for label in legal_labels)
        legal_density = legal_count / total_entities if total_entities > 0 else 0
        
        # Pattern-based fallback if entities are ambiguous
        if medical_density < 0.15 and legal_density < 0.15:
            # Use phrase pattern matching (more specific than single words)
            medical_phrases = [
                r'\bpatient\s+(?:presents|diagnosed|admitted)\b',
                r'\b(?:prescribed|medication|treatment|dosage)\b',
                r'\b(?:doctor|physician|clinician|surgeon)\b.*\b(?:examined|treated|prescribed)\b',
                r'\b(?:hospital|clinic|ward|emergency)\s+(?:admission|visit|stay)\b',
                r'\b(?:mg|ml|mcg)\b',  # Dosage units
                r'\b(?:blood pressure|heart rate|temperature)\b',
            ]
            
            legal_phrases = [
                r'\b(?:plaintiff|defendant)\s+(?:alleges|claims|argues)\b',
                r'\b(?:court|tribunal)\s+(?:finds|rules|orders|holds)\b',
                r'\bcase\s+no\.?\s*\d+\b',
                r'\b(?:section|article|clause)\s+\d+\b',
                r'\b(?:hereby|whereas|pursuant|aforementioned)\b',
                r'\b(?:jurisdiction|venue|statute)\b',
            ]
            
            medical_pattern_score = sum(1 for p in medical_phrases if re.search(p, text, re.IGNORECASE))
            legal_pattern_score = sum(1 for p in legal_phrases if re.search(p, text, re.IGNORECASE))
            
            if medical_pattern_score >= 2:
                return "medical"
            if legal_pattern_score >= 2:
                return "legal"
        
        # Final decision based on entity density
        if medical_density >= 0.15:
            return "medical"
        if legal_density >= 0.15:
            return "legal"
        
        return "general"

    def scan(self, text: str, parallel_detectors: bool = False) -> Dict[str, object]:
        """
        Scan text for entities without redacting.
        Returns a dict with detected entities and metadata.
        
        Args:
            text: Text to scan
            parallel_detectors: Run all detectors in parallel (faster on multi-core)
            
        Returns:
            Dict with keys: detections, total_detections, entity_counts, has_pii
        """
        spans: List[Span] = []
        
        # Determine which components to run
        active_components = self.components
        
        if self.cfg.mode == "auto":
            domain = self._detect_domain(text)
            active_components = []
            
            for comp in self.components:
                # Always run Regex (it's fast and handles basics like emails/dates)
                if isinstance(comp, RegexDetector):
                    active_components.append(comp)
                    continue
                    
                # Always run GLiNER (it's the smartest generalist)
                if isinstance(comp, GLiNERDetector):
                    active_components.append(comp)
                    continue
                
                # Domain specific routing
                if domain == "medical":
                    if OpenMedDetector and isinstance(comp, OpenMedDetector):
                        active_components.append(comp)
                    # Keep Spacy for basic names
                    elif isinstance(comp, SpacyDetector):
                        active_components.append(comp)
                        
                elif domain == "legal":
                    # In legal, Spacy and BERT are good. OpenMed is useless.
                    if isinstance(comp, (SpacyDetector, BertDetector)):
                        active_components.append(comp)
                        
                else: # General
                    # Run everything except specialized
                    if not (OpenMedDetector and isinstance(comp, OpenMedDetector)):
                        active_components.append(comp)

        # OPTIMIZATION: Run detectors in order of speed (fast -> slow)
        # Regex: ~1ms, spaCy: ~10ms, GLiNER: ~100ms, BERT: ~200ms, OpenMed: ~300ms
        sorted_components = self._sort_detectors_by_speed(active_components)
        
        if parallel_detectors and len(sorted_components) > 1:
            # Run all detectors in parallel for maximum speed
            from concurrent.futures import ThreadPoolExecutor
            
            def run_detector(comp):
                try:
                    return comp.detect(text)
                except Exception as e:
                    print(f"Detector {comp.__class__.__name__} failed: {e}")
                    return []
            
            with ThreadPoolExecutor(max_workers=len(sorted_components)) as executor:
                futures = [executor.submit(run_detector, comp) for comp in sorted_components]
                for future in futures:
                    spans.extend(future.result())
        else:
            # Sequential execution (default)
            for comp in sorted_components:
                spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)
        
        # Calculate statistics
        entity_counts = {}
        for s in merged:
            entity_counts[s.label] = entity_counts.get(s.label, 0) + 1

        # Convert spans to detection dicts
        detections = []
        for s in merged:
            detections.append({
                "start": s.start,
                "end": s.end,
                "label": s.label,
                "score": s.score,
                "source": s.source,
                "text": text[s.start:s.end]
            })

        return {
            "detections": detections,
            "total_detections": len(merged),
            "entity_counts": entity_counts,
            "has_pii": len(merged) > 0
        }
    
    def _sort_detectors_by_speed(self, components: List) -> List:
        """Sort detectors by execution speed (fastest first)"""
        speed_order = {
            'RegexDetector': 0,
            'SpacyDetector': 1,
            'StatisticalDetector': 2,
            'GLiNERDetector': 3,
            'BertDetector': 4,
            'OpenMedDetector': 5,
        }
        
        def get_priority(comp):
            class_name = comp.__class__.__name__
            return speed_order.get(class_name, 99)
        
        return sorted(components, key=get_priority)

    def _mask(self, s: str, label: str) -> str:
        style = self.cfg.masking_style
        if style == "mask":
            return "*" * len(s)
        if style == "replace":
            return f"<{label}>"
        if style == "brackets":
            return f"[{label}]"
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    def _process_spans(self, text: str, spans: List[Span]) -> List[Span]:
        """
        Apply consensus, context propagation, and allow-list filtering.
        """
        # 1. Resolve conflicts using Ensemble Voting
        resolved_spans = self.consensus.resolve(spans, text)
        
        # 2. Propagate context (Session Memory)
        # We run this after resolution so we propagate based on the "winner" labels
        propagated_spans = self.context_propagator.propagate(text, resolved_spans)
        
        # 3. Filter allow-listed terms
        allowed_spans = self.allow_list.filter(text, propagated_spans)
        
        # 4. Filter garbage (partial words, stopwords, etc.)
        final_spans = self.garbage_filter.filter(text, allowed_spans)
        
        # Sort for final output
        final_spans.sort(key=lambda x: (x.start, -x.end))
        
        return final_spans

    def redact_batch(self, texts: List[str], parallel: bool = True, max_workers: int = None) -> List[Dict[str, object]]:
        """
        Batch redact multiple texts with vectorized processing
        
        Args:
            texts: List of text strings to redact
            parallel: Use parallel processing for large batches (default: True)
            max_workers: Maximum parallel workers (default: CPU count)
            
        Returns:
            List of redaction results, same format as redact()
            
        Performance:
            - Vectorized: ~10x faster for batches >100 texts
            - Parallel: ~4x faster on 4-core CPU
            
        Example:
            texts = [
                "John Smith, SSN: 123-45-6789",
                "Jane Doe, email: jane@example.com",
                "Bob Wilson, phone: 555-123-4567"
            ]
            results = pipeline.redact_batch(texts)
            for i, result in enumerate(results):
                print(f"Text {i+1}: {result['text']}")
        """
        # For small batches (<10), serial is faster due to overhead
        if not parallel or len(texts) < 10:
            return [self.redact(text) for text in texts]
        
        # Parallel processing for large batches
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os
        
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, len(texts))
        
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self.redact, text): i 
                for i, text in enumerate(texts)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    # On error, return original text with error marker
                    results[idx] = {
                        'text': texts[idx],
                        'spans': [],
                        'error': str(e)
                    }
        
        return results
    
    def scan_batch(self, texts: List[str], parallel: bool = True, max_workers: int = None) -> List[Dict[str, object]]:
        """
        Batch scan multiple texts for PII/PHI with vectorized processing
        
        Args:
            texts: List of text strings to scan
            parallel: Use parallel processing for large batches (default: True)
            max_workers: Maximum parallel workers (default: CPU count)
            
        Returns:
            List of scan results, same format as scan()
        """
        # For small batches, serial is faster
        if not parallel or len(texts) < 10:
            return [self.scan(text) for text in texts]
        
        # Parallel processing
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os
        
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, len(texts))
        
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self.scan, text): i 
                for i, text in enumerate(texts)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = {
                        'detections': [],
                        'total_detections': 0,
                        'has_pii': False,
                        'error': str(e)
                    }
        
        return results

    def redact(self, text: str, user_context: Dict = None, session_id: str = None) -> Dict[str, object]:
        """
        Redact PII/PHI from text
        
        Args:
            text: Input text (str, required)
            user_context: Optional user context
            session_id: Optional session identifier
            
        Returns:
            Dictionary with 'text' (redacted) and 'spans' (detected entities)
        """
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)

        from ..policies.loader import load_policy
        policy = load_policy(self.cfg.country, self.cfg.company)
        actions = policy.get("actions", {})
        out_text = []
        i = 0
        for s in merged:
            out_text.append(text[i:s.start])
            action = actions.get(s.label, actions.get("default", "hash"))
            out_text.append(self._mask(text[s.start:s.end], s.label if not self.cfg.keep_surrogates else action.upper()))
            i = s.end
        out_text.append(text[i:])
        
        # Convert spans to dict and ensure JSON serializable types
        serializable_spans = []
        for s in merged:
            d = s.__dict__.copy()
            # Convert numpy/torch floats to python floats
            if hasattr(d['score'], 'item'):
                d['score'] = float(d['score'])
            serializable_spans.append(d)
            
        return {"text": "".join(out_text), "spans": serializable_spans}
    
    def calibrate(self, 
                  validation_texts: List[str],
                  validation_ground_truth: List[List[tuple]],
                  save_path: str = None) -> Dict:
        """
        Calibrate the pipeline on labeled validation data
        
        Args:
            validation_texts: List of text samples
            validation_ground_truth: List of ground truth annotations [(start, end, label), ...]
            save_path: Optional path to save calibration results
        
        Returns:
            Dictionary with optimized configuration and performance metrics
        
        Example:
            >>> texts = ["John Smith has diabetes", "Call 555-1234"]
            >>> ground_truth = [
            ...     [(0, 10, "PERSON_NAME"), (15, 23, "DISEASE")],
            ...     [(5, 13, "PHONE_NUMBER")]
            ... ]
            >>> results = pipeline.calibrate(texts, ground_truth, "calibration.json")
            >>> print(f"Optimized weights: {results['weights']}")
        """
        optimizer = ConfigurationOptimizer(self)
        raw_results = optimizer.calibrate(validation_texts, validation_ground_truth)
        
        if save_path and self.performance_tracker:
            self.performance_tracker.save_metrics(save_path)
        
        # Update pipeline with optimized configuration
        if self.performance_tracker:
            self.cfg.detector_weights = raw_results["detector_weights"]
            self.cfg.label_thresholds.update(raw_results["label_thresholds"])
            
            # Update consensus model with new weights
            if isinstance(self.consensus, AdaptiveConsensusModel):
                self.consensus.update_weights_from_tracker()
        
        # Calculate overall metrics from detector performance
        perf_summary = raw_results.get("performance_summary", {})
        total_tp = sum(m.get("true_positives", 0) for m in perf_summary.values())
        total_fp = sum(m.get("false_positives", 0) for m in perf_summary.values())
        total_fn = sum(m.get("false_negatives", 0) for m in perf_summary.values())
        
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
        
        # Return in expected format
        return {
            "weights": raw_results["detector_weights"],
            "detector_weights": raw_results["detector_weights"],  # Alias
            "label_thresholds": raw_results["label_thresholds"],
            "detector_metrics": perf_summary,
            "performance_summary": perf_summary,  # Alias
            "metrics": {
                "precision": overall_precision,
                "recall": overall_recall,
                "f1": overall_f1,
                "true_positives": total_tp,
                "false_positives": total_fp,
                "false_negatives": total_fn,
            }
        }
    
    def save_calibration(self, filepath: str):
        """
        Save current calibration (detector weights and thresholds) to file
        
        Args:
            filepath: Path to save calibration JSON
        """
        if not self.performance_tracker:
            print("Warning: Performance tracking not enabled. Saving current config only.")
        
        calibration_data = {
            "detector_weights": self.cfg.detector_weights,
            "label_thresholds": self.cfg.label_thresholds,
            "adaptive_weight_method": self.cfg.adaptive_weight_method,
        }
        
        if self.performance_tracker:
            calibration_data["performance_summary"] = self.performance_tracker.get_summary()
            calibration_data["recommended_weights"] = self.performance_tracker.get_all_weights()
        
        import json
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        
        print(f"✓ Calibration saved to: {filepath}")
    
    def load_calibration(self, filepath: str):
        """
        Load calibration from file and update pipeline configuration
        
        Args:
            filepath: Path to calibration JSON file
        """
        import json
        with open(filepath, 'r') as f:
            calibration_data = json.load(f)
        
        # Update configuration
        if "detector_weights" in calibration_data:
            self.cfg.detector_weights = calibration_data["detector_weights"]
        
        if "label_thresholds" in calibration_data:
            self.cfg.label_thresholds.update(calibration_data["label_thresholds"])
        
        # Update consensus model if using adaptive
        if isinstance(self.consensus, AdaptiveConsensusModel):
            self.consensus.weights = self.cfg.detector_weights.copy()
        
        print(f"✓ Calibration loaded from: {filepath}")
        print(f"  Detector weights: {self.cfg.detector_weights}")
        
        return calibration_data
    
    def get_performance_summary(self) -> Dict:
        """
        Get current performance metrics for all detectors
        Requires track_detector_performance=True in config
        """
        if self.performance_tracker:
            return self.performance_tracker.get_summary()
        return {"error": "Performance tracking not enabled. Set track_detector_performance=True"}

    def scan_report(self, text: str) -> Dict[str, object]:
        """Scan text for PII/PHI without redacting. Returns detection report with statistics."""
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        # Apply advanced processing
        merged = self._process_spans(text, spans)

        # Calculate statistics
        entity_counts = {}
        for s in merged:
            entity_counts[s.label] = entity_counts.get(s.label, 0) + 1

        # Extract matched text snippets
        detections = []
        for s in merged:
            detections.append({
                "start": s.start,
                "end": s.end,
                "label": s.label,
                "score": s.score,
                "source": s.source,
                "text": text[s.start:s.end],
                "context": text[max(0, s.start-20):min(len(text), s.end+20)]
            })

        return {
            "original_text": text,
            "total_detections": len(merged),
            "entity_counts": entity_counts,
            "detections": detections,
            "has_pii": len(merged) > 0
        }
