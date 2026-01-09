"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - REUSABLE UI COMPONENTS                       ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Reusable UI components for Streamlit dashboard                     ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import base64
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.styles import (
    COLORS, 
    get_threat_color, 
    render_alert, 
    render_metric,
    render_status
)
from config.settings import THREAT_CLASSES, ALERT_CONFIG


# =============================================================================
# VIDEO PLAYER COMPONENT
# =============================================================================

class VideoPlayerComponent:
    """
    Video player component with detection overlay capabilities.
    
    Features:
    - Frame-by-frame playback
    - Detection bounding box overlay
    - Timestamp and metadata display
    - Grid reference overlay
    
    Security Note:
        Video frames are processed locally only.
        No frames are transmitted externally.
    """
    
    def __init__(self):
        """Initialize the video player component."""
        self.current_frame_idx = 0
        self.total_frames = 0
        self.fps = 30.0
    
    def render_frame_with_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        show_grid: bool = True,
        timestamp: Optional[str] = None
    ) -> np.ndarray:
        """
        Render a video frame with detection overlays.
        
        Args:
            frame: Original video frame (BGR format)
            detections: List of detection dictionaries
            show_grid: Whether to show grid overlay
            timestamp: Optional timestamp to display
            
        Returns:
            Frame with overlays drawn
            
        Security Note:
            All processing happens in local memory.
        """
        # Create a copy to avoid modifying original
        output_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Draw grid overlay if enabled
        if show_grid:
            output_frame = self._draw_grid_overlay(output_frame)
        
        # Draw detection boxes
        for det in detections:
            output_frame = self._draw_detection_box(output_frame, det)
        
        # Draw timestamp overlay
        if timestamp:
            output_frame = self._draw_timestamp(output_frame, timestamp)
        
        # Draw classification banner
        output_frame = self._draw_classification_banner(output_frame)
        
        return output_frame
    
    def _draw_grid_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw military grid overlay on frame.
        
        Args:
            frame: Video frame
            
        Returns:
            Frame with grid overlay
        """
        height, width = frame.shape[:2]
        
        # Grid configuration (6 columns A-F, 5 rows 1-5)
        cols = 6
        rows = 5
        cell_width = width // cols
        cell_height = height // rows
        
        # Grid line color (semi-transparent green)
        grid_color = (61, 90, 61)  # BGR for military green
        
        # Draw vertical lines
        for i in range(1, cols):
            x = i * cell_width
            cv2.line(frame, (x, 0), (x, height), grid_color, 1)
        
        # Draw horizontal lines
        for i in range(1, rows):
            y = i * cell_height
            cv2.line(frame, (0, y), (width, y), grid_color, 1)
        
        # Draw grid labels
        labels = "ABCDEF"
        for col_idx, label in enumerate(labels):
            for row_idx in range(1, rows + 1):
                grid_ref = f"{label}-{row_idx}"
                x = col_idx * cell_width + 5
                y = row_idx * cell_height - 5
                cv2.putText(
                    frame, 
                    grid_ref, 
                    (x, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.3, 
                    (74, 222, 128),  # Green
                    1
                )
        
        return frame
    
    def _draw_detection_box(
        self, 
        frame: np.ndarray, 
        detection: Dict[str, Any]
    ) -> np.ndarray:
        """
        Draw detection bounding box with label.
        
        Args:
            frame: Video frame
            detection: Detection dictionary with bbox, class, confidence
            
        Returns:
            Frame with detection box drawn
        """
        # Extract detection info
        bbox = detection.get("bbox", [0, 0, 0, 0])
        obj_class = detection.get("class_name", "unknown")
        confidence = detection.get("confidence", 0.0)
        threat_level = detection.get("threat_level", "LOW")
        
        # Convert bbox coordinates
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        
        # Get color based on threat level
        color_hex = get_threat_color(threat_level)
        # Convert hex to BGR
        color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
        
        # Prepare label
        label = f"{obj_class.upper()} {confidence:.0%}"
        threat_label = f"[{threat_level}]"
        
        # Calculate label position
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        
        # Draw label background
        cv2.rectangle(
            frame, 
            (x1, y1 - 35), 
            (x1 + max(label_w + 10, 100), y1), 
            color_bgr, 
            -1
        )
        
        # Draw label text
        cv2.putText(
            frame, 
            label, 
            (x1 + 5, y1 - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            (255, 255, 255), 
            1
        )
        cv2.putText(
            frame, 
            threat_label, 
            (x1 + 5, y1 - 5), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            (255, 255, 255), 
            1
        )
        
        return frame
    
    def _draw_timestamp(
        self, 
        frame: np.ndarray, 
        timestamp: str
    ) -> np.ndarray:
        """
        Draw timestamp overlay on frame.
        
        Args:
            frame: Video frame
            timestamp: Timestamp string to display
            
        Returns:
            Frame with timestamp overlay
        """
        height, width = frame.shape[:2]
        
        # Position at bottom right
        text = f"UTC: {timestamp}"
        (text_w, text_h), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1
        )
        
        # Draw background
        x = width - text_w - 20
        y = height - 15
        cv2.rectangle(
            frame, 
            (x - 5, y - text_h - 5), 
            (width - 10, y + 5), 
            (0, 0, 0), 
            -1
        )
        
        # Draw text
        cv2.putText(
            frame, 
            text, 
            (x, y), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            (0, 255, 0), 
            1
        )
        
        return frame
    
    def _draw_classification_banner(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw classification banner at top of frame.
        
        Args:
            frame: Video frame
            
        Returns:
            Frame with classification banner
        """
        height, width = frame.shape[:2]
        
        # Draw red banner at top
        cv2.rectangle(frame, (0, 0), (width, 25), (0, 0, 139), -1)
        
        # Draw classification text
        text = "CLASSIFIED - AUTHORIZED VIEWING ONLY"
        (text_w, _), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1
        )
        x = (width - text_w) // 2
        cv2.putText(
            frame, 
            text, 
            (x, 17), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            (255, 255, 255), 
            1
        )
        
        return frame
    
    def display_frame(
        self, 
        frame: np.ndarray, 
        key: str = "video_frame"
    ) -> None:
        """
        Display a frame in Streamlit.
        
        Args:
            frame: Video frame to display (BGR format)
            key: Unique key for the Streamlit component
        """
        # Convert BGR to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, channels="RGB", use_container_width=True)


