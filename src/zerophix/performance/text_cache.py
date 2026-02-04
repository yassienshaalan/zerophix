"""
Text preprocessing cache to avoid redundant operations
"""

import hashlib
from functools import lru_cache
from typing import Dict, Optional, Tuple


class TextPreprocessor:
    """
    Cache text preprocessing results for performance
    """
    
    def __init__(self, cache_size: int = 10000):
        """
        Initialize text preprocessor with LRU cache
        
        Args:
            cache_size: Maximum number of cached preprocessed texts
        """
        self.cache_size = cache_size
        # Use LRU cache for automatic memory management
        self._normalize_text = lru_cache(maxsize=cache_size)(self._normalize_text_impl)
        self._compute_hash = lru_cache(maxsize=cache_size)(self._compute_hash_impl)
    
    def _compute_hash_impl(self, text: str) -> str:
        """Compute hash of text for deduplication"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def compute_hash(self, text: str) -> str:
        """Cached hash computation"""
        return self._compute_hash(text)
    
    def _normalize_text_impl(self, text: str) -> str:
        """Normalize text (lowercase, strip, etc.)"""
        # Basic normalization
        normalized = text.strip()
        # Remove excessive whitespace
        normalized = ' '.join(normalized.split())
        return normalized
    
    def normalize_text(self, text: str) -> str:
        """Cached text normalization"""
        return self._normalize_text(text)
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'normalize_hits': self._normalize_text.cache_info().hits,
            'normalize_misses': self._normalize_text.cache_info().misses,
            'normalize_size': self._normalize_text.cache_info().currsize,
            'hash_hits': self._compute_hash.cache_info().hits,
            'hash_misses': self._compute_hash.cache_info().misses,
            'hash_size': self._compute_hash.cache_info().currsize,
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self._normalize_text.cache_clear()
        self._compute_hash.cache_clear()


# Global preprocessor instance
_global_preprocessor = None


def get_text_preprocessor(cache_size: int = 10000) -> TextPreprocessor:
    """Get or create global text preprocessor"""
    global _global_preprocessor
    if _global_preprocessor is None:
        _global_preprocessor = TextPreprocessor(cache_size=cache_size)
    return _global_preprocessor
