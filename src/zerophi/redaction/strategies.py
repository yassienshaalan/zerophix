import hashlib
import secrets
import string
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

@dataclass
class RedactionResult:
    """Result of a redaction operation"""
    redacted_text: str
    reversible: bool = False
    metadata: Dict[str, Any] = None
    privacy_budget_used: float = 0.0

class RedactionStrategy(ABC):
    """Abstract base class for redaction strategies"""
    
    @abstractmethod
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        """Apply redaction to text"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this redaction strategy"""
        pass

class MaskingStrategy(RedactionStrategy):
    """Simple masking with configurable characters"""
    
    def __init__(self, mask_char: str = "*", preserve_length: bool = True):
        self.mask_char = mask_char
        self.preserve_length = preserve_length
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        if self.preserve_length:
            redacted = self.mask_char * len(text)
        else:
            redacted = f"<{entity_type}>"
        
        return RedactionResult(
            redacted_text=redacted,
            reversible=False,
            metadata={"original_length": len(text)}
        )
    
    def get_strategy_name(self) -> str:
        return "masking"

class HashStrategy(RedactionStrategy):
    """Cryptographic hashing for irreversible redaction"""
    
    def __init__(self, algorithm: str = "sha256", salt: Optional[str] = None, truncate_length: int = 12):
        self.algorithm = algorithm
        self.salt = salt or secrets.token_hex(16)
        self.truncate_length = truncate_length
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        salted_text = f"{self.salt}{text}{entity_type}"
        
        if self.algorithm == "sha256":
            hash_obj = hashlib.sha256(salted_text.encode('utf-8'))
        elif self.algorithm == "sha512":
            hash_obj = hashlib.sha512(salted_text.encode('utf-8'))
        elif self.algorithm == "blake2b":
            hash_obj = hashlib.blake2b(salted_text.encode('utf-8'))
        else:
            hash_obj = hashlib.sha256(salted_text.encode('utf-8'))
        
        hash_value = hash_obj.hexdigest()[:self.truncate_length]
        
        return RedactionResult(
            redacted_text=f"HASH_{hash_value}",
            reversible=False,
            metadata={"algorithm": self.algorithm, "truncated": True}
        )
    
    def get_strategy_name(self) -> str:
        return "hash"

