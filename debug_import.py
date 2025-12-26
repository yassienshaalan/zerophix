import sys
import traceback

sys.path.insert(0, "src")

print("Attempting to import OpenMedDetector...")
try:
    from zerophix.detectors.openmed_detector import OpenMedDetector
    print("Import successful!")
except Exception:
    print("Import failed!")
    traceback.print_exc()
