"""zerophix: AU-first PII/PHI redaction."""

from zerophix.__version__ import (
    __version__,
    __version_info__,
    __author__,
    __license__,
    __copyright__,
)

# Core imports for easy access
from zerophix.config import RedactionConfig
from zerophix.pipelines.redaction import RedactionPipeline

__all__ = [
    # Version info
    "__version__",
    "__version_info__",
    "__author__",
    "__license__",
    "__copyright__",
    # Core classes
    "RedactionConfig",
    "RedactionPipeline",
    # Submodules
    "config",
    "cli",
    "pipelines",
    "detectors",
    "models",
]

