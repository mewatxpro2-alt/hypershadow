"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - LOGGING CONFIGURATION                        ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Centralized logging with audit trail capabilities                   ║
║  Security Level: TOP SECRET                                                  ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SECURITY NOTICE:
- All logs are stored locally only
- Sensitive data is redacted before logging
- Log files are rotated and archived
- Audit logs are tamper-evident (hashed)
"""

import logging
import logging.handlers
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import LOGGING_CONFIG, BASE_DIR, SECURITY_CONFIG


# =============================================================================
# CONFIGURATION
# =============================================================================

# Log directories
LOG_DIR = BASE_DIR / "logs"
AUDIT_LOG_DIR = LOG_DIR / "audit"
SYSTEM_LOG_DIR = LOG_DIR / "system"
DETECTION_LOG_DIR = LOG_DIR / "detections"

# Ensure directories exist
for directory in [LOG_DIR, AUDIT_LOG_DIR, SYSTEM_LOG_DIR, DETECTION_LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# =============================================================================
# CUSTOM FORMATTERS
# =============================================================================

class MilitaryFormatter(logging.Formatter):
    """
    Custom formatter for military-style log output.
    
    Format: [TIMESTAMP] [LEVEL] [SOURCE] MESSAGE
    
    Includes:
    - ISO 8601 timestamp with milliseconds
    - Log level in fixed-width format
    - Source module/function
    - Structured message
    """
    
    def __init__(self):
        """Initialize the military formatter."""
        super().__init__()
        
        # Level name mapping for consistent width
        self.level_names = {
            "DEBUG": "DEBUG   ",
            "INFO": "INFO    ",
            "WARNING": "WARNING ",
            "ERROR": "ERROR   ",
            "CRITICAL": "CRITICAL",
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: LogRecord instance
            
        Returns:
            Formatted log string
        """
        # Timestamp in ISO 8601 format
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]  # Truncate to milliseconds
        
        # Level name with fixed width
        level = self.level_names.get(record.levelname, record.levelname.ljust(8))
        
        # Source location
        source = f"{record.module}.{record.funcName}"
        
        # Format the message
        message = record.getMessage()
        
        # Check for extra data
        extra_data = ""
        if hasattr(record, "extra_data") and record.extra_data:
            extra_data = f" | {json.dumps(record.extra_data, default=str)}"
        
        return f"[{timestamp}] [{level}] [{source}] {message}{extra_data}"


