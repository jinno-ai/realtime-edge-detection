"""
Tests for ONNX detector implementation.
"""

import pytest
import numpy as np
from src.models.onnx import ONNXDetector
from src.models.base import AbstractDetector


class TestONNXDetector:
    """Test suite for ONNXDetector class."""

    def test_onnx_detector_is_abstract_detector(self):
        """Test that ONNXDetector inherits from AbstractDetector."""
        config = {
            'model_path': 'test.onnx',
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        assert isinstance(detector, AbstractDetector)

    def test_detector_initialization(self):
        """Test ONNXDetector can be initialized."""
        config = {
            'model_path': 'test.onnx',
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        assert detector.config == config
        assert detector.device == 'cpu'

    def test_load_onnx_model(self, tmp_path):
        """Test loading ONNX model."""
        # Create a dummy ONNX file
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)

        # This should load the model
        detector.load_model()
        assert detector.model is not None

    def test_detect_single_image(self, tmp_path):
        """Test detection on single image."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        detector.load_model()

        # Create test image
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # Run detection
        detections = detector.detect(test_image)

        # Should return list of detections
        assert isinstance(detections, list)

    def test_detect_batch_images(self, tmp_path):
        """Test batch detection."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        detector.load_model()

        # Create test images
        test_images = [
            np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            for _ in range(3)
        ]

        # Run batch detection
        batch_detections = detector.detect_batch(test_images)

        # Should return list of detection lists
        assert isinstance(batch_detections, list)
        assert len(batch_detections) == 3

    def test_get_model_info(self, tmp_path):
        """Test getting model information."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        detector.load_model()

        info = detector.get_model_info()

        assert isinstance(info, dict)
        assert 'name' in info
        assert 'classes' in info
        assert 'input_size' in info

    def test_output_format_matches_pytorch(self, tmp_path):
        """Test that ONNX output format matches PyTorch detector format."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)
        detector.load_model()

        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        detections = detector.detect(test_image)

        # Check that each detection has required fields
        for det in detections:
            assert 'class' in det
            assert 'confidence' in det
            assert 'bbox' in det
            assert isinstance(det['bbox'], list)
            assert len(det['bbox']) == 4

    def test_onnx_runtime_provider_selection(self, tmp_path):
        """Test ONNX Runtime provider selection."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        # Test CPU provider
        config = {
            'model_path': str(onnx_file),
            'device': 'cpu',
            'provider': 'CPUExecutionProvider'
        }
        detector = ONNXDetector(config=config)
        detector.load_model()
        assert detector.provider == 'CPUExecutionProvider'

    def test_preprocess(self, tmp_path):
        """Test image preprocessing."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)

        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        preprocessed = detector.preprocess(test_image)

        assert isinstance(preprocessed, np.ndarray)

    def test_postprocess(self, tmp_path):
        """Test output postprocessing."""
        onnx_file = tmp_path / "test.onnx"
        onnx_file.write_bytes(b"dummy onnx model")

        config = {
            'model_path': str(onnx_file),
            'device': 'cpu'
        }
        detector = ONNXDetector(config=config)

        # Mock raw output
        raw_output = np.random.rand(1, 84, 8400)  # Typical YOLO output shape
        detections = detector.postprocess(raw_output, (640, 640, 3))

        assert isinstance(detections, list)
