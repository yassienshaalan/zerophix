import base64
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass

class KeyManager:
    """Secure key management for encryption at rest"""
    
    def __init__(self, key_store_path: str = "./keys"):
        """
        Initialize key manager
        
        Args:
            key_store_path: Path to store encryption keys
        """
        if not CRYPTO_AVAILABLE:
            raise EncryptionError("Cryptography library not available")
        
        self.key_store_path = Path(key_store_path)
        self.key_store_path.mkdir(exist_ok=True, mode=0o700)  # Secure permissions
        
        # Master key for key encryption
        self.master_key_file = self.key_store_path / "master.key"
        self.master_key = self._load_or_create_master_key()
        
        # Key rotation settings
        self.key_rotation_days = 90  # Rotate keys every 90 days
        self.key_versions = {}  # Track key versions
        
    def _load_or_create_master_key(self) -> bytes:
        """Load or create master encryption key"""
        if self.master_key_file.exists():
            try:
                with open(self.master_key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                raise EncryptionError(f"Failed to load master key: {e}")
        else:
            # Generate new master key
            master_key = secrets.token_bytes(32)  # 256-bit key
            
            try:
                with open(self.master_key_file, 'wb') as f:
                    f.write(master_key)
                # Set secure permissions (owner read/write only)
                os.chmod(self.master_key_file, 0o600)
                return master_key
            except Exception as e:
                raise EncryptionError(f"Failed to create master key: {e}")
    
    def generate_data_encryption_key(self, purpose: str) -> Dict[str, Any]:
        """Generate a new data encryption key (DEK)"""
        # Generate DEK
        dek = Fernet.generate_key()
        
        # Create key metadata
        key_metadata = {
            "purpose": purpose,
            "created_at": datetime.utcnow().isoformat(),
            "version": 1,
            "algorithm": "Fernet",
            "rotation_due": (datetime.utcnow() + timedelta(days=self.key_rotation_days)).isoformat()
        }
        
        # Encrypt DEK with master key
        master_fernet = Fernet(base64.urlsafe_b64encode(self.master_key))
        encrypted_dek = master_fernet.encrypt(dek)
        
        # Store encrypted DEK
        key_id = hashlib.sha256(f"{purpose}_{time.time()}".encode()).hexdigest()[:16]
        key_file = self.key_store_path / f"{key_id}.key"
        
        key_data = {
            "encrypted_key": base64.b64encode(encrypted_dek).decode(),
            "metadata": key_metadata
        }
        
        with open(key_file, 'w') as f:
            json.dump(key_data, f)
        os.chmod(key_file, 0o600)
        
        self.key_versions[purpose] = key_id
        
        return {
            "key_id": key_id,
            "key": dek,
            "metadata": key_metadata
        }
    
    def get_data_encryption_key(self, key_id: str) -> bytes:
        """Retrieve and decrypt a data encryption key"""
        key_file = self.key_store_path / f"{key_id}.key"
        
        if not key_file.exists():
            raise EncryptionError(f"Key {key_id} not found")
        
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
            
            encrypted_dek = base64.b64decode(key_data["encrypted_key"])
            master_fernet = Fernet(base64.urlsafe_b64encode(self.master_key))
            dek = master_fernet.decrypt(encrypted_dek)
            
            return dek
            
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt key {key_id}: {e}")
    
    def rotate_key(self, purpose: str) -> Dict[str, Any]:
        """Rotate a data encryption key"""
        old_key_id = self.key_versions.get(purpose)
        new_key_info = self.generate_data_encryption_key(purpose)
        
        if old_key_id:
            # Mark old key for deprecation
            old_key_file = self.key_store_path / f"{old_key_id}.key"
            if old_key_file.exists():
                with open(old_key_file, 'r') as f:
                    old_key_data = json.load(f)
                
                old_key_data["metadata"]["deprecated_at"] = datetime.utcnow().isoformat()
                old_key_data["metadata"]["replaced_by"] = new_key_info["key_id"]
                
                with open(old_key_file, 'w') as f:
                    json.dump(old_key_data, f)
        
        return new_key_info
    
    def cleanup_old_keys(self, retention_days: int = 365):
        """Clean up old deprecated keys"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        for key_file in self.key_store_path.glob("*.key"):
            if key_file.name == "master.key":
                continue
                
            try:
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                
                deprecated_at = key_data["metadata"].get("deprecated_at")
                if deprecated_at:
                    deprecated_date = datetime.fromisoformat(deprecated_at)
                    if deprecated_date < cutoff_date:
                        key_file.unlink()
                        
            except Exception:
                continue

class SecureDataStore:
    """Secure data storage with encryption at rest"""
    
    def __init__(self, storage_path: str = "./secure_data", key_manager: KeyManager = None):
        """
        Initialize secure data store
        
        Args:
            storage_path: Path to store encrypted data
            key_manager: Key manager instance
        """
        if not CRYPTO_AVAILABLE:
            raise EncryptionError("Cryptography library not available")
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, mode=0o700)
        
        self.key_manager = key_manager or KeyManager()
        self._setup_data_keys()
        
    def _setup_data_keys(self):
        """Setup data encryption keys"""
        # Generate keys for different data types
        self.audit_key_info = self.key_manager.generate_data_encryption_key("audit_logs")
        self.config_key_info = self.key_manager.generate_data_encryption_key("configurations")
        self.cache_key_info = self.key_manager.generate_data_encryption_key("cache_data")
        
    def store_encrypted_data(self, data: Union[str, bytes, Dict], 
                           data_type: str,
                           identifier: str,
                           metadata: Optional[Dict] = None) -> str:
        """Store data with encryption"""
        
        # Get appropriate encryption key
        if data_type == "audit":
            key = self.audit_key_info["key"]
        elif data_type == "config":
            key = self.config_key_info["key"]
        elif data_type == "cache":
            key = self.cache_key_info["key"]
        else:
            # Generate new key for unknown data type
            key_info = self.key_manager.generate_data_encryption_key(data_type)
            key = key_info["key"]
        
        # Prepare data for encryption
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        # Encrypt data
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data_bytes)
        
        # Create storage record
        storage_record = {
            "identifier": identifier,
            "data_type": data_type,
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encryption_algorithm": "Fernet",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store encrypted record
        record_id = hashlib.sha256(f"{data_type}_{identifier}_{time.time()}".encode()).hexdigest()[:16]
        record_file = self.storage_path / f"{record_id}.encrypted"
        
        with open(record_file, 'w') as f:
            json.dump(storage_record, f)
        os.chmod(record_file, 0o600)
        
        return record_id
    
    def retrieve_encrypted_data(self, record_id: str) -> Dict[str, Any]:
        """Retrieve and decrypt stored data"""
        record_file = self.storage_path / f"{record_id}.encrypted"
        
        if not record_file.exists():
            raise EncryptionError(f"Record {record_id} not found")
        
        try:
            with open(record_file, 'r') as f:
                storage_record = json.load(f)
            
            # Get decryption key
            data_type = storage_record["data_type"]
            if data_type == "audit":
                key = self.audit_key_info["key"]
            elif data_type == "config":
                key = self.config_key_info["key"]
            elif data_type == "cache":
                key = self.cache_key_info["key"]
            else:
                # Try to find key for this data type
                purpose_key_id = self.key_manager.key_versions.get(data_type)
                if not purpose_key_id:
                    raise EncryptionError(f"No key found for data type: {data_type}")
                key = self.key_manager.get_data_encryption_key(purpose_key_id)
            
            # Decrypt data
            encrypted_data = base64.b64decode(storage_record["encrypted_data"])
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Try to parse as JSON, fallback to string
            try:
                data = json.loads(decrypted_data.decode('utf-8'))
            except json.JSONDecodeError:
                data = decrypted_data.decode('utf-8')
            
            return {
                "data": data,
                "metadata": storage_record["metadata"],
                "created_at": storage_record["created_at"]
            }
            
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt record {record_id}: {e}")
    
    def delete_encrypted_data(self, record_id: str):
        """Securely delete encrypted data"""
        record_file = self.storage_path / f"{record_id}.encrypted"
        
        if record_file.exists():
            # Secure deletion: overwrite file before deletion
            file_size = record_file.stat().st_size
            with open(record_file, 'r+b') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            record_file.unlink()

class SecureConfiguration:
    """Secure configuration management with encryption"""
    
    def __init__(self, config_file: str = "zerophi_secure_config.json", 
                 key_manager: KeyManager = None):
        """
        Initialize secure configuration
        
        Args:
            config_file: Path to configuration file
            key_manager: Key manager instance
        """
        if not CRYPTO_AVAILABLE:
            raise EncryptionError("Cryptography library not available")
        
        self.config_file = Path(config_file)
        self.key_manager = key_manager or KeyManager()
        self.data_store = SecureDataStore(key_manager=self.key_manager)
        
        # Default secure configuration
        self.default_config = {
            "security": {
                "encryption_at_rest": True,
                "audit_logging": True,
                "zero_trust_mode": True,
                "key_rotation_days": 90,
                "session_timeout_minutes": 30,
                "max_failed_logins": 3,
                "password_policy": {
                    "min_length": 12,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_symbols": True
                }
            },
            "compliance": {
                "standards": ["GDPR", "HIPAA"],
                "audit_retention_days": 2555,  # 7 years
                "data_classification_required": True,
                "consent_management": True,
                "breach_notification": True
            },
            "privacy": {
                "differential_privacy_enabled": True,
                "k_anonymity_threshold": 5,
                "data_minimization": True,
                "purpose_limitation": True,
                "storage_limitation_days": 365
            },
            "api": {
                "rate_limiting": {
                    "requests_per_minute": 100,
                    "burst_limit": 20
                },
                "authentication_required": True,
                "tls_min_version": "1.3",
                "cors_enabled": False
            }
        }
        
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load or create secure configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Decrypt sensitive values if they exist
                if "encrypted_record_id" in config_data:
                    record_id = config_data["encrypted_record_id"]
                    decrypted_data = self.data_store.retrieve_encrypted_data(record_id)
                    return decrypted_data["data"]
                else:
                    # Legacy unencrypted config
                    return config_data
                    
            except Exception as e:
                print(f"Failed to load config: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        """Save configuration with encryption"""
        try:
            # Store config data encrypted
            record_id = self.data_store.store_encrypted_data(
                data=self.config,
                data_type="config",
                identifier="main_config",
                metadata={"version": "1.0", "encrypted": True}
            )
            
            # Save reference to encrypted config
            config_ref = {
                "encrypted_record_id": record_id,
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_ref, f, indent=2)
            
            os.chmod(self.config_file, 0o600)
            
        except Exception as e:
            raise EncryptionError(f"Failed to save secure config: {e}")
    
    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """Set configuration value by dot-separated path"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get all security-related settings"""
        return self.config.get("security", {})
    
    def get_compliance_settings(self) -> Dict[str, Any]:
        """Get all compliance-related settings"""
        return self.config.get("compliance", {})
    
    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get all privacy-related settings"""
        return self.config.get("privacy", {})
    
    def update_security_policy(self, policy_updates: Dict[str, Any]):
        """Update security policy settings"""
        if "security" not in self.config:
            self.config["security"] = {}
        
        self.config["security"].update(policy_updates)
        self.save_config()
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """Check if a security/privacy feature is enabled"""
        return bool(self.get(feature_path, False))

class SecureFileHandler:
    """Handle file operations with encryption and secure deletion"""
    
    def __init__(self, key_manager: KeyManager = None):
        """
        Initialize secure file handler
        
        Args:
            key_manager: Key manager instance
        """
        if not CRYPTO_AVAILABLE:
            raise EncryptionError("Cryptography library not available")
        
        self.key_manager = key_manager or KeyManager()
        
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file"""
        input_file = Path(file_path)
        if not input_file.exists():
            raise EncryptionError(f"File not found: {file_path}")
        
        # Generate encryption key for this file
        key_info = self.key_manager.generate_data_encryption_key(f"file_{input_file.name}")
        fernet = Fernet(key_info["key"])
        
        # Determine output path
        if output_path is None:
            output_file = input_file.with_suffix(input_file.suffix + '.encrypted')
        else:
            output_file = Path(output_path)
        
        # Encrypt file
        try:
            with open(input_file, 'rb') as infile:
                plaintext = infile.read()
            
            encrypted_data = fernet.encrypt(plaintext)
            
            # Create encrypted file with metadata
            file_metadata = {
                "original_name": input_file.name,
                "original_size": len(plaintext),
                "key_id": key_info["key_id"],
                "encrypted_at": datetime.utcnow().isoformat(),
                "checksum": hashlib.sha256(plaintext).hexdigest()
            }
            
            encrypted_package = {
                "metadata": file_metadata,
                "encrypted_data": base64.b64encode(encrypted_data).decode()
            }
            
            with open(output_file, 'w') as outfile:
                json.dump(encrypted_package, outfile)
            
            os.chmod(output_file, 0o600)
            
            return str(output_file)
            
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt file: {e}")
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        encrypted_file = Path(encrypted_file_path)
        if not encrypted_file.exists():
            raise EncryptionError(f"Encrypted file not found: {encrypted_file_path}")
        
        try:
            with open(encrypted_file, 'r') as infile:
                encrypted_package = json.load(infile)
            
            metadata = encrypted_package["metadata"]
            encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
            
            # Get decryption key
            key = self.key_manager.get_data_encryption_key(metadata["key_id"])
            fernet = Fernet(key)
            
            # Decrypt data
            plaintext = fernet.decrypt(encrypted_data)
            
            # Verify checksum
            if hashlib.sha256(plaintext).hexdigest() != metadata["checksum"]:
                raise EncryptionError("File integrity check failed")
            
            # Determine output path
            if output_path is None:
                output_file = encrypted_file.parent / metadata["original_name"]
            else:
                output_file = Path(output_path)
            
            with open(output_file, 'wb') as outfile:
                outfile.write(plaintext)
            
            return str(output_file)
            
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt file: {e}")
    
    def secure_delete(self, file_path: str, passes: int = 3):
        """Securely delete a file by overwriting multiple times"""
        file_to_delete = Path(file_path)
        if not file_to_delete.exists():
            return
        
        try:
            file_size = file_to_delete.stat().st_size
            
            with open(file_to_delete, 'r+b') as f:
                for _ in range(passes):
                    # Overwrite with random data
                    f.seek(0)
                    f.write(secrets.token_bytes(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            file_to_delete.unlink()
            
        except Exception as e:
            raise EncryptionError(f"Failed to securely delete file: {e}")

# Export encryption key generation utility
def generate_fernet_key() -> str:
    """Generate a new Fernet encryption key"""
    if not CRYPTO_AVAILABLE:
        raise EncryptionError("Cryptography library not available")
    
    return Fernet.generate_key().decode()

def generate_master_key() -> str:
    """Generate a new master encryption key"""
    return base64.b64encode(secrets.token_bytes(32)).decode()