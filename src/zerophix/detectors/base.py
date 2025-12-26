from typing import List, Dict, Any, Iterable
from dataclasses import dataclass

@dataclass
class Span:
    start: int
    end: int
    label: str
    score: float = 1.0
    source: str = "regex"

class Detector:
    name: str = "base"
    labels: Iterable[str] = ()

    def detect(self, text: str) -> List[Span]:
        raise NotImplementedError
