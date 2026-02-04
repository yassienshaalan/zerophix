# Performance optimization module for ZeroPhix
from .optimization import (
    PerformanceCache,
    StreamProcessor,
    PerformanceMonitor,
    ProcessingMetrics,
    AdaptiveOptimizer,
    performance_monitor,
    async_performance_monitor
)

# New high-performance utilities
from .model_cache import ModelCache, get_model_cache
from .batch_processor import BatchProcessor, DatabricksOptimizer, optimize_batch_size
from .text_cache import TextPreprocessor, get_text_preprocessor

__all__ = [
    # Original exports
    'PerformanceCache',
    'StreamProcessor',
    'PerformanceMonitor',
    'ProcessingMetrics',
    'AdaptiveOptimizer',
    'performance_monitor',
    'async_performance_monitor',
    
    # New performance utilities
    'ModelCache',
    'get_model_cache',
    'BatchProcessor',
    'DatabricksOptimizer',
    'optimize_batch_size',
    'TextPreprocessor',
    'get_text_preprocessor',
]