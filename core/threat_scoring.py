"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - THREAT SCORING ENGINE
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: core/threat_scoring.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    This module implements the point-based threat scoring algorithm.
    Each detection is evaluated based on multiple factors to determine
    threat level (CRITICAL, MEDIUM, LOW, or NO_THREAT).
    
SCORING METHODOLOGY:
    The system uses a cumulative point-based approach:
    
    1. OBJECT TYPE (+1 to +3 points)
       - Person: +1 (baseline threat)
       - Car/Motorcycle: +2 (vehicle threat)
       - Truck/Bus: +3 (heavy vehicle threat)
       
    2. TIME OF DAY (-1 to +3 points)
       - Daytime (06:00-17:59): -1 (normal activity)
       - Evening (18:00-21:59): +1 (increased risk)
       - Night (22:00-05:59): +3 (high risk)
       
    3. ZONE LOCATION (+0 to +5 points)
       - Row 1 (enemy territory): +5
       - Row 2 (approach zone): +3
       - Row 3 (border line): +2
       - Row 4 (our territory): +1
       - Row 5 (safe zone): +0
       
    4. GROUP SIZE (+0 to +5 points)
       - Single: +0
       - Pair (2): +2
       - Small group (3-5): +3
       - Large group (6+): +5
       
    5. CONFIDENCE ADJUSTMENT (-1 to +1 points)
       - High confidence (>=90%): +1
       - Medium confidence (75-89%): +0
       - Low confidence (<75%): -1
       
THREAT LEVELS:
    - CRITICAL: 11+ points (immediate response required)
    - MEDIUM: 6-10 points (alert supervisor)
    - LOW: 1-5 points (monitor)
    - NO_THREAT: 0 or below (log only)

SECURITY NOTE:
    This is the core threat assessment logic. Any modifications should be:
    1. Reviewed by security personnel
    2. Thoroughly tested
    3. Documented in audit log

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports
from config.settings import (
    THREAT_SCORING,
    THREAT_CLASS_POINTS,
    BORDER_CONFIG,
    CONFIG_DIR,
)

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ThreatFactor:
    """
    Represents a single factor in threat calculation.
    
    Used to provide detailed breakdown of how threat score was calculated.
    """
    name: str
    value: str
    points: int
    description: str


