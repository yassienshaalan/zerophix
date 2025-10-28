import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import pickle
from functools import wraps
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

@dataclass
class ProcessingMetrics:
    """Metrics for performance monitoring"""
    total_time: float
    detection_time: float
    redaction_time: float
    entities_found: int
    text_length: int
    throughput_chars_per_sec: float
    cache_hits: int = 0
    cache_misses: int = 0

class PerformanceCache:
    """High-performance caching for detection results"""
    
    def __init__(self, cache_type: str = "memory", redis_url: Optional[str] = None, 
                 max_memory_items: int = 10000, ttl_seconds: int = 3600):
        """
        Initialize cache
        
        Args:
            cache_type: "memory", "redis", or "hybrid"
            redis_url: Redis connection URL for distributed caching
            max_memory_items: Maximum items in memory cache
            ttl_seconds: Time to live for cached items
        """
        self.cache_type = cache_type
        self.max_memory_items = max_memory_items
        self.ttl_seconds = ttl_seconds
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # Redis setup
        self.redis_client = None
        if cache_type in ["redis", "hybrid"] and REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
            except Exception as e:
                logging.warning(f"Redis connection failed: {e}. Falling back to memory cache.")
                self.cache_type = "memory"
    
    def _generate_cache_key(self, text: str, config_hash: str) -> str:
        """Generate cache key for text and configuration"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        return f"zerophi:{config_hash}:{text_hash}"
    
    def get(self, text: str, config_hash: str) -> Optional[Any]:
        """Get cached detection results"""
        cache_key = self._generate_cache_key(text, config_hash)
        
        # Try memory cache first
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.ttl_seconds:
                self.cache_stats["hits"] += 1
                return cached_item["data"]
            else:
                # Expired
                del self.memory_cache[cache_key]
        
        # Try Redis cache
        if self.redis_client and self.cache_type in ["redis", "hybrid"]:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    result = pickle.loads(cached_data)
                    # Store in memory cache for faster access
                    if self.cache_type == "hybrid":
                        self._store_memory(cache_key, result)
                    return result
            except Exception as e:
                logging.warning(f"Redis get error: {e}")
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, text: str, config_hash: str, data: Any):
        """Cache detection results"""
        cache_key = self._generate_cache_key(text, config_hash)
        
        # Store in memory cache
        if self.cache_type in ["memory", "hybrid"]:
            self._store_memory(cache_key, data)
        
        # Store in Redis cache
        if self.redis_client and self.cache_type in ["redis", "hybrid"]:
            try:
                serialized_data = pickle.dumps(data)
                self.redis_client.setex(cache_key, self.ttl_seconds, serialized_data)
            except Exception as e:
                logging.warning(f"Redis set error: {e}")
    
    def _store_memory(self, cache_key: str, data: Any):
        """Store item in memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Simple LRU: remove oldest item
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]["timestamp"])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hit_rate": hit_rate,
            "total_hits": self.cache_stats["hits"],
            "total_misses": self.cache_stats["misses"],
            "memory_cache_size": len(self.memory_cache),
            "cache_type": self.cache_type
        }
    
    def clear(self):
        """Clear all caches"""
        self.memory_cache.clear()
        if self.redis_client:
            try:
                # Clear only zerophi keys
                keys = self.redis_client.keys("zerophi:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logging.warning(f"Redis clear error: {e}")

class BatchProcessor:
    """Efficient batch processing for large datasets"""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4, 
                 use_process_pool: bool = False):
        """
        Initialize batch processor
        
        Args:
            batch_size: Number of items per batch
            max_workers: Maximum number of worker threads/processes
            use_process_pool: Use process pool instead of thread pool for CPU-intensive work
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool
        
        if use_process_pool:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batch(self, texts: List[str], processor_func: Callable, 
                     progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Process a batch of texts in parallel
        
        Args:
            texts: List of texts to process
            processor_func: Function to apply to each text
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of processing results
        """
        results = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        # Split into batches
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(texts))
            batch = texts[start_idx:end_idx]
            
            # Submit batch for processing
            futures = []
            for text in batch:
                future = self.executor.submit(processor_func, text)
                futures.append(future)
            
            # Collect results
            batch_results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    batch_results.append(result)
                except Exception as e:
                    logging.error(f"Batch processing error: {e}")
                    batch_results.append(None)
            
            results.extend(batch_results)
            
            # Progress callback
            if progress_callback:
                progress = (batch_idx + 1) / total_batches
                progress_callback(progress, batch_idx + 1, total_batches)
        
        return results
    
    async def process_batch_async(self, texts: List[str], processor_func: Callable,
                                 progress_callback: Optional[Callable] = None) -> List[Any]:
        """Async version of batch processing"""
        results = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(texts))
            batch = texts[start_idx:end_idx]
            
            # Process batch asynchronously
            tasks = []
            for text in batch:
                if asyncio.iscoroutinefunction(processor_func):
                    task = asyncio.create_task(processor_func(text))
                else:
                    # Wrap sync function in async
                    task = asyncio.create_task(asyncio.to_thread(processor_func, text))
                tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logging.error(f"Async batch processing error: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            results.extend(processed_results)
            
            # Progress callback
            if progress_callback:
                progress = (batch_idx + 1) / total_batches
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(progress, batch_idx + 1, total_batches)
                else:
                    progress_callback(progress, batch_idx + 1, total_batches)
        
        return results
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)

