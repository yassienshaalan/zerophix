"""
Global Model Cache for ZeroPhix
Ensures models are loaded once and reused across pipeline instances
Massive performance boost for batch processing
"""

import threading
from typing import Dict, Any, Optional


class ModelCache:
    """Thread-safe singleton cache for ML models"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._cache_lock = threading.Lock()
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached model"""
        with self._cache_lock:
            return self._cache.get(key)
    
    def set(self, key: str, model: Any) -> None:
        """Cache a model"""
        with self._cache_lock:
            self._cache[key] = model
    
    def has(self, key: str) -> bool:
        """Check if model is cached"""
        with self._cache_lock:
            return key in self._cache
    
    def clear(self) -> None:
        """Clear all cached models (useful for memory management)"""
        with self._cache_lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached models"""
        with self._cache_lock:
            return len(self._cache)


# Global singleton instance
_model_cache = ModelCache()


def get_model_cache() -> ModelCache:
    """Get the global model cache instance"""
    return _model_cache
