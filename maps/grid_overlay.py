"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - MILITARY GRID OVERLAY                        ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Military grid reference overlay for maps                            ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import folium
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import BORDER_CONFIG, GRID_ZONES


# =============================================================================
# GRID OVERLAY CLASS
# =============================================================================

class MilitaryGridOverlay:
    """
    Creates military-style grid overlays for Folium maps.
    
    This class generates MGRS-style (Military Grid Reference System) grid
    overlays that can be added to Folium maps for tactical visualization.
    
    Grid Structure:
        - Columns: A through F (west to east)
        - Rows: 1 through 5 (south to north)
        - Total: 30 grid cells
        
    Security Note:
        Grid references are used for secure location communication.
        Actual coordinates should not be transmitted over unsecure channels.
    
    Attributes:
        bounds: Geographic bounds [[south, west], [north, east]]
        cols: Number of columns (default: 6)
        rows: Number of rows (default: 5)
        col_labels: Column label characters
    """
    
    def __init__(
        self,
        bounds: Optional[List[List[float]]] = None,
        cols: int = 6,
        rows: int = 5
    ):
        """
        Initialize the grid overlay.
        
        Args:
            bounds: [[south, west], [north, east]] bounds
            cols: Number of columns
            rows: Number of rows
        """
        # Use default bounds from config if not provided
        self.bounds = bounds or BORDER_CONFIG.get("bounds", [
            [24.5, 54.5],
            [25.5, 55.5]
        ])
        
        self.cols = cols
        self.rows = rows
        self.col_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:cols]
        
        # Calculate cell dimensions
        self.south, self.west = self.bounds[0]
        self.north, self.east = self.bounds[1]
        
        self.cell_width = (self.east - self.west) / self.cols
        self.cell_height = (self.north - self.south) / self.rows
    
    def get_cell_bounds(self, col: int, row: int) -> Dict[str, float]:
        """
        Get the geographic bounds of a specific grid cell.
        
        Args:
            col: Column index (0-based)
            row: Row index (0-based)
            
        Returns:
            Dictionary with bounds: {north, south, east, west, center_lat, center_lon}
        """
        cell_south = self.south + row * self.cell_height
        cell_north = cell_south + self.cell_height
        cell_west = self.west + col * self.cell_width
        cell_east = cell_west + self.cell_width
        
        return {
            "north": cell_north,
            "south": cell_south,
            "east": cell_east,
            "west": cell_west,
            "center_lat": (cell_north + cell_south) / 2,
            "center_lon": (cell_east + cell_west) / 2,
        }
    
    def get_grid_reference(self, lat: float, lon: float) -> Optional[str]:
        """
        Get the grid reference for a coordinate.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Grid reference string (e.g., "C-3") or None if outside grid
        """
        # Check if within bounds
        if lat < self.south or lat > self.north:
            return None
        if lon < self.west or lon > self.east:
            return None
        
        # Calculate cell indices
        col = int((lon - self.west) / self.cell_width)
        row = int((lat - self.south) / self.cell_height)
        
        # Clamp to valid range
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        
        # Generate reference (row is 1-indexed from bottom)
        col_label = self.col_labels[col]
        row_label = row + 1
        
        return f"{col_label}-{row_label}"
    
    def get_coordinates_from_reference(self, grid_ref: str) -> Optional[Dict[str, float]]:
        """
        Get center coordinates from a grid reference.
        
        Args:
            grid_ref: Grid reference string (e.g., "C-3")
            
        Returns:
            Dictionary with center_lat, center_lon or None if invalid
        """
        try:
            parts = grid_ref.upper().split("-")
            if len(parts) != 2:
                return None
            
            col_label = parts[0]
            row_label = int(parts[1])
            
            if col_label not in self.col_labels:
                return None
            if row_label < 1 or row_label > self.rows:
                return None
            
            col = self.col_labels.index(col_label)
            row = row_label - 1  # Convert to 0-indexed
            
            return self.get_cell_bounds(col, row)
            
        except (ValueError, IndexError):
            return None
    
    def create_grid_lines(
        self,
        line_color: str = "#3d5a3d",
        line_weight: int = 1,
        line_opacity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Create grid line definitions.
        
        Args:
            line_color: Color for grid lines
            line_weight: Line weight in pixels
            line_opacity: Line opacity (0-1)
            
        Returns:
            List of line definitions for Folium
        """
        lines = []
        
        # Vertical lines
        for i in range(self.cols + 1):
            lon = self.west + i * self.cell_width
            lines.append({
                "coordinates": [[self.south, lon], [self.north, lon]],
                "color": line_color,
                "weight": line_weight,
                "opacity": line_opacity,
            })
        
        # Horizontal lines
        for i in range(self.rows + 1):
            lat = self.south + i * self.cell_height
            lines.append({
                "coordinates": [[lat, self.west], [lat, self.east]],
                "color": line_color,
                "weight": line_weight,
                "opacity": line_opacity,
            })
        
        return lines
    
    def create_grid_labels(
        self,
        font_size: int = 10,
        font_color: str = "#4ade80"
    ) -> List[Dict[str, Any]]:
        """
        Create grid label definitions.
        
        Args:
            font_size: Font size in pixels
            font_color: Text color
            
        Returns:
            List of label definitions
        """
        labels = []
        
        for col in range(self.cols):
            for row in range(self.rows):
                bounds = self.get_cell_bounds(col, row)
                grid_ref = f"{self.col_labels[col]}-{row + 1}"
                
                labels.append({
                    "lat": bounds["center_lat"],
                    "lon": bounds["center_lon"],
                    "text": grid_ref,
                    "font_size": font_size,
                    "font_color": font_color,
                })
        
        return labels
    
    def create_zone_polygons(
        self,
        zones: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create zone polygon definitions with threat-level coloring.
        
        Args:
            zones: Zone definitions (uses GRID_ZONES if not provided)
            
        Returns:
            List of polygon definitions
        """
        zones = zones or GRID_ZONES
        polygons = []
        
        # Threat modifier to color mapping
        threat_colors = {
            -1: "rgba(50, 205, 50, 0.2)",    # Low threat - green
            0: "rgba(255, 215, 0, 0.2)",      # Normal - yellow
            1: "rgba(255, 165, 0, 0.2)",      # Elevated - orange
            2: "rgba(255, 69, 0, 0.2)",       # High - red-orange
            3: "rgba(255, 0, 0, 0.2)",        # Critical - red
        }
        
        for zone_id, zone_info in zones.items():
            # Parse zone ID (e.g., "A" -> column 0)
            if len(zone_id) == 1 and zone_id in self.col_labels:
                col = self.col_labels.index(zone_id)
                
                # Create polygon for entire column
                col_west = self.west + col * self.cell_width
                col_east = col_west + self.cell_width
                
                threat_mod = zone_info.get("threat_modifier", 0)
                fill_color = threat_colors.get(threat_mod, "rgba(128, 128, 128, 0.2)")
                
                polygons.append({
                    "coordinates": [
                        [self.south, col_west],
                        [self.north, col_west],
                        [self.north, col_east],
                        [self.south, col_east],
                    ],
                    "fill_color": fill_color,
                    "border_color": "#3d5a3d",
                    "name": zone_info.get("name", f"Zone {zone_id}"),
                    "terrain": zone_info.get("terrain", "unknown"),
                    "threat_modifier": threat_mod,
                })
        
        return polygons
    
    def add_to_map(
        self,
        m: folium.Map,
        show_lines: bool = True,
        show_labels: bool = True,
        show_zones: bool = True
    ) -> folium.Map:
        """
        Add grid overlay to a Folium map.
        
        Args:
            m: Folium Map object
            show_lines: Whether to show grid lines
            show_labels: Whether to show grid labels
            show_zones: Whether to show zone coloring
            
        Returns:
            Map with grid overlay added
        """
        # Create feature group for grid
        grid_group = folium.FeatureGroup(name="Military Grid")
        
        # Add zone polygons (background)
        if show_zones:
            for polygon in self.create_zone_polygons():
                coords = polygon["coordinates"]
                # Convert to [lat, lon] pairs
                folium_coords = [[c[0], c[1]] for c in coords]
                
                folium.Polygon(
                    locations=folium_coords,
                    color=polygon["border_color"],
                    fill=True,
                    fill_color=polygon["fill_color"],
                    fill_opacity=0.3,
                    weight=1,
                    popup=f"{polygon['name']}<br>Terrain: {polygon['terrain']}<br>Threat: {polygon['threat_modifier']:+d}"
                ).add_to(grid_group)
        
        # Add grid lines
        if show_lines:
            for line in self.create_grid_lines():
                folium.PolyLine(
                    line["coordinates"],
                    color=line["color"],
                    weight=line["weight"],
                    opacity=line["opacity"],
                    dash_array="5, 5"
                ).add_to(grid_group)
        
        # Add grid labels
        if show_labels:
            for label in self.create_grid_labels():
                folium.Marker(
                    [label["lat"], label["lon"]],
                    icon=folium.DivIcon(
                        icon_size=(50, 20),
                        icon_anchor=(25, 10),
                        html=f'''
                        <div style="
                            font-family: monospace;
                            font-size: {label["font_size"]}px;
                            color: {label["font_color"]};
                            text-shadow: 0 0 3px #000, 0 0 5px #000;
                            font-weight: bold;
                        ">
                            {label["text"]}
                        </div>
                        '''
                    )
                ).add_to(grid_group)
        
        grid_group.add_to(m)
        
        return m
    
    def get_adjacent_cells(self, grid_ref: str) -> List[str]:
        """
        Get adjacent grid cells for a reference.
        
        Args:
            grid_ref: Grid reference string (e.g., "C-3")
            
        Returns:
            List of adjacent grid references
        """
        try:
            parts = grid_ref.upper().split("-")
            col_label = parts[0]
            row = int(parts[1])
            
            col = self.col_labels.index(col_label)
            
            adjacent = []
            
            # Check all 8 directions
            for dc in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if dc == 0 and dr == 0:
                        continue
                    
                    new_col = col + dc
                    new_row = row + dr
                    
                    if 0 <= new_col < self.cols and 1 <= new_row <= self.rows:
                        adjacent.append(f"{self.col_labels[new_col]}-{new_row}")
            
            return adjacent
            
        except (ValueError, IndexError):
            return []
    
    def calculate_distance(
        self,
        ref1: str,
        ref2: str
    ) -> Optional[int]:
        """
        Calculate grid distance between two references.
        
        Args:
            ref1: First grid reference
            ref2: Second grid reference
            
        Returns:
            Manhattan distance in grid cells, or None if invalid
        """
        try:
            parts1 = ref1.upper().split("-")
            parts2 = ref2.upper().split("-")
            
            col1 = self.col_labels.index(parts1[0])
            row1 = int(parts1[1])
            
            col2 = self.col_labels.index(parts2[0])
            row2 = int(parts2[1])
            
            return abs(col2 - col1) + abs(row2 - row1)
            
        except (ValueError, IndexError):
            return None


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "MilitaryGridOverlay",
]
