import logging
import json
import time
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import os
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class LogLevel(Enum):
    """Audit log levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ComplianceStandard(Enum):
    """Supported compliance standards"""
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    CCPA = "CCPA"
    UK_DPA_2018 = "UK_DPA_2018"
    PIPEDA = "PIPEDA"
    SOX = "SOX"
    PCI_DSS = "PCI_DSS"

@dataclass
class AuditLogEntry:
    """Audit log entry structure"""
    timestamp: str
    event_id: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    operation: str
    resource: str
    details: Dict[str, Any]
    compliance_context: Dict[str, Any]
    risk_level: str
    data_classification: str
    retention_period: int  # days
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SecureAuditLogger:
    """Secure audit logging with compliance features"""
    
    def __init__(self, 
                 log_directory: str = "./audit_logs",
                 encryption_key: Optional[bytes] = None,
                 compliance_standards: List[ComplianceStandard] = None,
                 max_log_size: int = 100 * 1024 * 1024,  # 100MB
                 retention_days: int = 2555):  # 7 years default
        """
        Initialize secure audit logger
        
        Args:
            log_directory: Directory to store audit logs
            encryption_key: Key for encrypting audit logs
            compliance_standards: List of compliance standards to enforce
            max_log_size: Maximum size of a single log file
            retention_days: Default retention period in days
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        self.max_log_size = max_log_size
        self.retention_days = retention_days
        self.compliance_standards = compliance_standards or [ComplianceStandard.GDPR]
        
        # Setup encryption
        if CRYPTO_AVAILABLE and encryption_key:
            self.fernet = Fernet(encryption_key)
            self.encryption_enabled = True
        else:
            self.fernet = None
            self.encryption_enabled = False
            if encryption_key:
                logging.warning("Cryptography not available. Audit logs will not be encrypted.")
        
        # Setup logging
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup secure file logger"""
        logger = logging.getLogger(f"zerophi_audit_{id(self)}")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create secure file handler
        log_file = self.log_directory / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        
        handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        # Detailed formatter for audit trails
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_redaction_event(self,
                           operation: str,
                           text_length: int,
                           entities_found: int,
                           entity_types: List[str],
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           country: Optional[str] = None,
                           data_classification: str = "SENSITIVE",
                           additional_details: Optional[Dict] = None):
        """Log a redaction event"""
        
        event_details = {
            "text_length": text_length,
            "entities_found": entities_found,
            "entity_types": entity_types,
            "country_policy": country,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            **(additional_details or {})
        }
        
        compliance_context = self._build_compliance_context(
            operation, data_classification, entity_types
        )
        
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=str(uuid.uuid4()),
            event_type="DATA_REDACTION",
            user_id=user_id,
            session_id=session_id,
            operation=operation,
            resource="TEXT_DATA",
            details=event_details,
            compliance_context=compliance_context,
            risk_level=self._assess_risk_level(entities_found, entity_types),
            data_classification=data_classification,
            retention_period=self._get_retention_period(data_classification)
        )
        
        self._write_audit_log(audit_entry)
    
    def log_api_access(self,
                      endpoint: str,
                      method: str,
                      status_code: int,
                      user_id: Optional[str] = None,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      request_size: Optional[int] = None,
                      response_size: Optional[int] = None):
        """Log API access event"""
        
        event_details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_size": request_size,
            "response_size": response_size
        }
        
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=str(uuid.uuid4()),
            event_type="API_ACCESS",
            user_id=user_id,
            session_id=None,
            operation=f"{method} {endpoint}",
            resource="API_ENDPOINT",
            details=event_details,
            compliance_context={"requires_authentication": True},
            risk_level="LOW" if status_code < 400 else "MEDIUM",
            data_classification="SYSTEM",
            retention_period=365  # 1 year for API logs
        )
        
        self._write_audit_log(audit_entry)
    
    def log_security_event(self,
                          event_type: str,
                          description: str,
                          severity: str = "MEDIUM",
                          user_id: Optional[str] = None,
                          additional_details: Optional[Dict] = None):
        """Log security-related events"""
        
        event_details = {
            "description": description,
            "severity": severity,
            **(additional_details or {})
        }
        
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=str(uuid.uuid4()),
            event_type="SECURITY_EVENT",
            user_id=user_id,
            session_id=None,
            operation=event_type,
            resource="SECURITY",
            details=event_details,
            compliance_context={"security_incident": True},
            risk_level=severity,
            data_classification="SECURITY",
            retention_period=self.retention_days
        )
        
        self._write_audit_log(audit_entry)
    
    def _build_compliance_context(self, operation: str, data_classification: str, 
                                entity_types: List[str]) -> Dict[str, Any]:
        """Build compliance context based on standards"""
        context = {}
        
        for standard in self.compliance_standards:
            if standard == ComplianceStandard.GDPR:
                context["gdpr"] = {
                    "lawful_basis_required": True,
                    "data_subject_rights_applicable": True,
                    "special_category_data": any(
                        et in ["HEALTH_DATA", "BIOMETRIC_DATA", "GENETIC_DATA"] 
                        for et in entity_types
                    ),
                    "cross_border_transfer": False  # Set based on actual context
                }
            
            elif standard == ComplianceStandard.HIPAA:
                context["hipaa"] = {
                    "phi_processed": any(
                        et in ["MEDICAL_RECORD", "PATIENT_ID", "HEALTH_PLAN_ID"] 
                        for et in entity_types
                    ),
                    "minimum_necessary_standard": True,
                    "safe_harbor_method": operation == "redaction"
                }
            
            elif standard == ComplianceStandard.PCI_DSS:
                context["pci_dss"] = {
                    "cardholder_data": "CREDIT_CARD" in entity_types,
                    "encryption_required": True,
                    "access_logged": True
                }
        
        return context
    
    def _assess_risk_level(self, entities_found: int, entity_types: List[str]) -> str:
        """Assess risk level based on entities found"""
        high_risk_entities = {
            "SSN", "CREDIT_CARD", "MEDICAL_RECORD", "PASSPORT", 
            "BANK_ACCOUNT", "HEALTH_PLAN_ID"
        }
        
        if any(et in high_risk_entities for et in entity_types):
            return "HIGH"
        elif entities_found > 10:
            return "MEDIUM"
        elif entities_found > 0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_retention_period(self, data_classification: str) -> int:
        """Get retention period based on data classification"""
        retention_map = {
            "PUBLIC": 365,      # 1 year
            "INTERNAL": 1095,   # 3 years
            "SENSITIVE": 2555,  # 7 years
            "RESTRICTED": 2555, # 7 years
            "SECURITY": 2555,   # 7 years
            "SYSTEM": 365       # 1 year
        }
        return retention_map.get(data_classification, self.retention_days)
    
    def _write_audit_log(self, audit_entry: AuditLogEntry):
        """Write audit entry to secure log"""
        try:
            log_data = json.dumps(audit_entry.to_dict(), ensure_ascii=False)
            
            if self.encryption_enabled:
                encrypted_data = self.fernet.encrypt(log_data.encode('utf-8'))
                log_message = f"ENCRYPTED:{encrypted_data.hex()}"
            else:
                log_message = log_data
            
            self.logger.info(log_message)
            
        except Exception as e:
            # Fallback logging - critical for audit trail
            fallback_entry = {
                "timestamp": audit_entry.timestamp,
                "event_id": audit_entry.event_id,
                "error": f"Failed to write audit log: {str(e)}",
                "original_operation": audit_entry.operation
            }
            self.logger.error(json.dumps(fallback_entry))
    
    def query_audit_logs(self, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        event_type: Optional[str] = None,
                        user_id: Optional[str] = None,
                        risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        # This is a simplified implementation
        # In production, use a proper database for efficient querying
        
        results = []
        log_files = list(self.log_directory.glob("audit_*.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            # Parse log entry
                            if line.startswith("ENCRYPTED:"):
                                if not self.encryption_enabled:
                                    continue
                                encrypted_hex = line[10:].strip()
                                encrypted_data = bytes.fromhex(encrypted_hex)
                                decrypted_data = self.fernet.decrypt(encrypted_data)
                                log_data = json.loads(decrypted_data.decode('utf-8'))
                            else:
                                # Parse regular JSON log
                                start = line.find('{')
                                if start == -1:
                                    continue
                                log_data = json.loads(line[start:])
                            
                            # Apply filters
                            if start_date and datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00')) < start_date:
                                continue
                            if end_date and datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00')) > end_date:
                                continue
                            if event_type and log_data.get('event_type') != event_type:
                                continue
                            if user_id and log_data.get('user_id') != user_id:
                                continue
                            if risk_level and log_data.get('risk_level') != risk_level:
                                continue
                            
                            results.append(log_data)
                            
                        except (json.JSONDecodeError, ValueError):
                            continue
                            
            except Exception as e:
                logging.error(f"Error reading audit log {log_file}: {e}")
                continue
        
        return results
    
    def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policies"""
        current_time = datetime.now()
        
        for log_file in self.log_directory.glob("audit_*.log"):
            try:
                # Extract date from filename
                date_str = log_file.stem.split('_')[1]
                log_date = datetime.strptime(date_str, '%Y%m%d')
                
                # Check if log is older than retention period
                age_days = (current_time - log_date).days
                
                if age_days > self.retention_days:
                    log_file.unlink()
                    logging.info(f"Deleted old audit log: {log_file}")
                    
            except (ValueError, IndexError) as e:
                logging.warning(f"Could not parse log file date {log_file}: {e}")
                continue

