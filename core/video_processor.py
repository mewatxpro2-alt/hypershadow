"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - VIDEO PROCESSOR
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: core/video_processor.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    This module handles video file operations including:
    - Loading and validating video files
    - Extracting frames for processing
    - Managing frame buffer
    - Generating thumbnails and screenshots
    - Video metadata extraction
    
SECURITY NOTE:
    All video processing is done locally. No video data is transmitted
    to external services.

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Third-party imports
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("WARNING: OpenCV not installed")

# Local imports
from config.settings import (
    VIDEO_CONFIG,
    DATA_DIR,
    CACHE_DIR,
    SCREENSHOTS_DIR,
)

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VideoMetadata:
    """
    Metadata for a video file.
    
    Attributes:
        path: Full path to video file
        filename: Just the filename
        width: Frame width in pixels
        height: Frame height in pixels
        fps: Frames per second
        total_frames: Total number of frames
        duration_seconds: Video duration
        file_size_mb: File size in megabytes
        codec: Video codec
        created: File creation time
    """
    path: str
    filename: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration_seconds: float
    file_size_mb: float
    codec: str = "unknown"
    created: datetime = None
    
    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 2),
            "total_frames": self.total_frames,
            "duration_seconds": round(self.duration_seconds, 2),
            "duration_formatted": self.format_duration(),
            "file_size_mb": round(self.file_size_mb, 2),
            "codec": self.codec,
            "created": self.created.isoformat() if self.created else None,
        }
    
    def format_duration(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        total_seconds = int(self.duration_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


@dataclass
class FrameData:
    """
    Container for a video frame and its metadata.
    
    Attributes:
        frame: The actual frame as numpy array
        frame_number: Frame index in video
        timestamp: Relative timestamp from video start
        width: Frame width
        height: Frame height
    """
    frame: np.ndarray
    frame_number: int
    timestamp: float
    width: int
    height: int
    
    @property
    def shape(self) -> Tuple[int, int, int]:
        """Get frame shape (height, width, channels)."""
        return self.frame.shape


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO PROCESSOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class VideoProcessor:
    """
    Handles video file loading, frame extraction, and processing.
    
    This class provides a high-level interface for working with
    surveillance video files.
    
    Example:
        >>> processor = VideoProcessor("surveillance.mp4")
        >>> print(processor.metadata.duration_formatted)
        '05:32'
        >>> for frame_data in processor.get_frames():
        ...     # Process frame
        ...     pass
    """
    
    def __init__(self, video_path: Optional[str] = None):
        """
        Initialize the video processor.
        
        Args:
            video_path: Path to video file (can be set later)
            
        Raises:
            RuntimeError: If OpenCV is not available
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV not installed. Run: pip install opencv-python")
        
        self.video_path = video_path
        self.capture: Optional[cv2.VideoCapture] = None
        self.metadata: Optional[VideoMetadata] = None
        
        # Frame buffer for caching
        self.frame_buffer: List[FrameData] = []
        self.buffer_size = VIDEO_CONFIG.get("frame_buffer_size", 30)
        
        # Statistics
        self.frames_extracted = 0
        self.frames_cached = 0
        
        if video_path:
            self.load_video(video_path)
    
    def load_video(self, video_path: str) -> VideoMetadata:
        """
        Load a video file and extract metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoMetadata object
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format is not supported or file too large
            RuntimeError: If video cannot be opened
        """
        path = Path(video_path)
        
        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Check file extension
        suffix = path.suffix.lower()
        if suffix not in VIDEO_CONFIG["supported_formats"]:
            raise ValueError(
                f"Unsupported video format: {suffix}. "
                f"Supported: {VIDEO_CONFIG['supported_formats']}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        max_size = VIDEO_CONFIG["max_video_size_mb"]
        if file_size_mb > max_size:
            raise ValueError(
                f"Video too large: {file_size_mb:.1f}MB (max: {max_size}MB)"
            )
        
        # Close existing capture if any
        self.release()
        
        # Open video
        self.capture = cv2.VideoCapture(str(path))
        
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        # Extract metadata
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get codec
        fourcc_int = int(self.capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        
        # Calculate duration
        duration = total_frames / fps if fps > 0 else 0
        
        # Check duration limit
        max_duration = VIDEO_CONFIG["max_duration_minutes"] * 60
        if duration > max_duration:
            self.release()
            raise ValueError(
                f"Video too long: {duration/60:.1f} min "
                f"(max: {VIDEO_CONFIG['max_duration_minutes']} min)"
            )
        
        # Get file creation time
        try:
            created = datetime.fromtimestamp(path.stat().st_mtime)
        except Exception:
            created = datetime.now()
        
        self.metadata = VideoMetadata(
            path=str(path),
            filename=path.name,
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_seconds=duration,
            file_size_mb=file_size_mb,
            codec=codec,
            created=created
        )
        
        self.video_path = str(path)
        
        logger.info(
            f"Loaded video: {path.name}, "
            f"{width}x{height}, {fps:.1f}fps, "
            f"{self.metadata.format_duration()}"
        )
        
        return self.metadata
    
    def get_frames(
        self,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        frame_skip: Optional[int] = None,
        resize: Optional[Tuple[int, int]] = None
    ) -> Generator[FrameData, None, None]:
        """
        Generator that yields video frames.
        
        Args:
            start_frame: Frame number to start from
            end_frame: Frame number to end at (None = end of video)
            frame_skip: Skip every N frames (None = use config default)
            resize: Resize frames to (width, height) if specified
            
        Yields:
            FrameData objects containing frames and metadata
            
        Example:
            >>> for frame_data in processor.get_frames(frame_skip=3):
            ...     cv2.imshow("Frame", frame_data.frame)
        """
        if self.capture is None:
            raise RuntimeError("No video loaded. Call load_video() first.")
        
        frame_skip = frame_skip or VIDEO_CONFIG["frame_skip"]
        end_frame = end_frame or self.metadata.total_frames
        
        # Seek to start frame
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_frame = start_frame
        fps = self.metadata.fps
        
        while current_frame < end_frame:
            ret, frame = self.capture.read()
            
            if not ret:
                break
            
            # Skip frames if configured
            if (current_frame - start_frame) % frame_skip != 0:
                current_frame += 1
                continue
            
            # Resize if requested
            if resize:
                frame = cv2.resize(frame, resize)
            
            # Calculate timestamp
            timestamp = current_frame / fps if fps > 0 else 0
            
            # Create frame data
            frame_data = FrameData(
                frame=frame,
                frame_number=current_frame,
                timestamp=timestamp,
                width=frame.shape[1],
                height=frame.shape[0]
            )
            
            self.frames_extracted += 1
            current_frame += 1
            
            yield frame_data
    
    def get_frame_at(self, frame_number: int) -> Optional[FrameData]:
        """
        Get a specific frame by number.
        
        Args:
            frame_number: Frame index to retrieve
            
        Returns:
            FrameData object or None if frame not available
        """
        if self.capture is None:
            raise RuntimeError("No video loaded")
        
        if frame_number < 0 or frame_number >= self.metadata.total_frames:
            return None
        
        # Seek to frame
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.capture.read()
        
        if not ret:
            return None
        
        timestamp = frame_number / self.metadata.fps if self.metadata.fps > 0 else 0
        
        return FrameData(
            frame=frame,
            frame_number=frame_number,
            timestamp=timestamp,
            width=frame.shape[1],
            height=frame.shape[0]
        )
    
    def get_frame_at_time(self, seconds: float) -> Optional[FrameData]:
        """
        Get frame at a specific time position.
        
        Args:
            seconds: Time position in seconds
            
        Returns:
            FrameData object or None
        """
        if self.metadata is None:
            return None
        
        frame_number = int(seconds * self.metadata.fps)
        return self.get_frame_at(frame_number)
    
    def generate_thumbnail(
        self,
        frame_number: Optional[int] = None,
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Generate a thumbnail image from the video.
        
        Args:
            frame_number: Frame to use (default: 10% into video)
            size: Thumbnail size (default from config)
            
        Returns:
            Thumbnail image as numpy array
        """
        if self.metadata is None:
            return None
        
        # Default to frame at 10% of video
        if frame_number is None:
            frame_number = int(self.metadata.total_frames * 0.1)
        
        size = size or VIDEO_CONFIG["thumbnail_size"]
        
        frame_data = self.get_frame_at(frame_number)
        if frame_data is None:
            return None
        
        thumbnail = cv2.resize(frame_data.frame, size)
        return thumbnail
    
    def save_screenshot(
        self,
        frame: np.ndarray,
        filename: Optional[str] = None,
        directory: Optional[str] = None
    ) -> str:
        """
        Save a frame as a screenshot image.
        
        Args:
            frame: Frame to save
            filename: Output filename (auto-generated if None)
            directory: Output directory (default: screenshots/)
            
        Returns:
            Path to saved screenshot
        """
        directory = directory or str(SCREENSHOTS_DIR)
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.jpg"
        
        filepath = Path(directory) / filename
        
        # Save with specified quality
        quality = VIDEO_CONFIG.get("thumbnail_quality", 90)
        cv2.imwrite(
            str(filepath),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)
    
    def extract_clip(
        self,
        start_frame: int,
        end_frame: int,
        output_path: str,
        fps: Optional[float] = None
    ) -> str:
        """
        Extract a clip from the video.
        
        Args:
            start_frame: Starting frame number
            end_frame: Ending frame number
            output_path: Path for output video file
            fps: Output FPS (default: same as source)
            
        Returns:
            Path to saved clip
        """
        if self.capture is None or self.metadata is None:
            raise RuntimeError("No video loaded")
        
        fps = fps or self.metadata.fps
        width = self.metadata.width
        height = self.metadata.height
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        try:
            for frame_data in self.get_frames(start_frame, end_frame, frame_skip=1):
                out.write(frame_data.frame)
        finally:
            out.release()
        
        logger.info(f"Clip extracted: {output_path}")
        return output_path
    
    def get_progress(self) -> float:
        """
        Get current read position as progress percentage.
        
        Returns:
            Progress from 0.0 to 1.0
        """
        if self.capture is None or self.metadata is None:
            return 0.0
        
        current = self.capture.get(cv2.CAP_PROP_POS_FRAMES)
        total = self.metadata.total_frames
        
        return current / total if total > 0 else 0.0
    
    def reset(self) -> None:
        """Reset video to beginning."""
        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    def release(self) -> None:
        """Release video capture resources."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        
        self.frame_buffer.clear()
        logger.debug("Video resources released")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release resources."""
        self.release()
    
    def __del__(self):
        """Destructor - ensure resources are released."""
        self.release()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def list_videos(directory: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all video files in a directory.
    
    Args:
        directory: Directory to search (default: data/videos/)
        
    Returns:
        List of dictionaries with video info
    """
    directory = Path(directory) if directory else DATA_DIR / "videos"
    
    if not directory.exists():
        return []
    
    videos = []
    supported = VIDEO_CONFIG["supported_formats"]
    
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in supported:
            stat = path.stat()
            videos.append({
                "filename": path.name,
                "path": str(path),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    
    # Sort by modification time (newest first)
    videos.sort(key=lambda x: x["modified"], reverse=True)
    
    return videos


def validate_video(video_path: str) -> Dict[str, Any]:
    """
    Validate a video file without fully loading it.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dict with validation results
    """
    result = {
        "valid": False,
        "path": video_path,
        "errors": [],
        "warnings": [],
        "metadata": None,
    }
    
    path = Path(video_path)
    
    # Check file exists
    if not path.exists():
        result["errors"].append("File not found")
        return result
    
    # Check extension
    if path.suffix.lower() not in VIDEO_CONFIG["supported_formats"]:
        result["errors"].append(f"Unsupported format: {path.suffix}")
        return result
    
    # Check file size
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > VIDEO_CONFIG["max_video_size_mb"]:
        result["errors"].append(
            f"File too large: {size_mb:.1f}MB "
            f"(max: {VIDEO_CONFIG['max_video_size_mb']}MB)"
        )
        return result
    
    # Try to open and get metadata
    try:
        processor = VideoProcessor(video_path)
        result["metadata"] = processor.metadata.to_dict()
        processor.release()
        result["valid"] = True
    except Exception as e:
        result["errors"].append(str(e))
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Video Processor Test")
    print("=" * 70)
    
    # List available videos
    print("\nSearching for videos...")
    videos = list_videos()
    
    if videos:
        print(f"\nFound {len(videos)} video(s):")
        for v in videos:
            print(f"  - {v['filename']} ({v['size_mb']} MB)")
        
        # Test with first video
        first_video = videos[0]["path"]
        print(f"\nTesting with: {first_video}")
        
        try:
            with VideoProcessor(first_video) as processor:
                print("\nVideo Metadata:")
                for key, value in processor.metadata.to_dict().items():
                    print(f"  {key}: {value}")
                
                # Extract a few frames
                print("\nExtracting sample frames...")
                count = 0
                for frame_data in processor.get_frames(frame_skip=30):
                    count += 1
                    if count <= 3:
                        print(f"  Frame {frame_data.frame_number}: "
                              f"{frame_data.width}x{frame_data.height}")
                    if count >= 10:
                        break
                
                print(f"\nExtracted {count} frames")
        
        except Exception as e:
            print(f"Error processing video: {e}")
    
    else:
        print("\nNo videos found in data/videos/")
        print("Place video files there to test.")
    
    print("\n" + "=" * 70)
