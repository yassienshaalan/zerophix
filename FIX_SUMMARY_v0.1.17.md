# ZeroPhix v0.1.17 - Fix Summary

## Problem Identified & Fixed

### The Issue

When you installed ZeroPhix as a library or on Databricks and ran the Australian entities example:
- **Expected**: TFN 123 456 782, ABN 53 004 085 616 → detected and redacted
- **Actual**: 0 entities found, text unchanged

### Root Cause

The **policy YAML files** (`au.yml`, `us.yml`, etc.) containing all regex patterns were not being included in the wheel distribution package. 

When the package was installed on a system without the source code (like Databricks or from PyPI), the policies directory was missing. The `RegexDetector` would then load an empty dictionary, resulting in zero detections.

### Why This Happened

- `MANIFEST.in` didn't include `src/zerophix/policies/*.yml`
- `pyproject.toml` didn't specify package-data for policy files
- These files are data files (not Python code), so they need explicit inclusion

## The Fix

### Changes Made

#### 1. **MANIFEST.in** (Updated)
Added policy files to distribution manifest:
```diff
+ # Include policy and data files
+ recursive-include src/zerophix/policies *.yml *.yaml
  recursive-include src/zerophix/data *.json *.txt *.yml
```

#### 2. **pyproject.toml** (Updated)
Added package-data configuration for setuptools:
```diff
  [tool.setuptools.packages.find]
  where = ["src"]
  
+ [tool.setuptools.package-data]
+ zerophix = ["policies/*.yml", "data/*.json", "data/*.txt"]
  
  [tool.setuptools.dynamic]
  version = {attr = "zerophix.__version__.__version__"}
```

### Files Now Included in Wheel

Verified the wheel now contains policy files:
```
zerophix/policies/au.yml      (3534 bytes) - Australian patterns
zerophix/policies/ca.yml      (5806 bytes) - Canadian patterns  
zerophix/policies/eu.yml      (5313 bytes) - European patterns
zerophix/policies/us.yml      (4788 bytes) - US patterns
zerophix/policies/uk.yml      (4492 bytes) - UK patterns
```

## Verification

### Test 1: Check Policies Load
```bash
python verify_installation.py
```

Output:
```
✓ PASS: Policies Available
✓ PASS: Detection Works
✓ PASS: Australian Entities
```

### Test 2: Manual Verification
```python
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

text = "TFN: 123 456 782, ABN: 53 004 085 616"
config = RedactionConfig(country="AU", detectors=["regex"])
pipeline = RedactionPipeline(config)
result = pipeline.redact(text)

print(f"Original: {text}")
print(f"Redacted: {result['text']}")
print(f"Found {len(result.get('spans', []))} entities")
```

Expected output:
```
Original: TFN: 123 456 782, ABN: 53 004 085 616
Redacted: TFN: 004a709a7991, ABN: daa5b71390f6
Found 2 entities
```

## Updated Examples Now Work

All example files from README work correctly:

### Quick Start Examples ✓
- `python examples/quick_start_examples.py` → Detects and redacts
- `python examples/scan_example.py` → Scans without errors
- `python examples/australian_entities_examples.py` → All 10 examples work

### Testing the Fix

Run comprehensive tests:
```bash
python test_installed_library.py      # 4 tests
python verify_installation.py         # 3 verification tests
```

All tests now PASS with entity detection working correctly.

## Using on Databricks

After this fix, you can now use ZeroPhix on Databricks:

### Installation
```bash
%pip install zerophix
%pip install zerophix[au]          # For Australian entities
%pip install "zerophix[all]"       # For all features
```

### Verify Installation
```python
%run /Workspace/verify_installation.py
```

### Use in Code
```python
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

text = """
Patient: Jane Doe
TFN: 123 456 782
Medicare: 2234 5678 9 1
Phone: 0412 345 678
"""

config = RedactionConfig(country="AU", detectors=["regex"])
pipeline = RedactionPipeline(config)
result = pipeline.redact(text)

display(dbutils.fs.put("/tmp/redacted.txt", result['text'], overwrite=True))
```

## What Was Tested

✓ Entity detection for all Australian entities (TFN, ABN, Medicare, Phone, Address)
✓ Multi-entity detection in complex documents
✓ Redaction strategies (replace, hash, mask)
✓ Checksum validation
✓ Batch processing
✓ File processing (CSV, Excel, PDF)
✓ Installation verification on clean venv

## Impact

This fix enables:
1. **Production deployments** - Wheels work correctly
2. **PyPI installations** - `pip install zerophix` works end-to-end
3. **Databricks** - All examples work on Databricks clusters
4. **Cloud environments** - Works in any containerized environment
5. **Development** - Easier testing and debugging

## Commits

```
653e903 fix: fix ReportGenerator and example files - handle missing context field
d1de9df fix: resolve example failures - remove unicode chars
5fe66a8 fix: update examples to work with minimal install
aeab0c3 fix: add graceful handling for missing dependencies
NEW:    fix: include policy YAML files in wheel distribution - fixes detection on installed lib
NEW:    docs: add debugging guide and test script for library installations
NEW:    test: add installation verification script
```

## Files Modified

- `MANIFEST.in` - Added policy files to distribution
- `pyproject.toml` - Added package-data configuration
- `DEBUGGING_ENTITY_DETECTION.md` - New comprehensive debugging guide
- `test_installed_library.py` - New test suite
- `verify_installation.py` - New verification script
- `README.md` - Updated with troubleshooting section

##Next Steps

1. ✓ **Fixed** - Policy files now included in wheel
2. ✓ **Tested** - All verification tests pass
3. ✓ **Documented** - Added debugging guide and verification scripts
4. **Ready** - For production release v0.1.17

## How to Rebuild

```bash
cd c:\Workspace\repos\zerophix
rm -r dist build
python -m build --wheel

# Wheel will include all policy files
python -m zipfile -l dist/zerophix-0.1.17-py3-none-any.whl | grep "policies"
```

## Support

For troubleshooting:
1. Run `python verify_installation.py` to check installation
2. See `DEBUGGING_ENTITY_DETECTION.md` for detailed debugging
3. Check that policy files are in site-packages: `python -c "from pathlib import Path; import zerophix; print(Path(zerophix.__file__).parent / 'policies')"`

---

**Status**: ✓ FIXED and VERIFIED  
**Version**: v0.1.17  
**Date**: February 18, 2026
