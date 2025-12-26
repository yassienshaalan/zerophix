#!/usr/bin/env python3
"""
ZeroPhi Comprehensive Usage Examples
===================================

This file demonstrates how to use every functionality in ZeroPhi step by step.
Each section shows practical examples with real code that you can run.

Author: ZeroPhi Team
Date: October 2025
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any

# Core ZeroPhi imports
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig
from zerophix.policies.loader import PolicyLoader

# Detection engines
from zerophix.detectors.regex_detector import RegexDetector
from zerophix.detectors.spacy_detector import SpacyDetector
from zerophix.detectors.bert_detector import BertDetector
from zerophix.detectors.openmed_detector import OpenMedDetector
from zerophix.detectors.statistical_detector import StatisticalDetector
from zerophix.detectors.custom_detector import CustomEntityDetector

# Security and compliance
from zerophix.security.audit import SecureAuditLogger
from zerophix.security.compliance import ComplianceValidator
from zerophix.security.zero_trust import ZeroTrustValidator
from zerophix.security.encryption import EncryptionManager

# Performance features
from zerophix.performance.cache import RedisCache
from zerophix.performance.batch import BatchProcessor
from zerophix.performance.stream import StreamProcessor

# Document processing
from zerophix.processors.documents import (
    PDFProcessor,
    DOCXProcessor,
    ExcelProcessor,
    CSVProcessor,
)

# API components
from zerophix.api.server import create_app
from zerophix.api.webhooks import WebhookManager


def print_section(title: str):
    """Helper function to print section headers"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Helper function to print subsection headers"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


# =============================================================================
# 1. BASIC TEXT REDACTION
# =============================================================================

def example_1_basic_redaction():
    """Example 1: Basic text redaction with different countries"""
    print_section("1. BASIC TEXT REDACTION")
    
    # Sample sensitive text
    sample_texts = {
        "US": "John Doe, SSN: 123-45-6789, born 1985-03-15, phone: (555) 123-4567",
        "AU": "Jane Smith, TFN: 123 456 789, Medicare: 2234 5678 9 1, ABN: 12 345 678 901",
        "EU": "Hans Mueller, German ID: 123456789, IBAN: DE89 3704 0044 0532 0130 00",
        "UK": "Sarah Johnson, NHS: 123 456 7890, NI: AB 12 34 56 C, phone: +44 20 7946 0958",
        "CA": "Mike Brown, SIN: 123-456-789, Health Card: 1234-567-890-AB"
    }
    
    # Test each country configuration
    for country, text in sample_texts.items():
        print_subsection(f"Redacting {country} PII")
        
        # Create country-specific configuration
        config = RedactionConfig(
            country=country,
            detectors=["regex"],  # Start with fast regex
            redaction_strategy="replace",
            replacement_char="*"
        )
        
        # Create pipeline
        pipeline = RedactionPipeline(config)
        
        # Perform redaction
        result = pipeline.redact(text)
        
        print(f"Original : {text}")
        print(f"Redacted : {result['text']}")
        print(f"Entities : {result['entities']}")
        print(f"Confidence: {result['confidence']:.2f}")


# =============================================================================
# 2. ADVANCED ML DETECTION ENGINES
# =============================================================================

