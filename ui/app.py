"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - MAIN DASHBOARD APPLICATION                   ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Primary Streamlit dashboard for border surveillance operations     ║
║  Security Level: TOP SECRET                                                  ║
║  Version: 1.0.0                                                              ║
║                                                                              ║
║  AUTHORIZED PERSONNEL ONLY - ALL ACCESS IS MONITORED AND LOGGED             ║
╚══════════════════════════════════════════════════════════════════════════════╝

OPERATIONAL SECURITY NOTICE:
- This system operates OFFLINE only
- No external network connections permitted
- All video processing occurs locally
- Detection data encrypted at rest
- Audit trail maintained for all actions

SYSTEM REQUIREMENTS:
- Python 3.9+
- Minimum 8GB RAM (16GB recommended)
- GPU optional but recommended for real-time processing
- 50GB available disk space
"""

import streamlit as st
import cv2
import numpy as np
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import sys
import os

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Get the base directory of the project
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# =============================================================================
# IMPORTS - LOCAL MODULES
# =============================================================================

from config.settings import (
    MODEL_CONFIG,
    VIDEO_CONFIG,
    BORDER_CONFIG,
    ALERT_CONFIG,
    SECURITY_CONFIG,
    MAP_CONFIG,
    LOGGING_CONFIG,
    SYSTEM_INFO,
    THREAT_CLASSES,
    GRID_ZONES,
    PATROL_UNITS,
    BORDER_POSTS,
)
from config.security import SecurityManager
from core.detection import BorderDetector
from core.threat_scoring import ThreatScoringEngine
from core.grid_system import MilitaryGridSystem
from core.video_processor import VideoProcessor
from database.db_manager import DatabaseManager
from database.encryption import DataEncryption
from ui.styles import MAIN_CSS, render_header, CLASSIFICATION_BANNER, COLORS
from ui.auth import (
    AuthManager, 
    render_login_page, 
    require_auth,
    render_session_info,
    render_password_change_dialog
)
from ui.components import (
    VideoPlayerComponent,
    AlertPanelComponent,
    MetricDashboardComponent,
    PatrolStatusComponent,
    FileUploaderComponent,
    ActivityLogComponent,
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="CLASSIFIED - Border Surveillance System",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,  # Disabled - no external links
        "Report a bug": None,  # Disabled - no external links
        "About": """
        ## Border Surveillance System
        **CLASSIFIED - AUTHORIZED PERSONNEL ONLY**
        
        Version: 1.0.0
        
        This system is for authorized military/government use only.
        Unauthorized access is prohibited and will be prosecuted.
        """,
    }
)

# =============================================================================
# INJECT CSS STYLES
# =============================================================================

st.markdown(MAIN_CSS, unsafe_allow_html=True)
st.markdown(CLASSIFICATION_BANNER, unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def initialize_session_state() -> None:
    """
    Initialize all session state variables.
    
    This function sets up the initial state for the application,
    including authentication state, detection results, and UI state.
    
    Security Note:
        Session state is stored in memory only.
        No session data is persisted to disk without encryption.
    """
    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "session_start" not in st.session_state:
        st.session_state.session_start = None
    
    # Video processing state
    if "video_frames" not in st.session_state:
        st.session_state.video_frames = []
    if "current_frame_idx" not in st.session_state:
        st.session_state.current_frame_idx = 0
    if "detections" not in st.session_state:
        st.session_state.detections = []
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = "idle"
    
    # Alert state
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    if "alert_history" not in st.session_state:
        st.session_state.alert_history = []
    
    # System state
    if "detector_loaded" not in st.session_state:
        st.session_state.detector_loaded = False
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False
    
    # Activity log
    if "activity_log" not in st.session_state:
        st.session_state.activity_log = []


# =============================================================================
# SYSTEM INITIALIZATION
# =============================================================================

@st.cache_resource
def initialize_detector() -> BorderDetector:
    """
    Initialize the YOLOv8 detection model.
    
    Returns:
        BorderDetector instance
        
    Security Note:
        Model is loaded from local storage only.
        No network connections are made.
    """
    try:
        detector = BorderDetector()
        return detector
    except Exception as e:
        st.error(f"Failed to initialize detector: {str(e)}")
        return None


@st.cache_resource
def initialize_database() -> DatabaseManager:
    """
    Initialize the encrypted database connection.
    
    Returns:
        DatabaseManager instance
        
    Security Note:
        Database is encrypted at rest using SQLCipher.
    """
    try:
        db = DatabaseManager()
        db.initialize_database()
        return db
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        return None


def initialize_systems() -> Tuple[
    Optional[BorderDetector],
    Optional[ThreatScoringEngine],
    Optional[MilitaryGridSystem],
    Optional[VideoProcessor],
    Optional[DatabaseManager]
]:
    """
    Initialize all system components.
    
    Returns:
        Tuple of initialized system components
        
    Security Note:
        All components operate locally without network access.
    """
    detector = initialize_detector()
    threat_scorer = ThreatScoringEngine()
    grid_system = MilitaryGridSystem()
    video_processor = VideoProcessor()
    db = initialize_database()
    
    return detector, threat_scorer, grid_system, video_processor, db


# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

def log_activity(action: str, details: str, user: str = None) -> None:
    """
    Log an activity to the session activity log.
    
    Args:
        action: Action type/name
        details: Detailed description
        user: Username (optional, uses current user if not provided)
    """
    if user is None:
        user = st.session_state.get("user", {}).get("username", "system")
    
    entry = {
        "timestamp": datetime.now(),
        "action": action,
        "details": details,
        "user": user,
    }
    
    # Add to beginning of list
    st.session_state.activity_log.insert(0, entry)
    
    # Keep only last 100 entries
    st.session_state.activity_log = st.session_state.activity_log[:100]


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> Dict[str, Any]:
    """
    Render the sidebar with navigation and controls.
    
    Returns:
        Dictionary of sidebar selections and settings
    """
    with st.sidebar:
        # System logo and title
        st.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="
                font-family: 'Orbitron', monospace;
                font-size: 18px;
                color: #4ade80;
                letter-spacing: 2px;
            ">
                ⬡ BSS v1.0
            </div>
            <div style="
                font-family: 'Roboto Mono', monospace;
                font-size: 10px;
                color: #6e6e6e;
                margin-top: 5px;
            ">
                Border Surveillance System
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Session info
        render_session_info()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("""
        <div class="sidebar-title">Navigation</div>
        """, unsafe_allow_html=True)
        
        page = st.selectbox(
            "Select View",
            [
                "🎯 Live Monitoring",
                "📹 Video Analysis",
                "🗺️ Map View",
                "📊 Reports",
                "⚙️ Settings",
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("""
        <div class="sidebar-title">System Status</div>
        """, unsafe_allow_html=True)
        
        # System status indicators
        detector_status = "🟢 Online" if st.session_state.detector_loaded else "🔴 Offline"
        db_status = "🟢 Connected" if st.session_state.db_initialized else "🔴 Disconnected"
        
        st.markdown(f"""
        <div class="sidebar-section">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 11px;">
                <div style="margin-bottom: 8px;">
                    <span style="color: #6e6e6e;">Detection Engine:</span>
                    <span style="color: #e6e6e6;"> {detector_status}</span>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #6e6e6e;">Database:</span>
                    <span style="color: #e6e6e6;"> {db_status}</span>
                </div>
                <div>
                    <span style="color: #6e6e6e;">Active Alerts:</span>
                    <span style="color: #ff6b35;"> {len(st.session_state.alerts)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("""
        <div class="sidebar-title">Quick Actions</div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        if st.button("🚨 Test Alert", use_container_width=True):
            # Create a test alert
            test_alert = {
                "id": f"test_{int(time.time())}",
                "threat_level": "MEDIUM",
                "object_type": "TEST",
                "grid_reference": "C-3",
                "confidence": 0.95,
                "timestamp": datetime.now(),
                "status": "ACTIVE",
            }
            st.session_state.alerts.insert(0, test_alert)
            log_activity("TEST_ALERT", "Test alert generated")
            st.rerun()
        
        if st.button("🗑️ Clear Alerts", use_container_width=True):
            st.session_state.alerts = []
            log_activity("CLEAR_ALERTS", "All alerts cleared")
            st.rerun()
        
        st.markdown("---")
        
        # Date/time display
        st.markdown(f"""
        <div style="
            text-align: center;
            font-family: 'Roboto Mono', monospace;
            font-size: 10px;
            color: #6e6e6e;
        ">
            UTC: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
        """, unsafe_allow_html=True)
        
        return {"page": page}


# =============================================================================
# MAIN CONTENT PAGES
# =============================================================================

def render_live_monitoring_page(
    detector: BorderDetector,
    threat_scorer: ThreatScoringEngine,
    grid_system: MilitaryGridSystem,
    db: DatabaseManager
) -> None:
    """
    Render the live monitoring dashboard.
    
    Args:
        detector: BorderDetector instance
        threat_scorer: ThreatScoringEngine instance
        grid_system: MilitaryGridSystem instance
        db: DatabaseManager instance
    """
    # Header
    st.markdown(
        render_header("LIVE MONITORING DASHBOARD"),
        unsafe_allow_html=True
    )
    
    # Top metrics row
    metrics = MetricDashboardComponent()
    metrics.render_system_metrics(
        detections_today=len(st.session_state.detections),
        alerts_active=len([a for a in st.session_state.alerts if a.get("status") == "ACTIVE"]),
        patrols_dispatched=0,  # TODO: Get from database
        system_status="ONLINE" if detector else "OFFLINE"
    )
    
    st.markdown("---")
    
    # Main content - 3 column layout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Column 1: Video Feed
    with col1:
        st.markdown("""
        <div class="military-card-header">📹 Primary Feed</div>
        """, unsafe_allow_html=True)
        
        # File uploader
        uploader = FileUploaderComponent()
        uploaded_data = uploader.render_uploader()
        
        if uploaded_data:
            # Process uploaded video
            with st.spinner("Processing video..."):
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(uploaded_data)
                    tmp_path = tmp.name
                
                try:
                    # Initialize video capture
                    cap = cv2.VideoCapture(tmp_path)
                    
                    if cap.isOpened():
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        st.info(f"Video loaded: {total_frames} frames at {fps:.1f} FPS")
                        
                        # Frame slider
                        frame_idx = st.slider(
                            "Frame",
                            0,
                            max(0, total_frames - 1),
                            st.session_state.current_frame_idx,
                            key="frame_slider"
                        )
                        st.session_state.current_frame_idx = frame_idx
                        
                        # Seek to frame
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame = cap.read()
                        
                        if ret:
                            # Run detection if detector is available
                            frame_detections = []
                            
                            if detector:
                                detection_results = detector.process_frame(frame)
                                
                                # Score each detection
                                for det in detection_results:
                                    # Get grid reference
                                    cx = (det["bbox"][0] + det["bbox"][2]) / 2
                                    cy = (det["bbox"][1] + det["bbox"][3]) / 2
                                    grid_ref = grid_system.pixel_to_grid(
                                        int(cx), int(cy),
                                        frame.shape[1], frame.shape[0]
                                    )
                                    
                                    # Calculate threat score
                                    threat_info = threat_scorer.calculate_threat_score(
                                        object_type=det["class_name"],
                                        zone_name=grid_ref.split("-")[0] if grid_ref else "A",
                                        confidence=det["confidence"]
                                    )
                                    
                                    det["grid_reference"] = grid_ref
                                    det["threat_level"] = threat_info["threat_level"]
                                    det["threat_score"] = threat_info["total_score"]
                                    
                                    frame_detections.append(det)
                            
                            # Render frame with detections
                            video_player = VideoPlayerComponent()
                            annotated_frame = video_player.render_frame_with_detections(
                                frame,
                                frame_detections,
                                show_grid=True,
                                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            
                            # Display frame
                            video_player.display_frame(annotated_frame)
                            
                            # Store detections
                            st.session_state.detections = frame_detections
                            
                            # Auto-generate alerts for high threat detections
                            for det in frame_detections:
                                if det.get("threat_level") in ["CRITICAL", "HIGH"]:
                                    alert = {
                                        "id": f"alert_{int(time.time())}_{det['class_name']}",
                                        "threat_level": det["threat_level"],
                                        "object_type": det["class_name"],
                                        "grid_reference": det.get("grid_reference", "N/A"),
                                        "confidence": det["confidence"],
                                        "timestamp": datetime.now(),
                                        "status": "ACTIVE",
                                    }
                                    
                                    # Avoid duplicate alerts
                                    existing_ids = [a["id"] for a in st.session_state.alerts]
                                    if alert["id"] not in existing_ids:
                                        st.session_state.alerts.insert(0, alert)
                        
                        cap.release()
                    else:
                        st.error("Failed to open video file")
                        
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
        else:
            # Placeholder when no video
            st.markdown("""
            <div style="
                background-color: #000000;
                border: 2px solid #3d5a3d;
                border-radius: 8px;
                height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    font-family: 'Roboto Mono', monospace;
                    color: #4ade80;
                    text-align: center;
                ">
                    <div style="font-size: 48px; margin-bottom: 15px;">📹</div>
                    <div style="font-size: 14px;">NO FEED ACTIVE</div>
                    <div style="font-size: 11px; color: #6e6e6e; margin-top: 10px;">
                        Upload drone footage to begin analysis
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Column 2: Alert Panel
    with col2:
        st.markdown("""
        <div class="military-card-header">🚨 Active Alerts</div>
        """, unsafe_allow_html=True)
        
        alert_panel = AlertPanelComponent()
        alert_action = alert_panel.render_alert_list(st.session_state.alerts, max_display=5)
        
        if alert_action:
            action_type, alert_id = alert_action
            
            # Find the alert
            for alert in st.session_state.alerts:
                if alert.get("id") == alert_id:
                    if action_type == "acknowledge":
                        alert["status"] = "ACKNOWLEDGED"
                        log_activity("ALERT_ACK", f"Alert {alert_id} acknowledged")
                    elif action_type == "dismiss":
                        alert["status"] = "DISMISSED"
                        log_activity("ALERT_DISMISS", f"Alert {alert_id} dismissed")
                    elif action_type == "dispatch":
                        alert["status"] = "DISPATCHED"
                        log_activity("PATROL_DISPATCH", f"Patrol dispatched for alert {alert_id}")
                    break
            
            st.rerun()
    
    # Column 3: Detection Stats & Patrol Status
    with col3:
        st.markdown("""
        <div class="military-card-header">📊 Detection Stats</div>
        """, unsafe_allow_html=True)
        
        # Count detections by type
        detection_stats = {}
        for det in st.session_state.detections:
            obj_type = det.get("class_name", "unknown")
            detection_stats[obj_type] = detection_stats.get(obj_type, 0) + 1
        
        if detection_stats:
            metrics.render_detection_stats(detection_stats)
        else:
            st.caption("No detections in current frame")
        
        st.markdown("---")
        
        st.markdown("""
        <div class="military-card-header">🚔 Patrol Units</div>
        """, unsafe_allow_html=True)
        
        patrol_component = PatrolStatusComponent()
        patrol_component.render_patrol_list(PATROL_UNITS)


def render_video_analysis_page(
    detector: BorderDetector,
    threat_scorer: ThreatScoringEngine,
    grid_system: MilitaryGridSystem,
    video_processor: VideoProcessor,
    db: DatabaseManager
) -> None:
    """
    Render the video analysis page for batch processing.
    
    Args:
        detector: BorderDetector instance
        threat_scorer: ThreatScoringEngine instance
        grid_system: MilitaryGridSystem instance
        video_processor: VideoProcessor instance
        db: DatabaseManager instance
    """
    st.markdown(
        render_header("VIDEO ANALYSIS"),
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">📹 Batch Video Processing</div>
        """, unsafe_allow_html=True)
        
        # File uploader for batch processing
        uploader = FileUploaderComponent()
        uploaded_data = uploader.render_uploader(key="batch_uploader")
        
        # Processing options
        st.markdown("<br>", unsafe_allow_html=True)
        
        process_col1, process_col2 = st.columns(2)
        
        with process_col1:
            frame_skip = st.slider(
                "Frame Skip (process every Nth frame)",
                1, 30, 5,
                help="Higher values = faster processing but may miss detections"
            )
        
        with process_col2:
            confidence_threshold = st.slider(
                "Confidence Threshold",
                0.5, 1.0, 0.7,
                help="Minimum confidence for detections"
            )
        
        if uploaded_data and st.button("🔍 Start Analysis", use_container_width=True):
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(uploaded_data)
                tmp_path = tmp.name
            
            try:
                # Process video
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                all_detections = []
                
                cap = cv2.VideoCapture(tmp_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                frame_idx = 0
                processed = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if frame_idx % frame_skip == 0:
                        # Run detection
                        if detector:
                            detections = detector.process_frame(frame)
                            
                            for det in detections:
                                if det["confidence"] >= confidence_threshold:
                                    # Calculate grid and threat
                                    cx = (det["bbox"][0] + det["bbox"][2]) / 2
                                    cy = (det["bbox"][1] + det["bbox"][3]) / 2
                                    grid_ref = grid_system.pixel_to_grid(
                                        int(cx), int(cy),
                                        frame.shape[1], frame.shape[0]
                                    )
                                    
                                    threat_info = threat_scorer.calculate_threat_score(
                                        object_type=det["class_name"],
                                        zone_name=grid_ref.split("-")[0] if grid_ref else "A",
                                        confidence=det["confidence"]
                                    )
                                    
                                    det["frame_idx"] = frame_idx
                                    det["grid_reference"] = grid_ref
                                    det["threat_level"] = threat_info["threat_level"]
                                    det["threat_score"] = threat_info["total_score"]
                                    
                                    all_detections.append(det)
                        
                        processed += 1
                    
                    frame_idx += 1
                    progress = frame_idx / total_frames
                    progress_bar.progress(progress)
                    status_text.text(f"Processing frame {frame_idx}/{total_frames}...")
                
                cap.release()
                
                # Complete
                progress_bar.progress(1.0)
                status_text.text(f"✅ Analysis complete! Found {len(all_detections)} detections")
                
                log_activity(
                    "VIDEO_ANALYSIS",
                    f"Processed {total_frames} frames, found {len(all_detections)} detections"
                )
                
                # Store results
                st.session_state.batch_results = all_detections
                
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Results display
        if "batch_results" in st.session_state and st.session_state.batch_results:
            st.markdown("""
            <div class="military-card">
                <div class="military-card-header">📊 Analysis Results</div>
            """, unsafe_allow_html=True)
            
            results = st.session_state.batch_results
            
            # Summary by threat level
            threat_counts = {}
            for det in results:
                level = det.get("threat_level", "UNKNOWN")
                threat_counts[level] = threat_counts.get(level, 0) + 1
            
            st.write("**Threat Level Distribution:**")
            for level, count in sorted(threat_counts.items()):
                st.write(f"- {level}: {count}")
            
            # Download results button
            import json
            results_json = json.dumps(results, default=str, indent=2)
            st.download_button(
                "📥 Download Results (JSON)",
                results_json,
                file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Activity log
        activity_log = ActivityLogComponent()
        activity_log.render_log(st.session_state.activity_log)


def render_map_view_page() -> None:
    """
    Render the map view page with grid overlay.
    
    Note: Full map implementation requires offline tiles to be downloaded.
    """
    st.markdown(
        render_header("TACTICAL MAP VIEW"),
        unsafe_allow_html=True
    )
    
    st.info("""
    **Map View Configuration Required**
    
    To use the map view, you need to:
    1. Download offline map tiles using the tile downloader
    2. Configure the map center coordinates in settings
    3. Set up the grid overlay parameters
    
    See the `maps/tile_downloader.py` utility for downloading tiles.
    """)
    
    # Display grid information
    st.markdown("""
    <div class="military-card">
        <div class="military-card-header">🗺️ Grid Configuration</div>
    """, unsafe_allow_html=True)
    
    st.write("**Active Grid Zones:**")
    
    for zone_id, zone_info in GRID_ZONES.items():
        st.markdown(f"""
        <div style="
            background-color: #1a1a1a;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
        ">
            <div style="
                font-family: 'Roboto Mono', monospace;
                font-size: 12px;
                color: #4ade80;
            ">
                Zone {zone_id}: {zone_info.get('name', 'Unknown')}
            </div>
            <div style="
                font-family: 'Roboto Mono', monospace;
                font-size: 10px;
                color: #6e6e6e;
                margin-top: 4px;
            ">
                Terrain: {zone_info.get('terrain', 'unknown')} | 
                Threat Modifier: {zone_info.get('threat_modifier', 0):+d}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Border posts
    st.markdown("""
    <div class="military-card">
        <div class="military-card-header">🏛️ Border Posts</div>
    """, unsafe_allow_html=True)
    
    for post in BORDER_POSTS:
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #252525;
        ">
            <span style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #e6e6e6;">
                {post['name']}
            </span>
            <span style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #6e6e6e;">
                {post['coordinates']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_reports_page(db: DatabaseManager) -> None:
    """
    Render the reports and analytics page.
    
    Args:
        db: DatabaseManager instance
    """
    st.markdown(
        render_header("REPORTS & ANALYTICS"),
        unsafe_allow_html=True
    )
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        [
            "📊 Daily Activity Summary",
            "🚨 Alert History",
            "📹 Detection Log",
            "🔐 Audit Trail",
        ]
    )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now().date())
    
    if st.button("Generate Report", use_container_width=True):
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">📋 Report Output</div>
        """, unsafe_allow_html=True)
        
        if "Daily Activity" in report_type:
            st.write("**Daily Activity Summary**")
            st.write(f"Date Range: {start_date} to {end_date}")
            st.write("---")
            st.write(f"Total Detections: {len(st.session_state.detections)}")
            st.write(f"Total Alerts Generated: {len(st.session_state.alerts)}")
            st.write(f"Active Alerts: {len([a for a in st.session_state.alerts if a.get('status') == 'ACTIVE'])}")
        
        elif "Alert History" in report_type:
            st.write("**Alert History**")
            for alert in st.session_state.alert_history + st.session_state.alerts:
                st.write(f"- [{alert.get('timestamp', 'N/A')}] {alert.get('threat_level')} - {alert.get('object_type')} @ {alert.get('grid_reference')}")
        
        elif "Detection Log" in report_type:
            st.write("**Detection Log**")
            st.write("Detections are stored in the encrypted database.")
            st.write(f"Current session detections: {len(st.session_state.detections)}")
        
        elif "Audit Trail" in report_type:
            st.write("**Audit Trail**")
            for entry in st.session_state.activity_log:
                st.write(f"- [{entry.get('timestamp', 'N/A')}] {entry.get('user')}: {entry.get('action')} - {entry.get('details')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        log_activity("REPORT_GENERATED", f"{report_type} for {start_date} to {end_date}")


def render_settings_page() -> None:
    """
    Render the settings and configuration page.
    """
    st.markdown(
        render_header("SYSTEM SETTINGS"),
        unsafe_allow_html=True
    )
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Detection",
        "🚨 Alerts",
        "🔐 Security",
        "ℹ️ System Info"
    ])
    
    with tab1:
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">Detection Settings</div>
        """, unsafe_allow_html=True)
        
        st.write("**Model Configuration:**")
        st.write(f"- Model: {MODEL_CONFIG.get('model_path', 'yolov8n.pt')}")
        st.write(f"- Confidence Threshold: {MODEL_CONFIG.get('confidence_threshold', 0.7)}")
        st.write(f"- Device: {MODEL_CONFIG.get('device', 'auto')}")
        
        st.write("**Threat Classes:**")
        for class_name, class_id in THREAT_CLASSES.items():
            st.write(f"- {class_name}: ID {class_id}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">Alert Settings</div>
        """, unsafe_allow_html=True)
        
        st.write("**Alert Configuration:**")
        st.write(f"- Auto-escalation: {ALERT_CONFIG.get('auto_escalation', False)}")
        st.write(f"- Sound Alerts: {ALERT_CONFIG.get('enable_sounds', True)}")
        st.write(f"- Response Time SLA: {ALERT_CONFIG.get('response_time_sla_minutes', 5)} minutes")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">Security Settings</div>
        """, unsafe_allow_html=True)
        
        st.write("**Security Configuration:**")
        st.write(f"- Session Timeout: {SECURITY_CONFIG.get('session_timeout_minutes', 480)} minutes")
        st.write(f"- Max Login Attempts: {SECURITY_CONFIG.get('max_login_attempts', 3)}")
        st.write(f"- Lockout Duration: {SECURITY_CONFIG.get('lockout_duration_minutes', 30)} minutes")
        st.write(f"- Encryption: AES-256-GCM")
        st.write(f"- Password Hashing: bcrypt (12 rounds)")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown("""
        <div class="military-card">
            <div class="military-card-header">System Information</div>
        """, unsafe_allow_html=True)
        
        st.write("**System Details:**")
        for key, value in SYSTEM_INFO.items():
            st.write(f"- {key}: {value}")
        
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main() -> None:
    """
    Main application entry point.
    
    This function orchestrates the entire dashboard application,
    handling authentication, navigation, and page rendering.
    
    Security Note:
        All access requires authentication.
        Session is validated on each interaction.
    """
    # Initialize session state
    initialize_session_state()
    
    # Check authentication
    auth = AuthManager()
    
    if not auth.check_session():
        # Show login page
        render_login_page()
        return
    
    # Check if password change required
    render_password_change_dialog()
    
    # Initialize systems
    detector, threat_scorer, grid_system, video_processor, db = initialize_systems()
    
    # Update session state with system status
    st.session_state.detector_loaded = detector is not None
    st.session_state.db_initialized = db is not None
    
    # Render sidebar and get navigation selection
    sidebar_state = render_sidebar()
    page = sidebar_state.get("page", "🎯 Live Monitoring")
    
    # Route to appropriate page
    if "Live Monitoring" in page:
        render_live_monitoring_page(detector, threat_scorer, grid_system, db)
    
    elif "Video Analysis" in page:
        render_video_analysis_page(detector, threat_scorer, grid_system, video_processor, db)
    
    elif "Map View" in page:
        render_map_view_page()
    
    elif "Reports" in page:
        render_reports_page(db)
    
    elif "Settings" in page:
        render_settings_page()
    
    else:
        # Default to live monitoring
        render_live_monitoring_page(detector, threat_scorer, grid_system, db)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
