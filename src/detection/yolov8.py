"""
YOLOv8 detector implementation.
"""

import numpy as np
from typing import List
from src.detection.base import AbstractDetector, DetectionResult, ModelInfo


class YOLOv8Detector(AbstractDetector):
    """
    YOLOv8 detector implementation using ultralytics package.

    Supports all YOLOv8 variants: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
    """

    def __init__(self):
        """Initialize YOLOv8 detector."""
        super().__init__()
        self._class_names: List[str] = []

    def load_model(self, model_path: str, device: str = "cpu") -> None:
        """
        Load YOLOv8 model.

        Args:
            model_path: Path to YOLOv8 model file (e.g., "yolov8n.pt")
            device: Device to load model on ("cpu", "cuda", "mps", etc.)

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model format is invalid
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics package is required for YOLOv8Detector. "
                "Install it with: pip install ultralytics"
            )

        try:
            self._model = YOLO(model_path)
            self._model_path = model_path
            self._device = device

            # Extract class names from model
            if hasattr(self._model, 'names') and self._model.names:
                self._class_names = list(self._model.names.values())

        except Exception as e:
            raise ValueError(
                f"Failed to load YOLOv8 model from {model_path}: {e}"
            )

    def detect(self, image: np.ndarray) -> DetectionResult:
        """
        Run object detection on a single image.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format

        Returns:
            DetectionResult with boxes, scores, classes, and metadata
        """
        self._ensure_loaded()

        # Validate image format
        if not isinstance(image, np.ndarray):
            raise ValueError(f"Image must be numpy array, got {type(image)}")

        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Image must have shape (H, W, 3), got {image.shape}"
            )

        # Run inference
        results = self._model(image, device=self._device, verbose=False)

        # Extract detection data
        return self._extract_results(results[0], image.shape)

    def detect_batch(self, images: List[np.ndarray]) -> List[DetectionResult]:
        """
        Run object detection on a batch of images.

        Args:
            images: List of input images as numpy arrays

        Returns:
            List of DetectionResult objects, one per input image
        """
        self._ensure_loaded()

        if not images:
            raise ValueError("Images list cannot be empty")

        # Run batch inference
        results = self._model(images, device=self._device, verbose=False)

        # Extract results for each image
        detection_results = []
        for i, result in enumerate(results):
            detection_results.append(
                self._extract_results(result, images[i].shape)
            )

        return detection_results

    def get_model_info(self) -> ModelInfo:
        """
        Get model metadata and information.

        Returns:
            ModelInfo object with YOLOv8 model details
        """
        self._ensure_loaded()

        # Extract model name from path
        model_name = self._model_path.split('/')[-1].replace('.pt', '')

        # Get input size from model
        input_size = None
        if hasattr(self._model, 'args'):
            # Try to get imgsz from model args
            imgsz = self._model.args.get('imgsz') if hasattr(self._model, 'args') else None
            if imgsz:
                if isinstance(imgsz, (list, tuple)) and len(imgsz) >= 2:
                    input_size = tuple(imgsz[:2])
                elif isinstance(imgsz, int):
                    input_size = (imgsz, imgsz)

        return ModelInfo(
            name=model_name,
            version="8.0",  # YOLOv8 version
            input_size=input_size,
            class_names=self._class_names if self._class_names else None,
            metadata={
                "framework": "ultralytics",
                "device": self._device,
                "model_type": "YOLOv8",
            }
        )

    def _extract_results(
        self,
        result,
        image_shape: tuple
    ) -> DetectionResult:
        """
        Extract detection results from YOLOv8 output.

        Args:
            result: YOLOv8 result object
            image_shape: Original image shape (H, W, C)

        Returns:
            DetectionResult with standardized format
        """
        import time

        # Extract boxes
        if result.boxes is not None and len(result.boxes) > 0:
            # Boxes are in xyxy format
            boxes = result.boxes.xyxy.cpu().numpy()

            # Scores
            scores = result.boxes.conf.cpu().numpy()

            # Classes
            classes = result.boxes.cls.cpu().numpy().astype(int)
        else:
            # No detections
            boxes = np.empty((0, 4), dtype=np.float32)
            scores = np.empty((0,), dtype=np.float32)
            classes = np.empty((0,), dtype=np.int32)

        return DetectionResult(
            boxes=boxes,
            scores=scores,
            classes=classes,
            metadata={
                "num_detections": len(boxes),
                "inference_time": getattr(result, 'speed', {}).get('inference', 0),
            }
        )
