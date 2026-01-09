"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - MILITARY GRID REFERENCE SYSTEM
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: core/grid_system.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    This module implements a military-style grid reference system for
    mapping video pixel coordinates to grid zones.
    
GRID LAYOUT:
    The video frame is divided into a 6x5 grid (columns A-F, rows 1-5):
    
        A       B       C       D       E       F
      ┌───────┬───────┬───────┬───────┬───────┬───────┐
    1 │ A-1   │ B-1   │ C-1   │ D-1   │ E-1   │ F-1   │  ← Enemy Territory
      ├───────┼───────┼───────┼───────┼───────┼───────┤
    2 │ A-2   │ B-2   │ C-2   │ D-2   │ E-2   │ F-2   │  ← Approach Zone
      ├───────┼───────┼───────┼───────┼───────┼───────┤
    3 │ A-3   │ B-3   │ C-3   │ D-3   │ E-3   │ F-3   │  ← BORDER LINE
      ├───────┼───────┼───────┼───────┼───────┼───────┤
    4 │ A-4   │ B-4   │ C-4   │ D-4   │ E-4   │ F-4   │  ← Our Territory
      ├───────┼───────┼───────┼───────┼───────┼───────┤
    5 │ A-5   │ B-5   │ C-5   │ D-5   │ E-5   │ F-5   │  ← Safe Zone/Base
      └───────┴───────┴───────┴───────┴───────┴───────┘

COORDINATE SYSTEM:
    - Origin (0,0) is top-left of video frame
    - X increases left-to-right (columns A→F)
    - Y increases top-to-bottom (rows 1→5)
    - Default video size: 640x480 pixels

SECURITY NOTE:
    Grid zone definitions affect threat scoring. Any changes should be
    coordinated with operations and documented in audit log.

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports
from config.settings import (
    BORDER_CONFIG,
    PATROL_UNITS,
    BORDER_POSTS,
    CONFIG_DIR,
)

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GridCell:
    """
    Represents a single cell in the military grid.
    
    Attributes:
        reference: Grid reference string (e.g., "C-3")
        column: Column letter (A-F)
        row: Row number (1-5)
        pixel_bounds: (x1, y1, x2, y2) pixel boundaries
        center_pixel: (x, y) center point in pixels
        sensitivity: Zone sensitivity level
        terrain: Terrain type
        nearest_patrol: ID of nearest patrol unit
        patrol_eta: Estimated patrol arrival time in minutes
    """
    reference: str
    column: str
    row: str
    pixel_bounds: Tuple[int, int, int, int]
    center_pixel: Tuple[int, int]
    sensitivity: str = "normal"
    terrain: str = "unknown"
    nearest_patrol: str = ""
    patrol_eta: int = 10
    distance_to_border: int = 0
    risk_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reference": self.reference,
            "column": self.column,
            "row": self.row,
            "pixel_bounds": self.pixel_bounds,
            "center_pixel": self.center_pixel,
            "sensitivity": self.sensitivity,
            "terrain": self.terrain,
            "nearest_patrol": self.nearest_patrol,
            "patrol_eta": self.patrol_eta,
            "distance_to_border": self.distance_to_border,
            "risk_factors": self.risk_factors,
        }


