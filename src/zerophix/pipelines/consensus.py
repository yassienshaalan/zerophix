from typing import List, Dict
from ..detectors.base import Span
from ..config import RedactionConfig

class ConsensusModel:
    """
    Implements Weighted Voting for conflict resolution.
    """
    def __init__(self, config: RedactionConfig):
        self.weights = config.detector_weights

    def resolve(self, spans: List[Span], text: str = None) -> List[Span]:
        if not spans:
            return []

        # Sort by start position
        spans.sort(key=lambda x: x.start)
        
        resolved = []
        # Simple greedy resolution with weighted scoring for overlaps
        # A more complex graph-based approach could be used, but this is efficient.
        
        # We will group overlapping spans and pick the winner
        current_group = []
        group_end = -1
        
        for span in spans:
            if not current_group:
                current_group.append(span)
                group_end = span.end
                continue
            
            # Check overlap
            # Overlap if start < group_end
            if span.start < group_end:
                current_group.append(span)
                group_end = max(group_end, span.end)
            else:
                # Resolve current group
                winner = self._pick_winner(current_group)
                resolved.append(winner)
                
                # Start new group
                current_group = [span]
                group_end = span.end
        
        if current_group:
            winner = self._pick_winner(current_group)
            resolved.append(winner)
            
        return resolved

    def _pick_winner(self, group: List[Span]) -> Span:
        if len(group) == 1:
            return group[0]
            
        best_span = None
        best_score = -1.0
        
        # Medical label priority for healthcare domain
        medical_priority = {
            'MEDICATION': 3.0,
            'DRUG': 3.0,
            'MEDICAL_CONDITION': 3.0,
            'DISEASE': 3.0,
            'DIAGNOSIS': 3.0,
            'TREATMENT': 2.5,
            'PROCEDURE': 2.5,
            'PERSON': 1.0,  # Lower priority to avoid false positives
            'PERSON_NAME': 1.0,
        }
        
        for span in group:
            # Calculate weighted score
            # Base score * Detector Weight * Length Bonus * Label Priority
            weight = self.weights.get(span.source, 1.0)
            
            # Length bonus: prefer longer matches (often more specific)
            # but cap it so it doesn't overwhelm confidence
            length = span.end - span.start
            length_factor = 1.0 + (min(length, 20) / 100.0)
            
            # Label priority bonus for medical entities
            label_priority = medical_priority.get(span.label, 2.0)
            
            final_score = span.score * weight * length_factor * label_priority
            
            if final_score > best_score:
                best_score = final_score
                best_span = span
                
        return best_span
