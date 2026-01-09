"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - MODEL LOADER MODULE                          ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Initialize and manage YOLOv8 detection models                       ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SECURITY NOTICE:
- All models are loaded from LOCAL storage only
- No network connections for model downloads
- Model integrity verified via checksums
"""

import hashlib
import torch
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import MODEL_CONFIG, BASE_DIR


# =============================================================================
# MODEL CHECKSUMS (for integrity verification)
# =============================================================================

# SHA256 checksums of official YOLOv8 models
# These should be updated when using specific model versions
MODEL_CHECKSUMS: Dict[str, str] = {
    "yolov8n.pt": None,  # Add checksum after downloading official model
    "yolov8s.pt": None,
    "yolov8m.pt": None,
    "yolov8l.pt": None,
    "yolov8x.pt": None,
}


# =============================================================================
# MODEL LOADER CLASS
# =============================================================================

class ModelLoader:
    """
    Handles loading and verification of YOLOv8 models.
    
    This class manages the detection model lifecycle including:
    - Loading models from local storage
    - Verifying model integrity
    - Configuring inference settings
    - Managing GPU/CPU device selection
    
    Security Features:
    - Models loaded from local filesystem only
    - Optional checksum verification
    - No automatic downloads
    
    Attributes:
        model_dir: Directory containing model files
        model: Loaded YOLO model instance
        device: Inference device (cuda/cpu)
    """
    
    def __init__(
        self,
        model_dir: Optional[Path] = None,
        verify_checksum: bool = True
    ):
        """
        Initialize the model loader.
        
        Args:
            model_dir: Directory containing model files
            verify_checksum: Whether to verify model checksums
            
        Security Note:
            Set verify_checksum=True for production deployments.
        """
        self.model_dir = model_dir or (BASE_DIR / "models")
        self.verify_checksum = verify_checksum
        self.model = None
        self.device = self._detect_device()
        self.model_info: Dict[str, Any] = {}
    
    def _detect_device(self) -> str:
        """
        Detect the best available device for inference.
        
        Returns:
            Device string ('cuda:0', 'mps', or 'cpu')
            
        Priority:
            1. CUDA (NVIDIA GPU)
            2. MPS (Apple Silicon)
            3. CPU
        """
        device = MODEL_CONFIG.get("device", "auto")
        
        if device != "auto":
            return device
        
        # Check for CUDA
        if torch.cuda.is_available():
            return "cuda:0"
        
        # Check for Apple Silicon (MPS)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        
        # Fallback to CPU
        return "cpu"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex digest of SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _verify_model(self, model_path: Path) -> bool:
        """
        Verify model file integrity.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            True if verification passes or is disabled
            
        Security Note:
            Enable checksum verification for production.
        """
        if not self.verify_checksum:
            return True
        
        model_name = model_path.name
        expected_checksum = MODEL_CHECKSUMS.get(model_name)
        
        if expected_checksum is None:
            # No checksum defined, skip verification
            print(f"[WARNING] No checksum defined for {model_name}, skipping verification")
            return True
        
        actual_checksum = self._calculate_checksum(model_path)
        
        if actual_checksum != expected_checksum:
            print(f"[SECURITY] Model checksum mismatch for {model_name}")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            return False
        
        return True
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models in the model directory.
        
        Returns:
            List of model information dictionaries
        """
        models = []
        
        if not self.model_dir.exists():
            return models
        
        for model_file in self.model_dir.glob("*.pt"):
            models.append({
                "name": model_file.name,
                "path": str(model_file),
                "size_mb": model_file.stat().st_size / (1024 * 1024),
                "checksum_available": model_file.name in MODEL_CHECKSUMS,
            })
        
        return models
    
    def load_model(
        self,
        model_name: Optional[str] = None,
        model_path: Optional[Path] = None
    ) -> bool:
        """
        Load a YOLOv8 model for inference.
        
        Args:
            model_name: Name of model file (e.g., "yolov8n.pt")
            model_path: Full path to model file (overrides model_name)
            
        Returns:
            True if model loaded successfully
            
        Security Note:
            Models are loaded from local storage only.
            No network requests are made.
        """
        # Determine model path
        if model_path:
            path = Path(model_path)
        elif model_name:
            path = self.model_dir / model_name
        else:
            # Use default from config
            path = self.model_dir / MODEL_CONFIG.get("model_path", "yolov8n.pt")
        
        # Check if model exists
        if not path.exists():
            print(f"[ERROR] Model not found: {path}")
            print(f"[INFO] Please download the model and place it in: {self.model_dir}")
            return False
        
        # Verify model integrity
        if not self._verify_model(path):
            print("[SECURITY] Model verification failed, aborting load")
            return False
        
        try:
            # Import ultralytics YOLO
            from ultralytics import YOLO
            
            # Load model
            print(f"[INFO] Loading model from: {path}")
            print(f"[INFO] Using device: {self.device}")
            
            self.model = YOLO(str(path))
            
            # Move to appropriate device
            # Note: YOLO handles device management internally
            
            # Store model info
            self.model_info = {
                "name": path.name,
                "path": str(path),
                "device": self.device,
                "size_mb": path.stat().st_size / (1024 * 1024),
                "loaded_at": str(__import__("datetime").datetime.now()),
            }
            
            print(f"[INFO] Model loaded successfully: {path.name}")
            return True
            
        except ImportError:
            print("[ERROR] ultralytics package not installed")
            print("[INFO] Install with: pip install ultralytics")
            return False
            
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
    
    def get_model(self):
        """
        Get the loaded model instance.
        
        Returns:
            YOLO model instance or None if not loaded
        """
        return self.model
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if not self.model:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            **self.model_info
        }
    
    def unload_model(self) -> None:
        """
        Unload the current model to free memory.
        
        Security Note:
            Call this when switching models or shutting down.
        """
        if self.model:
            del self.model
            self.model = None
            self.model_info = {}
            
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print("[INFO] Model unloaded")
    
    def run_inference(
        self,
        source,
        conf: float = None,
        iou: float = 0.45,
        classes: List[int] = None,
        verbose: bool = False
    ):
        """
        Run inference on an image or video frame.
        
        Args:
            source: Image/frame to process (numpy array, path, etc.)
            conf: Confidence threshold (uses config default if not provided)
            iou: IOU threshold for NMS
            classes: List of class IDs to detect (None = all classes)
            verbose: Whether to print inference details
            
        Returns:
            YOLO Results object or None if error
            
        Security Note:
            All inference happens locally.
            No data is transmitted externally.
        """
        if not self.model:
            print("[ERROR] No model loaded")
            return None
        
        # Use config confidence if not specified
        if conf is None:
            conf = MODEL_CONFIG.get("confidence_threshold", 0.7)
        
        try:
            results = self.model.predict(
                source=source,
                conf=conf,
                iou=iou,
                classes=classes,
                verbose=verbose,
                device=self.device
            )
            return results
            
        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            return None


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_model_loader_instance: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """
    Get the singleton ModelLoader instance.
    
    Returns:
        ModelLoader instance
    """
    global _model_loader_instance
    
    if _model_loader_instance is None:
        _model_loader_instance = ModelLoader()
    
    return _model_loader_instance


def load_default_model() -> bool:
    """
    Load the default detection model.
    
    Returns:
        True if model loaded successfully
        
    Convenience function for quick initialization.
    """
    loader = get_model_loader()
    return loader.load_model()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "ModelLoader",
    "get_model_loader",
    "load_default_model",
    "MODEL_CHECKSUMS",
]
