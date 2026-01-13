"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              BORDER DRONE SURVEILLANCE - ENHANCED MVP v3.0                   ║
║                     Hackathon Demo - Precision Edition                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Enhanced MVP with precision improvements:
1. Non-Maximum Suppression (NMS) for duplicate removal
2. Object tracking across frames
3. Confidence filtering and validation
4. Movement analysis and speed estimation
5. Unique object counting (not just detection count)
6. Smooth detection with temporal filtering

Run with: streamlit run mvp_app.py
"""

import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import time
import hashlib

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    st.error("Please install ultralytics: pip install ultralytics")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Detection settings - Optimized for precision
CONFIDENCE_THRESHOLD = 0.30  # Slightly higher for fewer false positives
IOU_THRESHOLD = 0.45  # For NMS duplicate removal
MODEL_PATH = Path(__file__).parent / "models" / "yolov8n.pt"

# Tracking settings
TRACKING_IOU_THRESHOLD = 0.3  # For matching objects across frames
MAX_TRACK_AGE = 15  # Frames before a track is considered lost
MIN_TRACK_HITS = 2  # Minimum detections before confirming track

# Classes we care about (COCO dataset IDs)
THREAT_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car", 
    3: "motorcycle",
    5: "bus",
    7: "truck",
    14: "bird",  # Could be drone
    15: "cat",   # Wildlife
    16: "dog",   # Patrol dog / intruder with dog
    17: "horse", # Border crossing on horseback
}

# Detailed threat info
THREAT_INFO = {
    "person": {"points": 5, "icon": "👤", "desc": "Human detected - potential unauthorized crossing", "priority": 1},
    "bicycle": {"points": 3, "icon": "🚲", "desc": "Bicycle - possible smuggling vehicle", "priority": 3},
    "car": {"points": 6, "icon": "🚗", "desc": "Vehicle detected - check for authorization", "priority": 2},
    "motorcycle": {"points": 5, "icon": "🏍️", "desc": "Motorcycle - fast moving, high priority", "priority": 2},
    "bus": {"points": 7, "icon": "🚌", "desc": "Large vehicle - potential mass crossing", "priority": 1},
    "truck": {"points": 7, "icon": "🚛", "desc": "Truck - high capacity smuggling risk", "priority": 1},
    "bird": {"points": 1, "icon": "🦅", "desc": "Aerial object - verify not a drone", "priority": 4},
    "cat": {"points": 1, "icon": "🐱", "desc": "Wildlife - non-threat", "priority": 5},
    "dog": {"points": 2, "icon": "🐕", "desc": "Dog detected - may accompany person", "priority": 4},
    "horse": {"points": 4, "icon": "🐴", "desc": "Horse - possible mounted crossing", "priority": 2},
}

# Threat points for scoring (backward compatible)
THREAT_POINTS = {k: v["points"] for k, v in THREAT_INFO.items()}

# Colors for different threat levels (BGR for OpenCV)
COLORS = {
    "LOW": (0, 255, 0),      # Green
    "MEDIUM": (0, 255, 255), # Yellow
    "HIGH": (0, 165, 255),   # Orange
    "CRITICAL": (0, 0, 255), # Red
}

# Class-specific colors for better visualization
CLASS_COLORS = {
    "person": (0, 100, 255),    # Orange-red
    "car": (255, 150, 0),       # Blue
    "truck": (255, 100, 0),     # Dark blue
    "motorcycle": (0, 255, 255), # Yellow
    "bus": (255, 0, 100),       # Purple
    "bicycle": (100, 255, 100), # Light green
    "dog": (200, 150, 100),     # Light blue
    "cat": (150, 150, 150),     # Gray
    "bird": (255, 200, 100),    # Light blue
    "horse": (100, 100, 255),   # Red-ish
}

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Border Drone Surveillance",
    page_icon="🛸",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4ade80;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #0a0a0a 0%, #1a2e1a 50%, #0a0a0a 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #3d5a3d;
        box-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
    }
    .stat-box {
        background: linear-gradient(145deg, #1a1a1a 0%, #0a0a0a 100%);
        border: 1px solid #3d5a3d;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stat-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4ade80;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
    }
    .stat-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .detection-item {
        background: linear-gradient(90deg, #1a1a1a 0%, #0f0f0f 100%);
        border-left: 4px solid #4ade80;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        transition: background 0.2s;
    }
    .detection-item:hover {
        background: linear-gradient(90deg, #252525 0%, #1a1a1a 100%);
    }
    .threat-critical { border-left-color: #ef4444 !important; }
    .threat-high { border-left-color: #f97316 !important; }
    .threat-medium { border-left-color: #eab308 !important; }
    .threat-low { border-left-color: #22c55e !important; }
    
    .alert-banner {
        background: linear-gradient(90deg, #7f1d1d 0%, #450a0a 100%);
        border: 1px solid #dc2626;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .timeline-event {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        border-bottom: 1px solid #333;
    }
    .timeline-time {
        color: #4ade80;
        font-family: monospace;
        min-width: 80px;
    }
    
    .analytics-card {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #333;
    }
    
    .progress-ring {
        stroke: #4ade80;
        stroke-linecap: round;
        animation: progress 1s ease-out forwards;
    }
    
    .zone-marker {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .zone-restricted { background: #7f1d1d; color: #fca5a5; }
    .zone-surveillance { background: #78350f; color: #fcd34d; }
    .zone-patrol { background: #14532d; color: #86efac; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IMPROVED DETECTION & TRACKING CLASSES
# =============================================================================

class ObjectTracker:
    """
    Simple IoU-based object tracker to track objects across frames.
    Helps eliminate duplicates and provides unique object IDs.
    """
    
    def __init__(self, iou_threshold=0.3, max_age=15, min_hits=2):
        self.iou_threshold = iou_threshold
        self.max_age = max_age  # Frames before track is lost
        self.min_hits = min_hits  # Minimum hits to confirm track
        self.tracks = {}  # track_id -> track_info
        self.next_id = 1
        self.frame_count = 0
    
    def _compute_iou(self, box1, box2):
        """Compute Intersection over Union between two boxes."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def update(self, detections):
        """
        Update tracks with new detections.
        Returns detections with assigned track IDs.
        """
        self.frame_count += 1
        
        # If no tracks, create new ones for all detections
        if not self.tracks:
            for det in detections:
                det['track_id'] = self.next_id
                det['track_age'] = 1
                det['track_hits'] = 1
                det['is_confirmed'] = False
                det['velocity'] = (0, 0)
                self.tracks[self.next_id] = {
                    'bbox': det['bbox'],
                    'center': det['center'],
                    'class_name': det['class_name'],
                    'last_seen': self.frame_count,
                    'hits': 1,
                    'history': [det['center']],
                }
                self.next_id += 1
            return detections
        
        # Match detections to existing tracks using IoU
        matched_tracks = set()
        matched_detections = set()
        
        # Sort detections by confidence (highest first)
        sorted_dets = sorted(enumerate(detections), key=lambda x: -x[1]['confidence'])
        
        for det_idx, det in sorted_dets:
            best_iou = 0
            best_track_id = None
            
            for track_id, track in self.tracks.items():
                if track_id in matched_tracks:
                    continue
                # Only match same class
                if track['class_name'] != det['class_name']:
                    continue
                    
                iou = self._compute_iou(det['bbox'], track['bbox'])
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                matched_tracks.add(best_track_id)
                matched_detections.add(det_idx)
                
                track = self.tracks[best_track_id]
                old_center = track['center']
                new_center = det['center']
                
                # Calculate velocity
                velocity = (new_center[0] - old_center[0], new_center[1] - old_center[1])
                
                track['bbox'] = det['bbox']
                track['center'] = new_center
                track['last_seen'] = self.frame_count
                track['hits'] += 1
                track['history'].append(new_center)
                if len(track['history']) > 30:
                    track['history'] = track['history'][-30:]
                
                det['track_id'] = best_track_id
                det['track_age'] = self.frame_count - (track['last_seen'] - track['hits'])
                det['track_hits'] = track['hits']
                det['is_confirmed'] = track['hits'] >= self.min_hits
                det['velocity'] = velocity
                det['track_history'] = track['history'].copy()
        
        # Create new tracks for unmatched detections
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_detections:
                det['track_id'] = self.next_id
                det['track_age'] = 1
                det['track_hits'] = 1
                det['is_confirmed'] = False
                det['velocity'] = (0, 0)
                self.tracks[self.next_id] = {
                    'bbox': det['bbox'],
                    'center': det['center'],
                    'class_name': det['class_name'],
                    'last_seen': self.frame_count,
                    'hits': 1,
                    'history': [det['center']],
                }
                self.next_id += 1
        
        # Remove old tracks
        tracks_to_remove = []
        for track_id, track in self.tracks.items():
            if self.frame_count - track['last_seen'] > self.max_age:
                tracks_to_remove.append(track_id)
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
        
        return detections
    
    def get_unique_count(self):
        """Get count of unique confirmed objects."""
        return len([t for t in self.tracks.values() if t['hits'] >= self.min_hits])
    
    def get_all_unique_ids(self):
        """Get all unique track IDs that were confirmed."""
        return [tid for tid, t in self.tracks.items() if t['hits'] >= self.min_hits]


