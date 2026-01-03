"""
Unit tests for configuration validation.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config.validation import (
    EdgeDetectionConfig,
    ModelConfig,
    DeviceConfig,
    DetectionConfig,
    validate_config,
)


class TestModelConfig:
    """Test ModelConfig validation."""

    def test_valid_model_names(self):
        """Test valid model names."""
        valid_names = ['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x', 'yolov10n', 'yolov10s']
        for name in valid_names:
            config = ModelConfig(name=name)
            assert config.name == name

    def test_invalid_model_name(self):
        """Test invalid model name raises error."""
        with pytest.raises(ValueError, match="Invalid model name"):
            ModelConfig(name="invalid_model")

    def test_custom_model_name(self):
        """Test custom model name is allowed."""
        config = ModelConfig(name="custom")
        assert config.name == "custom"

    def test_model_name_case_insensitive(self):
        """Test model name is converted to lowercase."""
        config = ModelConfig(name="YOLOV8N")
        assert config.name == "yolov8n"


class TestDeviceConfig:
    """Test DeviceConfig validation."""

    def test_valid_device_types(self):
        """Test valid device types."""
        valid_types = ['auto', 'cpu', 'cuda', 'mps', 'tpu', 'onnx']
        for device_type in valid_types:
            config = DeviceConfig(type=device_type)
            assert config.type == device_type

    def test_cuda_device_with_index(self):
        """Test CUDA device with index."""
        config = DeviceConfig(type="cuda:0")
        assert config.type == "cuda:0"

    def test_invalid_device_type(self):
        """Test invalid device type raises error."""
        with pytest.raises(ValueError, match="Invalid device type"):
            DeviceConfig(type="invalid_device")


class TestDetectionConfig:
    """Test DetectionConfig validation."""

    def test_valid_confidence_threshold(self):
        """Test valid confidence thresholds."""
        thresholds = [0.0, 0.25, 0.5, 0.75, 1.0]
        for threshold in thresholds:
            config = DetectionConfig(confidence_threshold=threshold)
            assert config.confidence_threshold == threshold

    def test_invalid_confidence_threshold_high(self):
        """Test confidence threshold > 1.0 raises error."""
        with pytest.raises(ValueError):
            DetectionConfig(confidence_threshold=1.5)

    def test_invalid_confidence_threshold_low(self):
        """Test confidence threshold < 0.0 raises error."""
        with pytest.raises(ValueError):
            DetectionConfig(confidence_threshold=-0.1)

    def test_valid_iou_threshold(self):
        """Test valid IOU thresholds."""
        thresholds = [0.0, 0.25, 0.5, 0.75, 1.0]
        for threshold in thresholds:
            config = DetectionConfig(iou_threshold=threshold)
            assert config.iou_threshold == threshold

    def test_invalid_iou_threshold(self):
        """Test IOU threshold > 1.0 raises error."""
        with pytest.raises(ValueError):
            DetectionConfig(iou_threshold=1.5)

    def test_valid_max_detections(self):
        """Test valid max_detections values."""
        config = DetectionConfig(max_detections=500)
        assert config.max_detections == 500

    def test_invalid_max_detections_low(self):
        """Test max_detections < 1 raises error."""
        with pytest.raises(ValueError):
            DetectionConfig(max_detections=0)

    def test_invalid_max_detections_high(self):
        """Test max_detections > 1000 raises error."""
        with pytest.raises(ValueError):
            DetectionConfig(max_detections=1001)


class TestEdgeDetectionConfig:
    """Test complete EdgeDetectionConfig validation."""

    def test_valid_configuration(self):
        """Test creating valid complete configuration."""
        config = EdgeDetectionConfig()
        assert config.model.name == "yolov8n"
        assert config.device.type == "auto"
        assert config.detection.confidence_threshold == 0.25

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = EdgeDetectionConfig(
            model=ModelConfig(name="yolov8s"),
            device=DeviceConfig(type="cpu"),
            detection=DetectionConfig(confidence_threshold=0.5)
        )
        assert config.model.name == "yolov8s"
        assert config.device.type == "cpu"
        assert config.detection.confidence_threshold == 0.5

    def test_validation_from_dict(self):
        """Test validation from dictionary."""
        config_dict = {
            "model": {"name": "yolov8n"},
            "device": {"type": "cpu"},
            "detection": {"confidence_threshold": 0.3}
        }
        config = EdgeDetectionConfig(**config_dict)
        assert config.model.name == "yolov8n"
        assert config.device.type == "cpu"
        assert config.detection.confidence_threshold == 0.3


class TestValidateConfig:
    """Test validate_config function."""

    def test_valid_config_dict(self):
        """Test validating valid configuration dictionary."""
        config_dict = {
            "model": {"name": "yolov8n"},
            "device": {"type": "cpu"},
            "detection": {"confidence_threshold": 0.5}
        }
        validated = validate_config(config_dict)
        assert isinstance(validated, EdgeDetectionConfig)

    def test_invalid_config_dict_raises_error(self):
        """Test invalid configuration raises ValueError."""
        config_dict = {
            "model": {"name": "invalid"},
            "device": {"type": "cpu"},
        }
        with pytest.raises(ValueError, match="Invalid model name"):
            validate_config(config_dict)

    def test_invalid_confidence_includes_hint(self):
        """Test error message includes hint for invalid confidence."""
        config_dict = {
            "detection": {"confidence_threshold": 1.5}
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_dict)
        error_msg = str(exc_info.value)
        assert "💡 Hint:" in error_msg
        assert "0.0 and 1.0" in error_msg

    def test_invalid_device_includes_hint(self):
        """Test error message includes hint for invalid device."""
        config_dict = {
            "device": {"type": "invalid"}
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_dict)
        error_msg = str(exc_info.value)
        assert "💡 Hint:" in error_msg
        assert "auto, cpu, cuda" in error_msg
