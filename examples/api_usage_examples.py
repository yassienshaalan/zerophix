#!/usr/bin/env python3
"""
ZeroPhi API Usage Examples
==========================

Examples showing how to use ZeroPhi via REST API, Python SDK, and integrations.
Perfect for integration into existing applications and services.
"""

import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Any


# =============================================================================
# 1. REST API EXAMPLES (using requests)
# =============================================================================

def example_1_rest_api_basic():
    """Basic REST API usage with requests"""
    print("=" * 60)
    print("1. REST API - BASIC USAGE")
    print("=" * 60)
    
    # API endpoint (assuming server is running on localhost:8000)
    base_url = "http://localhost:8000"
    
    # Example 1.1: Simple text redaction
    print("1.1 Simple Text Redaction")
    print("-" * 30)
    
    payload = {
        "text": "Hi John Doe, your SSN 123-45-6789 has been verified.",
        "country": "US",
        "detectors": ["regex"],
        "strategy": "replace"
    }
    
    try:
        response = requests.post(f"{base_url}/redact", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"Original: {payload['text']}")
            print(f"Redacted: {result['text']}")
            print(f"Entities: {len(result['entities'])}")
        else:
            print(f"API Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Server not running. Start with: zerophi serve")
    
    print()
    
    # Example 1.2: Batch processing
    print("1.2 Batch Processing")
    print("-" * 30)
    
    batch_payload = {
        "texts": [
            "John Doe, SSN: 123-45-6789",
            "Jane Smith, phone: (555) 987-6543", 
            "Bob Wilson, email: bob@email.com"
        ],
        "country": "US",
        "detectors": ["regex", "spacy"]
    }
    
    try:
        response = requests.post(f"{base_url}/redact/batch", json=batch_payload)
        if response.status_code == 200:
            results = response.json()
            print(f"Processed {len(results['results'])} texts")
            for i, result in enumerate(results['results']):
                print(f"  {i+1}: {result['text']}")
        else:
            print(f"Batch API Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Server not running. Start with: zerophi serve")
    
    print()


