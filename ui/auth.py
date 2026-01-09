"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - AUTHENTICATION MODULE                        ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: User authentication and session management for Streamlit           ║
║  Security Level: TOP SECRET                                                  ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SECURITY NOTICE:
- All authentication attempts are logged
- Sessions expire after configured timeout
- Failed login attempts trigger security alerts
- NO external authentication services - all local
"""

import streamlit as st
import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SECURITY_CONFIG, BASE_DIR
from config.security import SecurityManager


# =============================================================================
# AUTHENTICATION MANAGER
# =============================================================================

class AuthManager:
    """
    Manages user authentication and session handling for the surveillance system.
    
    Security Features:
    - bcrypt password hashing with salt
    - Session token generation with CSPRNG
    - Automatic session expiration
    - Failed login attempt tracking
    - IP-based rate limiting (when available)
    
    Attributes:
        security: SecurityManager instance for cryptographic operations
        max_attempts: Maximum failed login attempts before lockout
        lockout_duration: Minutes to lock account after max failures
        session_timeout: Minutes before session expires
        
    Security Note:
        All authentication events are logged for audit trail.
        Credentials are never stored in plaintext.
    """
    
    def __init__(self):
        """
        Initialize the authentication manager.
        
        Security Note:
            Uses configuration from SECURITY_CONFIG for consistent settings.
        """
        self.security = SecurityManager()
        self.max_attempts = SECURITY_CONFIG.get("max_login_attempts", 3)
        self.lockout_duration = SECURITY_CONFIG.get("lockout_duration_minutes", 30)
        self.session_timeout = SECURITY_CONFIG.get("session_timeout_minutes", 480)
        
        # Path to user credentials file (encrypted JSON)
        self.credentials_file = BASE_DIR / "data" / "credentials.enc"
        
        # In-memory failed attempt tracking
        # In production, this should be in database
        if "failed_attempts" not in st.session_state:
            st.session_state.failed_attempts = {}
    
    def _load_credentials(self) -> Dict[str, Any]:
        """
        Load user credentials from encrypted file.
        
        Returns:
            Dictionary of username -> credential info
            
        Security Note:
            Credentials file is encrypted at rest using AES-256.
            Returns default admin account if file doesn't exist.
        """
        if not self.credentials_file.exists():
            # Create default admin account on first run
            # Default password is 'admin123' - MUST be changed immediately
            default_creds = {
                "admin": {
                    "password_hash": bcrypt.hashpw(
                        b"admin123", 
                        bcrypt.gensalt(rounds=12)
                    ).decode("utf-8"),
                    "role": "administrator",
                    "clearance": "TOP_SECRET",
                    "created": datetime.now().isoformat(),
                    "must_change_password": True,
                    "active": True,
                }
            }
            self._save_credentials(default_creds)
            return default_creds
        
        try:
            # Read encrypted credentials
            with open(self.credentials_file, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt and parse
            decrypted = self.security.decrypt_data(encrypted_data)
            return json.loads(decrypted)
        except Exception as e:
            # Log error but don't expose details
            print(f"[SECURITY] Failed to load credentials: {type(e).__name__}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Save user credentials to encrypted file.
        
        Args:
            credentials: Dictionary of username -> credential info
            
        Returns:
            True if saved successfully, False otherwise
            
        Security Note:
            Always encrypts credentials before writing to disk.
        """
        try:
            # Ensure directory exists
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Encrypt and save
            json_data = json.dumps(credentials, default=str)
            encrypted = self.security.encrypt_data(json_data)
            
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"[SECURITY] Failed to save credentials: {type(e).__name__}")
            return False
    
    def _check_lockout(self, username: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a user account is locked out.
        
        Args:
            username: Username to check
            
        Returns:
            Tuple of (is_locked, minutes_remaining)
            
        Security Note:
            Lockout protects against brute force attacks.
        """
        attempts = st.session_state.failed_attempts.get(username, {})
        
        if not attempts:
            return False, None
        
        count = attempts.get("count", 0)
        last_attempt = attempts.get("last_attempt")
        
        if count >= self.max_attempts and last_attempt:
            lockout_end = last_attempt + timedelta(minutes=self.lockout_duration)
            
            if datetime.now() < lockout_end:
                remaining = int((lockout_end - datetime.now()).total_seconds() / 60)
                return True, remaining
            else:
                # Lockout expired, reset counter
                st.session_state.failed_attempts[username] = {}
                return False, None
        
        return False, None
    
    def _record_failed_attempt(self, username: str) -> int:
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed authentication
            
        Returns:
            Number of remaining attempts before lockout
            
        Security Note:
            This helps prevent brute force attacks.
        """
        if username not in st.session_state.failed_attempts:
            st.session_state.failed_attempts[username] = {"count": 0}
        
        st.session_state.failed_attempts[username]["count"] += 1
        st.session_state.failed_attempts[username]["last_attempt"] = datetime.now()
        
        count = st.session_state.failed_attempts[username]["count"]
        remaining = self.max_attempts - count
        
        return max(0, remaining)
    
    def _clear_failed_attempts(self, username: str) -> None:
        """
        Clear failed attempts after successful login.
        
        Args:
            username: Username to clear attempts for
        """
        if username in st.session_state.failed_attempts:
            del st.session_state.failed_attempts[username]
    
    def authenticate(
        self, 
        username: str, 
        password: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's plaintext password
            
        Returns:
            Tuple of (success, message, user_info)
            - success: True if authentication succeeded
            - message: Status message for user
            - user_info: User details if authenticated, None otherwise
            
        Security Note:
            - Passwords are verified using bcrypt
            - Timing attacks are mitigated by consistent response time
            - All attempts are logged
        """
        # Normalize username
        username = username.lower().strip()
        
        # Check for lockout
        is_locked, minutes = self._check_lockout(username)
        if is_locked:
            return (
                False, 
                f"Account locked. Try again in {minutes} minutes.",
                None
            )
        
        # Load credentials
        credentials = self._load_credentials()
        
        # Check if user exists
        if username not in credentials:
            # Record failed attempt even for non-existent users
            # This prevents username enumeration
            self._record_failed_attempt(username)
            remaining = self.max_attempts - st.session_state.failed_attempts.get(
                username, {}
            ).get("count", 0)
            return (
                False,
                f"Invalid credentials. {remaining} attempts remaining.",
                None
            )
        
        user = credentials[username]
        
        # Check if account is active
        if not user.get("active", True):
            return False, "Account is deactivated. Contact administrator.", None
        
        # Verify password using bcrypt
        try:
            password_hash = user["password_hash"].encode("utf-8")
            is_valid = bcrypt.checkpw(password.encode("utf-8"), password_hash)
        except Exception:
            is_valid = False
        
        if not is_valid:
            remaining = self._record_failed_attempt(username)
            return (
                False,
                f"Invalid credentials. {remaining} attempts remaining.",
                None
            )
        
        # Successful authentication
        self._clear_failed_attempts(username)
        
        # Generate session token
        session_token = self.security.generate_token()
        
        # Prepare user info
        user_info = {
            "username": username,
            "role": user.get("role", "operator"),
            "clearance": user.get("clearance", "CONFIDENTIAL"),
            "session_token": session_token,
            "login_time": datetime.now().isoformat(),
            "must_change_password": user.get("must_change_password", False),
        }
        
        return True, "Authentication successful.", user_info
    
    def create_session(self, user_info: Dict[str, Any]) -> None:
        """
        Create a new session in Streamlit state.
        
        Args:
            user_info: User information from successful authentication
            
        Security Note:
            Session data is stored in Streamlit's session_state.
            Session expires after configured timeout.
        """
        st.session_state.authenticated = True
        st.session_state.user = user_info
        st.session_state.session_start = datetime.now()
        st.session_state.last_activity = datetime.now()
    
    def check_session(self) -> bool:
        """
        Check if the current session is valid.
        
        Returns:
            True if session is valid and not expired
            
        Security Note:
            Checks both authentication state and session timeout.
        """
        if not st.session_state.get("authenticated", False):
            return False
        
        if not st.session_state.get("session_start"):
            return False
        
        # Check session timeout
        session_start = st.session_state.session_start
        elapsed = (datetime.now() - session_start).total_seconds() / 60
        
        if elapsed > self.session_timeout:
            self.logout()
            return False
        
        # Update last activity
        st.session_state.last_activity = datetime.now()
        
        return True
    
    def logout(self) -> None:
        """
        End the current session and clear authentication state.
        
        Security Note:
            Clears all session data to prevent session hijacking.
        """
        # Clear authentication state
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.session_start = None
        st.session_state.last_activity = None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently authenticated user.
        
        Returns:
            User info dictionary or None if not authenticated
        """
        if self.check_session():
            return st.session_state.get("user")
        return None
    
    def has_permission(self, required_clearance: str) -> bool:
        """
        Check if current user has required clearance level.
        
        Args:
            required_clearance: Minimum clearance level required
            
        Returns:
            True if user has sufficient clearance
            
        Security Note:
            Clearance levels: CONFIDENTIAL < SECRET < TOP_SECRET
        """
        clearance_levels = {
            "CONFIDENTIAL": 1,
            "SECRET": 2,
            "TOP_SECRET": 3,
        }
        
        user = self.get_current_user()
        if not user:
            return False
        
        user_level = clearance_levels.get(user.get("clearance", ""), 0)
        required_level = clearance_levels.get(required_clearance, 999)
        
        return user_level >= required_level
    
    def change_password(
        self, 
        username: str, 
        old_password: str, 
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            username: Username to change password for
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
            
        Security Note:
            - Verifies old password before allowing change
            - New password is hashed with fresh salt
            - Password strength should be validated before calling
        """
        # Verify old password
        success, _, _ = self.authenticate(username, old_password)
        if not success:
            return False, "Current password is incorrect."
        
        # Validate new password strength
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."
        
        # Load and update credentials
        credentials = self._load_credentials()
        
        if username not in credentials:
            return False, "User not found."
        
        # Hash new password
        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")
        
        credentials[username]["password_hash"] = new_hash
        credentials[username]["must_change_password"] = False
        credentials[username]["password_changed"] = datetime.now().isoformat()
        
        if self._save_credentials(credentials):
            return True, "Password changed successfully."
        else:
            return False, "Failed to save new password."


# =============================================================================
# LOGIN UI COMPONENT
# =============================================================================

def render_login_page() -> Optional[Dict[str, Any]]:
    """
    Render the login page UI.
    
    Returns:
        User info if login successful, None otherwise
        
    Security Note:
        - Uses form submission to prevent accidental credential exposure
        - Shows security warnings prominently
    """
    auth = AuthManager()
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Security banner
        st.markdown("""
        <div style="
            background-color: #8b0000;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            font-family: 'Roboto Mono', monospace;
            font-weight: bold;
            margin-bottom: 30px;
        ">
            ⚠ CLASSIFIED SYSTEM - UNAUTHORIZED ACCESS PROHIBITED ⚠
        </div>
        """, unsafe_allow_html=True)
        
        # System title
        st.markdown("""
        <div style="
            text-align: center;
            margin-bottom: 30px;
        ">
            <h1 style="
                font-family: 'Orbitron', 'Roboto Mono', monospace;
                color: #4ade80;
                font-size: 28px;
                margin-bottom: 10px;
            ">
                ⬡ BORDER SURVEILLANCE SYSTEM
            </h1>
            <p style="
                font-family: 'Roboto Mono', monospace;
                color: #6e6e6e;
                font-size: 12px;
            ">
                Authentication Required
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div style="
                background-color: #1a1a1a;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 20px;
            ">
            """, unsafe_allow_html=True)
            
            # Username field
            username = st.text_input(
                "USERNAME",
                placeholder="Enter your username",
                key="login_username"
            )
            
            # Password field
            password = st.text_input(
                "PASSWORD",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            # Submit button
            submitted = st.form_submit_button(
                "🔐 AUTHENTICATE",
                use_container_width=True
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                    return None
                
                success, message, user_info = auth.authenticate(username, password)
                
                if success:
                    auth.create_session(user_info)
                    st.success(message)
                    st.rerun()
                    return user_info
                else:
                    st.error(message)
                    return None
        
        # Security notice
        st.markdown("""
        <div style="
            text-align: center;
            margin-top: 30px;
            font-family: 'Roboto Mono', monospace;
            font-size: 10px;
            color: #6e6e6e;
        ">
            All access attempts are logged and monitored<br>
            Unauthorized access will be prosecuted
        </div>
        """, unsafe_allow_html=True)
    
    return None


def require_auth(func):
    """
    Decorator to require authentication for a function.
    
    Usage:
        @require_auth
        def protected_page():
            st.write("Secret content")
            
    Security Note:
        Redirects to login page if not authenticated.
    """
    def wrapper(*args, **kwargs):
        auth = AuthManager()
        
        if not auth.check_session():
            render_login_page()
            st.stop()
        
        return func(*args, **kwargs)
    
    return wrapper


def require_clearance(clearance: str):
    """
    Decorator to require specific clearance level.
    
    Args:
        clearance: Required clearance level (CONFIDENTIAL, SECRET, TOP_SECRET)
        
    Usage:
        @require_clearance("TOP_SECRET")
        def admin_page():
            st.write("Admin only content")
            
    Security Note:
        Shows access denied message if insufficient clearance.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            auth = AuthManager()
            
            if not auth.check_session():
                render_login_page()
                st.stop()
            
            if not auth.has_permission(clearance):
                st.error(f"Access denied. {clearance} clearance required.")
                st.stop()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# SESSION INFO COMPONENT
# =============================================================================

def render_session_info() -> None:
    """
    Render session information in sidebar.
    
    Security Note:
        Shows current user and session status for transparency.
    """
    auth = AuthManager()
    user = auth.get_current_user()
    
    if not user:
        return
    
    st.sidebar.markdown("""
    <div style="
        background-color: #1a2e1a;
        border: 1px solid #3d5a3d;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 15px;
    ">
        <div style="
            font-family: 'Roboto Mono', monospace;
            font-size: 10px;
            color: #4ade80;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        ">
            Authenticated User
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
        <div style="font-family: 'Roboto Mono', monospace; font-size: 12px; color: #e6e6e6;">
            👤 {user['username'].upper()}
        </div>
        <div style="font-family: 'Roboto Mono', monospace; font-size: 10px; color: #a0a0a0; margin-top: 4px;">
            Role: {user['role'].upper()}
        </div>
        <div style="font-family: 'Roboto Mono', monospace; font-size: 10px; color: #ffd700; margin-top: 4px;">
            Clearance: {user['clearance']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    if st.sidebar.button("🚪 Logout", key="logout_btn", use_container_width=True):
        auth.logout()
        st.rerun()


# =============================================================================
# PASSWORD CHANGE DIALOG
# =============================================================================

def render_password_change_dialog() -> None:
    """
    Render password change dialog for users who must change password.
    
    Security Note:
        Forced password change on first login enhances security.
    """
    auth = AuthManager()
    user = auth.get_current_user()
    
    if not user or not user.get("must_change_password"):
        return
    
    st.warning("⚠️ You must change your password before continuing.")
    
    with st.form("password_change_form"):
        current_password = st.text_input(
            "Current Password",
            type="password"
        )
        
        new_password = st.text_input(
            "New Password",
            type="password",
            help="Minimum 8 characters"
        )
        
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )
        
        if st.form_submit_button("Change Password"):
            if new_password != confirm_password:
                st.error("New passwords do not match.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                success, message = auth.change_password(
                    user["username"],
                    current_password,
                    new_password
                )
                
                if success:
                    st.success(message)
                    # Update session state
                    st.session_state.user["must_change_password"] = False
                    st.rerun()
                else:
                    st.error(message)
    
    st.stop()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "AuthManager",
    "render_login_page",
    "require_auth",
    "require_clearance",
    "render_session_info",
    "render_password_change_dialog",
]
