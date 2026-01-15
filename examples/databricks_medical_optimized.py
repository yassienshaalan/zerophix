# Databricks notebook source
# Australian Medical Records - Optimized for Maximum Accuracy
# Uses new label-specific thresholds and medical domain optimization

from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline
from pyspark.sql import Row
from pyspark.sql.functions import col, count as spark_count, avg, sum as spark_sum

# Test records
batch_records = [
    """Patient: Emily Chen, Medicare: 2234 56789 0, DOB: 15/03/1985
    Diagnosis: Type 2 diabetes mellitus, prescribed Metformin 1000mg BD
    Dr. Sarah Mitchell, St Vincent's Hospital, Provider: 123456X""",
    
    """Patient: Michael Thompson, Medicare: 3345 67890 1, DOB: 22/08/1970
    Chief Complaint: Hypertension, currently on Perindopril 5mg daily
    Contact: 0412 345 678, Seen by Dr. James Wong, Royal Melbourne Hospital""",
    
    """Patient: Sarah Williams, Medicare: 4456 78901 2, DOB: 10/11/1992
    Treatment: Atorvastatin 40mg for hyperlipidemia
    Follow-up at Alfred Hospital, ABN: 12 345 678 901""",
    
    """Patient: Robert Lee, Medicare: 5567 89012 3, DOB: 05/02/1988
    Medication: Aspirin 100mg daily, diagnosed with diabetic retinopathy
    Dr. Lisa Chen, Provider: 234567Y, Sydney Hospital""",
    
    """Patient: Dr. Maria Garcia, Medicare: 6678 90123 4, DOB: 18/07/1965
    Condition: Uncontrolled diabetes, HbA1c 8.2%, increase Metformin to 1000mg TDS
    Royal Brisbane Hospital, Contact: 07 3636 8111"""
]

print("=" * 90)
print("AUSTRALIAN MEDICAL RECORDS - OPTIMIZED ACCURACY PIPELINE")
print("=" * 90)
print("Total records: {}".format(len(batch_records)))
print("")

# COMMAND ----------

# Custom patterns for Australian identifiers with enhanced phone detection
custom_patterns = {
    'MEDICARE_NUMBER': [r'\bMedicare\s*:?\s*(\d{4}\s*\d{5}\s*\d)'],
    'PROVIDER_NUMBER': [r'\bProvider\s*:?\s*([A-Z0-9]{6,8})'],
    'PHONE_AU': [
        r'\b(?:\+?61\s?)?0?[2-478]\s?\d{4}\s?\d{4}\b',
        r'\bContact\s*:?\s*(\d{2,4}\s?\d{3,4}\s?\d{3,4})\b',
        r'\b(?:phone|tel|mobile)\s*:?\s*(\d{2,4}[-\s]?\d{4}[-\s]?\d{4})\b'
    ],
}

# Optimized configuration with label-specific thresholds
config = RedactionConfig(
    country="au",
    mode="custom",
    use_gliner=True,
    use_openmed=False,
    use_spacy=True,
    use_bert=False,
    use_statistical=False,
    custom_patterns=custom_patterns,
    gliner_labels=[
        # Core entities
        "person", "drug", "medication", "pharmaceutical",
        # Medical specifics
        "medical_condition", "disease", "diagnosis", "symptom",
        "treatment", "procedure", "dosage",
        # Locations
        "organization", "location", "facility", "hospital",
        # Identifiers
        "date", "phone_number", "identifier", "medical_record"
    ],
    thresholds={
        'gliner_conf': 0.3,      # Lower from 0.5 for better recall
        'spacy_conf': 0.5,
    },
    label_thresholds={
        'MEDICATION': 0.3,       # Very low for drugs (prioritize recall)
        'DRUG': 0.3,
        'MEDICAL_CONDITION': 0.4,
        'DISEASE': 0.4,
        'PERSON': 0.7,           # High for names (prioritize precision)
        'PERSON_NAME': 0.7,
        'PHONE_NUMBER': 0.5,
    },
    masking_style="replace",
    filter_stopwords=False,
    min_entity_length=2,
    consensus_threshold=0.6,
    use_context_propagation=True,
)