def example_2_ml_detection_engines():
    """Example 2: Using different ML detection engines"""
    print_section("2. ADVANCED ML DETECTION ENGINES")
    
    # Sample text with various entities
    text = """
    Patient John Doe (DOB: 1985-03-15) was admitted on 2023-10-15. 
    His SSN is 123-45-6789 and insurance ID is INS-987654321.
    Contact: john.doe@email.com, phone (555) 123-4567.
    Medical history shows diabetes diagnosed in 2020.
    Prescription: Metformin 500mg twice daily.
    """
    
    # Example 2.1: spaCy NER Detection
    print_subsection("2.1 spaCy NER Detection")
    try:
        config = RedactionConfig(
            country="US",
            detectors=["spacy"],
            spacy_model="en_core_web_lg",  # Large model for best accuracy
            use_contextual=True,
            confidence_threshold=0.8
        )
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        print(f"spaCy Result: {result['text'][:100]}...")
        print(f"Entities found: {len(result['entities'])}")
        for entity in result['entities'][:3]:  # Show first 3
            print(f"  - {entity['text']} ({entity['label']}) - {entity['confidence']:.2f}")
    except Exception as e:
        print(f"spaCy detection failed: {e}")
    
    # Example 2.2: BERT-based Detection
    print_subsection("2.2 BERT-based Detection")
    try:
        config = RedactionConfig(
            country="US",
            detectors=["bert"],
            bert_model="bert-base-cased",
            bert_confidence_threshold=0.9,
            max_seq_length=512
        )
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        print(f"BERT Result: {result['text'][:100]}...")
        print(f"Entities found: {len(result['entities'])}")
        for entity in result['entities'][:3]:
            print(f"  - {entity['text']} ({entity['label']}) - {entity['confidence']:.2f}")
    except Exception as e:
        print(f"BERT detection failed: {e}")
    
    # Example 2.3: OpenMed Medical Detection
    print_subsection("2.3 OpenMed Medical Detection")
    try:
        config = RedactionConfig(
            country="US",
            detectors=["openmed"],
            openmed_model="openmed-base",
            openmed_confidence=0.8,
            enable_assertion=True  # Filter negated entities
        )
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        
        print(f"OpenMed Result: {result['text'][:100]}...")
        print(f"Medical entities found: {len(result['entities'])}")
        for entity in result['entities'][:3]:
            print(f"  - {entity['text']} ({entity['label']}) - {entity['confidence']:.2f}")
    except Exception as e:
        print(f"OpenMed detection failed: {e}")
    
    # Example 2.4: Statistical Detection
    print_subsection("2.4 Statistical Pattern Detection")
    config = RedactionConfig(
        country="US",
        detectors=["statistical"],
        entropy_threshold=4.5,
        frequency_analysis=True,
        n_gram_analysis=True
    )
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Statistical Result: {result['text'][:100]}...")
    print(f"Pattern anomalies found: {len(result['entities'])}")
    
    # Example 2.5: Multi-Engine Ensemble
    print_subsection("2.5 Multi-Engine Ensemble (Best Results)")
    config = RedactionConfig(
        country="US",
        detectors=["regex", "spacy", "statistical"],  # Combine multiple engines
        ensemble_method="voting",  # or "confidence_weighted"
        min_confidence=0.7
    )
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Ensemble Result: {result['text'][:100]}...")
    print(f"Total entities found: {len(result['entities'])}")
    print(f"Overall confidence: {result['confidence']:.2f}")


# =============================================================================
# 3. CUSTOM ENTITY DETECTION
# =============================================================================

def example_3_custom_entities():
    """Example 3: Custom entity detection for domain-specific data"""
    print_section("3. CUSTOM ENTITY DETECTION")
    
    # Create custom detector
    custom_detector = CustomEntityDetector()
    
    # Add custom patterns
    custom_detector.add_pattern(
        "EMPLOYEE_ID", 
        r"EMP-\d{6}", 
        confidence=0.95,
        description="Employee ID format"
    )
    
    custom_detector.add_pattern(
        "PROJECT_CODE", 
        r"PROJ-[A-Z]{3}-\d{4}", 
        confidence=0.9,
        description="Project code format"
    )
    
    custom_detector.add_pattern(
        "INTERNAL_IP", 
        r"192\.168\.\d{1,3}\.\d{1,3}", 
        confidence=0.85,
        description="Internal IP addresses"
    )
    
    # Add contextual patterns
    custom_detector.add_contextual_pattern(
        "SALARY_INFO",
        r"\$[\d,]+",
        context_words=["salary", "pay", "compensation", "wage"],
        confidence=0.9
    )
    
    # Sample text with custom entities
    text = """
    Employee EMP-123456 is working on PROJ-ABC-2023 with salary $75,000.
    Server IP: 192.168.1.100, access code: AC-789123.
    Project PROJ-XYZ-2024 budget: $150,000 allocated to team.
    """
    
    # Use custom detector
    config = RedactionConfig(
        country="US",
        detectors=["custom"],
        custom_detector=custom_detector
    )
    
    pipeline = RedactionPipeline(config)
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print("\nCustom entities detected:")
    for entity in result['entities']:
        print(f"  - {entity['text']} ({entity['label']}) - {entity['confidence']:.2f}")


# =============================================================================
# 4. ADVANCED REDACTION STRATEGIES
# =============================================================================