# =============================================================================
# ALERT PANEL COMPONENT
# =============================================================================

class AlertPanelComponent:
    """
    Alert display panel with threat level indicators.
    
    Features:
    - Color-coded threat levels
    - Action buttons for each alert
    - Auto-refresh capability
    - Audit logging integration
    
    Security Note:
        All alert actions are logged for audit trail.
    """
    
    def __init__(self):
        """Initialize the alert panel."""
        self.alert_sounds = ALERT_CONFIG.get("enable_sounds", True)
    
    def render_alert_list(
        self, 
        alerts: List[Dict[str, Any]], 
        max_display: int = 10
    ) -> Optional[str]:
        """
        Render a list of alerts with action buttons.
        
        Args:
            alerts: List of alert dictionaries
            max_display: Maximum number of alerts to show
            
        Returns:
            Alert ID if an action button was clicked, None otherwise
        """
        if not alerts:
            st.info("📭 No active alerts")
            return None
        
        selected_alert = None
        
        # Display alerts
        for idx, alert in enumerate(alerts[:max_display]):
            threat_level = alert.get("threat_level", "LOW")
            timestamp = alert.get("timestamp", "Unknown")
            grid_ref = alert.get("grid_reference", "N/A")
            obj_type = alert.get("object_type", "Unknown")
            confidence = alert.get("confidence", 0) * 100
            alert_id = alert.get("id", f"alert_{idx}")
            status = alert.get("status", "ACTIVE")
            
            # Render alert card
            st.markdown(
                render_alert(
                    threat_level=threat_level,
                    object_type=obj_type,
                    grid_ref=grid_ref,
                    timestamp=timestamp if isinstance(timestamp, str) else timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    confidence=confidence
                ),
                unsafe_allow_html=True
            )
            
            # Action buttons
            if status == "ACTIVE":
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✓ Acknowledge", key=f"ack_{alert_id}"):
                        selected_alert = ("acknowledge", alert_id)
                
                with col2:
                    if st.button("🚨 Dispatch", key=f"dispatch_{alert_id}"):
                        selected_alert = ("dispatch", alert_id)
                
                with col3:
                    if st.button("✕ Dismiss", key=f"dismiss_{alert_id}"):
                        selected_alert = ("dismiss", alert_id)
            
            st.markdown("---")
        
        # Show count if more alerts exist
        if len(alerts) > max_display:
            remaining = len(alerts) - max_display
            st.caption(f"+ {remaining} more alerts...")
        
        return selected_alert
    
    def render_alert_summary(self, alerts: List[Dict[str, Any]]) -> None:
        """
        Render alert summary statistics.
        
        Args:
            alerts: List of all alerts
        """
        # Count by threat level
        counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "MINIMAL": 0
        }
        
        for alert in alerts:
            level = alert.get("threat_level", "LOW")
            if level in counts:
                counts[level] += 1
        
        # Display as metrics
        cols = st.columns(5)
        
        with cols[0]:
            st.markdown(
                render_metric(
                    str(counts["CRITICAL"]), 
                    "Critical", 
                    COLORS["status_critical"]
                ),
                unsafe_allow_html=True
            )
        
        with cols[1]:
            st.markdown(
                render_metric(
                    str(counts["HIGH"]), 
                    "High", 
                    COLORS["status_high"]
                ),
                unsafe_allow_html=True
            )
        
        with cols[2]:
            st.markdown(
                render_metric(
                    str(counts["MEDIUM"]), 
                    "Medium", 
                    COLORS["status_medium"]
                ),
                unsafe_allow_html=True
            )
        
        with cols[3]:
            st.markdown(
                render_metric(
                    str(counts["LOW"]), 
                    "Low", 
                    COLORS["status_low"]
                ),
                unsafe_allow_html=True
            )
        
        with cols[4]:
            st.markdown(
                render_metric(
                    str(len(alerts)), 
                    "Total", 
                    COLORS["text_accent"]
                ),
                unsafe_allow_html=True
            )