def apply_nms(detections, iou_threshold=0.45):
    """
    Apply Non-Maximum Suppression to remove overlapping detections.
    This prevents counting the same object multiple times.
    """
    if len(detections) == 0:
        return []
    
    # Group by class
    class_groups = defaultdict(list)
    for det in detections:
        class_groups[det['class_name']].append(det)
    
    result = []
    
    for class_name, class_dets in class_groups.items():
        if len(class_dets) == 1:
            result.extend(class_dets)
            continue
        
        # Sort by confidence (descending)
        class_dets = sorted(class_dets, key=lambda x: -x['confidence'])
        
        # Apply NMS
        boxes = np.array([d['bbox'] for d in class_dets])
        scores = np.array([d['confidence'] for d in class_dets])
        
        # Custom NMS implementation
        keep = []
        indices = list(range(len(class_dets)))
        
        while indices:
            # Take highest confidence
            best_idx = indices[0]
            keep.append(best_idx)
            indices = indices[1:]
            
            if not indices:
                break
            
            # Remove overlapping boxes
            best_box = boxes[best_idx]
            new_indices = []
            
            for idx in indices:
                # Compute IoU
                box = boxes[idx]
                x1 = max(best_box[0], box[0])
                y1 = max(best_box[1], box[1])
                x2 = min(best_box[2], box[2])
                y2 = min(best_box[3], box[3])
                
                intersection = max(0, x2 - x1) * max(0, y2 - y1)
                area1 = (best_box[2] - best_box[0]) * (best_box[3] - best_box[1])
                area2 = (box[2] - box[0]) * (box[3] - box[1])
                union = area1 + area2 - intersection
                iou = intersection / union if union > 0 else 0
                
                if iou < iou_threshold:
                    new_indices.append(idx)
            
            indices = new_indices
        
        result.extend([class_dets[i] for i in keep])
    
    return result


