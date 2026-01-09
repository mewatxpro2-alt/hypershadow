"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - MILITARY THEME STYLES                        ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Military dark theme CSS and styling constants                       ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Dict, Any

# =============================================================================
# COLOR PALETTE - MILITARY DARK THEME
# =============================================================================
# All colors designed for low-light tactical operations
# High contrast for critical alerts, muted tones for background elements

COLORS: Dict[str, str] = {
    # Primary background colors (dark military theme)
    "bg_primary": "#0a0a0a",           # Main background - near black
    "bg_secondary": "#1a1a1a",         # Secondary panels
    "bg_tertiary": "#252525",          # Cards and elevated elements
    "bg_header": "#0d1117",            # Header background
    
    # Border and divider colors
    "border_primary": "#30363d",       # Main borders
    "border_accent": "#3d5a3d",        # Accent borders (military green tint)
    "border_alert": "#8b0000",         # Alert borders (dark red)
    
    # Text colors (high contrast for readability)
    "text_primary": "#e6e6e6",         # Main text
    "text_secondary": "#a0a0a0",       # Secondary text
    "text_muted": "#6e6e6e",           # Muted/disabled text
    "text_accent": "#4ade80",          # Accent text (military green)
    
    # Alert/Status colors (highly visible)
    "status_critical": "#ff0000",      # Critical - bright red
    "status_high": "#ff6b35",          # High - orange
    "status_medium": "#ffd700",        # Medium - gold/yellow
    "status_low": "#00bfff",           # Low - sky blue
    "status_minimal": "#32cd32",       # Minimal - lime green
    
    # Action colors
    "action_primary": "#2d5a2d",       # Primary action (military green)
    "action_primary_hover": "#3d7a3d", # Primary hover
    "action_danger": "#8b0000",        # Danger action (dark red)
    "action_danger_hover": "#b22222",  # Danger hover
    "action_warning": "#8b4513",       # Warning action (saddle brown)
    
    # Special elements
    "map_grid": "#3d5a3d",             # Map grid lines
    "detection_box": "#00ff00",        # Detection bounding box
    "patrol_marker": "#00bfff",        # Patrol unit markers
    "alert_pulse": "#ff0000",          # Alert pulse animation
    
    # Status indicators
    "online": "#00ff00",               # System online
    "offline": "#ff0000",              # System offline
    "processing": "#ffd700",           # Processing/busy
    "standby": "#808080",              # Standby mode
}

# =============================================================================
# FONT CONFIGURATION
# =============================================================================

FONTS: Dict[str, str] = {
    "primary": "'Roboto Mono', 'Courier New', monospace",
    "display": "'Orbitron', 'Roboto Mono', monospace",
    "heading": "'Rajdhani', 'Roboto', sans-serif",
}

# =============================================================================
# MAIN CSS STYLESHEET
# =============================================================================