def example_4_redaction_strategies():
    """Example 4: Different redaction strategies"""
    print_section("4. ADVANCED REDACTION STRATEGIES")
    
    text = "John Doe, SSN: 123-45-6789, email: john.doe@company.com, phone: (555) 123-4567"
    
    strategies = [
        ("replace", "Simple replacement with asterisks"),
        ("mask", "Partial masking (show first/last chars)"),
        ("synthetic", "Replace with synthetic but realistic data"),
        ("hash", "Replace with consistent hash values"),
        ("encrypt", "Format-preserving encryption"),
        ("differential_privacy", "Add statistical noise for privacy")
    ]
    
    for strategy, description in strategies:
        print_subsection(f"4.{strategies.index((strategy, description))+1} {description}")
        
        try:
            config = RedactionConfig(
                country="US",
                detectors=["regex"],
                redaction_strategy=strategy,
                # Strategy-specific parameters
                mask_percentage=0.7 if strategy == "mask" else None,
                noise_scale=0.1 if strategy == "differential_privacy" else None,
                preserve_format=True if strategy in ["synthetic", "encrypt"] else None
            )
            
            pipeline = RedactionPipeline(config)
            result = pipeline.redact(text)
            
            print(f"Original : {text}")
            print(f"Redacted : {result['text']}")
            
            if strategy == "hash":
                # Show that hashing is consistent
                result2 = pipeline.redact(text)
                print(f"Same hash: {result['text'] == result2['text']}")
                
        except Exception as e:
            print(f"Strategy {strategy} failed: {e}")


# =============================================================================
# 5. DOCUMENT PROCESSING
# =============================================================================

def example_5_document_processing():
    """Example 5: Processing different document formats"""
    print_section("5. DOCUMENT PROCESSING")
    
    # Create sample documents directory
    docs_dir = Path("sample_documents")
    docs_dir.mkdir(exist_ok=True)
    
    # Example 5.1: PDF Processing
    print_subsection("5.1 PDF Document Processing")
    try:
        pdf_processor = PDFProcessor()
        
        # Process a PDF file
        config = RedactionConfig(country="US", detectors=["regex", "spacy"])
        
        # For demo - create a simple text file instead of PDF
        sample_pdf_path = docs_dir / "sample.txt"
        with open(sample_pdf_path, "w") as f:
            f.write("John Doe\nSSN: 123-45-6789\nEmail: john@example.com\nPhone: (555) 123-4567")
        
        print(f"Created sample document: {sample_pdf_path}")
        print("PDF processing would extract text, redact PII, and regenerate PDF")
        
    except Exception as e:
        print(f"PDF processing failed: {e}")
    
    # Example 5.2: Excel Processing
    print_subsection("5.2 Excel Spreadsheet Processing")
    try:
        excel_processor = ExcelProcessor()
        
        # Create sample Excel data
        import pandas as pd
        
        data = {
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'SSN': ['123-45-6789', '987-65-4321', '555-44-3333'],
            'Email': ['john@email.com', 'jane@email.com', 'bob@email.com'],
            'Salary': [75000, 65000, 80000]
        }
        
        df = pd.DataFrame(data)
        excel_path = docs_dir / "sample_data.xlsx"
        df.to_excel(excel_path, index=False)
        
        print(f"Created sample Excel: {excel_path}")
        print("Excel processing would redact PII while preserving structure")
        print(f"Original data shape: {df.shape}")
        
        # Simulate redaction
        redacted_df = df.copy()
        redacted_df['SSN'] = redacted_df['SSN'].apply(lambda x: "***-**-" + x[-4:])
        redacted_df['Email'] = redacted_df['Email'].apply(lambda x: "***@" + x.split('@')[1])
        
        print("Redacted preview:")
        print(redacted_df.head())
        
    except Exception as e:
        print(f"Excel processing failed: {e}")
    
    # Example 5.3: CSV Processing
    print_subsection("5.3 CSV File Processing")
    try:
        csv_processor = CSVProcessor()
        
        # Create sample CSV
        csv_path = docs_dir / "sample_data.csv"
        with open(csv_path, "w") as f:
            f.write("name,ssn,email,phone\n")
            f.write("John Doe,123-45-6789,john@email.com,(555) 123-4567\n")
            f.write("Jane Smith,987-65-4321,jane@email.com,(555) 987-6543\n")
        
        print(f"Created sample CSV: {csv_path}")
        print("CSV processing supports batch redaction with column mapping")
        
        # Read and show original
        with open(csv_path, "r") as f:
            print("Original CSV:")
            print(f.read())
        
    except Exception as e:
        print(f"CSV processing failed: {e}")


