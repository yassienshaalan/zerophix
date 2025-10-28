"""
ZeroPhi Security and Compliance Module

This module provides comprehensive security and compliance features including:
- Audit logging with encryption
- GDPR, HIPAA, and other compliance validation
- Zero Trust security model
- Encryption at rest
- Secure configuration management
"""

from .compliance import (
    SecureAuditLogger,
    ComplianceValidator,
    ZeroTrustValidator,
    ComplianceStandard,
    LogLevel,
    AuditLogEntry
)

from .encryption import (
    KeyManager,
    SecureDataStore,
    SecureConfiguration,
    SecureFileHandler,
    EncryptionError,
    generate_fernet_key,
    generate_master_key
)

__all__ = [
    # Compliance classes
    'SecureAuditLogger',
    'ComplianceValidator', 
    'ZeroTrustValidator',
    'ComplianceStandard',
    'LogLevel',
    'AuditLogEntry',
    
    # Encryption classes
    'KeyManager',
    'SecureDataStore',
    'SecureConfiguration',
    'SecureFileHandler',
    'EncryptionError',
    
    # Utility functions
    'generate_fernet_key',
    'generate_master_key'
]