def validate_detection(det, frame_shape):
    """
    Validate a detection to filter out false positives.
    Returns True if detection is likely valid.
    """
    x1, y1, x2, y2 = det['bbox']
    h, w = frame_shape[:2]
    
    # Check box is within frame
    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        return False
    
    # Check box has reasonable size
    box_w = x2 - x1
    box_h = y2 - y1
    
    # Too small (likely noise)
    if box_w < 15 or box_h < 15:
        return False
    
    # Too large (likely false positive covering whole frame)
    if box_w > w * 0.9 or box_h > h * 0.9:
        return False
    
    # Check aspect ratio for specific classes
    aspect_ratio = box_w / box_h if box_h > 0 else 0
    
    if det['class_name'] == 'person':
        # Person should be taller than wide (0.2 to 1.5 aspect ratio)
        if aspect_ratio > 2.5 or aspect_ratio < 0.15:
            return False
    
    if det['class_name'] in ['car', 'truck', 'bus']:
        # Vehicles usually wider than tall
        if aspect_ratio < 0.3:
            return False
    
    return True


@st.cache_resource
def load_model():
    """Load YOLOv8 model (cached) with optimized settings."""
    if not YOLO_AVAILABLE:
        return None
    
    if not MODEL_PATH.exists():
        st.error(f"Model not found at {MODEL_PATH}")
        return None
    
    try:
        model = YOLO(str(MODEL_PATH))
        # Warm up model
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = model(dummy, verbose=False)
        return model
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        return None


def detect_objects(model, frame, conf_threshold=0.30, iou_threshold=0.45, 
                   frame_idx=0, fps=30, apply_validation=True):
    """
    Run YOLOv8 detection with improved precision.
    
    Features:
    - Built-in NMS from YOLO
    - Additional custom NMS
    - Detection validation
    - Proper confidence filtering
    """
    if model is None:
        return []
    
    detections = []
    
    try:
        # Run inference with built-in NMS
        results = model(
            frame, 
            conf=conf_threshold, 
            iou=iou_threshold,  # Built-in NMS threshold
            verbose=False,
            classes=list(THREAT_CLASSES.keys()),  # Only detect our classes
            max_det=50,  # Limit max detections
        )
        
        for result in results:
            boxes = result.boxes
            
            if boxes is None or len(boxes) == 0:
                continue
                
            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Skip if not in our threat classes
                if class_id not in THREAT_CLASSES:
                    continue
                
                class_name = THREAT_CLASSES[class_id]
                x1, y1, x2, y2 = [int(x) for x in box.xyxy[0].tolist()]
                
                # Calculate center point
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                # Calculate bounding box dimensions
                box_w = x2 - x1
                box_h = y2 - y1
                area = box_w * box_h
                frame_area = frame.shape[0] * frame.shape[1]
                relative_size = (area / frame_area) * 100
                
                # Create detection object
                det = {
                    "id": f"DET-{frame_idx:05d}-{i:02d}",
                    "class_name": class_name,
                    "class_id": class_id,
                    "confidence": confidence,
                    "bbox": (x1, y1, x2, y2),
                    "center": (cx, cy),
                    "box_width": box_w,
                    "box_height": box_h,
                    "relative_size": relative_size,
                    "frame": frame_idx,
                }
                
                # Validate detection
                if apply_validation and not validate_detection(det, frame.shape):
                    continue
                
                # Calculate threat score with improved factors
                base_points = THREAT_POINTS.get(class_name, 1)
                
                # Confidence factor (higher confidence = more certain)
                conf_factor = 0.5 + (confidence * 0.5)  # Range: 0.5 - 1.0
                
                # Size factor - larger objects are closer/more threatening
                size_factor = min(1.5, 0.8 + (relative_size / 5))  # Range: 0.8 - 1.5
                
                # Position factor - center of frame is more critical
                frame_h, frame_w = frame.shape[:2]
                dist_from_center = np.sqrt((cx - frame_w/2)**2 + (cy - frame_h/2)**2)
                max_dist = np.sqrt((frame_w/2)**2 + (frame_h/2)**2)
                position_factor = 1.0 + (1.0 - dist_from_center / max_dist) * 0.3
                
                threat_score = int(base_points * conf_factor * size_factor * position_factor * 10)
                
                # Determine threat level
                if threat_score >= 35:
                    threat_level = "CRITICAL"
                elif threat_score >= 25:
                    threat_level = "HIGH"
                elif threat_score >= 15:
                    threat_level = "MEDIUM"
                else:
                    threat_level = "LOW"
                
                # Calculate grid reference
                grid_col = min(int(cx / (frame.shape[1] / 6)), 5)
                grid_row = min(int(cy / (frame.shape[0] / 5)), 4)
                grid_ref = f"{chr(65 + grid_col)}-{grid_row + 1}"
                
                # Calculate timestamp
                timestamp_sec = frame_idx / fps if fps > 0 else 0
                timestamp = str(timedelta(seconds=int(timestamp_sec)))
                
                # Get threat info
                info = THREAT_INFO.get(class_name, {"icon": "❓", "desc": "Unknown object", "priority": 5})
                
                det.update({
                    "threat_score": threat_score,
                    "threat_level": threat_level,
                    "grid_ref": grid_ref,
                    "timestamp": timestamp,
                    "icon": info["icon"],
                    "description": info["desc"],
                    "priority": info["priority"],
                })
                
                detections.append(det)
        
        # Apply additional NMS for any remaining duplicates
        detections = apply_nms(detections, iou_threshold)
        
        # Sort by priority (most important first)
        detections.sort(key=lambda x: (x.get('priority', 5), -x['confidence']))
    
    except Exception as e:
        st.error(f"Detection error: {e}")
    
    return detections


