"""
High-Performance Batch Processing for ZeroPhix
Optimized for Databricks and large-scale document processing
"""

from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
import time

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Fallback: simple progress indicator
    def tqdm(iterable, **kwargs):
        return iterable


class BatchProcessor:
    """
    Optimized batch processing with multiple strategies
    
    Features:
    - Thread-based parallelism for I/O-bound tasks
    - Process-based parallelism for CPU-bound tasks
    - Progress tracking with tqdm
    - Error handling and recovery
    - Memory-efficient chunking
    """
    
    def __init__(self, 
                 pipeline,
                 n_workers: Optional[int] = None,
                 use_processes: bool = False,
                 chunk_size: int = 100,
                 show_progress: bool = True):
        """
        Initialize batch processor
        
        Args:
            pipeline: RedactionPipeline instance (must be picklable for process mode)
            n_workers: Number of parallel workers (default: CPU count)
            use_processes: Use processes instead of threads (better for CPU-heavy)
            chunk_size: Number of documents per batch
            show_progress: Show progress bar
        """
        self.pipeline = pipeline
        self.n_workers = n_workers or mp.cpu_count()
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        self.show_progress = show_progress
    
    def process_batch(self, 
                     texts: List[str],
                     operation: str = 'redact',
                     **kwargs) -> List[Dict[str, Any]]:
        """
        Process a batch of texts with optimal parallelization
        
        Args:
            texts: List of text documents
            operation: 'redact' or 'scan'
            **kwargs: Additional arguments for the operation
            
        Returns:
            List of results (redacted texts or scan reports)
        """
        if len(texts) == 0:
            return []
        
        # For small batches, serial processing is faster
        if len(texts) < 10:
            return self._process_serial(texts, operation, **kwargs)
        
        # For medium batches, use thread-based parallelism
        if len(texts) < 100 or not self.use_processes:
            return self._process_parallel_threads(texts, operation, **kwargs)
        
        # For large batches, use process-based parallelism
        return self._process_parallel_processes(texts, operation, **kwargs)
    
    def _process_serial(self, texts: List[str], operation: str, **kwargs) -> List[Dict]:
        """Serial processing for small batches"""
        results = []
        iterator = tqdm(texts, desc=f"Processing ({operation})") if self.show_progress else texts
        
        for text in iterator:
            try:
                if operation == 'redact':
                    result = self.pipeline.redact(text, **kwargs)
                else:  # scan
                    result = self.pipeline.scan(text)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'text': text})
        
        return results
    
    def _process_parallel_threads(self, texts: List[str], operation: str, **kwargs) -> List[Dict]:
        """Thread-based parallel processing for I/O-bound operations"""
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
            futures = {}
            
            for idx, text in enumerate(texts):
                if operation == 'redact':
                    future = executor.submit(self.pipeline.redact, text, **kwargs)
                else:
                    future = executor.submit(self.pipeline.scan, text)
                futures[future] = idx
            
            iterator = tqdm(as_completed(futures), total=len(futures), 
                          desc=f"Processing ({operation})") if self.show_progress else as_completed(futures)
            
            for future in iterator:
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = {'error': str(e), 'text': texts[idx]}
        
        return results
    
    def _process_parallel_processes(self, texts: List[str], operation: str, **kwargs) -> List[Dict]:
        """Process-based parallel processing for CPU-bound operations"""
        # Chunk the texts for better load balancing
        chunks = [texts[i:i + self.chunk_size] for i in range(0, len(texts), self.chunk_size)]
        
        results = []
        
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            futures = [executor.submit(self._process_chunk, chunk, operation, **kwargs) 
                      for chunk in chunks]
            
            iterator = tqdm(as_completed(futures), total=len(futures),
                          desc=f"Processing chunks ({operation})") if self.show_progress else as_completed(futures)
            
            for future in iterator:
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    print(f"Chunk processing error: {e}")
        
        return results
    
    def _process_chunk(self, texts: List[str], operation: str, **kwargs) -> List[Dict]:
        """Process a chunk of texts (used in process pool)"""
        # Import here to avoid pickling issues
        results = []
        for text in texts:
            try:
                if operation == 'redact':
                    result = self.pipeline.redact(text, **kwargs)
                else:
                    result = self.pipeline.scan(text)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'text': text})
        return results


