"""
DataFrame processors for Pandas and PySpark
Redact PII/PHI in tabular data with column-level control
"""

from typing import List, Optional, Union, Dict, Any
from ..config import RedactionConfig
from ..pipelines.redaction import RedactionPipeline


class DataFrameProcessor:
    """
    Process Pandas and PySpark DataFrames with column-level redaction
    
    Features:
    - Redact specific columns
    - Preserve DataFrame structure
    - Batch processing for performance
    - Support for both Pandas and PySpark
    
    Example:
        processor = DataFrameProcessor(country='US')
        
        # Pandas DataFrame
        df_clean = processor.redact_dataframe(df, columns=['name', 'email', 'ssn'])
        
        # PySpark DataFrame
        spark_df_clean = processor.redact_spark_dataframe(spark_df, columns=['patient_name', 'mrn'])
    """
    
    def __init__(self, 
                 config: Optional[RedactionConfig] = None,
                 country: str = "US",
                 use_spacy: bool = True,
                 use_gliner: bool = False,
                 use_bert: bool = False):
        """
        Initialize DataFrame processor
        
        Args:
            config: RedactionConfig object (if None, creates default)
            country: Country code for policy
            use_spacy: Enable spaCy detector
            use_gliner: Enable GLiNER detector
            use_bert: Enable BERT detector
        """
        if config is None:
            config = RedactionConfig(
                country=country,
                use_spacy=use_spacy,
                use_gliner=use_gliner,
                use_bert=use_bert
            )
        
        self.config = config
        self.pipeline = RedactionPipeline(config)
    
    def redact_dataframe(self, 
                        df,
                        columns: Optional[List[str]] = None,
                        inplace: bool = False,
                        show_entities: bool = False) -> Any:
        """
        Redact PII/PHI in Pandas DataFrame
        
        Args:
            df: Pandas DataFrame
            columns: List of column names to redact (if None, redacts all string columns)
            inplace: Modify DataFrame in place (default: False, returns copy)
            show_entities: Add metadata columns with detected entities
            
        Returns:
            Redacted DataFrame (or None if inplace=True)
            
        Example:
            import pandas as pd
            
            df = pd.DataFrame({
                'id': [1, 2, 3],
                'name': ['John Smith', 'Jane Doe', 'Bob Wilson'],
                'email': ['john@example.com', 'jane@test.com', 'bob@company.com'],
                'ssn': ['123-45-6789', '987-65-4321', '555-12-3456']
            })
            
            processor = DataFrameProcessor(country='US')
            df_clean = processor.redact_dataframe(df, columns=['name', 'email', 'ssn'])
            
            print(df_clean)
            # Output:
            #    id         name              email           ssn
            # 0   1   [PERSON]        [EMAIL]      [SSN_US]
            # 1   2   [PERSON]        [EMAIL]      [SSN_US]
            # 2   3   [PERSON]        [EMAIL]      [SSN_US]
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas not installed. Install with: pip install pandas")
        
        if not inplace:
            df = df.copy()
        
        # Auto-detect string columns if not specified
        if columns is None:
            columns = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        # Process each column
        for col in columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found in DataFrame")
                continue
            
            # Redact each cell
            redacted_values = []
            entity_metadata = [] if show_entities else None
            
            for value in df[col]:
                if pd.isna(value) or value == '' or not isinstance(value, str):
                    redacted_values.append(value)
                    if show_entities:
                        entity_metadata.append(None)
                    continue
                
                result = self.pipeline.redact(str(value))
                redacted_values.append(result['text'])
                
                if show_entities:
                    entity_metadata.append({
                        'count': len(result['spans']),
                        'types': list(set([s['label'] for s in result['spans']]))
                    })
            
            df[col] = redacted_values
            
            if show_entities:
                df[f'{col}_entities'] = entity_metadata
        
        if not inplace:
            return df
    
    def redact_spark_dataframe(self,
                              spark_df,
                              columns: Optional[List[str]] = None,
                              broadcast_pipeline: bool = True) -> Any:
        """
        Redact PII/PHI in PySpark DataFrame
        
        Args:
            spark_df: PySpark DataFrame
            columns: List of column names to redact
            broadcast_pipeline: Broadcast pipeline to workers for performance
            
        Returns:
            Redacted PySpark DataFrame
            
        Example:
            from pyspark.sql import SparkSession
            
            spark = SparkSession.builder.appName("ZeroPhix").getOrCreate()
            
            df = spark.createDataFrame([
                (1, 'John Smith', 'john@example.com'),
                (2, 'Jane Doe', 'jane@test.com'),
                (3, 'Bob Wilson', 'bob@company.com')
            ], ['id', 'name', 'email'])
            
            processor = DataFrameProcessor(country='US')
            df_clean = processor.redact_spark_dataframe(df, columns=['name', 'email'])
            
            df_clean.show()
            # Output:
            # +---+---------+--------+
            # | id|     name|   email|
            # +---+---------+--------+
            # |  1| [PERSON]| [EMAIL]|
            # |  2| [PERSON]| [EMAIL]|
            # |  3| [PERSON]| [EMAIL]|
            # +---+---------+--------+
        """
        try:
            from pyspark.sql import functions as F
            from pyspark.sql.types import StringType
        except ImportError:
            raise ImportError("PySpark not installed. Install with: pip install pyspark")
        
        # Auto-detect string columns if not specified
        if columns is None:
            columns = [field.name for field in spark_df.schema.fields 
                      if str(field.dataType) == 'StringType']
        
        # Create redaction UDF
        def redact_udf(text):
            if text is None or text == '':
                return text
            result = self.pipeline.redact(text)
            return result['text']
        
        # Register UDF
        from pyspark.sql.functions import udf
        redact_fn = udf(redact_udf, StringType())
        
        # Broadcast pipeline if requested (for better performance)
        if broadcast_pipeline:
            try:
                spark = spark_df.sql_ctx.sparkSession
                broadcast_var = spark.sparkContext.broadcast(self.pipeline)
                
                def redact_broadcast_udf(text):
                    if text is None or text == '':
                        return text
                    pipeline = broadcast_var.value
                    result = pipeline.redact(text)
                    return result['text']
                
                redact_fn = udf(redact_broadcast_udf, StringType())
            except Exception as e:
                print(f"Warning: Could not broadcast pipeline: {e}. Using standard UDF.")
        
        # Apply redaction to specified columns
        for col in columns:
            if col not in spark_df.columns:
                print(f"Warning: Column '{col}' not found in DataFrame")
                continue
            
            spark_df = spark_df.withColumn(col, redact_fn(F.col(col)))
        
        return spark_df
    
    def scan_dataframe(self,
                      df,
                      columns: Optional[List[str]] = None,
                      return_summary: bool = True) -> Dict[str, Any]:
        """
        Scan Pandas DataFrame for PII/PHI without redacting
        
        Args:
            df: Pandas DataFrame
            columns: Columns to scan (if None, scans all string columns)
            return_summary: Return summary statistics
            
        Returns:
            Dictionary with scan results and statistics
            
        Example:
            scan_results = processor.scan_dataframe(df, columns=['name', 'email'])
            print(f"Total PII instances: {scan_results['total_entities']}")
            print(f"Affected rows: {scan_results['affected_rows']}")
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas not installed. Install with: pip install pandas")
        
        if columns is None:
            columns = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        results = {
            'total_entities': 0,
            'affected_rows': 0,
            'by_column': {},
            'by_entity_type': {}
        }
        
        affected_rows = set()
        
        for col in columns:
            if col not in df.columns:
                continue
            
            col_entities = 0
            entity_types = {}
            
            for idx, value in enumerate(df[col]):
                if pd.isna(value) or value == '' or not isinstance(value, str):
                    continue
                
                scan_result = self.pipeline.scan(str(value))
                
                if scan_result:
                    col_entities += len(scan_result)
                    affected_rows.add(idx)
                    
                    for span in scan_result:
                        entity_type = span.label
                        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                        results['by_entity_type'][entity_type] = results['by_entity_type'].get(entity_type, 0) + 1
            
            results['by_column'][col] = {
                'count': col_entities,
                'types': entity_types
            }
            results['total_entities'] += col_entities
        
        results['affected_rows'] = len(affected_rows)
        results['total_rows'] = len(df)
        results['percentage_affected'] = (len(affected_rows) / len(df) * 100) if len(df) > 0 else 0
        
        return results


# Convenience functions
def redact_pandas(df, columns: Optional[List[str]] = None, country: str = "US", **kwargs):
    """
    Quick function to redact Pandas DataFrame
    
    Example:
        from zerophix.processors import redact_pandas
        df_clean = redact_pandas(df, columns=['name', 'email'], country='US')
    """
    processor = DataFrameProcessor(country=country, **kwargs)
    return processor.redact_dataframe(df, columns=columns)


def redact_spark(spark_df, columns: Optional[List[str]] = None, country: str = "US", **kwargs):
    """
    Quick function to redact PySpark DataFrame
    
    Example:
        from zerophix.processors import redact_spark
        df_clean = redact_spark(spark_df, columns=['patient_name', 'mrn'], country='US')
    """
    processor = DataFrameProcessor(country=country, **kwargs)
    return processor.redact_spark_dataframe(spark_df, columns=columns)