def example_2_file_upload_api():
    """File upload via REST API"""
    print("=" * 60)
    print("2. REST API - FILE UPLOAD")
    print("=" * 60)
    
    # Create a sample file
    import tempfile
    import os
    
    sample_content = """
    CONFIDENTIAL EMPLOYEE RECORD
    
    Name: John Doe
    SSN: 123-45-6789
    Email: john.doe@company.com
    Phone: (555) 123-4567
    Address: 123 Main St, Anytown, ST 12345
    
    Performance Review: Excellent
    Salary: $75,000
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_content)
        temp_file = f.name
    
    try:
        base_url = "http://localhost:8000"
        
        # Upload file for redaction
        with open(temp_file, 'rb') as f:
            files = {'file': ('document.txt', f, 'text/plain')}
            data = {
                'country': 'US',
                'detectors': '["regex", "spacy"]',
                'strategy': 'replace'
            }
            
            response = requests.post(f"{base_url}/redact/file", files=files, data=data)
            
            if response.status_code == 200:
                # Save redacted file
                redacted_file = temp_file.replace('.txt', '_redacted.txt')
                with open(redacted_file, 'wb') as rf:
                    rf.write(response.content)
                
                print(f"Original file: {temp_file}")
                print(f"Redacted file: {redacted_file}")
                print("File redaction completed successfully")
                
                # Show redacted content
                with open(redacted_file, 'r') as rf:
                    redacted_content = rf.read()
                    print("\nRedacted content:")
                    print(redacted_content[:200] + "..." if len(redacted_content) > 200 else redacted_content)
            else:
                print(f"File upload error: {response.status_code}")
                
    except requests.exceptions.ConnectionError:
        print("Server not running. Start with: zerophi serve")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        redacted_file = temp_file.replace('.txt', '_redacted.txt')
        if os.path.exists(redacted_file):
            os.remove(redacted_file)


# =============================================================================
# 3. ASYNC API EXAMPLES (using aiohttp)
# =============================================================================

async def example_3_async_api():
    """Async API usage for better performance"""
    print("=" * 60)
    print("3. ASYNC API USAGE")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async def redact_text_async(session, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Async text redaction"""
        payload = {"text": text, **config}
        
        try:
            async with session.post(f"{base_url}/redact", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Status {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    # Process multiple texts concurrently
    texts = [
        "John Doe, SSN: 123-45-6789, email: john@email.com",
        "Jane Smith, phone: (555) 987-6543, DOB: 1990-05-15",
        "Bob Johnson, credit card: 4532-1234-5678-9012", 
        "Alice Brown, driver license: D12345678"
    ]
    
    config = {
        "country": "US",
        "detectors": ["regex"],
        "strategy": "replace"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Processing {len(texts)} texts concurrently...")
            
            # Create concurrent tasks
            tasks = [redact_text_async(session, text, config) for text in texts]
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks)
            
            # Display results
            for i, result in enumerate(results, 1):
                if 'error' in result:
                    print(f"Text {i}: Error - {result['error']}")
                else:
                    print(f"Text {i}: {result['text']}")
                    
    except Exception as e:
        print(f"Async processing failed: {e}")
        print("Make sure the server is running: zerophi serve")


# =============================================================================
# 4. WEBSOCKET REAL-TIME EXAMPLES
# =============================================================================

async def example_4_websocket_realtime():
    """Real-time redaction via WebSocket"""
    print("=" * 60)
    print("4. WEBSOCKET REAL-TIME REDACTION")
    print("=" * 60)
    
    try:
        import websockets
        
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Send configuration
            config_msg = {
                "type": "config",
                "country": "US",
                "detectors": ["regex"],
                "strategy": "replace"
            }
            
            await websocket.send(json.dumps(config_msg))
            response = await websocket.recv()
            print(f"Config response: {response}")
            
            # Send texts for real-time redaction
            texts = [
                "Real-time: John Doe, SSN: 123-45-6789",
                "Streaming: Jane Smith, phone: (555) 123-4567",
                "Live: Bob Wilson, email: bob@email.com"
            ]
            
            for text in texts:
                # Send text
                msg = {
                    "type": "redact", 
                    "text": text
                }
                
                await websocket.send(json.dumps(msg))
                
                # Receive result
                response = await websocket.recv()
                result = json.loads(response)
                
                print(f"Real-time: {text}")
                print(f"Redacted:  {result['text']}")
                print()
                
                # Small delay for demo
                await asyncio.sleep(0.5)
                
    except ImportError:
        print("WebSocket example requires: pip install websockets")
    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        print("Make sure the server is running: zerophi serve")


# =============================================================================
# 5. PYTHON SDK EXAMPLES
# =============================================================================

def example_5_python_sdk():
    """Direct Python SDK usage (no API server needed)"""
    print("=" * 60)
    print("5. PYTHON SDK - DIRECT USAGE")
    print("=" * 60)
    
    from zerophi.pipelines.redaction import RedactionPipeline
    from zerophi.config import RedactionConfig
    
    # Example 5.1: Simple SDK usage
    print("5.1 Simple SDK Usage")
    print("-" * 30)
    
    config = RedactionConfig(country="US", detectors=["regex"])
    pipeline = RedactionPipeline(config)
    
    text = "Contact John Doe at john.doe@email.com or (555) 123-4567"
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print(f"Entities: {len(result['entities'])}")
    print()
    
    # Example 5.2: Advanced SDK configuration
    print("5.2 Advanced SDK Configuration")
    print("-" * 30)
    
    advanced_config = RedactionConfig(
        country="US",
        detectors=["regex", "spacy"],  # Multiple detectors
        redaction_strategy="mask",      # Partial masking
        mask_percentage=0.7,           # Show 30% of characters
        confidence_threshold=0.8,      # High confidence only
        preserve_format=True           # Keep original format
    )
    
    pipeline = RedactionPipeline(advanced_config)
    
    text = "Patient John Doe (SSN: 123-45-6789) scheduled for 2023-10-15"
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Masked:   {result['text']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print()
    
    # Example 5.3: Custom entity handling
    print("5.3 Custom Entity Detection")
    print("-" * 30)
    
    from zerophi.detectors.custom_detector import CustomEntityDetector
    
    custom_detector = CustomEntityDetector()
    custom_detector.add_pattern("EMPLOYEE_ID", r"EMP-\d{6}", confidence=0.9)
    custom_detector.add_pattern("PROJECT_CODE", r"PROJ-[A-Z]{3}-\d{4}", confidence=0.9)
    
    custom_config = RedactionConfig(
        country="US",
        detectors=["regex", "custom"],
        custom_detector=custom_detector
    )
    
    pipeline = RedactionPipeline(custom_config)
    
    text = "Employee EMP-123456 is working on PROJ-ABC-2023 with John Doe"
    result = pipeline.redact(text)
    
    print(f"Original: {text}")
    print(f"Redacted: {result['text']}")
    print("Custom entities found:")
    for entity in result['entities']:
        if entity['label'] in ['EMPLOYEE_ID', 'PROJECT_CODE']:
            print(f"  - {entity['text']} ({entity['label']})")


# =============================================================================
# 6. INTEGRATION EXAMPLES
# =============================================================================

def example_6_integration_patterns():
    """Common integration patterns"""
    print("=" * 60)
    print("6. INTEGRATION PATTERNS")
    print("=" * 60)
    
    # Example 6.1: Database integration
    print("6.1 Database Integration Pattern")
    print("-" * 30)
    
    # Simulate database records
    db_records = [
        {"id": 1, "name": "John Doe", "ssn": "123-45-6789", "email": "john@email.com"},
        {"id": 2, "name": "Jane Smith", "ssn": "987-65-4321", "email": "jane@email.com"},
        {"id": 3, "name": "Bob Wilson", "ssn": "555-44-3333", "email": "bob@email.com"}
    ]
    
    from zerophi.pipelines.redaction import RedactionPipeline
    from zerophi.config import RedactionConfig
    
    config = RedactionConfig(country="US", detectors=["regex"])
    pipeline = RedactionPipeline(config)
    
    print("Original records:")
    for record in db_records:
        print(f"  {record}")
    
    print("\nRedacted records:")
    redacted_records = []
    for record in db_records:
        redacted_record = record.copy()
        
        # Redact sensitive fields
        if 'ssn' in record:
            ssn_result = pipeline.redact(record['ssn'])
            redacted_record['ssn'] = ssn_result['text']
            
        if 'email' in record:
            email_result = pipeline.redact(record['email'])
            redacted_record['email'] = email_result['text']
        
        redacted_records.append(redacted_record)
        print(f"  {redacted_record}")
    
    print()
    
    # Example 6.2: Log processing
    print("6.2 Log File Processing Pattern")
    print("-" * 30)
    
    # Simulate log entries
    log_entries = [
        "2023-10-15 10:30:00 INFO User john.doe@email.com logged in from 192.168.1.100",
        "2023-10-15 10:31:00 WARN Failed login attempt for SSN 123-45-6789",
        "2023-10-15 10:32:00 ERROR Payment failed for card 4532-1234-5678-9012",
        "2023-10-15 10:33:00 INFO User called support at (555) 123-4567"
    ]
    
    print("Original log entries:")
    for entry in log_entries:
        print(f"  {entry}")
    
    print("\nRedacted log entries:")
    for entry in log_entries:
        result = pipeline.redact(entry)
        print(f"  {result['text']}")
    
    print()
    
    # Example 6.3: API middleware pattern
    print("6.3 API Middleware Pattern")
    print("-" * 30)
    
    def redaction_middleware(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Middleware to automatically redact API responses"""
        
        # Fields that should be redacted
        sensitive_fields = ['ssn', 'email', 'phone', 'credit_card']
        
        result = request_data.copy()
        
        for field in sensitive_fields:
            if field in result:
                redacted = pipeline.redact(str(result[field]))
                result[field] = redacted['text']
        
        return result
    
    # Simulate API response
    api_response = {
        "user_id": 123,
        "name": "John Doe",
        "ssn": "123-45-6789",
        "email": "john.doe@email.com",
        "phone": "(555) 123-4567",
        "status": "active"
    }
    
    print(f"Original API response: {api_response}")
    
    redacted_response = redaction_middleware(api_response)
    print(f"Redacted API response: {redacted_response}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Run all API examples"""
    print("ZeroPhi API Usage Examples")
    print("==========================")
    print("These examples show how to integrate ZeroPhi into your applications")
    print()
    
    # Synchronous examples
    example_1_rest_api_basic()
    example_2_file_upload_api() 
    example_5_python_sdk()
    example_6_integration_patterns()
    
    # Asynchronous examples
    await example_3_async_api()
    await example_4_websocket_realtime()
    
    print("=" * 60)
    print("API EXAMPLES COMPLETE!")
    print("=" * 60)
    print("You've seen how to integrate ZeroPhi via:")
    print("- REST API endpoints")
    print("- File upload processing") 
    print("- Async/concurrent processing")
    print("- Real-time WebSocket streams")
    print("- Direct Python SDK")
    print("- Common integration patterns")
    print()
    print("Next steps:")
    print("1. Start the API server: zerophi serve")
    print("2. Test endpoints with your data")
    print("3. Integrate into your application")
    print("4. Configure security and monitoring")


if __name__ == "__main__":
    asyncio.run(main())