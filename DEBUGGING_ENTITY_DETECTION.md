# ZeroPhix Debugging Guide - Entity Detection Issues

## Problem Summary

When using ZeroPhix as an installed library (especially on Databricks), Australian entities (TFN, ABN, etc.) or other regex-based patterns were not being detected. The redacted output was identical to the input, indicating 0 entities found.

### Root Cause

The policy YAML files (`au.yml`, `us.yml`, `uk.yml`, etc.) containing al the regex patterns were **not included in the wheel distribution package**. When the package was installed, the policies directory was missing, causing the `RegexDetector` to load an empty policy dictionary.

### Impact

- Entity detection failed when using the package on systems where the source files weren't available
- Specifically affected:
  - Production deployments (wheels, pip installs)
  - Databricks installations
  - Cloud environments
  - Any installation method other than development mode (`pip install -e .`)

## The Fix

### Changes Made

1. **MANIFEST.in** - Added missing policy files to distribution:
   ```plaintext
   recursive-include src/zerophix/policies *.yml *.yaml
   ```

2. **pyproject.toml** - Added package-data configuration:
   ```toml
   [tool.setuptools.package-data]
   zerophix = ["policies/*.yml", "data/*.json", "data/*.txt"]
   ```

### Files Now Included in Distribution

The wheel package (`zerophix-X.X.X-py3-none-any.whl`) now contains:
```
zerophix/policies/au.yml      # Australian patterns
zerophix/policies/ca.yml      # Canadian patterns
zerophix/policies/eu.yml      # European patterns
zerophix/policies/us.yml      # US patterns
zerophix/policies/uk.yml      # UK patterns
zerophix/policies/__init__.py
zerophix/policies/loader.py
```

## Testing & Verification

### Quick Test on Installed Library

```python
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

# Test TFN/ABN detection
text = "TFN: 123 456 782, ABN: 53 004 085 616"
config = RedactionConfig(country="AU", detectors=["regex"])
pipeline = RedactionPipeline(config)
result = pipeline.redact(text)

print(f"Original: {text}")
print(f"Redacted: {result['text']}")
print(f"Entities found: {len(result.get('spans', []))}")
```

Expected output:
```
Original: TFN: 123 456 782, ABN: 53 004 085 616
Redacted: TFN: 004a709a7991, ABN: daa5b71390f6
Entities found: 2
```

### Test Script: `test_installed_library.py`

Run comprehensive tests:
```bash
python test_installed_library.py
```

Tests:
1. Basic TFN/ABN detection
2. Medicare/IHI detection
3. Address and postcode detection
4. Phone number detection

### Debug: Check if Policies Are Loaded

```python
from pathlib import Path
from zerophix.policies.loader import load_policy

# Check if policies load correctly
au_policy = load_policy("AU", None)
print(f"Regex patterns loaded: {len(au_policy.get('regex_patterns', {}))}")
print(f"Available entities: {list(au_policy.get('regex_patterns', {}).keys())[:5]}")

# Should output something like:
# Regex patterns loaded: 39
# Available entities: ['PERSON_NAME', 'TFN', 'ABN', 'ACN', 'MEDICARE']
```

### Debug: Check Detector Components

```python
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

config = RedactionConfig(country="AU", detectors=["regex"])
pipeline = RedactionPipeline(config)

print(f"Pipeline components: {[c.name for c in pipeline.components]}")
print(f"Pipeline component count: {len(pipeline.components)}")

# Check regex detector patterns
if pipeline.components:
    regex_detector = pipeline.components[0]
    print(f"Regex patterns: {len(regex_detector.patterns)}")
    print(f"Sample patterns: {list(regex_detector.patterns.keys())[:5]}")
```

## Installation Methods

### From PyPI (Recommended for Users)
```bash
pip install zerophix
pip install "zerophix[au]"           # AU specific
pip install "zerophix[all]"          # All features
```

### From Wheel File (Testing)
```bash
pip install dist/zerophix-0.1.17-py3-none-any.whl
```

### From Source (Development)
```bash
git clone https://github.com/yassienshaalan/zerophix.git
cd zerophix
pip install -e .  # Development mode
```

## Verifying the Fix

After rebuilding the wheel with the fix:

1. **Extract and inspect the wheel**:
   ```bash
   python -m zipfile -l zerophix-0.1.17-py3-none-any.whl | findstr "policies"
   ```
   Should show:
   ```
   zerophix/policies/au.yml
   zerophix/policies/ca.yml  
   zerophix/policies/eu.yml
   zerophix/policies/us.yml
   zerophix/policies/uk.yml
   ```

2. **Install and test**:
   ```bash
   pip install --force-reinstall dist/zerophix-0.1.17-py3-none-any.whl
   python test_installed_library.py
   ```

3. **On Databricks**:
   ```python
   %pip install zerophix
   # Then run the test examples
   %run /Workspace/examples/australian_entities_examples.py
   ```

## Common Issues & Solutions

### Issue: "Found 0 entities"
**Cause**: Policy files not loaded  
**Solution**: 
1. Verify policies are in site-packages: 
   ```bash
   python -c "from pathlib import Path; import zerophix; print(Path(zerophix.__file__).parent / 'policies')"
   ```
2. Check if files exist in that directory
3. Reinstall: `pip install --force-reinstall zerophix`

### Issue: "ModuleNotFoundError: zerophix"
**Cause**: Package not installed  
**Solution**:
```bash
pip install zerophix
```

### Issue: Detects some entities but not others
**Cause**: Pattern for that entity type may not exist or be incorrect  
**Solution**:
1. Check if entity is in policy file: `python -c "from zerophix.policies.loader import load_policy; print(load_policy('AU', None).get('regex_patterns', {}).keys())"`
2. Create custom pattern if needed:
   ```python
   config = RedactionConfig(
       country="AU",
       custom_patterns={"CUSTOM_ID": [r"\bCUST-\d{5}\b"]}
   )
   ```

### Issue: On Databricks - import error
**Cause**: Different Python environment or missing dependencies  
**Solution**:
1. Install in Databricks cluster libraries: `zerophix` 
2. Or via notebook: `%pip install zerophix`
3. Restart Python kernel after install

## Performance Considerations

- **First run**: ~100-200ms (loads models if using ML detectors)
- **Subsequent runs**: ~10-50ms (cached)
- **Batch processing**: Use `pipeline.redact_batch()` for multiple texts

## Next Steps

1. Rebuild and publish wheel to PyPI with this fix
2. Update release notes mentioning the fix
3. Update Databricks documentation
4. Add integration tests to CI/CD pipeline

## References

- **MANIFEST.in**: Controls which files are included in source distribution
- **pyproject.toml**: Controls which files are included in wheel distribution
- **Policy files**: `src/zerophix/policies/*.yml` - Contains regex patterns for each country

See `test_installed_library.py` for comprehensive testing examples.
