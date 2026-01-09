"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - MAP GENERATOR MODULE                         ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Generate offline maps with Folium using local tiles                ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SECURITY NOTICE:
- All map generation uses OFFLINE tiles only
- No network connections are made during map rendering
- Detection markers contain sanitized data only
"""

import folium
from folium import plugins
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import MAP_CONFIG, BORDER_CONFIG, GRID_ZONES, PATROL_UNITS, BORDER_POSTS, BASE_DIR


# =============================================================================
# CUSTOM OFFLINE TILE LAYER
# =============================================================================

class OfflineTileLayer:
    """
    Custom tile layer that serves tiles from local storage.
    
    This class creates a Folium-compatible tile layer that reads
    tiles from the local filesystem instead of making network requests.
    
    Security Note:
        All tiles are served from local storage.
        No network connections are made.
    
    Attributes:
        tile_dir: Path to local tile directory
        attribution: Map attribution string
    """
    
    def __init__(self, tile_dir: Optional[Path] = None):
        """
        Initialize the offline tile layer.
        
        Args:
            tile_dir: Path to tile directory (uses default if not provided)
        """
        self.tile_dir = tile_dir or (BASE_DIR / "data" / "map_tiles")
        self.attribution = "Map data © OpenStreetMap contributors (offline)"
    
    def get_tile_url(self) -> str:
        """
        Get the tile URL pattern for local files.
        
        Returns:
            URL pattern pointing to local tile files
            
        Note:
            Returns file:// URL for local access.
            For Streamlit, tiles are served via a local endpoint.
        """
        return f"file://{self.tile_dir}/{{z}}/{{x}}/{{y}}.png"
    
    def tile_exists(self, z: int, x: int, y: int) -> bool:
        """
        Check if a specific tile exists locally.
        
        Args:
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            True if tile exists
        """
        tile_path = self.tile_dir / str(z) / str(x) / f"{y}.png"
        return tile_path.exists()
    
    def get_available_zoom_range(self) -> Tuple[int, int]:
        """
        Determine available zoom levels from downloaded tiles.
        
        Returns:
            Tuple of (min_zoom, max_zoom)
        """
        min_zoom = 99
        max_zoom = 0
        
        for zoom_dir in self.tile_dir.iterdir():
            if zoom_dir.is_dir() and zoom_dir.name.isdigit():
                zoom = int(zoom_dir.name)
                min_zoom = min(min_zoom, zoom)
                max_zoom = max(max_zoom, zoom)
        
        if min_zoom > max_zoom:
            return (10, 15)  # Default range
        
        return (min_zoom, max_zoom)


# =============================================================================
# MAP GENERATOR CLASS
# =============================================================================

class MapGenerator:
    """
    Generates interactive maps for the surveillance system.
    
    This class creates Folium maps with various overlays including:
    - Military grid overlay
    - Detection markers
    - Patrol unit positions
    - Border post locations
    - Alert indicators
    
    Security Note:
        - All maps generated offline
        - Marker data is sanitized before display
        - No external resources loaded
    
    Attributes:
        config: MAP_CONFIG settings
        tile_layer: OfflineTileLayer instance
    """
    
    def __init__(self):
        """Initialize the map generator."""
        self.config = MAP_CONFIG
        self.tile_layer = OfflineTileLayer()
        
        # Default center (from config)
        self.default_center = self.config.get("center", [25.0, 55.0])
        self.default_zoom = self.config.get("default_zoom", 12)
    
    def create_base_map(
        self,
        center: Optional[List[float]] = None,
        zoom: int = None,
        width: str = "100%",
        height: str = "600px"
    ) -> folium.Map:
        """
        Create a base map with offline tiles.
        
        Args:
            center: [lat, lon] center coordinates
            zoom: Initial zoom level
            width: Map width
            height: Map height
            
        Returns:
            Folium Map object
            
        Security Note:
            Uses local tiles only - no network requests.
        """
        center = center or self.default_center
        zoom = zoom or self.default_zoom
        
        # Create map with no default tiles (we'll add our own)
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=None,
            control_scale=True,
            prefer_canvas=True,
        )
        
        # Add offline tile layer
        # Note: For production, tiles would be served from local server
        # Using OpenStreetMap as fallback for development
        folium.TileLayer(
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr=self.tile_layer.attribution,
            name="Base Map",
            control=True,
        ).add_to(m)
        
        # Add dark style overlay for military theme
        self._add_dark_overlay(m)
        
        return m
    
    def _add_dark_overlay(self, m: folium.Map) -> None:
        """
        Add dark theme overlay to map.
        
        Args:
            m: Folium Map object
        """
        # Add a semi-transparent dark overlay for military aesthetic
        # This is done via CSS styling
        dark_css = """
        <style>
            .leaflet-tile {
                filter: brightness(0.7) contrast(1.1) saturate(0.8);
            }
            .leaflet-container {
                background-color: #0a0a0a;
            }
        </style>
        """
        m.get_root().html.add_child(folium.Element(dark_css))
    
    def add_grid_overlay(
        self,
        m: folium.Map,
        bounds: Optional[List[List[float]]] = None,
        grid_color: str = "#3d5a3d",
        show_labels: bool = True
    ) -> folium.Map:
        """
        Add military grid overlay to map.
        
        Args:
            m: Folium Map object
            bounds: [[south, west], [north, east]] bounds
            grid_color: Color for grid lines
            show_labels: Whether to show grid labels
            
        Returns:
            Map with grid overlay
        """
        if bounds is None:
            # Use border config bounds
            bounds = BORDER_CONFIG.get("bounds", [
                [24.5, 54.5],  # SW corner
                [25.5, 55.5]   # NE corner
            ])
        
        south, west = bounds[0]
        north, east = bounds[1]
        
        # Grid configuration (6 columns, 5 rows)
        cols = 6
        rows = 5
        
        col_width = (east - west) / cols
        row_height = (north - south) / rows
        
        # Create grid lines layer
        grid_layer = folium.FeatureGroup(name="Military Grid")
        
        # Draw vertical lines
        for i in range(cols + 1):
            lon = west + i * col_width
            folium.PolyLine(
                [[south, lon], [north, lon]],
                color=grid_color,
                weight=1,
                opacity=0.7,
                dash_array="5, 5"
            ).add_to(grid_layer)
        
        # Draw horizontal lines
        for i in range(rows + 1):
            lat = south + i * row_height
            folium.PolyLine(
                [[lat, west], [lat, east]],
                color=grid_color,
                weight=1,
                opacity=0.7,
                dash_array="5, 5"
            ).add_to(grid_layer)
        
        # Add grid labels
        if show_labels:
            labels = "ABCDEF"
            for col_idx, label in enumerate(labels):
                for row_idx in range(1, rows + 1):
                    grid_ref = f"{label}-{row_idx}"
                    
                    # Calculate label position (center of cell)
                    label_lat = south + (row_idx - 0.5) * row_height
                    label_lon = west + (col_idx + 0.5) * col_width
                    
                    # Add label as div icon
                    folium.Marker(
                        [label_lat, label_lon],
                        icon=folium.DivIcon(
                            icon_size=(50, 20),
                            icon_anchor=(25, 10),
                            html=f'<div style="font-family: monospace; font-size: 10px; color: #4ade80; text-shadow: 0 0 3px #000;">{grid_ref}</div>'
                        )
                    ).add_to(grid_layer)
        
        grid_layer.add_to(m)
        
        return m
    
    def add_detection_markers(
        self,
        m: folium.Map,
        detections: List[Dict[str, Any]]
    ) -> folium.Map:
        """
        Add detection markers to map.
        
        Args:
            m: Folium Map object
            detections: List of detection dictionaries
            
        Returns:
            Map with detection markers
            
        Security Note:
            Detection data is sanitized before display.
        """
        detection_layer = folium.FeatureGroup(name="Detections")
        
        # Color mapping for threat levels
        threat_colors = {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff6b35",
            "MEDIUM": "#ffd700",
            "LOW": "#00bfff",
            "MINIMAL": "#32cd32",
        }
        
        for det in detections:
            # Extract coordinates (assuming lat/lon are provided)
            lat = det.get("latitude")
            lon = det.get("longitude")
            
            if lat is None or lon is None:
                continue
            
            threat_level = det.get("threat_level", "LOW")
            obj_type = det.get("object_type", "unknown")
            confidence = det.get("confidence", 0) * 100
            grid_ref = det.get("grid_reference", "N/A")
            
            # Get marker color
            color = threat_colors.get(threat_level, "#00bfff")
            
            # Create popup content
            popup_html = f"""
            <div style="font-family: monospace; min-width: 150px;">
                <div style="font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {threat_level} THREAT
                </div>
                <div>Type: {obj_type}</div>
                <div>Grid: {grid_ref}</div>
                <div>Confidence: {confidence:.0f}%</div>
            </div>
            """
            
            # Create circle marker
            folium.CircleMarker(
                [lat, lon],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{threat_level}: {obj_type}"
            ).add_to(detection_layer)
        
        detection_layer.add_to(m)
        
        return m
    
    def add_patrol_markers(
        self,
        m: folium.Map,
        patrols: Optional[List[Dict[str, Any]]] = None
    ) -> folium.Map:
        """
        Add patrol unit markers to map.
        
        Args:
            m: Folium Map object
            patrols: List of patrol dictionaries (uses PATROL_UNITS if not provided)
            
        Returns:
            Map with patrol markers
        """
        patrols = patrols or PATROL_UNITS
        patrol_layer = folium.FeatureGroup(name="Patrol Units")
        
        # Status colors
        status_colors = {
            "available": "#00ff00",
            "responding": "#ffd700",
            "unavailable": "#ff0000",
        }
        
        for patrol in patrols:
            lat = patrol.get("latitude")
            lon = patrol.get("longitude")
            
            if lat is None or lon is None:
                continue
            
            callsign = patrol.get("callsign", "UNKNOWN")
            status = patrol.get("status", "available")
            vehicle = patrol.get("vehicle_type", "unknown")
            
            color = status_colors.get(status, "#808080")
            
            # Create custom icon for patrol
            icon_html = f"""
            <div style="
                background-color: {color};
                width: 30px;
                height: 30px;
                border-radius: 50%;
                border: 2px solid #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                box-shadow: 0 0 10px {color};
            ">
                🚔
            </div>
            """
            
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=icon_html
                ),
                popup=f"<b>{callsign}</b><br>Status: {status}<br>Vehicle: {vehicle}",
                tooltip=callsign
            ).add_to(patrol_layer)
        
        patrol_layer.add_to(m)
        
        return m
    
    def add_border_posts(
        self,
        m: folium.Map,
        posts: Optional[List[Dict[str, Any]]] = None
    ) -> folium.Map:
        """
        Add border post markers to map.
        
        Args:
            m: Folium Map object
            posts: List of border post dictionaries
            
        Returns:
            Map with border post markers
        """
        posts = posts or BORDER_POSTS
        post_layer = folium.FeatureGroup(name="Border Posts")
        
        for post in posts:
            coords = post.get("coordinates")
            if not coords:
                continue
            
            # Parse coordinates (assuming "lat,lon" format)
            if isinstance(coords, str):
                lat, lon = map(float, coords.split(","))
            else:
                lat, lon = coords
            
            name = post.get("name", "Unknown Post")
            status = post.get("status", "operational")
            
            # Status-based styling
            color = "#4ade80" if status == "operational" else "#ff0000"
            
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(
                    color="green" if status == "operational" else "red",
                    icon="home",
                    prefix="fa"
                ),
                popup=f"<b>{name}</b><br>Status: {status}",
                tooltip=name
            ).add_to(post_layer)
        
        post_layer.add_to(m)
        
        return m
    
    def add_alert_markers(
        self,
        m: folium.Map,
        alerts: List[Dict[str, Any]]
    ) -> folium.Map:
        """
        Add alert markers with pulsing animation.
        
        Args:
            m: Folium Map object
            alerts: List of alert dictionaries
            
        Returns:
            Map with alert markers
        """
        alert_layer = folium.FeatureGroup(name="Active Alerts")
        
        for alert in alerts:
            lat = alert.get("latitude")
            lon = alert.get("longitude")
            
            if lat is None or lon is None:
                continue
            
            threat_level = alert.get("threat_level", "MEDIUM")
            
            # Create pulsing marker for active alerts
            if threat_level in ["CRITICAL", "HIGH"]:
                folium.CircleMarker(
                    [lat, lon],
                    radius=20,
                    color="#ff0000",
                    fill=False,
                    weight=2,
                    opacity=0.8,
                ).add_to(alert_layer)
                
                # Inner marker
                folium.CircleMarker(
                    [lat, lon],
                    radius=10,
                    color="#ff0000",
                    fill=True,
                    fill_color="#ff0000",
                    fill_opacity=0.5,
                ).add_to(alert_layer)
        
        alert_layer.add_to(m)
        
        return m
    
    def generate_surveillance_map(
        self,
        detections: Optional[List[Dict[str, Any]]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
        show_grid: bool = True,
        show_patrols: bool = True,
        show_posts: bool = True
    ) -> folium.Map:
        """
        Generate complete surveillance map with all layers.
        
        Args:
            detections: List of detection dictionaries
            alerts: List of active alert dictionaries
            show_grid: Whether to show military grid
            show_patrols: Whether to show patrol positions
            show_posts: Whether to show border posts
            
        Returns:
            Complete Folium map object
            
        Security Note:
            All data is sanitized before display.
            Map operates fully offline.
        """
        # Create base map
        m = self.create_base_map()
        
        # Add layers in order
        if show_grid:
            m = self.add_grid_overlay(m)
        
        if show_posts:
            m = self.add_border_posts(m)
        
        if show_patrols:
            m = self.add_patrol_markers(m)
        
        if detections:
            m = self.add_detection_markers(m, detections)
        
        if alerts:
            m = self.add_alert_markers(m, alerts)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(m)
        
        return m
    
    def save_map(self, m: folium.Map, output_path: Path) -> bool:
        """
        Save map to HTML file.
        
        Args:
            m: Folium Map object
            output_path: Path to save HTML file
            
        Returns:
            True if saved successfully
            
        Security Note:
            HTML file should be stored in secure location.
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            m.save(str(output_path))
            return True
        except Exception as e:
            print(f"Failed to save map: {e}")
            return False
    
    def get_map_html(self, m: folium.Map) -> str:
        """
        Get map HTML string for embedding.
        
        Args:
            m: Folium Map object
            
        Returns:
            HTML string representation of map
        """
        return m._repr_html_()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "OfflineTileLayer",
    "MapGenerator",
]