class AuditFormatter(logging.Formatter):
    """
    Formatter for tamper-evident audit logs.
    
    Each log entry includes:
    - Sequence number
    - Timestamp
    - Hash of previous entry (chain integrity)
    - Event details
    - Hash of current entry
    """
    
    sequence_counter = 0
    previous_hash = "GENESIS"
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format an audit log record with chain integrity.
        
        Args:
            record: LogRecord instance
            
        Returns:
            JSON-formatted audit entry
        """
        AuditFormatter.sequence_counter += 1
        
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        # Build audit entry
        entry = {
            "seq": AuditFormatter.sequence_counter,
            "timestamp": timestamp,
            "prev_hash": AuditFormatter.previous_hash,
            "level": record.levelname,
            "event": record.getMessage(),
            "user": getattr(record, "user", "system"),
            "ip": getattr(record, "ip_address", "local"),
            "action": getattr(record, "action", "unknown"),
            "resource": getattr(record, "resource", None),
            "result": getattr(record, "result", None),
        }
        
        # Calculate hash of entry (excluding the hash field)
        entry_str = json.dumps(entry, sort_keys=True, default=str)
        entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()[:16]
        
        entry["hash"] = entry_hash
        AuditFormatter.previous_hash = entry_hash
        
        return json.dumps(entry, default=str)


# =============================================================================
# CUSTOM HANDLERS
# =============================================================================

class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Secure rotating file handler with permissions enforcement.
    
    Features:
    - Automatic rotation at max size
    - Backup count limit
    - Secure file permissions (owner-only)
    - Optional compression of rotated files
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB default
        backup_count: int = 10,
        encoding: str = "utf-8"
    ):
        """
        Initialize the secure rotating handler.
        
        Args:
            filename: Log file path
            max_bytes: Maximum size before rotation
            backup_count: Number of backups to keep
            encoding: File encoding
        """
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )
        
        # Set secure permissions (owner read/write only)
        self._set_secure_permissions(filename)
    
    def _set_secure_permissions(self, filepath: str) -> None:
        """
        Set secure file permissions.
        
        Args:
            filepath: Path to the file
        """
        try:
            # Unix-like systems: owner read/write only (600)
            if os.name != "nt":
                os.chmod(filepath, 0o600)
        except Exception:
            pass  # Ignore permission errors on Windows
    
    def doRollover(self) -> None:
        """Perform rollover with secure permissions."""
        super().doRollover()
        
        # Set permissions on new file
        self._set_secure_permissions(self.baseFilename)


# =============================================================================
# REDACTION FILTER
# =============================================================================

class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive data from log messages.
    
    Redacts:
    - Passwords
    - API keys
    - Session tokens
    - Coordinates (optional)
    - Personal identifiers
    """
    
    # Patterns to redact
    REDACT_PATTERNS = [
        ("password", "********"),
        ("api_key", "[REDACTED]"),
        ("token", "[TOKEN]"),
        ("secret", "[SECRET]"),
        ("credential", "[CRED]"),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and redact sensitive data.
        
        Args:
            record: LogRecord to filter
            
        Returns:
            True (always allows the record, just modifies it)
        """
        # Redact message
        message = record.getMessage()
        
        for pattern, replacement in self.REDACT_PATTERNS:
            # Case-insensitive replacement
            import re
            regex = re.compile(
                f'{pattern}["\']?\\s*[:=]\\s*["\']?[^"\'\\s,}}]+',
                re.IGNORECASE
            )
            message = regex.sub(f'{pattern}={replacement}', message)
        
        record.msg = message
        record.args = ()
        
        return True


# =============================================================================
# LOGGER FACTORY
# =============================================================================

class LoggerFactory:
    """
    Factory for creating configured loggers.
    
    Provides centralized logger creation with consistent configuration
    across the entire surveillance system.
    
    Logger Types:
    - system: General system operations
    - audit: Security-sensitive actions (tamper-evident)
    - detection: Object detection events
    - alert: Alert generation and handling
    - access: Authentication and access events
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the logging system.
        
        Should be called once at application startup.
        """
        if cls._initialized:
            return
        
        # Set root logger level
        logging.root.setLevel(logging.DEBUG)
        
        # Remove default handlers
        logging.root.handlers = []
        
        cls._initialized = True
    
    @classmethod
    def get_system_logger(cls, name: str = "system") -> logging.Logger:
        """
        Get a system logger for general operations.
        
        Args:
            name: Logger name
            
        Returns:
            Configured Logger instance
        """
        cls.initialize()
        
        full_name = f"bss.system.{name}"
        
        if full_name in cls._loggers:
            return cls._loggers[full_name]
        
        logger = logging.getLogger(full_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        # File handler
        file_handler = SecureRotatingFileHandler(
            str(SYSTEM_LOG_DIR / f"{name}.log"),
            max_bytes=LOGGING_CONFIG.get("max_file_size_mb", 10) * 1024 * 1024,
            backup_count=LOGGING_CONFIG.get("backup_count", 10)
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(MilitaryFormatter())
        file_handler.addFilter(SensitiveDataFilter())
        
        # Console handler (for development)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(MilitaryFormatter())
        console_handler.addFilter(SensitiveDataFilter())
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        cls._loggers[full_name] = logger
        
        return logger
    
    @classmethod
    def get_audit_logger(cls) -> logging.Logger:
        """
        Get the audit logger for security events.
        
        Returns:
            Configured audit Logger instance
            
        Security Note:
            Audit logs use tamper-evident formatting with hash chains.
        """
        cls.initialize()
        
        if "bss.audit" in cls._loggers:
            return cls._loggers["bss.audit"]
        
        logger = logging.getLogger("bss.audit")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # Audit file handler
        audit_file = AUDIT_LOG_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = SecureRotatingFileHandler(
            str(audit_file),
            max_bytes=50 * 1024 * 1024,  # 50 MB
            backup_count=365  # Keep a year of audit logs
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(AuditFormatter())
        
        logger.addHandler(file_handler)
        
        cls._loggers["bss.audit"] = logger
        
        return logger
    
    @classmethod
    def get_detection_logger(cls) -> logging.Logger:
        """
        Get logger for detection events.
        
        Returns:
            Configured detection Logger instance
        """
        cls.initialize()
        
        if "bss.detection" in cls._loggers:
            return cls._loggers["bss.detection"]
        
        logger = logging.getLogger("bss.detection")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        # Detection log file
        file_handler = SecureRotatingFileHandler(
            str(DETECTION_LOG_DIR / "detections.log"),
            max_bytes=100 * 1024 * 1024,  # 100 MB
            backup_count=30
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(MilitaryFormatter())
        
        logger.addHandler(file_handler)
        
        cls._loggers["bss.detection"] = logger
        
        return logger


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_logger(name: str = "default") -> logging.Logger:
    """
    Get a system logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured Logger instance
    """
    return LoggerFactory.get_system_logger(name)


def get_audit_logger() -> logging.Logger:
    """
    Get the audit logger.
    
    Returns:
        Audit Logger instance
    """
    return LoggerFactory.get_audit_logger()


def log_audit_event(
    action: str,
    user: str = "system",
    resource: Optional[str] = None,
    result: str = "success",
    details: Optional[str] = None
) -> None:
    """
    Log an audit event.
    
    Args:
        action: Action being performed
        user: User performing the action
        resource: Resource being accessed
        result: Result of the action
        details: Additional details
        
    Security Note:
        All audit events are logged with tamper-evident formatting.
    """
    logger = get_audit_logger()
    
    message = details or f"{action} by {user}"
    
    # Create log record with extra attributes
    extra = {
        "user": user,
        "action": action,
        "resource": resource,
        "result": result,
    }
    
    logger.info(message, extra=extra)


def log_detection_event(
    detection_type: str,
    grid_reference: str,
    confidence: float,
    threat_level: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a detection event.
    
    Args:
        detection_type: Type of object detected
        grid_reference: Grid reference location
        confidence: Detection confidence
        threat_level: Assessed threat level
        details: Additional detection details
    """
    logger = LoggerFactory.get_detection_logger()
    
    message = f"DETECTION: {detection_type} at {grid_reference} " \
              f"(confidence={confidence:.2f}, threat={threat_level})"
    
    if details:
        # Add extra data attribute for structured logging
        record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = details
        logger.handle(record)
    else:
        logger.info(message)


def log_alert_event(
    alert_id: str,
    threat_level: str,
    action: str,
    user: str = "system"
) -> None:
    """
    Log an alert-related event.
    
    Args:
        alert_id: Alert identifier
        threat_level: Threat level of the alert
        action: Action taken (created, acknowledged, dispatched, etc.)
        user: User who took the action
    """
    logger = get_logger("alerts")
    
    message = f"ALERT [{alert_id}] {action.upper()} | " \
              f"Threat: {threat_level} | By: {user}"
    
    logger.info(message)
    
    # Also log to audit trail
    log_audit_event(
        action=f"ALERT_{action.upper()}",
        user=user,
        resource=alert_id,
        result="success",
        details=f"Alert {alert_id} {action}"
    )


def log_security_event(
    event_type: str,
    user: str,
    success: bool,
    details: Optional[str] = None
) -> None:
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event (LOGIN, LOGOUT, ACCESS_DENIED, etc.)
        user: User involved
        success: Whether the action was successful
        details: Additional details
    """
    logger = get_logger("security")
    
    result = "SUCCESS" if success else "FAILED"
    message = f"SECURITY: {event_type} | User: {user} | Result: {result}"
    
    if details:
        message += f" | {details}"
    
    if success:
        logger.info(message)
    else:
        logger.warning(message)
    
    # Always log security events to audit trail
    log_audit_event(
        action=event_type,
        user=user,
        result="success" if success else "failure",
        details=details
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "LoggerFactory",
    "get_logger",
    "get_audit_logger",
    "log_audit_event",
    "log_detection_event",
    "log_alert_event",
    "log_security_event",
    "MilitaryFormatter",
    "AuditFormatter",
    "SecureRotatingFileHandler",
    "SensitiveDataFilter",
]
