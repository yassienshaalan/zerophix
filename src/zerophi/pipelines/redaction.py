from typing import List, Dict, Optional
from ..config import RedactionConfig
from ..detectors.regex_detector import RegexDetector
from ..detectors.base import Span
from ..detectors.custom_detector import CustomEntityDetector
from ..detectors.statistical_detector import StatisticalDetector, FrequencyDetector
from ..performance.optimization import PerformanceCache, PerformanceMonitor, ProcessingMetrics
from ..redaction.strategies import RedactionStrategyManager
from ..security import SecureAuditLogger, ComplianceValidator, ZeroTrustValidator, ComplianceStandard

try:
    from ..detectors.openmed_detector import OpenMedDetector
except Exception:
    OpenMedDetector = None

try:
    from ..detectors.spacy_detector import SpacyDetector
except Exception:
    SpacyDetector = None

try:
    from ..detectors.bert_detector import BertDetector, ContextualDetector
except Exception:
    BertDetector = None
    ContextualDetector = None

import hashlib
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class RedactionPipeline:

    def __init__(self, cfg: RedactionConfig):
        self.cfg = cfg
        self.components = []
        self.async_components = []
        
        # Security and compliance
        self.audit_logger = SecureAuditLogger(
            log_directory=getattr(cfg, 'audit_log_dir', './audit_logs'),
            compliance_standards=[
                ComplianceStandard.GDPR,
                ComplianceStandard.HIPAA,
                ComplianceStandard.CCPA
            ]
        )
        
        self.compliance_validator = ComplianceValidator([
            ComplianceStandard.GDPR,
            ComplianceStandard.HIPAA,
            ComplianceStandard.PCI_DSS
        ])
        
        self.zero_trust_validator = ZeroTrustValidator()
        
        # Performance optimization
        self.cache = PerformanceCache(
            cache_type=getattr(cfg, 'cache_type', 'memory'),
            redis_url=getattr(cfg, 'redis_url', None),
            max_memory_items=getattr(cfg, 'cache_max_items', 10000),
            ttl_seconds=getattr(cfg, 'cache_ttl', 3600)
        ) if cfg.cache_detections else None
        
        self.performance_monitor = PerformanceMonitor()
        self.strategy_manager = RedactionStrategyManager()
        
        # Generate configuration hash for caching
        self.config_hash = self._generate_config_hash()
        
        # Always include regex detector (fastest, baseline)
        self.components.append(RegexDetector(cfg.country, cfg.company))
        
        # Add custom entity detector
        custom_detector = CustomEntityDetector()
        if cfg.custom_patterns:
            for entity_type, patterns in cfg.custom_patterns.items():
                for pattern in patterns:
                    custom_detector.add_pattern(entity_type, pattern)
        self.components.append(custom_detector)
        
        # Add statistical detector for pattern analysis
        if cfg.use_statistical:
            self.components.append(StatisticalDetector())
        
        # Add ML-based detectors based on configuration
        if cfg.use_spacy and SpacyDetector is not None:
            spacy_detector = SpacyDetector(model_name=cfg.spacy_model)
            if cfg.use_contextual:
                # Wrap with contextual enhancement
                self.components.append(ContextualDetector(spacy_detector))
            else:
                self.components.append(spacy_detector)
        
        if cfg.use_bert and BertDetector is not None:
            bert_detector = BertDetector(
                model_name=cfg.bert_model,
                confidence_threshold=cfg.thresholds.get('bert_conf', 0.9)
            )
            if cfg.use_contextual:
                self.components.append(ContextualDetector(bert_detector))
            else:
                self.components.append(bert_detector)
        
        if cfg.use_openmed and OpenMedDetector is not None:
            self.components.append(OpenMedDetector(
                models_dir=cfg.models_dir, 
                conf=cfg.thresholds.get('ner_conf', 0.5)
            ))
        
        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=cfg.max_workers)
    
    def _generate_config_hash(self) -> str:
        """Generate hash of configuration for caching"""
        config_str = f"{self.cfg.country}_{self.cfg.company}_{self.cfg.detectors}_{self.cfg.thresholds}"
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()[:16]

    @classmethod
    def from_config(cls, cfg: RedactionConfig):
        return cls(cfg)

    def _apply_redaction(self, text: str, label: str, action: str) -> str:
        """Apply specific redaction action using strategy manager"""
        redaction_result = self.strategy_manager.apply_redaction(
            text=text,
            entity_type=label,
            strategy_name=action,
            metadata={"pipeline": "zerophi"}
        )
        return redaction_result.redacted_text
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get performance summary and optimization recommendations"""
        summary = self.performance_monitor.get_performance_summary()
        
        if self.cache:
            cache_stats = self.cache.get_stats()
            summary.update(cache_stats)
        
        # Add recommendations
        summary['recommendations'] = self.performance_monitor.get_recommendations()
        
        return summary
    
    def clear_cache(self):
        """Clear performance cache"""
        if self.cache:
            self.cache.clear()
    
    def batch_redact(self, texts: List[str], progress_callback=None) -> List[Dict[str, any]]:
        """Batch redaction for multiple texts"""
        from ..performance.optimization import BatchProcessor
        
        with BatchProcessor(
            batch_size=self.cfg.batch_size,
            max_workers=self.cfg.max_workers
        ) as processor:
            return processor.process_batch(texts, self.redact, progress_callback)
    
    async def batch_redact_async(self, texts: List[str], progress_callback=None) -> List[Dict[str, any]]:
        """Async batch redaction for multiple texts"""
        from ..performance.optimization import BatchProcessor
        
        with BatchProcessor(
            batch_size=self.cfg.batch_size,
            max_workers=self.cfg.max_workers
        ) as processor:
            return await processor.process_batch_async(texts, self.redact, progress_callback)

    def redact(self, text: str, user_context: Optional[Dict] = None, 
               session_id: Optional[str] = None) -> Dict[str, object]:
        """Redact text using all configured detectors with security and compliance checks"""
        start_time = self.performance_monitor.start_timing()
        
        # Security and compliance validation
        if user_context:
            # Zero Trust validation
            trust_result = self.zero_trust_validator.validate_request(user_context)
            if not trust_result["trusted"]:
                self.audit_logger.log_security_event(
                    event_type="UNTRUSTED_ACCESS_ATTEMPT",
                    description=f"Zero Trust validation failed: {trust_result['recommendations']}",
                    severity="HIGH",
                    user_id=user_context.get("user_id"),
                    additional_details=trust_result
                )
                return {
                    "error": "Access denied - security validation failed",
                    "trust_score": trust_result["trust_score"],
                    "recommendations": trust_result["recommendations"]
                }
            
            # Compliance validation
            request_data = {
                "text_length": len(text),
                "processing_purpose": user_context.get("purpose", "redaction"),
                "entity_types": []  # Will be populated after detection
            }
            
            compliance_result = self.compliance_validator.validate_redaction_request(
                request_data, user_context
            )
            
            if not compliance_result["compliant"]:
                self.audit_logger.log_security_event(
                    event_type="COMPLIANCE_VIOLATION",
                    description=f"Compliance validation failed: {compliance_result['violations']}",
                    severity="HIGH",
                    user_id=user_context.get("user_id"),
                    additional_details=compliance_result
                )
                # Still proceed but log violation for audit
        
        # Check cache first
        cached_result = None
        if self.cache:
            cached_result = self.cache.get(text, self.config_hash)
            if cached_result:
                # Log cache hit for audit
                self.audit_logger.log_redaction_event(
                    operation="CACHED_REDACTION",
                    text_length=len(text),
                    entities_found=len(cached_result.get('spans', [])),
                    entity_types=[span.get('label', 'UNKNOWN') for span in cached_result.get('spans', [])],
                    user_id=user_context.get("user_id") if user_context else None,
                    session_id=session_id,
                    country=self.cfg.country,
                    additional_details={"cache_hit": True}
                )
                
                # Update performance metrics for cache hit
                total_time = self.performance_monitor.end_timing(start_time)
                metrics = ProcessingMetrics(
                    total_time=total_time,
                    detection_time=0,
                    redaction_time=0,
                    entities_found=len(cached_result.get('spans', [])),
                    text_length=len(text),
                    throughput_chars_per_sec=len(text) / max(total_time, 0.001),
                    cache_hits=1,
                    cache_misses=0
                )
                self.performance_monitor.record_metrics(metrics)
                return cached_result
        
        # Process with performance monitoring
        if self.cfg.use_async:
            result = asyncio.run(self._redact_async(text))
        else:
            result = self._redact_sync(text)
        
        # Log redaction event for audit
        entity_types = [span.get('label', 'UNKNOWN') for span in result.get('spans', [])]
        self.audit_logger.log_redaction_event(
            operation="TEXT_REDACTION",
            text_length=len(text),
            entities_found=len(result.get('spans', [])),
            entity_types=entity_types,
            user_id=user_context.get("user_id") if user_context else None,
            session_id=session_id,
            country=self.cfg.country,
            data_classification=user_context.get("data_classification", "SENSITIVE") if user_context else "SENSITIVE",
            additional_details={
                "cache_hit": False,
                "processing_mode": "async" if self.cfg.use_async else "sync",
                "parallel_detection": self.cfg.parallel_detection,
                "redaction_strategy": result.get('strategy_used', 'default')
            }
        )
        
        # Cache the result
        if self.cache:
            self.cache.set(text, self.config_hash, result)
        
        # Record performance metrics
        total_time = self.performance_monitor.end_timing(start_time)
        metrics = ProcessingMetrics(
            total_time=total_time,
            detection_time=result.get('stats', {}).get('detection_time', 0),
            redaction_time=result.get('stats', {}).get('redaction_time', 0),
            entities_found=len(result.get('spans', [])),
            text_length=len(text),
            throughput_chars_per_sec=len(text) / max(total_time, 0.001),
            cache_hits=0,
            cache_misses=1 if self.cache else 0
        )
        self.performance_monitor.record_metrics(metrics)
        
        return result
    
    def _redact_sync(self, text: str) -> Dict[str, object]:
        """Synchronous redaction pipeline with performance optimization"""
        detection_start = time.time()
        spans: List[Span] = []
        
        if self.cfg.parallel_detection:
            # Run detectors in parallel using thread pool
            futures = []
            for comp in self.components:
                future = self.executor.submit(comp.detect, text)
                futures.append(future)
            
            for future in futures:
                try:
                    component_spans = future.result(timeout=30)  # 30 second timeout
                    spans.extend(component_spans)
                except Exception as e:
                    print(f"Detector failed: {e}")
                    continue
        else:
            # Sequential detection
            for comp in self.components:
                try:
                    component_spans = comp.detect(text)
                    spans.extend(component_spans)
                except Exception as e:
                    print(f"Detector {comp.name} failed: {e}")
                    continue

        detection_time = time.time() - detection_start
        redaction_start = time.time()
        
        result = self._process_spans(text, spans)
        
        redaction_time = time.time() - redaction_start
        
        # Add timing information to stats
        if 'stats' not in result:
            result['stats'] = {}
        result['stats']['detection_time'] = detection_time
        result['stats']['redaction_time'] = redaction_time
        
        return result
    
    async def _redact_async(self, text: str) -> Dict[str, object]:
        """Asynchronous redaction pipeline"""
        spans: List[Span] = []
        
        # Run detectors concurrently
        tasks = []
        for comp in self.components:
            task = asyncio.create_task(self._run_detector_async(comp, text))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Async detector failed: {result}")
                continue
            spans.extend(result)

        return self._process_spans(text, spans)
    
    async def _run_detector_async(self, detector, text: str) -> List[Span]:
        """Run detector in async context"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, detector.detect, text)
    
    def _process_spans(self, text: str, spans: List[Span]) -> Dict[str, object]:
        """Process and merge detected spans"""
        # Sort spans by position and priority
        spans.sort(key=lambda x: (x.start, -x.end, -x.score))
        
        # Advanced span merging with confidence-based resolution
        merged: List[Span] = []
        for s in spans:
            if merged and self._spans_overlap(merged[-1], s):
                existing = merged[-1]
                
                # Choose span based on multiple criteria
                if self._should_replace_span(existing, s):
                    merged[-1] = s
                # Optionally merge spans if they're complementary
                elif self.cfg.merge_overlapping:
                    merged[-1] = self._merge_spans(existing, s)
                continue
            merged.append(s)

        # Apply redaction policies
        from ..policies.loader import load_policy
        policy = load_policy(self.cfg.country, self.cfg.company)
        actions = policy.get("actions", {})
        
        # Generate redacted text
        out_text = []
        i = 0
        redaction_log = []
        
        for s in merged:
            # Add text before redaction
            out_text.append(text[i:s.start])
            
            # Get redaction action for this entity type
            action = actions.get(s.label, actions.get("default", "hash"))
            original_text = text[s.start:s.end]
            
            # Apply redaction
            redacted_text = self._apply_redaction(original_text, s.label, action)
            out_text.append(redacted_text)
            
            # Log redaction for audit trail
            redaction_log.append({
                "original_length": len(original_text),
                "entity_type": s.label,
                "action": action,
                "confidence": s.score,
                "detector": s.source,
                "position": [s.start, s.end]
            })
            
            i = s.end
        
        # Add remaining text
        out_text.append(text[i:])