class EncryptionStrategy(RedactionStrategy):
    """Reversible encryption for secure redaction"""
    
    def __init__(self, encryption_key: Optional[bytes] = None, key_derivation_salt: Optional[bytes] = None):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library not available. Install with: pip install cryptography")
        
        self.key_derivation_salt = key_derivation_salt or secrets.token_bytes(16)
        
        if encryption_key:
            self.key = encryption_key
        else:
            # Generate a key from a password (in production, use proper key management)
            password = secrets.token_bytes(32)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.key_derivation_salt,
                iterations=100000,
            )
            self.key = kdf.derive(password)
        
        self.fernet = Fernet(Fernet.generate_key())
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        encrypted_bytes = self.fernet.encrypt(text.encode('utf-8'))
        encrypted_text = f"ENC_{encrypted_bytes.hex()[:24]}"
        
        return RedactionResult(
            redacted_text=encrypted_text,
            reversible=True,
            metadata={"encryption_key_id": hashlib.sha256(self.key).hexdigest()[:16]}
        )
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt previously encrypted text"""
        if not encrypted_text.startswith("ENC_"):
            raise ValueError("Invalid encrypted text format")
        
        # Note: This is simplified - in production, store full encrypted data
        raise NotImplementedError("Full decryption requires storing complete encrypted data")
    
    def get_strategy_name(self) -> str:
        return "encryption"

class FormatPreservingStrategy(RedactionStrategy):
    """Format-preserving redaction that maintains data structure"""
    
    def __init__(self, preserve_case: bool = True, preserve_special_chars: bool = True):
        self.preserve_case = preserve_case
        self.preserve_special_chars = preserve_special_chars
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        redacted_chars = []
        
        for char in text:
            if char.isdigit():
                redacted_chars.append(str(random.randint(0, 9)))
            elif char.isalpha():
                if self.preserve_case:
                    if char.isupper():
                        redacted_chars.append(random.choice(string.ascii_uppercase))
                    else:
                        redacted_chars.append(random.choice(string.ascii_lowercase))
                else:
                    redacted_chars.append(random.choice(string.ascii_letters))
            elif self.preserve_special_chars:
                redacted_chars.append(char)
            else:
                redacted_chars.append('X')
        
        return RedactionResult(
            redacted_text=''.join(redacted_chars),
            reversible=False,
            metadata={"format_preserved": True, "original_pattern": self._extract_pattern(text)}
        )
    
    def _extract_pattern(self, text: str) -> str:
        """Extract the format pattern of the text"""
        pattern = []
        for char in text:
            if char.isdigit():
                pattern.append('9')
            elif char.isalpha():
                pattern.append('A' if char.isupper() else 'a')
            else:
                pattern.append(char)
        return ''.join(pattern)
    
    def get_strategy_name(self) -> str:
        return "format_preserving"

class SyntheticDataStrategy(RedactionStrategy):
    """Generate realistic synthetic replacements"""
    
    def __init__(self):
        self.generators = {
            'PERSON_NAME': self._generate_name,
            'EMAIL': self._generate_email,
            'PHONE': self._generate_phone,
            'SSN': self._generate_ssn,
            'CREDIT_CARD': self._generate_credit_card,
            'DATE': self._generate_date,
            'ADDRESS': self._generate_address,
            'COMPANY': self._generate_company
        }
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        generator = self.generators.get(entity_type.upper(), self._generate_generic)
        synthetic_text = generator(text, metadata)
        
        return RedactionResult(
            redacted_text=synthetic_text,
            reversible=False,
            metadata={"synthetic": True, "entity_type": entity_type}
        )
    
    def _generate_name(self, original: str, metadata: Optional[Dict] = None) -> str:
        first_names = ['Alex', 'Jordan', 'Casey', 'Riley', 'Morgan', 'Avery', 'Quinn', 'Sage']
        last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Anderson', 'Taylor', 'Moore']
        
        # Try to preserve name structure
        parts = original.split()
        if len(parts) == 2:
            return f"{random.choice(first_names)} {random.choice(last_names)}"
        elif len(parts) >= 3:
            middle_initials = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            return f"{random.choice(first_names)} {random.choice(middle_initials)}. {random.choice(last_names)}"
        else:
            return random.choice(first_names)
    
    def _generate_email(self, original: str, metadata: Optional[Dict] = None) -> str:
        usernames = ['user', 'person', 'individual', 'contact']
        domains = ['example.com', 'test.org', 'sample.net', 'demo.co']
        
        username = f"{random.choice(usernames)}{random.randint(100, 999)}"
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    def _generate_phone(self, original: str, metadata: Optional[Dict] = None) -> str:
        # Generate a phone number preserving format
        if '-' in original:
            return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        elif '(' in original:
            return f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        else:
            return f"555{random.randint(100, 999)}{random.randint(1000, 9999)}"
    
    def _generate_ssn(self, original: str, metadata: Optional[Dict] = None) -> str:
        if '-' in original:
            return f"{random.randint(100, 799)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        else:
            return f"{random.randint(100, 799)}{random.randint(10, 99)}{random.randint(1000, 9999)}"
    
    def _generate_credit_card(self, original: str, metadata: Optional[Dict] = None) -> str:
        # Generate fake credit card preserving format
        if '-' in original:
            return f"4000-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        elif ' ' in original:
            return f"4000 {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
        else:
            return f"4000{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
    
    def _generate_date(self, original: str, metadata: Optional[Dict] = None) -> str:
        year = random.randint(1950, 2020)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        
        if '/' in original:
            return f"{month:02d}/{day:02d}/{year}"
        elif '-' in original:
            return f"{year}-{month:02d}-{day:02d}"
        else:
            return f"{month:02d}{day:02d}{year}"
    
    def _generate_address(self, original: str, metadata: Optional[Dict] = None) -> str:
        streets = ['Main St', 'Oak Ave', 'First St', 'Second Ave', 'Park Blvd']
        return f"{random.randint(100, 9999)} {random.choice(streets)}"
    
    def _generate_company(self, original: str, metadata: Optional[Dict] = None) -> str:
        companies = ['TechCorp', 'DataSystems', 'InfoSolutions', 'GlobalTech', 'NetServices']
        return random.choice(companies)
    
    def _generate_generic(self, original: str, metadata: Optional[Dict] = None) -> str:
        # Generic replacement based on original structure
        if original.isdigit():
            return ''.join([str(random.randint(0, 9)) for _ in range(len(original))])
        elif original.isalpha():
            return ''.join([random.choice(string.ascii_letters) for _ in range(len(original))])
        else:
            # Mixed content - preserve structure
            result = []
            for char in original:
                if char.isdigit():
                    result.append(str(random.randint(0, 9)))
                elif char.isalpha():
                    result.append(random.choice(string.ascii_letters))
                else:
                    result.append(char)
            return ''.join(result)
    
    def get_strategy_name(self) -> str:
        return "synthetic"

class DifferentialPrivacyStrategy(RedactionStrategy):
    """Differential privacy-based redaction with noise injection"""
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5, sensitivity: float = 1.0):
        """
        Initialize differential privacy strategy
        
        Args:
            epsilon: Privacy budget parameter (lower = more private)
            delta: Probability of privacy failure
            sensitivity: Sensitivity of the function (max change in output)
        """
        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity
        self.privacy_budget_used = 0.0
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        if self.privacy_budget_used >= self.epsilon:
            # Budget exhausted, use deterministic redaction
            return RedactionResult(
                redacted_text=f"<{entity_type}>",
                reversible=False,
                metadata={"privacy_budget_exhausted": True},
                privacy_budget_used=0.0
            )
        
        # Add Laplace noise for differential privacy
        budget_fraction = min(0.1, self.epsilon - self.privacy_budget_used)
        noise_scale = self.sensitivity / budget_fraction
        
        if text.isdigit():
            # Numerical data - add noise to value
            original_value = float(text)
            noise = np.random.laplace(0, noise_scale)
            noisy_value = original_value + noise
            
            # Ensure non-negative for certain types
            if entity_type in ['AGE', 'COUNT', 'QUANTITY']:
                noisy_value = max(0, noisy_value)
            
            redacted_text = str(int(round(noisy_value)))
        else:
            # Categorical data - probabilistic suppression
            suppression_prob = min(0.5, budget_fraction / self.epsilon)
            
            if random.random() < suppression_prob:
                redacted_text = f"<{entity_type}>"
            else:
                # Apply k-anonymity style generalization
                redacted_text = self._generalize_categorical(text, entity_type)
        
        self.privacy_budget_used += budget_fraction
        
        return RedactionResult(
            redacted_text=redacted_text,
            reversible=False,
            metadata={
                "differential_privacy": True,
                "epsilon_used": budget_fraction,
                "total_budget_used": self.privacy_budget_used
            },
            privacy_budget_used=budget_fraction
        )
    
    def _generalize_categorical(self, text: str, entity_type: str) -> str:
        """Apply generalization to categorical data"""
        generalizations = {
            'PERSON_NAME': ['Individual', 'Person', 'User'],
            'LOCATION': ['Location', 'Place', 'Area'],
            'ORGANIZATION': ['Organization', 'Company', 'Entity'],
            'EMAIL': ['email@domain.com'],
            'PHONE': ['XXX-XXX-XXXX']
        }
        
        candidates = generalizations.get(entity_type, [f'<{entity_type}>'])
        return random.choice(candidates)
    
    def get_remaining_budget(self) -> float:
        """Get remaining privacy budget"""
        return max(0, self.epsilon - self.privacy_budget_used)
    
    def reset_budget(self):
        """Reset the privacy budget"""
        self.privacy_budget_used = 0.0
    
    def get_strategy_name(self) -> str:
        return "differential_privacy"

class KAnonymityStrategy(RedactionStrategy):
    """K-anonymity based redaction using generalization"""
    
    def __init__(self, k: int = 5, generalization_hierarchies: Optional[Dict] = None):
        """
        Initialize k-anonymity strategy
        
        Args:
            k: Minimum group size for anonymity
            generalization_hierarchies: Custom generalization rules
        """
        self.k = k
        self.generalization_hierarchies = generalization_hierarchies or self._default_hierarchies()
        self.seen_values = {}  # Track seen values for grouping
    
    def _default_hierarchies(self) -> Dict[str, List[str]]:
        """Default generalization hierarchies"""
        return {
            'AGE': ['<30', '30-50', '50-70', '>70'],
            'LOCATION': ['City', 'State', 'Country', 'Continent'],
            'DATE': ['Year', 'Decade', 'Century'],
            'INCOME': ['Low', 'Medium', 'High', 'Very High']
        }
    
    def redact(self, text: str, entity_type: str, metadata: Optional[Dict] = None) -> RedactionResult:
        # Track occurrences of this value
        if entity_type not in self.seen_values:
            self.seen_values[entity_type] = {}
        
        if text not in self.seen_values[entity_type]:
            self.seen_values[entity_type][text] = 0
        
        self.seen_values[entity_type][text] += 1
        
        # If we have enough similar values, use original (k-anonymous)
        if self.seen_values[entity_type][text] >= self.k:
            redacted_text = text
        else:
            # Apply generalization
            redacted_text = self._generalize(text, entity_type)
        
        return RedactionResult(
            redacted_text=redacted_text,
            reversible=False,
            metadata={
                "k_anonymity": True,
                "k_value": self.k,
                "group_size": self.seen_values[entity_type][text]
            }
        )
    
    def _generalize(self, text: str, entity_type: str) -> str:
        """Apply generalization based on entity type"""
        if entity_type == 'AGE' and text.isdigit():
            age = int(text)
            if age < 30:
                return '<30'
            elif age < 50:
                return '30-50'
            elif age < 70:
                return '50-70'
            else:
                return '>70'
        
        # Default generalization
        hierarchy = self.generalization_hierarchies.get(entity_type, [f'<{entity_type}>'])
        return hierarchy[0]  # Use most general form
    
    def get_strategy_name(self) -> str:
        return "k_anonymity"

class RedactionStrategyManager:
    """Manager for different redaction strategies"""
    
    def __init__(self):
        self.strategies = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default redaction strategies"""
        self.strategies['mask'] = MaskingStrategy()
        self.strategies['hash'] = HashStrategy()
        self.strategies['synthetic'] = SyntheticDataStrategy()
        self.strategies['preserve_format'] = FormatPreservingStrategy()
        
        if CRYPTO_AVAILABLE:
            self.strategies['encrypt'] = EncryptionStrategy()
        
        # Advanced strategies
        self.strategies['differential_privacy'] = DifferentialPrivacyStrategy()
        self.strategies['k_anonymity'] = KAnonymityStrategy()
    
    def register_strategy(self, name: str, strategy: RedactionStrategy):
        """Register a custom redaction strategy"""
        self.strategies[name] = strategy
    
    def get_strategy(self, name: str) -> Optional[RedactionStrategy]:
        """Get a redaction strategy by name"""
        return self.strategies.get(name)
    
    def apply_redaction(self, text: str, entity_type: str, strategy_name: str, 
                       metadata: Optional[Dict] = None) -> RedactionResult:
        """Apply redaction using specified strategy"""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            # Fallback to hash strategy
            strategy = self.strategies['hash']
        
        return strategy.redact(text, entity_type, metadata)
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available redaction strategies"""
        return list(self.strategies.keys())