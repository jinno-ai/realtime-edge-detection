"""
Tests for the detector factory.
"""

import pytest
from src.detection.factory import DetectorFactory
from src.detection.yolov8 import YOLOv8Detector
from src.detection.yolov10 import YOLOv10Detector
from src.detection.custom import CustomDetector


class TestDetectorFactory:
    """Test DetectorFactory class."""

    def test_create_yolov8_detector(self):
        """Test creating YOLOv8 detector."""
        detector = DetectorFactory.create_detector("yolov8n")
        assert isinstance(detector, YOLOv8Detector)

    def test_create_yolov8_with_extension(self):
        """Test creating YOLOv8 detector with .pt extension."""
        detector = DetectorFactory.create_detector("yolov8n.pt")
        assert isinstance(detector, YOLOv8Detector)

    def test_create_yolov10_detector(self):
        """Test creating YOLOv10 detector."""
        detector = DetectorFactory.create_detector("yolov10n")
        assert isinstance(detector, YOLOv10Detector)

    def test_create_yolov10_with_extension(self):
        """Test creating YOLOv10 detector with .pt extension."""
        detector = DetectorFactory.create_detector("yolov10s.pt")
        assert isinstance(detector, YOLOv10Detector)

    def test_create_custom_detector_from_path(self):
        """Test creating custom detector from file path."""
        detector = DetectorFactory.create_detector("/path/to/model.pt")
        assert isinstance(detector, CustomDetector)

    def test_create_custom_detector_onnx(self):
        """Test creating custom detector from ONNX path."""
        detector = DetectorFactory.create_detector("/path/to/model.onnx")
        assert isinstance(detector, CustomDetector)

    def test_unsupported_model_type_raises_error(self):
        """Test that unsupported model type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported model type"):
            DetectorFactory.create_detector("unsupported_model")

    def test_is_supported_yolov8(self):
        """Test is_supported for YOLOv8 models."""
        assert DetectorFactory.is_supported("yolov8n")
        assert DetectorFactory.is_supported("yolov8x")

    def test_is_supported_yolov10(self):
        """Test is_supported for YOLOv10 models."""
        assert DetectorFactory.is_supported("yolov10n")
        assert DetectorFactory.is_supported("yolov10m")

    def test_is_supported_custom(self):
        """Test is_supported for custom models."""
        assert DetectorFactory.is_supported("/path/to/model.pt")
        assert DetectorFactory.is_supported("/path/to/model.onnx")

    def test_is_not_supported(self):
        """Test is_supported returns False for unsupported models."""
        assert not DetectorFactory.is_supported("invalid")

    def test_case_insensitive(self):
        """Test that model type matching is case insensitive."""
        detector = DetectorFactory.create_detector("YOLOV8N")
        assert isinstance(detector, YOLOv8Detector)

    def test_whitespace_handling(self):
        """Test that whitespace is trimmed."""
        detector = DetectorFactory.create_detector("  yolov8n  ")
        assert isinstance(detector, YOLOv8Detector)
