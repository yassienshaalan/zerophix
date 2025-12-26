import unittest
from zerophix.config import RedactionConfig
from zerophix.pipelines.consensus import ConsensusModel
from zerophix.pipelines.context import ContextPropagator
from zerophix.pipelines.allowlist import AllowListFilter
from zerophix.detectors.base import Span

class TestAccuracyFeatures(unittest.TestCase):

    def setUp(self):
        self.config = RedactionConfig(
            country="us",
            company="acme",
            enable_ensemble_voting=True,
            enable_context_propagation=True,
            allow_list=["ZeroPhix", "Acme Corp"],
            detector_weights={"regex": 2.0, "ml": 1.0}
        )

    def test_consensus_voting(self):
        consensus = ConsensusModel(self.config)
        text = "Call John at 555-1234"
        
        # Conflict: Regex says PHONE (score 1.0 * 2.0 = 2.0), ML says ID (score 0.9 * 1.0 = 0.9)
        spans = [
            Span(13, 21, "PHONE", 1.0, "regex"),
            Span(13, 21, "ID", 0.9, "ml")
        ]
        
        resolved = consensus.resolve(spans, text)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].label, "PHONE")
        self.assertEqual(resolved[0].source, "regex")

    def test_context_propagation(self):
        prop = ContextPropagator(self.config)
        text = "Dr. Smith is here. Smith is busy."
        
        # Detector found first "Smith" with high confidence
        spans = [
            Span(4, 9, "PERSON", 0.95, "ml")
        ]
        
        # Should propagate to second "Smith" (index 19-24)
        new_spans = prop.propagate(text, spans)
        
        self.assertEqual(len(new_spans), 2)
        self.assertEqual(new_spans[1].label, "PERSON")
        self.assertEqual(new_spans[1].start, 19)
        self.assertEqual(new_spans[1].source, "context_memory")

    def test_allow_list(self):
        allow = AllowListFilter(self.config)
        text = "Contact Acme Corp for support."
        
        spans = [
            Span(8, 17, "ORG", 0.9, "ml") # "Acme Corp"
        ]
        
        filtered = allow.filter(text, spans)
        self.assertEqual(len(filtered), 0)

if __name__ == '__main__':
    unittest.main()