MAIN_CSS: str = """
<style>
    /* ========================================================================
       ROOT VARIABLES AND GLOBAL STYLES
       ======================================================================== */
    
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #1a1a1a;
        --bg-tertiary: #252525;
        --text-primary: #e6e6e6;
        --text-secondary: #a0a0a0;
        --accent-green: #4ade80;
        --accent-red: #ff0000;
        --border-color: #30363d;
    }
    
    /* Global background override */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Main container styling */
    .main .block-container {
        padding: 1rem 2rem !important;
        max-width: 100% !important;
    }
    
    /* ========================================================================
       HEADER STYLING
       ======================================================================== */
    
    .military-header {
        background: linear-gradient(135deg, #0d1117 0%, #1a1a1a 100%);
        border: 2px solid #3d5a3d;
        border-radius: 8px;
        padding: 15px 25px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .header-title {
        font-family: 'Orbitron', 'Roboto Mono', monospace;
        font-size: 24px;
        font-weight: 700;
        color: #4ade80;
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
    }
    
    .header-classification {
        font-family: 'Roboto Mono', monospace;
        font-size: 14px;
        color: #ff0000;
        font-weight: 700;
        padding: 5px 15px;
        border: 2px solid #ff0000;
        border-radius: 4px;
        animation: pulse-red 2s infinite;
    }
    
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 5px rgba(255, 0, 0, 0.5); }
        50% { box-shadow: 0 0 20px rgba(255, 0, 0, 0.8); }
    }
    
    /* ========================================================================
       SIDEBAR STYLING
       ======================================================================== */
    
    [data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 2px solid #3d5a3d !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary) !important;
    }
    
    .sidebar-section {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 15px;
    }
    
    .sidebar-title {
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        color: #4ade80;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 1px solid #3d5a3d;
    }
    
    /* ========================================================================
       CARD/PANEL STYLING
       ======================================================================== */
    
    .military-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .military-card-header {
        font-family: 'Roboto Mono', monospace;
        font-size: 14px;
        color: #4ade80;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding-bottom: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid #3d5a3d;
    }
    
    /* ========================================================================
       ALERT STYLING
       ======================================================================== */
    
    .alert-critical {
        background: linear-gradient(90deg, rgba(255, 0, 0, 0.2) 0%, rgba(255, 0, 0, 0.1) 100%);
        border-left: 4px solid #ff0000 !important;
        animation: alert-flash 1s infinite;
    }
    
    .alert-high {
        background: linear-gradient(90deg, rgba(255, 107, 53, 0.2) 0%, rgba(255, 107, 53, 0.1) 100%);
        border-left: 4px solid #ff6b35 !important;
    }
    
    .alert-medium {
        background: linear-gradient(90deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 215, 0, 0.1) 100%);
        border-left: 4px solid #ffd700 !important;
    }
    
    .alert-low {
        background: linear-gradient(90deg, rgba(0, 191, 255, 0.2) 0%, rgba(0, 191, 255, 0.1) 100%);
        border-left: 4px solid #00bfff !important;
    }
    
    @keyframes alert-flash {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* ========================================================================
       BUTTON STYLING
       ======================================================================== */
    
    .stButton > button {
        background-color: #2d5a2d !important;
        color: #e6e6e6 !important;
        border: 1px solid #3d5a3d !important;
        font-family: 'Roboto Mono', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #3d7a3d !important;
        box-shadow: 0 0 10px rgba(74, 222, 128, 0.3) !important;
    }
    
    .danger-button > button {
        background-color: #8b0000 !important;
        border-color: #b22222 !important;
    }
    
    .danger-button > button:hover {
        background-color: #b22222 !important;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.3) !important;
    }
    
    /* ========================================================================
       INPUT STYLING
       ======================================================================== */
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        font-family: 'Roboto Mono', monospace !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4ade80 !important;
        box-shadow: 0 0 5px rgba(74, 222, 128, 0.3) !important;
    }
    
    /* ========================================================================
       TABLE STYLING
       ======================================================================== */
    
    .dataframe {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .dataframe th {
        background-color: #1a2e1a !important;
        color: #4ade80 !important;
        font-family: 'Roboto Mono', monospace !important;
        text-transform: uppercase !important;
    }
    
    .dataframe td {
        border-color: var(--border-color) !important;
    }
    
    /* ========================================================================
       METRIC STYLING
       ======================================================================== */
    
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', 'Roboto Mono', monospace !important;
        color: #4ade80 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Roboto Mono', monospace !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
    }
    
    /* ========================================================================
       STATUS INDICATORS
       ======================================================================== */
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        animation: status-pulse 2s infinite;
    }
    
    .status-online { background-color: #00ff00; }
    .status-offline { background-color: #ff0000; }
    .status-processing { background-color: #ffd700; }
    .status-standby { background-color: #808080; }
    
    @keyframes status-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
    }
    
    /* ========================================================================
       VIDEO PLAYER STYLING
       ======================================================================== */
    
    .video-container {
        background-color: #000000;
        border: 2px solid #3d5a3d;
        border-radius: 8px;
        overflow: hidden;
        position: relative;
    }
    
    .video-overlay {
        position: absolute;
        top: 10px;
        left: 10px;
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        color: #00ff00;
        text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
        z-index: 10;
    }
    
    /* ========================================================================
       MAP STYLING
       ======================================================================== */
    
    .map-container {
        border: 2px solid #3d5a3d;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .grid-label {
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        color: #4ade80;
        font-weight: bold;
    }
    
    /* ========================================================================
       PROGRESS BAR STYLING
       ======================================================================== */
    
    .stProgress > div > div > div > div {
        background-color: #4ade80 !important;
    }
    
    /* ========================================================================
       TAB STYLING
       ======================================================================== */
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-secondary) !important;
        border-bottom: 2px solid #3d5a3d !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Roboto Mono', monospace !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #4ade80 !important;
        border-bottom: 2px solid #4ade80 !important;
    }
    
    /* ========================================================================
       SCROLLBAR STYLING
       ======================================================================== */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3d5a3d;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4d7a4d;
    }
    
    /* ========================================================================
       EXPANDER STYLING
       ======================================================================== */
    
    .streamlit-expanderHeader {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        font-family: 'Roboto Mono', monospace !important;
    }
    
    /* ========================================================================
       FILE UPLOADER STYLING
       ======================================================================== */
    
    [data-testid="stFileUploader"] {
        background-color: var(--bg-secondary) !important;
        border: 2px dashed #3d5a3d !important;
        border-radius: 8px !important;
    }
    
    /* ========================================================================
       CLASSIFICATION BANNER
       ======================================================================== */
    
    .classification-banner {
        background-color: #ff0000;
        color: #ffffff;
        text-align: center;
        padding: 5px;
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 2px;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
    }
    
    /* ========================================================================
       RESPONSIVE ADJUSTMENTS
       ======================================================================== */
    
    @media (max-width: 768px) {
        .header-title {
            font-size: 16px;
        }
        
        .military-card {
            padding: 10px;
        }
    }
</style>
"""