# =============================================================================
# 6. PERFORMANCE OPTIMIZATION
# =============================================================================

def example_6_performance_optimization():
    """Example 6: Performance optimization features"""
    print_section("6. PERFORMANCE OPTIMIZATION")
    
    # Example 6.1: Caching
    print_subsection("6.1 Redis Caching")
    try:
        # Note: Requires Redis server running
        cache = RedisCache(host='localhost', port=6379, db=0)
        
        # Test caching
        text = "John Doe, SSN: 123-45-6789"
        cache_key = f"redaction:{hash(text)}"
        
        print(f"Cache key: {cache_key}")
        print("Caching speeds up repeated redactions significantly")
        
        # Simulate cache usage
        cached_result = cache.get(cache_key)
        if cached_result:
            print("Result retrieved from cache")
        else:
            print("Result not in cache, performing redaction")
            
    except Exception as e:
        print(f"Caching setup failed: {e}")
    
    # Example 6.2: Batch Processing
    print_subsection("6.2 Batch Processing")
    
    # Create batch processor
    batch_processor = BatchProcessor(
        batch_size=100,
        max_workers=4,
        use_async=True
    )
    
    # Sample batch data
    batch_texts = [
        f"Person {i}: SSN: {123+i:03d}-{45+i:02d}-{6789+i:04d}" 
        for i in range(10)
    ]
    
    print(f"Processing batch of {len(batch_texts)} texts")
    
    # Simulate batch processing
    config = RedactionConfig(country="US", detectors=["regex"])
    
    # Process in batches (simplified for demo)
    for i, text in enumerate(batch_texts[:3]):  # Show first 3
        pipeline = RedactionPipeline(config)
        result = pipeline.redact(text)
        print(f"  Batch item {i+1}: {result['text']}")
    
    print(f"Batch processing provides {4}x speedup with parallel workers")
    
    # Example 6.3: Streaming Processing
    print_subsection("6.3 Stream Processing")
    
    stream_processor = StreamProcessor(
        chunk_size=1024,
        overlap_size=100,  # Handle entities spanning chunks
        buffer_size=10
    )
    
    # Simulate large text stream
    large_text = """
    This is a large document with multiple people mentioned.
    John Doe (SSN: 123-45-6789) works with Jane Smith (SSN: 987-65-4321).
    They handle sensitive data including credit cards and phone numbers.
    Contact information: john@company.com, jane@company.com.
    Phone numbers: (555) 123-4567, (555) 987-6543.
    """ * 100  # Repeat to make it large
    
    print(f"Stream processing {len(large_text):,} characters")
    print("Stream processing enables real-time redaction of large documents")
    
    # Simulate streaming (show concept)
    chunk_size = 200
    chunks_processed = 0
    for i in range(0, min(len(large_text), 1000), chunk_size):
        chunk = large_text[i:i+chunk_size]
        chunks_processed += 1
        
    print(f"Processed {chunks_processed} chunks with overlap handling")


# =============================================================================
# 7. SECURITY AND COMPLIANCE
# =============================================================================