# =============================================================================
# METRIC DASHBOARD COMPONENT
# =============================================================================

class MetricDashboardComponent:
    """
    Dashboard metrics display component.
    
    Features:
    - Real-time metric updates
    - Trend indicators
    - Status monitoring
    """
    
    def render_system_metrics(
        self, 
        detections_today: int,
        alerts_active: int,
        patrols_dispatched: int,
        system_status: str
    ) -> None:
        """
        Render system-wide metrics.
        
        Args:
            detections_today: Number of detections today
            alerts_active: Number of active alerts
            patrols_dispatched: Number of patrols dispatched
            system_status: Current system status
        """
        cols = st.columns(4)
        
        with cols[0]:
            st.metric(
                label="DETECTIONS TODAY",
                value=detections_today,
                delta=None
            )
        
        with cols[1]:
            st.metric(
                label="ACTIVE ALERTS",
                value=alerts_active,
                delta=None
            )
        
        with cols[2]:
            st.metric(
                label="PATROLS DISPATCHED",
                value=patrols_dispatched,
                delta=None
            )
        
        with cols[3]:
            status_color = "🟢" if system_status == "ONLINE" else "🔴"
            st.metric(
                label="SYSTEM STATUS",
                value=f"{status_color} {system_status}",
                delta=None
            )
    
    def render_detection_stats(
        self, 
        stats: Dict[str, int]
    ) -> None:
        """
        Render detection statistics by object type.
        
        Args:
            stats: Dictionary of object_type -> count
        """
        st.markdown("""
        <div style="
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: #4ade80;
            text-transform: uppercase;
            margin-bottom: 10px;
        ">
            Detection Breakdown
        </div>
        """, unsafe_allow_html=True)
        
        for obj_type, count in stats.items():
            # Create a progress-bar style display
            max_count = max(stats.values()) if stats.values() else 1
            percentage = (count / max_count) * 100
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            ">
                <span style="
                    font-family: 'Roboto Mono', monospace;
                    font-size: 11px;
                    color: #e6e6e6;
                    text-transform: uppercase;
                ">
                    {obj_type}
                </span>
                <span style="
                    font-family: 'Orbitron', monospace;
                    font-size: 14px;
                    color: #4ade80;
                ">
                    {count}
                </span>
            </div>
            <div style="
                background-color: #252525;
                border-radius: 4px;
                height: 4px;
                margin-bottom: 12px;
            ">
                <div style="
                    background-color: #4ade80;
                    border-radius: 4px;
                    height: 4px;
                    width: {percentage}%;
                "></div>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# PATROL STATUS COMPONENT
# =============================================================================

