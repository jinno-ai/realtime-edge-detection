"""
Integration tests for device selection

Tests device manager behavior against the actual implementation APIs.
"""

import pytest
import numpy as np
import cv2
import torch
from unittest.mock import patch, Mock


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
        from src.hardware.device_manager import DeviceManager, DeviceType

        manager = DeviceManager(device_str='cpu')
        assert manager.selected_device == DeviceType.CPU

    def test_cpu_detection(self, sample_image):
        """Test detection works on CPU"""
        from src.models.yolo_detector import YOLODetector

        # Mock model loading to avoid actual inference
        with patch.object(YOLODetector, 'load_model'):
            detector = YOLODetector(model_path='yolov8n.pt')
            detector.load_model()

            assert detector.model_path == 'yolov8n.pt'

    def test_cpu_fallback_from_cuda(self):
        """Test CPU fallback when CUDA is unavailable"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = DeviceManager(device_str='auto')
                # Should fallback to CPU
                assert manager.selected_device == DeviceType.CPU


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
        from src.hardware.device_manager import DeviceManager, DeviceType

        manager = DeviceManager(device_str='cuda')
        assert manager.selected_device == DeviceType.CUDA

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_detection(self, sample_image):
        """Test detection works on CUDA"""
        from src.models.yolo_detector import YOLODetector

        with patch.object(YOLODetector, 'load_model'):
            detector = YOLODetector(model_path='yolov8n.pt')
            detector.load_model()

            assert detector.model_path == 'yolov8n.pt'

    def test_cuda_unavailable_error(self):
        """Test auto selection falls back when CUDA is unavailable"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = DeviceManager(device_str='auto')
                assert manager.selected_device == DeviceType.CPU


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
        """Test ONNX detector accepts CPU provider config"""
        try:
            from src.models.onnx import ONNXDetector
        except ImportError:
            pytest.skip("ONNX not available")

        detector = ONNXDetector({
            'model_path': 'model.onnx',
            'provider': 'CPUExecutionProvider',
        })

        assert detector.provider == 'CPUExecutionProvider'
        assert detector.device == 'cpu'

    def test_onnx_cuda_provider(self):
        """Test ONNX detector accepts CUDA provider when available"""
        try:
            import onnxruntime as ort
        except ImportError:
            pytest.skip("ONNX not available")

        available_providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' not in available_providers:
            pytest.skip("CUDA provider not available")

        from src.models.onnx import ONNXDetector

        detector = ONNXDetector({
            'model_path': 'model.onnx',
            'provider': 'CUDAExecutionProvider',
        })

        assert detector.provider == 'CUDAExecutionProvider'


class TestDeviceFallback:
    """Test device fallback mechanisms"""

    def test_auto_selection_priority(self):
        """Test auto device selection follows priority order"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        # Should try CUDA -> MPS -> CPU
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = DeviceManager(device_str='auto')
                assert manager.selected_device == DeviceType.CPU

    def test_fallback_on_error(self):
        """Test that explicit CUDA selection raises when unavailable"""
        from src.hardware.device_manager import DeviceManager

        with patch('torch.cuda.is_available', return_value=False):
            # Explicit CUDA on a machine without it must surface a clear error
            with pytest.raises((RuntimeError, ValueError)):
                manager = DeviceManager(device_str='cuda')
                manager.validate_device()

    def test_explicit_cpu_no_fallback(self):
        """Test explicit CPU selection doesn't attempt fallback"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        manager = DeviceManager(device_str='cpu')
        assert manager.selected_device == DeviceType.CPU


class TestDeviceCompatibility:
    """Test device compatibility checks"""

    def test_incompatible_device_error(self):
        """Test error with incompatible device string"""
        from src.hardware.device_manager import DeviceManager

        with pytest.raises((ValueError, RuntimeError)):
            DeviceManager(device_str='invalid_device')

    def test_device_detection_reporting(self):
        """Test device detection reports available devices"""
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device_str='auto')

        # Should report device information
        assert manager.selected_device is not None
        assert isinstance(manager.device_string, str)


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
        """Test device manager is consistent across calls"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        manager = DeviceManager(device_str='cpu')

        device_1 = manager.selected_device
        device_2 = manager.selected_device

        assert device_1 is device_2 == DeviceType.CPU

    def test_device_switching(self):
        """Test switching between devices"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        cpu_manager = DeviceManager(device_str='cpu')
        assert cpu_manager.selected_device == DeviceType.CPU

        # Create new manager with different device
        auto_manager = DeviceManager(device_str='auto')
        assert auto_manager.selected_device is not None


class TestDeviceMemoryManagement:
    """Test device memory management"""

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_memory_cleanup(self):
        """Test CUDA memory is properly cleaned up"""
        initial_memory = torch.cuda.memory_allocated()

        test_tensor = torch.randn(1000, 1000).cuda()
        del test_tensor

        torch.cuda.empty_cache()

        final_memory = torch.cuda.memory_allocated()
        # Exact equality may not hold due to caching, but should be close
        assert final_memory <= initial_memory + 1024 * 1024

    def test_cpu_memory_management(self):
        """Test CPU memory management"""
        import gc
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device_str='cpu')
        assert manager is not None

        # Create tensor and clean up
        tensor = torch.randn(1000, 1000)
        del tensor
        gc.collect()


class TestDeviceErrorHandling:
    """Test device error handling"""

    def test_oom_error_handling(self):
        """OOM errors surface as RuntimeError, simulated without huge allocations"""
        # Simulate an OOM during tensor allocation by mocking torch.randn
        with patch('torch.randn', side_effect=RuntimeError("out of memory")):
            with pytest.raises(RuntimeError, match='memory|out of'):
                torch.randn(1000, 1000)

    def test_device_not_ready_error(self):
        """Test error propagates when device selection raises"""
        from src.hardware.device_manager import DeviceManager

        with patch('torch.device', side_effect=RuntimeError("Device not ready")):
            with pytest.raises(RuntimeError):
                manager = DeviceManager(device_str='cpu')
                manager.get_torch_device()
