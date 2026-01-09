"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - SECURITY CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: config/security.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

██╗    ██╗ █████╗ ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
██║    ██║██╔══██╗██╔══██╗████╗  ██║██║████╗  ██║██╔════╝ 
██║ █╗ ██║███████║██████╔╝██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══██║██╔══██╗██║╚██╗██║██║██║╚██╗██║██║   ██║
╚███╔███╔╝██║  ██║██║  ██║██║ ╚████║██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 

THIS FILE CONTAINS SENSITIVE SECURITY CREDENTIALS AND KEYS.

SECURITY REQUIREMENTS:
1. Set file permissions to 600 (owner read/write only)
2. Never commit this file to version control with real credentials
3. Rotate encryption keys periodically
4. Audit access to this file
5. Restrict physical access to machines containing this file

PRODUCTION DEPLOYMENT:
- Replace all placeholder values with secure random values
- Use environment variables for highly sensitive data
- Consider using a secrets manager

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import secrets
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64

# Try to import cryptography, fall back to basic implementation if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("WARNING: cryptography library not installed. Using fallback encryption.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: ENCRYPTION KEYS
# ═══════════════════════════════════════════════════════════════════════════════
# CRITICAL: Change these keys before production deployment!

# Database encryption key (32 bytes, base64 encoded)
# Generate new key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
DATABASE_ENCRYPTION_KEY: str = os.environ.get(
    "BSS_DB_KEY",
    "CHANGE_THIS_KEY_BEFORE_PRODUCTION_USE_GENERATE_FERNET_KEY"  # PLACEHOLDER
)

# Salt for password hashing (at least 16 bytes)
# Generate new salt: python -c "import secrets; print(secrets.token_hex(16))"
PASSWORD_SALT: str = os.environ.get(
    "BSS_PASSWORD_SALT",
    "b0rd3r_s3cur1ty_s4lt_2026"  # PLACEHOLDER - Change in production
)

# Session secret key for web application
# Generate new key: python -c "import secrets; print(secrets.token_hex(32))"
SESSION_SECRET_KEY: str = os.environ.get(
    "BSS_SESSION_KEY",
    "change_this_session_secret_key_in_production_deployment"  # PLACEHOLDER
)

# API key for internal services (if any)
INTERNAL_API_KEY: str = os.environ.get(
    "BSS_API_KEY",
    "internal_api_key_change_before_deployment"  # PLACEHOLDER
)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DEFAULT USERS
# ═══════════════════════════════════════════════════════════════════════════════
# Default administrator account (change password immediately after setup)
# In production, use proper user management, not hardcoded users

