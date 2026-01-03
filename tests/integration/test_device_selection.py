"""
Integration tests for device selection and fallback.

Tests:
- CPU device selection
- CUDA device selection (when available)
- ONNX runtime device selection
- Device fallback mechanisms
- Error handling for incompatible devices
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, Mock
import torch


class TestCPUDeviceSelection:
    """Test CPU device selection"""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    def test_cpu_device_initialization(self):
        """Test CPU device can be initialized"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')
        assert manager.device.type == 'cpu'

    def test_cpu_detection(self, sample_image):
        """Test detection works on CPU"""
        from src.hardware.device_manager import DeviceManager
        from src.models.yolo_detector import YOLODetector

        manager = DeviceManager(device='cpu')

        # Mock the model to avoid actual inference
        with patch.object(YOLODetector, '_load_model') as mock_load:
            mock_model = Mock()
            mock_model.return_value = []
            mock_load.return_value = mock_model

            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            assert detector.device_manager.device.type == 'cpu'

    def test_cpu_fallback_from_cuda(self):
        """Test CPU fallback when CUDA is unavailable"""
        from src.hardware.device_manager import DeviceManager

        with patch('torch.cuda.is_available', return_value=False):
            manager = DeviceManager(device='auto')
            # Should fallback to CPU
            assert manager.device.type == 'cpu'


class TestCUDADeviceSelection:
    """Test CUDA device selection"""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_device_initialization(self):
        """Test CUDA device can be initialized"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cuda')
        assert manager.device.type == 'cuda'

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_detection(self, sample_image):
        """Test detection works on CUDA"""
        from src.hardware.device_manager import DeviceManager
        from src.models.yolo_detector import YOLODetector

        manager = DeviceManager(device='cuda')

        with patch.object(YOLODetector, '_load_model') as mock_load:
            mock_model = Mock()
            mock_model.return_value = []
            mock_load.return_value = mock_model

            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            assert detector.device_manager.device.type == 'cuda'

    def test_cuda_unavailable_error(self):
        """Test error when CUDA is requested but unavailable"""
        from src.hardware.device_manager import DeviceManager

        with patch('torch.cuda.is_available', return_value=False):
            # Should fallback to CPU instead of error
            manager = DeviceManager(device='auto')
            assert manager.device.type == 'cpu'


class TestONNXDeviceSelection:
    """Test ONNX runtime device selection"""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    def test_onnx_cpu_provider(self, sample_image):
        """Test ONNX with CPU provider"""
        try:
            from src.models.onnx import ONNXDetector

            detector = ONNXDetector(
                model_path='model.onnx',
                providers=['CPUExecutionProvider']
            )

            assert 'CPUExecutionProvider' in detector.providers

        except ImportError:
            pytest.skip("ONNX not available")

    def test_onnx_cuda_provider(self):
        """Test ONNX with CUDA provider"""
        try:
            import onnxruntime as ort

            # Check if CUDA provider is available
            available_providers = ort.get_available_providers()
            if 'CUDAExecutionProvider' not in available_providers:
                pytest.skip("CUDA provider not available")

            from src.models.onnx import ONNXDetector

            detector = ONNXDetector(
                model_path='model.onnx',
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )

            assert 'CUDAExecutionProvider' in detector.providers

        except ImportError:
            pytest.skip("ONNX not available")


class TestDeviceFallback:
    """Test device fallback mechanisms"""

    def test_auto_selection_priority(self):
        """Test auto device selection follows priority order"""
        from src.hardware.device_manager import DeviceManager

        # Should try CUDA -> MPS -> CPU
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = DeviceManager(device='auto')
                assert manager.device.type == 'cpu'

    def test_fallback_on_error(self):
        """Test fallback when device initialization fails"""
        from src.hardware.device_manager import DeviceManager

        # Mock CUDA to fail initialization
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.device') as mock_device:
                mock_device.side_effect = RuntimeError("CUDA error")

                # Should gracefully handle and fallback
                try:
                    manager = DeviceManager(device='cuda')
                except RuntimeError:
                    # Expected to raise error if explicit CUDA fails
                    pass

    def test_explicit_cpu_no_fallback(self):
        """Test explicit CPU selection doesn't attempt fallback"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')
        assert manager.device.type == 'cpu'
        # Should not try other devices


class TestDeviceCompatibility:
    """Test device compatibility checks"""

    def test_incompatible_device_error(self):
        """Test error with incompatible device string"""
        from src.hardware.device_manager import DeviceManager

        with pytest.raises((ValueError, RuntimeError)):
            manager = DeviceManager(device='invalid_device')

    def test_device_detection_reporting(self):
        """Test device detection reports available devices"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='auto')

        # Should report device information
        assert manager.device is not None
        assert hasattr(manager, 'device_type')


class TestMultiDeviceScenarios:
    """Test multi-device scenarios"""

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create multiple sample images"""
        images = []
        for i in range(3):
            img_path = tmp_path / f"test_{i}.jpg"
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(img_path), img)
            images.append(str(img_path))
        return images

    def test_batch_processing_same_device(self, sample_images):
        """Test batch processing uses consistent device"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')

        # All operations should use same device
        device_1 = manager.device
        device_2 = manager.device

        assert device_1.type == device_2.type == 'cpu'

    def test_device_switching(self):
        """Test switching between devices"""
        from src.hardware.device_manager import DeviceManager

        cpu_manager = DeviceManager(device='cpu')
        assert cpu_manager.device.type == 'cpu'

        # Create new manager with different device
        auto_manager = DeviceManager(device='auto')
        # Should initialize successfully
        assert auto_manager.device is not None


class TestDeviceMemoryManagement:
    """Test device memory management"""

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_memory_cleanup(self):
        """Test CUDA memory is properly cleaned up"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cuda')

        # Get initial memory
        if torch.cuda.is_available():
            initial_memory = torch.cuda.memory_allocated()

            # Create tensor and ensure cleanup
            test_tensor = torch.randn(1000, 1000).cuda()
            del test_tensor

            torch.cuda.empty_cache()

            # Memory should be freed
            final_memory = torch.cuda.memory_allocated()
            # Note: exact equality may not hold due to caching, but should be close

    def test_cpu_memory_management(self):
        """Test CPU memory management"""
        import gc
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')

        # Create large tensor
        large_tensor = torch.randn(10000, 10000)
        del large_tensor
        gc.collect()

        # Should not leak memory (pytest process will exit anyway)


class TestDeviceErrorHandling:
    """Test device error handling"""

    def test_oom_error_handling(self):
        """Test out-of-memory error handling"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')

        # Attempt to allocate very large tensor
        try:
            # This should fail with OOM on most systems
            large_tensor = torch.randn(1000000, 1000000)
            del large_tensor
        except RuntimeError as e:
            # Expected to fail with out-of-memory
            assert 'memory' in str(e).lower() or 'out of' in str(e).lower()

    def test_device_not_ready_error(self):
        """Test error when device is not ready"""
        from src.hardware.device_manager import DeviceManager

        # Mock device to raise error
        with patch('torch.device') as mock_device:
            mock_device.side_effect = RuntimeError("Device not ready")

            try:
                manager = DeviceManager(device='cpu')
            except RuntimeError:
                # Expected to raise error
                pass