class PatrolStatusComponent:
    """
    Patrol unit status display component.
    
    Features:
    - Real-time patrol positions
    - Status indicators
    - Dispatch interface
    """
    
    def render_patrol_list(
        self, 
        patrols: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Render list of patrol units with status.
        
        Args:
            patrols: List of patrol unit dictionaries
            
        Returns:
            Patrol ID if dispatch button clicked, None otherwise
        """
        selected_patrol = None
        
        for patrol in patrols:
            callsign = patrol.get("callsign", "UNKNOWN")
            status = patrol.get("status", "unknown")
            grid = patrol.get("current_grid", "N/A")
            
            # Status color
            status_class = "online" if status == "available" else \
                          "processing" if status == "responding" else \
                          "offline"
            
            st.markdown(f"""
            <div style="
                background-color: #1a1a1a;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 10px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        {render_status(status_class, callsign)}
                    </div>
                    <div style="
                        font-family: 'Roboto Mono', monospace;
                        font-size: 10px;
                        color: #6e6e6e;
                    ">
                        Grid: {grid}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        return selected_patrol


# =============================================================================
# FILE UPLOADER COMPONENT
# =============================================================================

class FileUploaderComponent:
    """
    Secure file upload component for video files.
    
    Security Note:
        - Files are validated before processing
        - Only allowed extensions are accepted
        - File size limits are enforced
    """
    
    def __init__(self):
        """Initialize the file uploader."""
        self.allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        self.max_size_mb = 500  # Maximum file size in MB
    
    def render_uploader(self, key: str = "video_uploader") -> Optional[bytes]:
        """
        Render the file upload interface.
        
        Args:
            key: Unique key for the uploader
            
        Returns:
            File bytes if uploaded, None otherwise
        """
        st.markdown("""
        <div style="
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: #4ade80;
            text-transform: uppercase;
            margin-bottom: 10px;
        ">
            📁 Upload Drone Footage
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Select video file",
            type=["mp4", "avi", "mov", "mkv", "webm"],
            key=key,
            help="Supported formats: MP4, AVI, MOV, MKV, WebM. Max size: 500MB"
        )
        
        if uploaded_file:
            # Validate file
            file_ext = Path(uploaded_file.name).suffix.lower()
            
            if file_ext not in self.allowed_extensions:
                st.error(f"Invalid file type: {file_ext}")
                return None
            
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            
            if file_size_mb > self.max_size_mb:
                st.error(f"File too large: {file_size_mb:.1f}MB (max: {self.max_size_mb}MB)")
                return None
            
            # Show file info
            st.markdown(f"""
            <div style="
                background-color: #1a2e1a;
                border: 1px solid #3d5a3d;
                border-radius: 6px;
                padding: 10px;
                margin-top: 10px;
            ">
                <div style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #e6e6e6;">
                    📎 {uploaded_file.name}
                </div>
                <div style="font-family: 'Roboto Mono', monospace; font-size: 10px; color: #6e6e6e; margin-top: 4px;">
                    Size: {file_size_mb:.1f} MB
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            return uploaded_file.getvalue()
        
        return None


# =============================================================================
# ACTIVITY LOG COMPONENT
# =============================================================================

class ActivityLogComponent:
    """
    Activity/audit log display component.
    
    Security Note:
        Shows recent system activity for situational awareness.
    """
    
    def render_log(
        self, 
        entries: List[Dict[str, Any]], 
        max_entries: int = 20
    ) -> None:
        """
        Render activity log entries.
        
        Args:
            entries: List of log entry dictionaries
            max_entries: Maximum entries to display
        """
        st.markdown("""
        <div style="
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: #4ade80;
            text-transform: uppercase;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #3d5a3d;
        ">
            📋 Recent Activity
        </div>
        """, unsafe_allow_html=True)
        
        if not entries:
            st.caption("No recent activity")
            return
        
        for entry in entries[:max_entries]:
            timestamp = entry.get("timestamp", "")
            action = entry.get("action", "")
            details = entry.get("details", "")
            user = entry.get("user", "system")
            
            # Format timestamp
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%H:%M:%S")
            
            st.markdown(f"""
            <div style="
                font-family: 'Roboto Mono', monospace;
                font-size: 10px;
                padding: 4px 0;
                border-bottom: 1px solid #252525;
            ">
                <span style="color: #6e6e6e;">[{timestamp}]</span>
                <span style="color: #a0a0a0;"> {user}:</span>
                <span style="color: #e6e6e6;"> {action}</span>
                <span style="color: #6e6e6e;"> - {details}</span>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "VideoPlayerComponent",
    "AlertPanelComponent",
    "MetricDashboardComponent",
    "PatrolStatusComponent",
    "FileUploaderComponent",
    "ActivityLogComponent",
]
