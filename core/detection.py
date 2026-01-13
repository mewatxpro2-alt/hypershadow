"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - LOCAL YOLOV8 DETECTION ENGINE
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: core/detection.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    This module provides LOCAL object detection using YOLOv8.
    NO EXTERNAL API CALLS - all inference runs on local hardware.
    
SECURITY NOTES:
    - Model files are stored locally in the models/ directory
    - No network connections are made during inference
    - All processing happens on the local machine
    - Detection results are stored in encrypted database
    
DEPENDENCIES:
    - ultralytics (YOLOv8 implementation)
    - torch (PyTorch for model inference)
    - opencv-python (image processing)
    - numpy (array operations)
    
USAGE:
    from core.detection import DetectionEngine
    
    # Initialize engine
    engine = DetectionEngine()
    
    # Process a single frame
    detections = engine.detect_frame(frame)
    
    # Process entire video
    for result in engine.process_video(video_path):
        print(result)

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator, Any
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Third-party imports
import numpy as np

# Try to import required libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("WARNING: OpenCV not installed. Install with: pip install opencv-python")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("WARNING: Ultralytics not installed. Install with: pip install ultralytics")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not installed. Install with: pip install torch")

# Local imports
from config.settings import (
    MODEL_CONFIG,
    THREAT_CLASSES,
    IGNORE_CLASSES,
    VIDEO_CONFIG,
    BORDER_CONFIG,
    MODELS_DIR,
    LOGGING_CONFIG,
)

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION RESULT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Detection:
    """
    Represents a single object detection from YOLOv8.
    
    This class encapsulates all information about a detected object,
    making it easy to pass detection data between modules.
    
    Attributes:
        class_id (int): COCO class ID (e.g., 0 for person)
        class_name (str): Human-readable class name (e.g., "person")
        confidence (float): Detection confidence (0.0 to 1.0)
        bbox (Tuple[int, int, int, int]): Bounding box (x1, y1, x2, y2)
        center (Tuple[int, int]): Center point (x, y)
        timestamp (datetime): When detection occurred
        frame_number (int): Video frame number
        
    Example:
        >>> detection = Detection(
        ...     class_id=0,
        ...     class_name="person",
        ...     confidence=0.95,
        ...     bbox=(100, 200, 150, 300),
        ...     frame_number=42
        ... )
        >>> print(detection.center)
        (125, 250)
    """
    
    def __init__(
        self,
        class_id: int,
        class_name: str,
        confidence: float,
        bbox: Tuple[int, int, int, int],
        frame_number: int = 0,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a Detection object.
        
        Args:
            class_id: COCO dataset class ID
            class_name: Human-readable class name
            confidence: Detection confidence score (0-1)
            bbox: Bounding box coordinates (x1, y1, x2, y2)
            frame_number: Frame number in video
            timestamp: Time of detection (defaults to now)
        """
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox
        self.frame_number = frame_number
        self.timestamp = timestamp or datetime.now()
        
        # Calculate derived properties
        x1, y1, x2, y2 = bbox
        self.center = ((x1 + x2) // 2, (y1 + y2) // 2)
        self.width = x2 - x1
        self.height = y2 - y1
        self.area = self.width * self.height
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert detection to dictionary for storage/serialization.
        
        Returns:
            Dict containing all detection data
        """
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox,
            "center_x": self.center[0],
            "center_y": self.center[1],
            "width": self.width,
            "height": self.height,
            "area": self.area,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Detection(class={self.class_name}, conf={self.confidence:.2f}, "
            f"center={self.center}, frame={self.frame_number})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DETECTION ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class DetectionEngine:
    """
    Local YOLOv8 detection engine for border surveillance.
    
    This class handles all object detection operations using a locally
    installed YOLOv8 model. NO EXTERNAL API CALLS are made.
    
    SECURITY NOTE:
        All processing is done locally. The model file must be present
        in the models/ directory before use.
        
    Attributes:
        model: Loaded YOLOv8 model
        device: Computing device (cpu/cuda)
        confidence_threshold: Minimum confidence for detections
        
    Example:
        >>> engine = DetectionEngine()
        >>> frame = cv2.imread("test_frame.jpg")
        >>> detections = engine.detect_frame(frame)
        >>> for det in detections:
        ...     print(f"{det.class_name}: {det.confidence:.2f}")
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ):
        """
        Initialize the detection engine with a local YOLOv8 model.
        
        Args:
            model_path: Path to YOLOv8 model file (.pt)
                       Defaults to MODEL_CONFIG["regular"]
            device: Computing device ("cpu" or "cuda")
                   Defaults to MODEL_CONFIG["device"]
            confidence_threshold: Minimum detection confidence
                                 Defaults to MODEL_CONFIG["confidence_threshold"]
            iou_threshold: IOU threshold for NMS
                          Defaults to MODEL_CONFIG["iou_threshold"]
                          
        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If required libraries not installed
        """
        # Check dependencies
        if not YOLO_AVAILABLE:
            raise RuntimeError(
                "YOLOv8 not available. Install with: pip install ultralytics"
            )
        if not CV2_AVAILABLE:
            raise RuntimeError(
                "OpenCV not available. Install with: pip install opencv-python"
            )
        
        # Set configuration
        self.model_path = model_path or MODEL_CONFIG["regular"]
        self.device = device or MODEL_CONFIG["device"]
        self.confidence_threshold = confidence_threshold or MODEL_CONFIG["confidence_threshold"]
        self.iou_threshold = iou_threshold or MODEL_CONFIG["iou_threshold"]
        
        # Validate model path
        if not Path(self.model_path).exists():
            # Try to find model in MODELS_DIR
            alt_path = MODELS_DIR / Path(self.model_path).name
            if alt_path.exists():
                self.model_path = str(alt_path)
            else:
                logger.warning(
                    f"Model not found at {self.model_path}. "
                    f"Will attempt to download on first use."
                )
        
        # Load model
        self.model = None
        self._load_model()
        
        # Statistics tracking
        self.total_frames_processed = 0
        self.total_detections = 0
        self.last_detection_time = None
        
        logger.info(
            f"DetectionEngine initialized: model={self.model_path}, "
            f"device={self.device}, conf={self.confidence_threshold}"
        )
    
    def _load_model(self) -> None:
        """
        Load the YOLOv8 model from local file.
        
        SECURITY NOTE:
            This loads a LOCAL model file. No network calls are made
            if the model file already exists.
        """
        try:
            logger.info(f"Loading YOLOv8 model from {self.model_path}")
            
            # Load model
            self.model = YOLO(self.model_path)
            
            # Set device
            if self.device == "auto":
                # Auto-detect GPU
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info("CUDA GPU detected, using GPU acceleration")
                else:
                    self.device = "cpu"
                    logger.info("No GPU detected, using CPU")
            
            # Move model to device
            self.model.to(self.device)
            
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Could not load YOLOv8 model: {e}")
    
    def detect_frame(
        self,
        frame: np.ndarray,
        frame_number: int = 0,
        timestamp: Optional[datetime] = None
    ) -> List[Detection]:
        """
        Run detection on a single video frame.
        
        This is the core detection function. It runs YOLOv8 inference
        on the provided frame and returns filtered detections.
        
        Args:
            frame: Video frame as numpy array (BGR format from OpenCV)
            frame_number: Frame number in video sequence
            timestamp: Time of frame capture
            
        Returns:
            List of Detection objects for threat classes only
            
        Example:
            >>> frame = cv2.imread("frame.jpg")
            >>> detections = engine.detect_frame(frame)
            >>> print(f"Found {len(detections)} objects")
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received, skipping detection")
            return []
        
        timestamp = timestamp or datetime.now()
        detections = []
        
        try:
            # Run inference
            # verbose=False suppresses output, stream=False returns results immediately
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False,
                stream=False,
                device=self.device
            )
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                if boxes is None or len(boxes) == 0:
                    continue
                
                # Iterate through each detection
                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])
                    
                    # Skip ignored classes (animals, etc.)
                    if class_id in IGNORE_CLASSES:
                        continue
                    
                    # Only process threat classes (persons, vehicles)
                    if class_id not in THREAT_CLASSES:
                        continue
                    
                    # Get class name
                    class_name = THREAT_CLASSES.get(class_id, "unknown")
                    
                    # Get confidence
                    confidence = float(box.conf[0])
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bbox = (int(x1), int(y1), int(x2), int(y2))
                    
                    # Create Detection object
                    detection = Detection(
                        class_id=class_id,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=bbox,
                        frame_number=frame_number,
                        timestamp=timestamp
                    )
                    
                    detections.append(detection)
            
            # Update statistics
            self.total_frames_processed += 1
            self.total_detections += len(detections)
            if detections:
                self.last_detection_time = timestamp
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error on frame {frame_number}: {e}")
            return []
    
    def process_video(
        self,
        video_path: str,
        frame_skip: Optional[int] = None,
        max_frames: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process an entire video file and yield detections frame by frame.
        
        This is a generator function that processes the video incrementally,
        yielding results for each processed frame.
        
        Args:
            video_path: Path to video file
            frame_skip: Process every Nth frame (default from VIDEO_CONFIG)
            max_frames: Maximum frames to process (None = all)
            progress_callback: Function called with (current_frame, total_frames)
            
        Yields:
            Dict containing:
                - frame_number: int
                - timestamp: datetime
                - detections: List[Detection]
                - frame: np.ndarray (the processed frame)
                
        Example:
            >>> for result in engine.process_video("surveillance.mp4"):
            ...     print(f"Frame {result['frame_number']}: "
            ...           f"{len(result['detections'])} detections")
        """
        # Validate video path
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Check file size
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb > VIDEO_CONFIG["max_video_size_mb"]:
            raise ValueError(
                f"Video too large: {file_size_mb:.1f}MB "
                f"(max: {VIDEO_CONFIG['max_video_size_mb']}MB)"
            )
        
        # Set frame skip
        frame_skip = frame_skip or VIDEO_CONFIG["frame_skip"]
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        try:
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(
                f"Processing video: {video_path.name}, "
                f"{total_frames} frames, {fps:.1f} FPS, {width}x{height}"
            )
            
            frame_number = 0
            processed_count = 0
            start_time = datetime.now()
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break  # End of video
                
                # Skip frames if configured
                if frame_number % frame_skip != 0:
                    frame_number += 1
                    continue
                
                # Check max frames limit
                if max_frames and processed_count >= max_frames:
                    break
                
                # Calculate timestamp based on frame number and FPS
                timestamp = start_time
                if fps > 0:
                    from datetime import timedelta
                    timestamp = start_time + timedelta(seconds=frame_number / fps)
                
                # Run detection
                detections = self.detect_frame(
                    frame,
                    frame_number=frame_number,
                    timestamp=timestamp
                )
                
                # Yield result
                yield {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "detections": detections,
                    "frame": frame,
                    "total_frames": total_frames,
                    "progress": frame_number / total_frames if total_frames > 0 else 0
                }
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(frame_number, total_frames)
                
                frame_number += 1
                processed_count += 1
            
            logger.info(
                f"Video processing complete: {processed_count} frames processed, "
                f"{self.total_detections} total detections"
            )
            
        finally:
            cap.release()
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        draw_grid: bool = True,
        draw_border: bool = True
    ) -> np.ndarray:
        """
        Draw detection boxes and annotations on a frame.
        
        Args:
            frame: Original video frame
            detections: List of Detection objects
            draw_grid: Whether to draw military grid overlay
            draw_border: Whether to draw border line
            
        Returns:
            Annotated frame with bounding boxes and labels
        """
        annotated = frame.copy()
        
        # Draw grid if requested
        if draw_grid:
            annotated = self._draw_grid(annotated)
        
        # Draw border line if requested
        if draw_border:
            annotated = self._draw_border_line(annotated)
        
        # Draw each detection
        for detection in detections:
            # Determine color based on threat level
            # (This is simplified - actual color should come from threat scoring)
            if detection.confidence >= 0.9:
                color = (0, 0, 255)    # Red - high confidence
            elif detection.confidence >= 0.75:
                color = (0, 165, 255)  # Orange - medium confidence
            else:
                color = (0, 255, 255)  # Yellow - lower confidence
            
            # Draw bounding box
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label = f"{detection.class_name} {detection.confidence:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )
            
            cv2.rectangle(
                annotated,
                (x1, y1 - text_height - 5),
                (x1 + text_width, y1),
                color,
                -1  # Filled
            )
            
            # Draw label text
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 5),
                font,
                font_scale,
                (255, 255, 255),  # White text
                thickness
            )
            
            # Draw center point
            cv2.circle(annotated, detection.center, 4, color, -1)
        
        return annotated
    
    def _draw_grid(self, frame: np.ndarray) -> np.ndarray:
        """Draw military grid overlay on frame."""
        h, w = frame.shape[:2]
        
        cols = BORDER_CONFIG["grid_columns"]
        rows = BORDER_CONFIG["grid_rows"]
        col_labels = BORDER_CONFIG["column_labels"]
        row_labels = BORDER_CONFIG["row_labels"]
        
        cell_width = w // cols
        cell_height = h // rows
        
        # Grid line color (semi-transparent green)
        grid_color = (0, 200, 0)
        
        # Draw vertical lines
        for i in range(1, cols):
            x = i * cell_width
            cv2.line(frame, (x, 0), (x, h), grid_color, 1)
        
        # Draw horizontal lines
        for i in range(1, rows):
            y = i * cell_height
            cv2.line(frame, (0, y), (w, y), grid_color, 1)
        
        # Draw grid labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        for col_idx, col_label in enumerate(col_labels):
            for row_idx, row_label in enumerate(row_labels):
                label = f"{col_label}-{row_label}"
                x = col_idx * cell_width + 5
                y = row_idx * cell_height + 15
                cv2.putText(frame, label, (x, y), font, 0.4, grid_color, 1)
        
        return frame
    
    def _draw_border_line(self, frame: np.ndarray) -> np.ndarray:
        """Draw border line indicator on frame."""
        h, w = frame.shape[:2]
        border_y = BORDER_CONFIG["border_line_y"]
        
        # Scale border_y if frame dimensions differ from expected
        expected_h = BORDER_CONFIG["video_height"]
        if h != expected_h:
            border_y = int(border_y * h / expected_h)
        
        # Draw dashed red line
        dash_length = 20
        for x in range(0, w, dash_length * 2):
            cv2.line(
                frame,
                (x, border_y),
                (min(x + dash_length, w), border_y),
                (0, 0, 255),  # Red
                2
            )
        
        # Add label
        cv2.putText(
            frame,
            "--- BORDER LINE ---",
            (w // 2 - 80, border_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )
        
        return frame
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection engine statistics.
        
        Returns:
            Dict with processing statistics
        """
        return {
            "total_frames_processed": self.total_frames_processed,
            "total_detections": self.total_detections,
            "last_detection_time": (
                self.last_detection_time.isoformat()
                if self.last_detection_time else None
            ),
            "model_path": self.model_path,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
        }
    
    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        self.total_frames_processed = 0
        self.total_detections = 0
        self.last_detection_time = None


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def check_model_availability() -> Dict[str, Any]:
    """
    Check if YOLOv8 model is available locally.
    
    Returns:
        Dict with model status information
    """
    model_path = Path(MODEL_CONFIG["regular"])
    thermal_path = Path(MODEL_CONFIG["thermal"])
    
    return {
        "regular_model": {
            "path": str(model_path),
            "exists": model_path.exists(),
            "size_mb": model_path.stat().st_size / (1024 * 1024) if model_path.exists() else 0
        },
        "thermal_model": {
            "path": str(thermal_path),
            "exists": thermal_path.exists(),
            "size_mb": thermal_path.stat().st_size / (1024 * 1024) if thermal_path.exists() else 0
        },
        "yolo_available": YOLO_AVAILABLE,
        "cv2_available": CV2_AVAILABLE,
        "torch_available": TORCH_AVAILABLE,
        "cuda_available": TORCH_AVAILABLE and torch.cuda.is_available() if TORCH_AVAILABLE else False
    }


def download_model(model_name: str = "yolov8n.pt") -> str:
    """
    Download YOLOv8 model if not present.
    
    NOTE: This requires internet connection and should only be used
    during initial setup, NOT during operation.
    
    Args:
        model_name: Name of model to download (e.g., "yolov8n.pt")
        
    Returns:
        Path to downloaded model
    """
    if not YOLO_AVAILABLE:
        raise RuntimeError("Ultralytics not installed")
    
    logger.info(f"Downloading {model_name}...")
    
    # YOLO automatically downloads if not present
    model = YOLO(model_name)
    
    # Move to models directory
    target_path = MODELS_DIR / model_name
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # The model is cached in ~/.cache/ultralytics
    # Copy to our models directory
    import shutil
    cache_path = Path.home() / ".cache" / "ultralytics" / model_name
    
    if cache_path.exists():
        shutil.copy(cache_path, target_path)
        logger.info(f"Model saved to {target_path}")
    
    return str(target_path)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Test the detection engine.
    
    Usage:
        python -m core.detection [video_path]
    """
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Detection Engine Test")
    print("=" * 70)
    
    # Check model availability
    print("\nChecking model availability...")
    status = check_model_availability()
    
    for key, value in status.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    # Try to initialize engine
    print("\n" + "-" * 70)
    print("Initializing detection engine...")
    
    try:
        engine = DetectionEngine()
        print("✓ Detection engine initialized successfully")
        
        # Test with a sample frame if available
        test_image_path = Path("test_frame.jpg")
        if test_image_path.exists():
            print(f"\nTesting with {test_image_path}...")
            frame = cv2.imread(str(test_image_path))
            detections = engine.detect_frame(frame)
            print(f"Detected {len(detections)} objects:")
            for det in detections:
                print(f"  - {det}")
        else:
            print("\nNo test image found. Place 'test_frame.jpg' in working directory to test.")
        
        # Print statistics
        print("\nEngine statistics:")
        stats = engine.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
    
    print("\n" + "=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS FOR BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════
# BorderDetector is an alias for DetectionEngine for compatibility with imports
BorderDetector = DetectionEngine