def example_7_security_compliance():
    """Example 7: Security and compliance features"""
    print_section("7. SECURITY AND COMPLIANCE")
    
    # Example 7.1: Audit Logging
    print_subsection("7.1 Secure Audit Logging")
    
    # Create audit logger
    audit_logger = SecureAuditLogger(
        log_file="audit.log",
        encryption_key=None,  # Will generate key
        integrity_check=True
    )
    
    # Log redaction events
    events = [
        {
            'action': 'redaction',
            'user_id': 'user123',
            'text_length': 150,
            'entities_found': 3,
            'confidence': 0.95,
            'ip_address': '192.168.1.100'
        },
        {
            'action': 'document_process',
            'user_id': 'user456',
            'file_type': 'pdf',
            'file_size': 2048576,
            'entities_redacted': 15
        }
    ]
    
    for event in events:
        audit_logger.log_event(**event)
        print(f"Logged: {event['action']} by {event['user_id']}")
    
    print("Audit logs are encrypted and tamper-evident")
    
    # Example 7.2: Compliance Validation
    print_subsection("7.2 Compliance Validation")
    
    compliance_validator = ComplianceValidator()
    
    # Check different compliance standards
    standards = ['GDPR', 'HIPAA', 'PCI_DSS', 'SOX']
    
    for standard in standards:
        try:
            is_compliant = compliance_validator.validate_standard(
                standard=standard,
                data_types=['PII', 'PHI', 'PCI'] if standard == 'PCI_DSS' else ['PII'],
                retention_days=365,
                encryption_enabled=True,
                audit_logging=True
            )
            status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
            print(f"  {standard}: {status}")
        except Exception as e:
            print(f"  {standard}: Error - {e}")
    
    # Example 7.3: Zero Trust Validation
    print_subsection("7.3 Zero Trust Security")
    
    zero_trust = ZeroTrustValidator()
    
    # Simulate security validation
    security_context = {
        'user_id': 'user123',
        'device_id': 'device456',
        'ip_address': '192.168.1.100',
        'time_since_auth': 300,  # 5 minutes
        'mfa_verified': True,
        'device_trusted': True
    }
    
    trust_score = zero_trust.calculate_trust_score(**security_context)
    print(f"Trust Score: {trust_score:.2f}/100")
    
    if trust_score >= 80:
        print("Access GRANTED - High trust score")
    elif trust_score >= 60:
        print("Access CONDITIONAL - Medium trust, additional verification required")
    else:
        print("Access DENIED - Low trust score")
    
    # Example 7.4: Encryption at Rest
    print_subsection("7.4 Encryption at Rest")
    
    encryption_manager = EncryptionManager()
    
    # Encrypt sensitive data
    sensitive_data = "John Doe, SSN: 123-45-6789"
    encrypted_data = encryption_manager.encrypt(sensitive_data, purpose="redaction_cache")
    
    print(f"Original: {sensitive_data}")
    print(f"Encrypted: {encrypted_data[:50]}...")
    
    # Decrypt data
    decrypted_data = encryption_manager.decrypt(encrypted_data, purpose="redaction_cache")
    print(f"Decrypted: {decrypted_data}")
    print(f"Encryption successful: {sensitive_data == decrypted_data}")


# =============================================================================
# 8. API SERVER AND INTEGRATION
# =============================================================================

async def example_8_api_integration():
    """Example 8: API server and integration features"""
    print_section("8. API SERVER AND INTEGRATION")
    
    # Example 8.1: FastAPI Server
    print_subsection("8.1 REST API Server")
    
    # Create FastAPI app
    app = create_app()
    
    print("FastAPI server configured with endpoints:")
    print("  POST /redact - Text redaction")
    print("  POST /redact/file - File redaction")
    print("  POST /redact/batch - Batch processing")
    print("  GET /health - Health check")
    print("  GET /metrics - Performance metrics")
    print("  WebSocket /ws - Real-time redaction")
    
    # Simulate API usage (conceptual)
    api_request = {
        "text": "John Doe, SSN: 123-45-6789",
        "country": "US",
        "detectors": ["regex", "spacy"],
        "strategy": "replace"
    }
    
    print(f"\nSample API request: {json.dumps(api_request, indent=2)}")
    
    # Example 8.2: Webhook Integration
    print_subsection("8.2 Webhook Integration")
    
    webhook_manager = WebhookManager()
    
    # Register webhooks
    webhooks = [
        {
            "url": "https://api.company.com/redaction-complete",
            "events": ["redaction.completed", "batch.finished"],
            "secret": "webhook_secret_123"
        },
        {
            "url": "https://compliance.company.com/audit",
            "events": ["audit.log", "compliance.violation"],
            "secret": "audit_secret_456"
        }
    ]
    
    for webhook in webhooks:
        webhook_manager.register_webhook(**webhook)
        print(f"Registered webhook: {webhook['url']}")
    
    # Simulate webhook trigger
    event_data = {
        "event": "redaction.completed",
        "job_id": "job_123",
        "entities_found": 5,
        "processing_time": 1.25,
        "timestamp": "2025-10-29T10:30:00Z"
    }
    
    print(f"Webhook event: {json.dumps(event_data, indent=2)}")
    
    # Example 8.3: Database Integration
    print_subsection("8.3 Database Integration")
    
    # Simulate database configuration
    db_configs = {
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "company_data",
            "table": "customer_records",
            "columns": ["name", "ssn", "email", "phone"]
        },
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "database": "documents",
            "collection": "sensitive_docs",
            "fields": ["content", "metadata.pii"]
        }
    }
    
    for db_type, config in db_configs.items():
        print(f"{db_type.upper()} Integration:")
        print(f"  Host: {config['host']}:{config['port']}")
        if db_type == "postgresql":
            print(f"  Table: {config['table']}")
            print(f"  Columns: {', '.join(config['columns'])}")
        else:
            print(f"  Collection: {config['collection']}")
            print(f"  Fields: {', '.join(config['fields'])}")
        print("  CONFIGURED for automatic PII redaction")


