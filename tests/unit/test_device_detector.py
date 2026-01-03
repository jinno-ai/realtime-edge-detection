"""Unit tests for DeviceDetector class."""

import pytest
from unittest.mock import patch, MagicMock
from src.hardware.device_detector import DeviceDetector, DeviceType


class TestDeviceDetector:
    """Test device auto-detection functionality."""

    @patch('src.hardware.device_detector.torch.cuda.is_available')
    @patch('src.hardware.device_detector.torch.backends.mps.is_available')
    def test_auto_detection_cuda_first(self, mock_mps, mock_cuda):
        """Test AC1: Auto-detection selects CUDA when available."""
        mock_cuda.return_value = True
        mock_mps.return_value = True  # Even if MPS available, CUDA takes priority

        detector = DeviceDetector()
        device = detector.detect_device()

        assert device == DeviceType.CUDA
        assert mock_cuda.called

    @patch('src.hardware.device_detector.torch.cuda.is_available')
    @patch('src.hardware.device_detector.torch.backends.mps.is_available')
    def test_auto_detection_fallback_to_mps(self, mock_mps, mock_cuda):
        """Test AC1: Falls back to MPS when CUDA unavailable."""
        mock_cuda.return_value = False
        mock_mps.return_value = True

        detector = DeviceDetector()
        device = detector.detect_device()

        assert device == DeviceType.MPS

    @patch('src.hardware.device_detector.torch.cuda.is_available')
    @patch('src.hardware.device_detector.torch.backends.mps.is_available')
    @patch('src.hardware.device_detector.Platform.has_tflite')
    def test_auto_detection_fallback_to_tflite(self, mock_tflite, mock_mps, mock_cuda):
        """Test AC1: Falls back to TFLite when CUDA and MPS unavailable."""
        mock_cuda.return_value = False
        mock_mps.return_value = False
        mock_tflite.return_value = True

        detector = DeviceDetector()
        device = detector.detect_device()

        assert device == DeviceType.TFLITE

    @patch('src.hardware.device_detector.torch.cuda.is_available')
    @patch('src.hardware.device_detector.torch.backends.mps.is_available')
    @patch('src.hardware.device_detector.Platform.has_tflite')
    def test_auto_detection_fallback_to_cpu(self, mock_tflite, mock_mps, mock_cuda):
        """Test AC1: Falls back to CPU as last resort."""
        mock_cuda.return_value = False
        mock_mps.return_value = False
        mock_tflite.return_value = False

        detector = DeviceDetector()
        device = detector.detect_device()

        assert device == DeviceType.CPU

    @patch('src.hardware.device_detector.torch.cuda.is_available', return_value=True)
    @patch('src.hardware.device_detector.torch.cuda.device_count')
    def test_get_gpu_count(self, mock_device_count, mock_cuda_avail):
        """Test AC5: Query number of available GPUs."""
        mock_device_count.return_value = 2

        detector = DeviceDetector()
        count = detector.get_gpu_count()

        assert count == 2
        mock_device_count.assert_called_once()

    @patch('src.hardware.device_detector.torch.cuda.is_available', return_value=True)
    @patch('src.hardware.device_detector.torch.cuda.device_count', return_value=1)
    @patch('src.hardware.device_detector.torch.cuda.get_device_properties')
    def test_get_gpu_info(self, mock_get_props, mock_device_count, mock_cuda_avail):
        """Test AC5: Get GPU information."""
        mock_props = MagicMock()
        mock_props.name = "NVIDIA RTX 3080"
        mock_props.total_memory = 10 * 1024 * 1024 * 1024  # 10GB
        mock_props.major = 8
        mock_props.minor = 6
        mock_get_props.return_value = mock_props

        detector = DeviceDetector()
        info = detector.get_gpu_info(0)

        assert info["name"] == "NVIDIA RTX 3080"
        assert info["memory_gb"] == 10
        assert info["compute_capability"] == "8.6"
        mock_get_props.assert_called_with(0)


class TestDeviceType:
    """Test DeviceType enum functionality."""

    def test_device_type_values(self):
        """Test DeviceType enum has correct values."""
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.CUDA.value == "cuda"
        assert DeviceType.MPS.value == "mps"
        assert DeviceType.TFLITE.value == "tflite"
        assert DeviceType.ONNX.value == "onnx"

    def test_device_type_from_string(self):
        """Test creating DeviceType from string."""
        assert DeviceType("cpu") == DeviceType.CPU
        assert DeviceType("cuda") == DeviceType.CUDA
        assert DeviceType("mps") == DeviceType.MPS

    def test_device_type_invalid_string(self):
        """Test DeviceType with invalid string raises error."""
        with pytest.raises(ValueError):
            DeviceType("invalid")