<<<<<<< HEAD
        return {"text": "".join(out_text), "spans": [s.__dict__ for s in merged]}

    def scan(self, text: str) -> Dict[str, object]:
        """Scan text for PII/PHI without redacting. Returns detection report."""
        spans: List[Span] = []
        for comp in self.components:
            spans.extend(comp.detect(text))

        spans.sort(key=lambda x: (x.start, -x.end))
        merged: List[Span] = []
        for s in spans:
            if merged and not (s.start >= merged[-1].end or s.end <= merged[-1].start):
                a = merged[-1]
                if (s.end - s.start) > (a.end - a.start) or s.score >= a.score:
                    merged[-1] = s
                continue
            merged.append(s)

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
                "text": text[s.start:s.end],
                "context": text[max(0, s.start-20):min(len(text), s.end+20)]
            })

        return {
            "original_text": text,
            "total_detections": len(merged),
            "entity_counts": entity_counts,
            "detections": detections,
            "has_pii": len(merged) > 0
=======
        
        # Generate comprehensive result
        result = {
            "text": "".join(out_text),
            "spans": [s.__dict__ for s in merged],
            "redaction_log": redaction_log,
            "stats": {
                "total_entities": len(merged),
                "entity_types": list(set(s.label for s in merged)),
                "confidence_distribution": self._calculate_confidence_stats(merged),
                "detectors_used": list(set(s.source for s in merged))
            }
        }
        
        return result
    
    def _spans_overlap(self, span1: Span, span2: Span) -> bool:
        """Check if two spans overlap"""
        return not (span1.end <= span2.start or span2.end <= span1.start)
    
    def _should_replace_span(self, existing: Span, new: Span) -> bool:
        """Determine if new span should replace existing one"""
        # Prefer longer spans
        if len(new.end - new.start) > len(existing.end - existing.start):
            return True
        
        # Prefer higher confidence
        if new.score > existing.score + 0.1:  # Small threshold for stability
            return True
        
        # Prefer more specific entity types
        specificity_order = [
            'regex', 'custom', 'spacy', 'bert', 'openmed', 'statistical'
        ]
        
        existing_priority = specificity_order.index(existing.source) if existing.source in specificity_order else 999
        new_priority = specificity_order.index(new.source) if new.source in specificity_order else 999
        
        return new_priority < existing_priority
    
    def _merge_spans(self, span1: Span, span2: Span) -> Span:
        """Merge two overlapping spans"""
        return Span(
            start=min(span1.start, span2.start),
            end=max(span1.end, span2.end),
            label=span1.label if span1.score >= span2.score else span2.label,
            score=(span1.score + span2.score) / 2,
            source=f"{span1.source}+{span2.source}"
        )
    
    def _calculate_confidence_stats(self, spans: List[Span]) -> Dict[str, float]:
        """Calculate confidence statistics"""
        if not spans:
            return {"mean": 0.0, "min": 0.0, "max": 0.0}
        
        scores = [s.score for s in spans]
        return {
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores)
>>>>>>> 169e84a6d9f4b73172a9aad0989d646c76618b36
        }