pipeline = RedactionPipeline.from_config(config)

# Apply medical optimization
pipeline.optimize_for_medical()

print("Pipeline Configuration:")
print("  Country: {}".format(config.country))
print("  Mode: {}".format(config.mode))
print("  GLiNER Threshold: {}".format(config.thresholds.get('gliner_conf')))
print("  Masking Style: {}".format(config.masking_style))
print("  Medical Optimization: ENABLED")
print("")
print("Active Components: {}".format(len(pipeline.components)))
for i, comp in enumerate(pipeline.components):
    print("  {}. {}".format(i+1, comp.__class__.__name__))
print("")
print("Label-Specific Thresholds:")
for label, threshold in sorted(config.label_thresholds.items()):
    print("  {:<25}: {:.2f}".format(label, threshold))
print("")

# COMMAND ----------

# Test first record for verification
print("=" * 90)
print("VERIFICATION TEST - RECORD 1")
print("=" * 90)

test_text = batch_records[0]
print("\nOriginal:")
print(test_text)

scan_result = pipeline.scan(test_text)

print("\n" + "-" * 90)
print("DETECTIONS: {} total".format(scan_result['total_detections']))
print("-" * 90)
for det in scan_result['detections']:
    print("  [{:<20s}] '{}' (score: {:.3f})".format(det['label'], det['text'], det['score']))

print("\n" + "-" * 90)
print("Entity Breakdown:")
for entity_type, count_val in sorted(scan_result['entity_counts'].items()):
    print("  {:<20s}: {}".format(entity_type, count_val))
print("-" * 90)

# COMMAND ----------

# Batch scan
print("\n" + "=" * 90)
print("BATCH SCAN RESULTS")
print("=" * 90)

scan_results = pipeline.scan_batch(batch_records, parallel=False)

total_detections = sum(r['total_detections'] for r in scan_results)
avg_detections = total_detections / len(batch_records)

print("\nOverall Statistics:")
print("-" * 90)
print("  Total Records: {}".format(len(batch_records)))
print("  Total Entities Detected: {}".format(total_detections))
print("  Average Entities per Record: {:.1f}".format(avg_detections))
print("  Records with PII: {}/{}".format(
    sum(1 for r in scan_results if r['has_pii']), 
    len(batch_records)
))

# Entity type breakdown
entity_counts = {}
for result in scan_results:
    for entity_type, count_val in result['entity_counts'].items():
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + count_val

print("\nEntity Type Breakdown:")
print("-" * 90)
print("{:<25} {:>15}".format("Entity Type", "Count"))
print("-" * 90)
for entity_type in sorted(entity_counts.keys()):
    print("{:<25} {:>15}".format(entity_type, entity_counts[entity_type]))
print("-" * 90)

# COMMAND ----------

# Batch redaction
print("\n" + "=" * 90)
print("BATCH REDACTION RESULTS")
print("=" * 90)

redaction_results = pipeline.redact_batch(batch_records, parallel=False)

for i in range(len(batch_records)):
    print("\n" + "=" * 90)
    print("RECORD {}".format(i + 1))
    print("=" * 90)
    print("\nOriginal:")
    print(batch_records[i])
    print("\n" + "-" * 90)
    print("Redacted: {} entities masked".format(len(redaction_results[i]['spans'])))
    print("-" * 90)
    print(redaction_results[i]['text'])
    
    if scan_results[i]['detections']:
        print("\nDetected Entities:")
        for det in scan_results[i]['detections']:
            print("  [{:<20}] '{}' (score: {:.3f})".format(
                det['label'], det['text'], det['score']
            ))

# COMMAND ----------