@dataclass
class ThreatAssessment:
    """
    Complete threat assessment for a detection.
    
    Attributes:
        total_score: Sum of all factor points
        threat_level: Category (CRITICAL, MEDIUM, LOW, NO_THREAT)
        factors: List of ThreatFactor explaining each component
        recommended_action: Suggested response
        color: Hex color for UI display
        
    Example:
        >>> assessment = ThreatAssessment(
        ...     total_score=13,
        ...     threat_level="CRITICAL",
        ...     factors=[...],
        ...     recommended_action="Immediate patrol dispatch",
        ...     color="#FF0000"
        ... )
    """
    total_score: int
    threat_level: str
    factors: List[ThreatFactor]
    recommended_action: str
    color: str
    priority: int = 0
    zone: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "total_score": self.total_score,
            "threat_level": self.threat_level,
            "factors": [
                {
                    "name": f.name,
                    "value": f.value,
                    "points": f.points,
                    "description": f.description
                }
                for f in self.factors
            ],
            "recommended_action": self.recommended_action,
            "color": self.color,
            "priority": self.priority,
            "zone": self.zone,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def get_explanation(self) -> str:
        """
        Generate human-readable explanation of threat assessment.
        
        Returns:
            Formatted string explaining the threat score
        """
        lines = [
            f"THREAT ASSESSMENT: {self.threat_level}",
            f"Total Score: {self.total_score} points",
            f"Zone: {self.zone}",
            "",
            "Factor Breakdown:",
        ]
        
        for factor in self.factors:
            sign = "+" if factor.points >= 0 else ""
            lines.append(
                f"  • {factor.name}: {factor.value} ({sign}{factor.points} pts)"
            )
            lines.append(f"    {factor.description}")
        
        lines.extend([
            "",
            f"Recommended Action: {self.recommended_action}",
        ])
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# THREAT SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ThreatScoringEngine:
    """
    Engine for calculating threat scores based on multiple factors.
    
    This class implements the point-based threat scoring algorithm
    used to assess detections and generate alerts.
    
    SECURITY NOTE:
        All scoring logic is documented and auditable. Changes to
        scoring weights should be reviewed by security personnel.
        
    Example:
        >>> engine = ThreatScoringEngine()
        >>> detection = {
        ...     'class_name': 'person',
        ...     'center_x': 520,
        ...     'center_y': 150,
        ...     'confidence': 0.94,
        ...     'timestamp': datetime(2026, 1, 2, 23, 42, 15)
        ... }
        >>> assessment = engine.calculate_threat(detection)
        >>> print(assessment.threat_level)
        'CRITICAL'
    """
    
    def __init__(self, zones_file: Optional[str] = None):
        """
        Initialize the threat scoring engine.
        
        Args:
            zones_file: Path to zones.json configuration file
                       Defaults to config/zones.json
        """
        # Load zone configuration
        self.zones_file = zones_file or str(CONFIG_DIR / "zones.json")
        self.zones_data = self._load_zones()
        
        # Statistics
        self.assessments_made = 0
        self.critical_count = 0
        self.medium_count = 0
        self.low_count = 0
        
        logger.info("ThreatScoringEngine initialized")
    
    def calculate_threat_score(
        self,
        object_type: str,
        zone_name: str = "A",
        confidence: float = 0.5,
        group_size: int = 1
    ) -> Dict[str, Any]:
        """
        Simplified threat score calculation for quick assessments.
        
        This is a convenience method for the UI that returns a simple dict.
        
        Args:
            object_type: Type of object detected (person, car, truck, etc.)
            zone_name: Grid zone name (A, B, C, etc.)
            confidence: Detection confidence (0.0 to 1.0)
            group_size: Number of objects detected
            
        Returns:
            Dict with threat_level, total_score, and color
        """
        # Base points for object type
        type_points = THREAT_CLASS_POINTS.get(object_type.lower(), 1)
        
        # Zone modifier (border zones are more critical)
        zone_modifiers = {
            "A": 2, "B": 1, "C": 3, "D": 2, "E": 1, "F": 2,
        }
        zone_points = zone_modifiers.get(zone_name.upper(), 1)
        
        # Time factor (night is more suspicious)
        hour = datetime.now().hour
        if 0 <= hour < 6:
            time_points = 3  # Night
        elif 6 <= hour < 18:
            time_points = 0  # Day
        else:
            time_points = 1  # Evening
        
        # Confidence factor
        if confidence >= 0.9:
            conf_points = 1
        elif confidence >= 0.7:
            conf_points = 0
        else:
            conf_points = -1
        
        # Group size factor
        group_points = min(group_size - 1, 4)  # Max +4 for groups
        
        # Calculate total
        total_score = type_points + zone_points + time_points + conf_points + group_points
        
        # Determine threat level
        if total_score >= 8:
            threat_level = "CRITICAL"
            color = "#ff3333"
        elif total_score >= 5:
            threat_level = "HIGH"
            color = "#ff8c00"
        elif total_score >= 2:
            threat_level = "MEDIUM"
            color = "#ffd700"
        else:
            threat_level = "LOW"
            color = "#4ade80"
        
        return {
            "threat_level": threat_level,
            "total_score": total_score,
            "color": color,
            "object_type": object_type,
            "zone": zone_name,
        }
    
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
    
    def calculate_threat(
        self,
        detection: Dict[str, Any],
        group_size: int = 1,
        movement_pattern: str = "stationary"
    ) -> ThreatAssessment:
        """
        Calculate comprehensive threat score for a detection.
        
        This is the main function that evaluates all threat factors
        and returns a complete assessment.
        
        Args:
            detection: Dictionary containing:
                - class_name: str (person/car/truck/etc.)
                - center_x: int (pixel X coordinate)
                - center_y: int (pixel Y coordinate)
                - confidence: float (0.0 to 1.0)
                - timestamp: datetime (when detection occurred)
            group_size: Number of detected objects in same area
            movement_pattern: Movement type (stationary/slow/fast/erratic)
            
        Returns:
            ThreatAssessment object with complete evaluation
            
        Example:
            >>> detection = {
            ...     'class_name': 'person',
            ...     'center_x': 320,
            ...     'center_y': 120,
            ...     'confidence': 0.92,
            ...     'timestamp': datetime.now()
            ... }
            >>> result = engine.calculate_threat(detection)
            >>> print(f"Score: {result.total_score}, Level: {result.threat_level}")
        """
        factors = []
        total_score = 0
        
        # Extract detection info
        class_name = detection.get('class_name', 'unknown')
        center_x = detection.get('center_x', 0)
        center_y = detection.get('center_y', 0)
        confidence = detection.get('confidence', 0.5)
        timestamp = detection.get('timestamp', datetime.now())
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 1: OBJECT TYPE
        # ─────────────────────────────────────────────────────────────
        type_points = THREAT_CLASS_POINTS.get(class_name, 0)
        
        type_descriptions = {
            "person": "Personnel detected - potential unauthorized entry",
            "car": "Light vehicle detected - potential smuggling",
            "motorcycle": "Motorcycle detected - fast infiltration capability",
            "bus": "Large vehicle detected - mass transport capability",
            "truck": "Heavy vehicle detected - significant smuggling risk",
        }
        
        factors.append(ThreatFactor(
            name="Object Type",
            value=class_name.upper(),
            points=type_points,
            description=type_descriptions.get(class_name, "Unknown object type")
        ))
        total_score += type_points
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 2: TIME OF DAY
        # ─────────────────────────────────────────────────────────────
        hour = timestamp.hour
        time_period, time_points = self._calculate_time_factor(hour)
        
        time_descriptions = {
            "day": "Daytime activity - normal operations period",
            "evening": "Evening hours - increased vigilance required",
            "night": "Nighttime activity - high suspicion period",
        }
        
        factors.append(ThreatFactor(
            name="Time of Day",
            value=f"{time_period.upper()} ({hour:02d}:00)",
            points=time_points,
            description=time_descriptions.get(time_period, "Unknown time period")
        ))
        total_score += time_points
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 3: ZONE LOCATION
        # ─────────────────────────────────────────────────────────────
        grid_ref = self._pixel_to_grid(center_x, center_y)
        zone_info = self._get_zone_info(grid_ref)
        zone_points = zone_info.get("points", 0)
        
        sensitivity = zone_info.get("sensitivity", "normal")
        terrain = zone_info.get("terrain", "unknown")
        
        zone_descriptions = {
            "critical": f"CRITICAL ZONE ({grid_ref}) - Enemy territory, highest threat",
            "high": f"HIGH SENSITIVITY ({grid_ref}) - Approach zone, elevated risk",
            "medium": f"BORDER ZONE ({grid_ref}) - Active border crossing area",
            "normal": f"PATROL ZONE ({grid_ref}) - Our territory, standard monitoring",
            "low": f"SAFE ZONE ({grid_ref}) - Internal area, minimal threat",
        }
        
        factors.append(ThreatFactor(
            name="Zone Location",
            value=f"Grid {grid_ref} ({sensitivity})",
            points=zone_points,
            description=zone_descriptions.get(
                sensitivity,
                f"Zone {grid_ref} - {terrain}"
            )
        ))
        total_score += zone_points
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 4: GROUP SIZE
        # ─────────────────────────────────────────────────────────────
        group_category, group_points = self._calculate_group_factor(group_size)
        
        group_descriptions = {
            "single": "Single individual detected",
            "pair": "Two individuals detected - possible coordinated activity",
            "small_group": "Small group (3-5) detected - organized operation suspected",
            "large_group": "Large group (6+) detected - significant threat",
        }
        
        factors.append(ThreatFactor(
            name="Group Size",
            value=f"{group_size} ({group_category})",
            points=group_points,
            description=group_descriptions.get(group_category, "Group detected")
        ))
        total_score += group_points
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 5: CONFIDENCE ADJUSTMENT
        # ─────────────────────────────────────────────────────────────
        conf_category, conf_points = self._calculate_confidence_factor(confidence)
        
        conf_descriptions = {
            "high": "High confidence detection - AI very certain",
            "medium": "Medium confidence detection - reasonable certainty",
            "low": "Low confidence detection - possible false positive",
        }
        
        factors.append(ThreatFactor(
            name="Detection Confidence",
            value=f"{confidence:.0%} ({conf_category})",
            points=conf_points,
            description=conf_descriptions.get(conf_category, "Detection confidence")
        ))
        total_score += conf_points
        
        # ─────────────────────────────────────────────────────────────
        # FACTOR 6: MOVEMENT PATTERN (optional)
        # ─────────────────────────────────────────────────────────────
        if movement_pattern != "stationary":
            movement_points = THREAT_SCORING["movement_points"].get(movement_pattern, 0)
            
            movement_descriptions = {
                "slow": "Slow movement detected - cautious approach",
                "fast": "Fast movement detected - attempting rapid crossing",
                "erratic": "Erratic movement - suspicious behavior pattern",
            }
            
            factors.append(ThreatFactor(
                name="Movement Pattern",
                value=movement_pattern.upper(),
                points=movement_points,
                description=movement_descriptions.get(
                    movement_pattern,
                    "Movement detected"
                )
            ))
            total_score += movement_points
        
        # ─────────────────────────────────────────────────────────────
        # CALCULATE FINAL THREAT LEVEL
        # ─────────────────────────────────────────────────────────────
        threat_level = self._determine_threat_level(total_score)
        recommended_action = self._get_recommended_action(threat_level, zone_info)
        color = self._get_threat_color(threat_level)
        priority = self._get_priority(threat_level)
        
        # Update statistics
        self.assessments_made += 1
        if threat_level == "CRITICAL":
            self.critical_count += 1
        elif threat_level == "MEDIUM":
            self.medium_count += 1
        elif threat_level == "LOW":
            self.low_count += 1
        
        return ThreatAssessment(
            total_score=total_score,
            threat_level=threat_level,
            factors=factors,
            recommended_action=recommended_action,
            color=color,
            priority=priority,
            zone=grid_ref,
            timestamp=timestamp
        )
    
    def _calculate_time_factor(self, hour: int) -> Tuple[str, int]:
        """
        Calculate time-of-day threat factor.
        
        Args:
            hour: Hour of day (0-23)
            
        Returns:
            Tuple of (time_period, points)
        """
        time_points = THREAT_SCORING["time_points"]
        
        if 6 <= hour < 18:
            return ("day", time_points["day"])
        elif 18 <= hour < 22:
            return ("evening", time_points["evening"])
        else:
            return ("night", time_points["night"])
    
    def _calculate_group_factor(self, group_size: int) -> Tuple[str, int]:
        """
        Calculate group size threat factor.
        
        Args:
            group_size: Number of detections in area
            
        Returns:
            Tuple of (group_category, points)
        """
        group_points = THREAT_SCORING["group_points"]
        
        if group_size <= 1:
            return ("single", group_points["single"])
        elif group_size == 2:
            return ("pair", group_points["pair"])
        elif group_size <= 5:
            return ("small_group", group_points["small_group"])
        else:
            return ("large_group", group_points["large_group"])
    
    def _calculate_confidence_factor(self, confidence: float) -> Tuple[str, int]:
        """
        Calculate confidence adjustment factor.
        
        Args:
            confidence: Detection confidence (0-1)
            
        Returns:
            Tuple of (confidence_category, points)
        """
        conf_adjustment = THREAT_SCORING["confidence_adjustment"]
        
        if confidence >= 0.90:
            return ("high", conf_adjustment["high"])
        elif confidence >= 0.75:
            return ("medium", conf_adjustment["medium"])
        else:
            return ("low", conf_adjustment["low"])
    
    def _pixel_to_grid(self, x: int, y: int) -> str:
        """
        Convert pixel coordinates to military grid reference.
        
        Args:
            x: X pixel coordinate
            y: Y pixel coordinate
            
        Returns:
            Grid reference string (e.g., "C-2")
        """
        video_width = BORDER_CONFIG["video_width"]
        video_height = BORDER_CONFIG["video_height"]
        cols = BORDER_CONFIG["grid_columns"]
        rows = BORDER_CONFIG["grid_rows"]
        col_labels = BORDER_CONFIG["column_labels"]
        row_labels = BORDER_CONFIG["row_labels"]
        
        # Calculate cell size
        cell_width = video_width / cols
        cell_height = video_height / rows
        
        # Determine column
        col_idx = min(int(x / cell_width), cols - 1)
        col_idx = max(0, col_idx)
        
        # Determine row
        row_idx = min(int(y / cell_height), rows - 1)
        row_idx = max(0, row_idx)
        
        return f"{col_labels[col_idx]}-{row_labels[row_idx]}"
    
    def _get_zone_info(self, grid_ref: str) -> Dict[str, Any]:
        """
        Get zone information for a grid reference.
        
        Args:
            grid_ref: Grid reference (e.g., "C-2")
            
        Returns:
            Dict with zone properties
        """
        zones = self.zones_data.get("zones", {})
        
        if grid_ref in zones:
            return zones[grid_ref]
        
        # Default zone info if not found
        return {
            "sensitivity": "normal",
            "points": 1,
            "terrain": "unknown",
            "nearest_patrol": "PATROL-B2",
            "patrol_eta_minutes": 10,
        }
    
    def _determine_threat_level(self, score: int) -> str:
        """
        Determine threat level from total score.
        
        Args:
            score: Total threat score
            
        Returns:
            Threat level string
        """
        if score >= THREAT_SCORING["critical_threshold"]:
            return "CRITICAL"
        elif score >= THREAT_SCORING["medium_threshold"]:
            return "MEDIUM"
        elif score >= THREAT_SCORING["low_threshold"]:
            return "LOW"
        else:
            return "NO_THREAT"
    
    def _get_recommended_action(
        self,
        threat_level: str,
        zone_info: Dict[str, Any]
    ) -> str:
        """
        Generate recommended action based on threat level.
        
        Args:
            threat_level: Threat level string
            zone_info: Zone information dictionary
            
        Returns:
            Recommended action string
        """
        nearest_patrol = zone_info.get("nearest_patrol", "nearest unit")
        eta = zone_info.get("patrol_eta_minutes", 10)
        
        actions = {
            "CRITICAL": f"IMMEDIATE DISPATCH: Alert {nearest_patrol}, ETA {eta} min. "
                       f"Notify command post. Maintain visual tracking.",
            "MEDIUM": f"PRIORITY ALERT: Notify supervisor. {nearest_patrol} on standby. "
                     f"Continue monitoring and tracking.",
            "LOW": f"MONITOR: Log incident. Track movement. Notify patrol if pattern changes.",
            "NO_THREAT": "LOG ONLY: Record detection for analysis. No immediate action required.",
        }
        
        return actions.get(threat_level, "Monitor and assess")
    
    def _get_threat_color(self, threat_level: str) -> str:
        """Get hex color for threat level."""
        colors = {
            "CRITICAL": "#FF0000",   # Red
            "MEDIUM": "#FFA500",     # Orange
            "LOW": "#FFFF00",        # Yellow
            "NO_THREAT": "#00FF00",  # Green
        }
        return colors.get(threat_level, "#FFFFFF")
    
    def _get_priority(self, threat_level: str) -> int:
        """Get numeric priority for sorting (lower = higher priority)."""
        priorities = {
            "CRITICAL": 1,
            "MEDIUM": 2,
            "LOW": 3,
            "NO_THREAT": 4,
        }
        return priorities.get(threat_level, 5)
    
    def batch_assess(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[ThreatAssessment]:
        """
        Assess multiple detections and sort by priority.
        
        Automatically calculates group size based on grid proximity.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            List of ThreatAssessments sorted by priority
        """
        # Group detections by grid zone
        zone_groups: Dict[str, List[Dict]] = {}
        
        for det in detections:
            grid_ref = self._pixel_to_grid(
                det.get('center_x', 0),
                det.get('center_y', 0)
            )
            if grid_ref not in zone_groups:
                zone_groups[grid_ref] = []
            zone_groups[grid_ref].append(det)
        
        # Assess each detection with group context
        assessments = []
        
        for grid_ref, group in zone_groups.items():
            group_size = len(group)
            
            for det in group:
                assessment = self.calculate_threat(
                    detection=det,
                    group_size=group_size
                )
                assessments.append(assessment)
        
        # Sort by priority (CRITICAL first)
        assessments.sort(key=lambda a: (a.priority, -a.total_score))
        
        return assessments
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scoring engine statistics."""
        return {
            "assessments_made": self.assessments_made,
            "critical_count": self.critical_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "no_threat_count": self.assessments_made - (
                self.critical_count + self.medium_count + self.low_count
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def quick_assess(
    class_name: str,
    x: int,
    y: int,
    confidence: float,
    timestamp: Optional[datetime] = None
) -> ThreatAssessment:
    """
    Quick threat assessment convenience function.
    
    Args:
        class_name: Object type (person/car/etc.)
        x: X pixel coordinate
        y: Y pixel coordinate  
        confidence: Detection confidence
        timestamp: Detection time (defaults to now)
        
    Returns:
        ThreatAssessment object
        
    Example:
        >>> assessment = quick_assess("person", 320, 120, 0.92)
        >>> print(assessment.threat_level)
    """
    engine = ThreatScoringEngine()
    detection = {
        'class_name': class_name,
        'center_x': x,
        'center_y': y,
        'confidence': confidence,
        'timestamp': timestamp or datetime.now()
    }
    return engine.calculate_threat(detection)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Threat Scoring Engine Test")
    print("=" * 70)
    
    # Initialize engine
    engine = ThreatScoringEngine()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Night person in enemy territory",
            "detection": {
                "class_name": "person",
                "center_x": 50,    # Column A
                "center_y": 50,    # Row 1 (enemy)
                "confidence": 0.95,
                "timestamp": datetime(2026, 1, 2, 23, 30, 0)  # Night
            },
            "expected_level": "CRITICAL"
        },
        {
            "name": "Day person in safe zone",
            "detection": {
                "class_name": "person",
                "center_x": 320,   # Column C
                "center_y": 450,   # Row 5 (safe)
                "confidence": 0.85,
                "timestamp": datetime(2026, 1, 2, 10, 0, 0)  # Day
            },
            "expected_level": "LOW"
        },
        {
            "name": "Evening truck at border",
            "detection": {
                "class_name": "truck",
                "center_x": 320,   # Column C
                "center_y": 288,   # Row 3 (border)
                "confidence": 0.88,
                "timestamp": datetime(2026, 1, 2, 19, 0, 0)  # Evening
            },
            "expected_level": "MEDIUM"
        },
        {
            "name": "Night vehicle group approaching",
            "detection": {
                "class_name": "car",
                "center_x": 200,   # Column B
                "center_y": 150,   # Row 2 (approach)
                "confidence": 0.92,
                "timestamp": datetime(2026, 1, 2, 2, 0, 0)  # Night
            },
            "group_size": 3,
            "expected_level": "CRITICAL"
        },
    ]
    
    print("\nRunning test scenarios...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print("-" * 50)
        
        assessment = engine.calculate_threat(
            detection=test["detection"],
            group_size=test.get("group_size", 1)
        )
        
        # Print results
        print(f"Expected: {test['expected_level']}")
        print(f"Got:      {assessment.threat_level} (Score: {assessment.total_score})")
        print(f"Match:    {'✓ PASS' if assessment.threat_level == test['expected_level'] else '✗ FAIL'}")
        print()
        print(assessment.get_explanation())
        print("\n" + "=" * 70 + "\n")
    
    # Print statistics
    print("Engine Statistics:")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