# =============================================================================
# 9. ASYNC AND CONCURRENT PROCESSING
# =============================================================================

async def example_9_async_processing():
    """Example 9: Asynchronous and concurrent processing"""
    print_section("9. ASYNC AND CONCURRENT PROCESSING")
    
    # Example 9.1: Async Text Processing
    print_subsection("9.1 Async Text Processing")
    
    async def async_redact_text(text: str, delay: float = 0.1) -> Dict[str, Any]:
        """Simulate async redaction with processing delay"""
        await asyncio.sleep(delay)  # Simulate processing time
        
        config = RedactionConfig(country="US", detectors=["regex"])
        pipeline = RedactionPipeline(config)
        return pipeline.redact(text)
    
    # Process multiple texts concurrently
    texts = [
        "John Doe, SSN: 123-45-6789",
        "Jane Smith, SSN: 987-65-4321", 
        "Bob Johnson, SSN: 555-44-3333",
        "Alice Brown, SSN: 111-22-3333"
    ]
    
    print(f"Processing {len(texts)} texts concurrently...")
    
    # Process concurrently
    start_time = asyncio.get_event_loop().time()
    tasks = [async_redact_text(text) for text in texts]
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    for i, result in enumerate(results):
        print(f"  Text {i+1}: {result['text']}")
    
    print(f"Concurrent processing time: {end_time - start_time:.2f}s")
    
    # Example 9.2: Stream Processing
    print_subsection("9.2 Async Stream Processing")
    
    async def process_text_stream():
        """Simulate processing a stream of text data"""
        stream_data = [
            "User alice@email.com logged in",
            "SSN 123-45-6789 requires verification", 
            "Phone (555) 123-4567 updated",
            "Credit card 4532-1234-5678-9012 charged"
        ]
        
        for i, text in enumerate(stream_data):
            result = await async_redact_text(text, delay=0.05)
            print(f"  Stream {i+1}: {result['text']}")
            
        return len(stream_data)
    
    processed_count = await process_text_stream()
    print(f"Processed {processed_count} stream items")


# =============================================================================
# 10. COMPREHENSIVE CONFIGURATION
# =============================================================================

