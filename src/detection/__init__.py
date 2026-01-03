"""
Detection module for object detection abstraction.

This module provides a unified interface for multiple detector types including
YOLOv8, YOLOv10, and custom models.
"""

from src.detection.base import AbstractDetector, DetectionResult, ModelInfo
from src.detection.yolov8 import YOLOv8Detector
from src.detection.yolov10 import YOLOv10Detector
from src.detection.custom import CustomDetector
from src.detection.factory import DetectorFactory

__all__ = [
    "AbstractDetector",
    "DetectionResult",
    "ModelInfo",
    "YOLOv8Detector",
    "YOLOv10Detector",
    "CustomDetector",
    "DetectorFactory",
]
