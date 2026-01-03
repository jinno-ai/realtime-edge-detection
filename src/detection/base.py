"""
Abstract base class for object detectors.

This module defines the common interface that all detector implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class DetectionResult:
    """
    Standardized detection result format.

    All detectors must return results in this format to ensure consistency.
    """
    # Bounding boxes in format [x1, y1, x2, y2] (absolute coordinates)
    boxes: np.ndarray  # Shape: (N, 4)

    # Confidence scores for each detection
    scores: np.ndarray  # Shape: (N,)

    # Class IDs for each detection
    classes: np.ndarray  # Shape: (N,)

    # Additional metadata (timing, model info, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate detection result arrays."""
        if len(self.boxes) != len(self.scores) or len(self.boxes) != len(self.classes):
            raise ValueError(
                f"Mismatch in array lengths: boxes={len(self.boxes)}, "
                f"scores={len(self.scores)}, classes={len(self.classes)}"
            )

        if self.boxes.shape[1] != 4:
            raise ValueError(f"Boxes must have shape (N, 4), got {self.boxes.shape}")


@dataclass
class ModelInfo:
    """
    Model metadata and information.

    Provides standardized model information across different detector types.
    """
    # Model name (e.g., "yolov8n", "yolov10s", "custom")
    name: str

    # Model version (if available)
    version: Optional[str] = None

    # Input size (height, width)
    input_size: Optional[tuple] = None

    # Class names list
    class_names: Optional[List[str]] = None

    # Additional model metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class AbstractDetector(ABC):
    """
    Abstract base class for object detectors.

    All detector implementations must inherit from this class and implement
    the required methods. This ensures a consistent interface across different
    model types and inference engines.
    """

    def __init__(self):
        """Initialize the detector."""
        self._model = None
        self._model_path: Optional[str] = None
        self._device: Optional[str] = None

    @abstractmethod
    def load_model(self, model_path: str, device: str = "cpu") -> None:
        """
        Load a detection model.

        Args:
            model_path: Path to the model file (e.g., "yolov8n.pt", "custom.onnx")
            device: Device to load model on ("cpu", "cuda", "mps", etc.)

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model format is invalid or incompatible
        """
        pass

    @abstractmethod
    def detect(self, image: np.ndarray) -> DetectionResult:
        """
        Run object detection on a single image.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format

        Returns:
            DetectionResult with boxes, scores, classes, and metadata

        Raises:
            RuntimeError: If model is not loaded
            ValueError: If image format is invalid
        """
        pass

    @abstractmethod
    def detect_batch(self, images: List[np.ndarray]) -> List[DetectionResult]:
        """
        Run object detection on a batch of images.

        Args:
            images: List of input images as numpy arrays (H, W, C) in RGB format

        Returns:
            List of DetectionResult objects, one per input image

        Raises:
            RuntimeError: If model is not loaded
            ValueError: If image format is invalid or list is empty
        """
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """
        Get model metadata and information.

        Returns:
            ModelInfo object with model details

        Raises:
            RuntimeError: If model is not loaded
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def _ensure_loaded(self) -> None:
        """Raise error if model is not loaded."""
        if not self.is_loaded:
            raise RuntimeError(
                f"{self.__class__.__name__}: Model not loaded. "
                f"Call load_model() first."
            )