@dataclass
class PatrolUnit:
    """
    Represents a patrol unit available for dispatch.
    
    Attributes:
        id: Unique patrol identifier
        name: Human-readable name
        type: Unit type (vehicle/foot)
        base_grid: Grid location of patrol base
        status: Current status (active/standby/dispatched)
        personnel: Number of personnel
        response_time: Base response time in minutes
    """
    id: str
    name: str
    type: str
    base_grid: str
    status: str
    personnel: int = 4
    response_time: int = 10
    lat: float = 0.0
    lon: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "base_grid": self.base_grid,
            "status": self.status,
            "personnel": self.personnel,
            "response_time": self.response_time,
            "lat": self.lat,
            "lon": self.lon,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MILITARY GRID SYSTEM CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class MilitaryGridSystem:
    """
    Military-style grid reference system for border surveillance.
    
    This class handles all grid-related calculations including:
    - Converting pixel coordinates to grid references
    - Looking up zone information
    - Calculating distances and patrol ETAs
    - Managing patrol unit assignments
    
    Example:
        >>> grid = MilitaryGridSystem()
        >>> cell = grid.pixel_to_grid(320, 240)
        >>> print(cell.reference)
        'C-3'
        >>> print(cell.sensitivity)
        'medium'
    """
    
    def __init__(
        self,
        video_width: int = None,
        video_height: int = None,
        zones_file: Optional[str] = None
    ):
        """
        Initialize the military grid system.
        
        Args:
            video_width: Video frame width in pixels
            video_height: Video frame height in pixels
            zones_file: Path to zones.json configuration
        """
        self.video_width = video_width or BORDER_CONFIG["video_width"]
        self.video_height = video_height or BORDER_CONFIG["video_height"]
        
        self.columns = BORDER_CONFIG["grid_columns"]
        self.rows = BORDER_CONFIG["grid_rows"]
        self.column_labels = BORDER_CONFIG["column_labels"]
        self.row_labels = BORDER_CONFIG["row_labels"]
        
        # Calculate cell dimensions
        self.cell_width = self.video_width / self.columns
        self.cell_height = self.video_height / self.rows
        
        # Load zone data
        self.zones_file = zones_file or str(CONFIG_DIR / "zones.json")
        self.zones_data = self._load_zones()
        
        # Build grid lookup table
        self.grid_cells: Dict[str, GridCell] = {}
        self._build_grid()
        
        # Initialize patrol units
        self.patrol_units: Dict[str, PatrolUnit] = {}
        self._load_patrol_units()
        
        logger.info(
            f"MilitaryGridSystem initialized: {self.columns}x{self.rows} grid, "
            f"{len(self.patrol_units)} patrol units"
        )
    
    def _load_zones(self) -> Dict[str, Any]:
        """Load zone definitions from JSON file."""
        try:
            zones_path = Path(self.zones_file)
            if zones_path.exists():
                with open(zones_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Zones file not found: {zones_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading zones: {e}")
            return {}
    
    def _build_grid(self) -> None:
        """Build the complete grid lookup table."""
        zones = self.zones_data.get("zones", {})
        
        for col_idx, col_label in enumerate(self.column_labels):
            for row_idx, row_label in enumerate(self.row_labels):
                ref = f"{col_label}-{row_label}"
                
                # Calculate pixel boundaries
                x1 = int(col_idx * self.cell_width)
                y1 = int(row_idx * self.cell_height)
                x2 = int((col_idx + 1) * self.cell_width)
                y2 = int((row_idx + 1) * self.cell_height)
                
                # Calculate center point
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                # Get zone info from configuration
                zone_info = zones.get(ref, {})
                
                # Create grid cell
                cell = GridCell(
                    reference=ref,
                    column=col_label,
                    row=row_label,
                    pixel_bounds=(x1, y1, x2, y2),
                    center_pixel=(cx, cy),
                    sensitivity=zone_info.get("sensitivity", "normal"),
                    terrain=zone_info.get("terrain", "unknown"),
                    nearest_patrol=zone_info.get("nearest_patrol", ""),
                    patrol_eta=zone_info.get("patrol_eta_minutes", 10),
                    distance_to_border=zone_info.get("distance_to_border_m", 0),
                    risk_factors=zone_info.get("risk_factors", [])
                )
                
                self.grid_cells[ref] = cell
    
    def _load_patrol_units(self) -> None:
        """Load patrol unit definitions."""
        # Load from zones.json if available
        patrol_data = self.zones_data.get("patrol_units", PATROL_UNITS)
        
        for unit in patrol_data:
            patrol = PatrolUnit(
                id=unit.get("id", ""),
                name=unit.get("name", ""),
                type=unit.get("type", "vehicle"),
                base_grid=unit.get("base_grid", ""),
                status=unit.get("status", "standby"),
                personnel=unit.get("personnel_count", 4),
                response_time=unit.get("response_time_minutes", 10),
                lat=unit.get("lat", 0.0),
                lon=unit.get("lon", 0.0),
            )
            self.patrol_units[patrol.id] = patrol
    
    def pixel_to_grid(self, x: int, y: int) -> GridCell:
        """
        Convert pixel coordinates to grid cell.
        
        Args:
            x: X pixel coordinate
            y: Y pixel coordinate
            
        Returns:
            GridCell object for the cell containing the point
            
        Example:
            >>> cell = grid.pixel_to_grid(320, 240)
            >>> print(cell.reference)
            'C-3'
        """
        # Clamp coordinates to valid range
        x = max(0, min(x, self.video_width - 1))
        y = max(0, min(y, self.video_height - 1))
        
        # Calculate cell indices
        col_idx = min(int(x / self.cell_width), self.columns - 1)
        row_idx = min(int(y / self.cell_height), self.rows - 1)
        
        # Get reference
        ref = f"{self.column_labels[col_idx]}-{self.row_labels[row_idx]}"
        
        return self.grid_cells.get(ref, self._create_default_cell(ref))
    
    def grid_to_pixel(self, reference: str) -> Tuple[int, int]:
        """
        Get center pixel coordinates for a grid reference.
        
        Args:
            reference: Grid reference string (e.g., "C-3")
            
        Returns:
            (x, y) pixel coordinates of cell center
            
        Example:
            >>> x, y = grid.grid_to_pixel("C-3")
            >>> print(f"Center at ({x}, {y})")
        """
        cell = self.grid_cells.get(reference)
        if cell:
            return cell.center_pixel
        
        # Parse reference and calculate
        try:
            col_label, row_label = reference.split("-")
            col_idx = self.column_labels.index(col_label)
            row_idx = self.row_labels.index(row_label)
            
            cx = int((col_idx + 0.5) * self.cell_width)
            cy = int((row_idx + 0.5) * self.cell_height)
            
            return (cx, cy)
        except (ValueError, IndexError):
            logger.warning(f"Invalid grid reference: {reference}")
            return (self.video_width // 2, self.video_height // 2)
    
    def _create_default_cell(self, reference: str) -> GridCell:
        """Create a default grid cell for unknown references."""
        return GridCell(
            reference=reference,
            column=reference.split("-")[0] if "-" in reference else "?",
            row=reference.split("-")[1] if "-" in reference else "?",
            pixel_bounds=(0, 0, 0, 0),
            center_pixel=(0, 0),
            sensitivity="unknown",
            terrain="unknown"
        )
    
    def get_cell(self, reference: str) -> Optional[GridCell]:
        """
        Get grid cell by reference.
        
        Args:
            reference: Grid reference string
            
        Returns:
            GridCell object or None if not found
        """
        return self.grid_cells.get(reference)
    
    def get_all_cells(self) -> List[GridCell]:
        """
        Get all grid cells.
        
        Returns:
            List of all GridCell objects
        """
        return list(self.grid_cells.values())
    
    def get_adjacent_cells(self, reference: str) -> List[GridCell]:
        """
        Get all cells adjacent to a given cell (including diagonals).
        
        Args:
            reference: Grid reference string
            
        Returns:
            List of adjacent GridCell objects
        """
        try:
            col_label, row_label = reference.split("-")
            col_idx = self.column_labels.index(col_label)
            row_idx = self.row_labels.index(row_label)
        except (ValueError, IndexError):
            return []
        
        adjacent = []
        
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue  # Skip self
                
                new_col = col_idx + dc
                new_row = row_idx + dr
                
                if 0 <= new_col < self.columns and 0 <= new_row < self.rows:
                    ref = f"{self.column_labels[new_col]}-{self.row_labels[new_row]}"
                    cell = self.grid_cells.get(ref)
                    if cell:
                        adjacent.append(cell)
        
        return adjacent
    
    def get_nearest_patrol(self, reference: str) -> Tuple[Optional[PatrolUnit], int]:
        """
        Find the nearest patrol unit to a grid cell.
        
        Args:
            reference: Grid reference string
            
        Returns:
            Tuple of (PatrolUnit, estimated_eta_minutes)
            Returns (None, -1) if no patrol available
            
        Example:
            >>> patrol, eta = grid.get_nearest_patrol("C-2")
            >>> print(f"{patrol.name} - ETA: {eta} min")
        """
        cell = self.grid_cells.get(reference)
        if not cell:
            return (None, -1)
        
        # First check pre-configured nearest patrol
        if cell.nearest_patrol:
            patrol = self.patrol_units.get(cell.nearest_patrol)
            if patrol and patrol.status in ["active", "standby"]:
                return (patrol, cell.patrol_eta)
        
        # Find nearest active patrol by grid distance
        best_patrol = None
        best_eta = float('inf')
        
        for patrol in self.patrol_units.values():
            if patrol.status not in ["active", "standby"]:
                continue
            
            # Calculate grid distance
            distance = self._grid_distance(reference, patrol.base_grid)
            
            # Estimate ETA based on distance and patrol type
            eta = self._estimate_eta(distance, patrol.type)
            
            if eta < best_eta:
                best_eta = eta
                best_patrol = patrol
        
        if best_patrol:
            return (best_patrol, int(best_eta))
        
        return (None, -1)
    
    def _grid_distance(self, ref1: str, ref2: str) -> float:
        """
        Calculate grid distance between two cells (in cell units).
        
        Uses Chebyshev distance (max of column/row difference).
        """
        try:
            col1, row1 = ref1.split("-")
            col2, row2 = ref2.split("-")
            
            col_dist = abs(
                self.column_labels.index(col1) - 
                self.column_labels.index(col2)
            )
            row_dist = abs(
                self.row_labels.index(row1) - 
                self.row_labels.index(row2)
            )
            
            return max(col_dist, row_dist)
        except (ValueError, IndexError):
            return float('inf')
    
    def _estimate_eta(self, grid_distance: float, patrol_type: str) -> float:
        """
        Estimate patrol arrival time based on distance and type.
        
        Args:
            grid_distance: Distance in grid cells
            patrol_type: "vehicle" or "foot"
            
        Returns:
            Estimated time in minutes
        """
        # Base time per grid cell (minutes)
        if patrol_type == "vehicle":
            time_per_cell = 1.5  # ~2 min per cell for vehicles
        else:
            time_per_cell = 4.0  # ~4 min per cell for foot patrol
        
        return grid_distance * time_per_cell + 2  # +2 min mobilization time
    
    def get_cells_by_sensitivity(self, sensitivity: str) -> List[GridCell]:
        """
        Get all cells with a specific sensitivity level.
        
        Args:
            sensitivity: Level string (critical/high/medium/normal/low)
            
        Returns:
            List of matching GridCell objects
        """
        return [
            cell for cell in self.grid_cells.values()
            if cell.sensitivity == sensitivity
        ]
    
    def get_cells_in_row(self, row: str) -> List[GridCell]:
        """
        Get all cells in a specific row.
        
        Args:
            row: Row label (1-5)
            
        Returns:
            List of GridCell objects in that row
        """
        return [
            cell for cell in self.grid_cells.values()
            if cell.row == row
        ]
    
    def get_cells_in_column(self, column: str) -> List[GridCell]:
        """
        Get all cells in a specific column.
        
        Args:
            column: Column label (A-F)
            
        Returns:
            List of GridCell objects in that column
        """
        return [
            cell for cell in self.grid_cells.values()
            if cell.column == column
        ]
    
    def get_border_cells(self) -> List[GridCell]:
        """
        Get all cells along the border line (row 3).
        
        Returns:
            List of GridCell objects on the border
        """
        return self.get_cells_in_row("3")
    
    def get_patrol_unit(self, patrol_id: str) -> Optional[PatrolUnit]:
        """
        Get patrol unit by ID.
        
        Args:
            patrol_id: Patrol unit identifier
            
        Returns:
            PatrolUnit object or None
        """
        return self.patrol_units.get(patrol_id)
    
    def get_active_patrols(self) -> List[PatrolUnit]:
        """
        Get all active patrol units.
        
        Returns:
            List of active PatrolUnit objects
        """
        return [
            patrol for patrol in self.patrol_units.values()
            if patrol.status == "active"
        ]
    
    def update_patrol_status(self, patrol_id: str, status: str) -> bool:
        """
        Update patrol unit status.
        
        Args:
            patrol_id: Patrol unit identifier
            status: New status (active/standby/dispatched)
            
        Returns:
            True if updated, False if patrol not found
        """
        patrol = self.patrol_units.get(patrol_id)
        if patrol:
            patrol.status = status
            logger.info(f"Patrol {patrol_id} status updated to {status}")
            return True
        return False
    
    def get_grid_overlay_data(self) -> Dict[str, Any]:
        """
        Get data for rendering grid overlay on video/map.
        
        Returns:
            Dict with grid lines and labels for rendering
        """
        return {
            "video_size": (self.video_width, self.video_height),
            "cell_size": (int(self.cell_width), int(self.cell_height)),
            "columns": self.columns,
            "rows": self.rows,
            "column_labels": self.column_labels,
            "row_labels": self.row_labels,
            "vertical_lines": [
                int(i * self.cell_width) 
                for i in range(1, self.columns)
            ],
            "horizontal_lines": [
                int(i * self.cell_height)
                for i in range(1, self.rows)
            ],
            "border_line_y": int(2.5 * self.cell_height),  # Middle of row 3
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get grid system statistics."""
        sensitivity_counts = {}
        for cell in self.grid_cells.values():
            s = cell.sensitivity
            sensitivity_counts[s] = sensitivity_counts.get(s, 0) + 1
        
        return {
            "total_cells": len(self.grid_cells),
            "columns": self.columns,
            "rows": self.rows,
            "video_size": (self.video_width, self.video_height),
            "cell_size": (int(self.cell_width), int(self.cell_height)),
            "sensitivity_distribution": sensitivity_counts,
            "patrol_units": len(self.patrol_units),
            "active_patrols": len(self.get_active_patrols()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def format_grid_reference(column: str, row: str) -> str:
    """
    Format column and row into standard grid reference.
    
    Args:
        column: Column letter (A-F)
        row: Row number (1-5)
        
    Returns:
        Formatted reference string (e.g., "C-3")
    """
    return f"{column.upper()}-{row}"


def parse_grid_reference(reference: str) -> Tuple[str, str]:
    """
    Parse grid reference into column and row.
    
    Args:
        reference: Grid reference string (e.g., "C-3")
        
    Returns:
        Tuple of (column, row)
        
    Raises:
        ValueError: If reference format is invalid
    """
    parts = reference.upper().split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid grid reference format: {reference}")
    return (parts[0], parts[1])


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Military Grid System Test")
    print("=" * 70)
    
    # Initialize grid system
    grid = MilitaryGridSystem()
    
    # Print grid statistics
    print("\nGrid Statistics:")
    stats = grid.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test pixel to grid conversion
    print("\nPixel to Grid Conversion Tests:")
    test_points = [
        (50, 50),     # Should be A-1
        (320, 240),   # Should be C-3
        (600, 450),   # Should be F-5
        (0, 0),       # Edge case
        (639, 479),   # Edge case
    ]
    
    for x, y in test_points:
        cell = grid.pixel_to_grid(x, y)
        print(f"  ({x}, {y}) → {cell.reference} "
              f"[{cell.sensitivity}, {cell.terrain}]")
    
    # Test grid to pixel conversion
    print("\nGrid to Pixel Conversion Tests:")
    test_refs = ["A-1", "C-3", "F-5"]
    
    for ref in test_refs:
        px, py = grid.grid_to_pixel(ref)
        print(f"  {ref} → ({px}, {py})")
    
    # Test nearest patrol lookup
    print("\nNearest Patrol Tests:")
    for ref in ["A-1", "C-3", "F-5"]:
        patrol, eta = grid.get_nearest_patrol(ref)
        if patrol:
            print(f"  {ref} → {patrol.name} ({patrol.type}), ETA: {eta} min")
        else:
            print(f"  {ref} → No patrol available")
    
    # Print all cells
    print("\nAll Grid Cells:")
    print("    A       B       C       D       E       F")
    for row in grid.row_labels:
        row_cells = grid.get_cells_in_row(row)
        row_str = f"{row} "
        for col in grid.column_labels:
            cell = grid.get_cell(f"{col}-{row}")
            if cell:
                # Show first letter of sensitivity
                s = cell.sensitivity[0].upper() if cell.sensitivity else "?"
                row_str += f"  [{s}]  "
            else:
                row_str += "  [?]  "
        print(row_str)
    
    print("\nLegend: [C]=Critical, [H]=High, [M]=Medium, [N]=Normal, [L]=Low")
    print("=" * 70)