class StreamProcessor:
    """Stream processing for real-time redaction"""
    
    def __init__(self, buffer_size: int = 1000, flush_interval: float = 1.0):
        """
        Initialize stream processor
        
        Args:
            buffer_size: Maximum number of items to buffer
            flush_interval: Time interval for flushing buffer (seconds)
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.last_flush = time.time()
        self.metrics = {"processed": 0, "errors": 0}
    
    async def process_stream(self, input_stream, processor_func: Callable, 
                           output_handler: Callable):
        """
        Process a stream of data
        
        Args:
            input_stream: Async iterable of input items
            processor_func: Function to process each item
            output_handler: Function to handle processed results
        """
        async for item in input_stream:
            try:
                # Process item
                if asyncio.iscoroutinefunction(processor_func):
                    result = await processor_func(item)
                else:
                    result = await asyncio.to_thread(processor_func, item)
                
                # Add to buffer
                self.buffer.append(result)
                self.metrics["processed"] += 1
                
                # Check if buffer should be flushed
                current_time = time.time()
                if (len(self.buffer) >= self.buffer_size or 
                    current_time - self.last_flush >= self.flush_interval):
                    await self._flush_buffer(output_handler)
                
            except Exception as e:
                logging.error(f"Stream processing error: {e}")
                self.metrics["errors"] += 1
        
        # Flush remaining items
        if self.buffer:
            await self._flush_buffer(output_handler)
    
    async def _flush_buffer(self, output_handler: Callable):
        """Flush buffer to output handler"""
        if not self.buffer:
            return
        
        try:
            if asyncio.iscoroutinefunction(output_handler):
                await output_handler(self.buffer.copy())
            else:
                await asyncio.to_thread(output_handler, self.buffer.copy())
        except Exception as e:
            logging.error(f"Buffer flush error: {e}")
        
        self.buffer.clear()
        self.last_flush = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        return self.metrics.copy()

class PerformanceMonitor:
    """Monitor and optimize performance"""
    
    def __init__(self):
        self.metrics_history = []
        self.current_metrics = ProcessingMetrics(0, 0, 0, 0, 0, 0)
    
    def start_timing(self) -> float:
        """Start timing an operation"""
        return time.perf_counter()
    
    def end_timing(self, start_time: float) -> float:
        """End timing and return duration"""
        return time.perf_counter() - start_time
    
    def record_metrics(self, metrics: ProcessingMetrics):
        """Record performance metrics"""
        self.metrics_history.append(metrics)
        self.current_metrics = metrics
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {}
        
        total_times = [m.total_time for m in self.metrics_history]
        throughputs = [m.throughput_chars_per_sec for m in self.metrics_history]
        cache_hit_rates = []
        
        for m in self.metrics_history:
            total_cache_ops = m.cache_hits + m.cache_misses
            hit_rate = m.cache_hits / total_cache_ops if total_cache_ops > 0 else 0
            cache_hit_rates.append(hit_rate)
        
        return {
            "avg_processing_time": sum(total_times) / len(total_times),
            "max_processing_time": max(total_times),
            "min_processing_time": min(total_times),
            "avg_throughput": sum(throughputs) / len(throughputs),
            "max_throughput": max(throughputs),
            "avg_cache_hit_rate": sum(cache_hit_rates) / len(cache_hit_rates),
            "total_operations": len(self.metrics_history)
        }
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        summary = self.get_performance_summary()
        
        if not summary:
            return recommendations
        
        # Check throughput
        if summary["avg_throughput"] < 1000:  # chars per second
            recommendations.append("Consider enabling parallel processing to improve throughput")
        
        # Check cache hit rate
        if summary["avg_cache_hit_rate"] < 0.5:
            recommendations.append("Cache hit rate is low. Consider increasing cache size or TTL")
        
        # Check processing time variance
        time_variance = summary["max_processing_time"] / summary["min_processing_time"]
        if time_variance > 10:
            recommendations.append("High processing time variance detected. Consider text preprocessing")
        
        return recommendations

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        logging.info(f"{func.__name__} took {duration:.4f} seconds")
        
        return result
    return wrapper

def async_performance_monitor(func):
    """Decorator to monitor async function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        logging.info(f"{func.__name__} took {duration:.4f} seconds")
        
        return result
    return wrapper

class AdaptiveOptimizer:
    """Adaptive optimization based on runtime performance"""
    
    def __init__(self):
        self.performance_history = []
        self.current_config = {
            "parallel_detection": True,
            "cache_enabled": True,
            "batch_size": 100,
            "max_workers": 4
        }
    
    def update_performance(self, metrics: ProcessingMetrics, config: Dict[str, Any]):
        """Update performance metrics and potentially adjust configuration"""
        self.performance_history.append({
            "metrics": metrics,
            "config": config.copy(),
            "timestamp": time.time()
        })
        
        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Trigger optimization if we have enough data
        if len(self.performance_history) >= 10:
            self._optimize_configuration()
    
    def _optimize_configuration(self):
        """Optimize configuration based on performance history"""
        recent_metrics = self.performance_history[-10:]
        
        # Calculate average throughput for current config
        avg_throughput = sum(m["metrics"].throughput_chars_per_sec for m in recent_metrics) / len(recent_metrics)
        
        # Simple optimization rules
        if avg_throughput < 500:  # Low throughput
            if self.current_config["max_workers"] < 8:
                self.current_config["max_workers"] += 1
                logging.info(f"Increased max_workers to {self.current_config['max_workers']}")
        elif avg_throughput > 2000:  # High throughput, might reduce workers to save resources
            if self.current_config["max_workers"] > 2:
                self.current_config["max_workers"] -= 1
                logging.info(f"Decreased max_workers to {self.current_config['max_workers']}")
    
    def get_optimized_config(self) -> Dict[str, Any]:
        """Get current optimized configuration"""
        return self.current_config.copy()