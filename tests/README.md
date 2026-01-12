# ZeroPhix Unit Tests

This directory contains comprehensive unit tests for ZeroPhix.

## Test Coverage

### Core Functionality Tests
- **test_basic.py**: Basic redaction pipeline functionality
- **test_redaction_pipeline.py**: Comprehensive pipeline tests (email, phone, SSN, encryption)
- **test_accuracy_features.py**: Accuracy enhancement features (ensemble voting, context propagation)

### Australian Entity Tests
- **test_au_validators.py**: Checksum validation (TFN, ABN, ACN, Medicare, BSB)
- **test_au_detector.py**: Australian entity detection
- **test_au_integration.py**: End-to-end Australian redaction
- **test_au_manual.py**: Manual testing scenarios

### Configuration Tests
- **test_api_config.py**: API configuration (environment variables, SSL, CORS, rate limiting)

### Evaluation Tests
- **test_eval_snapshot.py**: Benchmark evaluation snapshots

## Running Tests

### Install pytest
```bash
pip install pytest pytest-cov
```

### Run all tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=zerophix --cov-report=html

# Run specific test file
pytest tests/test_basic.py -v

# Run tests matching pattern
pytest tests/ -k "test_email" -v
```

### Expected Output
```
tests/test_basic.py::test_basic_redaction PASSED
tests/test_au_validators.py::test_valid_tfn PASSED
tests/test_au_validators.py::test_valid_abn PASSED
tests/test_api_config.py::test_default_configuration PASSED
...
=================== X passed in Y.XXs ====================
```

## Test Categories

### Unit Tests (Fast)
- Checksum validators
- Configuration parsing
- Basic redaction

### Integration Tests (Medium)
- Full pipeline execution
- Multiple detectors
- File processing

### Benchmark Tests (Slow)
- TAB evaluation
- PDF Deid evaluation
- Performance metrics

## Writing New Tests

Follow pytest conventions:
```python
import pytest
from zerophix.pipelines.redaction import RedactionPipeline
from zerophix.config import RedactionConfig

def test_my_feature():
    config = RedactionConfig(country='US')
    pipeline = RedactionPipeline(config)
    
    result = pipeline.redact("Test text")
    
    assert result['text'] != "Test text"
    assert len(result['spans']) > 0
```

## Continuous Integration

Tests run automatically on:
- Push to main branch
- Pull requests
- Manual workflow dispatch

See `.github/workflows/` for CI configuration.