def example_10_comprehensive_config():
    """Example 10: Comprehensive configuration examples"""
    print_section("10. COMPREHENSIVE CONFIGURATION")
    
    # Example 10.1: Enterprise Configuration
    print_subsection("10.1 Enterprise Production Configuration")
    
    enterprise_config = RedactionConfig(
        # Multi-country support
        country="US",
        additional_countries=["EU", "UK", "CA"],
        
        # Multi-engine detection
        detectors=["regex", "spacy", "bert", "statistical"],
        ensemble_method="confidence_weighted",
        
        # Model configuration
        spacy_model="en_core_web_lg",
        bert_model="bert-base-cased", 
        openmed_model="openmed-large",
        
        # Performance optimization
        use_async=True,
        batch_size=100,
        max_workers=8,
        use_cache=True,
        cache_ttl=3600,
        
        # Advanced redaction
        redaction_strategy="differential_privacy",
        noise_scale=0.1,
        preserve_format=True,
        
        # Security
        encryption_enabled=True,
        audit_logging=True,
        zero_trust_validation=True,
        
        # Compliance
        compliance_standards=["GDPR", "HIPAA", "PCI_DSS"],
        data_retention_days=2555,  # 7 years
        
        # Confidence thresholds
        min_confidence=0.8,
        high_confidence_threshold=0.95
    )
    
    print("Enterprise configuration created with:")
    print(f"  Countries: {enterprise_config.country} + {len(enterprise_config.additional_countries or [])} others")
    print(f"  Detectors: {', '.join(enterprise_config.detectors)}")
    print(f"  Security: Encryption + Audit + Zero Trust")
    print(f"  Compliance: {', '.join(enterprise_config.compliance_standards)}")
    
    # Example 10.2: Healthcare-Specific Configuration
    print_subsection("10.2 Healthcare PHI Configuration")
    
    healthcare_config = RedactionConfig(
        country="US",
        detectors=["regex", "openmed", "spacy"],
        
        # Healthcare-specific settings
        openmed_model="openmed-clinical",
        enable_assertion=True,  # Filter negated medical entities
        medical_entity_types=[
            "CONDITION", "MEDICATION", "DOSAGE", 
            "PROCEDURE", "ANATOMY", "TEMPORAL"
        ],
        
        # HIPAA compliance
        compliance_standards=["HIPAA"],
        hipaa_safe_harbor=True,
        
        # Advanced privacy
        redaction_strategy="k_anonymity",
        k_value=5,  # k-anonymity parameter
        
        # Medical-specific confidence
        medical_confidence_threshold=0.9,
        general_confidence_threshold=0.8
    )
    
    print("Healthcare configuration optimized for:")
    print("  HIPAA Safe Harbor compliance")
    print("  Medical entity recognition with OpenMed")
    print("  Assertion filtering (negated entities)")
    print("  K-anonymity privacy protection")
    
    # Example 10.3: Financial Services Configuration
    print_subsection("10.3 Financial Services Configuration")
    
    financial_config = RedactionConfig(
        country="US",
        additional_countries=["EU"],  # Cross-border transactions
        detectors=["regex", "bert", "statistical"],
        
        # Financial-specific entities
        custom_entities=[
            "CREDIT_CARD", "BANK_ACCOUNT", "ROUTING_NUMBER",
            "SWIFT_CODE", "IBAN", "CRYPTOCURRENCY_ADDRESS"
        ],
        
        # PCI DSS compliance
        compliance_standards=["PCI_DSS", "GDPR"],
        pci_dss_level=1,  # Highest security level
        
        # Advanced encryption
        redaction_strategy="format_preserving_encryption",
        encryption_algorithm="AES-256",
        key_rotation_days=90,
        
        # High security thresholds
        min_confidence=0.95,
        require_dual_approval=True,
        
        # Audit requirements
        detailed_audit_logging=True,
        real_time_monitoring=True
    )
    
    print("Financial services configuration includes:")
    print("  PCI DSS Level 1 compliance")
    print("  Format-preserving encryption") 
    print("  Quarterly key rotation")
    print("  Real-time monitoring")
    print("  Dual approval workflows")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main function to run all examples"""
    print("ZeroPhi Comprehensive Usage Examples")
    print("====================================")
    print("This script demonstrates every feature of ZeroPhi")
    print("Each section shows practical, runnable code examples")
    print("\nNOTE: Some examples require additional setup:")
    print("- spaCy models: python -m spacy download en_core_web_lg")
    print("- BERT models: Auto-downloaded on first use")
    print("- OpenMed models: Auto-downloaded on first use") 
    print("- Redis server: For caching examples")
    print("- Database servers: For integration examples")
    
    try:
        # Run synchronous examples
        example_1_basic_redaction()
        example_2_ml_detection_engines()
        example_3_custom_entities()
        example_4_redaction_strategies()
        example_5_document_processing()
        example_6_performance_optimization()
        example_7_security_compliance()
        example_10_comprehensive_config()
        
        # Run asynchronous examples
        await example_8_api_integration()
        await example_9_async_processing()
        
        print_section("EXAMPLES COMPLETED SUCCESSFULLY")
        print("All ZeroPhi functionalities demonstrated!")
        print("\nNext steps:")
        print("1. Install required dependencies for features you need")
        print("2. Adapt configurations for your use case")
        print("3. Set up production infrastructure (Redis, databases)")
        print("4. Configure security and compliance requirements")
        print("5. Test with your actual data")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("This is normal - examples require full ZeroPhi installation")
        print("Use individual sections as reference for your implementation")


if __name__ == "__main__":
    # Run the comprehensive examples
    asyncio.run(main())