# =============================================================================
# COMPONENT HTML TEMPLATES
# =============================================================================

HEADER_TEMPLATE: str = """
<div class="military-header">
    <div class="header-title">⬡ {title}</div>
    <div class="header-classification">CLASSIFIED</div>
</div>
"""

CLASSIFICATION_BANNER: str = """
<div class="classification-banner">
    ▲ CLASSIFIED - AUTHORIZED PERSONNEL ONLY - HANDLE ACCORDING TO SECURITY PROTOCOLS ▲
</div>
"""

CARD_TEMPLATE: str = """
<div class="military-card">
    <div class="military-card-header">{title}</div>
    <div class="military-card-content">{content}</div>
</div>
"""

ALERT_TEMPLATE: str = """
<div class="military-card alert-{level}">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 14px; font-weight: bold; color: {color};">
                {threat_level} THREAT
            </div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 12px; color: #a0a0a0; margin-top: 5px;">
                {object_type} detected in Grid {grid_ref}
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #6e6e6e;">
                {timestamp}
            </div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #a0a0a0;">
                Confidence: {confidence}%
            </div>
        </div>
    </div>
</div>
"""

STATUS_INDICATOR_TEMPLATE: str = """
<span class="status-indicator status-{status}"></span>
<span style="font-family: 'Roboto Mono', monospace; font-size: 12px; color: #e6e6e6;">
    {label}
</span>
"""

METRIC_TEMPLATE: str = """
<div style="background-color: #1a1a1a; border: 1px solid #30363d; border-radius: 6px; padding: 15px; text-align: center;">
    <div style="font-family: 'Orbitron', monospace; font-size: 28px; color: {color}; margin-bottom: 5px;">
        {value}
    </div>
    <div style="font-family: 'Roboto Mono', monospace; font-size: 11px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px;">
        {label}
    </div>
</div>
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_threat_color(level: str) -> str:
    """
    Get the color code for a threat level.
    
    Args:
        level: Threat level string (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
        
    Returns:
        Hex color code for the threat level
        
    Security Note:
        Colors are designed for maximum visibility in tactical displays
    """
    color_map = {
        "CRITICAL": COLORS["status_critical"],
        "HIGH": COLORS["status_high"],
        "MEDIUM": COLORS["status_medium"],
        "LOW": COLORS["status_low"],
        "MINIMAL": COLORS["status_minimal"],
    }
    return color_map.get(level.upper(), COLORS["text_secondary"])


def get_threat_class(level: str) -> str:
    """
    Get the CSS class for a threat level.
    
    Args:
        level: Threat level string
        
    Returns:
        CSS class name for the alert
    """
    class_map = {
        "CRITICAL": "critical",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
        "MINIMAL": "low",
    }
    return class_map.get(level.upper(), "low")


def render_header(title: str) -> str:
    """
    Render the military-style header HTML.
    
    Args:
        title: Dashboard title to display
        
    Returns:
        Formatted HTML string for the header
    """
    return HEADER_TEMPLATE.format(title=title)


def render_metric(value: str, label: str, color: str = "#4ade80") -> str:
    """
    Render a metric display card.
    
    Args:
        value: The metric value to display
        label: Label describing the metric
        color: Color for the value (default military green)
        
    Returns:
        Formatted HTML string for the metric
    """
    return METRIC_TEMPLATE.format(value=value, label=label, color=color)


def render_alert(
    threat_level: str,
    object_type: str,
    grid_ref: str,
    timestamp: str,
    confidence: float
) -> str:
    """
    Render an alert card with threat information.
    
    Args:
        threat_level: The assessed threat level
        object_type: Type of detected object
        grid_ref: Military grid reference
        timestamp: Time of detection
        confidence: Detection confidence (0-100)
        
    Returns:
        Formatted HTML string for the alert card
    """
    return ALERT_TEMPLATE.format(
        level=get_threat_class(threat_level),
        color=get_threat_color(threat_level),
        threat_level=threat_level,
        object_type=object_type,
        grid_ref=grid_ref,
        timestamp=timestamp,
        confidence=int(confidence)
    )


def render_status(status: str, label: str) -> str:
    """
    Render a status indicator with label.
    
    Args:
        status: Status type (online, offline, processing, standby)
        label: Text label for the status
        
    Returns:
        Formatted HTML string for the status indicator
    """
    return STATUS_INDICATOR_TEMPLATE.format(status=status, label=label)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "COLORS",
    "FONTS",
    "MAIN_CSS",
    "HEADER_TEMPLATE",
    "CLASSIFICATION_BANNER",
    "CARD_TEMPLATE",
    "ALERT_TEMPLATE",
    "STATUS_INDICATOR_TEMPLATE",
    "METRIC_TEMPLATE",
    "get_threat_color",
    "get_threat_class",
    "render_header",
    "render_metric",
    "render_alert",
    "render_status",
]
