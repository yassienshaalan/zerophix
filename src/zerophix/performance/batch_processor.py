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
                 show_progress: bool = True,
                 parallel_detectors: bool = True):
        """
        Initialize batch processor
        
        Args:
            pipeline: RedactionPipeline instance (must be picklable for process mode)
            n_workers: Number of parallel workers (default: CPU count)
            use_processes: Use processes instead of threads (better for CPU-heavy)
            chunk_size: Number of documents per batch
            show_progress: Show progress bar
            parallel_detectors: Run detectors in parallel within each document (3-4x faster)
        """
        self.pipeline = pipeline
        self.n_workers = n_workers or mp.cpu_count()
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        self.show_progress = show_progress
        self.parallel_detectors = parallel_detectors
    
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
                    result = self.pipeline.scan(text, parallel_detectors=self.parallel_detectors)
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
                    future = executor.submit(self.pipeline.scan, text, self.parallel_detectors)
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
                    result = self.pipeline.scan(text, parallel_detectors=self.parallel_detectors)
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
    def get_optimal_config():
        """
        Dynamically detect cluster resources and return optimized configuration
        
        Returns:
            Dict with optimal settings based on current cluster
        """
        config = {
            'n_workers': mp.cpu_count(),
            'executor_memory': '8g',
            'executor_cores': 4,
            'batch_size': 100,
            'use_gpu': False,
            'max_concurrent_tasks': mp.cpu_count() * 2
        }
        
        try:
            # Try to detect Databricks environment
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            sc = spark.sparkContext
            
            # Get cluster configuration
            executor_memory = sc.getConf().get('spark.executor.memory', '8g')
            executor_cores = int(sc.getConf().get('spark.executor.cores', '4'))
            num_executors = len(sc._jsc.sc().statusTracker().getExecutorInfos()) - 1  # Exclude driver
            
            # Calculate total resources
            total_cores = executor_cores * max(num_executors, 1)
            
            # Aggressive optimization: use all available cores
            config['n_workers'] = total_cores
            config['executor_memory'] = executor_memory
            config['executor_cores'] = executor_cores
            config['max_concurrent_tasks'] = total_cores * 3  # Oversubscribe for I/O heavy
            
            # Adaptive batch size based on memory
            memory_gb = int(executor_memory.replace('g', '').replace('G', ''))
            config['batch_size'] = min(memory_gb * 25, 500)  # 25 docs per GB, max 500
            
            # Check for GPU availability
            try:
                import torch
                if torch.cuda.is_available():
                    config['use_gpu'] = True
                    config['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory // (1024**3)
                    # With GPU, increase batch size significantly
                    config['batch_size'] = min(config['batch_size'] * 2, 1000)
            except:
                pass
            
            print(f"Detected Databricks cluster configuration:")
            print(f"  - Executors: {max(num_executors, 1)}")
            print(f"  - Cores per executor: {executor_cores}")
            print(f"  - Total cores: {total_cores}")
            print(f"  - Executor memory: {executor_memory}")
            print(f"  - GPU available: {config['use_gpu']}")
            print(f"\nOptimized settings for maximum performance:")
            print(f"  - Workers: {config['n_workers']} (using ALL cores)")
            print(f"  - Batch size: {config['batch_size']}")
            print(f"  - Max concurrent: {config['max_concurrent_tasks']}")
            
        except Exception as e:
            print(f"Warning: Could not detect Spark cluster, using local defaults: {e}")
            print(f"  - Workers: {config['n_workers']} (local CPU count)")
            print(f"  - Batch size: {config['batch_size']}")
        
        return config
    
    @staticmethod
    def optimize_spark_config():
        """
        Print recommended Spark configuration for ZeroPhix on Databricks
        """
        config = (
            "Recommended Databricks Configuration for ZeroPhix\n\n"
            "Cluster Settings:\n"
            "- Runtime: ML Runtime 15.4 LTS (recommended for best performance)\n"
            "- Instance Type: GPU instances (g5.xlarge or better) for BERT/GLiNER\n"
            "- Workers: 4-16 depending on dataset size (more = faster)\n"
            "- Driver: Standard_DS5_v2 or better (16GB+ RAM)\n\n"
            "Aggressive Spark Configuration (Maximum Performance):\n"
            "- spark.executor.memory: 16g (or higher if available)\n"
            "- spark.executor.cores: 8 (use all available cores)\n"
            "- spark.task.cpus: 1\n"
            "- spark.default.parallelism: <num_cores * 3>\n"
            "- spark.sql.shuffle.partitions: <num_cores * 2>\n"
            "- spark.sql.execution.arrow.enabled: true\n"
            "- spark.sql.execution.arrow.pyspark.enabled: true\n"
            "- spark.sql.execution.arrow.maxRecordsPerBatch: 10000\n"
            "- spark.executor.memoryOverhead: 4g\n"
            "- spark.memory.fraction: 0.8\n"
            "- spark.memory.storageFraction: 0.3\n\n"
            "Python Libraries:\n"
            "%pip install zerophix[all] --upgrade --no-cache-dir\n\n"
            "Environment Variables:\n"
            "- TOKENIZERS_PARALLELISM: false\n"
            "- TRANSFORMERS_CACHE: /dbfs/models/cache\n"
            "- HF_HOME: /dbfs/models/huggingface\n"
            "- OMP_NUM_THREADS: 1\n\n"
            "Performance Tips (Push to Limit):\n"
            "1. Use broadcast variables for the pipeline object\n"
            "2. Repartition to num_workers * 3 for better parallelism\n"
            "3. Use .persist(StorageLevel.MEMORY_AND_DISK) for large datasets\n"
            "4. Enable adaptive query execution (AQE)\n"
            "5. Use mapInPandas with optimal batch sizes\n"
            "6. Cache models globally with ModelCache\n"
            "7. Process in parallel with BatchProcessor(n_workers=<total_cores>)\n"
        )
        print(config)
        return config
