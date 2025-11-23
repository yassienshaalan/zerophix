import re
import json
from typing import List, Dict, Optional, Set, Any
from .base import Detector, Span

class CustomEntityDetector(Detector):
    """Configurable detector for domain-specific and custom entity types"""
    
    name = "custom"
    
    def __init__(self, config_file: Optional[str] = None, custom_patterns: Optional[Dict] = None):
        """
        Initialize custom entity detector
        
        Args:
            config_file: Path to JSON config file with entity definitions
            custom_patterns: Dictionary of custom patterns to use directly
        """
        self.patterns = {}
        self.validators = {}
        self.transformers = {}
        
        if config_file:
            self._load_config_file(config_file)
        
        if custom_patterns:
            self._load_patterns(custom_patterns)
        
        # Default medical patterns
        self._add_medical_patterns()
        
        # Default financial patterns  
        self._add_financial_patterns()
        
        # Default technical patterns
        self._add_technical_patterns()
    
    def _load_config_file(self, config_file: str):
        """Load entity patterns from JSON config file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self._load_patterns(config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _load_patterns(self, patterns_config: Dict):
        """Load patterns from configuration dictionary"""
        for entity_type, config in patterns_config.items():
            if isinstance(config, str):
                # Simple pattern string
                self.patterns[entity_type] = [config]
            elif isinstance(config, dict):
                # Complex configuration
                self.patterns[entity_type] = config.get('patterns', [])
                if 'validator' in config:
                    self.validators[entity_type] = config['validator']
                if 'transformer' in config:
                    self.transformers[entity_type] = config['transformer']
            elif isinstance(config, list):
                # List of patterns
                self.patterns[entity_type] = config
    
    def _add_medical_patterns(self):
        """Add medical-specific entity patterns"""
        medical_patterns = {
            'MEDICAL_RECORD_NUMBER': [
                r'\bMRN\s*:?\s*([A-Z0-9]{6,12})\b',
                r'\b(medical\s+record|chart)\s+(?:number|#)\s*:?\s*([A-Z0-9]{6,12})\b'
            ],
            'DEA_NUMBER': [
                r'\bDEA\s*:?\s*([A-Z]{2}\d{7})\b',
                r'\b([A-Z]{2}\d{7})\b'  # Basic DEA format
            ],
            'NPI_NUMBER': [
                r'\bNPI\s*:?\s*(\d{10})\b',
                r'\b(national\s+provider\s+identifier)\s*:?\s*(\d{10})\b'
            ],
            'MEDICAL_LICENSE': [
                r'\b(medical\s+license|license)\s*(?:number|#)?\s*:?\s*([A-Z0-9]{4,15})\b',
                r'\bMD\s*:?\s*([A-Z0-9]{4,15})\b'
            ],
            'PATIENT_ID': [
                r'\b(patient\s+(?:id|identifier|number))\s*:?\s*([A-Z0-9]{4,12})\b',
                r'\bPID\s*:?\s*([A-Z0-9]{4,12})\b'
            ],
            'INSURANCE_POLICY': [
                r'\b(policy\s+(?:number|#))\s*:?\s*([A-Z0-9]{6,20})\b',
                r'\b(insurance\s+(?:id|number))\s*:?\s*([A-Z0-9]{6,20})\b'
            ],
            'PRESCRIPTION_NUMBER': [
                r'\b(prescription|rx)\s+(?:number|#)\s*:?\s*([A-Z0-9]{6,15})\b',
                r'\bRX\s*:?\s*([A-Z0-9]{6,15})\b'
            ],
            'ICD_CODE': [
                r'\bICD[-\s]?(?:9|10)\s*:?\s*([A-Z]\d{2}(?:\.\d{1,3})?)\b',
                r'\b([A-Z]\d{2}(?:\.\d{1,3})?)\b'  # ICD format
            ],
            'CPT_CODE': [
                r'\bCPT\s*:?\s*(\d{5})\b',
                r'\b(\d{5})\b'  # 5-digit CPT format
            ]
        }
        
        for entity_type, patterns in medical_patterns.items():
            if entity_type not in self.patterns:
                self.patterns[entity_type] = patterns
    
    def _add_financial_patterns(self):
        """Add financial-specific entity patterns"""
        financial_patterns = {
            'BANK_ACCOUNT': [
                r'\b(account\s+(?:number|#))\s*:?\s*(\d{8,17})\b',
                r'\b(acct)\s*:?\s*(\d{8,17})\b'
            ],
            'ROUTING_NUMBER': [
                r'\b(routing\s+(?:number|#))\s*:?\s*(\d{9})\b',
                r'\b(ABA)\s*:?\s*(\d{9})\b'
            ],
            'SWIFT_CODE': [
                r'\b(SWIFT|BIC)\s*:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b'
            ],
            'IBAN': [
                r'\bIBAN\s*:?\s*([A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{0,16})\b'
            ],
            'INVESTMENT_ACCOUNT': [
                r'\b(investment|brokerage)\s+account\s*:?\s*([A-Z0-9]{6,15})\b'
            ],
            'TAX_ID': [
                r'\b(tax\s+(?:id|identification))\s*:?\s*(\d{2}-?\d{7})\b',
                r'\bEIN\s*:?\s*(\d{2}-?\d{7})\b'
            ]
        }
        
        for entity_type, patterns in financial_patterns.items():
            if entity_type not in self.patterns:
                self.patterns[entity_type] = patterns
    
    def _add_technical_patterns(self):
        """Add technical/IT-specific entity patterns"""
        technical_patterns = {
            'API_KEY': [
                r'\b(api[_\s]?key)\s*[:=]\s*["\']?([A-Za-z0-9]{20,})["\']?',
                r'\b(token)\s*[:=]\s*["\']?([A-Za-z0-9]{20,})["\']?'
            ],
            'DATABASE_CONNECTION': [
                r'(mongodb://|mysql://|postgresql://|redis://)[^\s]+',
                r'\b(connection\s+string)\s*[:=]\s*["\']?([^"\']+)["\']?'
            ],
            'IP_ADDRESS_PRIVATE': [
                r'\b(10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3})\b',
                r'\b(192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3})\b',
                r'\b(172\.(?:1[6-9]|2[0-9]|3[0-1])\.(?:[0-9]{1,3}\.)[0-9]{1,3})\b'
            ],
            'MAC_ADDRESS': [
                r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'
            ],
            'UUID': [
                r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
            ],
            'JWT_TOKEN': [
                r'\b(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b'
            ],
            'PRIVATE_KEY': [
                r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
                r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+OPENSSH\s+PRIVATE\s+KEY-----'
            ],
            'AWS_ACCESS_KEY': [
                r'\b(AKIA[0-9A-Z]{16})\b'
            ],
            'GCP_API_KEY': [
                r'\b(AIza[0-9A-Za-z_-]{35})\b'
            ]
        }
        
        for entity_type, patterns in technical_patterns.items():
            if entity_type not in self.patterns:
                self.patterns[entity_type] = patterns
    
    def detect(self, text: str) -> List[Span]:
        """Detect custom entities in text"""
        spans = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                        # Extract the actual entity (might be in a group)
                        entity_text = match.group(match.lastindex) if match.lastindex else match.group(0)
                        
                        # Validate if validator is defined
                        if entity_type in self.validators:
                            if not self._validate_entity(entity_text, entity_type):
                                continue
                        
                        # Calculate confidence based on pattern specificity
                        confidence = self._calculate_confidence(entity_text, entity_type, pattern)
                        
                        span = Span(
                            start=match.start(),
                            end=match.end(),
                            label=entity_type,
                            score=confidence,
                            source="custom"
                        )
                        spans.append(span)
                        
                except re.error as e:
                    print(f"Invalid regex pattern for {entity_type}: {pattern} - {e}")
                    continue
        
        return spans
    
    def _validate_entity(self, entity_text: str, entity_type: str) -> bool:
        """Validate detected entity using custom validator"""
        validator = self.validators.get(entity_type)
        if not validator:
            return True
        
        # Simple validation rules
        if isinstance(validator, dict):
            min_length = validator.get('min_length', 0)
            max_length = validator.get('max_length', float('inf'))
            required_chars = validator.get('required_chars', [])
            forbidden_chars = validator.get('forbidden_chars', [])
            
            if not (min_length <= len(entity_text) <= max_length):
                return False
            
            for char in required_chars:
                if char not in entity_text:
                    return False
            
            for char in forbidden_chars:
                if char in entity_text:
                    return False
        
        return True
    
    def _calculate_confidence(self, entity_text: str, entity_type: str, pattern: str) -> float:
        """Calculate confidence score for detected entity"""
        base_confidence = 0.8
        
        # Higher confidence for longer, more specific patterns
        if len(pattern) > 50:
            base_confidence += 0.1
        
        # Higher confidence for entities with specific prefixes/contexts
        if any(keyword in pattern.lower() for keyword in ['number', 'id', 'code']):
            base_confidence += 0.05
        
        # Medical/financial entities get higher confidence due to specificity
        if entity_type.startswith(('MEDICAL_', 'DEA_', 'NPI_', 'BANK_', 'SWIFT_')):
            base_confidence += 0.1
        
        # Adjust based on entity length
        if len(entity_text) > 10:
            base_confidence += 0.05
        elif len(entity_text) < 4:
            base_confidence -= 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def add_pattern(self, entity_type: str, pattern: str, validator: Optional[Dict] = None):
        """Add a new pattern for entity detection"""
        if entity_type not in self.patterns:
            self.patterns[entity_type] = []
        
        self.patterns[entity_type].append(pattern)
        
        if validator:
            self.validators[entity_type] = validator
    
    def remove_pattern(self, entity_type: str, pattern: Optional[str] = None):
        """Remove pattern(s) for an entity type"""
        if entity_type in self.patterns:
            if pattern:
                self.patterns[entity_type] = [p for p in self.patterns[entity_type] if p != pattern]
            else:
                del self.patterns[entity_type]
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        return list(self.patterns.keys())