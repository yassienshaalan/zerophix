from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Span:
    start: int
    end: int
    label: str
    text: str
    confidence: float
    detector: str
    attrs: Dict[str, Any]

@dataclass
class Doc:
    text: str
    spans: List[Span]

@dataclass
class Decision:
    action: str
    replacement: Optional[str]
    reason: str

@dataclass
class Result:
    text: str
    entities: List[Dict[str, Any]]
    audit: List[Dict[str, Any]]
