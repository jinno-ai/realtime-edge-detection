"""Unit tests for DeviceManager class."""

import pytest
from unittest.mock import patch, MagicMock
from src.hardware.device_manager import DeviceManager
from src.hardware.device_detector import DeviceType


class TestDeviceManager:
    """Test device management functionality."""

    def test_parse_device_string_auto(self):
        """Test parsing 'auto' device string."""
        with patch.object(DeviceManager, '_auto_detect', return_value=DeviceType.CUDA) as mock_detect:
            manager = DeviceManager()
            device = manager.parse_device_string("auto")

            assert device == DeviceType.CUDA
            # Called once in parse_device_string
            assert mock_detect.call_count >= 1

    def test_parse_device_string_cpu(self):
        """Test parsing 'cpu' device string (AC2)."""
        manager = DeviceManager()
        device = manager.parse_device_string("cpu")

        assert device == DeviceType.CPU

    def test_parse_device_string_cuda(self):
        """Test parsing 'cuda' device string."""
        manager = DeviceManager(device_str="cuda")

        assert manager.selected_device == DeviceType.CUDA
        assert manager.gpu_id == 0  # Should default to GPU 0

    def test_parse_device_string_cuda_with_id(self):
        """Test parsing 'cuda:0' or 'cuda:1' device string (AC5)."""
        manager = DeviceManager(device_str="cuda:0")

        assert manager.selected_device == DeviceType.CUDA
        assert manager.gpu_id == 0

    def test_parse_device_string_mps(self):
        """Test parsing 'mps' device string."""
        manager = DeviceManager()
        device = manager.parse_device_string("mps")

        assert device == DeviceType.MPS

    def test_parse_device_string_invalid(self):
        """Test parsing invalid device string raises error."""
        manager = DeviceManager()

        with pytest.raises(ValueError, match="Unknown device"):
            manager.parse_device_string("invalid")

    def test_parse_device_string_invalid_gpu_id(self):
        """Test parsing device string with invalid GPU ID."""
        manager = DeviceManager()

        with pytest.raises(ValueError, match="Invalid GPU ID"):
            manager.parse_device_string("cuda:abc")

    @patch('src.hardware.device_manager.torch.cuda.is_available')
    def test_validate_device_cuda_unavailable(self, mock_cuda):
        """Test AC3: Error when CUDA requested but unavailable."""
        mock_cuda.return_value = False

        manager = DeviceManager()
        manager.selected_device = DeviceType.CUDA

        with pytest.raises(RuntimeError, match="Device 'cuda' is not available"):
            manager.validate_device()

    @patch('src.hardware.device_manager.torch.cuda.is_available')
    def test_validate_device_cuda_available(self, mock_cuda):
        """Test validation passes when CUDA available."""
        mock_cuda.return_value = True

        manager = DeviceManager()
        manager.selected_device = DeviceType.CUDA

        # Should not raise
        manager.validate_device()

    def test_get_torch_device_cpu(self):
        """Test getting torch device object for CPU."""
        manager = DeviceManager()
        manager.selected_device = DeviceType.CPU

        device = manager.get_torch_device()

        assert device.type == "cpu"

    @patch('src.hardware.device_manager.torch.cuda.is_available')
    def test_get_torch_device_cuda(self, mock_cuda):
        """Test getting torch device object for CUDA."""
        mock_cuda.return_value = True

        manager = DeviceManager()
        manager.selected_device = DeviceType.CUDA
        manager.gpu_id = 0

        device = manager.get_torch_device()

        assert device.type == "cuda"
        assert device.index == 0

    @patch('src.hardware.device_manager.torch.cuda.is_available')
    def test_get_torch_device_cuda_with_gpu_id(self, mock_cuda):
        """Test AC5: Getting torch device for specific GPU."""
        mock_cuda.return_value = True

        manager = DeviceManager()
        manager.selected_device = DeviceType.CUDA
        manager.gpu_id = 1

        device = manager.get_torch_device()

        assert device.type == "cuda"
        assert device.index == 1

    def test_device_string_representation(self):
        """Test device string representation."""
        manager = DeviceManager()
        manager.selected_device = DeviceType.CUDA
        manager.gpu_id = 0

        assert manager.device_string == "cuda:0"

        manager.gpu_id = None
        assert manager.device_string == "cuda"

        manager.selected_device = DeviceType.CPU
        assert manager.device_string == "cpu"


class TestDeviceManagerConfigIntegration:
    """Test DeviceManager integration with configuration."""

    def test_from_config_auto(self):
        """Test AC4: DeviceManager from config with 'auto' device."""
        config = {"device": "auto"}

        with patch.object(DeviceManager, '_auto_detect') as mock_detect:
            mock_detect.return_value = DeviceType.MPS

            manager = DeviceManager.from_config(config)

            assert manager.selected_device == DeviceType.MPS

    def test_from_config_cpu(self):
        """Test AC2, AC4: DeviceManager from config forcing CPU."""
        config = {"device": "cpu"}

        manager = DeviceManager.from_config(config)

        assert manager.selected_device == DeviceType.CPU

    def test_from_config_cuda_with_id(self):
        """Test AC5: DeviceManager from config with specific GPU."""
        config = {"device": "cuda:1"}

        manager = DeviceManager.from_config(config)

        assert manager.selected_device == DeviceType.CUDA
        assert manager.gpu_id == 1
