"""
Comprehensive examples for all ZeroPhix input interfaces:
- String
- List of strings (batch)
- Files (PDF, DOCX, Excel, CSV)
- Pandas DataFrame
- PySpark DataFrame
"""

import sys
sys.path.insert(0, 'src')

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig
from zerophix.processors import DataFrameProcessor, redact_pandas, redact_spark

print("=" * 80)
print("ZEROPHIX - ALL INPUT INTERFACES DEMO")
print("=" * 80)

config = RedactionConfig(
    country='US',
    use_spacy=False,
    use_gliner=False,  # Fast mode
    use_bert=False
)
pipeline = RedactionPipeline(config)

# ============================================================================
# 1. SINGLE STRING
# ============================================================================
print("\n[1] SINGLE STRING INPUT")
print("-" * 80)

text = "John Smith, SSN: 123-45-6789, Email: john.smith@example.com"
result = pipeline.redact(text)

print(f"Original: {text}")
print(f"Redacted: {result['text']}")
print(f"Entities: {len(result['spans'])} found")

# ============================================================================
# 2. LIST OF STRINGS (BATCH)
# ============================================================================
print("\n[2] BATCH PROCESSING - LIST OF STRINGS")
print("-" * 80)

texts = [
    "Patient: John Doe, MRN: 12345, DOB: 01/15/1980",
    "Contact: Jane Smith, Phone: 555-123-4567, Email: jane@hospital.com",
    "Employee: Bob Wilson, SSN: 987-65-4321, Salary: $75,000"
]

batch_results = pipeline.redact_batch(texts)

for i, result in enumerate(batch_results, 1):
    print(f"\nText {i}:")
    print(f"  Original: {texts[i-1]}")
    print(f"  Redacted: {result['text']}")
    print(f"  Entities: {len(result['spans'])}")

# ============================================================================
# 3. PANDAS DATAFRAME
# ============================================================================
print("\n[3] PANDAS DATAFRAME")
print("-" * 80)

try:
    import pandas as pd
    
    # Create sample DataFrame
    df = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'patient_name': ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown'],
        'email': ['john@example.com', 'jane@test.com', 'bob@company.com', 'alice@hospital.com'],
        'ssn': ['123-45-6789', '987-65-4321', '555-12-3456', '111-22-3333'],
        'notes': ['Patient has diabetes', 'Annual checkup', 'Surgery scheduled', 'Lab results pending']
    })
    
    print("\nOriginal DataFrame:")
    print(df.to_string(index=False))
    
    # Option 1: Using DataFrameProcessor
    processor = DataFrameProcessor(country='US', use_spacy=True)
    df_clean = processor.redact_dataframe(df, columns=['patient_name', 'email', 'ssn'])
    
    print("\nRedacted DataFrame:")
    print(df_clean.to_string(index=False))
    
    # Option 2: Quick function
    df_clean2 = redact_pandas(df, columns=['patient_name', 'email', 'ssn'], country='US')
    
    # Scan to see statistics
    scan_results = processor.scan_dataframe(df, columns=['patient_name', 'email', 'ssn', 'notes'])
    print(f"\nScan Results:")
    print(f"  Total entities: {scan_results['total_entities']}")
    print(f"  Affected rows: {scan_results['affected_rows']} / {scan_results['total_rows']}")
    print(f"  Percentage: {scan_results['percentage_affected']:.1f}%")
    print(f"  By column:")
    for col, stats in scan_results['by_column'].items():
        print(f"    {col}: {stats['count']} entities")

except ImportError:
    print("Pandas not installed. Install with: pip install pandas")
except Exception as e:
    print(f"Pandas example failed: {e}")

# ============================================================================
# 4. PYSPARK DATAFRAME
# ============================================================================
print("\n[4] PYSPARK DATAFRAME")
print("-" * 80)

try:
    from pyspark.sql import SparkSession
    
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("ZeroPhix") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    
    # Suppress Spark logs
    spark.sparkContext.setLogLevel("ERROR")
    
    # Create sample DataFrame
    data = [
        (1, 'John Smith', 'john@example.com', '123-45-6789'),
        (2, 'Jane Doe', 'jane@test.com', '987-65-4321'),
        (3, 'Bob Wilson', 'bob@company.com', '555-12-3456'),
        (4, 'Alice Brown', 'alice@hospital.com', '111-22-3333')
    ]
    
    spark_df = spark.createDataFrame(data, ['id', 'name', 'email', 'ssn'])
    
    print("\nOriginal PySpark DataFrame:")
    spark_df.show(truncate=False)
    
    # Redact using DataFrameProcessor
    processor = DataFrameProcessor(country='US', use_spacy=True)
    spark_df_clean = processor.redact_spark_dataframe(
        spark_df, 
        columns=['name', 'email', 'ssn'],
        broadcast_pipeline=True  # Performance optimization
    )
    
    print("\nRedacted PySpark DataFrame:")
    spark_df_clean.show(truncate=False)
    
    # Quick function approach
    spark_df_clean2 = redact_spark(spark_df, columns=['name', 'email', 'ssn'], country='US')
    
    spark.stop()

except ImportError:
    print("PySpark not installed. Install with: pip install pyspark")
except Exception as e:
    print(f"PySpark example failed: {e}")

# ============================================================================
# 5. FILE PROCESSING (PDF, DOCX, EXCEL)
# ============================================================================
print("\n[5] FILE PROCESSING")
print("-" * 80)

try:
    from zerophix.processors import PDFProcessor, ExcelProcessor
    
    # PDF
    print("\nPDF Processing:")
    print("  Use: PDFProcessor().redact_file(input_path, output_path, pipeline)")
    print("  Example: processor.redact_file('document.pdf', 'redacted.pdf', pipeline)")
    
    # Excel
    print("\nExcel Processing:")
    print("  Use: ExcelProcessor().redact_file(input_path, output_path, pipeline, columns=['A', 'B'])")
    print("  Example: processor.redact_file('data.xlsx', 'redacted.xlsx', pipeline)")
    
    # CSV
    print("\nCSV Processing:")
    print("  Read with Pandas, redact with redact_pandas(), save with df.to_csv()")
    
except Exception as e:
    print(f"File processing examples: {e}")

# ============================================================================
# 6. SCANNING (NO REDACTION)
# ============================================================================
print("\n[6] SCANNING WITHOUT REDACTION")
print("-" * 80)

text_to_scan = "Patient: John Smith, DOB: 01/15/1980, SSN: 123-45-6789, Phone: 555-1234"
scan_result = pipeline.scan(text_to_scan)

print(f"Text: {text_to_scan}")
print(f"\nScan Results:")
print(f"  Contains PII: {scan_result['has_pii']}")
print(f"  Total detections: {scan_result['total_detections']}")
print(f"  Entity types: {list(scan_result['entity_counts'].keys())}")
print(f"\nDetailed findings:")
for detection in scan_result['detections']:
    print(f"  - {detection['label']}: {detection['text']} (confidence: {detection['score']:.2f})")

print("\n" + "=" * 80)
print("ALL INPUT INTERFACES DEMONSTRATED")
print("=" * 80)
print("\nSummary:")
print("  ✓ Single string: pipeline.redact(text)")
print("  ✓ Batch strings: pipeline.redact_batch(texts)")
print("  ✓ Pandas DataFrame: redact_pandas(df, columns=['col1', 'col2'])")
print("  ✓ PySpark DataFrame: redact_spark(spark_df, columns=['col1', 'col2'])")
print("  ✓ PDF files: PDFProcessor().redact_file(input, output, pipeline)")
print("  ✓ Scanning: pipeline.scan(text) or processor.scan_dataframe(df)")