class ComplianceValidator:
    """Validate operations against compliance requirements"""
    
    def __init__(self, standards: List[ComplianceStandard]):
        self.standards = standards
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules for each compliance standard"""
        rules = {}
        
        if ComplianceStandard.GDPR in self.standards:
            rules["GDPR"] = {
                "data_minimization": True,
                "purpose_limitation": True,
                "storage_limitation": True,
                "accuracy_requirement": True,
                "lawful_basis_required": True,
                "consent_management": True,
                "right_to_erasure": True,
                "data_portability": True,
                "privacy_by_design": True
            }
        
        if ComplianceStandard.HIPAA in self.standards:
            rules["HIPAA"] = {
                "minimum_necessary": True,
                "administrative_safeguards": True,
                "physical_safeguards": True,
                "technical_safeguards": True,
                "breach_notification": True,
                "business_associate_agreements": True
            }
        
        if ComplianceStandard.PCI_DSS in self.standards:
            rules["PCI_DSS"] = {
                "secure_network": True,
                "protect_cardholder_data": True,
                "vulnerability_management": True,
                "access_control": True,
                "monitoring": True,
                "information_security_policy": True
            }
        
        return rules
    
    def validate_redaction_request(self, 
                                 request_data: Dict[str, Any],
                                 user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate redaction request against compliance requirements"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": []
        }
        
        for standard_name, rules in self.validation_rules.items():
            standard_result = self._validate_against_standard(
                standard_name, rules, request_data, user_context
            )
            
            if not standard_result["compliant"]:
                validation_result["compliant"] = False
                validation_result["violations"].extend(standard_result["violations"])
            
            validation_result["recommendations"].extend(standard_result["recommendations"])
            validation_result["required_actions"].extend(standard_result["required_actions"])
        
        return validation_result
    
    def _validate_against_standard(self, 
                                 standard: str,
                                 rules: Dict[str, Any],
                                 request_data: Dict[str, Any],
                                 user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against specific compliance standard"""
        result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": []
        }
        
        if standard == "GDPR":
            result.update(self._validate_gdpr(rules, request_data, user_context))
        elif standard == "HIPAA":
            result.update(self._validate_hipaa(rules, request_data, user_context))
        elif standard == "PCI_DSS":
            result.update(self._validate_pci_dss(rules, request_data, user_context))
        
        return result
    
    def _validate_gdpr(self, rules: Dict[str, Any], 
                      request_data: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against GDPR requirements"""
        violations = []
        recommendations = []
        required_actions = []
        
        # Check lawful basis
        if rules.get("lawful_basis_required") and not user_context.get("lawful_basis"):
            violations.append("GDPR: Lawful basis for processing not specified")
            required_actions.append("Specify lawful basis under Article 6 GDPR")
        
        # Check data subject consent
        if user_context.get("lawful_basis") == "consent" and not user_context.get("consent_obtained"):
            violations.append("GDPR: Valid consent not obtained")
            required_actions.append("Obtain explicit consent from data subject")
        
        # Check purpose limitation
        if rules.get("purpose_limitation") and not request_data.get("processing_purpose"):
            recommendations.append("GDPR: Specify purpose for data processing")
        
        # Check data minimization
        if rules.get("data_minimization"):
            recommendations.append("GDPR: Ensure only necessary data is processed")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations,
            "required_actions": required_actions
        }
    
    def _validate_hipaa(self, rules: Dict[str, Any],
                       request_data: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against HIPAA requirements"""
        violations = []
        recommendations = []
        required_actions = []
        
        # Check if PHI is involved
        entity_types = request_data.get("entity_types", [])
        phi_entities = ["MEDICAL_RECORD", "PATIENT_ID", "HEALTH_PLAN_ID", "DEA_NUMBER"]
        
        if any(et in phi_entities for et in entity_types):
            # Check authorization
            if not user_context.get("authorized_user"):
                violations.append("HIPAA: Unauthorized access to PHI")
                required_actions.append("Verify user authorization for PHI access")
            
            # Check minimum necessary
            if rules.get("minimum_necessary") and not user_context.get("minimum_necessary_justified"):
                recommendations.append("HIPAA: Justify minimum necessary standard")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations,
            "required_actions": required_actions
        }
    
    def _validate_pci_dss(self, rules: Dict[str, Any],
                         request_data: Dict[str, Any],
                         user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against PCI DSS requirements"""
        violations = []
        recommendations = []
        required_actions = []
        
        # Check if cardholder data is involved
        entity_types = request_data.get("entity_types", [])
        
        if "CREDIT_CARD" in entity_types:
            # Check secure processing
            if not user_context.get("secure_environment"):
                violations.append("PCI DSS: Cardholder data not processed in secure environment")
                required_actions.append("Ensure PCI DSS compliant environment")
            
            # Check access controls
            if not user_context.get("access_controls_verified"):
                recommendations.append("PCI DSS: Verify access controls for cardholder data")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations,
            "required_actions": required_actions
        }

class ZeroTrustValidator:
    """Zero Trust security validation"""
    
    def __init__(self):
        self.trust_factors = [
            "user_identity",
            "device_security",
            "network_location",
            "data_classification", 
            "request_context",
            "behavioral_analysis"
        ]
    
    def validate_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request using Zero Trust principles"""
        trust_score = 0
        max_score = len(self.trust_factors) * 10
        
        validation_details = {}
        
        # User Identity (0-10 points)
        user_score = self._validate_user_identity(request_context)
        trust_score += user_score
        validation_details["user_identity"] = user_score
        
        # Device Security (0-10 points)
        device_score = self._validate_device_security(request_context)
        trust_score += device_score
        validation_details["device_security"] = device_score
        
        # Network Location (0-10 points)
        network_score = self._validate_network_location(request_context)
        trust_score += network_score
        validation_details["network_location"] = network_score
        
        # Data Classification (0-10 points)
        data_score = self._validate_data_classification(request_context)
        trust_score += data_score
        validation_details["data_classification"] = data_score
        
        # Request Context (0-10 points)
        context_score = self._validate_request_context(request_context)
        trust_score += context_score
        validation_details["request_context"] = context_score
        
        # Behavioral Analysis (0-10 points)
        behavior_score = self._validate_behavioral_patterns(request_context)
        trust_score += behavior_score
        validation_details["behavioral_analysis"] = behavior_score
        
        trust_percentage = (trust_score / max_score) * 100
        
        return {
            "trust_score": trust_percentage,
            "trusted": trust_percentage >= 70,  # Threshold for trusted requests
            "details": validation_details,
            "recommendations": self._get_security_recommendations(trust_percentage, validation_details)
        }
    
    def _validate_user_identity(self, context: Dict[str, Any]) -> int:
        """Validate user identity factors"""
        score = 0
        
        if context.get("user_authenticated"):
            score += 3
        if context.get("mfa_verified"):
            score += 4
        if context.get("certificate_based_auth"):
            score += 3
        
        return min(score, 10)
    
    def _validate_device_security(self, context: Dict[str, Any]) -> int:
        """Validate device security posture"""
        score = 0
        
        if context.get("device_managed"):
            score += 3
        if context.get("device_encrypted"):
            score += 2
        if context.get("antivirus_updated"):
            score += 2
        if context.get("os_patched"):
            score += 3
        
        return min(score, 10)
    
    def _validate_network_location(self, context: Dict[str, Any]) -> int:
        """Validate network security"""
        score = 0
        
        if context.get("internal_network"):
            score += 4
        elif context.get("vpn_connection"):
            score += 3
        
        if context.get("geo_location_verified"):
            score += 3
        if context.get("known_ip_address"):
            score += 3
        
        return min(score, 10)
    
    def _validate_data_classification(self, context: Dict[str, Any]) -> int:
        """Validate data classification handling"""
        score = 0
        
        data_class = context.get("data_classification", "UNKNOWN")
        
        if data_class == "PUBLIC":
            score += 10
        elif data_class == "INTERNAL":
            score += 8
        elif data_class == "SENSITIVE":
            score += 6
        elif data_class == "RESTRICTED":
            score += 4
        
        return score
    
    def _validate_request_context(self, context: Dict[str, Any]) -> int:
        """Validate request context"""
        score = 0
        
        if context.get("business_hours"):
            score += 3
        if context.get("authorized_application"):
            score += 4
        if context.get("rate_limit_compliant"):
            score += 3
        
        return min(score, 10)
    
    def _validate_behavioral_patterns(self, context: Dict[str, Any]) -> int:
        """Validate behavioral patterns"""
        score = 5  # Base score
        
        if context.get("unusual_access_pattern"):
            score -= 3
        if context.get("suspicious_volume"):
            score -= 2
        if context.get("anomalous_timing"):
            score -= 2
        
        return max(score, 0)
    
    def _get_security_recommendations(self, trust_score: float, 
                                    details: Dict[str, Any]) -> List[str]:
        """Get security recommendations based on trust score"""
        recommendations = []
        
        if trust_score < 50:
            recommendations.append("DENY: Trust score too low for sensitive operations")
        elif trust_score < 70:
            recommendations.append("ADDITIONAL_VERIFICATION: Require additional authentication")
        
        if details.get("user_identity", 0) < 7:
            recommendations.append("STRENGTHEN_AUTH: Implement stronger authentication")
        
        if details.get("device_security", 0) < 6:
            recommendations.append("DEVICE_SECURITY: Improve device security posture")
        
        if details.get("network_location", 0) < 5:
            recommendations.append("NETWORK_SECURITY: Use secure network connection")
        
        return recommendations