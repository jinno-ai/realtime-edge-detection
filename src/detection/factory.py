"""
Detector factory for creating detector instances.
"""

from pathlib import Path
from typing import Optional
from src.detection.base import AbstractDetector
from src.detection.yolov8 import YOLOv8Detector
from src.detection.yolov10 import YOLOv10Detector
from src.detection.custom import CustomDetector


class DetectorFactory:
    """
    Factory for creating detector instances based on model type.

    Supported model types:
    - YOLOv8 variants: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
    - YOLOv10 variants: yolov10n, yolov10s, yolov10m, yolov10b, yolov10l, yolov10x
    - Custom models: file paths ending in .pt or .onnx
    """

    # Supported model types mapping
    YOLOV8_MODELS = {
        "yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x",
        "yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt",
    }

    YOLOV10_MODELS = {
        "yolov10n", "yolov10s", "yolov10m", "yolov10b", "yolov10l", "yolov10x",
        "yolov10n.pt", "yolov10s.pt", "yolov10m.pt", "yolov10b.pt", "yolov10l.pt", "yolov10x.pt",
    }

    @staticmethod
    def create_detector(model_type: str) -> AbstractDetector:
        """
        Create a detector instance based on model type.

        Args:
            model_type: Model type identifier (e.g., "yolov8n", "yolov10s", "/path/to/model.pt")

        Returns:
            AbstractDetector instance (YOLOv8Detector, YOLOv10Detector, or CustomDetector)

        Raises:
            ValueError: If model type is not supported

        Examples:
            >>> detector = DetectorFactory.create_detector("yolov8n")
            >>> detector = DetectorFactory.create_detector("yolov10s")
            >>> detector = DetectorFactory.create_detector("/path/to/custom.pt")
        """
        model_type_lower = model_type.lower().strip()

        # Check YOLOv8 models FIRST (before checking for .pt extension)
        if model_type_lower in DetectorFactory.YOLOV8_MODELS:
            return YOLOv8Detector()

        # Check YOLOv10 models FIRST (before checking for .pt extension)
        if model_type_lower in DetectorFactory.YOLOV10_MODELS:
            return YOLOv10Detector()

        # Check if it's a custom model path (has path separators or unknown .pt file)
        if DetectorFactory._is_custom_model_path(model_type):
            return CustomDetector()

        # Model type not recognized
        supported = DetectorFactory._get_supported_models()
        raise ValueError(
            f"Unsupported model type: '{model_type}'\n\n"
            f"Supported model types:\n"
            f"  YOLOv8: {', '.join(sorted(set([m.replace('.pt', '') for m in DetectorFactory.YOLOV8_MODELS])))}\n"
            f"  YOLOv10: {', '.join(sorted(set([m.replace('.pt', '') for m in DetectorFactory.YOLOV10_MODELS])))}\n"
            f"  Custom: Provide file path ending in .pt or .onnx\n\n"
            f"Example usage:\n"
            f"  detector = DetectorFactory.create_detector('yolov8n')\n"
            f"  detector = DetectorFactory.create_detector('/path/to/custom_model.pt')"
        )

    @staticmethod
    def _is_custom_model_path(model_type: str) -> bool:
        """
        Check if model_type is a custom model file path.

        Args:
            model_type: Model type string

        Returns:
            True if it's a file path, False otherwise
        """
        # Check if it contains path separators (definitive sign of path)
        if '/' in model_type or '\\' in model_type:
            return True

        # Check for ONNX extension (always custom)
        if model_type.endswith('.onnx'):
            return True

        # Check for .pt extension BUT only if it's not a known YOLO model name
        # This check happens AFTER known model checks in create_detector()
        if model_type.endswith('.pt'):
            # If we get here, it wasn't in YOLOV8_MODELS or YOLOV10_MODELS
            # So it must be a custom model path
            return True

        return False

    @staticmethod
    def _get_supported_models() -> str:
        """Get formatted list of supported model types."""
        yolo8 = sorted(set([m.replace('.pt', '') for m in DetectorFactory.YOLOV8_MODELS]))
        yolo10 = sorted(set([m.replace('.pt', '') for m in DetectorFactory.YOLOV10_MODELS]))

        return f"YOLOv8: {', '.join(yolo8)}\nYOLOv10: {', '.join(yolo10)}\nCustom: .pt/.onnx file paths"

    @staticmethod
    def is_supported(model_type: str) -> bool:
        """
        Check if a model type is supported.

        Args:
            model_type: Model type to check

        Returns:
            True if supported, False otherwise
        """
        model_type_lower = model_type.lower().strip()

        # Check known models first
        if model_type_lower in DetectorFactory.YOLOV8_MODELS:
            return True

        if model_type_lower in DetectorFactory.YOLOV10_MODELS:
            return True

        # Check if it's a custom model path
        if DetectorFactory._is_custom_model_path(model_type):
            return True

        return False
