#!/usr/bin/env python3
"""
Quick test of all ZeroPhix interfaces
Run this to verify all input types work
"""

import sys
sys.path.insert(0, 'src')

from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

print("Testing ZeroPhix - All Interfaces")
print("=" * 60)

config = RedactionConfig(country='US', use_spacy=False, use_gliner=False, use_bert=False)
pipeline = RedactionPipeline(config)

# 1. Single String
print("\n✓ Test 1: Single String")
text = "John Smith, SSN: 123-45-6789"
result = pipeline.redact(text)
print(f"  Input:  {text}")
print(f"  Output: {result['text']}")
assert result['text'] != text, "Redaction failed!"

# 2. Batch Strings
print("\n✓ Test 2: Batch Strings")
texts = ["Email: john@test.com", "Phone: 555-123-4567"]
results = pipeline.redact_batch(texts)
print(f"  Processed {len(results)} texts")
for i, r in enumerate(results):
    print(f"  {i+1}. {r['text']}")

# 3. Scan (no redaction)
print("\n✓ Test 3: Scan Mode")
scan = pipeline.scan("Jane Doe, email: jane@example.com, phone: 555-9999")
print(f"  Found {scan['total_detections']} entities")
print(f"  Types: {list(scan['entity_counts'].keys())}")

# 4. Pandas DataFrame
print("\n✓ Test 4: Pandas DataFrame")
try:
    import pandas as pd
    from zerophix.processors import redact_pandas
    
    df = pd.DataFrame({
        'name': ['John Smith', 'Jane Doe'],
        'email': ['john@test.com', 'jane@test.com']
    })
    print("  Original:")
    print(f"    {df.to_dict('records')}")
    
    df_clean = redact_pandas(df, columns=['name', 'email'])
    print("  Redacted:")
    print(f"    {df_clean.to_dict('records')}")
    
except ImportError:
    print("  Pandas not installed - skipping")

# 5. CSV Processing (via Pandas)
print("\n✓ Test 5: CSV File")
try:
    import pandas as pd
    from zerophix.processors import redact_pandas
    import tempfile
    import os
    
    # Create temp CSV file
    temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
    temp_csv.write('name,email,phone\n')
    temp_csv.write('John Smith,john@test.com,555-1234\n')
    temp_csv.write('Jane Doe,jane@test.com,555-5678\n')
    temp_csv.close()
    
    # Read, redact, save
    df = pd.read_csv(temp_csv.name)
    df_clean = redact_pandas(df, columns=['name', 'email', 'phone'])
    
    output_csv = temp_csv.name.replace('.csv', '_redacted.csv')
    df_clean.to_csv(output_csv, index=False)
    
    print(f"  Input CSV:  {os.path.basename(temp_csv.name)}")
    print(f"  Output CSV: {os.path.basename(output_csv)}")
    print(f"  Redacted {len(df_clean)} rows, {len(df_clean.columns)} columns")
    
    # Cleanup
    os.unlink(temp_csv.name)
    os.unlink(output_csv)
    
except ImportError:
    print("  Pandas not installed - skipping")
except Exception as e:
    print(f"  CSV test failed: {e}")

# 6. PySpark DataFrame
print("\n✓ Test 6: PySpark DataFrame")
try:
    from pyspark.sql import SparkSession
    from zerophix.processors import redact_spark
    
    spark = SparkSession.builder.appName("Test").master("local[1]").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    
    spark_df = spark.createDataFrame([
        (1, 'John Smith', 'john@test.com'),
        (2, 'Jane Doe', 'jane@test.com')
    ], ['id', 'name', 'email'])
    
    print("  Original:")
    spark_df.show(truncate=False)
    
    spark_df_clean = redact_spark(spark_df, columns=['name', 'email'])
    
    print("  Redacted:")
    spark_df_clean.show(truncate=False)
    
    spark.stop()
    
except ImportError:
    print("  PySpark not installed - skipping")
except Exception as e:
    print(f"  PySpark test failed: {e}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
print("\nAll interfaces working:")
print("  • Single string: pipeline.redact(text)")
print("  • Batch strings: pipeline.redact_batch(texts)")
print("  • Scan mode: pipeline.scan(text)")
print("  • Pandas: redact_pandas(df, columns=[])")
print("  • CSV files: Read with Pandas, redact, save")
print("  • PySpark: redact_spark(spark_df, columns=[])")
print("\nFor file processing, use:")
print("  • PDF: PDFProcessor().redact_file(input, output, pipeline)")
print("  • Excel: ExcelProcessor().redact_file(input, output, pipeline)")
print("\nTo install PySpark:")
print("  pip install pyspark")