def draw_detections(frame, detections, show_details=True, show_tracks=False):
    """Draw bounding boxes and labels on frame with enhanced visuals."""
    output = frame.copy()
    
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cx, cy = det["center"]
        
        # Use class-specific color or threat level color
        class_color = CLASS_COLORS.get(det["class_name"], (0, 255, 0))
        threat_color = COLORS.get(det["threat_level"], (0, 255, 0))
        
        # Draw tracking trail if available
        if show_tracks and 'track_history' in det and len(det['track_history']) > 1:
            history = det['track_history']
            for i in range(1, len(history)):
                alpha = i / len(history)  # Fade older points
                pt1 = tuple(map(int, history[i-1]))
                pt2 = tuple(map(int, history[i]))
                cv2.line(output, pt1, pt2, class_color, max(1, int(alpha * 3)))
        
        # Draw glow effect for high threats
        if det["threat_level"] in ["HIGH", "CRITICAL"]:
            cv2.rectangle(output, (x1-3, y1-3), (x2+3, y2+3), threat_color, 1)
        
        # Draw main box
        cv2.rectangle(output, (x1, y1), (x2, y2), class_color, 2)
        
        # Draw corner accents with threat color
        corner_len = min(20, (x2-x1)//4, (y2-y1)//4)
        # Top-left
        cv2.line(output, (x1, y1), (x1 + corner_len, y1), threat_color, 3)
        cv2.line(output, (x1, y1), (x1, y1 + corner_len), threat_color, 3)
        # Top-right
        cv2.line(output, (x2, y1), (x2 - corner_len, y1), threat_color, 3)
        cv2.line(output, (x2, y1), (x2, y1 + corner_len), threat_color, 3)
        # Bottom-left
        cv2.line(output, (x1, y2), (x1 + corner_len, y2), threat_color, 3)
        cv2.line(output, (x1, y2), (x1, y2 - corner_len), threat_color, 3)
        # Bottom-right
        cv2.line(output, (x2, y2), (x2 - corner_len, y2), threat_color, 3)
        cv2.line(output, (x2, y2), (x2, y2 - corner_len), threat_color, 3)
        
        # Draw center crosshair
        cv2.line(output, (cx - 5, cy), (cx + 5, cy), class_color, 1)
        cv2.line(output, (cx, cy - 5), (cx, cy + 5), class_color, 1)
        
        if show_details:
            # Build label with track ID if available
            track_info = f" #{det.get('track_id', '?')}" if 'track_id' in det else ""
            confirmed = "✓" if det.get('is_confirmed', False) else ""
            label = f"{det['class_name'].upper()}{track_info}{confirmed} {det['confidence']:.0%}"
            
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(output, (x1, y1 - 50), (x1 + max(w + 10, 120), y1), class_color, -1)
            
            # Draw main label
            cv2.putText(output, label, (x1 + 5, y1 - 32), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
            
            # Draw grid reference and size
            info_label = f"Grid:{det['grid_ref']} Size:{det.get('relative_size', 0):.1f}%"
            cv2.putText(output, info_label, (x1 + 5, y1 - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
            
            # Draw threat level below box
            threat_label = f"[{det['threat_level']}] {det['threat_score']}pts"
            cv2.putText(output, threat_label, (x1 + 5, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, threat_color, 2)
            
            # Draw velocity indicator if available
            if 'velocity' in det and det['velocity'] != (0, 0):
                vx, vy = det['velocity']
                speed = np.sqrt(vx*vx + vy*vy)
                if speed > 2:  # Only show if moving
                    end_x = int(cx + vx * 3)
                    end_y = int(cy + vy * 3)
                    cv2.arrowedLine(output, (cx, cy), (end_x, end_y), (255, 255, 0), 2)
    
    return output


def draw_grid(frame, cols=6, rows=5, highlight_cells=None):
    """Draw military-style grid overlay with optional cell highlighting."""
    h, w = frame.shape[:2]
    cell_w, cell_h = w // cols, h // rows
    
    # Grid color (dark green)
    color = (61, 90, 61)
    
    # Highlight cells with detections
    if highlight_cells:
        for cell in highlight_cells:
            col = ord(cell[0]) - ord('A')
            row = int(cell.split('-')[1]) - 1
            x1 = col * cell_w
            y1 = row * cell_h
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x1 + cell_w, y1 + cell_h), 
                         (0, 255, 255), -1)
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
    
    # Vertical lines
    for i in range(1, cols):
        cv2.line(frame, (i * cell_w, 0), (i * cell_w, h), color, 1)
    
    # Horizontal lines  
    for i in range(1, rows):
        cv2.line(frame, (0, i * cell_h), (w, i * cell_h), color, 1)
    
    # Grid labels
    labels = "ABCDEF"
    for col in range(cols):
        for row in range(rows):
            ref = f"{labels[col]}-{row+1}"
            x = col * cell_w + 5
            y = (row + 1) * cell_h - 5
            cv2.putText(frame, ref, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.35, (74, 222, 128), 1)
    
    return frame


def create_heatmap(frame, detections_history, decay=0.95):
    """Create a heatmap overlay showing detection hotspots."""
    h, w = frame.shape[:2]
    heatmap = np.zeros((h, w), dtype=np.float32)
    
    for det in detections_history:
        cx, cy = det.get("center", (w//2, h//2))
        # Add gaussian blob at detection location
        for dy in range(-30, 31):
            for dx in range(-30, 31):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < 30:
                        heatmap[ny, nx] += np.exp(-dist/15) * det.get("threat_score", 1)
    
    # Normalize and colorize
    if heatmap.max() > 0:
        heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # Blend with original frame
        output = cv2.addWeighted(frame, 0.7, heatmap_colored, 0.3, 0)
        return output
    
    return frame


def draw_timestamp_overlay(frame, frame_idx, fps, total_frames):
    """Draw timestamp and progress overlay."""
    h, w = frame.shape[:2]
    
    # Semi-transparent overlay at top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 40), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Timestamp
    timestamp_sec = frame_idx / fps if fps > 0 else 0
    timestamp_str = str(timedelta(seconds=int(timestamp_sec)))
    cv2.putText(frame, f"TIME: {timestamp_str}", (10, 28), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (74, 222, 128), 2)
    
    # Frame counter
    cv2.putText(frame, f"FRAME: {frame_idx}/{total_frames}", (w - 200, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (74, 222, 128), 2)
    
    # Progress bar
    progress = frame_idx / max(total_frames, 1)
    bar_width = w - 20
    cv2.rectangle(frame, (10, h - 15), (10 + bar_width, h - 5), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, h - 15), (10 + int(bar_width * progress), h - 5), 
                  (74, 222, 128), -1)
    
    return frame


# =============================================================================
# ANALYTICS HELPERS
# =============================================================================

def generate_analytics(all_detections, tracker=None):
    """Generate detailed analytics from detection data with unique object counting."""
    if not all_detections:
        return {}
    
    analytics = {
        "total_detections": len(all_detections),
        "unique_objects": 0,  # Will be filled by tracker
        "unique_frames": len(set(d["frame"] for d in all_detections)),
        "by_class": defaultdict(int),
        "by_class_unique": defaultdict(set),  # Track unique IDs per class
        "by_threat_level": defaultdict(int),
        "by_grid": defaultdict(int),
        "avg_confidence": 0,
        "max_threat_score": 0,
        "min_confidence": 1.0,
        "max_confidence": 0.0,
        "timeline": [],
        "hotspots": [],
        "confirmed_tracks": 0,
    }
    
    total_conf = 0
    unique_track_ids = set()
    confirmed_tracks = set()
    
    for det in all_detections:
        analytics["by_class"][det["class_name"]] += 1
        analytics["by_threat_level"][det["threat_level"]] += 1
        analytics["by_grid"][det["grid_ref"]] += 1
        total_conf += det["confidence"]
        
        # Track unique objects
        if "track_id" in det:
            unique_track_ids.add(det["track_id"])
            analytics["by_class_unique"][det["class_name"]].add(det["track_id"])
            if det.get("is_confirmed", False):
                confirmed_tracks.add(det["track_id"])
        
        if det["threat_score"] > analytics["max_threat_score"]:
            analytics["max_threat_score"] = det["threat_score"]
        if det["confidence"] < analytics["min_confidence"]:
            analytics["min_confidence"] = det["confidence"]
        if det["confidence"] > analytics["max_confidence"]:
            analytics["max_confidence"] = det["confidence"]
    
    analytics["avg_confidence"] = total_conf / len(all_detections) if all_detections else 0
    analytics["unique_objects"] = len(unique_track_ids) if unique_track_ids else len(all_detections)
    analytics["confirmed_tracks"] = len(confirmed_tracks)
    
    # Convert sets to counts for unique per class
    analytics["unique_by_class"] = {k: len(v) for k, v in analytics["by_class_unique"].items()}
    
    # Find hotspots (most active grid cells)
    sorted_grids = sorted(analytics["by_grid"].items(), key=lambda x: -x[1])
    analytics["hotspots"] = sorted_grids[:5]
    
    # Create timeline (group by timestamp)
    timeline_dict = defaultdict(list)
    for det in all_detections:
        timeline_dict[det["timestamp"]].append(det)
    analytics["timeline"] = dict(timeline_dict)
    
    # Calculate detection quality metrics
    if analytics["total_detections"] > 0:
        analytics["detection_density"] = analytics["total_detections"] / max(analytics["unique_frames"], 1)
        analytics["uniqueness_ratio"] = analytics["unique_objects"] / analytics["total_detections"]
    else:
        analytics["detection_density"] = 0
        analytics["uniqueness_ratio"] = 0
    
    return analytics


def render_analytics_dashboard(analytics, all_detections):
    """Render the analytics dashboard with unique object counts."""
    st.markdown("## 📊 Precision Analytics Dashboard")
    
    # Top metrics row - now includes unique objects
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{analytics['total_detections']}</div>
            <div class="stat-label">Total Detections</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color: #60a5fa;">{analytics.get('unique_objects', '?')}</div>
            <div class="stat-label">🎯 Unique Objects</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_persons = analytics.get("unique_by_class", {}).get("person", analytics["by_class"].get("person", 0))
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{unique_persons}</div>
            <div class="stat-label">👤 Unique Persons</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        unique_vehicles = sum(analytics.get("unique_by_class", {}).get(v, 0) for v in ["car", "truck", "bus", "motorcycle"])
        if unique_vehicles == 0:
            unique_vehicles = sum(analytics["by_class"].get(v, 0) for v in ["car", "truck", "bus", "motorcycle"])
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{unique_vehicles}</div>
            <div class="stat-label">🚗 Unique Vehicles</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        critical = analytics["by_threat_level"].get("CRITICAL", 0)
        high = analytics["by_threat_level"].get("HIGH", 0)
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color: #ef4444;">{critical + high}</div>
            <div class="stat-label">⚠️ High/Critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{analytics['avg_confidence']:.0%}</div>
            <div class="stat-label">Avg Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two-column layout for detailed breakdown
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 🎯 Detection Breakdown by Type")
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        
        for cls, count in sorted(analytics["by_class"].items(), key=lambda x: -x[1]):
            info = THREAT_INFO.get(cls, {"icon": "❓"})
            percentage = (count / analytics["total_detections"]) * 100
            st.markdown(f"""
            **{info['icon']} {cls.upper()}**: {count} ({percentage:.1f}%)
            """)
            st.progress(percentage / 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 🗺️ Hotspot Grid Cells")
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        
        for grid_ref, count in analytics["hotspots"]:
            st.markdown(f"""
            <span class="zone-marker zone-surveillance">{grid_ref}</span> 
            **{count}** detections
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown("### ⚠️ Threat Level Distribution")
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        
        threat_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        threat_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        threat_colors = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        
        for level in threat_order:
            count = analytics["by_threat_level"].get(level, 0)
            percentage = (count / analytics["total_detections"]) * 100 if analytics["total_detections"] > 0 else 0
            st.markdown(f"""
            {threat_icons[level]} **{level}**: {count} ({percentage:.1f}%)
            """)
            st.progress(percentage / 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 📈 Key Statistics")
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown(f"""
        - **Max Threat Score**: {analytics['max_threat_score']} pts
        - **Unique Frames with Detections**: {analytics['unique_frames']}
        - **Active Grid Cells**: {len(analytics['by_grid'])}
        - **Detection Density**: {analytics['total_detections'] / max(analytics['unique_frames'], 1):.1f} per frame
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Detection Timeline
    st.markdown("---")
    st.markdown("### 📅 Detection Timeline")
    
    # Show first 10 detections sorted by frame
    sorted_detections = sorted(all_detections, key=lambda x: x["frame"])[:20]
    
    for det in sorted_detections:
        level_class = f"threat-{det['threat_level'].lower()}"
        st.markdown(f"""
        <div class="detection-item {level_class}">
            <div class="timeline-event">
                <span class="timeline-time">{det['timestamp']}</span>
                {det['icon']} <b>{det['class_name'].upper()}</b> 
                at <b>{det['grid_ref']}</b> | 
                Confidence: {det['confidence']:.0%} | 
                Threat: {det['threat_level']} ({det['threat_score']} pts)
            </div>
            <small style="color: #666;">📝 {det['description']}</small>
        </div>
        """, unsafe_allow_html=True)


def generate_report(analytics, all_detections, video_info):
    """Generate a downloadable JSON report with unique object info."""
    report = {
        "report_generated": datetime.now().isoformat(),
        "video_info": video_info,
        "summary": {
            "total_detections": analytics["total_detections"],
            "unique_objects": analytics.get("unique_objects", "N/A"),
            "confirmed_tracks": analytics.get("confirmed_tracks", "N/A"),
            "by_class": dict(analytics["by_class"]),
            "unique_by_class": analytics.get("unique_by_class", {}),
            "by_threat_level": dict(analytics["by_threat_level"]),
            "hotspots": analytics["hotspots"],
            "avg_confidence": analytics["avg_confidence"],
            "max_threat_score": analytics["max_threat_score"],
            "detection_quality": {
                "uniqueness_ratio": analytics.get("uniqueness_ratio", 0),
                "detection_density": analytics.get("detection_density", 0),
            }
        },
        "detections": all_detections,
    }
    return json.dumps(report, indent=2, default=str)


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        🛸 BORDER DRONE SURVEILLANCE<br>
        <small style="font-size: 0.4em; color: #888;">Precision Intelligence System v3.0</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Load model
    model = load_model()
    
    if model is None:
        st.error("❌ Detection model not available. Please check installation.")
        st.stop()
    
    # Model info in sidebar
    st.sidebar.markdown("### 🤖 Model Status")
    st.sidebar.success("✅ YOLOv8n Loaded")
    st.sidebar.markdown(f"**Path**: `{MODEL_PATH.name}`")
    st.sidebar.markdown(f"**Classes**: {len(THREAT_CLASSES)} threat types")
    
    st.sidebar.markdown("---")
    
    # Sidebar settings - Enhanced precision controls
    st.sidebar.markdown("### ⚙️ Detection Settings")
    conf_threshold = st.sidebar.slider(
        "Confidence Threshold", 
        0.15, 0.90, 0.30,
        help="Higher = more precise, fewer false positives"
    )
    
    iou_threshold = st.sidebar.slider(
        "NMS IoU Threshold", 
        0.20, 0.80, 0.45,
        help="Lower = more aggressive duplicate removal"
    )
    
    st.sidebar.markdown("### 🎯 Tracking Settings")
    enable_tracking = st.sidebar.checkbox("Enable Object Tracking", value=True,
                                          help="Track objects across frames for unique counting")
    min_track_hits = st.sidebar.slider(
        "Min Track Confirmations", 
        1, 5, 2,
        help="Detections needed to confirm an object"
    ) if enable_tracking else 2
    
    st.sidebar.markdown("### 🎨 Display Options")
    show_grid = st.sidebar.checkbox("Show Grid Overlay", value=True)
    show_details = st.sidebar.checkbox("Show Detection Details", value=True)
    show_tracks = st.sidebar.checkbox("Show Movement Trails", value=True) if enable_tracking else False
    show_heatmap = st.sidebar.checkbox("Show Heatmap Mode", value=False)
    
    st.sidebar.markdown("### 🎬 Processing")
    frame_skip = st.sidebar.slider("Frame Skip", 1, 30, 3, 
                                   help="Process every Nth frame (lower = more precise)")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📹 Live Analysis", "📊 Batch Processing", "ℹ️ About"])
    
    # ==========================================================================
    # TAB 1: Live Analysis (single frame)
    # ==========================================================================
    with tab1:
        st.markdown("### 🔍 Frame-by-Frame Analysis")
        st.markdown("Upload drone footage to analyze individual frames in detail.")
        
        uploaded_file = st.file_uploader(
            "Select drone footage",
            type=["mp4", "avi", "mov", "mkv"],
            key="live_upload"
        )
        
        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(uploaded_file.read())
                video_path = tmp.name
            
            try:
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                duration = total_frames / fps if fps > 0 else 0
                
                # Video info panel
                st.markdown(f"""
                <div class="analytics-card">
                    📹 <b>Video Info</b>: {total_frames} frames | {fps:.1f} FPS | 
                    {width}x{height} | Duration: {timedelta(seconds=int(duration))}
                </div>
                """, unsafe_allow_html=True)
                
                # Frame selector
                frame_num = st.slider("Select Frame", 0, max(0, total_frames-1), 0)
                
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    # Run detection with improved precision
                    with st.spinner("🔍 Analyzing frame with precision detection..."):
                        detections = detect_objects(
                            model, frame, 
                            conf_threshold=conf_threshold,
                            iou_threshold=iou_threshold,
                            frame_idx=frame_num, 
                            fps=fps,
                            apply_validation=True
                        )
                    
                    # Alert banner for high threats
                    critical_count = len([d for d in detections if d["threat_level"] in ["CRITICAL", "HIGH"]])
                    if critical_count > 0:
                        st.markdown(f"""
                        <div class="alert-banner">
                            🚨 <b>ALERT</b>: {critical_count} HIGH/CRITICAL threat(s) detected!
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Draw results
                    output_frame = frame.copy()
                    
                    # Get active grid cells for highlighting
                    active_cells = list(set(d["grid_ref"] for d in detections))
                    
                    if show_heatmap and detections:
                        output_frame = create_heatmap(output_frame, detections)
                    
                    output_frame = draw_detections(output_frame, detections, show_details, show_tracks)
                    
                    if show_grid:
                        output_frame = draw_grid(output_frame, highlight_cells=active_cells)
                    
                    output_frame = draw_timestamp_overlay(output_frame, frame_num, fps, total_frames)
                    
                    # Display layout
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Convert BGR to RGB for display
                        output_rgb = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
                        st.image(output_rgb, caption=f"Frame {frame_num} Analysis", 
                                use_container_width=True)
                    
                    with col2:
                        st.markdown("### 📊 Frame Analysis")
                        
                        # Quick stats
                        st.markdown(f"""
                        <div class="stat-box">
                            <div class="stat-number">{len(detections)}</div>
                            <div class="stat-label">Objects Detected</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Detection list with details
                        if detections:
                            st.markdown("---")
                            st.markdown("**Detected Objects:**")
                            
                            for det in detections:
                                level_class = f"threat-{det['threat_level'].lower()}"
                                st.markdown(f"""
                                <div class="detection-item {level_class}">
                                    {det['icon']} <b>{det['class_name'].upper()}</b><br>
                                    📍 Grid: <b>{det['grid_ref']}</b><br>
                                    🎯 Confidence: {det['confidence']:.1%}<br>
                                    ⚠️ Threat: {det['threat_level']} ({det['threat_score']} pts)<br>
                                    <small style="color: #888;">📝 {det['description']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("✅ No threats detected in this frame")
                            
                        # Active grid cells
                        if active_cells:
                            st.markdown("---")
                            st.markdown("**Active Grid Cells:**")
                            st.markdown(" ".join([f'<span class="zone-marker zone-surveillance">{cell}</span>' 
                                                 for cell in active_cells]), unsafe_allow_html=True)
                else:
                    st.error("Failed to read frame")
                    
            finally:
                os.unlink(video_path)
    
    # ==========================================================================
    # TAB 2: Batch Processing with Tracking
    # ==========================================================================
    with tab2:
        st.markdown("### 🎬 Full Video Analysis with Object Tracking")
        st.markdown("Process entire video with **duplicate removal** and **unique object counting**.")
        
        batch_file = st.file_uploader(
            "Select video for batch analysis",
            type=["mp4", "avi", "mov", "mkv"],
            key="batch_upload"
        )
        
        if batch_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(batch_file.read())
                video_path = tmp.name
            
            try:
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                duration = total_frames / fps if fps > 0 else 0
                cap.release()
                
                video_info = {
                    "filename": batch_file.name,
                    "total_frames": total_frames,
                    "fps": fps,
                    "resolution": f"{width}x{height}",
                    "duration_seconds": duration,
                }
                
                # Video info with tracking info
                st.markdown(f"""
                <div class="analytics-card">
                    📹 <b>{batch_file.name}</b><br>
                    Frames: {total_frames} | FPS: {fps:.1f} | Resolution: {width}x{height} | 
                    Duration: {timedelta(seconds=int(duration))}<br>
                    <small>Processing every {frame_skip} frame(s) = ~{total_frames // frame_skip} frames</small><br>
                    <small>🎯 Tracking: {'Enabled' if enable_tracking else 'Disabled'} | 
                    NMS IoU: {iou_threshold} | Min Confirmations: {min_track_hits}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Start Precision Analysis", type="primary", use_container_width=True):
                    cap = cv2.VideoCapture(video_path)
                    
                    # Initialize tracker
                    tracker = ObjectTracker(
                        iou_threshold=TRACKING_IOU_THRESHOLD,
                        max_age=MAX_TRACK_AGE,
                        min_hits=min_track_hits
                    ) if enable_tracking else None
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    metrics_placeholder = st.empty()
                    
                    all_detections = []
                    frames_processed = 0
                    frame_idx = 0
                    start_time = time.time()
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Process every Nth frame
                        if frame_idx % frame_skip == 0:
                            # Detect with improved precision
                            detections = detect_objects(
                                model, frame, 
                                conf_threshold=conf_threshold,
                                iou_threshold=iou_threshold,
                                frame_idx=frame_idx, 
                                fps=fps,
                                apply_validation=True
                            )
                            
                            # Apply tracking for unique object counting
                            if tracker and detections:
                                detections = tracker.update(detections)
                            
                            all_detections.extend(detections)
                            frames_processed += 1
                            
                            # Update live metrics
                            elapsed = time.time() - start_time
                            fps_processing = frames_processed / elapsed if elapsed > 0 else 0
                            unique_count = tracker.get_unique_count() if tracker else len(all_detections)
                            
                            with metrics_placeholder.container():
                                m1, m2, m3, m4, m5 = st.columns(5)
                                m1.metric("Raw Detections", len(all_detections))
                                m2.metric("🎯 Unique Objects", unique_count)
                                m3.metric("Frames", f"{frames_processed}")
                                m4.metric("Speed", f"{fps_processing:.1f} fps")
                                m5.metric("Progress", f"{(frame_idx / total_frames) * 100:.0f}%")
                        
                        frame_idx += 1
                        progress_bar.progress(min(frame_idx / total_frames, 1.0))
                        status_text.text(f"🔍 Processing frame {frame_idx}/{total_frames}...")
                    
                    cap.release()
                    
                    # Final status
                    total_time = time.time() - start_time
                    progress_bar.progress(1.0)
                    unique_final = tracker.get_unique_count() if tracker else "N/A"
                    status_text.markdown(f"""
                    ✅ **Analysis Complete!** 
                    - Processed {frames_processed} frames in {total_time:.1f}s
                    - Found **{unique_final}** unique objects from {len(all_detections)} raw detections
                    """)
                    
                    # Generate and display analytics
                    st.markdown("---")
                    
                    if all_detections:
                        analytics = generate_analytics(all_detections, tracker)
                        render_analytics_dashboard(analytics, all_detections)
                        
                        # Download report button
                        st.markdown("---")
                        st.markdown("### 📥 Export Report")
                        
                        report_json = generate_report(analytics, all_detections, video_info)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Download JSON Report",
                                report_json,
                                file_name=f"surveillance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        with col2:
                            # Simple CSV export
                            csv_lines = ["timestamp,class,confidence,threat_level,threat_score,grid_ref"]
                            for det in all_detections:
                                csv_lines.append(f"{det['timestamp']},{det['class_name']},{det['confidence']:.2f},{det['threat_level']},{det['threat_score']},{det['grid_ref']}")
                            csv_data = "\n".join(csv_lines)
                            
                            st.download_button(
                                "📥 Download CSV Report",
                                csv_data,
                                file_name=f"detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ No objects detected in video. Try lowering the confidence threshold.")
                        
            finally:
                os.unlink(video_path)
    
    # ==========================================================================
    # TAB 3: About
    # ==========================================================================
    with tab3:
        st.markdown("### ℹ️ About This System")
        
        st.markdown("""
        <div class="analytics-card">
        <h4>🛸 Border Drone Surveillance System</h4>
        
        This enhanced MVP demonstrates AI-powered drone surveillance for border security:
        
        **Features:**
        - 🤖 **YOLOv8 Detection**: Real-time object detection using state-of-the-art neural network
        - 📊 **Detailed Analytics**: Comprehensive breakdown of detections by type, threat level, and location
        - 🗺️ **Grid Reference System**: Military-style grid overlay for precise location reporting
        - ⚠️ **Threat Scoring**: Multi-factor threat assessment based on object type, size, and position
        - 📈 **Timeline View**: Chronological detection log with timestamps
        - 📥 **Export Reports**: Downloadable JSON and CSV reports for further analysis
        
        **Detection Classes:**
        </div>
        """, unsafe_allow_html=True)
        
        # Show all detection classes
        cols = st.columns(4)
        for i, (cls_id, cls_name) in enumerate(THREAT_CLASSES.items()):
            info = THREAT_INFO.get(cls_name, {"icon": "❓", "points": 1})
            with cols[i % 4]:
                st.markdown(f"""
                <div class="detection-item">
                    {info['icon']} <b>{cls_name.upper()}</b><br>
                    <small>Points: {info['points']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="analytics-card">
        <h4>⚠️ Threat Levels</h4>
        
        - 🟢 **LOW** (0-9 pts): Minimal concern, routine monitoring
        - 🟡 **MEDIUM** (10-19 pts): Elevated attention required
        - 🟠 **HIGH** (20-29 pts): Significant threat, immediate review
        - 🔴 **CRITICAL** (30+ pts): Maximum threat, urgent response needed
        
        **Scoring Factors:**
        - Base points per object type
        - Detection confidence
        - Object size (larger = closer = higher threat)
        - Position in frame (center = higher priority)
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <center>
        <small style="color: #666;">
            Border Drone Surveillance MVP v2.0 | Enhanced Edition | 
            Built with Streamlit + YOLOv8 | Hackathon Demo
        </small>
    </center>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
