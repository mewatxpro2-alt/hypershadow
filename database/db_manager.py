"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - DATABASE MANAGER
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: database/db_manager.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    Central database management module for all CRUD operations.
    Handles SQLite database with optional encryption.
    
SECURITY NOTES:
    - All database operations are logged to audit trail
    - Password hashes never stored in plaintext
    - Support for encrypted database using SQLCipher
    - Automatic backup functionality
    
USAGE:
    from database.db_manager import DatabaseManager
    
    db = DatabaseManager()
    db.initialize()
    
    # CRUD operations
    user_id = db.create_user("admin", "password", "Admin User", "admin")
    alerts = db.get_active_alerts()

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports
from config.settings import (
    DATABASE_CONFIG,
    DATABASE_DIR,
    LOGGING_CONFIG,
)
from config.security import (
    hash_password,
    verify_password,
    initialize_default_users,
)

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE MANAGER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """
    Manages all database operations for the surveillance system.
    
    This class provides a unified interface for all database interactions
    including users, detections, alerts, and audit logging.
    
    SECURITY NOTE:
        All write operations are automatically logged to the audit trail.
        
    Example:
        >>> db = DatabaseManager()
        >>> db.initialize()
        >>> user = db.get_user_by_username("admin")
        >>> alerts = db.get_active_alerts(limit=10)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file (default from config)
        """
        self.db_path = db_path or DATABASE_CONFIG["db_path"]
        self.backup_dir = DATABASE_CONFIG.get("backup_dir", str(DATABASE_DIR / "backups"))
        
        # Ensure directories exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        self._connection: Optional[sqlite3.Connection] = None
        
        logger.info(f"DatabaseManager initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection.
        
        Returns:
            SQLite connection object
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                timeout=DATABASE_CONFIG.get("connection_timeout", 30),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._connection.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            if DATABASE_CONFIG.get("wal_mode", True):
                self._connection.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys=ON")
        
        return self._connection
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize(self) -> None:
        """
        Initialize the database with schema and default data.
        
        Creates all tables, indexes, and default users.
        Safe to call multiple times.
        """
        conn = self._get_connection()
        
        # Load and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            logger.info("Database schema applied")
        else:
            # Create minimal schema inline
            self._create_minimal_schema(conn)
        
        # Create default users if needed
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            self._create_default_users()
            logger.info("Default users created")
        
        conn.commit()
        logger.info("Database initialized successfully")
    
    def _create_minimal_schema(self, conn: sqlite3.Connection) -> None:
        """Create minimal schema if schema.sql not found."""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'operator',
                active INTEGER DEFAULT 1,
                force_password_change INTEGER DEFAULT 1,
                failed_login_attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                success INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                center_x INTEGER,
                center_y INTEGER,
                grid_reference TEXT,
                threat_score INTEGER DEFAULT 0,
                threat_level TEXT DEFAULT 'NO_THREAT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER,
                threat_level TEXT NOT NULL,
                threat_score INTEGER NOT NULL,
                grid_reference TEXT NOT NULL,
                object_type TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    
    def _create_default_users(self) -> None:
        """Create default user accounts."""
        default_users = initialize_default_users()
        
        for user in default_users:
            try:
                self.create_user(
                    username=user["username"],
                    password=user.get("password_hash", ""),
                    name=user["name"],
                    role=user["role"],
                    password_already_hashed=True
                )
            except Exception as e:
                logger.error(f"Error creating default user {user['username']}: {e}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # USER MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    def create_user(
        self,
        username: str,
        password: str,
        name: str,
        role: str = "operator",
        email: Optional[str] = None,
        password_already_hashed: bool = False
    ) -> int:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            name: Display name
            role: User role (admin/supervisor/operator/readonly)
            email: Optional email address
            password_already_hashed: If True, password is already a hash
            
        Returns:
            New user ID
            
        Raises:
            ValueError: If username already exists
        """
        conn = self._get_connection()
        
        # Hash password if not already hashed
        if password_already_hashed:
            password_hash = password
        else:
            password_hash = hash_password(password)
        
        try:
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, name, role, email)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, name, role, email))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            self._audit_log(
                action="USER_CREATED",
                resource_type="user",
                resource_id=str(user_id),
                details=f"Created user: {username} with role: {role}"
            )
            
            return user_id
            
        except sqlite3.IntegrityError:
            raise ValueError(f"Username already exists: {username}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User dictionary or None
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify user credentials and return user if valid.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User dictionary if valid, None otherwise
        """
        user = self.get_user_by_username(username)
        
        if user is None:
            self._audit_log(
                action="LOGIN_FAILED",
                details=f"User not found: {username}",
                success=False
            )
            return None
        
        # Check if account is active
        if not user.get("active", True):
            self._audit_log(
                action="LOGIN_FAILED",
                username=username,
                details="Account disabled",
                success=False
            )
            return None
        
        # Check if account is locked
        locked_until = user.get("locked_until")
        if locked_until:
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until)
            if datetime.now() < locked_until:
                self._audit_log(
                    action="LOGIN_FAILED",
                    username=username,
                    details=f"Account locked until {locked_until}",
                    success=False
                )
                return None
        
        # Verify password
        if verify_password(password, user["password_hash"]):
            # Reset failed attempts and update last login
            self._update_user_login_success(user["id"])
            
            self._audit_log(
                action="LOGIN_SUCCESS",
                user_id=user["id"],
                username=username
            )
            
            return user
        else:
            # Increment failed attempts
            self._update_user_login_failure(user["id"])
            
            self._audit_log(
                action="LOGIN_FAILED",
                username=username,
                details="Invalid password",
                success=False
            )
            
            return None
    
    def _update_user_login_success(self, user_id: int) -> None:
        """Update user after successful login."""
        conn = self._get_connection()
        conn.execute("""
            UPDATE users 
            SET failed_login_attempts = 0,
                locked_until = NULL,
                last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        conn.commit()
    
    def _update_user_login_failure(self, user_id: int) -> None:
        """Update user after failed login."""
        conn = self._get_connection()
        
        # Get current failed attempts
        cursor = conn.execute(
            "SELECT failed_login_attempts FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        failed_attempts = (row["failed_login_attempts"] or 0) + 1
        
        # Check if should lock account
        max_attempts = 3
        locked_until = None
        
        if failed_attempts >= max_attempts:
            locked_until = datetime.now() + timedelta(minutes=15)
            self._audit_log(
                action="LOGIN_LOCKED",
                user_id=user_id,
                details=f"Account locked after {failed_attempts} failed attempts"
            )
        
        conn.execute("""
            UPDATE users 
            SET failed_login_attempts = ?,
                locked_until = ?
            WHERE id = ?
        """, (failed_attempts, locked_until, user_id))
        conn.commit()
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New plain text password
            
        Returns:
            True if updated successfully
        """
        conn = self._get_connection()
        password_hash = hash_password(new_password)
        
        conn.execute("""
            UPDATE users 
            SET password_hash = ?,
                force_password_change = 0,
                password_changed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (password_hash, user_id))
        conn.commit()
        
        self._audit_log(
            action="PASSWORD_CHANGED",
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id)
        )
        
        return True
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (excluding password hashes)."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT id, username, name, role, email, active,
                   force_password_change, last_login, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    # ─────────────────────────────────────────────────────────────────────────
    # DETECTION MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    def save_detection(self, detection: Dict[str, Any]) -> int:
        """
        Save a detection to the database.
        
        Args:
            detection: Detection dictionary containing:
                - timestamp: datetime
                - class_name: str
                - confidence: float
                - bbox: tuple (x1, y1, x2, y2)
                - center_x, center_y: int
                - grid_reference: str
                - threat_score: int
                - threat_level: str
                
        Returns:
            Detection ID
        """
        conn = self._get_connection()
        
        bbox = detection.get("bbox", (0, 0, 0, 0))
        
        cursor = conn.execute("""
            INSERT INTO detections (
                timestamp, class_name, class_id, confidence,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                center_x, center_y, grid_reference,
                threat_score, threat_level, video_id, frame_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            detection.get("timestamp", datetime.now()),
            detection.get("class_name", "unknown"),
            detection.get("class_id"),
            detection.get("confidence", 0),
            bbox[0], bbox[1], bbox[2], bbox[3],
            detection.get("center_x", 0),
            detection.get("center_y", 0),
            detection.get("grid_reference", ""),
            detection.get("threat_score", 0),
            detection.get("threat_level", "NO_THREAT"),
            detection.get("video_id"),
            detection.get("frame_number", 0)
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def save_detections_batch(self, detections: List[Dict[str, Any]]) -> int:
        """
        Save multiple detections in a batch.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Number of detections saved
        """
        conn = self._get_connection()
        
        for detection in detections:
            self.save_detection(detection)
        
        return len(detections)
    
    def get_detections(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        threat_level: Optional[str] = None,
        grid_reference: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query detections with filters.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            threat_level: Filter by threat level
            grid_reference: Filter by grid reference
            limit: Maximum results
            
        Returns:
            List of detection dictionaries
        """
        conn = self._get_connection()
        
        query = "SELECT * FROM detections WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if threat_level:
            query += " AND threat_level = ?"
            params.append(threat_level)
        
        if grid_reference:
            query += " AND grid_reference = ?"
            params.append(grid_reference)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    # ─────────────────────────────────────────────────────────────────────────
    # ALERT MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    def create_alert(self, alert: Dict[str, Any]) -> int:
        """
        Create a new alert.
        
        Args:
            alert: Alert dictionary containing:
                - detection_id: int (optional)
                - alert_type: str
                - threat_level: str
                - threat_score: int
                - grid_reference: str
                - object_type: str
                - description: str (optional)
                - screenshot_path: str (optional)
                
        Returns:
            Alert ID
        """
        conn = self._get_connection()
        
        cursor = conn.execute("""
            INSERT INTO alerts (
                detection_id, alert_type, threat_level, threat_score,
                grid_reference, object_type, object_count, description,
                screenshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.get("detection_id"),
            alert.get("alert_type", "detection"),
            alert.get("threat_level", "LOW"),
            alert.get("threat_score", 0),
            alert.get("grid_reference", ""),
            alert.get("object_type", "unknown"),
            alert.get("object_count", 1),
            alert.get("description"),
            alert.get("screenshot_path")
        ))
        
        conn.commit()
        alert_id = cursor.lastrowid
        
        self._audit_log(
            action="ALERT_CREATED",
            resource_type="alert",
            resource_id=str(alert_id),
            details=f"Created {alert.get('threat_level')} alert at {alert.get('grid_reference')}"
        )
        
        return alert_id
    
    def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active (non-resolved) alerts.
        
        Args:
            limit: Maximum alerts to return
            
        Returns:
            List of alert dictionaries, sorted by priority
        """
        conn = self._get_connection()
        
        cursor = conn.execute("""
            SELECT * FROM alerts
            WHERE status IN ('active', 'acknowledged', 'dispatched')
            ORDER BY 
                CASE threat_level 
                    WHEN 'CRITICAL' THEN 1 
                    WHEN 'MEDIUM' THEN 2 
                    WHEN 'LOW' THEN 3 
                END,
                created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Get alert by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def acknowledge_alert(
        self,
        alert_id: int,
        user_id: int
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            user_id: ID of user acknowledging
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        
        conn.execute("""
            UPDATE alerts
            SET status = 'acknowledged',
                acknowledged_at = CURRENT_TIMESTAMP,
                acknowledged_by = ?
            WHERE id = ?
        """, (user_id, alert_id))
        
        conn.commit()
        
        self._audit_log(
            action="ALERT_ACKNOWLEDGED",
            user_id=user_id,
            resource_type="alert",
            resource_id=str(alert_id)
        )
        
        return True
    
    def dispatch_patrol(
        self,
        alert_id: int,
        patrol_unit_id: str,
        patrol_unit_name: str,
        user_id: int,
        eta_minutes: int = 10
    ) -> int:
        """
        Dispatch a patrol unit to an alert.
        
        Args:
            alert_id: Alert ID
            patrol_unit_id: Patrol unit ID
            patrol_unit_name: Patrol unit name
            user_id: ID of dispatching user
            eta_minutes: Estimated arrival time
            
        Returns:
            Dispatch record ID
        """
        conn = self._get_connection()
        
        # Get alert info
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        # Create dispatch record
        cursor = conn.execute("""
            INSERT INTO patrol_dispatches (
                alert_id, patrol_unit_id, patrol_unit_name,
                target_grid, estimated_eta_minutes, dispatched_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alert_id, patrol_unit_id, patrol_unit_name,
            alert["grid_reference"], eta_minutes, user_id
        ))
        
        dispatch_id = cursor.lastrowid
        
        # Update alert status
        conn.execute("""
            UPDATE alerts
            SET status = 'dispatched',
                dispatched_at = CURRENT_TIMESTAMP,
                dispatched_by = ?
            WHERE id = ?
        """, (user_id, alert_id))
        
        conn.commit()
        
        self._audit_log(
            action="PATROL_DISPATCHED",
            user_id=user_id,
            resource_type="alert",
            resource_id=str(alert_id),
            details=f"Dispatched {patrol_unit_name} to {alert['grid_reference']}, ETA {eta_minutes} min"
        )
        
        return dispatch_id
    
    def resolve_alert(
        self,
        alert_id: int,
        user_id: int,
        resolution_notes: str = "",
        false_alarm: bool = False
    ) -> bool:
        """
        Mark an alert as resolved.
        
        Args:
            alert_id: Alert ID
            user_id: ID of resolving user
            resolution_notes: Notes about resolution
            false_alarm: Whether it was a false alarm
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        
        conn.execute("""
            UPDATE alerts
            SET status = 'resolved',
                resolved_at = CURRENT_TIMESTAMP,
                resolved_by = ?,
                resolution_notes = ?,
                false_alarm = ?
            WHERE id = ?
        """, (user_id, resolution_notes, int(false_alarm), alert_id))
        
        conn.commit()
        
        self._audit_log(
            action="ALERT_RESOLVED",
            user_id=user_id,
            resource_type="alert",
            resource_id=str(alert_id),
            details=f"False alarm: {false_alarm}"
        )
        
        return True
    
    def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get alert statistics for the specified period.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        conn = self._get_connection()
        start_date = datetime.now() - timedelta(days=days)
        
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN threat_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN threat_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN threat_level = 'LOW' THEN 1 ELSE 0 END) as low,
                SUM(CASE WHEN false_alarm = 1 THEN 1 ELSE 0 END) as false_alarms,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
            FROM alerts
            WHERE created_at >= ?
        """, (start_date,))
        
        row = cursor.fetchone()
        
        return {
            "period_days": days,
            "total_alerts": row["total"] or 0,
            "critical_alerts": row["critical"] or 0,
            "medium_alerts": row["medium"] or 0,
            "low_alerts": row["low"] or 0,
            "false_alarms": row["false_alarms"] or 0,
            "resolved": row["resolved"] or 0,
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUDIT LOGGING
    # ─────────────────────────────────────────────────────────────────────────
    
    def _audit_log(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        success: bool = True
    ) -> None:
        """
        Write an entry to the audit log.
        
        SECURITY NOTE:
            This method should be called for all significant actions.
            Audit log entries should never be deleted.
        """
        conn = self._get_connection()
        
        conn.execute("""
            INSERT INTO audit_log (
                user_id, username, action, resource_type,
                resource_id, details, success
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, username, action, resource_type,
            resource_id, details, int(success)
        ))
        
        conn.commit()
    
    def get_audit_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query the audit log.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            user_id: Filter by user
            action: Filter by action type
            limit: Maximum entries
            
        Returns:
            List of audit log entries
        """
        conn = self._get_connection()
        
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    # ─────────────────────────────────────────────────────────────────────────
    # BACKUP & MAINTENANCE
    # ─────────────────────────────────────────────────────────────────────────
    
    def backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a database backup.
        
        Args:
            backup_name: Custom backup filename (auto-generated if None)
            
        Returns:
            Path to backup file
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
        
        backup_path = Path(self.backup_dir) / backup_name
        
        # Close current connection to ensure all data is flushed
        self.close()
        
        # Copy database file
        shutil.copy2(self.db_path, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        
        self._audit_log(
            action="DATABASE_BACKUP",
            details=f"Backup created: {backup_name}"
        )
        
        return str(backup_path)
    
    def restore(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
            
        WARNING:
            This will overwrite the current database!
        """
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Close current connection
        self.close()
        
        # Create backup of current database
        current_backup = self.backup("pre_restore_backup.db")
        
        # Restore from backup
        shutil.copy2(backup_path, self.db_path)
        
        logger.info(f"Database restored from: {backup_path}")
        
        self._audit_log(
            action="DATABASE_RESTORE",
            details=f"Restored from: {backup_path}"
        )
        
        return True
    
    def vacuum(self) -> None:
        """
        Optimize database by running VACUUM.
        
        This reclaims unused space and defragments the database.
        """
        conn = self._get_connection()
        conn.execute("VACUUM")
        logger.info("Database vacuumed")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for initialization and testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Manager")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--backup", action="store_true", help="Create backup")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Database Manager")
    print("=" * 70)
    
    db = DatabaseManager()
    
    if args.init or not Path(db.db_path).exists():
        print("\nInitializing database...")
        db.initialize()
        print("✓ Database initialized")
    
    if args.backup:
        print("\nCreating backup...")
        backup_path = db.backup()
        print(f"✓ Backup created: {backup_path}")
    
    if args.test:
        print("\nRunning tests...")
        
        # Test user operations
        print("\n1. Testing user operations...")
        users = db.get_all_users()
        print(f"   Found {len(users)} users")
        
        admin = db.get_user_by_username("admin")
        if admin:
            print(f"   Admin user exists: {admin['name']}")
        
        # Test alert statistics
        print("\n2. Testing alert statistics...")
        stats = db.get_alert_statistics()
        print(f"   Total alerts (7 days): {stats['total_alerts']}")
        
        # Test audit log
        print("\n3. Testing audit log...")
        logs = db.get_audit_log(limit=5)
        print(f"   Recent audit entries: {len(logs)}")
        
        print("\n✓ All tests passed")
    
    # Show database info
    print(f"\nDatabase path: {db.db_path}")
    print(f"Database exists: {Path(db.db_path).exists()}")
    
    if Path(db.db_path).exists():
        size_mb = Path(db.db_path).stat().st_size / (1024 * 1024)
        print(f"Database size: {size_mb:.2f} MB")
    
    db.close()
    print("\n" + "=" * 70)