DEFAULT_USERS: List[Dict[str, Any]] = [
    {
        "username": "admin",
        "password_hash": None,  # Will be set during initialization
        "default_password": "ChangeOnFirstLogin!2026",  # CHANGE IMMEDIATELY
        "role": "admin",
        "force_password_change": True,
        "created_date": "2026-01-02",
        "active": True,
        "name": "System Administrator",
    },
    {
        "username": "operator",
        "password_hash": None,
        "default_password": "OperatorPassword!2026",  # CHANGE IMMEDIATELY
        "role": "operator",
        "force_password_change": True,
        "created_date": "2026-01-02",
        "active": True,
        "name": "Default Operator",
    },
    {
        "username": "supervisor",
        "password_hash": None,
        "default_password": "SupervisorPassword!2026",  # CHANGE IMMEDIATELY
        "role": "supervisor",
        "force_password_change": True,
        "created_date": "2026-01-02",
        "active": True,
        "name": "Duty Supervisor",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: ROLE-BASED ACCESS CONTROL (RBAC)
# ═══════════════════════════════════════════════════════════════════════════════
# Define what each role can do

ROLES: Dict[str, Dict[str, Any]] = {
    "admin": {
        "display_name": "Administrator",
        "level": 3,
        "permissions": [
            "view_dashboard",
            "view_alerts",
            "acknowledge_alerts",
            "dispatch_patrol",
            "view_map",
            "upload_video",
            "process_video",
            "view_reports",
            "export_reports",
            "manage_users",
            "view_audit_log",
            "change_settings",
            "backup_database",
            "restore_database",
            "view_all_logs",
        ],
        "can_modify_settings": True,
        "can_manage_users": True,
    },
    "supervisor": {
        "display_name": "Supervisor",
        "level": 2,
        "permissions": [
            "view_dashboard",
            "view_alerts",
            "acknowledge_alerts",
            "dispatch_patrol",
            "view_map",
            "upload_video",
            "process_video",
            "view_reports",
            "export_reports",
            "view_audit_log",
        ],
        "can_modify_settings": False,
        "can_manage_users": False,
    },
    "operator": {
        "display_name": "Operator",
        "level": 1,
        "permissions": [
            "view_dashboard",
            "view_alerts",
            "acknowledge_alerts",
            "view_map",
            "upload_video",
            "process_video",
            "view_reports",
        ],
        "can_modify_settings": False,
        "can_manage_users": False,
    },
    "readonly": {
        "display_name": "Read Only",
        "level": 0,
        "permissions": [
            "view_dashboard",
            "view_alerts",
            "view_map",
            "view_reports",
        ],
        "can_modify_settings": False,
        "can_manage_users": False,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: PASSWORD POLICY
# ═══════════════════════════════════════════════════════════════════════════════
# Strong password requirements for military-grade security

PASSWORD_POLICY: Dict[str, Any] = {
    "min_length": 12,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "special_characters": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "password_history": 5,      # Cannot reuse last 5 passwords
    "max_age_days": 90,         # Force change every 90 days
    "min_age_days": 1,          # Cannot change more than once per day
    "lockout_threshold": 3,     # Failed attempts before lockout
    "lockout_duration_minutes": 15,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

SESSION_CONFIG: Dict[str, Any] = {
    "timeout_minutes": 30,          # Idle timeout
    "absolute_timeout_hours": 8,    # Maximum session duration
    "extend_on_activity": True,     # Reset timeout on activity
    "single_session": True,         # Only one session per user
    "secure_cookie": True,          # HTTPS only (if applicable)
    "http_only": True,              # No JavaScript access to cookie
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: SECURITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_encryption_key() -> bytes:
    """
    Generate a new Fernet encryption key.
    
    Returns:
        bytes: A new encryption key
        
    Example:
        >>> key = generate_encryption_key()
        >>> print(key)
        b'abc123...'
    
    SECURITY NOTE:
        Store generated keys securely. Never log or print in production.
    """
    if CRYPTOGRAPHY_AVAILABLE:
        return Fernet.generate_key()
    else:
        # Fallback: Generate 32 random bytes, base64 encode
        return base64.urlsafe_b64encode(secrets.token_bytes(32))


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password (str): The password to derive key from
        salt (bytes, optional): Salt for key derivation. If None, uses default.
        
    Returns:
        bytes: Derived encryption key
        
    SECURITY NOTE:
        Use a unique salt for each key derivation in production.
    """
    if salt is None:
        salt = PASSWORD_SALT.encode()
    
    if CRYPTOGRAPHY_AVAILABLE:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # High iteration count for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    else:
        # Fallback using hashlib
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            iterations=480000,
            dklen=32
        )
        return base64.urlsafe_b64encode(key)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt (or fallback to SHA-256 if bcrypt unavailable).
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password (bcrypt format or SHA-256 hex)
        
    Example:
        >>> hashed = hash_password("MySecurePassword123!")
        >>> print(hashed)
        '$2b$12$...'
        
    SECURITY NOTE:
        bcrypt is preferred. Fallback is less secure but functional.
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)  # High work factor
        return bcrypt.hashpw(password.encode(), salt).decode()
    except ImportError:
        # Fallback to SHA-256 with salt (less secure than bcrypt)
        salted = f"{PASSWORD_SALT}{password}".encode()
        return hashlib.sha256(salted).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): Plain text password to verify
        password_hash (str): Stored password hash
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MyPassword123!")
        >>> verify_password("MyPassword123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ImportError:
        # Fallback verification
        salted = f"{PASSWORD_SALT}{password}".encode()
        return hashlib.sha256(salted).hexdigest() == password_hash


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password against security policy.
    
    Args:
        password (str): Password to validate
        
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of error messages)
        
    Example:
        >>> result = validate_password_strength("weak")
        >>> result['valid']
        False
        >>> result['errors']
        ['Password must be at least 12 characters', ...]
    """
    errors = []
    policy = PASSWORD_POLICY
    
    # Length check
    if len(password) < policy["min_length"]:
        errors.append(f"Password must be at least {policy['min_length']} characters")
    
    if len(password) > policy["max_length"]:
        errors.append(f"Password must be at most {policy['max_length']} characters")
    
    # Character requirements
    if policy["require_uppercase"] and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if policy["require_lowercase"] and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if policy["require_digit"] and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if policy["require_special"]:
        special = policy["special_characters"]
        if not any(c in special for c in password):
            errors.append(f"Password must contain at least one special character ({special})")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": calculate_password_strength(password),
    }


def calculate_password_strength(password: str) -> int:
    """
    Calculate password strength score (0-100).
    
    Args:
        password (str): Password to evaluate
        
    Returns:
        int: Strength score (0=very weak, 100=very strong)
    """
    score = 0
    
    # Length contribution (up to 30 points)
    score += min(30, len(password) * 2)
    
    # Character variety (up to 40 points)
    if any(c.isupper() for c in password):
        score += 10
    if any(c.islower() for c in password):
        score += 10
    if any(c.isdigit() for c in password):
        score += 10
    if any(c in PASSWORD_POLICY["special_characters"] for c in password):
        score += 10
    
    # Unique characters (up to 30 points)
    unique_ratio = len(set(password)) / len(password) if password else 0
    score += int(unique_ratio * 30)
    
    return min(100, score)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length (int): Number of bytes (resulting hex string is 2x this)
        
    Returns:
        str: Secure random hex string
        
    Example:
        >>> token = generate_secure_token()
        >>> len(token)
        64
    """
    return secrets.token_hex(length)


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        user_role (str): Role name (admin, supervisor, operator, readonly)
        permission (str): Permission to check
        
    Returns:
        bool: True if role has permission
        
    Example:
        >>> has_permission('admin', 'manage_users')
        True
        >>> has_permission('operator', 'manage_users')
        False
    """
    role_config = ROLES.get(user_role, {})
    permissions = role_config.get("permissions", [])
    return permission in permissions


def get_role_level(user_role: str) -> int:
    """
    Get the privilege level of a role.
    
    Args:
        user_role (str): Role name
        
    Returns:
        int: Privilege level (higher = more privileges)
    """
    return ROLES.get(user_role, {}).get("level", 0)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: AUDIT LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
# Security-related audit events

AUDIT_EVENTS: Dict[str, str] = {
    "LOGIN_SUCCESS": "User logged in successfully",
    "LOGIN_FAILED": "Failed login attempt",
    "LOGIN_LOCKED": "Account locked due to failed attempts",
    "LOGOUT": "User logged out",
    "PASSWORD_CHANGED": "Password was changed",
    "PASSWORD_RESET": "Password was reset by administrator",
    "USER_CREATED": "New user account created",
    "USER_MODIFIED": "User account modified",
    "USER_DELETED": "User account deleted",
    "PERMISSION_DENIED": "Access denied to protected resource",
    "SETTINGS_CHANGED": "System settings were modified",
    "DATA_EXPORTED": "Data was exported from system",
    "DATABASE_BACKUP": "Database backup created",
    "DATABASE_RESTORE": "Database restored from backup",
    "ALERT_ACKNOWLEDGED": "Alert was acknowledged",
    "PATROL_DISPATCHED": "Patrol unit dispatched",
    "VIDEO_UPLOADED": "Surveillance video uploaded",
    "VIDEO_PROCESSED": "Video processing completed",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_default_users() -> List[Dict[str, Any]]:
    """
    Initialize default users with hashed passwords.
    
    Returns:
        List of user dictionaries with hashed passwords
        
    SECURITY NOTE:
        Run this only during initial setup. In production, manage users
        through the admin interface.
    """
    initialized_users = []
    
    for user in DEFAULT_USERS:
        user_copy = user.copy()
        if user_copy.get("default_password"):
            user_copy["password_hash"] = hash_password(user_copy["default_password"])
            del user_copy["default_password"]  # Don't store plain password
        initialized_users.append(user_copy)
    
    return initialized_users


def check_security_configuration() -> List[str]:
    """
    Check security configuration for issues.
    
    Returns:
        List of warning messages (empty if all OK)
    """
    warnings = []
    
    # Check for placeholder keys
    if "CHANGE_THIS" in DATABASE_ENCRYPTION_KEY:
        warnings.append("DATABASE_ENCRYPTION_KEY contains placeholder - CHANGE BEFORE PRODUCTION")
    
    if "change_this" in SESSION_SECRET_KEY.lower():
        warnings.append("SESSION_SECRET_KEY contains placeholder - CHANGE BEFORE PRODUCTION")
    
    if "change_before" in INTERNAL_API_KEY.lower():
        warnings.append("INTERNAL_API_KEY contains placeholder - CHANGE BEFORE PRODUCTION")
    
    # Check password salt
    if "placeholder" in PASSWORD_SALT.lower() or len(PASSWORD_SALT) < 16:
        warnings.append("PASSWORD_SALT should be a unique random value of at least 16 characters")
    
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# RUN SECURITY CHECK ON IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("SECURITY CONFIGURATION CHECK")
    print("=" * 70)
    
    warnings = check_security_configuration()
    
    if warnings:
        print("\n⚠️  SECURITY WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\n⚠️  FIX THESE ISSUES BEFORE PRODUCTION DEPLOYMENT")
    else:
        print("\n✓ Security configuration appears valid")
    
    print("\n" + "=" * 70)
    
    # Test password functions
    print("\nTesting password functions:")
    test_password = "TestPassword123!"
    hashed = hash_password(test_password)
    print(f"  Password hashing: {'PASS' if hashed else 'FAIL'}")
    print(f"  Password verification: {'PASS' if verify_password(test_password, hashed) else 'FAIL'}")
    
    # Test validation
    result = validate_password_strength("weak")
    print(f"  Weak password rejected: {'PASS' if not result['valid'] else 'FAIL'}")
    
    result = validate_password_strength("StrongPassword123!")
    print(f"  Strong password accepted: {'PASS' if result['valid'] else 'FAIL'}")
    
    print("\n" + "=" * 70)
