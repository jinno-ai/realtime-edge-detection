"""
Custom detector implementation for user-provided models.
"""

import numpy as np
from typing import List, Optional
from pathlib import Path
from src.detection.base import AbstractDetector, DetectionResult, ModelInfo


class CustomDetector(AbstractDetector):
    """
    Custom detector implementation for user-provided .pt or .onnx models.

    Supports any YOLO-compatible model file.
    """

    def __init__(self):
        """Initialize CustomDetector."""
        super().__init__()
        self._class_names: Optional[List[str]] = None

    def load_model(
        self,
        model_path: str,
        device: str = "cpu",
        class_names: Optional[List[str]] = None
    ) -> None:
        """
        Load custom model (.pt or .onnx).

        Args:
            model_path: Path to custom model file
            device: Device to load model on
            class_names: Optional list of class names (overrides model metadata)

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model format is invalid
        """
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics package is required for CustomDetector. "
                "Install it with: pip install ultralytics"
            )

        try:
            self._model = YOLO(model_path)
            self._model_path = model_path
            self._device = device

            # Use provided class names or extract from model
            if class_names is not None:
                self._class_names = class_names
            elif hasattr(self._model, 'names') and self._model.names:
                self._class_names = list(self._model.names.values())
            else:
                # Default COCO class names
                self._class_names = self._get_coco_class_names()

        except Exception as e:
            raise ValueError(
                f"Failed to load custom model from {model_path}: {e}"
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

        if not isinstance(image, np.ndarray):
            raise ValueError(f"Image must be numpy array, got {type(image)}")

        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Image must have shape (H, W, 3), got {image.shape}"
            )

        # Run inference
        results = self._model(image, device=self._device, verbose=False)

        # Extract detection data
        return self._extract_results(results[0])

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
        return [self._extract_results(result) for result in results]

    def get_model_info(self) -> ModelInfo:
        """
        Get model metadata and information.

        Returns:
            ModelInfo object with custom model details
        """
        self._ensure_loaded()

        # Extract model name from path
        model_name = Path(self._model_path).stem

        # Get input size from model
        input_size = None
        if hasattr(self._model, 'args'):
            imgsz = self._model.args.get('imgsz') if hasattr(self._model, 'args') else None
            if imgsz:
                if isinstance(imgsz, (list, tuple)) and len(imgsz) >= 2:
                    input_size = tuple(imgsz[:2])
                elif isinstance(imgsz, int):
                    input_size = (imgsz, imgsz)

        return ModelInfo(
            name=model_name,
            version=None,  # Unknown for custom models
            input_size=input_size,
            class_names=self._class_names if self._class_names else None,
            metadata={
                "framework": "ultralytics",
                "device": self._device,
                "model_type": "Custom",
                "model_path": self._model_path,
            }
        )

    def _extract_results(self, result) -> DetectionResult:
        """
        Extract detection results from model output.

        Args:
            result: Model result object

        Returns:
            DetectionResult with standardized format
        """
        # Extract boxes
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
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

    @staticmethod
    def _get_coco_class_names() -> List[str]:
        """Get default COCO class names."""
        return [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
            "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
            "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
            "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
            "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
            "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
            "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
            "toothbrush"
        ]