def optimize_batch_size(pipeline, sample_texts: List[str], max_test_size: int = 100) -> int:
    """
    Automatically determine optimal batch size for your hardware
    
    Args:
        pipeline: RedactionPipeline instance
        sample_texts: Sample texts representative of your data
        max_test_size: Maximum number of samples to test
        
    Returns:
        Optimal batch size for BatchProcessor
    """
    test_texts = sample_texts[:max_test_size]
    batch_sizes = [1, 10, 50, 100]
    
    timings = {}
    
    for batch_size in batch_sizes:
        if batch_size > len(test_texts):
            break
        
        test_subset = test_texts[:batch_size]
        
        start = time.time()
        processor = BatchProcessor(pipeline, chunk_size=batch_size, show_progress=False)
        processor.process_batch(test_subset, operation='scan')
        elapsed = time.time() - start
        
        time_per_doc = elapsed / batch_size
        timings[batch_size] = time_per_doc
        
        print(f"Batch size {batch_size:3d}: {time_per_doc:.4f}s per doc")
    
    # Find the batch size with best time per document
    optimal_size = min(timings, key=timings.get)
    
    print(f"\nOptimal batch size: {optimal_size}")
    return optimal_size


class DatabricksOptimizer:
    """
    Databricks-specific optimizations for ZeroPhix
    """
    
    @staticmethod
    def create_udf(pipeline, return_type='redacted'):
        """
        Create an optimized Spark UDF for Databricks
        
        Args:
            pipeline: RedactionPipeline instance
            return_type: 'redacted' (return redacted text) or 'spans' (return detected entities)
            
        Returns:
            PySpark UDF function
            
        Note:
            Requires PySpark to be installed. Install with: pip install pyspark
        """
        try:
            from pyspark.sql.functions import udf
            from pyspark.sql.types import StringType, ArrayType, StructType, StructField, FloatType, IntegerType
        except ImportError:
            raise ImportError(
                "PySpark not installed. Install with: pip install pyspark\n"
                "Or install zerophix with spark support: pip install zerophix[spark]"
            )
        
        if return_type == 'redacted':
            @udf(returnType=StringType())
            def redact_udf(text):
                if text is None:
                    return None
                try:
                    result = pipeline.redact(text)
                    return result['text']
                except Exception as e:
                    return f"[ERROR: {str(e)}]"
            return redact_udf
        
        else:  # return spans
            span_schema = ArrayType(StructType([
                StructField("start", IntegerType(), False),
                StructField("end", IntegerType(), False),
                StructField("label", StringType(), False),
                StructField("score", FloatType(), False),
                StructField("source", StringType(), False)
            ]))
            
            @udf(returnType=span_schema)
            def scan_udf(text):
                if text is None:
                    return []
                try:
                    spans = pipeline.scan(text)
                    return [
                        (s.start, s.end, s.label, float(s.score), s.source)
                        for s in spans
                    ]
                except Exception as e:
                    return []
            return scan_udf
    
    @staticmethod
    def optimize_spark_config():
        """
        Print recommended Spark configuration for ZeroPhix on Databricks
        """
        config = (
            "Recommended Databricks Configuration for ZeroPhix\n\n"
            "Cluster Settings:\n"
            "- Runtime: ML Runtime 13.3 LTS or later (includes transformers)\n"
            "- Instance Type: GPU instances (g5.xlarge or better) for BERT/GLiNER\n"
            "- Workers: 2-8 depending on dataset size\n\n"
            "Spark Configuration:\n"
            "- spark.executor.memory: 8g\n"
            "- spark.executor.cores: 4\n"
            "- spark.task.cpus: 1\n"
            "- spark.sql.execution.arrow.enabled: true\n"
            "- spark.sql.execution.arrow.pyspark.enabled: true\n\n"
            "Python Libraries:\n"
            "%pip install zerophix[all] --upgrade\n\n"
            "Environment Variables:\n"
            "- TRANSFORMERS_CACHE=/dbfs/models/cache\n"
            "- HF_HOME=/dbfs/models/huggingface\n\n"
            "Performance Tips:\n"
            "1. Use broadcast variables for the pipeline object\n"
            "2. Repartition data to match worker count\n"
            "3. Cache intermediate results with df.cache()\n"
            "4. Use mapInPandas for batch processing\n"
        )
        print(config)
        return config