# Create Spark DataFrame for batch summary
batch_data = []
for i, text in enumerate(batch_records):
    result = scan_results[i]
    batch_data.append(Row(
        record_id=i + 1,
        original_text=text[:100] + "...",
        total_detections=result['total_detections'],
        has_pii=result['has_pii'],
        person_count=result['entity_counts'].get('PERSON', 0) + result['entity_counts'].get('PERSON_NAME', 0),
        medication_count=result['entity_counts'].get('MEDICATION', 0) + result['entity_counts'].get('DRUG', 0),
        identifier_count=result['entity_counts'].get('MEDICARE_NUMBER', 0) + result['entity_counts'].get('PROVIDER_NUMBER', 0)
    ))

df_batch = spark.createDataFrame(batch_data)

print("\n" + "=" * 90)
print("SPARK DATAFRAME - BATCH SUMMARY")
print("=" * 90)
display(df_batch)

# COMMAND ----------

# Create entity details DataFrame
entity_details = []
for i, text in enumerate(batch_records):
    for det in scan_results[i]['detections']:
        entity_details.append(Row(
            record_id=i + 1,
            entity_type=det['label'],
            entity_text=det['text'],
            confidence=float(det['score']),
            start_pos=det['start'],
            end_pos=det['end']
        ))

df_entities = spark.createDataFrame(entity_details)

print("ENTITY DETAILS - ALL RECORDS:")
display(df_entities.orderBy("record_id", "entity_type", col("confidence").desc()))

# COMMAND ----------

# Statistical Analysis
print("\n" + "=" * 90)
print("STATISTICAL ANALYSIS")
print("=" * 90)

df_stats = df_batch.agg(
    avg("total_detections").alias("avg_detections"),
    spark_sum("total_detections").alias("total_detections"),
    avg("person_count").alias("avg_persons"),
    avg("medication_count").alias("avg_medications"),
    avg("identifier_count").alias("avg_identifiers")
)

print("\nAggregate Statistics:")
display(df_stats)

# Collect stats for printing
stats_row = df_stats.collect()[0]
print("\nStatistics Summary:")
print("  Average Detections per Record: {:.2f}".format(stats_row['avg_detections']))
print("  Total Detections: {}".format(stats_row['total_detections']))
print("  Average Persons per Record: {:.2f}".format(stats_row['avg_persons']))
print("  Average Medications per Record: {:.2f}".format(stats_row['avg_medications']))
print("  Average Identifiers per Record: {:.2f}".format(stats_row['avg_identifiers']))

df_entity_dist = df_entities.groupBy("entity_type").agg(
    spark_count("*").alias("count"),
    avg("confidence").alias("avg_confidence")
).orderBy(col("count").desc())

print("\nEntity Type Distribution:")
display(df_entity_dist)

# COMMAND ----------

# Accuracy Metrics
print("\n" + "=" * 90)
print("ACCURACY METRICS")
print("=" * 90)

# Normalize labels for consistency
label_mapping = {
    'DRUG': 'MEDICATION',
    'MEDICATION': 'MEDICATION',
    'PHONE_AU': 'PHONE_NUMBER',
    'MEDICARE_NUMBER': 'MEDICARE',
    'PERSON_NAME': 'PERSON',
    'DATE': 'DATE',
    'DOB_AU': 'DATE'
}

normalized_counts = {}
for entity_type, count_val in entity_counts.items():
    normalized = label_mapping.get(entity_type, entity_type)
    normalized_counts[normalized] = normalized_counts.get(normalized, 0) + count_val

print("\nNormalized Entity Types:")
print("-" * 50)
for entity_type in sorted(normalized_counts.keys()):
    print("  {:<25}: {}".format(entity_type, normalized_counts[entity_type]))

# Expected counts for Australian medical records
expected_entities = {
    'PERSON': 8,           # 5 patients + 3 doctors
    'MEDICATION': 5,       # Metformin(2x), Perindopril, Atorvastatin, Aspirin
    'MEDICAL_CONDITION': 3, # diabetes, hypertension, retinopathy
    'MEDICARE': 5,         # 5 Medicare numbers
    'PHONE_NUMBER': 2,     # 2 phone contacts
    'DATE': 5              # 5 dates of birth
}

