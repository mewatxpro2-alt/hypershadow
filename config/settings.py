"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILL# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 15: SYSTEM INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════E SYSTEM - MAIN CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: config/settings.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    Central configuration file for the entire surveillance system.
    All system-wide settings, paths, thresholds, and constants are defined here.
    
SECURITY NOTE:
    - Do NOT store sensitive credentials in this file
    - Credentials should be in security.py (with restricted permissions)
    - This file may be reviewed by technical staff
    
MODIFICATION:
    - Any changes to this file should be logged in the audit trail
    - Test thoroughly after any modifications
    - Backup current configuration before making changes

═══════════════════════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: BASE PATHS
# ═══════════════════════════════════════════════════════════════════════════════
# All paths are relative to the project root for portability
# Using pathlib ensures cross-platform compatibility (Windows/Linux/macOS)

# Get the absolute path to the project root directory
# __file__ = config/settings.py, so parent.parent = project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Primary data directories
DATA_DIR = BASE_DIR / "data"                    # All user data
MODELS_DIR = BASE_DIR / "models"                # AI models (YOLOv8)
LOGS_DIR = BASE_DIR / "logs"                    # Log files
CONFIG_DIR = BASE_DIR / "config"                # Configuration files
DATABASE_DIR = BASE_DIR / "database"            # Database files
MAPS_DIR = BASE_DIR / "maps"                    # Map tiles and overlays
UI_DIR = BASE_DIR / "ui"                        # User interface files
DOCS_DIR = BASE_DIR / "docs"                    # Documentation

# Secondary data directories (under DATA_DIR)
VIDEOS_DIR = DATA_DIR / "videos"                # Uploaded surveillance videos
CACHE_DIR = DATA_DIR / "cache"                  # Processed frames cache
SCREENSHOTS_DIR = DATA_DIR / "screenshots"      # Alert screenshots
EXPORTS_DIR = DATA_DIR / "exports"              # Exported reports

# Log subdirectories
DETECTIONS_LOG_DIR = LOGS_DIR / "detections"    # Detection event logs

# Map subdirectories
TILES_DIR = MAPS_DIR / "tiles"                  # Downloaded OSM tiles


