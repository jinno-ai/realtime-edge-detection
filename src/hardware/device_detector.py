"""Device detection and hardware abstraction for edge detection."""

from enum import Enum
from typing import Optional, Dict, Any
import torch


class DeviceType(Enum):
    """Supported device types for inference."""

    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    TFLITE = "tflite"
    ONNX = "onnx"


class Platform:
    """Platform-specific utilities."""

    @staticmethod
    def has_tflite() -> bool:
        """Check if TFLite runtime is available."""
        try:
            import tflite_runtime  # type: ignore
            return True
        except ImportError:
            return False


class DeviceDetector:
    """Auto-detect available hardware devices."""

    def __init__(self):
        """Initialize device detector."""
        self._cached_device: Optional[DeviceType] = None

    def detect_device(self) -> DeviceType:
        """
        Auto-detect best available device.

        Detection priority:
        1. CUDA (NVIDIA GPU)
        2. MPS (Apple Silicon GPU)
        3. TFLite (Edge TPU)
        4. CPU (fallback)

        Returns:
            Detected device type

        AC Reference: #1
        """
        # Return cached result if available
        if self._cached_device is not None:
            return self._cached_device

        # Check CUDA first (highest priority)
        if torch.cuda.is_available():
            self._cached_device = DeviceType.CUDA
            return DeviceType.CUDA

        # Check MPS for Apple Silicon
        if torch.backends.mps.is_available():
            self._cached_device = DeviceType.MPS
            return DeviceType.MPS

        # Check TFLite for edge devices
        if Platform.has_tflite():
            self._cached_device = DeviceType.TFLITE
            return DeviceType.TFLITE

        # Fallback to CPU
        self._cached_device = DeviceType.CPU
        return DeviceType.CPU

    def get_gpu_count(self) -> int:
        """
        Get number of available CUDA GPUs.

        Returns:
            Number of GPUs (0 if CUDA unavailable)

        AC Reference: #5
        """
        if not torch.cuda.is_available():
            return 0
        return torch.cuda.device_count()

    def get_gpu_info(self, gpu_id: int = 0) -> Dict[str, Any]:
        """
        Get information about a specific GPU.

        Args:
            gpu_id: GPU device ID (default: 0)

        Returns:
            Dictionary with GPU info (name, memory_gb)

        Raises:
            RuntimeError: If CUDA unavailable or gpu_id invalid

        AC Reference: #5
        """
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available on this system")

        device_count = torch.cuda.device_count()
        if gpu_id >= device_count:
            raise RuntimeError(
                f"Invalid GPU ID {gpu_id}. "
                f"Available GPUs: {device_count}"
            )

        props = torch.cuda.get_device_properties(gpu_id)
        memory_gb = props.total_memory / (1024 ** 3)

        return {
            "name": props.name,
            "memory_gb": round(memory_gb, 2),
            "compute_capability": f"{props.major}.{props.minor}",
        }

    def list_available_devices(self) -> Dict[str, Any]:
        """
        List all available devices with information.

        Returns:
            Dictionary with device availability and info

        AC Reference: #3, #5
        """
        devices = {
            "cpu": {"available": True, "name": "CPU"},
            "cuda": {"available": False},
            "mps": {"available": False},
            "tflite": {"available": False},
        }

        # Check CUDA
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            devices["cuda"]["available"] = True
            devices["cuda"]["count"] = gpu_count
            devices["cuda"]["gpus"] = []
            for i in range(gpu_count):
                devices["cuda"]["gpus"].append(self.get_gpu_info(i))

        # Check MPS
        if torch.backends.mps.is_available():
            devices["mps"]["available"] = True
            devices["mps"]["name"] = "Apple Silicon GPU"

        # Check TFLite
        if Platform.has_tflite():
            devices["tflite"]["available"] = True
            devices["tflite"]["name"] = "Edge TPU"

        return devices