print("\nAccuracy Metrics:")
print("-" * 50)
print("{:<25} {:>10} {:>10} {:>10}".format("Entity Type", "Expected", "Found", "Recall %"))
print("-" * 50)

total_expected = 0
total_found = 0

for entity_type, expected_count in expected_entities.items():
    found_count = normalized_counts.get(entity_type, 0)
    recall = min(found_count / expected_count * 100, 100.0) if expected_count > 0 else 0
    total_expected += expected_count
    total_found += min(found_count, expected_count)
    print("{:<25} {:>10} {:>10} {:>9.1f}%".format(
        entity_type, expected_count, found_count, recall
    ))

overall_recall = (total_found / total_expected * 100) if total_expected > 0 else 0
print("-" * 50)
print("{:<25} {:>10} {:>10} {:>9.1f}%".format(
    "OVERALL", total_expected, total_found, overall_recall
))

# Confidence score analysis
all_confidences = [det['confidence'] for det in entity_details]
if all_confidences:
    avg_conf = sum(all_confidences) / len(all_confidences)
    min_conf = min(all_confidences)
    max_conf = max(all_confidences)
    
    print("\nConfidence Score Distribution:")
    print("-" * 50)
    print("  Average: {:.3f}".format(avg_conf))
    print("  Minimum: {:.3f}".format(min_conf))
    print("  Maximum: {:.3f}".format(max_conf))
else:
    avg_conf = 0

# COMMAND ----------

# Final Summary Report
print("\n" + "=" * 90)
print("FINAL SUMMARY REPORT")
print("=" * 90)

print("\nDataset Statistics:")
print("  Total Records: {}".format(len(batch_records)))
print("  Total Entities Detected: {}".format(total_detections))
print("  Average Entities per Record: {:.1f}".format(avg_detections))
print("  Records with PII/PHI: {}/{}".format(
    sum(1 for r in scan_results if r['has_pii']),
    len(batch_records)
))

print("\nDetection Performance:")
print("  Overall Recall: {:.1f}%".format(overall_recall))
print("  Average Confidence: {:.3f}".format(avg_conf))

print("\nTop Entity Types Detected:")
sorted_types = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:5]
for entity_type, count_val in sorted_types:
    print("  {:<25}: {}".format(entity_type, count_val))

print("\nPipeline Configuration:")
print("  Country: {}".format(config.country))
print("  Mode: {}".format(config.mode))
print("  Active Detectors: {}".format(len(pipeline.components)))
print("  GLiNER Labels: {}".format(len(config.gliner_labels)))
print("  Confidence Threshold: {}".format(config.thresholds.get('gliner_conf', 'N/A')))
print("  Medical Optimization: ENABLED")

print("\nKey Findings:")
medications_found = normalized_counts.get('MEDICATION', 0)
print("  Medications Detected: {}/5 ({:.0f}%)".format(
    medications_found, 
    (medications_found / 5 * 100) if medications_found > 0 else 0
))

persons_found = normalized_counts.get('PERSON', 0)
print("  Persons Detected: {}/8 ({:.0f}%)".format(
    persons_found,
    (persons_found / 8 * 100) if persons_found > 0 else 0
))

medicare_found = normalized_counts.get('MEDICARE', 0)
print("  Medicare Numbers: {}/5 ({:.0f}%)".format(
    medicare_found,
    (medicare_found / 5 * 100) if medicare_found > 0 else 0
))

print("\nOptimization Features Applied:")
print("  - Label-specific confidence thresholds")
print("  - Medical domain label priority in consensus")
print("  - Enhanced person name false positive filtering")
print("  - Pattern-based medical entity protection")
print("  - Lower thresholds for medications (0.3)")
print("  - Higher thresholds for person names (0.7)")
print("  - Enhanced phone number detection patterns")

print("\n" + "=" * 90)
print("END OF ANALYSIS")
print("=" * 90)
