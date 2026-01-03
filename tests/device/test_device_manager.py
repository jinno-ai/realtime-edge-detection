"""
Unit tests for DeviceManager.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.device.device_manager import DeviceManager, DeviceType, DeviceError


@pytest.fixture
def device_manager():
    """Create a DeviceManager instance."""
    return DeviceManager()


class TestDeviceDetection:
    """Test device detection functionality."""

    def test_detect_cuda_available(self, device_manager):
        """Test CUDA detection when available."""
        with patch('builtins.__import__') as mock_import:
            # Mock torch module
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 2

            # Configure import to return mock_torch for 'torch'
            def import_side_effect(name, *args, **kwargs):
                if name == 'torch':
                    return mock_torch
                return MagicMock()

            mock_import.side_effect = import_side_effect

            devices = device_manager.detect_devices()

            assert DeviceType.CUDA in devices

    def test_detect_cuda_unavailable(self, device_manager):
        """Test CUDA detection when unavailable."""
        with patch('builtins.__import__') as mock_import:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False

            def import_side_effect(name, *args, **kwargs):
                if name == 'torch':
                    return mock_torch
                return MagicMock()

            mock_import.side_effect = import_side_effect

            devices = device_manager.detect_devices()

            # Should still have CPU as fallback
            assert DeviceType.CPU in devices

    def test_detect_mps_available(self, device_manager):
        """Test MPS (Apple Silicon) detection when available."""
        with patch('builtins.__import__') as mock_import:
            mock_torch = MagicMock()
            mock_torch.backends.mps.is_available.return_value = True
            mock_torch.cuda.is_available.return_value = False

            def import_side_effect(name, *args, **kwargs):
                if name == 'torch':
                    return mock_torch
                return MagicMock()

            mock_import.side_effect = import_side_effect

            devices = device_manager.detect_devices()

            assert DeviceType.MPS in devices

    def test_detect_cpu_always_available(self, device_manager):
        """Test that CPU is always detected."""
        with patch('builtins.__import__') as mock_import:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            # No MPS backend

            def import_side_effect(name, *args, **kwargs):
                if name == 'torch':
                    return mock_torch
                return MagicMock()

            mock_import.side_effect = import_side_effect

            devices = device_manager.detect_devices()

            assert DeviceType.CPU in devices
            assert len(devices) >= 1


class TestDeviceSelection:
    """Test device selection functionality."""

    def test_get_device_auto(self, device_manager):
        """Test automatic device selection."""
        with patch.object(device_manager, '_check_cuda', return_value=False):
            with patch.object(device_manager, '_check_mps', return_value=False):
                device = device_manager.get_device("auto")

                assert device == DeviceType.CPU

    def test_get_device_cpu(self, device_manager):
        """Test explicit CPU selection."""
        device = device_manager.get_device("cpu")
        assert device == DeviceType.CPU

    def test_get_device_with_index(self, device_manager):
        """Test device selection with index (e.g., cuda:0)."""
        with patch.object(device_manager, '_check_cuda', return_value=True):
            device = device_manager.get_device("cuda:0")
            assert device == DeviceType.CUDA

    def test_get_unavailable_device_raises_error(self, device_manager):
        """Test that requesting unavailable device raises error."""
        with patch.object(device_manager, '_check_cuda', return_value=False):
            with pytest.raises(DeviceError) as exc_info:
                device_manager.get_device("cuda")

            assert "not available" in str(exc_info.value)

    def test_get_invalid_device_raises_error(self, device_manager):
        """Test that invalid device specification raises error."""
        with pytest.raises(DeviceError) as exc_info:
            device_manager.get_device("invalid_device")

            assert "Invalid device specification" in str(exc_info.value)


class TestDeviceInfo:
    """Test device information retrieval."""

    def test_get_cuda_device_info(self, device_manager):
        """Test getting CUDA device information."""
        with patch('src.device.device_manager.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 2
            mock_torch.cuda.current_device.return_value = 0
            mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3080"

            info = device_manager.get_device_info(DeviceType.CUDA)

            assert info["type"] == "cuda"
            assert info["available"]
            assert info["device_count"] == 2
            assert info["device_name"] == "NVIDIA GeForce RTX 3080"

    def test_list_available_devices(self, device_manager):
        """Test listing available devices."""
        with patch.object(device_manager, '_check_cuda', return_value=True):
            with patch('src.device.device_manager.torch') as mock_torch:
                mock_torch.cuda.is_available.return_value = True
                mock_torch.cuda.device_count.return_value = 1

                devices_str = device_manager.list_available_devices()

                assert "Available devices:" in devices_str
                assert "cuda" in devices_str.lower()


class TestTorchDevice:
    """Test PyTorch device object conversion."""

    def test_get_torch_device_cpu(self, device_manager):
        """Test getting PyTorch CPU device."""
        import torch

        torch_device = device_manager.get_torch_device(DeviceType.CPU)

        assert torch_device.type == "cpu"

    def test_get_torch_device_cuda(self, device_manager):
        """Test getting PyTorch CUDA device."""
        import torch

        with patch('src.device.device_manager.torch', torch):
            torch_device = device_manager.get_torch_device(DeviceType.CUDA)

            assert torch_device.type == "cuda"

    def test_get_torch_device_without_pytorch(self, device_manager):
        """Test that ImportError is raised when PyTorch unavailable."""
        with patch('src.device.device_manager.torch', None):
            with pytest.raises(ImportError):
                device_manager.get_torch_device(DeviceType.CPU)


class TestPriorityOrder:
    """Test device detection priority order."""

    def test_cuda_has_priority_over_mps(self, device_manager):
        """Test that CUDA is prioritized over MPS."""
        with patch.object(device_manager, '_check_cuda', return_value=True):
            with patch.object(device_manager, '_check_mps', return_value=True):
                device = device_manager.get_device("auto")

                assert device == DeviceType.CUDA

    def test_mps_has_priority_over_tflite(self, device_manager):
        """Test that MPS is prioritized over TFLite."""
        with patch.object(device_manager, '_check_cuda', return_value=False):
            with patch.object(device_manager, '_check_mps', return_value=True):
                with patch.object(device_manager, '_check_tflite', return_value=True):
                    device = device_manager.get_device("auto")

                    assert device == DeviceType.MPS

    def test_tflite_has_priority_over_cpu(self, device_manager):
        """Test that TFLite is prioritized over CPU."""
        with patch.object(device_manager, '_check_cuda', return_value=False):
            with patch.object(device_manager, '_check_mps', return_value=False):
                with patch.object(device_manager, '_check_tflite', return_value=True):
                    device = device_manager.get_device("auto")

                    assert device == DeviceType.TFLITE


class TestCacheResults:
    """Test that detection results are cached."""

    def test_detect_devices_caches_results(self, device_manager):
        """Test that detect_devices caches results."""
        with patch.object(device_manager, '_check_cuda') as mock_check:
            mock_check.return_value = True

            # First call
            device_manager.detect_devices()
            assert mock_check.call_count == 1

            # Second call should use cache
            device_manager.detect_devices()
            assert mock_check.call_count == 1  # No additional call
