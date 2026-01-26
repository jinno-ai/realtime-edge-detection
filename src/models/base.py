"""
Abstract base class for object detectors.

Defines the common interface that all detector implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np


class AbstractDetector(ABC):
    """
    Base class for all object detectors.

    All detector implementations must inherit from this class and implement
    the defined abstract methods to ensure consistent interface across different
    model types (YOLO v8, YOLO v10, custom models, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize detector with configuration.

        Args:
            config: Configuration dictionary containing model parameters
        """
        self.config = config
        self.device = None
        self.model = None
        self.class_names = []

    @abstractmethod
    def load_model(self) -> None:
        """
        Load model into memory.

        This method should initialize the model, load weights, and set up
        the device for inference. Must be called before detect() or detect_batch().

        Raises:
            RuntimeError: If model loading fails
        """
        pass

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on a single image.

        Args:
            image: Input image as numpy array (BGR format)

        Returns:
            List of detections, each detection is a dict containing:
                - 'class': str, class name
                - 'confidence': float, confidence score (0-1)
                - 'bbox': List[int], bounding box [x1, y1, x2, y2]

        Raises:
            RuntimeError: If model not loaded
            ValueError: If image format is invalid
        """
        pass

    @abstractmethod
    def detect_batch(self, images: List[np.ndarray]) -> List[List[Dict[str, Any]]]:
        """
        Run detection on a batch of images.

        Args:
            images: List of input images as numpy arrays

        Returns:
            List of detection lists, one list per input image

        Raises:
            RuntimeError: If model not loaded
            ValueError: If images list is empty or format invalid
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Return model metadata.

        Returns:
            Dictionary containing:
                - 'name': str, model name
                - 'version': str, model version
                - 'classes': List[str], list of class names
                - 'input_size': Tuple[int, int], expected input size (width, height)
                - 'num_params': int, number of parameters (optional)
        """
        pass

    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        show_confidence: bool = True
    ) -> np.ndarray:
        """
        Draw detection boxes and labels on image.

        This is a default implementation that can be overridden by subclasses
        for custom visualization.

        Args:
            image: Input image
            detections: List of detection dictionaries
            show_confidence: Whether to show confidence scores

        Returns:
            Image with drawn detections (new array, doesn't modify input)
        """
        import cv2

        # Create a copy to avoid modifying original
        output = image.copy()

        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class']
            confidence = detection['confidence']

            x1, y1, x2, y2 = bbox

            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Prepare label text
            label = class_name
            if show_confidence:
                label += f' {confidence:.2f}'

            # Draw label background
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            cv2.rectangle(
                output,
                (x1, y1 - label_height - baseline - 5),
                (x1 + label_width, y1),
                (0, 255, 0),
                -1
            )

            # Draw label text
            cv2.putText(
                output,
                label,
                (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2
            )

        return output

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image before detection.

        Default implementation returns image as-is. Subclasses can override
        for model-specific preprocessing (normalization, resizing, etc.).

        Args:
            image: Input image

        Returns:
            Preprocessed image
        """
        return image

    def postprocess(
        self,
        raw_output: Any,
        original_shape: Tuple[int, int, int]
    ) -> List[Dict[str, Any]]:
        """
        Postprocess raw model output.

        Default implementation converts raw output to standard format.
        Subclasses can override for model-specific postprocessing.

        Args:
            raw_output: Raw output from model
            original_shape: Original image shape (height, width, channels)

        Returns:
            List of detection dictionaries
        """
        return []