def ensure_directories_exist() -> None:
    """
    Create all required directories if they don't exist.
    
    SECURITY NOTE:
        This function creates directories with default permissions.
        On production deployment, verify permissions are set correctly:
        - Data directories: 700 (owner only)
        - Log directories: 700 (owner only)
        - Config directories: 700 (owner only)
        
    Called automatically when module is imported, but can be called
    manually if needed.
    """
    directories = [
        DATA_DIR,
        MODELS_DIR,
        LOGS_DIR,
        VIDEOS_DIR,
        CACHE_DIR,
        SCREENSHOTS_DIR,
        EXPORTS_DIR,
        DETECTIONS_LOG_DIR,
        TILES_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Create directories on module import
ensure_directories_exist()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: SYSTEM INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════
# Static information about the system deployment

SYSTEM_INFO: Dict[str, str] = {
    "name": "Border Surveillance System",
    "version": "1.0.0",
    "classification": "RESTRICTED",
    "organization": "Border Security Force",
    "sector": "Punjab North",                   # Deployment sector
    "station_code": "BSS-PN-001",               # Unique station identifier
    "deployment_date": "2026-01-02",            # System deployment date
    "last_updated": datetime.now().strftime("%Y-%m-%d"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: AI MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# YOLOv8 model settings for local inference (NO EXTERNAL API CALLS)

MODEL_CONFIG: Dict[str, Any] = {
    # Primary model file path
    # The YOLOv8 nano model is used for fast inference with acceptable accuracy
    "regular": str(MODELS_DIR / "yolov8n.pt"),
    
    # Optional thermal-specific model (for enhanced thermal detection)
    "thermal": str(MODELS_DIR / "yolov8n_thermal.pt"),
    
    # Confidence threshold for detection filtering
    # Detections below this threshold are discarded
    # Range: 0.0 to 1.0 (higher = fewer but more confident detections)
    # Recommended: 0.65-0.75 for border surveillance
    "confidence_threshold": 0.70,
    
    # Intersection over Union threshold for Non-Maximum Suppression
    # Controls how much overlap is allowed between bounding boxes
    # Range: 0.0 to 1.0 (lower = more aggressive suppression)
    # Recommended: 0.40-0.50 for crowded scenes
    "iou_threshold": 0.45,
    
    # Processing device
    # Options: "cpu" (always works) or "cuda" (requires NVIDIA GPU)
    # Auto-detection: Set to "auto" to automatically use GPU if available
    "device": "cpu",
    
    # Maximum detections per frame
    # Limits processing for extremely crowded scenes
    "max_detections": 50,
    
    # Input image size for model
    # Larger = more accurate but slower
    # Options: 320, 416, 512, 640 (YOLOv8 supports various sizes)
    "input_size": 640,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: DETECTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════════
# COCO dataset class indices that we're interested in detecting
# Full COCO list: https://docs.ultralytics.com/datasets/detect/coco/

# Classes that trigger threat assessment
THREAT_CLASSES: Dict[int, str] = {
    0: "person",          # Primary threat - unauthorized personnel
    2: "car",             # Vehicle threat - potential smuggling
    3: "motorcycle",      # Vehicle threat - fast infiltration
    5: "bus",             # Vehicle threat - mass transport
    7: "truck",           # Vehicle threat - heavy smuggling
}

# Point values assigned to each threat class (used in threat scoring)
THREAT_CLASS_POINTS: Dict[str, int] = {
    "person": 1,          # Base threat level
    "car": 2,             # Higher threat - faster, can carry more
    "motorcycle": 2,      # Higher threat - fast and maneuverable
    "bus": 3,             # High threat - can carry many people
    "truck": 3,           # High threat - can carry heavy loads
}

# Classes to explicitly ignore (reduce false positives)
IGNORE_CLASSES: Dict[int, str] = {
    14: "bird",           # Flying animals
    15: "cat",            # Domestic animals
    16: "dog",            # Domestic animals
    17: "horse",          # Animals
    18: "sheep",          # Livestock
    19: "cow",            # Livestock
    20: "elephant",       # Wild animals
    21: "bear",           # Wild animals
    22: "zebra",          # Wild animals
    23: "giraffe",        # Wild animals
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: VIDEO PROCESSING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Settings for video upload, processing, and playback

VIDEO_CONFIG: Dict[str, Any] = {
    # Frame skip for processing efficiency
    # Process every Nth frame (1 = all frames, 3 = every 3rd frame)
    # Higher values = faster processing but may miss fast-moving objects
    "frame_skip": 3,
    
    # Target frames per second for display
    # Controls playback smoothness in the dashboard
    "target_fps": 10,
    
    # Maximum video file size in megabytes
    # Prevents system overload from very large files
    "max_video_size_mb": 500,
    
    # Supported video formats
    # Add more formats if needed, but test thoroughly
    "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
    
    # Maximum video duration in minutes
    # Very long videos may cause memory issues
    "max_duration_minutes": 30,
    
    # Frame buffer size for real-time processing
    # Number of frames to keep in memory
    "frame_buffer_size": 30,
    
    # Thumbnail generation
    "thumbnail_size": (320, 240),
    "thumbnail_quality": 85,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: BORDER AND GRID CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Settings for border line position and military grid system

BORDER_CONFIG: Dict[str, Any] = {
    # Y-coordinate of the border line in video frame (pixels)
    # Objects above this line are on one side, below on the other
    # Adjust based on camera angle and position
    "border_line_y": 400,
    
    # Expected video dimensions
    # Used for grid calculations and coordinate mapping
    "video_width": 640,
    "video_height": 480,
    
    # Grid system configuration
    # Standard military grid: 6 columns (A-F) x 5 rows (1-5)
    "grid_columns": 6,      # A, B, C, D, E, F
    "grid_rows": 5,         # 1, 2, 3, 4, 5
    
    # Grid labels
    "column_labels": ["A", "B", "C", "D", "E", "F"],
    "row_labels": ["1", "2", "3", "4", "5"],
    
    # Border crossing detection
    # Minimum Y-movement to count as border crossing
    "crossing_threshold_pixels": 20,
    
    # Zone sensitivity multipliers
    # Applied to base threat score based on zone
    "zone_multipliers": {
        "1": 1.5,   # Row 1 (enemy side) - highest sensitivity
        "2": 1.3,   # Row 2 - high sensitivity
        "3": 1.2,   # Row 3 (border) - medium-high sensitivity
        "4": 1.0,   # Row 4 - normal sensitivity
        "5": 0.8,   # Row 5 (our side) - lower sensitivity
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: THREAT SCORING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Point-based threat assessment rules
# Higher scores = more serious threats

THREAT_SCORING: Dict[str, Any] = {
    # Threat level thresholds
    # Based on total points from all factors
    "critical_threshold": 11,     # 11+ points = CRITICAL (RED)
    "medium_threshold": 6,        # 6-10 points = MEDIUM (YELLOW)
    "low_threshold": 1,           # 1-5 points = LOW (GREEN)
    # 0 or below = NO THREAT
    
    # Time-of-day scoring
    # Nighttime activity is more suspicious
    "time_points": {
        "day": -1,          # 06:00-17:59 (broad daylight)
        "evening": 1,       # 18:00-21:59 (dusk)
        "night": 3,         # 22:00-05:59 (darkness)
    },
    
    # Group size scoring
    # Multiple detections in same area
    "group_points": {
        "single": 0,        # 1 person/vehicle
        "pair": 2,          # 2 in same grid
        "small_group": 3,   # 3-5 in same grid
        "large_group": 5,   # 6+ in same grid
    },
    
    # Movement pattern scoring
    "movement_points": {
        "stationary": 0,        # Not moving
        "slow": 1,              # Walking speed
        "fast": 2,              # Running/driving
        "erratic": 3,           # Suspicious pattern
    },
    
    # Confidence level adjustment
    # Adjust score based on AI confidence
    "confidence_adjustment": {
        "high": 1,              # >= 0.90 confidence
        "medium": 0,            # 0.75-0.89 confidence
        "low": -1,              # < 0.75 confidence
    },
    
    # Zone-based scoring
    # Points added based on grid row
    "zone_points": {
        "1": 5,     # Enemy territory
        "2": 3,     # Approach zone
        "3": 2,     # Border line
        "4": 1,     # Our territory
        "5": 0,     # Safe zone
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: ALERT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Settings for alert generation and management

ALERT_CONFIG: Dict[str, Any] = {
    # Audio alert settings
    "audio_enabled": True,
    "audio_file": str(BASE_DIR / "assets" / "alert.wav"),
    "critical_sound": str(BASE_DIR / "assets" / "critical_alert.wav"),
    "medium_sound": str(BASE_DIR / "assets" / "medium_alert.wav"),
    
    # Alert auto-archive after specified hours
    # Old alerts are moved to archive, not deleted
    "auto_archive_hours": 24,
    
    # Maximum active alerts displayed
    "max_active_alerts": 100,
    
    # Alert refresh interval (seconds)
    "refresh_interval": 5,
    
    # Screenshot on alert
    "screenshot_on_alert": True,
    "screenshot_quality": 90,
    
    # Alert debounce (prevent duplicate alerts)
    # Minimum seconds between alerts for same object in same grid
    "debounce_seconds": 10,
    
    # Alert colors (CSS hex codes)
    "colors": {
        "critical": "#FF0000",  # Red
        "medium": "#FFA500",    # Orange
        "low": "#FFFF00",       # Yellow
        "no_threat": "#00FF00", # Green
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: MAP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Settings for offline map display

MAP_CONFIG: Dict[str, Any] = {
    # Default map center coordinates
    # Adjust to your deployment location
    "center_lat": 31.234,           # Latitude (example: Punjab border)
    "center_lon": 75.456,           # Longitude
    
    # Default zoom level
    # Higher = more zoomed in (typically 10-16 for border areas)
    "default_zoom": 13,
    
    # Zoom range
    "min_zoom": 10,
    "max_zoom": 16,
    
    # Offline tiles directory
    "tiles_dir": str(TILES_DIR),
    
    # CRITICAL: Always use offline mode for security
    "offline_mode": True,
    
    # Map attribution (required for OSM)
    "attribution": "© OpenStreetMap contributors",
    
    # Marker icons
    "markers": {
        "threat_critical": "red",
        "threat_medium": "orange",
        "threat_low": "yellow",
        "patrol_unit": "green",
        "border_post": "blue",
        "camera": "purple",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: PATROL UNITS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Define patrol units available for dispatch

PATROL_UNITS: List[Dict[str, Any]] = [
    {
        "id": "PATROL-A1",
        "name": "Alpha Unit",
        "type": "vehicle",
        "base_grid": "A-5",
        "lat": 31.230,
        "lon": 75.450,
        "status": "active",
        "response_time_minutes": 5,
    },
    {
        "id": "PATROL-B2",
        "name": "Bravo Unit",
        "type": "vehicle",
        "base_grid": "D-5",
        "lat": 31.232,
        "lon": 75.458,
        "status": "active",
        "response_time_minutes": 7,
    },
    {
        "id": "PATROL-C3",
        "name": "Charlie Unit",
        "type": "foot",
        "base_grid": "F-4",
        "lat": 31.228,
        "lon": 75.462,
        "status": "active",
        "response_time_minutes": 12,
    },
    {
        "id": "PATROL-D4",
        "name": "Delta Unit",
        "type": "vehicle",
        "base_grid": "B-5",
        "lat": 31.234,
        "lon": 75.452,
        "status": "standby",
        "response_time_minutes": 8,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: BORDER POSTS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Static border post locations

BORDER_POSTS: List[Dict[str, Any]] = [
    {
        "id": "POST-001",
        "name": "Border Post Alpha",
        "grid": "C-3",
        "lat": 31.234,
        "lon": 75.456,
        "type": "primary",
        "personnel": 10,
    },
    {
        "id": "POST-002",
        "name": "Border Post Bravo",
        "grid": "A-3",
        "lat": 31.234,
        "lon": 75.448,
        "type": "secondary",
        "personnel": 5,
    },
    {
        "id": "POST-003",
        "name": "Border Post Charlie",
        "grid": "F-3",
        "lat": 31.234,
        "lon": 75.464,
        "type": "secondary",
        "personnel": 5,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12: GRID ZONES CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Military grid system zones (A-1 through F-5)

GRID_ZONES: Dict[str, Dict[str, Any]] = {
    # Row A (Leftmost column)
    "A-1": {"name": "Alpha-One", "terrain": "riverbank", "threat_modifier": 2, "patrol_coverage": True},
    "A-2": {"name": "Alpha-Two", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "A-3": {"name": "Alpha-Three", "terrain": "border_fence", "threat_modifier": 3, "patrol_coverage": True},
    "A-4": {"name": "Alpha-Four", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "A-5": {"name": "Alpha-Five", "terrain": "hills", "threat_modifier": 2, "patrol_coverage": False},
    
    # Row B
    "B-1": {"name": "Bravo-One", "terrain": "farmland", "threat_modifier": 1, "patrol_coverage": True},
    "B-2": {"name": "Bravo-Two", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "B-3": {"name": "Bravo-Three", "terrain": "border_fence", "threat_modifier": 3, "patrol_coverage": True},
    "B-4": {"name": "Bravo-Four", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "B-5": {"name": "Bravo-Five", "terrain": "farmland", "threat_modifier": 1, "patrol_coverage": True},
    
    # Row C
    "C-1": {"name": "Charlie-One", "terrain": "riverbank", "threat_modifier": 4, "patrol_coverage": True},
    "C-2": {"name": "Charlie-Two", "terrain": "plains", "threat_modifier": 2, "patrol_coverage": True},
    "C-3": {"name": "Charlie-Three", "terrain": "border_post", "threat_modifier": 5, "patrol_coverage": True},
    "C-4": {"name": "Charlie-Four", "terrain": "plains", "threat_modifier": 2, "patrol_coverage": True},
    "C-5": {"name": "Charlie-Five", "terrain": "hills", "threat_modifier": 3, "patrol_coverage": True},
    
    # Row D
    "D-1": {"name": "Delta-One", "terrain": "marsh", "threat_modifier": 3, "patrol_coverage": False},
    "D-2": {"name": "Delta-Two", "terrain": "road_crossing", "threat_modifier": 4, "patrol_coverage": True},
    "D-3": {"name": "Delta-Three", "terrain": "border_fence", "threat_modifier": 3, "patrol_coverage": True},
    "D-4": {"name": "Delta-Four", "terrain": "plains", "threat_modifier": 2, "patrol_coverage": True},
    "D-5": {"name": "Delta-Five", "terrain": "forest", "threat_modifier": 3, "patrol_coverage": False},
    
    # Row E
    "E-1": {"name": "Echo-One", "terrain": "riverbank", "threat_modifier": 2, "patrol_coverage": True},
    "E-2": {"name": "Echo-Two", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "E-3": {"name": "Echo-Three", "terrain": "border_fence", "threat_modifier": 3, "patrol_coverage": True},
    "E-4": {"name": "Echo-Four", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "E-5": {"name": "Echo-Five", "terrain": "hills", "threat_modifier": 2, "patrol_coverage": False},
    
    # Row F (Rightmost column)
    "F-1": {"name": "Foxtrot-One", "terrain": "farmland", "threat_modifier": 1, "patrol_coverage": True},
    "F-2": {"name": "Foxtrot-Two", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "F-3": {"name": "Foxtrot-Three", "terrain": "border_post", "threat_modifier": 5, "patrol_coverage": True},
    "F-4": {"name": "Foxtrot-Four", "terrain": "plains", "threat_modifier": 1, "patrol_coverage": True},
    "F-5": {"name": "Foxtrot-Five", "terrain": "hills", "threat_modifier": 2, "patrol_coverage": False},
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13: SECURITY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Security-related settings (non-sensitive)
# Sensitive credentials are in security.py

SECURITY_CONFIG: Dict[str, Any] = {
    # Enable/disable encryption for database
    "encryption_enabled": True,
    
    # Require user authentication
    "require_authentication": True,
    
    # Session timeout in minutes
    # User must re-login after this period of inactivity
    "session_timeout_minutes": 30,
    
    # Maximum failed login attempts before lockout
    "max_failed_logins": 3,
    
    # Lockout duration in minutes
    "lockout_duration_minutes": 15,
    
    # Force password change on first login
    "force_password_change": True,
    
    # Password requirements
    "password_min_length": 12,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digit": True,
    "password_require_special": True,
    
    # Enable audit logging for all actions
    "audit_all_actions": True,
    
    # Enable secure deletion (overwrite before delete)
    "secure_delete": True,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14: LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Python logging settings

LOGGING_CONFIG: Dict[str, Any] = {
    # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_level": "INFO",
    
    # Maximum log file size in MB before rotation
    "max_log_size_mb": 100,
    
    # Number of backup log files to keep
    "backup_count": 5,
    
    # Audit log retention in days
    "audit_retention_days": 365,
    
    # Log file paths
    "system_log": str(LOGS_DIR / "system.log"),
    "audit_log": str(LOGS_DIR / "audit.log"),
    "error_log": str(LOGS_DIR / "error.log"),
    "detection_log": str(DETECTIONS_LOG_DIR / "detections.log"),
    
    # Log format
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14: DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# SQLite database settings

DATABASE_CONFIG: Dict[str, Any] = {
    # Database file path
    "db_path": str(DATABASE_DIR / "surveillance.db"),
    
    # Backup directory
    "backup_dir": str(DATABASE_DIR / "backups"),
    
    # Automatic backup interval in hours
    "auto_backup_hours": 6,
    
    # Maximum backups to keep
    "max_backups": 10,
    
    # Connection timeout in seconds
    "connection_timeout": 30,
    
    # Enable WAL mode for better concurrency
    "wal_mode": True,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 15: UI CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# User interface settings

UI_CONFIG: Dict[str, Any] = {
    # Page title
    "page_title": "Border Surveillance System",
    
    # Page icon (emoji or path to image)
    "page_icon": "🛡️",
    
    # Layout: "wide" or "centered"
    "layout": "wide",
    
    # Initial sidebar state: "expanded" or "collapsed"
    "initial_sidebar_state": "expanded",
    
    # Theme: "dark" (recommended for military) or "light"
    "theme": "dark",
    
    # Auto-refresh interval in seconds
    "auto_refresh_seconds": 5,
    
    # Maximum items in tables/lists
    "max_table_rows": 100,
    
    # Date/time format for display
    "datetime_format": "%Y-%m-%d %H:%M:%S",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M:%S",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 16: EXPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Settings for report generation and data export

EXPORT_CONFIG: Dict[str, Any] = {
    # Export formats
    "supported_formats": ["pdf", "csv", "json"],
    
    # PDF settings
    "pdf_page_size": "A4",
    "pdf_orientation": "portrait",
    
    # Include classification marking on exports
    "include_classification": True,
    "classification_text": "RESTRICTED - OFFICIAL USE ONLY",
    
    # Export directory
    "export_dir": str(EXPORTS_DIR),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 17: HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_time_period(hour: int) -> str:
    """
    Determine the time period based on hour.
    
    Args:
        hour (int): Hour of the day (0-23)
        
    Returns:
        str: Time period ("day", "evening", or "night")
        
    Example:
        >>> get_time_period(14)
        'day'
        >>> get_time_period(23)
        'night'
    """
    if 6 <= hour < 18:
        return "day"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_threat_level_name(score: int) -> str:
    """
    Convert threat score to threat level name.
    
    Args:
        score (int): Total threat score
        
    Returns:
        str: Threat level name ("CRITICAL", "MEDIUM", "LOW", or "NO_THREAT")
        
    Example:
        >>> get_threat_level_name(15)
        'CRITICAL'
        >>> get_threat_level_name(3)
        'LOW'
    """
    if score >= THREAT_SCORING["critical_threshold"]:
        return "CRITICAL"
    elif score >= THREAT_SCORING["medium_threshold"]:
        return "MEDIUM"
    elif score >= THREAT_SCORING["low_threshold"]:
        return "LOW"
    else:
        return "NO_THREAT"


def get_threat_color(level: str) -> str:
    """
    Get the color code for a threat level.
    
    Args:
        level (str): Threat level name
        
    Returns:
        str: Hex color code
        
    Example:
        >>> get_threat_color("CRITICAL")
        '#FF0000'
    """
    level_to_key = {
        "CRITICAL": "critical",
        "MEDIUM": "medium",
        "LOW": "low",
        "NO_THREAT": "no_threat",
    }
    key = level_to_key.get(level, "no_threat")
    return ALERT_CONFIG["colors"].get(key, "#FFFFFF")


def validate_config() -> List[str]:
    """
    Validate all configuration settings.
    
    Returns:
        List[str]: List of validation errors (empty if all valid)
        
    SECURITY NOTE:
        Run this function during system startup to catch configuration errors.
    """
    errors = []
    
    # Check critical directories exist
    if not BASE_DIR.exists():
        errors.append(f"Base directory not found: {BASE_DIR}")
    
    # Check model file exists
    model_path = Path(MODEL_CONFIG["regular"])
    if not model_path.exists():
        errors.append(f"Model file not found: {model_path}")
    
    # Check threshold values are valid
    if not 0 <= MODEL_CONFIG["confidence_threshold"] <= 1:
        errors.append("Confidence threshold must be between 0 and 1")
    
    if not 0 <= MODEL_CONFIG["iou_threshold"] <= 1:
        errors.append("IOU threshold must be between 0 and 1")
    
    # Check threat scoring thresholds are ordered correctly
    if THREAT_SCORING["critical_threshold"] <= THREAT_SCORING["medium_threshold"]:
        errors.append("Critical threshold must be higher than medium threshold")
    
    if THREAT_SCORING["medium_threshold"] <= THREAT_SCORING["low_threshold"]:
        errors.append("Medium threshold must be higher than low threshold")
    
    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# END OF CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Print configuration summary on import (for debugging)
if __name__ == "__main__":
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - CONFIGURATION")
    print("=" * 70)
    print(f"System: {SYSTEM_INFO['name']} v{SYSTEM_INFO['version']}")
    print(f"Classification: {SYSTEM_INFO['classification']}")
    print(f"Organization: {SYSTEM_INFO['organization']}")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Model Path: {MODEL_CONFIG['regular']}")
    print("=" * 70)
    
    # Validate configuration
    errors = validate_config()
    if errors:
        print("CONFIGURATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration validation: PASSED")
